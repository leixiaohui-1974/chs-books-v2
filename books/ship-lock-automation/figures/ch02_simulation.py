# -*- coding: utf-8 -*-
"""
教材：《船闸调度优化与自动化》
章节：第2章 船闸输水系统设计（2.1 基本概念与理论框架）
功能：基于伯努利方程+连续方程建立船闸充水过程仿真模型，
      并通过优化阀门开启时长，在“效率-安全”约束下对充水方案进行对比。
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# -------------------- 关键参数定义（工程中可标定） --------------------
G = 9.81                     # 重力加速度 (m/s^2)
RHO = 1000.0                 # 水密度 (kg/m^3)

A_CHAMBER = 34.0 * 280.0     # 闸室水面面积 (m^2)
UPSTREAM_LEVEL = 18.0        # 上游水位 (m)
DOWNSTREAM_LEVEL = 10.0      # 下游水位 (m)
TARGET_LEVEL = 17.8          # 目标水位 (m)

A_MAX = 42.0                 # 输水系统等效最大过水面积 (m^2)
CD = 0.86                    # 综合流量系数
TAU_Q = 10.0                 # 流量惯性时间常数 (s)
ETA_H = 0.83                 # 水力效率 (0~1)

BASELINE_OPEN_TIME = 80.0    # 基准方案：阀门达到全开所需时间 (s)
OPEN_TIME_BOUNDS = (20.0, 420.0)  # 优化变量范围 (s)

MAX_RISE_RATE_LIMIT = 0.18   # 安全约束：最大水位上升速率 (m/min)
PEAK_Q_LIMIT = 520.0         # 设备约束：峰值流量 (m^3/s)

# 目标函数惩罚权重（约束越重要，权重应越高）
W_RISE = 350.0
W_Q = 0.8
W_FAIL = 20000.0

T_MAX = 3600.0               # 最大仿真时长 (s)

# 中文显示
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def valve_ratio(t, t_open):
    """阀门开度曲线：线性开阀，t_open 时达到 100%"""
    return np.clip(t / t_open, 0.0, 1.0)


def simulate_fill(t_open):
    """
    充水过程仿真
    状态变量 y = [h, q]
    h: 闸室水位 (m)
    q: 实际流量 (m^3/s)
    """
    def ode(t, y):
        h, q = y

        # 伯努利关系得到“理想平衡流量”
        dh = max(UPSTREAM_LEVEL - h, 0.0)
        q_eq = CD * A_MAX * valve_ratio(t, t_open) * np.sqrt(2.0 * G * dh)

        # 流量采用一阶惯性逼近（表示输水系统响应滞后）
        dq_dt = (q_eq - q) / TAU_Q

        # 连续方程：水位变化率
        dh_dt = max(q, 0.0) / A_CHAMBER
        return [dh_dt, dq_dt]

    def event_target(t, y):
        # 到达目标水位后终止积分
        return y[0] - TARGET_LEVEL

    event_target.terminal = True
    event_target.direction = 1

    y0 = [DOWNSTREAM_LEVEL, 0.0]

    sol = solve_ivp(
        ode,
        t_span=(0.0, T_MAX),
        y0=y0,
        events=event_target,
        rtol=1e-6,
        atol=1e-8,
        max_step=2.0,
    )

    t = sol.t
    h = sol.y[0]
    q = np.maximum(sol.y[1], 0.0)

    reached = len(sol.t_events[0]) > 0
    fill_time = float(sol.t_events[0][0]) if reached else float(t[-1])

    # KPI 计算
    if len(t) > 2:
        rise_rate = np.gradient(h, t) * 60.0  # m/s -> m/min
        q_acc = np.gradient(q, t)             # m^3/s^2
    else:
        rise_rate = np.array([0.0])
        q_acc = np.array([0.0])

    peak_q = float(np.max(q))
    max_rise_rate = float(np.max(rise_rate))
    max_q_acc = float(np.max(np.abs(q_acc)))
    water_volume = A_CHAMBER * (h[-1] - DOWNSTREAM_LEVEL)

    # 简化能量损失估算：∫ rho*g*Δh*Q*(1-η) dt
    head = np.maximum(UPSTREAM_LEVEL - h, 0.0)
    energy_loss_mj = float(np.trapz(RHO * G * head * q * (1.0 - ETA_H), t) / 1e6)

    feasible = reached and (max_rise_rate <= MAX_RISE_RATE_LIMIT) and (peak_q <= PEAK_Q_LIMIT)

    kpi = {
        "t_open": float(t_open),
        "fill_time": fill_time,
        "peak_q": peak_q,
        "max_rise_rate": max_rise_rate,
        "max_q_acc": max_q_acc,
        "water_volume": float(water_volume),
        "energy_loss_mj": energy_loss_mj,
        "reached": reached,
        "feasible": feasible,
    }
    return t, h, q, kpi


def objective(t_open):
    """优化目标：缩短充水时长，同时满足安全与设备约束"""
    _, _, _, kpi = simulate_fill(t_open)

    penalty = 0.0
    if not kpi["reached"]:
        penalty += W_FAIL
    if kpi["max_rise_rate"] > MAX_RISE_RATE_LIMIT:
        penalty += W_RISE * (kpi["max_rise_rate"] - MAX_RISE_RATE_LIMIT) ** 2
    if kpi["peak_q"] > PEAK_Q_LIMIT:
        penalty += W_Q * (kpi["peak_q"] - PEAK_Q_LIMIT) ** 2

    return kpi["fill_time"] + penalty


def print_kpi_table(rows):
    """打印 KPI 结果表格"""
    headers = [
        "方案",
        "开阀时长(s)",
        "充水时长(s)",
        "峰值流量(m3/s)",
        "最大升速(m/min)",
        "耗水量(m3)",
        "能量损失(MJ)",
        "约束达标",
    ]
    widths = [10, 12, 12, 15, 15, 12, 12, 10]

    def fmt(vals):
        return " | ".join(str(v).ljust(w) for v, w in zip(vals, widths))

    print("\n" + "=" * 108)
    print(fmt(headers))
    print("-" * 108)
    for row in rows:
        print(fmt(row))
    print("=" * 108 + "\n")


def main():
    # 1) 基准方案
    t_b, h_b, q_b, kpi_b = simulate_fill(BASELINE_OPEN_TIME)

    # 2) 优化开阀时长
    result = minimize_scalar(
        objective,
        bounds=OPEN_TIME_BOUNDS,
        method="bounded",
        options={"xatol": 1e-2},
    )
    best_open_time = float(result.x)

    # 3) 优化方案
    t_o, h_o, q_o, kpi_o = simulate_fill(best_open_time)

    # 4) KPI 表格打印
    rows = [
        [
            "基准方案",
            f"{kpi_b['t_open']:.2f}",
            f"{kpi_b['fill_time']:.2f}",
            f"{kpi_b['peak_q']:.2f}",
            f"{kpi_b['max_rise_rate']:.4f}",
            f"{kpi_b['water_volume']:.2f}",
            f"{kpi_b['energy_loss_mj']:.2f}",
            "是" if kpi_b["feasible"] else "否",
        ],
        [
            "优化方案",
            f"{kpi_o['t_open']:.2f}",
            f"{kpi_o['fill_time']:.2f}",
            f"{kpi_o['peak_q']:.2f}",
            f"{kpi_o['max_rise_rate']:.4f}",
            f"{kpi_o['water_volume']:.2f}",
            f"{kpi_o['energy_loss_mj']:.2f}",
            "是" if kpi_o["feasible"] else "否",
        ],
    ]
    print_kpi_table(rows)

    # 5) 绘图
    fig, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)

    axes[0].plot(t_b / 60.0, h_b, label="基准", lw=2)
    axes[0].plot(t_o / 60.0, h_o, label="优化", lw=2)
    axes[0].axhline(TARGET_LEVEL, color="k", ls="--", lw=1, label="目标水位")
    axes[0].set_ylabel("闸室水位 (m)")
    axes[0].set_title("船闸输水系统充水仿真（第2章 2.1）")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].plot(t_b / 60.0, q_b, label="基准", lw=2)
    axes[1].plot(t_o / 60.0, q_o, label="优化", lw=2)
    axes[1].axhline(PEAK_Q_LIMIT, color="r", ls="--", lw=1, label="峰值流量约束")
    axes[1].set_ylabel("流量 Q (m3/s)")
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    t_end = max(t_b[-1], t_o[-1])
    t_show = np.linspace(0, t_end, 500)
    axes[2].plot(t_show / 60.0, valve_ratio(t_show, kpi_b["t_open"]), label="基准开度", lw=2)
    axes[2].plot(t_show / 60.0, valve_ratio(t_show, kpi_o["t_open"]), label="优化开度", lw=2)
    axes[2].set_ylabel("阀门开度 (0~1)")
    axes[2].set_xlabel("时间 (min)")
    axes[2].grid(alpha=0.3)
    axes[2].legend()

    plt.tight_layout()
    plt.savefig('ch02_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch02_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
