#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
书名：《河流泥沙动力学与河床演变》
章节：第4章 水库淤积与排沙
功能：
1) 构建非恒定水沙耦合的一维非平衡输沙模型；
2) 对比常规调度、降水位排沙、异重流排沙三种方案；
3) 统计三角洲淤积、锥体淤积、异重流淤积分区贡献；
4) 输出KPI结果表并绘制Matplotlib图件；
5) 给出二维非平衡输沙示意场，辅助解释坝前异重流沉积分布。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.integrate import trapezoid
from scipy.ndimage import gaussian_filter

# ========================= 关键参数（可调） =========================
# 空间与时间离散
L = 60_000.0                 # 库区长度(m)
NX = 160                     # 一维网格数
DX = L / (NX - 1)
T_DAYS = 15.0                # 模拟总时长(天)
DT = 180.0                   # 时间步长(s)
NT = int(T_DAYS * 86400 / DT)

# 水沙与几何参数
B = 600.0                    # 代表性库区宽度(m)
G = 9.81
RHO_W = 1000.0               # 水密度(kg/m3)
RHO_S = 2650.0               # 泥沙密度(kg/m3)
POROSITY = 0.40              # 床沙孔隙率
WS = 0.002                   # 代表沉速(m/s)
N_MANNING = 0.030            # 糙率

# 库水位与调度参数
A_SURFACE = 1.8e8            # 等效库表面积(m2)
H_INIT = 398.0               # 初始坝前水位(m)
H_MIN, H_MAX = 370.0, 405.0  # 物理约束水位范围(m)

# 非平衡输沙参数
K_CEQ = 50.0                 # 挟沙力系数
U_CRIT = 0.045               # 临界摩阻流速(m/s)
TAU_ADAPT = 5.5 * 3600.0     # 非平衡调整时间(s)
MORPH_DIFF = 0.035           # 河床形态扩散系数
MAX_DZDT = 2.2e-5            # 河床变化率上限(m/s)

# 2D示意参数
NX2, NY2 = 120, 56
Y_HALF_WIDTH = 1800.0        # 半宽(m)
KX2D, KY2D = 6.0, 1.8        # 2D扩散系数
TAU2D = 4 * 3600.0           # 2D非平衡调整时间(s)
DT2D = 120.0                 # 2D时间步长(s)
NSTEP2D = 360                # 2D迭代步数

# 中文显示（不同系统字体可自行补充）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def build_initial_bed(x):
    """构造初始河床：总体坡降 + 三类典型淤积地貌微起伏"""
    upstream_bed = 430.0
    dam_bed = 350.0
    zb = upstream_bed - (upstream_bed - dam_bed) * (x / L)

    # 三角洲区（上游）
    zb += 1.3 * np.exp(-((x - 0.18 * L) / (0.08 * L)) ** 2)
    # 锥体区（中部）
    zb += 0.9 * np.exp(-((x - 0.55 * L) / (0.10 * L)) ** 2)
    # 异重流影响区（近坝）
    zb += 0.4 * np.exp(-((x - 0.88 * L) / (0.06 * L)) ** 2)
    return zb


def build_inflow_series(t_day):
    """构造非恒定入库流量与含沙量过程线（双峰洪水+沙峰）"""
    q_base, q_peak = 1800.0, 2600.0
    c_base, c_peak = 1.8, 20.0

    qin = (
        q_base
        + q_peak * np.exp(-((t_day - 6.0) / 1.8) ** 2)
        + 0.55 * q_peak * np.exp(-((t_day - 10.5) / 1.6) ** 2)
    )
    cin = (
        c_base
        + c_peak * np.exp(-((t_day - 6.2) / 1.7) ** 2)
        + 0.45 * c_peak * np.exp(-((t_day - 10.7) / 1.3) ** 2)
    )
    return qin, cin


