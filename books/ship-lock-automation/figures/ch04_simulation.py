# -*- coding: utf-8 -*-
"""
教材：《船闸调度优化与自动化》
章节：基于批量放行策略的船闸调度优化仿真
功能：仿真船舶到港与船闸调度，利用 SciPy 优化放行间隔，输出 KPI 表格并绘制结果图。
关键词：随机到港、批量放行、容量约束、等待时间、能耗优化、自动化调度
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar

# ====================== 关键参数定义 ======================
RNG_SEED = 42                       # 随机种子（保证复现实验）
SIM_HOURS = 24                      # 仿真时长（小时）
SIM_MINUTES = SIM_HOURS * 60        # 仿真时长（分钟）

ARRIVAL_RATE_PER_HOUR = 10.0        # 平均每小时到港船舶数（泊松流）
SHIP_TYPE_NAMES = np.array(["小型", "中型", "大型"])
SHIP_TYPE_PROBS = np.array([0.50, 0.35, 0.15])   # 船型概率
SHIP_TYPE_UNITS = np.array([1, 2, 3])            # 不同船型占用闸室容量单位

LOCK_CAPACITY_UNITS = 8             # 闸室容量上限（容量单位）
BASE_CYCLE_MIN = 10.0               # 每次放行基础操作时间（分钟）
PER_UNIT_CYCLE_MIN = 2.2            # 每容量单位附加操作时间（分钟）

E_FIXED_KWH = 28.0                  # 每次放行固定能耗（kWh）
E_PER_MIN_KWH = 1.4                 # 每分钟操作能耗（kWh）

TARGET_WAIT_MIN = 30.0              # 目标等待时间阈值（分钟）
BASELINE_INTERVAL_MIN = 25.0        # 基线策略放行间隔（分钟）
MIN_INTERVAL_MIN = 8.0              # 优化搜索下界（分钟）
MAX_INTERVAL_MIN = 60.0             # 优化搜索上界（分钟）
ENERGY_WEIGHT = 0.12                # 目标函数中单位能耗权重
OVERTIME_WEIGHT = 0.06              # 目标函数中超时完工权重


def generate_ship_stream(seed=RNG_SEED):
    """生成随机到港船流（到港时间递增）"""
    rng = np.random.default_rng(seed)
    mean_interarrival = 60.0 / ARRIVAL_RATE_PER_HOUR

    arrivals = []
    t = 0.0
    while t < SIM_MINUTES:
        t += rng.exponential(mean_interarrival)
        if t <= SIM_MINUTES:
            arrivals.append(t)

    arrivals = np.array(arrivals, dtype=float)
    if arrivals.size == 0:
        return arrivals, np.array([], dtype=int), np.array([], dtype=int)

    type_idx = rng.choice(len(SHIP_TYPE_NAMES), size=arrivals.size, p=SHIP_TYPE_PROBS)
    units = SHIP_TYPE_UNITS[type_idx].astype(int)
    return arrivals, type_idx, units


def simulate(dispatch_interval, arrivals, units):
    """给定放行间隔，执行调度仿真并返回 KPI"""
    n = arrivals.size
    if n == 0:
        return {
            "interval": float(dispatch_interval),
            "n_ships": 0,
            "avg_wait": 0.0,
            "p95_wait": 0.0,
            "on_time_ratio": 1.0,
            "total_energy": 0.0,
            "unit_energy": 0.0,
            "completion_time": 0.0,
            "throughput_per_hour": 0.0,
            "objective": 0.0,
            "waits": np.array([]),
            "queue_len": np.array([0]),
            "time_axis": np.array([0.0]),
        }

    served = np.zeros(n, dtype=bool)
    start_times = np.full(n, np.nan)
    finish_times = np.full(n, np.nan)

    lock_available = 0.0
    planned_time = float(dispatch_interval)

    cycle_durations = []
    safety_counter = 0

    # 事件循环：直到所有船舶完成过闸
    while not served.all():
        safety_counter += 1
        if safety_counter > 200000:
            raise RuntimeError("仿真循环异常，请检查参数设置。")

        actual_start = max(planned_time, lock_available)

        # 找出已到港且未服务的船舶（FIFO）
        eligible = np.where((~served) & (arrivals <= actual_start))[0]

        if eligible.size > 0:
            load = 0
            chosen = []

            # 按先到先服务装载，直到容量上限
            for idx in eligible:
                u = int(units[idx])
                if load + u <= LOCK_CAPACITY_UNITS:
                    chosen.append(idx)
                    load += u

            # 极端兜底：若首船就超容量，仍强制单船放行避免死锁
            if not chosen:
                chosen = [eligible[0]]
                load = int(units[eligible[0]])

            cycle = BASE_CYCLE_MIN + PER_UNIT_CYCLE_MIN * load
            end_time = actual_start + cycle

            served[chosen] = True
            start_times[chosen] = actual_start
            finish_times[chosen] = end_time

            lock_available = end_time
            cycle_durations.append(cycle)

        planned_time += float(dispatch_interval)

    waits = start_times - arrivals
    total_energy = np.sum(E_FIXED_KWH + E_PER_MIN_KWH * np.array(cycle_durations))
    unit_energy = total_energy / n
    completion_time = float(np.nanmax(finish_times))
    throughput_per_hour = n / (completion_time / 60.0) if completion_time > 0 else 0.0

    avg_wait = float(np.mean(waits))
    p95_wait = float(np.percentile(waits, 95))
    on_time_ratio = float(np.mean(waits <= TARGET_WAIT_MIN))

    overtime = max(0.0, completion_time - SIM_MINUTES)
    objective = avg_wait + ENERGY_WEIGHT * unit_energy + OVERTIME_WEIGHT * overtime

    # 生成队列长度时间序列（分钟粒度）
    t_end = int(np.ceil(max(SIM_MINUTES, completion_time)))
    time_axis = np.arange(t_end + 1, dtype=float)
    queue_len = ((arrivals[:, None] <= time_axis[None, :]) &
                 (start_times[:, None] > time_axis[None, :])).sum(axis=0)

    return {
        "interval": float(dispatch_interval),
        "n_ships": int(n),
        "avg_wait": avg_wait,
        "p95_wait": p95_wait,
        "on_time_ratio": on_time_ratio,
        "total_energy": float(total_energy),
        "unit_energy": float(unit_energy),
        "completion_time": completion_time,
        "throughput_per_hour": float(throughput_per_hour),
        "objective": float(objective),
        "waits": waits,
        "queue_len": queue_len,
        "time_axis": time_axis,
    }


def print_kpi_table(results):
    """打印 KPI 结果表格"""
    print("\nKPI结果表")
    print("-" * 122)
    print("{:<10s}{:>12s}{:>10s}{:>14s}{:>14s}{:>14s}{:>14s}{:>14s}{:>10s}".format(
        "方案", "间隔(min)", "船舶数", "平均等待", "95分位等待", "准点率", "总能耗(kWh)", "单位能耗", "完工(min)"
    ))
    print("-" * 122)
    for name, r in results:
        print("{:<10s}{:>12.1f}{:>10d}{:>14.2f}{:>14.2f}{:>13.1%}{:>14.2f}{:>14.2f}{:>10.1f}".format(
            name, r["interval"], r["n_ships"], r["avg_wait"], r["p95_wait"],
            r["on_time_ratio"], r["total_energy"], r["unit_energy"], r["completion_time"]
        ))
    print("-" * 122)


def plot_results(baseline, optimized):
    """绘制队列长度与等待时间CDF图"""
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 1, figsize=(12, 9))

    # 图1：队列长度对比
    ax1 = axes[0]
    ax1.plot(baseline["time_axis"] / 60.0, baseline["queue_len"], lw=2.0,
             label=f"基线策略 ({baseline['interval']:.1f} min)")
    ax1.plot(optimized["time_axis"] / 60.0, optimized["queue_len"], lw=2.0,
             label=f"优化策略 ({optimized['interval']:.1f} min)")
    ax1.set_title("队列长度时序对比")
    ax1.set_xlabel("时间（小时）")
    ax1.set_ylabel("排队船舶数")
    ax1.grid(alpha=0.3)
    ax1.legend()

    # 图2：等待时间CDF对比
    ax2 = axes[1]

    def cdf_xy(data):
        x = np.sort(data)
        y = np.arange(1, len(x) + 1) / len(x)
        return x, y

    x1, y1 = cdf_xy(baseline["waits"])
    x2, y2 = cdf_xy(optimized["waits"])
    ax2.plot(x1, y1, lw=2.0, label="基线策略")
    ax2.plot(x2, y2, lw=2.0, label="优化策略")
    ax2.axvline(TARGET_WAIT_MIN, color="r", ls="--", lw=1.5, label=f"目标阈值 {TARGET_WAIT_MIN:.0f} min")
    ax2.set_title("等待时间累计分布（CDF）")
    ax2.set_xlabel("等待时间（分钟）")
    ax2.set_ylabel("累计比例")
    ax2.grid(alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    arrivals, type_idx, units = generate_ship_stream(seed=RNG_SEED)
    print(f"仿真船舶总数：{arrivals.size}")

    # 使用 SciPy 在给定范围内搜索最优放行间隔
    obj = lambda x: simulate(x, arrivals, units)["objective"]
    opt = minimize_scalar(obj, bounds=(MIN_INTERVAL_MIN, MAX_INTERVAL_MIN),
                          method="bounded", options={"xatol": 0.2})

    best_interval = float(opt.x)
    print(f"优化得到的放行间隔：{best_interval:.2f} 分钟（目标函数值={opt.fun:.3f}）")

    baseline = simulate(BASELINE_INTERVAL_MIN, arrivals, units)
    optimized = simulate(best_interval, arrivals, units)

    print_kpi_table([
        ("基线策略", baseline),
        ("优化策略", optimized),
    ])

    plot_results(baseline, optimized)


if __name__ == "__main__":
    main()
