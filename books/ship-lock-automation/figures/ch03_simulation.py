# -*- coding: utf-8 -*-
"""
教材：《船闸调度优化与自动化》
章节：第3章 船闸调度优化（排队论）- 3.1 基本概念与理论框架
功能：基于 M/M/1 排队模型进行船闸调度仿真，比较基准方案与优化方案，
      打印 KPI 结果表格，并生成 matplotlib 图形用于教学展示。
"""

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 关键参数（可直接调参）
# =========================
SEED = 20260307                  # 随机种子
N_SHIPS = 6000                   # 单次仿真的船舶数量
WARMUP_SHIPS = 1000              # 预热样本（不计入统计）
N_REPLICATIONS = 40              # 重复仿真次数（用于置信区间）

LAMBDA = 8.0                     # 到达率 λ（艘/小时）
MU_BASE = 9.5                    # 基准服务率 μ（艘/小时）
MU_BOUNDS = (LAMBDA + 0.2, 14.0) # 优化搜索区间（保证 μ > λ）

WAIT_COST_PER_SHIP_HOUR = 900.0  # 等待成本（元/艘·小时）
SERVICE_COST_WEIGHT = 550.0      # 提升服务率的运维成本权重
MU_REF = 9.0                     # 运维成本参考服务率（艘/小时）

PLOT_HOURS = 80.0                # 队列轨迹绘图时长（小时）

# 中文显示（不同电脑字体可能不同，按顺序回退）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def mm1_theory(lam: float, mu: float) -> dict:
    """M/M/1 理论指标。"""
    if mu <= lam:
        raise ValueError("系统不稳定：要求 mu > lambda。")
    rho = lam / mu
    Wq = lam / (mu * (mu - lam))
    W = 1.0 / (mu - lam)
    Lq = lam * Wq
    L = lam * W
    return {"rho": rho, "Wq": Wq, "W": W, "Lq": Lq, "L": L}


def hourly_total_cost(mu: float, lam: float = LAMBDA) -> float:
    """
    理论小时总成本函数：
    1) 排队等待成本 = 等待成本单价 * 到达率 * Wq
    2) 调度/运维成本 = SERVICE_COST_WEIGHT * (mu - MU_REF)^2
    """
    theo = mm1_theory(lam, mu)
    waiting_cost = WAIT_COST_PER_SHIP_HOUR * lam * theo["Wq"]
    operation_cost = SERVICE_COST_WEIGHT * (mu - MU_REF) ** 2
    return waiting_cost + operation_cost


def simulate_mm1(lam: float, mu: float, n_ships: int, warmup_ships: int, rng: np.random.Generator, return_sample=False) -> dict:
    """
    基于到达/服务指数分布的离散事件仿真（FCFS）。
    这里采用“到达时间 + 递推开工时间”的高效实现。
    """
    inter_arrivals = rng.exponential(scale=1.0 / lam, size=n_ships)
    arrivals = np.cumsum(inter_arrivals)
    service_times = rng.exponential(scale=1.0 / mu, size=n_ships)

    service_start = np.empty(n_ships)
    departures = np.empty(n_ships)

    service_start[0] = arrivals[0]
    departures[0] = service_start[0] + service_times[0]

    for i in range(1, n_ships):
        service_start[i] = max(arrivals[i], departures[i - 1])
        departures[i] = service_start[i] + service_times[i]

    waits = service_start - arrivals         # 排队等待时间
    systems = departures - arrivals          # 系统逗留时间（等待+服务）

    # 预热后统计，减小初始空系统偏差
    obs_begin = arrivals[warmup_ships]
    obs_end = departures[-1]
    obs_time = obs_end - obs_begin
    completed = n_ships - warmup_ships

    throughput = completed / obs_time
    utilization = np.sum(service_times[warmup_ships:]) / obs_time
    Wq = np.mean(waits[warmup_ships:])
    W = np.mean(systems[warmup_ships:])
    Lq = throughput * Wq
    L = throughput * W

    result = {
        "utilization": utilization,
        "Wq": Wq,
        "W": W,
        "Lq": Lq,
        "L": L,
        "throughput": throughput,
    }

    if return_sample:
        result["arrivals"] = arrivals
        result["departures"] = departures

    return result


def mean_ci95(values):
    """计算均值与95%置信区间半宽。"""
    arr = np.asarray(values, dtype=float)
    mean = np.mean(arr)
    if len(arr) < 2:
        return mean, 0.0
    sem = stats.sem(arr)
    h = stats.t.ppf(0.975, len(arr) - 1) * sem
    return mean, h


def evaluate_scheme(label: str, mu: float, seed: int) -> dict:
    """重复仿真并汇总 KPI。"""
    master = np.random.default_rng(seed)
    metrics = {"utilization": [], "Wq": [], "W": [], "Lq": [], "L": [], "throughput": []}
    sample = None

    for rep in range(N_REPLICATIONS):
        rng = np.random.default_rng(int(master.integers(1, 2**31 - 1)))
        out = simulate_mm1(LAMBDA, mu, N_SHIPS, WARMUP_SHIPS, rng, return_sample=(rep == 0))
        for k in metrics:
            metrics[k].append(out[k])
        if rep == 0:
            sample = {"arrivals": out["arrivals"], "departures": out["departures"]}

    summary = {
        "label": label,
        "mu": mu,
        "theory": mm1_theory(LAMBDA, mu),
        "cost_hourly": hourly_total_cost(mu),
        "metrics": {},
        "sample": sample,
    }

    for k, vals in metrics.items():
        m, h = mean_ci95(vals)
        summary["metrics"][k] = {"mean": m, "ci95": h}

    return summary


