"""
教材：《水库调度优化与决策》
章节：第8章 案例：多水库联合调度
功能：在简化的大渡河三级梯级场景中，对比 DP、NSGA-II、MPC 三种联合调度方法，
      输出 KPI 指标表，并绘制过程线与 Pareto 前沿图。
"""

import time
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import minimize


# =========================
# 1) 关键参数（可直接调参）
# =========================
PARAMS = {
    # 基础时空参数
    "T": 30,                     # 调度期长度（天）
    "N": 3,                      # 水库数量
    "DT": 86400.0,               # 秒/天

    # 水库名称（近似对应大渡河典型控制性梯级）
    "NAMES": ["双江口", "猴子岩", "瀑布沟"],

    # 库容边界（单位：百万立方米，Mm3）
    "S_MIN": np.array([400.0, 260.0, 700.0]),
    "S_MAX": np.array([1200.0, 700.0, 1800.0]),
    "S_FLOOD": np.array([1080.0, 620.0, 1650.0]),
    "S_TARGET": np.array([900.0, 520.0, 1400.0]),
    "S_INIT": np.array([820.0, 480.0, 1320.0]),

    # 下泄约束（单位：Mm3/天）
    "R_MIN": np.array([20.0, 30.0, 45.0]),
    "R_MAX": np.array([130.0, 170.0, 260.0]),
    "Q_ECO": np.array([25.0, 35.0, 50.0]),        # 生态流量需求
    "Q_TURB_MAX": np.array([120.0, 160.0, 240.0]),# 机组过流上限（超出部分视作弃水）

    # 水头与效率参数
    "H0": np.array([130.0, 95.0, 78.0]),          # 基准水头（m）
    "H_ALPHA": np.array([0.018, 0.020, 0.012]),   # 水头-库容线性系数
    "ETA": np.array([0.90, 0.91, 0.92]),          # 综合效率

    # DP 参数
    "DP_GRID_LEVELS": 7,         # 状态离散数
    "DP_ACTION_LEVELS": 4,       # 每库动作离散数

    # NSGA-II 参数
    "NSGA_POP": 48,
    "NSGA_GEN": 35,
    "NSGA_MUT_PROB": 0.10,
    "NSGA_MUT_SIGMA": 10.0,      # 变异标准差（Mm3/天）

    # MPC 参数
    "MPC_H": 6,                  # 预测时域

    # 目标权重（统一奖励/代价）
    "W_ECO": 0.35,
    "W_FLOOD": 0.03,
    "W_SPILL": 0.02,
    "W_TERMINAL": 0.02,

    # 入流预测误差
    "PRED_STD": 8.0,
    "SEED": 20260307,
}


# 中文显示
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 2) 数据生成与系统仿真
# =========================
def generate_case_data(p):
    """生成简化入流序列（真实值 + 预测值）"""
    rng = np.random.default_rng(p["SEED"])
    T, N = p["T"], p["N"]
    t = np.arange(T)

    inflow = np.zeros((T, N))
    # 三段工况：常态 -> 偏枯 -> 偏丰（体现不确定性和非平稳性）
    regime = np.ones(T)
    regime[10:20] = 0.78
    regime[20:] = 1.15

    base = np.array([90.0, 35.0, 55.0])
    amp = np.array([40.0, 10.0, 14.0])
    phase = np.array([2.0, 1.0, 0.0])

    for i in range(N):
        seasonal = amp[i] * np.sin(2 * np.pi * (t + phase[i]) / 12.0)
        noise = rng.normal(0.0, 4.0 + 2.0 * i, size=T)
        inflow[:, i] = np.clip(base[i] * regime + seasonal + noise, 5.0, None)

    # 预测入流：真实值 + 偏差 + 随机误差
    bias = np.zeros((T, N))
    bias[10:20, :] = -6.0
    bias[20:, :] = 4.0
    pred_noise = rng.normal(0.0, p["PRED_STD"], size=(T, N))
    inflow_pred = np.clip(inflow + bias + pred_noise, 5.0, None)

    return inflow, inflow_pred


