# -*- coding: utf-8 -*-
"""
教材：《船闸调度优化与自动化》
章节：第5章 案例——三峡/南水北调船闸
功能：基于非恒定流水动力学 + 多目标优化，构建两类大型船闸的日尺度调度仿真，
      输出KPI结果表，并生成调度过程与性能对比图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar, differential_evolution

# -----------------------------
# 全局参数（关键参数集中定义）
# -----------------------------
G = 9.81               # 重力加速度 m/s^2
RHO = 1000.0           # 水密度 kg/m^3
DT_MIN = 10            # 仿真时间步长（分钟）
HOURS = 24             # 仿真总时长（小时）
N_STEPS = HOURS * 60 // DT_MIN
TIME_MIN = np.arange(N_STEPS) * DT_MIN
RNG = np.random.default_rng(42)

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# 工程参数（可按实测继续修订）
PROJECTS = {
    "三峡船闸": {
        "chamber_area": 280.0 * 34.0,          # 闸室等效面积 m^2
        "valve_area_nominal": 42.0,            # 阀门等效过流面积 m^2
        "maneuver_min": 8.0,                   # 船舶进出闸操纵时间 min
        "gate_min": 6.0,                       # 启闭门附加时间 min
        "leakage_coeff": 0.04,                 # 漏损比例
        "aux_energy_kwh_per_lock": 160.0,      # 每次启闭闸辅助能耗 kWh
        "upstream_base": 175.0,                # 上游基准水位 m
        "downstream_base": 83.0,               # 下游基准水位 m
        "upstream_amp": 0.8,                   # 上游水位日内振幅 m
        "downstream_amp": 1.2,                 # 下游水位日内振幅 m
        "phase_up": 0.2,                       # 相位
        "phase_down": 1.0,
        "safety_queue": 90,                    # 安全排队阈值（艘）
        "target_throughput": 125,              # 目标过闸量（艘/日）
        "max_lockages": 40,                    # 最大启闭次数（次/日）
        "objective_weights": (0.45, 0.25, 0.10, 0.20),  # 等待/水耗/能耗/波动
    },
    "南水北调船闸": {
        "chamber_area": 220.0 * 23.0,
        "valve_area_nominal": 28.0,
        "maneuver_min": 6.0,
        "gate_min": 5.0,
        "leakage_coeff": 0.05,
        "aux_energy_kwh_per_lock": 95.0,
        "upstream_base": 64.0,
        "downstream_base": 42.0,
        "upstream_amp": 0.6,
        "downstream_amp": 0.9,
        "phase_up": 0.5,
        "phase_down": 1.3,
        "safety_queue": 70,
        "target_throughput": 85,
        "max_lockages": 36,
        "objective_weights": (0.50, 0.20, 0.10, 0.20),
    },
}

# 历史调度记录（示意：小时到港强度，艘/小时）
HIST_ARRIVAL_HOURLY = {
    "三峡船闸": np.array([2, 2, 2, 3, 4, 6, 8, 9, 8, 7, 6, 6, 6, 7, 8, 9, 10, 9, 8, 7, 6, 5, 4, 3], dtype=float),
    "南水北调船闸": np.array([1, 1, 1, 2, 3, 4, 6, 7, 7, 6, 5, 5, 5, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 2], dtype=float),
}

# 现场实测：不同水头下的充泄时间（秒），用于反演流量系数Cd
MEASURED_DELTA_H = np.array([8, 12, 16, 20, 24], dtype=float)
MEASURED_FILL_SEC = {
    "三峡船闸": np.array([290, 355, 418, 476, 535], dtype=float),
    "南水北调船闸": np.array([235, 300, 360, 415, 470], dtype=float),
}


def head_difference(t_min, p):
    """计算非恒定工况下上下游水位与瞬时水头差"""
    th = t_min / 60.0
    hup = p["upstream_base"] + p["upstream_amp"] * np.sin(2 * np.pi * th / 24 + p["phase_up"])
    hdown = p["downstream_base"] + p["downstream_amp"] * np.sin(2 * np.pi * th / 24 + p["phase_down"])
    dh = max(3.0, hup - hdown)
    return hup, hdown, dh


def filling_time_sec(delta_h, cd, valve_area, chamber_area):
    """
    基于简化非恒定流方程计算充泄时间：
    d(Δh)/dt = -k * sqrt(Δh),  k = Cd*A/Ac*sqrt(2g)
    """
    if delta_h <= 0:
        return 0.0
    k = cd * valve_area / chamber_area * np.sqrt(2 * G)

    def ode(_t, y):
        return [-k * np.sqrt(max(y[0], 0.0))]

    def reach_zero(_t, y):
        return y[0] - 0.01  # 逼近零水头时停止

    reach_zero.terminal = True
    reach_zero.direction = -1

    sol = solve_ivp(ode, (0, 8000), [delta_h], events=reach_zero, max_step=1.0, rtol=1e-6, atol=1e-9)
    if sol.t_events[0].size > 0:
        return float(sol.t_events[0][0])
    return float(sol.t[-1])


def calibrate_cd(project_name, p):
    """利用实测充泄时间反演Cd"""
    measured = MEASURED_FILL_SEC[project_name]

    def loss(cd):
        pred = np.array([
            filling_time_sec(h, cd, p["valve_area_nominal"], p["chamber_area"])
            for h in MEASURED_DELTA_H
        ])
        return np.mean((pred - measured) ** 2)

    res = minimize_scalar(loss, bounds=(0.45, 0.95), method="bounded")
    return float(res.x)


def build_arrivals(hourly_rate):
    """由历史小时到港强度生成10分钟粒度到港序列"""
    lam = np.repeat(hourly_rate * DT_MIN / 60.0, 60 // DT_MIN)
    # 日内扰动：模拟非平稳交通需求
    mod = 1.0 + 0.10 * np.sin(2 * np.pi * np.arange(N_STEPS) / N_STEPS * 2.5)
    lam = np.clip(lam * mod, 0.05, None)
    return RNG.poisson(lam).astype(int)


def simulate_project(project_name, p, cd, arrivals, decision):
    """
    调度仿真：
    decision = [发闸间隔min, 批量装载艘次, 阀门开度系数]
    """
    dispatch_interval = float(decision[0])
    batch_size = int(np.clip(np.round(decision[1]), 2, 10))
    valve_factor = float(decision[2])

    queue = []              # 存储每艘船的到达时刻，FIFO
    waits = []              # 每艘船等待时间（分钟）
    queue_len = []
    delta_h_series = np.zeros(N_STEPS)
    service_per_step = np.zeros(N_STEPS, dtype=int)
    lockage_times = []

    served_total = 0
    lockage_count = 0
    water_total = 0.0
    energy_total = 0.0
    next_ready_time = 0.0

    for k, t_min in enumerate(TIME_MIN):
        # 到港入队
        for _ in range(int(arrivals[k])):
            queue.append(t_min)

        # 当前水力状态
        _, _, delta_h = head_difference(t_min, p)
        delta_h_series[k] = delta_h

        # 调度决策：设备可用且队列非空时执行一次过闸
        if (t_min >= next_ready_time) and (len(queue) > 0):
            served = min(batch_size, len(queue))

            # FIFO计算等待时间
            for _ in range(served):
                ta = queue.pop(0)
                waits.append(t_min - ta)

            served_total += served
            lockage_count += 1
            lockage_times.append(t_min)
            service_per_step[k] = served

            # 每次过闸水耗与能耗
            chamber_volume = p["chamber_area"] * delta_h
            leakage = p["leakage_coeff"] * chamber_volume
            water_total += chamber_volume + leakage

            # 辅助能耗 + 与水头相关的等效能耗项（简化）
            energy_total += p["aux_energy_kwh_per_lock"] + 0.00003 * RHO * G * chamber_volume * delta_h / 3.6e6

            # 非恒定流决定本次充泄时间，进而决定设备下一次可用时刻
            fill_sec = filling_time_sec(
                delta_h,
                cd,
                p["valve_area_nominal"] * valve_factor,
                p["chamber_area"],
            )
            cycle_min = p["maneuver_min"] + p["gate_min"] + 2.0 * fill_sec / 60.0
            next_ready_time = t_min + max(dispatch_interval, cycle_min)

        queue_len.append(len(queue))

    arrivals_total = int(np.sum(arrivals))
    unserved = max(arrivals_total - served_total, 0)

    avg_wait = float(np.mean(waits)) if waits else 0.0
    p95_wait = float(np.percentile(waits, 95)) if waits else 0.0
    water_per_ship = water_total / max(served_total, 1)
    energy_per_ship = energy_total / max(served_total, 1)
    queue_std = float(np.std(queue_len))
    unserved_rate = unserved / max(arrivals_total, 1)

    # 约束惩罚：安全排队、目标通过量、启闭次数
    penalty = 0.0
    penalty += max(0.0, max(queue_len) - p["safety_queue"]) * 20.0
    penalty += max(0.0, p["target_throughput"] - served_total) * 10.0
    penalty += max(0.0, lockage_count - p["max_lockages"]) * 15.0

    w = p["objective_weights"]
    objective = (
        w[0] * avg_wait
        + w[1] * (water_per_ship / 1000.0)
        + w[2] * energy_per_ship
        + w[3] * queue_std
        + penalty
    )

    return {
        "project": project_name,
        "decision": (dispatch_interval, batch_size, valve_factor),
        "avg_wait": avg_wait,
        "p95_wait": p95_wait,
        "served_total": served_total,
        "arrivals_total": arrivals_total,
        "unserved_rate": unserved_rate,
        "water_per_ship": water_per_ship,
        "energy_per_ship": energy_per_ship,
        "lockage_count": lockage_count,
        "queue_std": queue_std,
        "objective": objective,
        "queue_len": np.array(queue_len),
        "delta_h_series": delta_h_series,
        "service_per_step": service_per_step,
        "lockage_times": np.array(lockage_times),
    }


def optimize_project(project_name, p, cd, arrivals):
    """多目标加权优化（微分进化）"""
    bounds = [
        (35.0, 120.0),   # 发闸间隔
        (2.0, 10.0),     # 每次编组艘数（取整）
        (0.75, 1.20),    # 阀门开度系数
    ]

    def obj(x):
        res = simulate_project(project_name, p, cd, arrivals, x)
        return res["objective"]

    de = differential_evolution(
        obj,
        bounds=bounds,
        seed=42,
        maxiter=30,
        popsize=8,
        polish=True,
        disp=False
    )

    best_x = np.array([de.x[0], np.round(de.x[1]), de.x[2]], dtype=float)
    best_res = simulate_project(project_name, p, cd, arrivals, best_x)
    best_res["de_fun"] = float(de.fun)
    return best_res


def print_kpi_table(results):
    print("\nKPI结果表（优化后）")
    print("-" * 118)
    print(f"{'工程':<12}{'平均等待(min)':>14}{'95分位等待(min)':>16}{'总过闸量(艘)':>14}"
          f"{'未服务率':>10}{'水耗(m3/艘)':>14}{'能耗(kWh/艘)':>14}{'目标函数':>12}")
    print("-" * 118)
    for r in results.values():
        print(f"{r['project']:<12}{r['avg_wait']:>14.2f}{r['p95_wait']:>16.2f}{r['served_total']:>14d}"
              f"{r['unserved_rate']:>10.2%}{r['water_per_ship']:>14.1f}{r['energy_per_ship']:>14.2f}"
              f"{r['objective']:>12.2f}")
    print("-" * 118)


def plot_results(results, arrivals_dict):
    names = list(results.keys())
    colors = ["#1f77b4", "#d62728"]
    hours = np.arange(24)
    time_h = TIME_MIN / 60.0

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    # 图1：排队长度演化
    ax = axes[0, 0]
    for i, name in enumerate(names):
        ax.plot(time_h, results[name]["queue_len"], lw=2, color=colors[i], label=f"{name}")
    ax.set_title("排队长度时序")
    ax.set_xlabel("时间 (h)")
    ax.set_ylabel("队列长度 (艘)")
    ax.grid(alpha=0.3)
    ax.legend()

    # 图2：非恒定水头差
    ax = axes[0, 1]
    for i, name in enumerate(names):
        ax.plot(time_h, results[name]["delta_h_series"], lw=2, color=colors[i], label=f"{name}")
    ax.set_title("水头差 Δh 非恒定过程")
    ax.set_xlabel("时间 (h)")
    ax.set_ylabel("Δh (m)")
    ax.grid(alpha=0.3)
    ax.legend()

    # 图3：到港与过闸（小时聚合）
    ax = axes[1, 0]
    for i, name in enumerate(names):
        arr_h = arrivals_dict[name].reshape(24, 60 // DT_MIN).sum(axis=1)
        srv_h = results[name]["service_per_step"].reshape(24, 60 // DT_MIN).sum(axis=1)
        ax.plot(hours, arr_h, "--", color=colors[i], alpha=0.7, label=f"{name}-到港")
        ax.plot(hours, srv_h, "-", color=colors[i], lw=2, label=f"{name}-过闸")
    ax.set_title("到港需求与执行服务对比")
    ax.set_xlabel("小时")
    ax.set_ylabel("艘/小时")
    ax.grid(alpha=0.3)
    ax.legend(ncol=2, fontsize=9)

    # 图4：吞吐与等待KPI对比（双轴）
    ax = axes[1, 1]
    x = np.arange(len(names))
    throughput = [results[n]["served_total"] for n in names]
    wait_avg = [results[n]["avg_wait"] for n in names]
    bars = ax.bar(x, throughput, width=0.5, color=["#4c78a8", "#f58518"], alpha=0.85, label="总过闸量")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("总过闸量 (艘/日)")
    ax.set_title("关键KPI对比")
    ax.grid(axis="y", alpha=0.3)

    ax2 = ax.twinx()
    line = ax2.plot(x, wait_avg, "ko-", lw=2, label="平均等待时间")
    ax2.set_ylabel("平均等待 (min)")

    # 合并图例
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right")

    plt.tight_layout()
    plt.savefig('ch05_simulation_result.png', dpi=160)
    # plt.show()  # 禁用弹窗


def main():
    cd_dict = {}
    arrivals_dict = {}
    results = {}

    # 1) 参数反演与需求构建
    for name, p in PROJECTS.items():
        cd_dict[name] = calibrate_cd(name, p)
        arrivals_dict[name] = build_arrivals(HIST_ARRIVAL_HOURLY[name])

    print("反演得到的流量系数 Cd：")
    for name, cd in cd_dict.items():
        print(f"  {name}: Cd = {cd:.4f}")

    # 2) 调度优化与仿真
    for name, p in PROJECTS.items():
        results[name] = optimize_project(name, p, cd_dict[name], arrivals_dict[name])

    # 3) 输出最优控制变量
    print("\n最优调度参数：")
    for name, r in results.items():
        di, bs, vf = r["decision"]
        print(f"  {name}: 发闸间隔={di:.1f} min, 编组艘数={int(bs)} 艘, 阀门系数={vf:.3f}, 启闭次数={r['lockage_count']}")

    # 4) 打印KPI表
    print_kpi_table(results)

    # 5) 绘图
    plot_results(results, arrivals_dict)


if __name__ == "__main__":
    main()
