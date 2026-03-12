#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《人工智能与水利水电工程》第10章（AI工程化：从实验室到SCADA部署）仿真脚本
功能：模拟“AI推理延迟”对前池水位闭环控制稳定性的影响，输出KPI对比并绘图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from collections import deque

# =========================
# 关键参数定义（可直接调参）
# =========================
DT = 1.0                       # 仿真步长(s)
T_END = 2400.0                 # 仿真总时长(s)
H_REF = 5.0                    # 目标水位(m)
H0 = 5.0                       # 初始水位(m)
A_TANK = 1200.0                # 前池等效面积(m^2)
K_PUMP = 18.0                  # 泵站单位控制量对应出流(m^3/s)
Q_IN_BASE = 9.0                # 基础入流(m^3/s)
Q_IN_STEP = 4.0                # 扰动阶跃增量(m^3/s)
T_STEP = 400.0                 # 扰动开始时刻(s)

# PI控制参数（可理解为AI+规则控制融合后的控制律）
U_BIAS = Q_IN_BASE / K_PUMP    # 静态平衡控制量
KP = 1.8                       # 比例系数
KI = 0.010                     # 积分系数
U_MIN, U_MAX = 0.0, 1.0        # 控制量上下限（归一化）
ANTI_WINDUP = 0.5              # 饱和时积分泄放系数

# KPI判据参数
SETTLE_BAND = 0.05             # 调节带(m)
PEAK_PROMINENCE = 0.03         # 峰值识别阈值(m)
PEAK_MIN_DISTANCE = 90.0       # 峰间最小间隔(s)

# 两个场景：低延迟 vs 高延迟
SCENARIOS = {
    "低延迟边缘部署": 2.0,      # 推理延迟(s)
    "高延迟拥塞场景": 120.0
}


def inlet_flow(t):
    """入流扰动模型：在T_STEP后叠加阶跃扰动"""
    return Q_IN_BASE + (Q_IN_STEP if t >= T_STEP else 0.0)


def simulate(delay_s):
    """单场景仿真：返回时间、水位、控制量、入流"""
    t = np.arange(0.0, T_END + DT, DT)
    n = len(t)

    h = np.zeros(n)
    u = np.zeros(n)
    qin = np.zeros(n)

    h[0] = H0
    u[0] = U_BIAS
    int_err = 0.0

    # 使用队列实现纯滞后：队首即当前生效控制量
    delay_steps = max(0, int(round(delay_s / DT)))
    u_delay_line = deque([U_BIAS] * (delay_steps + 1), maxlen=delay_steps + 1)

    for k in range(n - 1):
        qin[k] = inlet_flow(t[k])

        # 读取延迟后的控制信号驱动水力过程
        u_eff = u_delay_line[0]
        dh = (qin[k] - K_PUMP * u_eff) / A_TANK
        h[k + 1] = h[k] + DT * dh

        # 基于当前状态计算下一拍控制量
        err = H_REF - h[k + 1]
        int_err += err * DT

        u_raw = U_BIAS + KP * err + KI * int_err
        u_cmd = np.clip(u_raw, U_MIN, U_MAX)

        # 简单抗积分饱和：饱和时泄放部分积分项
        if u_cmd != u_raw:
            int_err -= ANTI_WINDUP * err * DT

        u[k + 1] = u_cmd
        u_delay_line.append(u_cmd)

    qin[-1] = inlet_flow(t[-1])
    return t, h, u, qin