def build_queue_trajectory(arrivals: np.ndarray, departures: np.ndarray, horizon: float):
    """生成队列长度阶梯图数据（时域）。"""
    a = arrivals[arrivals <= horizon]
    d = departures[departures <= horizon]

    times = np.concatenate([a, d])
    deltas = np.concatenate([np.ones(len(a), dtype=int), -np.ones(len(d), dtype=int)])

    order = np.argsort(times, kind="mergesort")
    times = times[order]
    deltas = deltas[order]

    t_plot = [0.0]
    q_plot = [0]
    q_now = 0

    for t, delta in zip(times, deltas):
        t_plot.append(t)
        q_plot.append(q_now)
        q_now += delta
        t_plot.append(t)
        q_plot.append(q_now)

    t_plot.append(horizon)
    q_plot.append(q_now)

    return np.array(t_plot), np.array(q_plot)


def fmt_pm(mean, ci, nd=3):
    return f"{mean:.{nd}f} ± {ci:.{nd}f}"


def print_kpi_table(base: dict, opti: dict):
    """打印 KPI 结果表格。"""
    print("\n=== KPI结果表（仿真均值 ±95%CI）===")
    header = (
        f"{'方案':<10}"
        f"{'μ(艘/时)':>10}"
        f"{'利用率ρ':>18}"
        f"{'Wq(小时)':>18}"
        f"{'W(小时)':>18}"
        f"{'Lq(艘)':>18}"
        f"{'吞吐率(艘/时)':>18}"
        f"{'成本(元/时)':>14}"
    )
    print(header)
    print("-" * len(header))

    def row(s):
        m = s["metrics"]
        return (
            f"{s['label']:<10}"
            f"{s['mu']:>10.3f}"
            f"{fmt_pm(m['utilization']['mean'], m['utilization']['ci95']):>18}"
            f"{fmt_pm(m['Wq']['mean'], m['Wq']['ci95']):>18}"
            f"{fmt_pm(m['W']['mean'], m['W']['ci95']):>18}"
            f"{fmt_pm(m['Lq']['mean'], m['Lq']['ci95']):>18}"
            f"{fmt_pm(m['throughput']['mean'], m['throughput']['ci95']):>18}"
            f"{s['cost_hourly']:>14.2f}"
        )

    print(row(base))
    print(row(opti))

    print("\n=== 理论值对照（M/M/1）===")
    print(f"{'方案':<10}{'rho':>10}{'Wq':>12}{'W':>12}{'Lq':>12}{'L':>12}")
    for s in [base, opti]:
        th = s["theory"]
        print(
            f"{s['label']:<10}"
            f"{th['rho']:>10.3f}"
            f"{th['Wq']:>12.3f}"
            f"{th['W']:>12.3f}"
            f"{th['Lq']:>12.3f}"
            f"{th['L']:>12.3f}"
        )


def plot_results(base: dict, opti: dict):
    """绘制成本曲线 + 队列轨迹。"""
    mu_grid = np.linspace(MU_BOUNDS[0], MU_BOUNDS[1], 240)
    cost_grid = np.array([hourly_total_cost(mu) for mu in mu_grid])

    tb, qb = build_queue_trajectory(base["sample"]["arrivals"], base["sample"]["departures"], PLOT_HOURS)
    to, qo = build_queue_trajectory(opti["sample"]["arrivals"], opti["sample"]["departures"], PLOT_HOURS)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].plot(mu_grid, cost_grid, lw=2, label="理论小时总成本")
    axes[0].axvline(base["mu"], ls="--", lw=1.5, label=f"基准 μ={base['mu']:.2f}")
    axes[0].axvline(opti["mu"], ls="--", lw=1.5, label=f"优化 μ={opti['mu']:.2f}")
    axes[0].set_title("服务率-成本优化曲线")
    axes[0].set_xlabel("服务率 μ（艘/小时）")
    axes[0].set_ylabel("总成本（元/小时）")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].step(tb, qb, where="post", lw=1.2, label="基准方案队列长度")
    axes[1].step(to, qo, where="post", lw=1.2, label="优化方案队列长度")
    axes[1].set_title(f"队列长度轨迹对比（前{PLOT_HOURS:.0f}小时）")
    axes[1].set_xlabel("时间（小时）")
    axes[1].set_ylabel("队列长度（艘）")
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig('ch03_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch03_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    # 1) 求解最优服务率（理论成本最小）
    opt_result = minimize_scalar(
        hourly_total_cost,
        bounds=MU_BOUNDS,
        method="bounded"
    )
    mu_opt = float(opt_result.x)

    # 2) 基准方案与优化方案仿真评估
    base = evaluate_scheme("基准方案", MU_BASE, seed=SEED)
    opti = evaluate_scheme("优化方案", mu_opt, seed=SEED + 1)

    # 3) 输出 KPI 表格
    print(f"到达率 λ = {LAMBDA:.3f} 艘/小时")
    print(f"基准服务率 μ_base = {MU_BASE:.3f} 艘/小时")
    print(f"优化服务率 μ_opt = {mu_opt:.3f} 艘/小时")
    print_kpi_table(base, opti)

    # 4) 绘图
    plot_results(base, opti)


if __name__ == "__main__":
    main()
