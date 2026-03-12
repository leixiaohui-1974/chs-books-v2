# -*- coding: utf-8 -*-
"""
教材：《河流泥沙动力学与河床演变》
章节：第1章 1.1 基本概念与理论框架
功能：构建“水动力-起动判别-推移质输运-悬移质分布”教学仿真，
      打印KPI结果表，并生成matplotlib图形。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import brentq
from scipy.integrate import simpson, cumulative_trapezoid

# -----------------------------
# 0) 全局参数（关键参数集中定义）
# -----------------------------
g = 9.81                 # 重力加速度 (m/s^2)
rho_w = 1000.0          # 水体密度 (kg/m^3)
rho_s = 2650.0          # 泥沙密度 (kg/m^3)
nu = 1.0e-6             # 水体运动黏度 (m^2/s)
kappa = 0.41            # von Karman 常数

# 泥沙与起动参数
d50 = 0.0006            # 中值粒径 d50 (m)
theta_c = 0.047         # Shields 临界参数（无量纲）

# 河道与糙率参数（矩形断面）
B = 60.0                # 河宽 (m)
S0 = 8.0e-5             # 河床比降 (-)
n_manning = 0.032       # Manning 糙率系数

# 来流过程参数
Q_mean = 220.0          # 平均流量 (m^3/s)
Q_amp = 120.0           # 日周期振幅 (m^3/s)
Q_sub_amp = 18.0        # 次谐波振幅 (m^3/s)
T_flood = 24.0 * 3600.0 # 主周期 (s)
phase_sub = 0.8         # 次谐波相位 (rad)
Q_min = 30.0            # 最小流量截断 (m^3/s)

# 仿真时长
sim_hours = 72.0        # 总时长 (h)
dt = 300.0              # 时间步长 (s)

# Rouse 剖面参数
reference_ratio = 0.05  # 参考高度 a/H
C_a = 0.002             # 参考点体积分数浓度（示意值）

# 绘图设置（中文显示）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# -----------------------------
# 1) 基础函数
# -----------------------------
def manning_discharge_residual(h, Q, B, S, n):
    """Manning公式残差：Q_est(h)-Q"""
    A = B * h
    P = B + 2.0 * h
    R = A / P
    Q_est = (1.0 / n) * A * (R ** (2.0 / 3.0)) * np.sqrt(S)
    return Q_est - Q


def solve_flow_depth(Q, B, S, n):
    """给定流量Q，反算矩形断面水深h"""
    return brentq(manning_discharge_residual, 0.05, 20.0, args=(Q, B, S, n))


def settling_velocity_soulsby(d, rho_s, rho_w, nu):
    """Soulsby 经验式：沉速 ws"""
    s = rho_s / rho_w
    d_star = d * (((s - 1.0) * g) / (nu ** 2.0)) ** (1.0 / 3.0)
    ws = (nu / d) * (np.sqrt(10.36 ** 2.0 + 1.049 * d_star ** 3.0) - 10.36)
    return ws


def bedload_mpm(theta, theta_c, d, rho_s, rho_w):
    """Meyer-Peter & Muller 公式：单位宽推移质输沙率 qb (m^2/s)"""
    s = rho_s / rho_w
    excess = np.maximum(theta - theta_c, 0.0)
    phi_b = 8.0 * excess ** 1.5
    qb = phi_b * np.sqrt((s - 1.0) * g * d ** 3.0)
    return qb


def print_kpi_table(rows):
    """打印KPI结果表格"""
    print("\n" + "=" * 72)
    print("KPI结果表（第1章 1.1 泥沙运动力学基础）")
    print("-" * 72)
    print(f"{'指标':<26}{'数值':>24}{'单位':>12}")
    print("-" * 72)
    for name, value, unit, fmt in rows:
        print(f"{name:<26}{fmt.format(value):>24}{unit:>12}")
    print("=" * 72)


# -----------------------------
# 2) 主程序
# -----------------------------
def main():
    # 时间轴与流量过程
    t = np.arange(0.0, sim_hours * 3600.0 + dt, dt)
    Q = (
        Q_mean
        + Q_amp * np.sin(2.0 * np.pi * t / T_flood)
        + Q_sub_amp * np.sin(4.0 * np.pi * t / T_flood + phase_sub)
    )
    Q = np.clip(Q, Q_min, None)

    # 预分配数组
    h = np.zeros_like(t)          # 水深
    u = np.zeros_like(t)          # 平均流速
    tau_b = np.zeros_like(t)      # 床面切应力
    theta = np.zeros_like(t)      # Shields参数
    q_b = np.zeros_like(t)        # 单位宽推移质输沙率

    # 时间步计算：水力 -> 起动 -> 输沙
    for i, Qi in enumerate(Q):
        hi = solve_flow_depth(Qi, B, S0, n_manning)
        A = B * hi
        P = B + 2.0 * hi
        R = A / P

        ui = Qi / A
        tau_i = rho_w * g * R * S0
        theta_i = tau_i / ((rho_s - rho_w) * g * d50)
        qb_i = bedload_mpm(theta_i, theta_c, d50, rho_s, rho_w)

        h[i] = hi
        u[i] = ui
        tau_b[i] = tau_i
        theta[i] = theta_i
        q_b[i] = qb_i

    # Rouse剖面（取峰值流量时刻）
    idx_peak = int(np.argmax(Q))
    H_peak = h[idx_peak]
    u_star_peak = np.sqrt(tau_b[idx_peak] / rho_w)
    ws = settling_velocity_soulsby(d50, rho_s, rho_w, nu)
    P_rouse = ws / (kappa * u_star_peak + 1e-12)

    a_ref = max(0.02, reference_ratio * H_peak)
    z = np.linspace(a_ref, H_peak - 1e-3, 250)
    Cz = C_a * ((((H_peak - z) / z) * (a_ref / (H_peak - a_ref))) ** P_rouse)
    C_mean = simpson(Cz, z) / (H_peak - a_ref)

    # KPI汇总
    q_section = q_b * B
    q_section_cum = cumulative_trapezoid(q_section, t, initial=0.0)
    total_bedload_volume = q_section_cum[-1]
    total_bedload_mass = total_bedload_volume * rho_s
    transport_ratio = np.mean(theta >= theta_c) * 100.0
    tau_c = theta_c * (rho_s - rho_w) * g * d50

    kpi_rows = [
        ("平均流量", np.mean(Q), "m^3/s", "{:.2f}"),
        ("平均水深", np.mean(h), "m", "{:.3f}"),
        ("平均流速", np.mean(u), "m/s", "{:.3f}"),
        ("峰值床面切应力", np.max(tau_b), "Pa", "{:.3f}"),
        ("临界切应力", tau_c, "Pa", "{:.3f}"),
        ("峰值Shields参数", np.max(theta), "-", "{:.4f}"),
        ("起动时长占比", transport_ratio, "%", "{:.1f}"),
        ("峰值单位宽输沙率", np.max(q_b), "m^2/s", "{:.6e}"),
        ("总推移质体积", total_bedload_volume, "m^3", "{:.2f}"),
        ("总推移质质量", total_bedload_mass, "kg", "{:.2e}"),
        ("峰值Rouse数", P_rouse, "-", "{:.3f}"),
        ("峰值时刻平均浓度", C_mean, "-", "{:.6f}"),
    ]
    print_kpi_table(kpi_rows)

    # -----------------------------
    # 3) 绘图
    # -----------------------------
    t_h = t / 3600.0
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    # 图1：流量-水深过程
    ax = axs[0, 0]
    ax.plot(t_h, Q, color="tab:blue", lw=1.8, label="流量 Q")
    ax.set_xlabel("时间 (h)")
    ax.set_ylabel("流量 (m^3/s)", color="tab:blue")
    ax.tick_params(axis="y", labelcolor="tab:blue")
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    ax2.plot(t_h, h, color="tab:orange", lw=1.8, label="水深 h")
    ax2.set_ylabel("水深 (m)", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")
    ax.set_title("流量与水深过程")

    # 图2：切应力与Shields参数
    ax = axs[0, 1]
    ax.plot(t_h, tau_b, color="tab:red", lw=1.8, label="床面切应力 τb")
    ax.axhline(tau_c, color="k", ls="--", lw=1.2, label="临界切应力 τc")
    ax.set_xlabel("时间 (h)")
    ax.set_ylabel("切应力 (Pa)")
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    ax2.plot(t_h, theta, color="tab:green", lw=1.5, label="Shields θ")
    ax2.axhline(theta_c, color="tab:purple", ls="--", lw=1.2, label="临界 θc")
    ax2.set_ylabel("Shields参数 (-)")
    ax.set_title("起动判别过程")

    # 图3：推移质输沙率与累计输沙量
    ax = axs[1, 0]
    ax.plot(t_h, q_b, color="tab:brown", lw=1.8, label="单位宽输沙率 qb")
    ax.set_xlabel("时间 (h)")
    ax.set_ylabel("qb (m^2/s)")
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    ax2.plot(t_h, q_section_cum, color="tab:cyan", lw=1.8, label="累计输沙体积")
    ax2.set_ylabel("累计输沙体积 (m^3)")
    ax.set_title("推移质输运过程")

    # 图4：Rouse浓度剖面
    ax = axs[1, 1]
    ax.plot(Cz / C_a, z / H_peak, color="tab:olive", lw=2.0)
    ax.set_xlabel("相对浓度 C(z)/Ca")
    ax.set_ylabel("相对水深 z/H")
    ax.grid(alpha=0.3)
    ax.set_title(f"峰值流量时Rouse剖面 (P={P_rouse:.2f})")

    fig.suptitle("第1章1.1 泥沙运动力学基础仿真", fontsize=13)
    plt.tight_layout()
    plt.savefig('ch01_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch01_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
