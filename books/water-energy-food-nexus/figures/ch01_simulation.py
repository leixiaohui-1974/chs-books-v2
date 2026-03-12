#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
教材：《水-能-粮纽带系统建模》
章节：第1章 1.1 基本概念与理论框架
功能：构建WEF（水-能-粮）纽带概念框架的动态仿真，输出KPI结果表并绘制图形。
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数定义（可直接调参）
# =========================
SECTOR_NAMES = ["水", "能", "粮"]

# 仿真时间（年）
T_START = 0.0
T_END = 30.0
N_POINTS = 301

# 初始状态指数（可理解为保障水平，0~100）
INITIAL_STATE = np.array([78.0, 72.0, 75.0])  # [水, 能, 粮]
CARRYING_CAPACITY = np.array([100.0, 100.0, 100.0])

# 自恢复速率（越大表示部门自身调节越快）
RECOVERY_RATE = np.array([0.22, 0.20, 0.18])

# 需求基线与增长率（指数增长）
DEMAND_BASE = np.array([70.0, 68.0, 65.0])
DEMAND_GROWTH = np.array([0.012, 0.015, 0.013])

# 耦合矩阵：某部门缺口对另一个部门的压力（行=受影响部门，列=缺口来源部门）
COUPLING_MATRIX = np.array([
    [0.45, 0.22, 0.28],  # 对水部门的压力：来自[水缺口, 能缺口, 粮缺口]
    [0.24, 0.40, 0.20],  # 对能部门的压力
    [0.30, 0.26, 0.42],  # 对粮部门的压力
])

# 外部冲击（例如干旱、能源价格波动等）
SHOCK_START = 12.0
SHOCK_END = 16.0
SHOCK_INTENSITY = np.array([6.5, 3.5, 4.0])  # [水, 能, 粮]

# 政策干预（效率提升、协同治理）
POLICY_START = 18.0
POLICY_RECOVERY_BOOST = np.array([0.10, 0.08, 0.12])  # 对恢复速率的提升比例上限
POLICY_COUPLING_REDUCTION = 0.25  # 对耦合压力的削减比例上限

# 绘图中文设置
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def demand_curve(t: float) -> np.ndarray:
    """计算时刻t的三部门需求。"""
    return DEMAND_BASE * np.exp(DEMAND_GROWTH * t)


def policy_recovery_factor(t: float) -> np.ndarray:
    """政策对恢复速率的增益（平滑生效）。"""
    if t < POLICY_START:
        return np.ones(3)
    tau = t - POLICY_START
    return 1.0 + POLICY_RECOVERY_BOOST * (1.0 - np.exp(-tau))


def policy_coupling_factor(t: float) -> float:
    """政策对耦合压力的削弱系数（平滑生效）。"""
    if t < POLICY_START:
        return 1.0
    tau = t - POLICY_START
    reduction = POLICY_COUPLING_REDUCTION * (1.0 - np.exp(-tau))
    return 1.0 - reduction


def shock_term(t: float) -> np.ndarray:
    """外部冲击项。"""
    if SHOCK_START <= t <= SHOCK_END:
        return SHOCK_INTENSITY
    return np.zeros(3)


def wef_ode(t: float, x: np.ndarray) -> np.ndarray:
    """WEF纽带概念模型微分方程。"""
    # 防止数值积分出现轻微负值导致非物理含义
    state = np.clip(x, 0.0, None)

    # 当前需求与缺口
    demand = demand_curve(t)
    deficit = np.maximum(demand - state, 0.0)

    # 政策影响后的参数
    effective_recovery = RECOVERY_RATE * policy_recovery_factor(t)
    effective_coupling = COUPLING_MATRIX * policy_coupling_factor(t)

    # 动态方程：自恢复 - 缺口耦合压力 - 外部冲击
    dstate = effective_recovery * (CARRYING_CAPACITY - state) - effective_coupling @ deficit - shock_term(t)
    return dstate


def print_kpi_table(rows):
    """打印KPI表格。"""
    print("\nWEF纽带系统 KPI 结果表")
    print("=" * 72)
    print(f"{'指标':<24}{'数值':>16}{'说明':>24}")
    print("-" * 72)
    for name, value, note in rows:
        print(f"{name:<24}{value:>16.4f}{note:>24}")
    print("=" * 72)


