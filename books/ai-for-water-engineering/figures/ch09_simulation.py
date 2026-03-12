#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
书名：《人工智能与水利水电工程》
章节：第9章 强化学习：水库调度/闸门控制
功能：用Q-learning实现水库调度与闸门控制仿真，对比规则曲线法，输出KPI表格并绘图。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.stats import gamma as gamma_dist

# =========================
# 1) 关键参数定义（可直接调参）
# =========================
RANDOM_SEED = 2026

# 时间与训练参数
DT = 24 * 3600                     # 仿真步长：1天（秒）
SIM_DAYS = 180                     # 单次场景长度（天）
TRAIN_EPISODES = 1400              # 训练回合数
EVAL_EPISODES = 120                # 评估场景数

# 水库约束参数（单位：m3）
S_MIN = 50e6
S_MAX = 300e6
S_INIT = 180e6
S_SAFE = 260e6
S_TARGET = 200e6
LOW_BUFFER = 12e6                  # 死水位之上缓冲
EVAP_LOSS = 0.8e6                  # 每日蒸发渗漏损失

# 闸门与下泄参数（单位：m3/s）
R_MIN = 60.0
R_MAX = 1200.0
ACTIONS = np.array([80, 150, 230, 320, 430, 560, 700, 860, 1030, 1180], dtype=float)

# 需水参数（单位：m3/s）
DEMAND_BASE = 360.0
DEMAND_AMP = 120.0

# 奖励权重
W_POWER = 1.0
W_SHORTAGE = 11.0
W_FLOOD = 18.0
W_SPILL = 8.0
W_SMOOTH = 2.5
W_LOW = 7.0

# 发电参数
RHO_WATER = 1000.0
GRAVITY = 9.81
EFFICIENCY = 0.90
HEAD_BASE = 18.0
HEAD_COEF = 1.0e-7                 # 库容越高，水头越大（简化）

# Q-learning参数
ALPHA = 0.08
GAMMA = 0.97
EPS_START = 1.00
EPS_END = 0.05
EPS_DECAY = 450.0

# 状态离散参数
N_STORAGE_BINS = 12
N_INFLOW_BINS = 6
N_SEASON_BINS = 6

# 规则曲线参数（基线）
K_RULE = 1.8
PRE_RELEASE = 140.0


# =========================
# 2) 场景与环境
# =========================
def generate_inflow_series(days, rng):
    """生成来水序列：季节项 + Gamma随机扰动（单位：m3/s）"""
    t = np.arange(days)
    seasonal = 220.0 + 420.0 * np.sin(2 * np.pi * (t - 35) / days) ** 2
    noise = gamma_dist.rvs(a=2.5, scale=1 / 2.5, size=days, random_state=rng)  # 均值约1
    inflow = np.clip(seasonal * noise, 30.0, 3200.0)
    return inflow


def generate_demand_series(days):
    """生成需水序列（单位：m3/s）"""
    t = np.arange(days)
    demand = DEMAND_BASE + DEMAND_AMP * np.sin(2 * np.pi * (t + 12) / days)
    return np.clip(demand, 180.0, 520.0)


def build_inflow_edges():
    """用样本分位数构建来水离散边界"""
    rng = np.random.default_rng(RANDOM_SEED + 1)
    sample = np.concatenate([generate_inflow_series(SIM_DAYS, rng) for _ in range(200)])
    qs = np.linspace(0, 1, N_INFLOW_BINS + 1)[1:-1]
    return np.quantile(sample, qs)


STORAGE_EDGES = np.linspace(S_MIN, S_MAX, N_STORAGE_BINS + 1)[1:-1]
INFLOW_EDGES = build_inflow_edges()


