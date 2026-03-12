# -*- coding: utf-8 -*-
"""
书名：《水库调度优化与决策》
章节：第6章 入库预报不确定性（6.1 基本概念与理论框架）
功能：构建“真实入流-预报入流-调度决策”闭环仿真，比较确定性、机会约束、鲁棒三种策略，
输出KPI结果表格，并生成风险-效益可视化图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import minimize_scalar


# ===================== 1) 关键参数定义 =====================
RANDOM_SEED = 20260307

# 仿真规模
T = 90
N_SCENARIOS = 240

# 水库与供水参数（示例量纲：百万m3）
DEMAND = 80.0
S_MIN = 150.0
S_MAX = 450.0
S_FLOOD = 420.0
S0 = 300.0
S_TARGET = 320.0
R_MIN = 20.0
R_MAX = 160.0

# 调度规则系数
K_STORAGE = 0.22
K_FORECAST = 0.35

# 入流生成参数
MU_BASE = 85.0
MU_AMP = 25.0
PERIOD = 45.0
AR_PHI = 0.65
AR_SIGMA = 11.0

# 预报误差参数
FORECAST_BIAS = -2.0
FORECAST_NOISE_STD = 13.0
SIGMA_BASE = 10.0
SIGMA_VAR = 5.0

# 风险参数
ALPHA_MIN = 0.02
ALPHA_MAX = 0.30
ROBUST_GAMMA = 1.60
FLOOD_RISK_TARGET = 0.05

# 评分权重（用于机会约束参数优化）
W_DEFICIT = 1.8
W_RISK = 350.0
W_SPILL = 50.0
W_CVAR = 0.10

# 发电近似参数
ENERGY_FACTOR = 0.0026
HEAD_MIN = 20.0
HEAD_MAX = 45.0

# 绘图参数
FIG_NAME = "ch6_inflow_uncertainty_sim.png"
SHOW_PLOT = False
SAVE_FIG = True


def seasonal_mean(t: int) -> np.ndarray:
    """季节性均值入流"""
    idx = np.arange(t)
    return MU_BASE + MU_AMP * np.sin(2.0 * np.pi * idx / PERIOD)


def generate_scenario(rng: np.random.Generator, t: int = T):
    """生成单个情景：真实入流、预报入流、预报标准差、季节均值"""
    mu = seasonal_mean(t)

    # 真实入流异常项：AR(1)
    eps = rng.normal(0.0, AR_SIGMA, size=t)
    anomaly = np.zeros(t)
    for k in range(1, t):
        anomaly[k] = AR_PHI * anomaly[k - 1] + eps[k]
    inflow_true = np.clip(mu + anomaly, 0.0, None)

    # 预报入流：带偏差和噪声，且与真实过程保持相关
    forecast_noise = rng.normal(FORECAST_BIAS, FORECAST_NOISE_STD, size=t)
    inflow_fcst = np.clip(mu + 0.75 * anomaly + forecast_noise, 0.0, None)

    # 预报不确定性（标准差）设置为随季节和噪声变化
    sigma = (
        SIGMA_BASE
        + SIGMA_VAR * (0.5 + 0.5 * np.sin(2.0 * np.pi * (np.arange(t) + 8.0) / PERIOD))
        + 0.10 * np.abs(forecast_noise)
    )
    sigma = np.clip(sigma, 4.0, None)

    return inflow_true, inflow_fcst, sigma, mu


def build_ensemble(n: int = N_SCENARIOS):
    """构建蒙特卡洛情景集"""
    master_rng = np.random.default_rng(RANDOM_SEED)
    scenarios = []
    for _ in range(n):
        child_seed = int(master_rng.integers(0, 2**32 - 1))
        scenarios.append(generate_scenario(np.random.default_rng(child_seed)))
    return scenarios


def risk_margin(policy: str, sigma_t: float, alpha: float = None, gamma: float = None) -> float:
    """不同策略的预泄安全裕度"""
    if policy == "deterministic":
        return 0.0
    if policy == "chance":
        return norm.ppf(1.0 - alpha) * sigma_t
    if policy == "robust":
        return gamma * sigma_t
    raise ValueError(f"未知策略: {policy}")


def simulate_policy(scenario, policy: str, alpha: float = None, gamma: float = None, return_series: bool = False):
    """在单情景下仿真给定策略"""
    inflow_true, inflow_fcst, sigma, mu = scenario
    t = len(inflow_true)

    storage = np.zeros(t + 1)
    release = np.zeros(t)
    spill = np.zeros(t)
    deficit = np.zeros(t)
    energy = np.zeros(t)

    storage[0] = S0

    for k in range(t):
        # 调度规则：需求项 + 库容反馈项 + 预报修正项 + 风险安全裕度
        margin = risk_margin(policy, sigma[k], alpha=alpha, gamma=gamma)
        release_plan = (
            DEMAND
            + K_STORAGE * (storage[k] - S_TARGET)
            + K_FORECAST * (inflow_fcst[k] - mu[k])
            + margin
        )
        release_plan = np.clip(release_plan, R_MIN, R_MAX)

        # 可行性约束：不能跌破最小库容
        max_release_feasible = max(0.0, storage[k] + inflow_true[k] - S_MIN)
        release[k] = min(release_plan, max_release_feasible)

        # 库容更新
        deficit[k] = max(0.0, DEMAND - release[k])
        s_next = storage[k] + inflow_true[k] - release[k]

        # 超上限部分记为弃水
        if s_next > S_MAX:
            spill[k] = s_next - S_MAX
            s_next = S_MAX
        storage[k + 1] = s_next

        # 简化发电模型：发电量与下泄流量和水头近似成正比
        head = HEAD_MIN + (HEAD_MAX - HEAD_MIN) * (storage[k] - S_MIN) / (S_MAX - S_MIN)
        head = np.clip(head, HEAD_MIN, HEAD_MAX)
        energy[k] = ENERGY_FACTOR * release[k] * head

    kpi = {
        "mean_energy": float(energy.sum()),
        "reliability": float(np.mean(release >= DEMAND)),
        "avg_deficit": float(deficit.mean()),
        "spill_ratio": float(spill.sum() / max(inflow_true.sum(), 1e-6)),
        "flood_prob": float(np.mean(storage[1:] > S_FLOOD)),
        "terminal_dev": float(abs(storage[-1] - S_TARGET)),
        "total_deficit": float(deficit.sum()),
    }

    if return_series:
        kpi.update({
            "storage": storage,
            "release": release,
            "deficit_series": deficit,
            "spill_series": spill,
        })
    return kpi


def cvar_right_tail(values: np.ndarray, q: float = 0.95) -> float:
    """计算右尾CVaR"""
    v = np.asarray(values, dtype=float)
    var_q = np.quantile(v, q)
    tail = v[v >= var_q]
    return float(tail.mean() if tail.size > 0 else var_q)


def evaluate_strategy(scenarios, policy: str, alpha: float = None, gamma: float = None):
    """在情景集合上统计某策略KPI"""
    all_kpi = []
    total_deficits = []

    for sc in scenarios:
        r = simulate_policy(sc, policy=policy, alpha=alpha, gamma=gamma, return_series=False)
        all_kpi.append(r)
        total_deficits.append(r["total_deficit"])

    total_deficits = np.array(total_deficits)
    cvar95 = cvar_right_tail(total_deficits, q=0.95)

    out = {
        "policy": policy,
        "alpha": alpha,
        "gamma": gamma,
        "mean_energy": float(np.mean([x["mean_energy"] for x in all_kpi])),
        "reliability": float(np.mean([x["reliability"] for x in all_kpi])),
        "avg_deficit": float(np.mean([x["avg_deficit"] for x in all_kpi])),
        "spill_ratio": float(np.mean([x["spill_ratio"] for x in all_kpi])),
        "flood_prob": float(np.mean([x["flood_prob"] for x in all_kpi])),
        "terminal_dev": float(np.mean([x["terminal_dev"] for x in all_kpi])),
        "cvar95_deficit": float(cvar95),
    }

    # 综合得分：越大越好（便于优化）
    out["score"] = (
        out["mean_energy"]
        - W_DEFICIT * out["avg_deficit"]
        - W_SPILL * out["spill_ratio"]
        - W_RISK * max(0.0, out["flood_prob"] - FLOOD_RISK_TARGET)
        - W_CVAR * out["cvar95_deficit"]
    )
    return out


def optimize_alpha(scenarios):
    """机会约束策略下优化alpha"""
    def objective(a):
        return -evaluate_strategy(scenarios, policy="chance", alpha=float(a))["score"]

    res = minimize_scalar(
        objective,
        bounds=(ALPHA_MIN, ALPHA_MAX),
        method="bounded",
        options={"xatol": 1e-3},
    )
    alpha_star = float(res.x)
    return alpha_star, res


def print_kpi_table(named_results):
    """打印KPI结果表"""
    print("=" * 136)
    print(
        f"{'策略':<14}{'参数':>10}{'发电量':>12}{'供水可靠率':>12}{'均值缺水':>12}"
        f"{'弃水率':>10}{'超汛限概率':>12}{'CVaR95缺水':>14}{'末库偏差':>12}{'综合得分':>12}"
    )
    print("-" * 136)

    for name, r in named_results.items():
        if r["policy"] == "chance":
            param = f"alpha={r['alpha']:.3f}"
        elif r["policy"] == "robust":
            param = f"gamma={r['gamma']:.2f}"
        else:
            param = "-"

        print(
            f"{name:<14}{param:>10}{r['mean_energy']:>12.2f}{r['reliability']:>12.3f}{r['avg_deficit']:>12.2f}"
            f"{r['spill_ratio']:>10.3f}{r['flood_prob']:>12.3f}{r['cvar95_deficit']:>14.2f}"
            f"{r['terminal_dev']:>12.2f}{r['score']:>12.2f}"
        )
    print("=" * 136)


def plot_results(sample_scenario, sample_series, named_results, alpha_grid, score_grid, alpha_star):
    """绘制对比图"""
    inflow_true, inflow_fcst, sigma, _ = sample_scenario
    t = len(inflow_true)

    # 中文字体兼容设置
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    # 图1：真实入流与预报入流
    ax = axes[0, 0]
    x = np.arange(t)
    ax.plot(x, inflow_true, lw=2.0, label="真实入流")
    ax.plot(x, inflow_fcst, lw=1.8, ls="--", label="预报入流")
    ax.fill_between(x, inflow_fcst - 1.28 * sigma, inflow_fcst + 1.28 * sigma, alpha=0.2, label="约80%预报区间")
    ax.set_title("入流过程与预报不确定性")
    ax.set_xlabel("时段")
    ax.set_ylabel("流量")
    ax.grid(alpha=0.3)
    ax.legend()

    # 图2：三种策略库容轨迹
    ax = axes[0, 1]
    for name, s in sample_series.items():
        ax.plot(np.arange(t + 1), s["storage"], lw=2.0, label=name)
    ax.axhline(S_MIN, color="gray", ls="--", lw=1.2, label="S_min")
    ax.axhline(S_FLOOD, color="r", ls=":", lw=1.2, label="S_flood")
    ax.axhline(S_MAX, color="gray", ls="-.", lw=1.2, label="S_max")
    ax.set_title("不同策略的库容演化")
    ax.set_xlabel("时段")
    ax.set_ylabel("库容")
    ax.grid(alpha=0.3)
    ax.legend()

    # 图3：alpha敏感性与最优点
    ax = axes[1, 0]
    ax.plot(alpha_grid, score_grid, "o-", lw=1.8)
    best_idx = int(np.argmin(np.abs(alpha_grid - alpha_star)))
    ax.scatter(alpha_grid[best_idx], score_grid[best_idx], color="red", zorder=5, label="最优alpha")
    ax.set_title("机会约束参数alpha敏感性")
    ax.set_xlabel("alpha")
    ax.set_ylabel("综合得分")
    ax.grid(alpha=0.3)
    ax.legend()

    # 图4：风险-效益散点
    ax = axes[1, 1]
    for name, r in named_results.items():
        ax.scatter(r["flood_prob"], r["mean_energy"], s=90, label=name)
        ax.annotate(name, (r["flood_prob"], r["mean_energy"]), textcoords="offset points", xytext=(6, 4))
    ax.axvline(FLOOD_RISK_TARGET, color="r", ls="--", lw=1.2, label="风险目标")
    ax.set_title("策略风险-效益对比")
    ax.set_xlabel("超汛限概率")
    ax.set_ylabel("平均发电量")
    ax.grid(alpha=0.3)
    ax.legend()

    plt.tight_layout()
    if SAVE_FIG:
        plt.savefig(FIG_NAME, dpi=150)
    if SHOW_PLOT:
        # plt.show()  # 禁用弹窗
    plt.close(fig)


def main():
    # 1) 生成情景
    scenarios = build_ensemble(N_SCENARIOS)

    # 2) 优化机会约束参数alpha
    alpha_star, opt_res = optimize_alpha(scenarios)

    # 3) 评估三种策略
    result_det = evaluate_strategy(scenarios, policy="deterministic")
    result_chance = evaluate_strategy(scenarios, policy="chance", alpha=alpha_star)
    result_robust = evaluate_strategy(scenarios, policy="robust", gamma=ROBUST_GAMMA)

    named_results = {
        "确定性策略": result_det,
        "机会约束策略": result_chance,
        "鲁棒策略": result_robust,
    }

    print("\nKPI结果表（第6章：入库预报不确定性）")
    print_kpi_table(named_results)
    print(f"alpha优化成功: {opt_res.success}，最优alpha = {alpha_star:.4f}")

    # 4) 单情景过程图
    sample = scenarios[0]
    sample_series = {
        "确定性策略": simulate_policy(sample, policy="deterministic", return_series=True),
        "机会约束策略": simulate_policy(sample, policy="chance", alpha=alpha_star, return_series=True),
        "鲁棒策略": simulate_policy(sample, policy="robust", gamma=ROBUST_GAMMA, return_series=True),
    }

    alpha_grid = np.linspace(ALPHA_MIN, ALPHA_MAX, 18)
    score_grid = [evaluate_strategy(scenarios, policy="chance", alpha=float(a))["score"] for a in alpha_grid]
    plot_results(sample, sample_series, named_results, alpha_grid, score_grid, alpha_star)

    if SAVE_FIG:
        print(f"图已保存: {FIG_NAME}")
    else:
        print("图生成逻辑已执行（当前未保存文件）。")


if __name__ == "__main__":
    main()