def cascade_step(s_t, inflow_local_t, release_cmd_t, p):
    """
    单步串联水库水量-电力耦合更新
    单位约定：
    - 库容、入流、下泄：Mm3 与 Mm3/天
    - 功率：MW
    """
    N = p["N"]
    s_next = np.zeros(N)
    r_ctrl = np.zeros(N)
    q_out = np.zeros(N)
    power = np.zeros(N)
    eco_def = np.zeros(N)
    flood = np.zeros(N)
    spill = np.zeros(N)

    upstream_out = 0.0  # 上游出流（含弃水）直接进入下游

    for i in range(N):
        net_inflow = inflow_local_t[i] + upstream_out
        available = s_t[i] + net_inflow

        # 控制下泄先按命令与边界修正
        r = np.clip(release_cmd_t[i], p["R_MIN"][i], p["R_MAX"][i])

        # 水量可行性：不能低于死库容
        max_release = max(0.0, available - p["S_MIN"][i])
        r = min(r, max_release)
        r = max(0.0, r)

        # 更新库容并处理溢库弃水
        st = available - r
        overflow = max(0.0, st - p["S_MAX"][i])
        st = min(st, p["S_MAX"][i])

        outflow = r + overflow  # 总出流=可控下泄+溢流
        spill[i] = overflow

        # 水头与出力
        head = max(20.0, p["H0"][i] + p["H_ALPHA"][i] * (s_t[i] - p["S_TARGET"][i]))
        q_gen_m3s = min(r, p["Q_TURB_MAX"][i]) * 1e6 / p["DT"]
        power[i] = 9.81 * p["ETA"][i] * q_gen_m3s * head / 1000.0  # MW

        # 生态缺水按总出流核算
        eco_def[i] = max(0.0, p["Q_ECO"][i] - outflow)

        # 防洪风险指标（超汛限库容）
        flood[i] = max(0.0, st - p["S_FLOOD"][i])

        s_next[i] = st
        r_ctrl[i] = r
        q_out[i] = outflow
        upstream_out = outflow

    return s_next, r_ctrl, q_out, power, eco_def, flood, spill


def simulate_plan(plan, inflow, p, s0=None):
    """给定整期决策计划，进行全期仿真"""
    T, N = p["T"], p["N"]
    if s0 is None:
        s0 = p["S_INIT"].copy()

    S = np.zeros((T + 1, N))
    R = np.zeros((T, N))
    Q = np.zeros((T, N))
    PWR = np.zeros((T, N))
    ECO = np.zeros((T, N))
    FLOOD = np.zeros((T, N))
    SPILL = np.zeros((T, N))
    S[0] = s0

    for t in range(T):
        S[t + 1], R[t], Q[t], PWR[t], ECO[t], FLOOD[t], SPILL[t] = cascade_step(
            S[t], inflow[t], plan[t], p
        )

    return {
        "S": S,
        "R": R,
        "Q": Q,
        "P": PWR,
        "ECO": ECO,
        "FLOOD": FLOOD,
        "SPILL": SPILL,
    }


def total_energy_gwh(power_mw, dt_sec):
    return np.sum(power_mw) * (dt_sec / 3600.0) / 1000.0


