# -*- coding: utf-8 -*-
"""
教材：《河流泥沙动力学与河床演变》
章节：第5章 河床演变预测（5.1 基本概念与理论框架）
功能：基于一维 Exner 方程与输沙能力关系，模拟整治前后河床冲淤演变，输出KPI并生成图件。
"""

import numpy as np
from scipy.integrate import cumulative_trapezoid
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt


# ===================== 关键参数（可调） =====================
G = 9.81                      # 重力加速度 (m/s^2)
RHO_W = 1000.0                # 水体密度 (kg/m^3)
RHO_S = 2650.0                # 泥沙密度 (kg/m^3)
D50 = 0.0008                  # 中值粒径 (m)
POROSITY = 0.40               # 河床孔隙率 (-)

L = 30_000.0                  # 计算河段长度 (m)
NX = 301                      # 空间网格数
S0 = 1.2e-4                   # 初始河床比降 (-)

YEARS = 15                    # 预测时长 (年)
DT_DAYS = 3                   # 时间步长 (天)
SECONDS_PER_YEAR = 365.0 * 24.0 * 3600.0

Q_MEAN = 1800.0               # 平均流量 (m^3/s)
Q_AMP = 0.35                  # 季节振幅系数 (-)

B_BEFORE = 220.0              # 整治前河宽 (m)
B_AFTER = 180.0               # 整治后河宽 (m)
N_BEFORE = 0.032              # 整治前糙率
N_AFTER = 0.028               # 整治后糙率
T_PROJECT = 8.0               # 整治实施时间 (第8年)

THETA_C = 0.047               # 起动 Shields 临界值
M_EXP = 1.6                   # 输沙能力指数
ALPHA_QB = 0.011              # 输沙能力系数 (m^2/s)
S_MIN = 1.0e-6                # 最小坡降（防止除零）

SED_IN_FACTOR_BEFORE = 1.15   # 整治前来沙系数（>1 偏淤积）
SED_IN_FACTOR_AFTER = 0.88    # 整治后来沙系数（<1 偏冲刷）

SAVE_FIG_PATH = "ch05_bed_evolution.png"  # 输出图像文件名
SHOW_FIG = True                              # 是否弹窗显示图形


# ===================== 模型函数 =====================
def discharge(t_sec: float) -> float:
    """季节性来流过程线。"""
    return Q_MEAN * (1.0 + Q_AMP * np.sin(2.0 * np.pi * t_sec / SECONDS_PER_YEAR))


def stage_params(t_sec: float):
    """按时间切换整治前后参数。"""
    if t_sec < T_PROJECT * SECONDS_PER_YEAR:
        return B_BEFORE, N_BEFORE, SED_IN_FACTOR_BEFORE
    return B_AFTER, N_AFTER, SED_IN_FACTOR_AFTER


def sediment_capacity(Q: float, B: float, n_m: float, slope: np.ndarray):
    """
    基于简化水力学 + Shields 参数估算单位宽输沙能力：
    q_b ~ (theta - theta_c)^m
    """
    slope_eff = np.maximum(slope, S_MIN)
    h = ((Q * n_m) / (B * np.sqrt(slope_eff))) ** (3.0 / 5.0)
    tau = RHO_W * G * h * slope_eff
    theta = tau / ((RHO_S - RHO_W) * G * D50)
    qb_cap = ALPHA_QB * np.maximum(theta - THETA_C, 0.0) ** M_EXP
    return qb_cap, h, theta


def print_kpi_table(rows):
    """打印 KPI 结果表格。"""
    print("\n=== KPI结果表：河床演变预测（第5章 5.1）===")
    print(f"{'指标':<26}{'数值':>14}{'单位':>10}")
    print("-" * 50)
    for name, value, unit in rows:
        print(f"{name:<26}{value:>14}{unit:>10}")