def main():
    # 时间网格
    t_eval = np.linspace(T_START, T_END, N_POINTS)

    # 数值求解
    sol = solve_ivp(
        fun=wef_ode,
        t_span=(T_START, T_END),
        y0=INITIAL_STATE,
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-8
    )

    if not sol.success:
        raise RuntimeError(f"积分失败: {sol.message}")

    t = sol.t
    states = sol.y.T  # shape=(N, 3)

    # 计算需求、缺口、安全系数
    demands = np.array([demand_curve(tt) for tt in t])
    deficits = np.maximum(demands - states, 0.0)
    security_ratio = np.clip(states / (demands + 1e-9), 0.0, 2.0)  # 状态/需求
    nexus_index = security_ratio.mean(axis=1)

    # KPI统计
    mean_security = security_ratio.mean(axis=0)
    cum_deficit = np.array([np.trapezoid(deficits[:, i], t) for i in range(3)])
    resilience = 1.0 / (1.0 + np.std(nexus_index))
    coordination = 1.0 - (np.std(mean_security) / (np.mean(mean_security) + 1e-9))
    coordination = float(np.clip(coordination, 0.0, 1.0))

    rows = []
    for i, n in enumerate(SECTOR_NAMES):
        rows.append((f"{n}平均安全系数", mean_security[i], "状态/需求"))
    rows.append(("系统综合安全系数", nexus_index.mean(), "三部门平均"))
    rows.append(("系统韧性指数", resilience, "1/(1+波动)"))
    rows.append(("纽带协调度", coordination, "越接近1越均衡"))
    for i, n in enumerate(SECTOR_NAMES):
        rows.append((f"{n}累计缺口面积", cum_deficit[i], "指数*年"))
    rows.append(("期末综合状态", states[-1].mean(), "期末三部门均值"))

    print_kpi_table(rows)

    # =========================
    # 3) 绘图
    # =========================
    fig, axes = plt.subplots(3, 1, figsize=(11, 12), sharex=True)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    # 图1：状态与需求
    for i, n in enumerate(SECTOR_NAMES):
        axes[0].plot(t, states[:, i], color=colors[i], lw=2.0, label=f"{n}状态")
        axes[0].plot(t, demands[:, i], color=colors[i], lw=1.5, ls="--", alpha=0.8, label=f"{n}需求")
    axes[0].axvspan(SHOCK_START, SHOCK_END, color="gray", alpha=0.15, label="冲击期")
    axes[0].axvline(POLICY_START, color="red", ls=":", lw=1.8, label="政策启动")
    axes[0].set_ylabel("指数")
    axes[0].set_title("WEF状态与需求演化")
    axes[0].legend(ncol=4, fontsize=9, frameon=False)

    # 图2：缺口演化
    for i, n in enumerate(SECTOR_NAMES):
        axes[1].plot(t, deficits[:, i], color=colors[i], lw=2.0, label=f"{n}缺口")
    axes[1].axvspan(SHOCK_START, SHOCK_END, color="gray", alpha=0.15)
    axes[1].axvline(POLICY_START, color="red", ls=":", lw=1.8)
    axes[1].set_ylabel("缺口指数")
    axes[1].set_title("WEF缺口动态")
    axes[1].legend(frameon=False)

    # 图3：安全系数与综合纽带指数
    for i, n in enumerate(SECTOR_NAMES):
        axes[2].plot(t, security_ratio[:, i], color=colors[i], lw=1.8, label=f"{n}安全系数")
    axes[2].plot(t, nexus_index, color="black", lw=2.5, label="综合纽带指数")
    axes[2].axhline(1.0, color="gray", ls="--", lw=1.2, label="供需平衡线")
    axes[2].axvspan(SHOCK_START, SHOCK_END, color="gray", alpha=0.15)
    axes[2].axvline(POLICY_START, color="red", ls=":", lw=1.8)
    axes[2].set_xlabel("时间（年）")
    axes[2].set_ylabel("无量纲")
    axes[2].set_title("系统安全系数与协调水平")
    axes[2].legend(ncol=3, fontsize=9, frameon=False)

    plt.tight_layout()
    plt.savefig('ch01_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch01_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