# =========================
# 3) DP 求解器
# =========================
def solve_dp(inflow, p):
    T, N = p["T"], p["N"]
    G, A = p["DP_GRID_LEVELS"], p["DP_ACTION_LEVELS"]

    # 离散状态网格与动作网格
    grids = [np.linspace(p["S_MIN"][i], p["S_MAX"][i], G) for i in range(N)]
    actions_1d = [np.linspace(p["R_MIN"][i], p["R_MAX"][i], A) for i in range(N)]
    action_set = np.array(np.meshgrid(*actions_1d, indexing="ij")).reshape(N, -1).T
    states = np.array(np.meshgrid(*grids, indexing="ij")).reshape(N, -1).T

    n_states = states.shape[0]
    n_actions = action_set.shape[0]

    # 值函数与策略
    J = np.full((T + 1, n_states), -1e15)
    policy = np.zeros((T, n_states), dtype=int)

    def nearest_state_id(s):
        idx_each = [int(np.argmin(np.abs(grids[i] - s[i]))) for i in range(N)]
        return np.ravel_multi_index(tuple(idx_each), (G, G, G))

    # 终端价值：靠近目标库容
    for sid, s in enumerate(states):
        J[T, sid] = -p["W_TERMINAL"] * np.sum((s - p["S_TARGET"]) ** 2)

    # 逆推
    for t in range(T - 1, -1, -1):
        for sid, s in enumerate(states):
            best_val = -1e15
            best_aid = 0
            for aid in range(n_actions):
                a = action_set[aid]
                s_next, _, _, pw, eco, flood, spill = cascade_step(s, inflow[t], a, p)
                reward = (
                    total_energy_gwh(pw, p["DT"])
                    - p["W_ECO"] * np.sum(eco)
                    - p["W_FLOOD"] * np.sum(flood)
                    - p["W_SPILL"] * np.sum(spill)
                )
                nsid = nearest_state_id(s_next)
                val = reward + J[t + 1, nsid]
                if val > best_val:
                    best_val = val
                    best_aid = aid

            J[t, sid] = best_val
            policy[t, sid] = best_aid

    # 前向生成计划
    sid = nearest_state_id(p["S_INIT"])
    plan = np.zeros((T, N))
    for t in range(T):
        aid = policy[t, sid]
        a = action_set[aid]
        plan[t] = a
        s_grid = states[sid]
        s_next, _, _, _, _, _, _ = cascade_step(s_grid, inflow[t], a, p)
        sid = nearest_state_id(s_next)

    sim = simulate_plan(plan, inflow, p)
    return {"plan": plan, "sim": sim}


# =========================
# 4) NSGA-II 求解器
# =========================
def fast_non_dominated_sort(objs):
    n = len(objs)
    S = [[] for _ in range(n)]
    dom_count = np.zeros(n, dtype=int)
    fronts = [[]]

    for p_idx in range(n):
        for q_idx in range(n):
            if p_idx == q_idx:
                continue
            p_dom_q = np.all(objs[p_idx] <= objs[q_idx]) and np.any(objs[p_idx] < objs[q_idx])
            q_dom_p = np.all(objs[q_idx] <= objs[p_idx]) and np.any(objs[q_idx] < objs[p_idx])

            if p_dom_q:
                S[p_idx].append(q_idx)
            elif q_dom_p:
                dom_count[p_idx] += 1

        if dom_count[p_idx] == 0:
            fronts[0].append(p_idx)

    i = 0
    while len(fronts[i]) > 0:
        nxt = []
        for p_idx in fronts[i]:
            for q_idx in S[p_idx]:
                dom_count[q_idx] -= 1
                if dom_count[q_idx] == 0:
                    nxt.append(q_idx)
        i += 1
        fronts.append(nxt)

    return fronts[:-1]


def crowding_distance(objs, front):
    m = objs.shape[1]
    d = np.zeros(len(front))
    if len(front) == 0:
        return d
    if len(front) <= 2:
        d[:] = 1e9
        return d

    fvals = objs[front]
    for j in range(m):
        order = np.argsort(fvals[:, j])
        d[order[0]] = 1e9
        d[order[-1]] = 1e9
        fmin = fvals[order[0], j]
        fmax = fvals[order[-1], j]
        if abs(fmax - fmin) < 1e-12:
            continue
        for k in range(1, len(front) - 1):
            d[order[k]] += (fvals[order[k + 1], j] - fvals[order[k - 1], j]) / (fmax - fmin)
    return d