def scenario_configs():
    """三种调度方案：按时间插值控制放流比与目标水位"""
    key_t = np.array([0, 3, 6, 9, 12, 15], dtype=float)

    scenarios = {
        "常规调度": {
            "release_ratio": np.array([0.86, 0.90, 0.95, 1.00, 0.96, 0.90]),
            "target_level": np.array([398, 399, 398, 397, 398, 398]),
            "venting": False,
        },
        "降水位排沙": {
            "release_ratio": np.array([0.92, 1.02, 1.32, 1.38, 1.12, 0.96]),
            "target_level": np.array([398, 394, 386, 384, 390, 396]),
            "venting": False,
        },
        "异重流排沙": {
            "release_ratio": np.array([0.90, 1.00, 1.12, 1.08, 0.98, 0.92]),
            "target_level": np.array([398, 396, 393, 392, 395, 397]),
            "venting": True,
        },
    }

    for name, cfg in scenarios.items():
        cfg["f_ratio"] = interp1d(key_t, cfg["release_ratio"], kind="linear", fill_value="extrapolate")
        cfg["f_htar"] = interp1d(key_t, cfg["target_level"], kind="linear", fill_value="extrapolate")
    return scenarios


def run_1d_model(name, cfg, x, qin, cin, t_day, zb0):
    """一维非平衡输沙：上风格式推进浓度，Exner思想更新床面"""
    zb = zb0.copy()
    c = np.ones_like(x) * cin[0]
    h = H_INIT

    ts_h = np.zeros(NT)
    ts_qout = np.zeros(NT)
    ts_cout = np.zeros(NT)
    ts_frd = np.zeros(NT)

    win_kg = 0.0
    wout_kg = 0.0
    wvent_kg = 0.0

    for k in range(NT):
        qi = qin[k]
        ci = cin[k]
        td = t_day[k]

        ratio = float(cfg["f_ratio"](td))
        h_target = float(cfg["f_htar"](td))

        # 目标放流：由方案放流比 + 水位偏差反馈共同决定
        qout = max(350.0, ratio * qi + 120.0 * (h - h_target))

        # 水动力简化：库内一维缓变，利用代表断面速度估算输沙能力
        depth = np.maximum(h - zb, 3.0)
        u = np.clip(0.5 * (qi + qout) / (B * depth), 0.02, 1.2)

        sf = (N_MANNING**2) * (u**2) / np.maximum(depth, 0.5) ** (4.0 / 3.0)
        u_star = np.sqrt(np.maximum(G * depth * sf, 0.0))
        c_eq = K_CEQ * np.maximum(u_star - U_CRIT, 0.0) ** 1.45

        # 一维非平衡输沙：平流 + 向挟沙力的松弛
        c_up = np.empty_like(c)
        c_up[0] = ci
        c_up[1:] = c[:-1]
        dc_adv = -u * (c - c_up) / DX
        dc_relax = -(c - c_eq) / TAU_ADAPT
        c += DT * (dc_adv + dc_relax)
        c[0] = ci
        c = np.clip(c, 0.02, 80.0)

        # 床面演变：C与C*差值决定冲淤方向
        dzdt = WS * (c - c_eq) / (RHO_S * (1.0 - POROSITY))
        dzdt = np.clip(dzdt, -MAX_DZDT, MAX_DZDT)
        zb += DT * dzdt

        # 形态扩散：等效于二维效应在一维中的参数化
        lap = np.zeros_like(zb)
        lap[1:-1] = (zb[2:] - 2.0 * zb[1:-1] + zb[:-2]) / (DX * DX)
        zb += MORPH_DIFF * DT * lap

        # 异重流判据（近坝）：密度Froude数控制底孔排沙触发
        c_dam = c[-1]
        u_dam = u[-1]
        depth_dam = depth[-1]
        cv = c_dam / RHO_S
        g_prime = G * cv * (RHO_S - RHO_W) / RHO_W
        frd = u_dam / np.sqrt(max(g_prime * depth_dam, 1e-8))
        ts_frd[k] = frd

        q_vent = 0.0
        if cfg["venting"] and (5.0 <= td <= 12.0):
            if (0.45 <= frd <= 1.2) and (c_dam >= 6.0):
                q_vent = min(900.0, 220.0 + 35.0 * (c_dam - 6.0))

        qout_eff = qout + q_vent

        # 库水位连续方程
        h += DT * (qi - qout_eff) / A_SURFACE
        h = float(np.clip(h, H_MIN, H_MAX))

        c_out = c[-1]
        c_bottom = min(120.0, 1.35 * c_dam)

        # 沙量收支
        win_kg += qi * ci * DT
        wout_kg += qout * c_out * DT + q_vent * c_bottom * DT
        wvent_kg += q_vent * c_bottom * DT

        ts_h[k] = h
        ts_qout[k] = qout_eff
        ts_cout[k] = c_out

    dz = zb - zb0
    dep = np.maximum(dz, 0.0)
    ero = np.minimum(dz, 0.0)

    dep_vol = trapezoid(dep * B, x)
    ero_vol = trapezoid(-ero * B, x)
    net_vol = trapezoid(dz * B, x)

    dep_mass_t = dep_vol * (1 - POROSITY) * RHO_S / 1000.0
    ero_mass_t = ero_vol * (1 - POROSITY) * RHO_S / 1000.0
    net_mass_t = net_vol * (1 - POROSITY) * RHO_S / 1000.0

    # 分区统计：三角洲、锥体、异重流区
    m_delta = x <= 0.35 * L
    m_cone = (x > 0.35 * L) & (x <= 0.75 * L)
    m_density = x > 0.75 * L

    v_delta = trapezoid(np.maximum(dz[m_delta], 0.0) * B, x[m_delta])
    v_cone = trapezoid(np.maximum(dz[m_cone], 0.0) * B, x[m_cone])
    v_density = trapezoid(np.maximum(dz[m_density], 0.0) * B, x[m_density])
    v_sum = max(v_delta + v_cone + v_density, 1e-9)

    return {
        "name": name,
        "zb": zb,
        "dz": dz,
        "ts_h": ts_h,
        "ts_qout": ts_qout,
        "ts_cout": ts_cout,
        "ts_frd": ts_frd,
        "win_t": win_kg / 1000.0,
        "wout_t": wout_kg / 1000.0,
        "wvent_t": wvent_kg / 1000.0,
        "eta": 100.0 * wout_kg / max(win_kg, 1e-6),
        "dep_mass_t": dep_mass_t,
        "ero_mass_t": ero_mass_t,
        "net_mass_t": net_mass_t,
        "net_vol": net_vol,
        "delta_pct": 100.0 * v_delta / v_sum,
        "cone_pct": 100.0 * v_cone / v_sum,
        "density_pct": 100.0 * v_density / v_sum,
    }


