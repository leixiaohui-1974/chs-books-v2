# -*- coding: utf-8 -*-
"""
教材：《洪水预报与防洪调度》
章节：第5章 堤防安全评估
功能：仿真“非稳定渗流-稳定安全系数-溃决演化-洪水淹没”闭环，输出KPI并绘图
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.sparse import diags, csc_matrix
from scipy.sparse.linalg import spsolve

# ------------------------------
# 0) 全局绘图设置（中文显示）
# ------------------------------
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ------------------------------
# 1) 关键参数（可按工程项目调整）
# ------------------------------
np.random.seed(42)  # 固定随机种子，便于教学复现

T_hour = 240.0       # 总仿真时长（h）
dt_hour = 1.0        # 时间步长（h）
dt_sec = dt_hour * 3600.0
t = np.arange(0.0, T_hour + dt_hour, dt_hour)
nt = len(t)

# 空间离散（堤基一维渗流剖面）
L = 60.0             # 计算域长度（m）
Nx = 121             # 网格点
x = np.linspace(0.0, L, Nx)
dx = x[1] - x[0]

# 水位与几何
H_land_m = 21.0      # 背水侧基准水位（m）
levee_crest_m = 33.0 # 堤顶高程（m）

# 水力扩散系数（真值用于构造“观测”，模型值用于预报）
D_true = 0.080       # m2/s
D_model = 0.060      # m2/s（带偏差，体现模型不确定性）

# 边坡稳定参数（简化无限边坡法）
slope_angle_deg = 20.0
phi_deg = 30.0
c_kpa = 18.0
gamma_sat = 19.0e3   # N/m3
slip_depth = 6.0     # m
i_crit = 0.85        # 临界出逸坡降

# 损伤与溃决参数
damage_crit = 0.65
k_damage_i = 0.080
k_damage_fs = 0.150
k_breach = 0.45      # m/h
B_max = 16.0         # m
C_weir = 0.90        # 宽顶堰综合系数

# 保护区淹没参数
polder_area_m2 = 2.5e7
drain_coeff = 25.0
risk_depth_ref = 1.5

# 数据同化参数
sensor_x = np.array([8.0, 18.0, 35.0, 52.0])
sensor_idx = np.array([int(round(v / dx)) for v in sensor_x], dtype=int)
obs_every = 3
obs_sigma = 0.08
assim_gain = 0.55


def build_river_level(t_hour):
    """构造双峰外水位过程（绝对高程，m）"""
    base = 24.0
    peak1 = 6.0 * np.exp(-0.5 * ((t_hour - 72.0) / 18.0) ** 2)
    peak2 = 4.5 * np.exp(-0.5 * ((t_hour - 132.0) / 16.0) ** 2)
    tail = 1.2 * np.exp(-np.maximum(t_hour - 150.0, 0.0) / 45.0)
    H = base + peak1 + peak2 + tail
    return np.clip(H, 22.0, 34.2)


def build_matrix(n, r):
    """组装隐式差分三对角矩阵"""
    main = (1.0 + 2.0 * r) * np.ones(n - 2)
    off = -r * np.ones(n - 3)
    A = diags([off, main, off], offsets=[-1, 0, 1], format="csc")
    return csc_matrix(A)


def run_simulation(diffusivity, H_river, params, truth_h=None, obs_dict=None, use_assim=False):
    """
    运行一次堤防安全评估仿真
    diffusivity: 水力扩散系数
    truth_h: 真值水头场（用于RMSE评估）
    obs_dict: 观测字典（k -> 传感器观测向量）
    use_assim: 是否启用同化
    """
    r = diffusivity * dt_sec / (dx ** 2)
    A = build_matrix(Nx, r)

    # 状态变量初始化
    h = np.zeros(Nx)                 # 当前步水头（相对背水侧）
    h_fields = np.zeros((nt, Nx))    # 全时段水头场

    exit_grad = np.zeros(nt)         # 背水侧出逸坡降
    FS = np.zeros(nt)                # 稳定安全系数
    damage = np.zeros(nt)            # 累计损伤（0~1）
    breach_width = np.zeros(nt)      # 溃口宽度
    Q_breach = np.zeros(nt)          # 溃口流量
    V_inland = np.zeros(nt)          # 保护区蓄水体积
    H_inland = np.zeros(nt)          # 保护区平均淹深
    risk = np.zeros(nt)              # 综合风险指数
    rmse = np.full(nt, np.nan)       # 相对真值误差

    breach_start_idx = None

    theta = np.deg2rad(params["slope_angle_deg"])
    phi = np.deg2rad(params["phi_deg"])
    c_pa = params["c_kpa"] * 1000.0
    slip_zone = (x >= 0.45 * L) & (x <= 0.90 * L)

    for k in range(nt):
        # 边界条件：迎水侧定水头，背水侧定水头
        left_bc = max(H_river[k] - params["H_land_m"], 0.0)
        right_bc = 0.0

        # 非稳定渗流隐式推进
        if k == 0:
            h[:] = np.linspace(left_bc, right_bc, Nx)
        else:
            b = h[1:-1].copy()
            b[0] += r * left_bc
            b[-1] += r * right_bc
            h[1:-1] = spsolve(A, b)
            h[0] = left_bc
            h[-1] = right_bc

        # 数据同化（Nudging）
        if use_assim and (obs_dict is not None) and (k in obs_dict):
            y_obs = obs_dict[k]
            h[sensor_idx] = h[sensor_idx] + params["assim_gain"] * (y_obs - h[sensor_idx])

        h_fields[k, :] = h

        # 出逸坡降
        exit_grad[k] = max((h[-2] - h[-1]) / dx, 0.0)

        # 极限平衡简化安全系数
        ru = np.clip(np.mean(h[slip_zone]) / (params["slip_depth"] + 1e-6), 0.0, 0.99)
        term_c = c_pa / (params["gamma_sat"] * params["slip_depth"] * np.sin(theta) * np.cos(theta))
        term_phi = (np.tan(phi) / np.tan(theta)) * (1.0 - ru)
        FS[k] = max(term_c + term_phi, 0.05)

        # 损伤累计
        if k > 0:
            over_i = max(exit_grad[k] / params["i_crit"] - 1.0, 0.0)
            over_fs = max(1.0 - FS[k], 0.0)
            dD = (params["k_damage_i"] * over_i + params["k_damage_fs"] * over_fs) * dt_hour
            damage[k] = np.clip(damage[k - 1] + dD, 0.0, 1.0)

        # 溃决触发判定
        if breach_start_idx is None:
            if (damage[k] >= params["damage_crit"]) and (exit_grad[k] > 0.6 * params["i_crit"]):
                breach_start_idx = k

        # 溃口展宽
        if k > 0:
            breach_width[k] = breach_width[k - 1]
        if breach_start_idx is not None and k >= breach_start_idx:
            h_over = max(H_river[k] - params["levee_crest_m"], 0.0)
            i_over = max(exit_grad[k] / params["i_crit"] - 1.0, 0.0)
            dB = params["k_breach"] * (h_over + 0.8 * i_over) ** 1.25 * dt_hour
            breach_width[k] = np.clip(breach_width[k] + dB, 0.0, params["B_max"])

        # 溃口流量
        if breach_width[k] > 0.0:
            delta_h = max(H_river[k] - params["H_land_m"], 0.0)
            Q_breach[k] = params["C_weir"] * breach_width[k] * delta_h ** 1.5

        # 洪水演进（保护区蓄排）
        if k > 0:
            Q_drain = params["drain_coeff"] * np.sqrt(max(H_inland[k - 1], 0.0))
            V_inland[k] = max(V_inland[k - 1] + (Q_breach[k] - Q_drain) * dt_sec, 0.0)
            H_inland[k] = V_inland[k] / params["polder_area_m2"]

        # 综合风险指标
        risk[k] = np.clip(
            0.30 * (exit_grad[k] / params["i_crit"])
            + 0.35 * (1.0 / FS[k] / 2.0)
            + 0.20 * damage[k]
            + 0.15 * np.clip(H_inland[k] / params["risk_depth_ref"], 0.0, 2.0),
            0.0, 1.5
        )

        # 与真值误差
        if truth_h is not None:
            rmse[k] = np.sqrt(np.mean((h - truth_h[k]) ** 2))

    return {
        "h_fields": h_fields,
        "exit_grad": exit_grad,
        "FS": FS,
        "damage": damage,
        "breach_width": breach_width,
        "Q_breach": Q_breach,
        "V_inland": V_inland,
        "H_inland": H_inland,
        "risk": risk,
        "rmse": rmse,
        "breach_start_idx": breach_start_idx,
    }


def print_kpi_table(rows):
    """打印ASCII KPI表格"""
    w1 = max(len(r[0]) for r in rows)
    w2 = max(len(r[1]) for r in rows)
    line = f"+{'-' * (w1 + 2)}+{'-' * (w2 + 2)}+"
    print("\n=== KPI结果表（第5章 堤防安全评估）===")
    print(line)
    print(f"| {'指标'.ljust(w1)} | {'数值'.ljust(w2)} |")
    print(line)
    for k, v in rows:
        print(f"| {k.ljust(w1)} | {v.ljust(w2)} |")
    print(line)


if __name__ == "__main__":
    # 2) 边界过程与观测构造
    H_river = build_river_level(t)
    params = {
        "H_land_m": H_land_m,
        "levee_crest_m": levee_crest_m,
        "slope_angle_deg": slope_angle_deg,
        "phi_deg": phi_deg,
        "c_kpa": c_kpa,
        "gamma_sat": gamma_sat,
        "slip_depth": slip_depth,
        "i_crit": i_crit,
        "damage_crit": damage_crit,
        "k_damage_i": k_damage_i,
        "k_damage_fs": k_damage_fs,
        "k_breach": k_breach,
        "B_max": B_max,
        "C_weir": C_weir,
        "polder_area_m2": polder_area_m2,
        "drain_coeff": drain_coeff,
        "risk_depth_ref": risk_depth_ref,
        "assim_gain": assim_gain,
    }

    # 真值模拟
    truth = run_simulation(D_true, H_river, params)

    # 构造传感器观测
    obs_dict = {}
    for k in range(0, nt, obs_every):
        obs_dict[k] = truth["h_fields"][k, sensor_idx] + np.random.normal(0.0, obs_sigma, len(sensor_idx))

    # 开环与同化模拟
    open_loop = run_simulation(D_model, H_river, params, truth_h=truth["h_fields"], use_assim=False)
    assim = run_simulation(D_model, H_river, params, truth_h=truth["h_fields"], obs_dict=obs_dict, use_assim=True)

    # 3) KPI统计
    peak_level = np.max(H_river)
    max_exit = np.max(assim["exit_grad"])
    min_fs = np.min(assim["FS"])
    max_damage = np.max(assim["damage"])
    breach_time_txt = "未触发" if assim["breach_start_idx"] is None else f"{t[assim['breach_start_idx']]:.0f} h"
    max_breach_width = np.max(assim["breach_width"])
    max_q_breach = np.max(assim["Q_breach"])
    vol_breach_mcm = np.sum(assim["Q_breach"]) * dt_sec / 1.0e6
    max_depth = np.max(assim["H_inland"])
    rmse_open = np.nanmean(open_loop["rmse"])
    rmse_assim = np.nanmean(assim["rmse"])
    rmse_gain = (rmse_open - rmse_assim) / (rmse_open + 1e-12) * 100.0
    high_risk_hours = np.sum(assim["risk"] >= 1.0) * dt_hour

    kpis = [
        ("洪峰外水位", f"{peak_level:.2f} m"),
        ("最大出逸坡降", f"{max_exit:.3f}"),
        ("最小安全系数FS", f"{min_fs:.3f}"),
        ("最大累计损伤", f"{max_damage:.3f}"),
        ("溃决触发时刻", breach_time_txt),
        ("最大溃口宽度", f"{max_breach_width:.2f} m"),
        ("最大溃口流量", f"{max_q_breach:.2f} m3/s"),
        ("溃决总水量", f"{vol_breach_mcm:.3f} 百万m3"),
        ("最大淹没深度", f"{max_depth:.3f} m"),
        ("开环RMSE", f"{rmse_open:.4f} m"),
        ("同化RMSE", f"{rmse_assim:.4f} m"),
        ("同化误差降幅", f"{rmse_gain:.2f} %"),
        ("高风险历时", f"{high_risk_hours:.0f} h"),
    ]
    print_kpi_table(kpis)

    # 4) 绘图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)

    ax = axes[0, 0]
    ax.plot(t, H_river, color="#1f77b4", lw=2.2, label="河道外水位")
    ax.axhline(levee_crest_m, color="black", ls="--", lw=1.4, label="堤顶高程")
    ax.axhline(H_land_m, color="gray", ls=":", lw=1.2, label="背水侧基准水位")
    if assim["breach_start_idx"] is not None:
        ax.axvline(t[assim["breach_start_idx"]], color="red", ls="--", lw=1.2, label="溃决触发")
    ax.set_ylabel("水位 (m)")
    ax.set_title("(a) 外部水位边界")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", fontsize=9)

    ax = axes[0, 1]
    ax.plot(t, open_loop["exit_grad"], color="#ff7f0e", lw=1.6, alpha=0.75, label="开环出逸坡降")
    ax.plot(t, assim["exit_grad"], color="#2ca02c", lw=2.0, label="同化出逸坡降")
    ax.axhline(i_crit, color="red", ls="--", lw=1.3, label="临界坡降")
    ax.set_ylabel("坡降 (-)")
    ax.set_title("(b) 背水侧出逸坡降")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", fontsize=9)

    ax = axes[1, 0]
    ax.plot(t, open_loop["FS"], color="#9467bd", lw=1.5, alpha=0.75, label="开环FS")
    ax.plot(t, assim["FS"], color="#8c564b", lw=2.0, label="同化FS")
    ax.axhline(1.0, color="red", ls="--", lw=1.2, label="FS=1.0")
    ax.set_ylabel("安全系数 FS")
    ax.grid(alpha=0.25)
    ax.set_title("(c) 稳定与损伤演化")
    ax2 = ax.twinx()
    ax2.plot(t, assim["damage"], color="#17becf", lw=1.8, label="累计损伤D")
    ax2.axhline(damage_crit, color="#17becf", ls=":", lw=1.2, label="损伤阈值")
    ax2.set_ylabel("损伤 D")
    l1, lb1 = ax.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax2.legend(l1 + l2, lb1 + lb2, loc="upper right", fontsize=8)

    ax = axes[1, 1]
    ax.plot(t, assim["Q_breach"], color="#d62728", lw=2.0, label="溃口流量")
    ax.plot(t, assim["breach_width"], color="#bcbd22", lw=1.8, label="溃口宽度")
    ax.set_ylabel("流量/宽度")
    ax.grid(alpha=0.25)
    ax.set_title("(d) 溃口动力学与淹没演进")
    ax2 = ax.twinx()
    ax2.plot(t, assim["H_inland"], color="#1f77b4", lw=2.0, label="保护区淹深")
    ax2.set_ylabel("淹深 (m)")
    l1, lb1 = ax.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax2.legend(l1 + l2, lb1 + lb2, loc="upper left", fontsize=8)

    for a in axes[1, :]:
        a.set_xlabel("时间 (h)")

    fig.suptitle("第5章 堤防安全评估：多过程耦合仿真", fontsize=14)
    plt.tight_layout()
    plt.savefig('ch05_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch05_simulation_result.png")
# plt.show()  # 禁用弹窗