def nsga_select(objs, pop_size):
    fronts = fast_non_dominated_sort(objs)
    selected = []
    ranks = np.full(len(objs), 999, dtype=int)
    crowds = np.zeros(len(objs))

    for r, front in enumerate(fronts):
        ranks[front] = r
        cd = crowding_distance(objs, front)
        for i, idx in enumerate(front):
            crowds[idx] = cd[i]

    for front in fronts:
        if len(selected) + len(front) <= pop_size:
            selected.extend(front)
        else:
            cd = crowding_distance(objs, front)
            order = np.argsort(-cd)  # 拥挤度大的优先保留
            need = pop_size - len(selected)
            selected.extend([front[i] for i in order[:need]])
            break

    return np.array(selected, dtype=int), ranks, crowds


def solve_nsga2(inflow, p):
    rng = np.random.default_rng(p["SEED"] + 1)
    T, N = p["T"], p["N"]
    pop_size = p["NSGA_POP"]
    generations = p["NSGA_GEN"]
    dim = T * N

    lb = np.tile(p["R_MIN"], T)
    ub = np.tile(p["R_MAX"], T)

    def evaluate_individual(x):
        plan = x.reshape(T, N)
        sim = simulate_plan(plan, inflow, p)
        energy = total_energy_gwh(sim["P"], p["DT"])
        eco = np.sum(sim["ECO"])
        flood = np.sum(sim["FLOOD"])

        # 两目标均转为最小化：f1(负发电)、f2(生态缺水)，并加入防洪风险惩罚
        f1 = -energy + 0.02 * flood
        f2 = eco + 0.20 * flood
        return np.array([f1, f2]), sim

    # 初始化
    pop = lb + (ub - lb) * rng.random((pop_size, dim))

    for _ in range(generations):
        objs = np.zeros((pop_size, 2))
        for i in range(pop_size):
            objs[i], _ = evaluate_individual(pop[i])

        _, rank, crowd = nsga_select(objs, pop_size)

        def tournament():
            a, b = rng.integers(0, pop_size, size=2)
            if rank[a] < rank[b]:
                return a
            if rank[b] < rank[a]:
                return b
            return a if crowd[a] > crowd[b] else b

        # 生成子代
        offspring = []
        while len(offspring) < pop_size:
            p1 = pop[tournament()]
            p2 = pop[tournament()]
            alpha = rng.random(dim)
            c1 = alpha * p1 + (1.0 - alpha) * p2
            c2 = alpha * p2 + (1.0 - alpha) * p1

            for c in [c1, c2]:
                mask = rng.random(dim) < p["NSGA_MUT_PROB"]
                c[mask] += rng.normal(0.0, p["NSGA_MUT_SIGMA"], size=np.sum(mask))
                c = np.clip(c, lb, ub)
                offspring.append(c)
                if len(offspring) >= pop_size:
                    break

        offspring = np.array(offspring)
        combined = np.vstack([pop, offspring])

        c_objs = np.zeros((2 * pop_size, 2))
        for i in range(2 * pop_size):
            c_objs[i], _ = evaluate_individual(combined[i])

        sel_idx, _, _ = nsga_select(c_objs, pop_size)
        pop = combined[sel_idx]

    # 最终评价
    final_objs = np.zeros((pop_size, 2))
    final_sims = []
    for i in range(pop_size):
        final_objs[i], simi = evaluate_individual(pop[i])
        final_sims.append(simi)

    fronts = fast_non_dominated_sort(final_objs)
    first_front = fronts[0]

    # 选择一个折中解（到归一化理想点的距离最小）
    f = final_objs[first_front]
    f_norm = (f - f.min(axis=0)) / (f.max(axis=0) - f.min(axis=0) + 1e-12)
    dist = np.sum(f_norm ** 2, axis=1)
    best_local = np.argmin(dist)
    best_idx = first_front[best_local]

    best_plan = pop[best_idx].reshape(T, N)
    best_sim = final_sims[best_idx]

    pareto_energy = -final_objs[first_front, 0]
    pareto_eco = final_objs[first_front, 1]

    return {
        "plan": best_plan,
        "sim": best_sim,
        "pareto_energy": pareto_energy,
        "pareto_eco": pareto_eco,
        "chosen_energy": -final_objs[best_idx, 0],
        "chosen_eco": final_objs[best_idx, 1],
    }


