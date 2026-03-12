#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
教材：《水库群调度优化》
章节：第1章 水库调度基础与调度图（1.1 基本概念与理论框架）
功能：基于“水量平衡 + 调度图规则曲线 + 单步优化”进行月尺度仿真，
输出KPI结果（Markdown表格）并生成PNG图。
"""

import numpy as np
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use("Agg")
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# 处理中文显示（若本机无对应字体，可按需替换）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 1) 关键参数（便于修改）
# =========================
RANDOM_SEED = 42
YEARS = 3
N = YEARS * 12  # 月尺度步数

# 库容参数（单位：亿 m3）
S_DEAD = 6.0           # 死库容
S_MAX = 28.0           # 最大库容
S_FLOOD_LIMIT = 26.0   # 汛限库容（汛期采用）
S0 = 18.0              # 初始库容

# 下泄与需水（单位：亿 m3/月）
R_MAX = 5.5            # 下泄能力上限
R_ECO = 0.4            # 生态流量建议下限（软约束）
DEMAND_BASE = 2.3      # 基准需水

# 优化目标权重（可教学调参）
W_DEFICIT = 8.0        # 供水缺额惩罚
W_STORAGE = 1.5        # 库容偏离目标惩罚
W_SPILL = 3.0          # 弃水惩罚
W_FLOOD = 10.0         # 汛限超限惩罚
W_ECO = 6.0            # 生态不足惩罚
W_SMOOTH = 0.4         # 下泄平滑惩罚


def build_rule_curves(t):
    """构造调度图的下限线、上限线、目标线与分月汛限线。"""
    lower = 11.0 + 1.3 * np.sin(2 * np.pi * (t - 2) / 12.0)
    upper = 18.5 + 1.8 * np.sin(2 * np.pi * (t - 2) / 12.0)

    # 保证曲线在合理范围内，且上限高于下限
    lower = np.clip(lower, S_DEAD + 0.8, S_FLOOD_LIMIT - 3.5)
    upper = np.clip(upper, lower + 2.0, S_FLOOD_LIMIT - 0.5)
    target = 0.5 * (lower + upper)

    month = (t % 12) + 1
    flood_limit = np.where((month >= 6) & (month <= 9), S_FLOOD_LIMIT, S_MAX)
    return lower, upper, target, flood_limit


def generate_inflow_and_demand(n):
    """生成具有季节性的来水与需水序列。"""
    t = np.arange(n)
    q_mean = (
        2.2
        + 1.15 * np.sin(2 * np.pi * (t - 4) / 12.0)
        + 0.35 * np.sin(4 * np.pi * (t - 1) / 12.0)
    )
    q_noise = np.random.normal(0.0, 0.28, size=n)
    inflow = np.clip(q_mean + q_noise, 0.25, None)

    demand = DEMAND_BASE * (1.0 + 0.20 * np.sin(2 * np.pi * (t - 1) / 12.0))
    demand = np.clip(demand, 1.6, None)
    return inflow, demand


def simulate():
    """执行单库月尺度调度仿真。"""
    np.random.seed(RANDOM_SEED)
    t = np.arange(N)
    inflow, demand = generate_inflow_and_demand(N)
    s_low, s_up, s_tar, s_flood = build_rule_curves(t)

    storage = np.zeros(N + 1)
    release = np.zeros(N)
    spill = np.zeros(N)
    deficit = np.zeros(N)

    storage[0] = S0
    prev_release = demand[0]  # 用于平滑项

    for k in range(N):
        s_t = storage[k]
        q_t = inflow[k]
        d_t = demand[k]

        # 可行下泄范围：兼顾不超库容与不低于死库容
        r_low = max(0.0, s_t + q_t - S_MAX)
        r_high = min(R_MAX, max(0.0, s_t + q_t - S_DEAD))

        def objective(r):
            s_after = s_t + q_t - r
            sp = max(0.0, s_after - S_MAX)      # 超库容部分作为弃水
            s_next = min(S_MAX, s_after)
            defc = max(0.0, d_t - r)
            flood_exc = max(0.0, s_next - s_flood[k])
            eco_short = max(0.0, R_ECO - r)

            return (
                W_DEFICIT * defc ** 2
                + W_STORAGE * (s_next - s_tar[k]) ** 2
                + W_SPILL * sp ** 2
                + W_FLOOD * flood_exc ** 2
                + W_ECO * eco_short ** 2
                + W_SMOOTH * (r - prev_release) ** 2
            )

        if r_low <= r_high:
            res = minimize_scalar(objective, bounds=(r_low, r_high), method="bounded")
            r_star = float(res.x)
        else:
            # 极端情况下取保守值
            r_star = float(np.clip(r_high, 0.0, R_MAX))

        s_after = s_t + q_t - r_star
        sp = max(0.0, s_after - S_MAX)
        s_next = min(S_MAX, s_after)

        release[k] = r_star
        spill[k] = sp
        storage[k + 1] = s_next
        deficit[k] = max(0.0, d_t - r_star)
        prev_release = r_star

    return t, inflow, demand, release, spill, deficit, storage, s_low, s_up, s_tar, s_flood


def calc_kpis(inflow, demand, release, spill, deficit, storage, s_low, s_up, s_flood):
    """计算教学常用KPI。"""
    fail = release < 0.95 * demand
    reliability = 1.0 - np.mean(fail)
    vulnerability = float(deficit[fail].mean()) if np.any(fail) else 0.0

    if np.sum(fail[:-1]) > 0:
        resilience = np.sum(fail[:-1] & (~fail[1:])) / np.sum(fail[:-1])
    else:
        resilience = 1.0

    band_violation = np.mean((storage[1:] < s_low) | (storage[1:] > s_up))
    flood_violation = np.mean(storage[1:] > s_flood)
    demand_satisfaction = np.sum(np.minimum(release, demand)) / np.sum(demand)

    rows = [
        ("总来水量", f"{inflow.sum():.2f}", "亿m3", "仿真期天然来水总量"),
        ("总供水量", f"{release.sum():.2f}", "亿m3", "仿真期水库下泄总量"),
        ("总弃水量", f"{spill.sum():.2f}", "亿m3", "超库容产生的弃水"),
        ("需水满足率", f"{demand_satisfaction * 100:.2f}", "%", "min(供水,需水)/总需水"),
        ("供水保证率", f"{reliability * 100:.2f}", "%", "R >= 0.95D 的时段占比"),
        ("脆弱度", f"{vulnerability:.3f}", "亿m3/月", "失效期平均缺水量"),
        ("恢复力", f"{resilience * 100:.2f}", "%", "失效后下一期恢复成功比例"),
        ("调度带越界率", f"{band_violation * 100:.2f}", "%", "库容超出上下规则线比例"),
        ("汛限超限率", f"{flood_violation * 100:.2f}", "%", "库容超过当月汛限比例"),
        ("期末库容", f"{storage[-1]:.2f}", "亿m3", "仿真末时段库容"),
    ]
    return rows


def print_markdown_table(rows):
    """以Markdown格式打印KPI表。"""
    print("| 指标 | 数值 | 单位 | 说明 |")
    print("|---|---:|---|---|")
    for name, value, unit, note in rows:
        print(f"| {name} | {value} | {unit} | {note} |")


def plot_and_save(t, inflow, demand, release, spill, deficit, storage, s_low, s_up, s_tar, s_flood, out_png):
    """绘制并保存仿真结果图。"""
    x = t + 1
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)

    # 子图1：来水-需水-供水
    axes[0].plot(x, inflow, label="来水Q", lw=2.0)
    axes[0].plot(x, demand, label="需水D", lw=2.0)
    axes[0].plot(x, release, label="下泄R", lw=2.0)
    axes[0].set_ylabel("流量/水量（亿m3/月）")
    axes[0].set_title("第1章 水库调度基础与调度图：月尺度仿真")
    axes[0].grid(alpha=0.25)
    axes[0].legend(ncol=3, frameon=False)

    # 子图2：调度图与库容轨迹
    axes[1].fill_between(x, s_low, s_up, color="#ccebc5", alpha=0.6, label="调度带（上/下规则线）")
    axes[1].plot(x, s_tar, "--", color="#2ca25f", lw=1.6, label="目标线")
    axes[1].plot(x, storage[1:], color="#1f78b4", lw=2.2, label="实际库容")
    axes[1].plot(x, s_flood, "--", color="#e31a1c", lw=1.6, label="当月汛限")
    axes[1].axhline(S_DEAD, ls="--", color="gray", lw=1.2, label="死库容")
    axes[1].set_ylabel("库容（亿m3）")
    axes[1].grid(alpha=0.25)
    axes[1].legend(ncol=3, frameon=False)

    # 子图3：缺水与弃水
    axes[2].bar(x, deficit, color="#fb9a99", alpha=0.85, label="供水缺额")
    axes[2].plot(x, spill, color="#ff7f00", lw=2.0, label="弃水")
    axes[2].set_ylabel("水量（亿m3/月）")
    axes[2].set_xlabel("时段（月）")
    axes[2].grid(alpha=0.25)
    axes[2].legend(frameon=False)

    plt.tight_layout()
    fig.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    t, inflow, demand, release, spill, deficit, storage, s_low, s_up, s_tar, s_flood = simulate()
    kpi_rows = calc_kpis(inflow, demand, release, spill, deficit, storage, s_low, s_up, s_flood)

    print_markdown_table(kpi_rows)

    output_png = "ch01_reservoir_dispatch_simulation.png"
    plot_and_save(t, inflow, demand, release, spill, deficit, storage, s_low, s_up, s_tar, s_flood, output_png)
    print(f"\n图件已保存：{output_png}")