def state_index(storage, inflow, day):
    """将连续状态映射到离散状态索引"""
    s_idx = int(np.digitize(storage, STORAGE_EDGES))
    i_idx = int(np.digitize(inflow, INFLOW_EDGES))
    season_idx = min(int(day / max(1, SIM_DAYS // N_SEASON_BINS)), N_SEASON_BINS - 1)
    return s_idx + N_STORAGE_BINS * (i_idx + N_INFLOW_BINS * season_idx)


def reservoir_step(storage, inflow_cms, release_cmd_cms, demand_cms, prev_release_cms):
    """一步状态转移 + 奖励计算"""
    inflow_vol = inflow_cms * DT

    # 可用水量限制：保证不跌破最小库容
    available = max(0.0, storage + inflow_vol - EVAP_LOSS - S_MIN)
    release_upper = min(R_MAX, available / DT)
    release = float(np.clip(release_cmd_cms, 0.0, release_upper))

    # 水量平衡
    next_storage_raw = storage + inflow_vol - release * DT - EVAP_LOSS
    spill = max(0.0, next_storage_raw - S_MAX)
    next_storage = np.clip(next_storage_raw - spill, S_MIN, S_MAX)

    # 约束偏差
    shortage = max(0.0, demand_cms - release)
    flood_excess = max(0.0, next_storage - S_SAFE)
    low_excess = max(0.0, (S_MIN + LOW_BUFFER) - next_storage)
    smooth = abs(release - prev_release_cms)

    # 简化水头与发电量
    head = HEAD_BASE + HEAD_COEF * (next_storage - S_MIN)
    energy_mwh = EFFICIENCY * RHO_WATER * GRAVITY * head * release * DT / 3.6e9

    # 奖励：发电收益 - 多类惩罚
    reward = (
        W_POWER * energy_mwh
        - W_SHORTAGE * (shortage / 100.0) ** 2
        - W_FLOOD * (flood_excess / 1e6) ** 2
        - W_SPILL * (spill / 1e6) ** 2
        - W_SMOOTH * (smooth / 100.0) ** 2
        - W_LOW * (low_excess / 1e6) ** 2
    )

    info = {
        "release": release,
        "spill": spill,
        "shortage": shortage,
        "energy_mwh": energy_mwh,
    }
    return next_storage, reward, info


def rule_curve_release(storage, demand, day):
    """规则曲线基线策略"""
    correction = K_RULE * (storage - S_TARGET) / 1e6
    flood_pre = PRE_RELEASE if (60 <= day <= 120 and storage > S_TARGET) else 0.0
    cmd = demand + correction + flood_pre
    return float(np.clip(cmd, R_MIN, R_MAX))


# =========================
# 3) Q-learning训练
# =========================
N_STATES = N_STORAGE_BINS * N_INFLOW_BINS * N_SEASON_BINS
N_ACTIONS = len(ACTIONS)


def train_q_learning():
    rng = np.random.default_rng(RANDOM_SEED + 2)
    q_table = np.zeros((N_STATES, N_ACTIONS), dtype=float)
    training_rewards = []

    for ep in range(TRAIN_EPISODES):
        inflow = generate_inflow_series(SIM_DAYS, rng)
        demand = generate_demand_series(SIM_DAYS)

        storage = S_INIT
        prev_release = DEMAND_BASE
        ep_reward = 0.0
        epsilon = EPS_END + (EPS_START - EPS_END) * np.exp(-ep / EPS_DECAY)

        for t in range(SIM_DAYS):
            s = state_index(storage, inflow[t], t)

            # epsilon-greedy动作选择
            if rng.random() < epsilon:
                a = int(rng.integers(N_ACTIONS))
            else:
                a = int(np.argmax(q_table[s]))

            cmd_release = ACTIONS[a]
            next_storage, reward, info = reservoir_step(
                storage, inflow[t], cmd_release, demand[t], prev_release
            )

            if t == SIM_DAYS - 1:
                target = reward
            else:
                s_next = state_index(next_storage, inflow[t + 1], t + 1)
                target = reward + GAMMA * np.max(q_table[s_next])

            q_table[s, a] += ALPHA * (target - q_table[s, a])

            storage = next_storage
            prev_release = info["release"]
            ep_reward += reward

        training_rewards.append(ep_reward)

    return q_table, np.array(training_rewards, dtype=float)


# =========================
# 4) 评估、KPI与绘图
# =========================
def simulate_episode(policy_name, q_table, inflow, demand):
    storage = S_INIT
    prev_release = DEMAND_BASE

    storage_trace = [storage]
    release_trace, reward_trace = [], []
    spill_trace, energy_trace, shortage_trace = [], [], []

    for t in range(SIM_DAYS):
        if policy_name == "rl":
            s = state_index(storage, inflow[t], t)
            action_id = int(np.argmax(q_table[s]))
            cmd_release = ACTIONS[action_id]
        else:
            cmd_release = rule_curve_release(storage, demand[t], t)

        next_storage, reward, info = reservoir_step(
            storage, inflow[t], cmd_release, demand[t], prev_release
        )

        release_trace.append(info["release"])
        reward_trace.append(reward)
        spill_trace.append(info["spill"])
        energy_trace.append(info["energy_mwh"])
        shortage_trace.append(info["shortage"])
        storage_trace.append(next_storage)

        storage = next_storage
        prev_release = info["release"]

    release_arr = np.array(release_trace)
    reward_arr = np.array(reward_trace)
    spill_arr = np.array(spill_trace)
    energy_arr = np.array(energy_trace)
    shortage_arr = np.array(shortage_trace)
    storage_arr = np.array(storage_trace)

    metrics = {
        "avg_reward": float(reward_arr.sum()),
        "supply_rate": float(np.mean(shortage_arr <= 1e-6)),
        "flood_days": float(np.sum(storage_arr[1:] > S_SAFE)),
        "spill_mm3": float(spill_arr.sum() / 1e6),
        "energy_mwh": float(energy_arr.sum()),
        "end_storage_mm3": float(storage_arr[-1] / 1e6),
    }
    traj = {
        "inflow": inflow,
        "demand": demand,
        "release": release_arr,
        "storage": storage_arr,
        "reward": reward_arr,
    }
    return metrics, traj


def build_eval_scenarios(n_scenarios, seed):
    rng = np.random.default_rng(seed)
    scenarios = []
    for _ in range(n_scenarios):
        inflow = generate_inflow_series(SIM_DAYS, rng)
        demand = generate_demand_series(SIM_DAYS)
        scenarios.append((inflow, demand))
    return scenarios


def evaluate_policy(policy_name, q_table, scenarios):
    all_metrics = []
    first_traj = None
    for i, (inflow, demand) in enumerate(scenarios):
        m, traj = simulate_episode(policy_name, q_table, inflow, demand)
        all_metrics.append(m)
        if i == 0:
            first_traj = traj

    keys = all_metrics[0].keys()
    mean_metrics = {k: float(np.mean([m[k] for m in all_metrics])) for k in keys}
    return mean_metrics, first_traj


def print_kpi_table(rl_metrics, rule_metrics, n_cases):
    print(f"\n=== KPI结果表（{n_cases}个随机来水场景均值） ===")
    header = (
        f"{'Policy':<18}"
        f"{'AvgReward':>12}"
        f"{'SupplyRate':>12}"
        f"{'FloodDays':>10}"
        f"{'Spill(Mm3)':>12}"
        f"{'Energy(MWh)':>12}"
        f"{'EndStor(Mm3)':>14}"
    )
    print(header)
    print("-" * len(header))

    rows = [("Q-Learning(RL)", rl_metrics), ("RuleCurve", rule_metrics)]
    for name, m in rows:
        print(
            f"{name:<18}"
            f"{m['avg_reward']:>12.2f}"
            f"{m['supply_rate']:>12.3f}"
            f"{m['flood_days']:>10.2f}"
            f"{m['spill_mm3']:>12.2f}"
            f"{m['energy_mwh']:>12.2f}"
            f"{m['end_storage_mm3']:>14.2f}"
        )


def moving_average(x, w=30):
    if len(x) < w:
        return x
    return np.convolve(x, np.ones(w) / w, mode="valid")


def plot_results(training_rewards, traj_rl, traj_rule):
    days = np.arange(SIM_DAYS)
    days_s = np.arange(SIM_DAYS + 1)

    
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.figure(figsize=(12, 10))

    ax1 = plt.subplot(3, 1, 1)
    ax1.plot(days, traj_rl["inflow"], label="Inflow", color="steelblue", alpha=0.7)
    ax1.plot(days, traj_rl["release"], label="Release-RL", color="tomato")
    ax1.plot(days, traj_rule["release"], label="Release-Rule", color="seagreen", linestyle="--")
    ax1.plot(days, traj_rl["demand"], label="Demand", color="gray", linestyle=":")
    ax1.set_ylabel("Flow (m3/s)")
    ax1.set_title("Reservoir Dispatch / Gate Control")
    ax1.grid(alpha=0.3)
    ax1.legend(loc="upper right")

    ax2 = plt.subplot(3, 1, 2)
    ax2.plot(days_s, traj_rl["storage"] / 1e6, label="Storage-RL", color="tomato")
    ax2.plot(days_s, traj_rule["storage"] / 1e6, label="Storage-Rule", color="seagreen", linestyle="--")
    ax2.axhline(S_SAFE / 1e6, color="black", linestyle=":", label="Safe Limit")
    ax2.axhline(S_TARGET / 1e6, color="gray", linestyle="-.", label="Target")
    ax2.set_ylabel("Storage (Mm3)")
    ax2.grid(alpha=0.3)
    ax2.legend(loc="upper right")

    ax3 = plt.subplot(3, 1, 3)
    ax3.plot(days, np.cumsum(traj_rl["reward"]), label="CumReward-RL", color="tomato")
    ax3.plot(days, np.cumsum(traj_rule["reward"]), label="CumReward-Rule", color="seagreen", linestyle="--")
    ax3.set_xlabel("Day")
    ax3.set_ylabel("Cumulative Reward")
    ax3.grid(alpha=0.3)
    ax3.legend(loc="upper left")

    plt.tight_layout()

    # 训练收敛曲线
    plt.figure(figsize=(10, 4))
    smooth = moving_average(training_rewards, 35)
    x = np.arange(len(smooth)) + (len(training_rewards) - len(smooth))
    plt.plot(x, smooth, color="purple")
    plt.title("Q-learning Training Reward (Moving Average)")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('ch09_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch09_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    np.random.seed(RANDOM_SEED)
    print("开始训练Q-learning智能体...")
    q_table, training_rewards = train_q_learning()

    scenarios = build_eval_scenarios(EVAL_EPISODES, seed=RANDOM_SEED + 100)

    rl_metrics, traj_rl = evaluate_policy("rl", q_table, scenarios)
    rule_metrics, traj_rule = evaluate_policy("rule", q_table, scenarios)

    print_kpi_table(rl_metrics, rule_metrics, EVAL_EPISODES)
    plot_results(training_rewards, traj_rl, traj_rule)


if __name__ == "__main__":
    main()
