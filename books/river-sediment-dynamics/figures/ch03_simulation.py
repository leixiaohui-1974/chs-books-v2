# -*- coding: utf-8 -*-
"""
教材：河流泥沙动力学与河床演变
章节：一维河床演变数值模拟（Exner方程 + Meyer-Peter Müller输沙公式）
功能：模拟河道在给定来流/来沙条件下的冲淤过程，打印KPI结果表并生成图形。
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt


def bedload_capacity(slope, h, d50, rho_w, rho_s, g, theta_c):
    """基于MPM公式计算单位宽度推移质输沙率 q_s (m2/s)"""
    # Shields数：反映床面切应力相对颗粒自重的强度
    theta = rho_w * h * slope / ((rho_s - rho_w) * d50)
    s = rho_s / rho_w
    # MPM公式，低于临界Shields数时输沙率置零
    qs = 8.0 * np.maximum(theta - theta_c, 0.0) ** 1.5 * np.sqrt((s - 1.0) * g * d50**3)
    return qs, theta


def compute_qs_from_bed(z, p):
    """由河床高程剖面计算输沙率分布"""
    slope = np.maximum(-np.gradient(z, p["dx"]), p["slope_floor"])  # 河床坡度 S=-dz/dx
    qs, _ = bedload_capacity(
        slope, p["h"], p["d50"], p["rho_w"], p["rho_s"], p["g"], p["theta_c"]
    )
    # 边界条件：上游给定来沙，下游采用零梯度
    qs[0] = p["qs_in"]
    qs[-1] = qs[-2]
    return qs, slope


def exner_rhs(t, z, p):
    """Exner方程右端项：dz/dt = -(1/(1-lambda_p))*dq_s/dx"""
    qs, _ = compute_qs_from_bed(z, p)
    dqsdx = np.gradient(qs, p["dx"])
    dzdt = -(p["morfac"] / (1.0 - p["porosity"])) * dqsdx
    return dzdt


def print_kpi_table(kpi):
    print("\n" + "=" * 68)
    print("KPI结果表")
    print("=" * 68)
    print(f"{'指标':<28}{'数值':>20}{'单位':>10}")
    print("-" * 68)
    for name, (val, unit) in kpi.items():
        print(f"{name:<28}{val:>20.6f}{unit:>10}")
    print("=" * 68)


def main():
    # -------------------- 关键参数（可按章节案例修改） --------------------
    L = 20_000.0          # 河段长度 (m)
    Nx = 121              # 空间网格数
    Q = 800.0             # 流量 (m3/s)
    B = 120.0             # 河宽 (m)
    n_manning = 0.030     # 曼宁糙率
    S_ref = 2.0e-4        # 参考比降（用于估算平均水深）
    d50 = 0.00030         # 中值粒径 (m)
    rho_w = 1000.0        # 水密度 (kg/m3)
    rho_s = 2650.0        # 泥沙密度 (kg/m3)
    g = 9.81              # 重力加速度 (m/s2)
    porosity = 0.40       # 河床孔隙率
    theta_c = 0.047       # 临界Shields数
    sediment_feed_ratio = 0.90  # 上游来沙/平衡输沙能力比
    morfac = 12.0         # 形态加速因子（缩短演变计算时长）
    slope_floor = 1.0e-6  # 数值稳定下限坡度

    T_days = 120.0        # 总模拟时长 (day)
    Nt_out = 241          # 输出时刻数

    # -------------------- 网格与初始河床 --------------------
    x = np.linspace(0.0, L, Nx)
    dx = x[1] - x[0]

    # 初始河床：整体下倾 + 中游微弱沙波扰动
    z0 = 8.0 - S_ref * x + 0.45 * np.exp(-((x - 10_000.0) / 2600.0) ** 2)

    # 由曼宁公式估算平均水深（宽浅河道近似）
    h = ((Q * n_manning) / (B * np.sqrt(S_ref))) ** (3.0 / 5.0)

    # 估算上游平衡输沙能力并施加来沙边界
    s_up = max(-(z0[1] - z0[0]) / dx, slope_floor)
    qs_eq_up, _ = bedload_capacity(
        np.array([s_up]), h, d50, rho_w, rho_s, g, theta_c
    )
    qs_in = sediment_feed_ratio * qs_eq_up[0]

    p = {
        "x": x, "dx": dx, "h": h, "d50": d50, "rho_w": rho_w, "rho_s": rho_s, "g": g,
        "porosity": porosity, "theta_c": theta_c, "qs_in": qs_in,
        "morfac": morfac, "slope_floor": slope_floor
    }

    # -------------------- 数值积分 --------------------
    t_span = (0.0, T_days * 86400.0)
    t_eval = np.linspace(t_span[0], t_span[1], Nt_out)

    sol = solve_ivp(
        fun=lambda t, y: exner_rhs(t, y, p),
        t_span=t_span,
        y0=z0,
        t_eval=t_eval,
        method="RK23",
        rtol=1e-5,
        atol=1e-7
    )
    if not sol.success:
        raise RuntimeError(f"数值积分失败: {sol.message}")

    z_end = sol.y[:, -1]
    z_mid = sol.y[:, len(sol.t) // 2]
    dz = z_end - z0

    qs_start, _ = compute_qs_from_bed(z0, p)
    qs_end, _ = compute_qs_from_bed(z_end, p)

    # -------------------- KPI计算 --------------------
    deposition_vol = np.trapz(np.clip(dz, 0.0, None) * B, x)         # 淤积体积
    erosion_vol = -np.trapz(np.clip(dz, None, 0.0) * B, x)           # 冲刷体积
    net_vol = np.trapz(dz * B, x)                                    # 净体积变化
    slope_ini = -np.polyfit(x, z0, 1)[0]
    slope_end = -np.polyfit(x, z_end, 1)[0]

    kpi = {
        "最大淤积厚度": (dz.max(), "m"),
        "最大冲刷深度": (dz.min(), "m"),
        "平均床面变化": (dz.mean(), "m"),
        "总淤积体积": (deposition_vol, "m3"),
        "总冲刷体积": (erosion_vol, "m3"),
        "净体积变化": (net_vol, "m3"),
        "上游来沙率": (qs_in, "m2/s"),
        "下游输沙率(初始)": (qs_start[-1], "m2/s"),
        "下游输沙率(末期)": (qs_end[-1], "m2/s"),
        "河段平均比降(初始)": (slope_ini, "-"),
        "河段平均比降(末期)": (slope_end, "-"),
    }
    print_kpi_table(kpi)

    # -------------------- 绘图 --------------------
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    x_km = x / 1000.0
    t_day = sol.t / 86400.0

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)

    ax1 = axes[0, 0]
    ax1.plot(x_km, z0, lw=2.0, label="初始河床")
    ax1.plot(x_km, z_mid, lw=2.0, label="中期河床")
    ax1.plot(x_km, z_end, lw=2.2, label="末期河床")
    ax1.set_xlabel("沿程距离 (km)")
    ax1.set_ylabel("床面高程 (m)")
    ax1.set_title("河床纵剖面演变")
    ax1.grid(alpha=0.3)
    ax1.legend()

    ax2 = axes[0, 1]
    ax2.plot(x_km, dz, color="tab:red", lw=2.0)
    ax2.axhline(0.0, color="k", lw=1.0)
    ax2.set_xlabel("沿程距离 (km)")
    ax2.set_ylabel("Δz = z末期 - z初始 (m)")
    ax2.set_title("冲淤分布")
    ax2.grid(alpha=0.3)

    ax3 = axes[1, 0]
    ax3.plot(x_km, qs_start, lw=2.0, label="初始输沙率")
    ax3.plot(x_km, qs_end, lw=2.0, label="末期输沙率")
    ax3.set_xlabel("沿程距离 (km)")
    ax3.set_ylabel("q_s (m²/s)")
    ax3.set_title("单位宽度输沙率沿程变化")
    ax3.grid(alpha=0.3)
    ax3.legend()

    ax4 = axes[1, 1]
    idx_points = [10, Nx // 2, Nx - 11]
    names = ["上游", "中游", "下游"]
    for idx, name in zip(idx_points, names):
        ax4.plot(t_day, sol.y[idx, :] - z0[idx], lw=2.0, label=f"{name}({x[idx]/1000:.1f} km)")
    ax4.set_xlabel("时间 (day)")
    ax4.set_ylabel("局部床面变化 (m)")
    ax4.set_title("典型断面冲淤时序")
    ax4.grid(alpha=0.3)
    ax4.legend()

    plt.savefig('ch03_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch03_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