def run_2d_demo(best_result, qin, cin, x1d, t_day):
    """二维非平衡输沙示意：给出平面沉积分布（教学演示用途）"""
    x2 = np.linspace(0, L, NX2)
    y2 = np.linspace(-Y_HALF_WIDTH, Y_HALF_WIDTH, NY2)
    dx2 = x2[1] - x2[0]
    dy2 = y2[1] - y2[0]
    X2, Y2 = np.meshgrid(x2, y2, indexing="xy")

    # 用一维结果构造二维速度背景场
    mean_h = np.mean(best_result["ts_h"])
    zb_interp = np.interp(x2, x1d, best_result["zb"])
    u_center = 0.5 * (np.max(qin) + np.mean(best_result["ts_qout"])) / (B * np.maximum(mean_h - zb_interp, 3.0))
    u_center = np.clip(u_center, 0.02, 1.1)

    Ux = np.tile(u_center, (NY2, 1))
    Uy = -0.04 * Y2 / Y_HALF_WIDTH  # 横向弱环流（示意）

    c2 = np.zeros((NY2, NX2))
    ceq2 = 3.0 * np.maximum(np.sqrt(Ux**2 + Uy**2) - 0.08, 0.0)

    c_in_peak = float(np.percentile(cin, 85))
    lat = np.exp(-(y2 / 900.0) ** 2)
    lat /= lat.max()

    for _ in range(NSTEP2D):
        c2[:, 0] = c_in_peak * lat

        cw = np.roll(c2, 1, axis=1)
        ce = np.roll(c2, -1, axis=1)
        cs = np.roll(c2, 1, axis=0)
        cn = np.roll(c2, -1, axis=0)

        dc_dx = (c2 - cw) / dx2
        dc_dy = (cn - cs) / (2.0 * dy2)
        d2c_dx2 = (ce - 2.0 * c2 + cw) / (dx2**2)
        d2c_dy2 = (cn - 2.0 * c2 + cs) / (dy2**2)

        dc_dt = -Ux * dc_dx - Uy * dc_dy + KX2D * d2c_dx2 + KY2D * d2c_dy2 - (c2 - ceq2) / TAU2D
        c2 += DT2D * dc_dt
        c2 = np.clip(c2, 0.0, 60.0)

        # 边界处理
        c2[:, -1] = c2[:, -2]
        c2[0, :] = c2[1, :]
        c2[-1, :] = c2[-2, :]

    dz2 = WS * (c2 - ceq2) / (RHO_S * (1.0 - POROSITY)) * (NSTEP2D * DT2D)
    dz2 = gaussian_filter(dz2, sigma=1.1)

    return x2, y2, dz2


