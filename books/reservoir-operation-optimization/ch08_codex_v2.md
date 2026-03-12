当前会话策略禁止执行 `python` 且文件系统只读，所以我无法在此环境实机运行与落盘；下面给你可直接运行的完整脚本（满足 `numpy/scipy/matplotlib`、KPI表、绘图、中文注释、关键参数变量化）。

```python
# -*- coding: utf-8 -*-
"""
教材：《水库调度优化与决策》
章节：第8章 案例——多水库联合调度（大渡河梯级）
功能：在同一仿真框架中对比 DP、NSGA-II、MPC 三种方法，
输出KPI结果表，并绘制调度过程与Pareto前沿图。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# ---------------- 全局显示设置 ----------------
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ---------------- 关键参数定义（可直接调参） ----------------
N_RES = 3
T = 24
RES_NAMES = ["上游控制库", "中游调节库", "下游控制库"]

S_MIN = np.array([18.0, 8.0, 20.0])      # 死库容
S_MAX = np.array([42.0, 22.0, 56.0])     # 兴利库容上限
S_INIT = np.array([30.0, 13.0, 35.0])    # 初始库容
S_TARGET = np.array([28.0, 12.0, 33.0])  # 期末目标库容

R_MIN = np.array([6.0, 5.0, 7.0])        # 最小下泄
R_MAX = np.array([30.0, 22.0, 34.0])     # 最大下泄
ECO_FLOW = np.array([7.0, 6.0, 8.0])     # 生态最小下泄

H_MIN = np.array([75.0, 45.0, 55.0])     # 最小有效水头
H_MAX = np.array([155.0, 105.0, 125.0])  # 最大有效水头
K_POWER = np.array([0.30, 0.26, 0.33])   # 出力系数（相对量）

LOAD_BASE = 1850.0                        # 系统负荷基准（相对量）

# DP参数
DP_STATE_GRID = 8
DP_ACTION_GRID = 5
DP_GAMMA = 0.98
DP_W_ECO = 20.0
DP_W_LOAD = 1.6
DP_W_SPILL = 5.0
DP_W_TERM = 10.0

# NSGA-II参数
NSGA_POP = 48
NSGA_GEN = 35
NSGA_PC = 0.90
NSGA_PM = 1.0 / (T * N_RES)
NSGA_SIGMA = 0.08

# MPC参数
MPC_HP = 5
MPC_W_ECO = 20.0
MPC_W_LOAD = 1.6
MPC_W_SPILL = 6.0
MPC_W_TERM = 12.0


def generate_series(t_len, seed=2026):
    """生成天然来水与系统负荷序列"""
    rng = np.random.default_rng(seed)
    t = np.arange(t_len)

    inflow = np.zeros((N_RES, t_len))
    # 上游库：季节波动 + 洪峰脉冲 + 随机扰动
    inflow[0] = 16 + 6 * np.sin(2 * np.pi * (t - 4) / t_len) + 4 * np.exp(-0.5 * ((t - 18) / 3) ** 2)
    inflow[0] += rng.normal(0, 1.2, t_len)

    # 中下游区间来水
    inflow[1] = 5 + 2 * np.sin(2 * np.pi * (t + 2) / t_len) + rng.normal(0, 0.5, t_len)
    inflow[2] = 7 + 3 * np.sin(2 * np.pi * (t - 1) / t_len) + rng.normal(0, 0.7, t_len)
    inflow = np.clip(inflow, 0.8, None)

    # 电网负荷（可理解为梯级需跟踪的出力目标）
    load = LOAD_BASE + 180 * np.sin(2 * np.pi * (t + 3) / t_len) + 90 * np.cos(2 * np.pi * t / 7.0)
    return inflow, load


def build_forecast_inflow(inflow_true, seed=7):
    """构造MPC使用的有偏差预测来水"""
    rng = np.random.default_rng(seed)
    rel_err = rng.normal(0.0, 0.18, size=inflow_true.shape)
    bias = np.array([[0.04], [-0.02], [0.01]])
    inflow_forecast = inflow_true * (1.0 + bias + rel_err)
    return np.clip(inflow_forecast, 0.5, None)


def head_of_reservoir(i, storage):
    """库容-水头线性近似"""
    ratio = (storage - S_MIN[i]) / (S_MAX[i] - S_MIN[i])
    ratio = np.clip(ratio, 0.0, 1.0)
    return H_MIN[i] + ratio * (H_MAX[i] - H_MIN[i])


def step_dynamics(storage_prev, release_cmd, inflow_t):
    """
    梯级单步状态转移：
    - 上游出流（发电下泄+弃水）进入下游
    - 保证不低于死库容，超上限部分记为弃水
    """
    storage_next = storage_prev.copy()
    release_real = np.zeros(N_RES)
    spill = np.zeros(N_RES)
    power = np.zeros(N_RES)

    upstream_out = 0.0
    for i in range(N_RES):
        q_in = inflow_t[i] + upstream_out

        # 指令下泄先受机组能力边界约束
        r = np.clip(release_cmd[i], R_MIN[i], R_MAX[i])

        # 可用水量约束：不得跌破死库容
        max_release = max(0.0, storage_next[i] + q_in - S_MIN[i])
        r = min(r, max_release)

        s_temp = storage_next[i] + q_in - r

        # 超库容上限部分记为弃水
        sp = max(0.0, s_temp - S_MAX[i])
        s_temp -= sp

        h = head_of_reservoir(i, 0.5 * (storage_next[i] + s_temp))
        p = K_POWER[i] * r * h

        storage_next[i] = s_temp
        release_real[i] = r
        spill[i] = sp
        power[i] = p

        # 梯级下传的是总出流（下泄+弃水）
        upstream_out = r + sp

    return storage_next, release_real, spill, power


def compute_cost(metrics):
    """统一综合成本（越小越好）"""
    return (
        -metrics["energy"]
        + 25.0 * metrics["eco_deficit"]
        + 2.0 * metrics["load_dev"]
        + 6.0 * metrics["spill"]
        + 12.0 * metrics["terminal_dev"]
        + 0.03 * metrics["smooth"]
    )


def simulate_system(command_plan, inflow, load, collect_traj=True):
    """给定全时段调度指令，完成系统仿真并计算KPI"""
    t_len = command_plan.shape[0]
    storage = np.zeros((t_len + 1, N_RES))
    storage[0] = S_INIT

    release = np.zeros((t_len, N_RES))
    spill = np.zeros((t_len, N_RES))
    power = np.zeros((t_len, N_RES))
    total_power = np.zeros(t_len)

    energy = 0.0
    eco_deficit = 0.0
    spill_sum = 0.0
    load_abs_sum = 0.0
    smooth = 0.0
    reliable_days = 0

    prev_r = None
    s = S_INIT.copy()

    for t in range(t_len):
        s_next, r, sp, p = step_dynamics(s, command_plan[t], inflow[:, t])

        tp = np.sum(p)
        energy += tp
        eco_deficit += np.sum(np.maximum(0.0, ECO_FLOW - r))
        spill_sum += np.sum(sp)
        load_abs_sum += abs(tp - load[t])

        if prev_r is not None:
            smooth += np.sum((r - prev_r) ** 2)
        prev_r = r.copy()

        if tp >= 0.90 * load[t]:
            reliable_days += 1

        storage[t + 1] = s_next
        release[t] = r
        spill[t] = sp
        power[t] = p
        total_power[t] = tp
        s = s_next

    terminal_dev = float(np.sum(np.abs(storage[-1] - S_TARGET)))
    metrics = {
        "energy": float(energy),
        "eco_deficit": float(eco_deficit),
        "load_dev": float(load_abs_sum / t_len),
        "spill": float(spill_sum),
        "terminal_dev": terminal_dev,
        "smooth": float(smooth),
        "reliability": float(100.0 * reliable_days / t_len),
    }
    metrics["cost"] = float(compute_cost(metrics))

    if not collect_traj:
        return {"metrics": metrics}

    return {
        "storage": storage,
        "release": release,
        "spill_ts": spill,
        "power": power,
        "total_power": total_power,
        "metrics": metrics,
    }


def decode_gene(gene):
    """将[0,1]基因映射为实际下泄指令"""
    u = gene.reshape(T, N_RES)
    return R_MIN + u * (R_MAX - R_MIN)


def nearest_grid_idx(x, x_min, x_max, n):
    """均匀网格最近索引"""
    if x <= x_min:
        return 0
    if x >= x_max:
        return n - 1
    return int(np.round((x - x_min) / (x_max - x_min) * (n - 1)))


def run_dp(inflow, load):
    """三库离散近似DP（加权单目标）"""
    n_s = DP_STATE_GRID
    n_a = DP_ACTION_GRID

    state_grids = [np.linspace(S_MIN[i], S_MAX[i], n_s) for i in range(N_RES)]
    action_grids = [np.linspace(R_MIN[i], R_MAX[i], n_a) for i in range(N_RES)]

    # 动作组合预生成
    action_combos = []
    for a0 in range(n_a):
        for a1 in range(n_a):
            for a2 in range(n_a):
                cmd = np.array([action_grids[0][a0], action_grids[1][a1], action_grids[2][a2]])
                action_combos.append((a0, a1, a2, cmd))

    value = np.full((T + 1, n_s, n_s, n_s), -1e18, dtype=float)
    policy = np.zeros((T, n_s, n_s, n_s, 3), dtype=np.int16)

    # 终端价值：靠近期末目标库容
    for i0 in range(n_s):
        s0 = state_grids[0][i0]
        for i1 in range(n_s):
            s1 = state_grids[1][i1]
            for i2 in range(n_s):
                s2 = state_grids[2][i2]
                term = np.abs(np.array([s0, s1, s2]) - S_TARGET).sum()
                value[T, i0, i1, i2] = -DP_W_TERM * term

    # 逆序递推
    for t in range(T - 1, -1, -1):
        for i0 in range(n_s):
            s0 = state_grids[0][i0]
            for i1 in range(n_s):
                s1 = state_grids[1][i1]
                for i2 in range(n_s):
                    s2 = state_grids[2][i2]
                    s_now = np.array([s0, s1, s2])

                    best_v = -1e18
                    best_a = (0, 0, 0)

                    for a0, a1, a2, cmd in action_combos:
                        s_next, r, sp, p = step_dynamics(s_now, cmd, inflow[:, t])

                        stage_reward = (
                            np.sum(p)
                            - DP_W_ECO * np.sum(np.maximum(0.0, ECO_FLOW - r))
                            - DP_W_LOAD * abs(np.sum(p) - load[t])
                            - DP_W_SPILL * np.sum(sp)
                        )

                        j0 = nearest_grid_idx(s_next[0], S_MIN[0], S_MAX[0], n_s)
                        j1 = nearest_grid_idx(s_next[1], S_MIN[1], S_MAX[1], n_s)
                        j2 = nearest_grid_idx(s_next[2], S_MIN[2], S_MAX[2], n_s)

                        v = stage_reward + DP_GAMMA * value[t + 1, j0, j1, j2]
                        if v > best_v:
                            best_v = v
                            best_a = (a0, a1, a2)

                    value[t, i0, i1, i2] = best_v
                    policy[t, i0, i1, i2] = best_a

    # 前向回放得到DP调度指令
    cmd_plan = np.zeros((T, N_RES))
    s = S_INIT.copy()
    for t in range(T):
        i0 = nearest_grid_idx(s[0], S_MIN[0], S_MAX[0], n_s)
        i1 = nearest_grid_idx(s[1], S_MIN[1], S_MAX[1], n_s)
        i2 = nearest_grid_idx(s[2], S_MIN[2], S_MAX[2], n_s)

        a0, a1, a2 = policy[t, i0, i1, i2]
        cmd = np.array([action_grids[0][a0], action_grids[1][a1], action_grids[2][a2]])
        cmd_plan[t] = cmd

        s, _, _, _ = step_dynamics(s, cmd, inflow[:, t])

    result = simulate_system(cmd_plan, inflow, load, collect_traj=True)
    result["command_plan"] = cmd_plan
    return result


def dominates(a, b):
    """最小化问题支配关系"""
    return np.all(a <= b) and np.any(a < b)


def fast_non_dominated_sort(objs):
    """快速非支配排序"""
    n = objs.shape[0]
    S = [[] for _ in range(n)]
    n_dom = np.zeros(n, dtype=int)
    rank = np.zeros(n, dtype=int)
    fronts = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominates(objs[p], objs[q]):
                S[p].append(q)
            elif dominates(objs[q], objs[p]):
                n_dom[p] += 1
        if n_dom[p] == 0:
            rank[p] = 0
            fronts[0].append(p)

    i = 0
    while len(fronts[i]) > 0:
        nxt = []
        for p in fronts[i]:
            for q in S[p]:
                n_dom[q] -= 1
                if n_dom[q] == 0:
                    rank[q] = i + 1
                    nxt.append(q)
        i += 1
        fronts.append(nxt)

    fronts.pop()
    return fronts, rank


def crowding_distance_all(objs, fronts):
    """计算各层拥挤度距离"""
    crowd = np.zeros(objs.shape[0])

    for front in fronts:
        if len(front) == 0:
            continue
        if len(front) <= 2:
            crowd[front] = np.inf
            continue

        fvals = objs[front]
        dist = np.zeros(len(front))

        for m in range(objs.shape[1]):
            order = np.argsort(fvals[:, m])
            dist[order[0]] = np.inf
            dist[order[-1]] = np.inf

            fmin = fvals[order[0], m]
            fmax = fvals[order[-1], m]
            if abs(fmax - fmin) < 1e-12:
                continue

            for k in range(1, len(front) - 1):
                if np.isinf(dist[order[k]]):
                    continue
                dist[order[k]] += (fvals[order[k + 1], m] - fvals[order[k - 1], m]) / (fmax - fmin)

        for local_idx, global_idx in enumerate(front):
            crowd[global_idx] = dist[local_idx]

    return crowd


def tournament_select_index(rng, rank, crowd):
    """锦标赛选择：先比等级，再比拥挤度"""
    i, j = rng.integers(0, len(rank), size=2)
    if rank[i] < rank[j]:
        return i
    if rank[i] > rank[j]:
        return j
    if crowd[i] > crowd[j]:
        return i
    if crowd[i] < crowd[j]:
        return j
    return i if rng.random() < 0.5 else j


def evaluate_gene(gene, inflow, load):
    """NSGA-II个体评价（双目标）"""
    cmd = decode_gene(gene)
    sim = simulate_system(cmd, inflow, load, collect_traj=False)
    m = sim["metrics"]

    # 目标1：发电最大 -> 最小化(-energy)
    obj1 = -m["energy"]

    # 目标2：生态+负荷+弃水+末期偏差综合风险最小
    obj2 = m["eco_deficit"] + 0.9 * m["load_dev"] + 0.7 * m["spill"] + 0.8 * m["terminal_dev"]
    return np.array([obj1, obj2], dtype=float)


def run_nsga2(inflow, load, seed=1234):
    """带精英保留策略的NSGA-II"""
    rng = np.random.default_rng(seed)

    dim = T * N_RES
    pop = rng.random((NSGA_POP, dim))
    objs = np.array([evaluate_gene(ind, inflow, load) for ind in pop])

    for _ in range(NSGA_GEN):
        fronts, rank = fast_non_dominated_sort(objs)
        crowd = crowding_distance_all(objs, fronts)

        # 生成子代
        offspring = np.zeros_like(pop)
        for k in range(0, NSGA_POP, 2):
            p1 = pop[tournament_select_index(rng, rank, crowd)]
            p2 = pop[tournament_select_index(rng, rank, crowd)]

            if rng.random() < NSGA_PC:
                alpha = rng.random(dim)
                c1 = alpha * p1 + (1.0 - alpha) * p2
                c2 = alpha * p2 + (1.0 - alpha) * p1
            else:
                c1 = p1.copy()
                c2 = p2.copy()

            # 高斯变异
            m1 = rng.random(dim) < NSGA_PM
            m2 = rng.random(dim) < NSGA_PM
            c1[m1] += rng.normal(0.0, NSGA_SIGMA, size=np.sum(m1))
            c2[m2] += rng.normal(0.0, NSGA_SIGMA, size=np.sum(m2))
            np.clip(c1, 0.0, 1.0, out=c1)
            np.clip(c2, 0.0, 1.0, out=c2)

            offspring[k] = c1
            if k + 1 < NSGA_POP:
                offspring[k + 1] = c2

        off_objs = np.array([evaluate_gene(ind, inflow, load) for ind in offspring])

        # 父代+子代，按等级+拥挤度精英保留
        comb_pop = np.vstack([pop, offspring])
        comb_objs = np.vstack([objs, off_objs])

        comb_fronts, _ = fast_non_dominated_sort(comb_objs)
        comb_crowd = crowding_distance_all(comb_objs, comb_fronts)

        new_indices = []
        for front in comb_fronts:
            if len(new_indices) + len(front) <= NSGA_POP:
                new_indices.extend(front)
            else:
                remain = NSGA_POP - len(new_indices)
                order = sorted(front, key=lambda idx: comb_crowd[idx], reverse=True)
                new_indices.extend(order[:remain])
                break

        pop = comb_pop[new_indices]
        objs = comb_objs[new_indices]

    # 最终Pareto前沿
    fronts, _ = fast_non_dominated_sort(objs)
    pareto_idx = fronts[0]
    pareto_objs = objs[pareto_idx]

    # 从Pareto集中选折中解（归一化后到理想点的L1距离最小）
    mins = pareto_objs.min(axis=0)
    spans = np.maximum(pareto_objs.max(axis=0) - mins, 1e-12)
    norm = (pareto_objs - mins) / spans
    compromise_local = int(np.argmin(np.sum(norm, axis=1)))
    best_global_idx = pareto_idx[compromise_local]

    best_gene = pop[best_global_idx]
    best_cmd = decode_gene(best_gene)
    best_result = simulate_system(best_cmd, inflow, load, collect_traj=True)
    best_result["command_plan"] = best_cmd

    chosen_obj = objs[best_global_idx]
    return best_result, pareto_objs, chosen_obj


def simulate_horizon_from_state(s0, cmd_seq, inflow_seq, load_seq):
    """MPC预测期滚动仿真（用于优化目标计算）"""
    s = s0.copy()
    energy = 0.0
    eco = 0.0
    spill = 0.0
    load_abs = 0.0

    h_len = cmd_seq.shape[0]
    for h in range(h_len):
        s, r, sp, p = step_dynamics(s, cmd_seq[h], inflow_seq[:, h])
        energy += np.sum(p)
        eco += np.sum(np.maximum(0.0, ECO_FLOW - r))
        spill += np.sum(sp)
        load_abs += abs(np.sum(p) - load_seq[h])

    terminal = np.sum(np.abs(s - S_TARGET))
    return energy, eco, spill, load_abs, terminal


def run_mpc(inflow_true, load, inflow_forecast):
    """模型预测控制：滚动优化 + 实时反馈"""
    cmd_plan = np.zeros((T, N_RES))
    s_now = S_INIT.copy()

    for t in range(T):
        hp = min(MPC_HP, T - t)
        inflow_h = inflow_forecast[:, t:t + hp]
        load_h = load[t:t + hp]

        def obj(x):
            u = x.reshape(hp, N_RES)
            cmd_seq = R_MIN + u * (R_MAX - R_MIN)
            energy, eco, sp, load_abs, terminal = simulate_horizon_from_state(s_now, cmd_seq, inflow_h, load_h)
            return (
                -energy
                + MPC_W_ECO * eco
                + MPC_W_LOAD * (load_abs / hp)
                + MPC_W_SPILL * sp
                + MPC_W_TERM * terminal
            )

        x0 = np.full(hp * N_RES, 0.5)
        bds = [(0.0, 1.0)] * (hp * N_RES)
        res = minimize(
            obj,
            x0,
            method="SLSQP",
            bounds=bds,
            options={"maxiter": 80, "ftol": 1e-4, "disp": False},
        )

        x_best = res.x if res.success else x0
        cmd_now = R_MIN + x_best.reshape(hp, N_RES)[0] * (R_MAX - R_MIN)
        cmd_plan[t] = cmd_now

        # 仅执行第一步，再用实测状态反馈修正
        s_now, _, _, _ = step_dynamics(s_now, cmd_now, inflow_true[:, t])

    result = simulate_system(cmd_plan, inflow_true, load, collect_traj=True)
    result["command_plan"] = cmd_plan
    return result


def print_kpi_table(result_dict):
    """打印KPI结果表格"""
    print("\nKPI结果表（总发电量越大越好，其余指标越小越好）")
    header = (
        f"{'算法':<10}"
        f"{'总发电量':>12}"
        f"{'生态缺水':>12}"
        f"{'负荷偏差':>12}"
        f"{'总弃水':>10}"
        f"{'末期偏差':>12}"
        f"{'可靠率%':>10}"
        f"{'综合成本':>12}"
    )
    print(header)
    print("-" * len(header))

    for name, res in result_dict.items():
        m = res["metrics"]
        line = (
            f"{name:<10}"
            f"{m['energy']:>12.2f}"
            f"{m['eco_deficit']:>12.2f}"
            f"{m['load_dev']:>12.2f}"
            f"{m['spill']:>10.2f}"
            f"{m['terminal_dev']:>12.2f}"
            f"{m['reliability']:>10.2f}"
            f"{m['cost']:>12.2f}"
        )
        print(line)


def plot_results(inflow, load, dp_res, nsga_res, mpc_res, pareto_objs, chosen_obj):
    """绘制调度对比图 + Pareto前沿"""
    days = np.arange(1, T + 1)
    days_s = np.arange(0, T + 1)

    fig, ax = plt.subplots(2, 2, figsize=(14, 10))

    # 图1：总出力与负荷
    ax[0, 0].plot(days, load, color="#222222", linewidth=2.2, label="系统负荷")
    ax[0, 0].plot(days, dp_res["total_power"], "--", color="#1f77b4", label="DP总出力")
    ax[0, 0].plot(days, nsga_res["total_power"], "-.", color="#ff7f0e", label="NSGA-II总出力")
    ax[0, 0].plot(days, mpc_res["total_power"], "-", color="#2ca02c", label="MPC总出力")
    ax[0, 0].set_title("总出力-负荷对比")
    ax[0, 0].set_xlabel("时段")
    ax[0, 0].set_ylabel("相对出力")
    ax[0, 0].legend()

    # 图2：上游控制库库容轨迹
    ax[0, 1].plot(days_s, dp_res["storage"][:, 0], "--", color="#1f77b4", label="DP")
    ax[0, 1].plot(days_s, nsga_res["storage"][:, 0], "-.", color="#ff7f0e", label="NSGA-II")
    ax[0, 1].plot(days_s, mpc_res["storage"][:, 0], "-", color="#2ca02c", label="MPC")
    ax[0, 1].axhline(S_MIN[0], color="gray", linestyle=":")
    ax[0, 1].axhline(S_MAX[0], color="gray", linestyle=":")
    ax[0, 1].set_title(f"{RES_NAMES[0]}库容轨迹")
    ax[0, 1].set_xlabel("时段")
    ax[0, 1].set_ylabel("库容")
    ax[0, 1].legend()

    # 图3：下游控制库库容轨迹
    ax[1, 0].plot(days_s, dp_res["storage"][:, 2], "--", color="#1f77b4", label="DP")
    ax[1, 0].plot(days_s, nsga_res["storage"][:, 2], "-.", color="#ff7f0e", label="NSGA-II")
    ax[1, 0].plot(days_s, mpc_res["storage"][:, 2], "-", color="#2ca02c", label="MPC")
    ax[1, 0].axhline(S_MIN[2], color="gray", linestyle=":")
    ax[1, 0].axhline(S_MAX[2], color="gray", linestyle=":")
    ax[1, 0].set_title(f"{RES_NAMES[2]}库容轨迹")
    ax[1, 0].set_xlabel("时段")
    ax[1, 0].set_ylabel("库容")
    ax[1, 0].legend()

    # 图4：NSGA-II Pareto前沿
    pareto_energy = -pareto_objs[:, 0]
    pareto_risk = pareto_objs[:, 1]
    chosen_energy = -chosen_obj[0]
    chosen_risk = chosen_obj[1]

    ax[1, 1].scatter(pareto_risk, pareto_energy, s=24, c="#7f7f7f", alpha=0.8, label="Pareto解集")
    ax[1, 1].scatter(chosen_risk, chosen_energy, s=90, c="red", marker="*", label="折中解")
    ax[1, 1].set_title("NSGA-II Pareto前沿")
    ax[1, 1].set_xlabel("综合风险目标（越小越好）")
    ax[1, 1].set_ylabel("总发电量目标（越大越好）")
    ax[1, 1].legend()

    plt.tight_layout()
    plt.show()


def main():
    # 1) 构造来水与负荷
    inflow_true, load = generate_series(T, seed=2026)
    inflow_forecast = build_forecast_inflow(inflow_true, seed=7)

    # 2) 三种算法求解
    dp_res = run_dp(inflow_true, load)
    nsga_res, pareto_objs, chosen_obj = run_nsga2(inflow_true, load, seed=1234)
    mpc_res = run_mpc(inflow_true, load, inflow_forecast)

    # 3) KPI结果表
    result_dict = {"DP": dp_res, "NSGA-II": nsga_res, "MPC": mpc_res}
    print_kpi_table(result_dict)

    # 4) 绘图
    plot_results(inflow_true, load, dp_res, nsga_res, mpc_res, pareto_objs, chosen_obj)


if __name__ == "__main__":
    main()
```