# ===================== 主程序 =====================
def main():
    # 中文显示配置
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # 空间离散
    x = np.linspace(0.0, L, NX)
    dx = x[1] - x[0]

    # 初始河床：总体下倾 + 两个局部扰动，体现河型非均匀性
    eta0 = -S0 * x
    eta0 += 1.0 * np.exp(-((x - 0.35 * L) / (0.09 * L)) ** 2)
    eta0 -= 0.5 * np.exp(-((x - 0.72 * L) / (0.07 * L)) ** 2)

    eta = eta0.copy()
    eta_project = None

    # 时间离散
    dt = DT_DAYS * 24.0 * 3600.0
    n_steps = int(YEARS * 365.0 / DT_DAYS)
    t = np.arange(n_steps + 1) * dt

    # 记录量
    q_in = np.zeros(n_steps)
    q_out = np.zeros(n_steps)
    q_series = np.zeros(n_steps)
    b_series = np.zeros(n_steps)

    sec_x = [0.2 * L, 0.5 * L, 0.8 * L]
    sec_idx = [np.argmin(np.abs(x - xi)) for xi in sec_x]
    eta_sections = np.zeros((n_steps + 1, len(sec_idx)))
    eta_sections[0, :] = eta[sec_idx]

    # 显式推进 Exner 方程
    for k in range(n_steps):
        tk = t[k]
        Qk = discharge(tk)
        Bk, nk, sed_factor = stage_params(tk)

        slope = np.maximum(-np.gradient(eta, dx), S_MIN)
        qb_cap, _, _ = sediment_capacity(Qk, Bk, nk, slope)

        # 面通量：上游给定来沙、下游自由出流、内部取相邻平均
        qb_face = np.zeros(NX + 1)
        qb_face[1:-1] = 0.5 * (qb_cap[:-1] + qb_cap[1:])
        qb_face[0] = sed_factor * qb_cap[0]
        qb_face[-1] = qb_cap[-1]

        # Exner 更新
        deta = -(dt / (1.0 - POROSITY)) * (qb_face[1:] - qb_face[:-1]) / dx
        eta_new = eta + deta

        # 端点控制（控制断面高程固定）
        eta_new[0] = eta0[0]
        eta_new[-1] = eta0[-1]
        eta = eta_new

        # 记录
        q_in[k] = qb_face[0]
        q_out[k] = qb_face[-1]
        q_series[k] = Qk
        b_series[k] = Bk
        eta_sections[k + 1, :] = eta[sec_idx]

        # 记录整治时刻河床线
        if eta_project is None and tk <= T_PROJECT * SECONDS_PER_YEAR < t[k + 1]:
            eta_project = eta.copy()

    if eta_project is None:
        eta_project = eta.copy()

    # KPI 计算
    delta_eta = eta - eta0
    b_ref = 0.5 * (B_BEFORE + B_AFTER)
    net_storage = np.trapz(delta_eta * b_ref, x)                  # m^3
    annual_net_storage = net_storage / YEARS                      # m^3/年

    sed_budget_rate = (q_in - q_out) * b_series                   # m^3/s
    sed_budget_cum = cumulative_trapezoid(sed_budget_rate, t[:-1], initial=0.0)

    kpi_rows = [
        ("最大淤积厚度", f"{np.max(delta_eta):.3f}", "m"),
        ("最大冲刷深度", f"{np.min(delta_eta):.3f}", "m"),
        ("全段平均床面变化", f"{np.mean(delta_eta):.3f}", "m"),
        ("中游断面床面变化", f"{delta_eta[sec_idx[1]]:.3f}", "m"),
        ("净冲淤体积", f"{net_storage:.2f}", "m^3"),
        ("年均净冲淤体积", f"{annual_net_storage:.2f}", "m^3/年"),
        ("末年输沙平衡比(q_out/q_in)", f"{np.mean(q_out[-120:] / np.maximum(q_in[-120:], 1e-12)):.3f}", "-"),
    ]
    print_kpi_table(kpi_rows)

    # 绘图
    ty = t / SECONDS_PER_YEAR
    ty_mid = t[:-1] / SECONDS_PER_YEAR

    fig, axs = plt.subplots(2, 2, figsize=(13, 8))

    axs[0, 0].plot(ty_mid, q_series, lw=1.2, color="#1f77b4")
    axs[0, 0].axvline(T_PROJECT, color="r", ls="--", lw=1.0, label="整治时刻")
    axs[0, 0].set_title("来流过程线")
    axs[0, 0].set_xlabel("时间（年）")
    axs[0, 0].set_ylabel("流量 Q (m³/s)")
    axs[0, 0].grid(alpha=0.3)
    axs[0, 0].legend()

    axs[0, 1].plot(x / 1000.0, eta0, label="初始河床", lw=1.8)
    axs[0, 1].plot(x / 1000.0, eta_project, label="整治时刻", lw=1.5)
    axs[0, 1].plot(x / 1000.0, eta, label="预测末期", lw=1.8)
    axs[0, 1].set_title("河床纵剖面对比")
    axs[0, 1].set_xlabel("沿程 x (km)")
    axs[0, 1].set_ylabel("床面高程 η (m)")
    axs[0, 1].grid(alpha=0.3)
    axs[0, 1].legend()

    labels = ["上游0.2L", "中游0.5L", "下游0.8L"]
    for i, lb in enumerate(labels):
        axs[1, 0].plot(ty, eta_sections[:, i] - eta_sections[0, i], label=lb)
    axs[1, 0].axvline(T_PROJECT, color="r", ls="--", lw=1.0)
    axs[1, 0].set_title("典型断面冲淤历时")
    axs[1, 0].set_xlabel("时间（年）")
    axs[1, 0].set_ylabel("床面变化 Δη (m)")
    axs[1, 0].grid(alpha=0.3)
    axs[1, 0].legend()

    axs[1, 1].plot(ty_mid, sed_budget_cum / 1e6, color="#2ca02c", lw=1.6)
    axs[1, 1].axvline(T_PROJECT, color="r", ls="--", lw=1.0)
    axs[1, 1].set_title("河段累计净冲淤体积")
    axs[1, 1].set_xlabel("时间（年）")
    axs[1, 1].set_ylabel("累计体积 (10^6 m³)")
    axs[1, 1].grid(alpha=0.3)

    fig.suptitle("第5章 河床演变预测：5.1 基本概念与理论框架仿真", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(SAVE_FIG_PATH, dpi=160)
    print(f"\n图件已保存为：{SAVE_FIG_PATH}")

    if SHOW_FIG:
        plt.savefig('ch05_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch05_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
