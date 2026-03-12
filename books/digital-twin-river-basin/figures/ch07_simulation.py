# -*- coding: utf-8 -*-
"""
书名：《流域数字孪生与智能决策》
章节：第7章 平台工程化（微服务）- 7.1 基本概念与理论框架
功能：仿真固定部署与弹性微服务编排两种平台策略，输出KPI结果表格并绘制关键指标图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import linprog
from scipy.signal import savgol_filter

# ========================= 关键参数（可调） =========================
RANDOM_SEED = 42            # 随机种子
SIM_HOURS = 24              # 仿真总时长（小时）
DT_MIN = 5                  # 时间步长（分钟）
STEPS = int(SIM_HOURS * 60 / DT_MIN)
TIME_H = np.arange(STEPS) * DT_MIN / 60

# 微服务链路：网关 -> 孪生计算 -> 智能推理 -> 决策接口
SERVICES = ["gateway", "twin_engine", "ai_infer", "decision_api"]
N = len(SERVICES)

# 单实例处理能力（rps）
MU = np.array([220, 140, 110, 180], dtype=float)

# 基础处理时延（ms）
BASE_LAT_MS = np.array([12, 45, 60, 20], dtype=float)

# 实例约束
MIN_INST = np.array([1, 1, 1, 1], dtype=float)
MAX_INST = np.array([6, 8, 8, 6], dtype=float)
STATIC_INST = np.array([2, 2, 2, 2], dtype=float)   # 固定部署实例数

# 弹性策略参数
TOTAL_BUDGET = 16         # 总实例预算
TARGET_UTIL = 0.72        # 目标利用率（越低表示冗余越高）
DEGRADE_RATIO = 0.25      # 熔断/降级最大比例


def generate_inflow(steps, dt_min, seed=42):
    """生成具有日周期 + 洪峰扰动的请求流（rps）"""
    rng = np.random.default_rng(seed)
    t = np.arange(steps)

    daily = 1.0 + 0.35 * np.sin(2 * np.pi * t / (24 * 60 / dt_min) - np.pi / 3)
    base_rps = 260 * daily

    spikes = np.zeros(steps)
    event_flags = rng.poisson(lam=0.08, size=steps)
    for i in np.where(event_flags > 0)[0]:
        width = rng.integers(2, 6)           # 洪峰持续 2~5 个步长
        amp = rng.uniform(80, 220)           # 洪峰幅值
        end = min(steps, i + width)
        spikes[i:end] += np.linspace(amp, amp * 0.4, end - i)

    noise = rng.normal(0, 18, size=steps)
    inflow = np.clip(base_rps + spikes + noise, 50, None)
    return inflow


def elastic_allocate(in_rps, queue_rps):
    """
    弹性实例分配：
    1) 先按目标利用率给出“理想实例数”
    2) 若超预算，使用线性规划在预算内最大化加权处理能力
    """
    pressure = np.maximum(in_rps + queue_rps, 1e-6)

    # 理想实例：需求 / (单实例能力 * 目标利用率)
    ideal = np.ceil(pressure / (MU * TARGET_UTIL))
    x = np.clip(ideal, MIN_INST, MAX_INST)

    if x.sum() > TOTAL_BUDGET:
        # 线性规划：max sum(weight_i * MU_i * x_i)
        weight = pressure / pressure.sum()
        c = -(weight * MU)
        A_ub = [np.ones(N)]
        b_ub = [TOTAL_BUDGET]
        bounds = [(MIN_INST[i], MAX_INST[i]) for i in range(N)]
        res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        if res.success:
            x = np.floor(res.x)
        else:
            x = STATIC_INST.copy()

    x = np.clip(x, MIN_INST, MAX_INST)

    # 修正到预算上限以内
    while x.sum() > TOTAL_BUDGET:
        idxs = np.where(x > MIN_INST)[0]
        if len(idxs) == 0:
            break
        score = pressure[idxs] / (x[idxs] * MU[idxs] + 1e-9)
        x[idxs[np.argmin(score)]] -= 1

    while x.sum() < TOTAL_BUDGET:
        room = np.where(x < MAX_INST)[0]
        if len(room) == 0:
            break
        score = pressure[room] / (x[room] * MU[room] + 1e-9)
        x[room[np.argmax(score)]] += 1

    return x.astype(int)


def simulate_step(arrival_rps, queue_rps, instances):
    """单步串行服务链仿真：排队、降级、处理、时延"""
    flow = arrival_rps
    new_queue = queue_rps.copy()
    util_list = []
    total_latency_ms = 0.0
    dropped_rps = 0.0

    for i in range(N):
        capacity = instances[i] * MU[i]
        incoming = flow + new_queue[i]

        # 超载时按比例降级低优先级流量（熔断思想）
        overload = max(0.0, incoming / (capacity + 1e-9) - 1.0)
        degrade = np.clip(overload * DEGRADE_RATIO, 0.0, DEGRADE_RATIO)

        protected = incoming * (1.0 - degrade)
        dropped_rps += (incoming - protected)

        served = min(capacity, protected)
        new_queue[i] = max(0.0, protected - served)

        util = served / (capacity + 1e-9)
        util_list.append(util)

        # 时延模型：基础时延 + 利用率惩罚 + 排队惩罚
        service_delay = BASE_LAT_MS[i] * (1 + 1.8 * util**2)
        queue_delay = 1000 * new_queue[i] / (capacity + 1e-9)
        total_latency_ms += service_delay + queue_delay

        flow = served

    success_rps = flow
    return new_queue, success_rps, dropped_rps, total_latency_ms, np.mean(util_list)


def run_simulation(mode="static"):
    inflow = generate_inflow(STEPS, DT_MIN, seed=RANDOM_SEED)

    queue = np.zeros(N)
    success_hist = np.zeros(STEPS)
    drop_hist = np.zeros(STEPS)
    lat_hist = np.zeros(STEPS)
    util_hist = np.zeros(STEPS)
    queue_hist = np.zeros(STEPS)
    inst_hist = np.zeros((STEPS, N))

    for t in range(STEPS):
        arrival = inflow[t]

        if mode == "static":
            inst = STATIC_INST.copy()
        else:
            demand = np.array([arrival, arrival * 0.97, arrival * 0.92, arrival * 0.90])
            inst = elastic_allocate(demand, queue)

        queue, succ, drop, lat, util = simulate_step(arrival, queue, inst)

        success_hist[t] = succ
        drop_hist[t] = drop
        lat_hist[t] = lat
        util_hist[t] = util
        queue_hist[t] = queue.sum()
        inst_hist[t, :] = inst

    return {
        "inflow": inflow,
        "success": success_hist,
        "drop": drop_hist,
        "lat_ms": lat_hist,
        "util": util_hist,
        "queue": queue_hist,
        "instances": inst_hist
    }


def calc_kpi(result):
    inflow = result["inflow"]
    success = result["success"]
    drop = result["drop"]
    lat = result["lat_ms"]
    util = result["util"]
    queue = result["queue"]
    inst = result["instances"]

    req_total = inflow.sum() * DT_MIN * 60
    succ_total = success.sum() * DT_MIN * 60
    drop_total = drop.sum() * DT_MIN * 60

    return {
        "总请求量(万次)": req_total / 1e4,
        "成功率(%)": succ_total / (req_total + 1e-9) * 100,
        "降级丢弃率(%)": drop_total / (req_total + 1e-9) * 100,
        "平均时延(ms)": np.mean(lat),
        "P95时延(ms)": np.percentile(lat, 95),
        "平均资源利用率(%)": np.mean(util) * 100,
        "资源成本(实例小时)": inst.sum() * DT_MIN / 60,
        "峰值积压(rps)": np.max(queue)
    }


def print_kpi_table(kpi_s, kpi_e):
    print("\n" + "=" * 84)
    print("流域数字孪生平台工程化（微服务）KPI对比")
    print("=" * 84)
    print(f"{'KPI':<28}{'固定部署':>16}{'弹性微服务':>16}{'改进幅度':>16}")
    print("-" * 84)

    for k in kpi_s.keys():
        s, e = kpi_s[k], kpi_e[k]
        lower_better = any(x in k for x in ["时延", "成本", "丢弃率", "积压"])
        improve = (s - e) / (s + 1e-9) * 100 if lower_better else (e - s) / (s + 1e-9) * 100
        print(f"{k:<28}{s:>16.2f}{e:>16.2f}{improve:>15.2f}%")

    print("=" * 84)


def plot_results(rs, re):
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    t = TIME_H
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)

    ax = axes[0, 0]
    ax.plot(t, rs["inflow"], label="输入流量", color="#4c78a8", alpha=0.7)
    ax.plot(t, rs["success"], label="固定部署成功", color="#f58518")
    ax.plot(t, re["success"], label="弹性微服务成功", color="#54a24b")
    ax.set_title("请求与成功吞吐")
    ax.set_xlabel("时间（小时）")
    ax.set_ylabel("rps")
    ax.grid(alpha=0.25)
    ax.legend()

    ax = axes[0, 1]
    win = 9 if STEPS >= 9 else (STEPS if STEPS % 2 == 1 else STEPS - 1)
    win = max(5, win)
    lat_s = savgol_filter(rs["lat_ms"], window_length=win, polyorder=2, mode="interp")
    lat_e = savgol_filter(re["lat_ms"], window_length=win, polyorder=2, mode="interp")
    ax.plot(t, lat_s, label="固定部署时延", color="#e45756")
    ax.plot(t, lat_e, label="弹性微服务时延", color="#72b7b2")
    ax.set_title("端到端时延对比")
    ax.set_xlabel("时间（小时）")
    ax.set_ylabel("ms")
    ax.grid(alpha=0.25)
    ax.legend()

    ax = axes[1, 0]
    ax.plot(t, rs["drop"], label="固定部署降级丢弃", color="#b279a2")
    ax.plot(t, re["drop"], label="弹性微服务降级丢弃", color="#9d755d")
    ax.set_title("降级丢弃流量")
    ax.set_xlabel("时间（小时）")
    ax.set_ylabel("rps")
    ax.grid(alpha=0.25)
    ax.legend()

    ax = axes[1, 1]
    ax.plot(t, rs["instances"].sum(axis=1), label="固定部署实例总数", color="#ff9da6")
    ax.plot(t, re["instances"].sum(axis=1), label="弹性编排实例总数", color="#59a14f")
    ax.set_title("资源编排规模")
    ax.set_xlabel("时间（小时）")
    ax.set_ylabel("实例数")
    ax.grid(alpha=0.25)
    ax.legend()

    fig.suptitle("第7章 平台工程化（微服务）仿真结果", fontsize=14)
    plt.savefig('ch07_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch07_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    result_static = run_simulation("static")
    result_elastic = run_simulation("elastic")

    kpi_static = calc_kpi(result_static)
    kpi_elastic = calc_kpi(result_elastic)

    print_kpi_table(kpi_static, kpi_elastic)
    plot_results(result_static, result_elastic)