def calc_kpi(t, h, delay_s):
    """计算KPI指标"""
    mask = t >= T_STEP
    t_after = t[mask]
    h_after = h[mask]
    e_after = h_after - H_REF

    rmse = np.sqrt(np.mean(e_after ** 2))
    overshoot = max(0.0, np.max(h_after) - H_REF)
    overshoot_pct = overshoot / H_REF * 100.0

    # 调节时间：进入调节带后不再越界
    settling_time = np.nan
    for i in range(len(h_after)):
        if np.all(np.abs(h_after[i:] - H_REF) <= SETTLE_BAND):
            settling_time = t_after[i] - T_STEP
            break

    tail = h[int(0.8 * len(h)):]
    tail_amp = np.max(tail) - np.min(tail)

    peaks, _ = find_peaks(
        h_after,
        prominence=PEAK_PROMINENCE,
        distance=max(1, int(PEAK_MIN_DISTANCE / DT))
    )
    peak_count = int(len(peaks))

    return {
        "delay_s": delay_s,
        "rmse": rmse,
        "overshoot_pct": overshoot_pct,
        "settling_time_s": settling_time,
        "tail_amp_m": tail_amp,
        "peak_count": peak_count
    }


def fmt(x, p=3):
    """格式化数值，NaN显示为--"""
    if isinstance(x, float) and np.isnan(x):
        return "--"
    if isinstance(x, (float, np.floating)):
        return f"{x:.{p}f}"
    return str(x)


def print_kpi_table(kpi_dict):
    """打印KPI结果表格"""
    headers = ["场景", "延迟(s)", "RMSE(m)", "最大超调(%)", "调节时间(s)", "尾段振幅(m)", "峰值个数"]
    rows = []
    for name, k in kpi_dict.items():
        rows.append([
            name,
            fmt(k["delay_s"], 1),
            fmt(k["rmse"], 4),
            fmt(k["overshoot_pct"], 2),
            fmt(k["settling_time_s"], 1),
            fmt(k["tail_amp_m"], 3),
            fmt(k["peak_count"], 0)
        ])

    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(str(c)))

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    print("\nKPI结果表：AI推理延迟对水位控制性能影响")
    print(sep)
    print("| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |")
    print(sep)
    for r in rows:
        print("| " + " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(r))) + " |")
    print(sep)


def plot_results(sim_data):
    """绘图：水位响应、控制量、入流扰动"""
    fig, axes = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(3, 1, figsize=(11, 10), sharex=True)

    for name, d in sim_data.items():
        t, h, u, qin, _ = d
        axes[0].plot(t, h, linewidth=2.0, label=name)
        axes[1].plot(t, u, linewidth=1.8, label=name)

    # 入流对两个场景相同，仅绘制一次
    t0, _, _, qin0, _ = next(iter(sim_data.values()))
    axes[2].plot(t0, qin0, color="tab:green", linewidth=2.0, label="入流Qin")

    axes[0].axhline(H_REF, color="k", linestyle="--", linewidth=1.2, label="目标水位")
    axes[0].axvline(T_STEP, color="tab:red", linestyle=":", linewidth=1.2, label="扰动时刻")
    axes[1].axvline(T_STEP, color="tab:red", linestyle=":", linewidth=1.2)
    axes[2].axvline(T_STEP, color="tab:red", linestyle=":", linewidth=1.2)

    axes[0].set_ylabel("h (m)")
    axes[1].set_ylabel("u (-)")
    axes[2].set_ylabel("Qin (m^3/s)")
    axes[2].set_xlabel("Time (s)")

    axes[0].set_title("第10章仿真：AI推理延迟对SCADA前池水位闭环控制的影响")
    axes[0].grid(alpha=0.3)
    axes[1].grid(alpha=0.3)
    axes[2].grid(alpha=0.3)
    axes[0].legend()
    axes[1].legend()
    axes[2].legend()

    plt.tight_layout()
    plt.savefig('ch10_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch10_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    sim_data = {}
    kpi_data = {}

    for name, delay_s in SCENARIOS.items():
        t, h, u, qin = simulate(delay_s)
        kpi = calc_kpi(t, h, delay_s)
        sim_data[name] = (t, h, u, qin, kpi)
        kpi_data[name] = kpi

    print_kpi_table(kpi_data)
    plot_results(sim_data)


if __name__ == "__main__":
    main()
