# -*- coding: utf-8 -*-
"""
《河流泥沙动力学与河床演变》 第2章：推移质/悬移质输沙公式
功能：基于 MPM 推移质公式 + Rouse-Einstein 悬移质框架进行数值仿真，
输出 KPI 结果表格，并绘制输沙过程关键图形。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.integrate import simpson
from scipy.optimize import brentq


# =========================
# 关键参数（可按工程对象修改）
# =========================
g = 9.81                 # 重力加速度 (m/s^2)
rho_w = 1000.0           # 水密度 (kg/m^3)
rho_s = 2650.0           # 泥沙密度 (kg/m^3)
nu = 1.0e-6              # 水动力黏性系数 (m^2/s)
kappa = 0.41             # von Karman 常数
theta_c = 0.047          # Shields 临界起动参数
alpha_mpm = 8.0          # MPM 经验系数

B = 60.0                 # 河宽 (m)
S0 = 8.0e-4              # 床坡
n_manning = 0.030        # 曼宁系数
d50 = 0.0005             # 中值粒径 (m), 0.5 mm

Q_series = np.linspace(80, 1600, 80)  # 流量序列 (m^3/s)


def normal_depth_from_discharge(Q, B, S0, n, h_min=0.05, h_max=30.0):
    """由曼宁公式反解恒定均匀流正常水深"""
    f = lambda h: B * (1.0 / n) * h ** (5.0 / 3.0) * np.sqrt(S0) - Q
    return brentq(f, h_min, h_max)


def soulsby_fall_velocity(d, s, nu, g):
    """Soulsby 公式估算沉速 ws"""
    d_star = d * (((s - 1.0) * g) / (nu ** 2)) ** (1.0 / 3.0)
    ws = (nu / d) * (np.sqrt(10.36 ** 2 + 1.049 * d_star ** 3) - 10.36)
    return ws


def mpm_bedload(theta, theta_c, d, s, g, alpha=8.0):
    """Meyer-Peter Muller 推移质输沙率（单位宽度体积率，m^2/s）"""
    if theta <= theta_c:
        return 0.0
    qb_star = alpha * (theta - theta_c) ** 1.5
    qb = qb_star * np.sqrt((s - 1.0) * g * d ** 3)
    return qb


def reference_concentration(theta, theta_c):
    """参考浓度 Ca（经验表达）"""
    excess = max(theta - theta_c, 0.0)
    if excess <= 0:
        return 0.0
    ca = 0.331 * excess ** 1.75 / (1.0 + 0.72 * excess ** 1.75)
    return float(np.clip(ca, 0.0, 0.20))


def suspended_load_rouse(u_star, h, d, theta, theta_c, ws, kappa):
    """
    基于 Rouse 垂线分布 + 对流积分计算悬移质输沙率（单位宽度，m^2/s）
    返回：qs, Rouse数P, z数组, C数组
    """
    if theta <= theta_c or u_star <= 1e-8 or h <= 3.0 * d:
        z = np.array([d, max(1.1 * d, 0.9 * h)])
        c = np.zeros_like(z)
        return 0.0, np.nan, z, c

    a = max(2.0 * d, 0.01 * h)   # 参考高度
    if a >= 0.98 * h:
        a = 0.2 * h

    z = np.linspace(a, 0.98 * h, 300)
    z0 = max(d / 30.0, 1e-6)
    P = ws / (kappa * u_star)    # Rouse 数
    Ca = reference_concentration(theta, theta_c)

    ratio = (a * (h - z)) / (z * (h - a))
    ratio = np.clip(ratio, 1e-12, None)

    C = Ca * ratio ** P
    C = np.clip(C, 0.0, 0.20)    # 防止非物理过大浓度

    u = (u_star / kappa) * np.log(z / z0)
    u = np.maximum(u, 0.0)

    qs = simpson(C * u, x=z)
    return float(qs), float(P), z, C


def print_kpi_table(rows):
    """打印 KPI 文本表格"""
    print("\n" + "=" * 90)
    print(f"{'KPI指标':<28}{'数值':>18}{'单位':>12}{'说明':>32}")
    print("-" * 90)
    for name, val, unit, note in rows:
        val_str = f"{val:,.4f}" if np.isfinite(val) else "N/A"
        print(f"{name:<28}{val_str:>18}{unit:>12}{note:>32}")
    print("=" * 90)


def main():
    s = rho_s / rho_w
    ws = soulsby_fall_velocity(d50, s, nu, g)

    h_list, u_list, ustar_list = [], [], []
    theta_list, qb_list, qs_list, qt_list, rouse_list = [], [], [], [], []

    for Q in Q_series:
        h = normal_depth_from_discharge(Q, B, S0, n_manning)
        U = Q / (B * h)
        u_star = np.sqrt(g * h * S0)

        tau_b = rho_w * u_star ** 2
        theta = tau_b / ((rho_s - rho_w) * g * d50)

        qb = mpm_bedload(theta, theta_c, d50, s, g, alpha_mpm)
        qs, P, _, _ = suspended_load_rouse(u_star, h, d50, theta, theta_c, ws, kappa)
        qt = qb + qs

        h_list.append(h)
        u_list.append(U)
        ustar_list.append(u_star)
        theta_list.append(theta)
        qb_list.append(qb)
        qs_list.append(qs)
        qt_list.append(qt)
        rouse_list.append(P)

    h_arr = np.array(h_list)
    U_arr = np.array(u_list)
    theta_arr = np.array(theta_list)
    qb_arr = np.array(qb_list)
    qs_arr = np.array(qs_list)
    qt_arr = np.array(qt_list)
    rouse_arr = np.array(rouse_list)

    susp_frac = np.divide(qs_arr, qt_arr, out=np.zeros_like(qs_arr), where=qt_arr > 0.0)

    moving_idx = np.where(theta_arr > theta_c)[0]
    Q_crit = Q_series[moving_idx[0]] if moving_idx.size > 0 else np.nan

    peak_idx = int(np.argmax(qt_arr))
    rows = [
        ("临界起动流量 Q_crit", Q_crit, "m^3/s", "Shields首次超过临界值"),
        ("峰值总输沙率 qt,max", qt_arr[peak_idx], "m^2/s", f"发生于 Q={Q_series[peak_idx]:.1f}"),
        ("平均推移质输沙率", np.mean(qb_arr), "m^2/s", "MPM结果均值"),
        ("平均悬移质输沙率", np.mean(qs_arr), "m^2/s", "Rouse积分均值"),
        ("平均悬移质占比", np.mean(susp_frac) * 100.0, "%", "qs/(qb+qs)"),
        ("平均Rouse数", np.nanmean(rouse_arr), "-", "沉降与湍扩散相对强度"),
        ("代表工况平均流速", np.mean(U_arr), "m/s", "流量序列平均"),
        ("代表工况平均水深", np.mean(h_arr), "m", "由曼宁公式反解"),
    ]
    print_kpi_table(rows)

    # ========== 绘图 ==========
    fig, axs = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(2, 2, figsize=(13, 9))

    # 1) Shields 参数
    ax = axs[0, 0]
    ax.plot(Q_series, theta_arr, lw=2, label="Shields theta")
    ax.axhline(theta_c, ls="--", color="r", label=f"theta_c={theta_c}")
    ax.set_xlabel("Discharge Q (m^3/s)")
    ax.set_ylabel("Shields parameter (-)")
    ax.set_title("Incipient Motion Criterion")
    ax.grid(alpha=0.3)
    ax.legend()

    # 2) 推移质/悬移质/总输沙
    ax = axs[0, 1]
    ax.plot(Q_series, qb_arr, lw=2, label="Bedload qb (MPM)")
    ax.plot(Q_series, qs_arr, lw=2, label="Suspended qs (Rouse)")
    ax.plot(Q_series, qt_arr, lw=2.5, label="Total qt")
    ax.set_xlabel("Discharge Q (m^3/s)")
    ax.set_ylabel("Unit-width transport rate (m^2/s)")
    ax.set_title("Sediment Transport Partition")
    ax.grid(alpha=0.3)
    ax.legend()

    # 3) 悬移质占比与Rouse数
    ax = axs[1, 0]
    ax.plot(Q_series, susp_frac * 100.0, color="tab:green", lw=2, label="Suspended fraction (%)")
    ax.set_xlabel("Discharge Q (m^3/s)")
    ax.set_ylabel("Suspended fraction (%)", color="tab:green")
    ax.tick_params(axis="y", labelcolor="tab:green")
    ax.grid(alpha=0.3)

    ax2 = ax.twinx()
    ax2.plot(Q_series, rouse_arr, color="tab:orange", lw=2, ls="--", label="Rouse number P")
    ax2.set_ylabel("Rouse number P (-)", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")
    ax.set_title("Suspended Ratio and Rouse Number")

    # 4) 典型流量下浓度剖面
    ax = axs[1, 1]
    idxs = [10, len(Q_series) // 2, -1]
    for idx in idxs:
        Q = Q_series[idx]
        h = normal_depth_from_discharge(Q, B, S0, n_manning)
        u_star = np.sqrt(g * h * S0)
        theta = (rho_w * u_star ** 2) / ((rho_s - rho_w) * g * d50)
        _, _, z, C = suspended_load_rouse(u_star, h, d50, theta, theta_c, ws, kappa)
        ax.plot(C, z / h, lw=2, label=f"Q={Q:.0f} m^3/s")
    ax.set_xlabel("Concentration C (-)")
    ax.set_ylabel("Relative elevation z/h (-)")
    ax.set_title("Rouse Concentration Profiles")
    ax.grid(alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig('ch02_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch02_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