这份代码的核心价值，是把第8章“多水库联合调度”里三种不同求解架构放进同一个可复现实验平台，避免“模型不同导致算法不可比”的常见问题。脚本先用同一组三级串联水库参数、同一段来水和同一负荷曲线，构建统一的水量平衡与出力计算逻辑：每个时段都按“来水+上游出流进入本库、下泄受机组与死库容约束、超上限形成弃水、由库容反推水头再算发电”这一物理过程推进。这样，DP、NSGA-II、MPC虽然决策机制不同，但评价口径一致。  
DP部分采用离散状态与离散动作的逆序递推，直接体现贝尔曼最优性思想。它把三库库容离散成网格、把三库下泄离散成动作组合，在每个阶段计算“发电收益-生态缺水惩罚-负荷偏差惩罚-弃水惩罚”，并叠加未来价值函数，最后通过前向回放得到完整调度序列。这个实现反映了DP在确定性全局寻优上的优势，也直观展示了维度上升后计算量快速放大的特征。  
NSGA-II部分保留了“快速非支配排序+拥挤度距离+精英保留”的标准结构。个体编码为全时段三库下泄基因，目标一是最大化发电（用最小化负发电量实现），目标二是最小化生态-负荷-弃水-末期偏差综合风险。算法不强行给出单一最优点，而是输出Pareto前沿，再从前沿中按归一化距离选折中方案。对应教学上“多目标权衡”这件事，图中的前沿曲线比单个数字更有解释力。  
MPC部分体现“预测-优化-执行第一步-状态反馈-滚动重算”的闭环思想。脚本刻意给预测来水加入偏差，让MPC在不确定条件下迭代修正，这正是其相对开环策略的工程价值。每个时段只优化有限预测窗，兼顾实时性与鲁棒性。  
KPI表中统一输出总发电、生态缺水、负荷偏差、弃水、末期偏差、可靠率和综合成本；图形则给出总出力跟踪、关键库容轨迹和Pareto前沿。由此可以一眼看出三类方法的适用边界：DP偏向确定性全局最优基准，NSGA-II擅长多目标折中与决策支持，MPC适合在线运行和应对预报误差。

## 参考文献

1. Bellman, R. (1957). *Dynamic Programming*. Princeton University Press.
2. Yeh, W. W.-G. (1985). Reservoir Management and Operations Models: A State-of-the-Art Review. *Water Resources Research*, 21(12), 1797-1818.
3. Labadie, J. W. (2004). Optimal Operation of Multireservoir Systems: State-of-the-Art Review. *Journal of Water Resources Planning and Management*, 130(2), 93-111.
4. Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077