# =========================
# 5) MPC 求解器
# =========================
def solve_mpc(inflow_true, inflow_pred, p):
    T, N = p["T"], p["N"]
    H = p["MPC_H"]

    plan = np.zeros((T, N))
    s = p["S_INIT"].copy()
    last_u = np.clip(p["Q_ECO"], p["R_MIN"], p["R_MAX"])

    for t in range(T):
        h = min(H, T - t)

        def mpc_cost(x):
            x = x.reshape(h, N)
            s_pred = s.copy()
            cost = 0.0

            for k in range(h):
                inflow_hat = inflow_pred[t + k]
                s_pred, _, _, pw, eco, flood, spill = cascade_step(s_pred, inflow_hat, x[k], p)

                stage_cost = (
                    -total_energy_gwh(pw, p["DT"])
                    + p["W_ECO"] * np.sum(eco)
                    + p["W_FLOOD"] * np.sum(flood)
                    + p["W_SPILL"] * np.sum(spill)
                )
                cost += stage_cost

            cost += p["W_TERMINAL"] * np.sum((s_pred - p["S_TARGET"]) ** 2)
            return cost

        x0 = np.tile(last_u, h)
        bounds = [(p["R_MIN"][i % N], p["R_MAX"][i % N]) for i in range(h * N)]

        res = minimize(
            mpc_cost,
            x0=x0,
            method="SLSQP",
            bounds=bounds,
            options={"maxiter": 80, "ftol": 1e-4, "disp": False},
        )

        if res.success:
            u = res.x[:N]
        else:
            u = last_u.copy()

        plan[t] = u
        s, _, _, _, _, _, _ = cascade_step(s, inflow_true[t], u, p)
        last_u = u.copy()

    sim = simulate_plan(plan, inflow_true, p)
    return {"plan": plan, "sim": sim}


# =========================
# 6) KPI 与绘图
# =========================
def calc_kpi(method, sim, p, runtime_sec):
    energy = total_energy_gwh(sim["P"], p["DT"])
    eco = np.sum(sim["ECO"])
    spill = np.sum(sim["SPILL"])
    flood_risk = np.sum(sim["FLOOD"])
    eco_req = np.sum(p["Q_ECO"]) * p["T"]
    eco_rate = max(0.0, 1.0 - eco / (eco_req + 1e-12)) * 100.0
    end_ratio = np.mean(sim["S"][-1] / p["S_TARGET"]) * 100.0

    return {
        "method": method,
        "energy": energy,
        "eco": eco,
        "spill": spill,
        "flood": flood_risk,
        "eco_rate": eco_rate,
        "end_ratio": end_ratio,
        "time": runtime_sec,
    }


def print_kpi_table(rows):
    print("\n" + "=" * 120)
    print(f"{'方法':<10}{'总发电量(GWh)':>14}{'生态缺水(Mm3)':>14}{'弃水(Mm3)':>12}"
          f"{'防洪风险指数':>14}{'生态满足率(%)':>14}{'末库容达标率(%)':>16}{'计算时间(s)':>12}")
    print("-" * 120)
    for r in rows:
        print(f"{r['method']:<10}{r['energy']:>14.2f}{r['eco']:>14.2f}{r['spill']:>12.2f}"
              f"{r['flood']:>14.2f}{r['eco_rate']:>14.2f}{r['end_ratio']:>16.2f}{r['time']:>12.2f}")
    print("=" * 120 + "\n")


