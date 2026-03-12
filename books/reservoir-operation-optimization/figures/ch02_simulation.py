# -*- coding: utf-8 -*-
"""
教材：《水库调度优化与决策》
章节：第2章 单库DP/SDP优化（2.1 基本概念与理论框架）
功能：构建单库确定性动态规划(DP)与随机动态规划(SDP)仿真，
      打印KPI结果表格，并生成matplotlib对比图。
"""

import numpy as np
from scipy.interpolate import interp1d
from scipy.linalg import eig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（可直接改这里）
# =========================
RANDOM_SEED = 2026
T = 12  # 时段数（月）

# 库容边界与初末条件
S_MIN = 10.0
S_MAX = 100.0
S0 = 50.0
S_END_TARGET = 50.0

# 离散网格
N_STORAGE = 91
N_RELEASE = 101

# 下泄能力与机组能力
R_MIN = 0.0
R_MAX = 25.0
R_TURBINE_MAX = 22.0

# 收益与惩罚系数
ETA = 0.88
HEAD_BASE = 18.0
HEAD_K = 0.08
POWER_COEF = 9.81e-3
W_SHORTAGE = 4.0
W_SPILL = 1.2
W_END_STORAGE = 2.0

# SDP蒙特卡洛评估场景数
N_MC = 500

# 图像参数
SAVE_FIG = True
FIG_PATH = "ch02_single_reservoir_dp_sdp.png"

# 中文绘图设置
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 需求过程（可换为实测）
months = np.arange(1, T + 1)
DEMAND = 12.0 + 2.0 * np.sin(2 * np.pi * (months - 1) / 12 + np.pi / 6)

# 确定性入流（DP用）
INFLOW_DET = 14.0 + 6.0 * np.sin(2 * np.pi * (months - 3) / 12) + 2.0 * np.cos(2 * np.pi * months / 6)
INFLOW_DET = np.clip(INFLOW_DET, 3.0, 30.0)

# SDP离散入流状态与转移矩阵（枯-平-丰）
INFLOW_STATES = np.array([8.0, 14.0, 22.0])
P_TRANS = np.array([
    [0.65, 0.30, 0.05],
    [0.25, 0.55, 0.20],
    [0.10, 0.35, 0.55]
])


def terminal_value(storage):
    """期末偏离目标库容的惩罚项。"""
    return -W_END_STORAGE * (storage - S_END_TARGET) ** 2


def reservoir_step(storage, release_cmd, inflow, demand):
    """
    单步水量平衡与收益计算。
    状态转移：S_{t+1} = S_t + I_t - R_t - Spill_t
    """
    # 可行下泄上限：既受工程上限约束，也受不跌破死库容约束
    r_feasible_max = max(R_MIN, min(R_MAX, storage + inflow - S_MIN))
    release = float(np.clip(release_cmd, R_MIN, r_feasible_max))

    s_next_raw = storage + inflow - release
    spill = max(0.0, s_next_raw - S_MAX)
    s_next = s_next_raw - spill

    # 发电收益（简化表达）
    head = HEAD_BASE + HEAD_K * 0.5 * (storage + s_next)
    turbine_flow = min(release, R_TURBINE_MAX)
    energy = ETA * POWER_COEF * turbine_flow * head

    # 缺水惩罚
    shortage = max(0.0, demand - release)

    reward = energy - W_SHORTAGE * shortage ** 2 - W_SPILL * spill ** 2
    return reward, s_next, spill, energy, shortage, release


def solve_dp(storage_grid, release_grid):
    """确定性DP逆序求解。"""
    n_s = len(storage_grid)
    V = np.full((T + 1, n_s), -1e18)
    policy = np.zeros((T, n_s))
    V[T, :] = terminal_value(storage_grid)

    for t in range(T - 1, -1, -1):
        v_next_interp = interp1d(
            storage_grid, V[t + 1, :], kind="linear",
            bounds_error=False, fill_value="extrapolate", assume_sorted=True
        )
        q_t = INFLOW_DET[t]
        d_t = DEMAND[t]

        for i, s_t in enumerate(storage_grid):
            r_max_state = max(R_MIN, min(R_MAX, s_t + q_t - S_MIN))
            feasible = release_grid[release_grid <= r_max_state + 1e-12]
            if feasible.size == 0:
                feasible = np.array([R_MIN])

            best_val = -1e18
            best_r = R_MIN

            for r_t in feasible:
                reward, s_next, *_ = reservoir_step(s_t, r_t, q_t, d_t)
                val = reward + float(v_next_interp(s_next))
                if val > best_val:
                    best_val = val
                    best_r = r_t

            V[t, i] = best_val
            policy[t, i] = best_r

    return V, policy


