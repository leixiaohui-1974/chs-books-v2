# -*- coding: utf-8 -*-
"""
书名：《内河航道与通航水力学》
章节：第1章 航道水力学基础（1.1 基本概念与理论框架）
功能：基于明渠均匀流理论，计算航道“流量-水深-流态”关系，输出KPI表，并绘制关键水力学图形。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import root_scalar

# =========================
# 1) 关键参数定义（可直接修改）
# =========================
g = 9.81                 # 重力加速度 (m/s^2)
nu = 1.0e-6              # 水的运动黏度 (m^2/s)
alpha = 1.05             # 动能修正系数（比能计算）
n_manning = 0.028        # 曼宁糙率
B = 60.0                 # 航道底宽（按矩形断面）(m)
S0 = 1.2e-4              # 底坡（近似水面坡）
design_depth = 3.2       # 设计通航水深 (m)
Q_design = 900.0         # 设计流量 (m^3/s)
Q_min, Q_max = 300.0, 1800.0
num_Q = 80               # 流量离散点数

# 中文显示（若本机无中文字体，可删除这两行）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 2) 水力学基础函数
# =========================
def area_rect(y, b=B):
    """矩形断面过水面积 A = b*y"""
    return b * y


def wetted_perimeter_rect(y, b=B):
    """矩形断面湿周 P = b + 2y"""
    return b + 2.0 * y


def hydraulic_radius_rect(y, b=B):
    """水力半径 R = A/P"""
    A = area_rect(y, b)
    P = wetted_perimeter_rect(y, b)
    return A / P


def manning_residual(y, Q, n_value, slope, b=B):
    """
    曼宁公式残差:
    Q_calc = (1/n) * A * R^(2/3) * S^(1/2)
    residual = Q_calc - Q
    """
    A = area_rect(y, b)
    R = hydraulic_radius_rect(y, b)
    Q_calc = (1.0 / n_value) * A * (R ** (2.0 / 3.0)) * np.sqrt(slope)
    return Q_calc - Q


def solve_normal_depth(Q, n_value=n_manning, slope=S0, b=B):
    """用数值法求正常水深 yn"""
    f = lambda y: manning_residual(y, Q, n_value, slope, b)
    # 在工程常见范围给出根区间
    sol = root_scalar(f, bracket=[0.05, 30.0], method="brentq")
    if not sol.converged:
        raise RuntimeError(f"正常水深求解失败: Q={Q}")
    return sol.root


def critical_depth_rect(Q, b=B, g_value=g):
    """矩形断面临界水深 yc = (Q^2/(g*b^2))^(1/3)"""
    return (Q ** 2 / (g_value * b ** 2)) ** (1.0 / 3.0)


def froude_number(Q, y, b=B, g_value=g):
    """Fr = V/sqrt(g*y)，矩形断面水力深度约为 y"""
    A = area_rect(y, b)
    V = Q / A
    return V / np.sqrt(g_value * y)


def reynolds_number(Q, y, b=B, nu_value=nu):
    """Re = V*Dh/nu，矩形断面 Dh = 4R"""
    A = area_rect(y, b)
    R = hydraulic_radius_rect(y, b)
    V = Q / A
    Dh = 4.0 * R
    return V * Dh / nu_value


def specific_energy(Q, y, b=B, alpha_value=alpha, g_value=g):
    """比能 E = y + alpha*V^2/(2g)"""
    A = area_rect(y, b)
    V = Q / A
    return y + alpha_value * V ** 2 / (2.0 * g_value)


def print_kpi_table(title, rows):
    """
    rows: [(指标, 数值, 单位, 说明), ...]
    """
    print(f"\n{title}")
    header = f"{'指标':<24} | {'数值':>12} | {'单位':<10} | 说明"
    print(header)
    print("-" * len(header))
    for name, value, unit, note in rows:
        if isinstance(value, (int, float, np.floating)):
            vtxt = f"{value:,.4f}"
        else:
            vtxt = str(value)
        print(f"{name:<24} | {vtxt:>12} | {unit:<10} | {note}")


def main():
    # =========================
    # 3) 批量计算：流量-水深-流态
    # =========================
    Q_series = np.linspace(Q_min, Q_max, num_Q)
    y_normal = np.array([solve_normal_depth(Q) for Q in Q_series])
    y_critical = critical_depth_rect(Q_series)

    Fr_series = np.array([froude_number(Q, y) for Q, y in zip(Q_series, y_normal)])
    Re_series = np.array([reynolds_number(Q, y) for Q, y in zip(Q_series, y_normal)])
    E_series = np.array([specific_energy(Q, y) for Q, y in zip(Q_series, y_normal)])

    # 设计点
    y_d = solve_normal_depth(Q_design)
    yc_d = critical_depth_rect(Q_design)
    A_d = area_rect(y_d)
    V_d = Q_design / A_d
    Fr_d = froude_number(Q_design, y_d)
    Re_d = reynolds_number(Q_design, y_d)
    E_d = specific_energy(Q_design, y_d)

    # =========================
    # 4) KPI结果表
    # =========================
    kpi_design = [
        ("设计流量 Qd", Q_design, "m^3/s", "输入设计工况"),
        ("正常水深 yn", y_d, "m", "曼宁方程求解"),
        ("临界水深 yc", yc_d, "m", "判别急缓流边界"),
        ("设计断面流速 V", V_d, "m/s", "V=Q/A"),
        ("弗劳德数 Fr", Fr_d, "-", "Fr<1为缓流"),
        ("雷诺数 Re", Re_d, "-", "Re>>4000为湍流"),
        ("比能 E", E_d, "m", "单位重量机械能"),
        ("水深裕度 yn/h0", y_d / design_depth, "-", ">=1表示满足设计水深"),
    ]
    print_kpi_table("=== KPI结果表（设计工况）===", kpi_design)

    subcritical_rate = np.mean(Fr_series < 1.0) * 100.0
    depth_guarantee_rate = np.mean(y_normal >= design_depth) * 100.0
    kpi_range = [
        ("流量范围", f"{Q_min:.0f}~{Q_max:.0f}", "m^3/s", "仿真区间"),
        ("缓流占比", subcritical_rate, "%", "Fr<1比例"),
        ("达标水深占比", depth_guarantee_rate, "%", f"yn>={design_depth} m 比例"),
        ("最大Fr", np.max(Fr_series), "-", "区间内最大值"),
        ("最小yn", np.min(y_normal), "m", "区间内最小正常水深"),
    ]
    print_kpi_table("=== KPI结果表（区间统计）===", kpi_range)

    # =========================
    # 5) 参数敏感性（n与S0对yn的影响）
    # =========================
    n_scan = n_manning * np.array([0.8, 0.9, 1.0, 1.1, 1.2])
    s_scan = S0 * np.array([0.8, 0.9, 1.0, 1.1, 1.2])

    y_by_n = np.array([solve_normal_depth(Q_design, n_value=ni, slope=S0) for ni in n_scan])
    y_by_s = np.array([solve_normal_depth(Q_design, n_value=n_manning, slope=si) for si in s_scan])

    dy_n_pct = (y_by_n / y_d - 1.0) * 100.0
    dy_s_pct = (y_by_s / y_d - 1.0) * 100.0

    # =========================
    # 6) 绘图
    # =========================
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), dpi=120)

    # 图1：流量-水深关系
    ax1 = axes[0, 0]
    ax1.plot(Q_series, y_normal, lw=2, label="正常水深 yn")
    ax1.plot(Q_series, y_critical, "--", lw=2, label="临界水深 yc")
    ax1.axhline(design_depth, color="r", ls=":", label=f"设计水深 h0={design_depth}m")
    ax1.set_xlabel("流量 Q (m^3/s)")
    ax1.set_ylabel("水深 (m)")
    ax1.set_title("流量-水深关系")
    ax1.grid(alpha=0.3)
    ax1.legend()

    # 图2：流量-Fr关系
    ax2 = axes[0, 1]
    ax2.plot(Q_series, Fr_series, color="tab:orange", lw=2)
    ax2.axhline(1.0, color="k", ls="--", label="Fr=1（临界）")
    ax2.set_xlabel("流量 Q (m^3/s)")
    ax2.set_ylabel("弗劳德数 Fr (-)")
    ax2.set_title("流态判别（Fr）")
    ax2.grid(alpha=0.3)
    ax2.legend()

    # 图3：设计流量下比能曲线
    ax3 = axes[1, 0]
    y_grid = np.linspace(0.2, 8.0, 300)
    E_grid = specific_energy(Q_design, y_grid)
    E_yc = specific_energy(Q_design, yc_d)
    ax3.plot(y_grid, E_grid, lw=2, label="E-y曲线")
    ax3.scatter([yc_d], [E_yc], color="red", zorder=3, label="临界点")
    ax3.scatter([y_d], [E_d], color="green", zorder=3, label="设计正常点")
    ax3.set_xlabel("水深 y (m)")
    ax3.set_ylabel("比能 E (m)")
    ax3.set_title(f"设计流量 Q={Q_design:.0f} m^3/s 的比能关系")
    ax3.grid(alpha=0.3)
    ax3.legend()

    # 图4：参数敏感性
    ax4 = axes[1, 1]
    ax4.plot(n_scan / n_manning, dy_n_pct, "o-", lw=2, label="糙率n变化")
    ax4.plot(s_scan / S0, dy_s_pct, "s-", lw=2, label="底坡S0变化")
    ax4.axhline(0.0, color="k", ls="--", lw=1)
    ax4.set_xlabel("参数相对基准值（倍数）")
    ax4.set_ylabel("设计水深变化率 (%)")
    ax4.set_title("设计水深参数敏感性")
    ax4.grid(alpha=0.3)
    ax4.legend()

    plt.tight_layout()
    plt.savefig('ch01_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch01_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