def plot_results(inflow, results, p):
    T = p["T"]
    t = np.arange(T)
    t_s = np.arange(T + 1)

    fig, ax = plt.subplots(2, 2, figsize=(14, 9))

    # 图1：三库区间来水
    for i in range(p["N"]):
        ax[0, 0].plot(t, inflow[:, i], lw=1.8, label=f"{p['NAMES'][i]}区间来水")
    ax[0, 0].set_title("输入来水过程")
    ax[0, 0].set_xlabel("时段(天)")
    ax[0, 0].set_ylabel("流量 (Mm3/天)")
    ax[0, 0].grid(alpha=0.3)
    ax[0, 0].legend(fontsize=9)

    # 图2：三方法总出力
    for k, v in results.items():
        total_power = np.sum(v["sim"]["P"], axis=1)
        ax[0, 1].plot(t, total_power, lw=2.0, label=k)
    ax[0, 1].set_title("总出力过程对比")
    ax[0, 1].set_xlabel("时段(天)")
    ax[0, 1].set_ylabel("功率 (MW)")
    ax[0, 1].grid(alpha=0.3)
    ax[0, 1].legend()

    # 图3：一级水库库容过程
    for k, v in results.items():
        ax[1, 0].plot(t_s, v["sim"]["S"][:, 0], lw=2.0, label=k)
    ax[1, 0].axhline(p["S_FLOOD"][0], ls="--", c="r", lw=1.2, label="一级汛限")
    ax[1, 0].set_title("一级水库库容轨迹")
    ax[1, 0].set_xlabel("时段(天)")
    ax[1, 0].set_ylabel("库容 (Mm3)")
    ax[1, 0].grid(alpha=0.3)
    ax[1, 0].legend()

    # 图4：NSGA-II Pareto 前沿
    pareto_x = results["NSGA-II"]["pareto_eco"]
    pareto_y = results["NSGA-II"]["pareto_energy"]
    ax[1, 1].scatter(pareto_x, pareto_y, s=22, alpha=0.75, label="Pareto解集")
    ax[1, 1].scatter(
        results["NSGA-II"]["chosen_eco"],
        results["NSGA-II"]["chosen_energy"],
        s=80, c="red", marker="*",
        label="选定折中解",
    )
    ax[1, 1].set_title("NSGA-II Pareto 前沿")
    ax[1, 1].set_xlabel("目标2：生态缺水+风险惩罚 (越小越好)")
    ax[1, 1].set_ylabel("目标1：总发电量近似收益 (越大越好)")
    ax[1, 1].grid(alpha=0.3)
    ax[1, 1].legend()

    plt.tight_layout()
    plt.savefig('ch08_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch08_simulation_result.png")
# plt.show()  # 禁用弹窗


# =========================
# 7) 主程序
# =========================
def main():
    p = PARAMS
    inflow, inflow_pred = generate_case_data(p)

    # DP
    t0 = time.perf_counter()
    dp_res = solve_dp(inflow, p)
    t_dp = time.perf_counter() - t0

    # NSGA-II
    t0 = time.perf_counter()
    nsga_res = solve_nsga2(inflow, p)
    t_nsga = time.perf_counter() - t0

    # MPC
    t0 = time.perf_counter()
    mpc_res = solve_mpc(inflow, inflow_pred, p)
    t_mpc = time.perf_counter() - t0

    results = {
        "DP": dp_res,
        "NSGA-II": nsga_res,
        "MPC": mpc_res,
    }

    kpi_rows = [
        calc_kpi("DP", dp_res["sim"], p, t_dp),
        calc_kpi("NSGA-II", nsga_res["sim"], p, t_nsga),
        calc_kpi("MPC", mpc_res["sim"], p, t_mpc),
    ]
    print_kpi_table(kpi_rows)
    plot_results(inflow, results, p)


if __name__ == "__main__":
    main()