def solve_sdp(storage_grid, release_grid):
    """随机DP逆序求解，状态为(S_t, I_t)。"""
    n_s = len(storage_grid)
    n_q = len(INFLOW_STATES)
    V = np.full((T + 1, n_s, n_q), -1e18)
    policy = np.zeros((T, n_s, n_q))

    end_v = terminal_value(storage_grid)
    for iq in range(n_q):
        V[T, :, iq] = end_v

    for t in range(T - 1, -1, -1):
        v_next_interps = [
            interp1d(
                storage_grid, V[t + 1, :, jq], kind="linear",
                bounds_error=False, fill_value="extrapolate", assume_sorted=True
            ) for jq in range(n_q)
        ]
        d_t = DEMAND[t]

        for iq, q_t in enumerate(INFLOW_STATES):
            for i, s_t in enumerate(storage_grid):
                r_max_state = max(R_MIN, min(R_MAX, s_t + q_t - S_MIN))
                feasible = release_grid[release_grid <= r_max_state + 1e-12]
                if feasible.size == 0:
                    feasible = np.array([R_MIN])

                best_val = -1e18
                best_r = R_MIN

                for r_t in feasible:
                    reward, s_next, *_ = reservoir_step(s_t, r_t, q_t, d_t)

                    # 条件期望余留价值
                    exp_future = 0.0
                    for jq in range(n_q):
                        exp_future += P_TRANS[iq, jq] * float(v_next_interps[jq](s_next))

                    val = reward + exp_future
                    if val > best_val:
                        best_val = val
                        best_r = r_t

                V[t, i, iq] = best_val
                policy[t, i, iq] = best_r

    return V, policy


def stationary_distribution(P):
    """由特征值法计算马尔可夫链平稳分布。"""
    vals, vecs = eig(P.T)
    idx = np.argmin(np.abs(vals - 1.0))
    v = np.real(vecs[:, idx])
    v = np.maximum(v, 0.0)
    if v.sum() < 1e-12:
        v = np.ones(P.shape[0])
    return v / v.sum()


def sample_inflow_path(rng):
    """按马尔可夫链采样一条入流状态路径。"""
    n_q = len(INFLOW_STATES)
    pi = stationary_distribution(P_TRANS)
    q_idx = np.zeros(T, dtype=int)
    q_idx[0] = rng.choice(n_q, p=pi)
    for t in range(1, T):
        q_idx[t] = rng.choice(n_q, p=P_TRANS[q_idx[t - 1], :])
    return q_idx, INFLOW_STATES[q_idx]


def simulate_dp(storage_grid, policy):
    """DP策略前向仿真。"""
    s = np.zeros(T + 1)
    r = np.zeros(T)
    spill = np.zeros(T)
    energy = np.zeros(T)
    shortage = np.zeros(T)
    reward_sum = 0.0

    s[0] = S0
    for t in range(T):
        pol_interp = interp1d(
            storage_grid, policy[t, :], kind="linear",
            bounds_error=False, fill_value="extrapolate", assume_sorted=True
        )
        r_cmd = float(pol_interp(s[t]))
        rew, s[t + 1], spill[t], energy[t], shortage[t], r[t] = reservoir_step(s[t], r_cmd, INFLOW_DET[t], DEMAND[t])
        reward_sum += rew

    reward_sum += terminal_value(s[-1])
    return {
        "name": "DP(确定)",
        "storage": s,
        "release": r,
        "spill": spill,
        "energy": energy,
        "shortage": shortage,
        "reward": reward_sum,
        "inflow": INFLOW_DET.copy()
    }


def simulate_sdp_once(storage_grid, policy, rng):
    """SDP策略在一条随机入流样本上的前向仿真。"""
    q_idx, inflow_path = sample_inflow_path(rng)

    s = np.zeros(T + 1)
    r = np.zeros(T)
    spill = np.zeros(T)
    energy = np.zeros(T)
    shortage = np.zeros(T)
    reward_sum = 0.0

    s[0] = S0
    for t in range(T):
        iq = q_idx[t]
        pol_interp = interp1d(
            storage_grid, policy[t, :, iq], kind="linear",
            bounds_error=False, fill_value="extrapolate", assume_sorted=True
        )
        r_cmd = float(pol_interp(s[t]))
        rew, s[t + 1], spill[t], energy[t], shortage[t], r[t] = reservoir_step(s[t], r_cmd, inflow_path[t], DEMAND[t])
        reward_sum += rew

    reward_sum += terminal_value(s[-1])
    return {
        "name": "SDP(随机样本)",
        "storage": s,
        "release": r,
        "spill": spill,
        "energy": energy,
        "shortage": shortage,
        "reward": reward_sum,
        "inflow": inflow_path
    }


def build_kpi(result):
    """计算单次仿真的KPI。"""
    reliability = 100.0 * np.mean(result["shortage"] <= 1e-6)
    return {
        "方案": result["name"],
        "目标函数值": result["reward"],
        "总发电收益": np.sum(result["energy"]),
        "供水保证率(%)": reliability,
        "总弃水量": np.sum(result["spill"]),
        "期末库容": result["storage"][-1]
    }