def print_kpi_table(results):
    print("\n==================== KPI结果表（第4章仿真） ====================")
    header = (
        f"{'方案':<12}"
        f"{'入库沙量(百万t)':>14}"
        f"{'出库沙量(百万t)':>14}"
        f"{'排沙效率(%)':>12}"
        f"{'净冲淤(百万t)':>14}"
        f"{'异重流排沙(百万t)':>16}"
        f"{'三角洲%':>10}"
        f"{'锥体%':>8}"
        f"{'异重流区%':>10}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        print(
            f"{r['name']:<12}"
            f"{r['win_t']/1e6:>14.3f}"
            f"{r['wout_t']/1e6:>14.3f}"
            f"{r['eta']:>12.1f}"
            f"{r['net_mass_t']/1e6:>14.3f}"
            f"{r['wvent_t']/1e6:>16.3f}"
            f"{r['delta_pct']:>10.1f}"
            f"{r['cone_pct']:>8.1f}"
            f"{r['density_pct']:>10.1f}"
        )


def plot_results(x, t_day, qin, cin, zb0, results, x2, y2, dz2):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 图1：水沙过程线（入流与各方案出流）
    ax = axes[0, 0]
    ax.plot(t_day, qin, "k-", lw=2.0, label="入库流量Qin")
    for r in results:
        ax.plot(t_day, r["ts_qout"], lw=1.6, label=f"{r['name']} Qout")
    ax.set_xlabel("时间(天)")
    ax.set_ylabel("流量(m³/s)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, ncol=2)

    # 图2：坝前出库含沙量过程
    ax = axes[0, 1]
    ax.plot(t_day, cin, "k--", lw=1.7, label="入库含沙量Cin")
    for r in results:
        ax.plot(t_day, r["ts_cout"], lw=1.6, label=f"{r['name']} Cout")
    ax.set_xlabel("时间(天)")
    ax.set_ylabel("含沙量(kg/m³)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)

    # 图3：最终河床纵剖变化
    ax = axes[1, 0]
    ax.plot(x / 1000.0, zb0, "k--", lw=2.0, label="初始河床")
    for r in results:
        ax.plot(x / 1000.0, r["zb"], lw=1.8, label=f"{r['name']} 最终河床")
    ax.set_xlabel("距库尾距离(km)")
    ax.set_ylabel("河床高程(m)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)

    # 图4：二维沉积/冲刷分布示意（最优排沙方案）
    ax = axes[1, 1]
    im = ax.contourf(x2 / 1000.0, y2, dz2, levels=20, cmap="RdBu_r")
    ax.set_xlabel("距库尾距离(km)")
    ax.set_ylabel("横向坐标(m)")
    ax.set_title("二维非平衡输沙示意：床面变化Δz(m)")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Δz (m)")

    fig.suptitle("第4章 水库淤积与排沙：一维-二维耦合教学仿真", fontsize=14)
    fig.tight_layout()
    plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    x = np.linspace(0.0, L, NX)
    t = np.arange(NT) * DT
    t_day = t / 86400.0

    zb0 = build_initial_bed(x)
    qin, cin = build_inflow_series(t_day)
    scenarios = scenario_configs()

    results = []
    for name, cfg in scenarios.items():
        results.append(run_1d_model(name, cfg, x, qin, cin, t_day, zb0))

    # 按排沙效率排序便于比较
    results_sorted = sorted(results, key=lambda r: r["eta"], reverse=True)
    print_kpi_table(results_sorted)

    best = results_sorted[0]
    print(f"\n最优排沙效率方案：{best['name']}，排沙效率 = {best['eta']:.1f}%")

    # 二维示意只对最优方案执行，避免计算冗余
    x2, y2, dz2 = run_2d_demo(best, qin, cin, x, t_day)

    # 绘图
    plot_results(x, t_day, qin, cin, zb0, results, x2, y2, dz2)


if __name__ == "__main__":
    main()