def evaluate_sdp_mc(storage_grid, policy, n_mc, rng):
    """蒙特卡洛评估SDP策略期望性能。"""
    obj_list, en_list, rel_list, spill_list, end_s_list = [], [], [], [], []
    sample_result = None

    for k in range(n_mc):
        res = simulate_sdp_once(storage_grid, policy, rng)
        if k == 0:
            sample_result = res
        obj_list.append(res["reward"])
        en_list.append(np.sum(res["energy"]))
        rel_list.append(100.0 * np.mean(res["shortage"] <= 1e-6))
        spill_list.append(np.sum(res["spill"]))
        end_s_list.append(res["storage"][-1])

    kpi = {
        "方案": f"SDP(随机,MC均值 n={n_mc})",
        "目标函数值": float(np.mean(obj_list)),
        "总发电收益": float(np.mean(en_list)),
        "供水保证率(%)": float(np.mean(rel_list)),
        "总弃水量": float(np.mean(spill_list)),
        "期末库容": float(np.mean(end_s_list))
    }
    return kpi, sample_result


def print_kpi_table(kpi_rows):
    """打印Markdown风格KPI表格。"""
    headers = ["方案", "目标函数值", "总发电收益", "供水保证率(%)", "总弃水量", "期末库容"]
    print("\nKPI结果表")
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in kpi_rows:
        print(
            f"| {row['方案']} | "
            f"{row['目标函数值']:.3f} | "
            f"{row['总发电收益']:.3f} | "
            f"{row['供水保证率(%)']:.2f} | "
            f"{row['总弃水量']:.3f} | "
            f"{row['期末库容']:.3f} |"
        )


def plot_results(dp_res, sdp_sample, storage_grid, sdp_policy):
    """绘制对比图。"""
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), dpi=130)

    # 入流对比
    axes[0, 0].plot(months, dp_res["inflow"], "-o", label="DP入流(确定)")
    axes[0, 0].plot(months, sdp_sample["inflow"], "-s", label="SDP入流(随机样本)")
    axes[0, 0].plot(months, DEMAND, "--", color="black", label="供水需求")
    axes[0, 0].set_title("入流与需求")
    axes[0, 0].set_xlabel("月份")
    axes[0, 0].set_ylabel("流量")
    axes[0, 0].grid(alpha=0.3)
    axes[0, 0].legend()

    # 库容过程
    axes[0, 1].plot(np.arange(T + 1), dp_res["storage"], "-o", label="DP库容")
    axes[0, 1].plot(np.arange(T + 1), sdp_sample["storage"], "-s", label="SDP库容(随机样本)")
    axes[0, 1].axhline(S_MIN, color="k", linestyle="--", linewidth=1, label="Smin/Smax")
    axes[0, 1].axhline(S_MAX, color="k", linestyle="--", linewidth=1)
    axes[0, 1].axhline(S_END_TARGET, color="tab:green", linestyle=":", linewidth=1.2, label="期末目标库容")
    axes[0, 1].set_title("库容轨迹")
    axes[0, 1].set_xlabel("时段")
    axes[0, 1].set_ylabel("库容")
    axes[0, 1].grid(alpha=0.3)
    axes[0, 1].legend()

    # 下泄过程
    axes[1, 0].plot(months, DEMAND, "--", color="black", label="需求")
    axes[1, 0].plot(months, dp_res["release"], "-o", label="DP下泄")
    axes[1, 0].plot(months, sdp_sample["release"], "-s", label="SDP下泄(随机样本)")
    axes[1, 0].set_title("下泄-需求对比")
    axes[1, 0].set_xlabel("月份")
    axes[1, 0].set_ylabel("流量")
    axes[1, 0].grid(alpha=0.3)
    axes[1, 0].legend()

    # SDP策略切片（t=1）
    t_show = 0
    for iq, q in enumerate(INFLOW_STATES):
        axes[1, 1].plot(storage_grid, sdp_policy[t_show, :, iq], label=f"入流状态{iq+1} Q={q:.1f}")
    axes[1, 1].set_title("SDP策略切片 (t=1)")
    axes[1, 1].set_xlabel("期初库容")
    axes[1, 1].set_ylabel("最优下泄")
    axes[1, 1].grid(alpha=0.3)
    axes[1, 1].legend()

    fig.suptitle("第2章 单库DP/SDP优化仿真结果", fontsize=14)
    fig.tight_layout()

    if SAVE_FIG:
        fig.savefig(FIG_PATH, bbox_inches="tight")
        print(f"\n图像已保存：{FIG_PATH}")

    plt.savefig('ch02_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch02_simulation_result.png")
# plt.show()


def main():
    rng = np.random.default_rng(RANDOM_SEED)
    storage_grid = np.linspace(S_MIN, S_MAX, N_STORAGE)
    release_grid = np.linspace(R_MIN, R_MAX, N_RELEASE)

    # 逆序求解
    _, pol_dp = solve_dp(storage_grid, release_grid)
    _, pol_sdp = solve_sdp(storage_grid, release_grid)

    # 前向仿真与评估
    res_dp = simulate_dp(storage_grid, pol_dp)
    kpi_dp = build_kpi(res_dp)

    kpi_sdp_mean, sdp_sample = evaluate_sdp_mc(storage_grid, pol_sdp, N_MC, rng)

    # KPI表格
    print_kpi_table([kpi_dp, kpi_sdp_mean])

    # 绘图
    plot_results(res_dp, sdp_sample, storage_grid, pol_sdp)


if __name__ == "__main__":
    main()
