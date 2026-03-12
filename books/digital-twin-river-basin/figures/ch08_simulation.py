# -*- coding: utf-8 -*-
"""
教材：《流域数字孪生与智能决策》
章节：第8章 案例：典型流域数字孪生（8.1 基本概念与理论框架）
功能：构建“感知数据→机理模型→调度决策→KPI评价”的简化闭环仿真脚本
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy.stats import gamma
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# 中文显示（若本机无对应字体，可删去这两行）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 1) 关键参数（集中定义）
# =========================
DT_H = 1.0                   # 时间步长（小时）
SIM_HOURS = 96               # 总仿真时长（小时）
TIME_H = np.arange(0, SIM_HOURS + DT_H, DT_H)
N = len(TIME_H)

# 流域产汇流参数
BASIN_AREA_KM2 = 450.0       # 流域面积（km2）
RUNOFF_COEFF = 0.60          # 产流系数
INITIAL_LOSS_MM = 3.0        # 初损（mm/h）
BASEFLOW_M3S = 28.0          # 基流（m3/s）

# 单位线参数（Gamma分布）
UH_SHAPE = 3.0
UH_SCALE = 2.5
UH_LEN = 24                  # 单位线长度（小时）

# 水库/闸坝参数
S0_MCM = 120.0               # 初始库容（百万m3）
Z0_M = 27.2                  # 初始水位（m）
Z_MIN_M = 25.8               # 最低运行水位（m）
Z_MAX_M = 30.2               # 最高安全水位（m）
RES_AREA_M2 = 9.0e7          # 等效水面面积（m2）
Q_GATE_MAX = 900.0           # 最大下泄能力（m3/s）
Q_ECO_MIN = 90.0             # 生态最小流量（m3/s）

# 河道汇流参数（Muskingum）
K_H = 2.5
X_MUSKINGUM = 0.2
SAFE_FLOW = 700.0            # 下游安全流量阈值（m3/s）

# 目标函数权重
W_PEAK = 1.0
W_FLOW_DUR = 80.0
W_LEVEL_HIGH = 220.0
W_LEVEL_LOW = 100.0

# =========================
# 2) 感知层：构造降雨过程
# =========================
def build_rainfall(time_h: np.ndarray) -> np.ndarray:
    """生成典型双峰暴雨过程（mm/h）"""
    p1 = 16.0 * np.exp(-0.5 * ((time_h - 30.0) / 5.0) ** 2)
    p2 = 24.0 * np.exp(-0.5 * ((time_h - 48.0) / 6.0) ** 2)
    rain = p1 + p2
    rain[time_h < 8] = 0.0
    return rain


# =========================
# 3) 模型层：降雨→入库流量
# =========================
def rainfall_to_inflow(rain_mm_h: np.ndarray) -> np.ndarray:
    """初损+产流+单位线汇流，输出入库流量（m3/s）"""
    # 有效雨强
    pe = np.maximum(rain_mm_h - INITIAL_LOSS_MM, 0.0)
    runoff_mm_h = RUNOFF_COEFF * pe

    # mm/h -> m3/s（1mm * 1km2 = 1000m3）
    q_raw = runoff_mm_h * BASIN_AREA_KM2 * 1000.0 / 3600.0

    # Gamma单位线（体现流域汇流滞后）
    t = np.arange(1, UH_LEN + 1)
    uh = gamma.pdf(t, a=UH_SHAPE, scale=UH_SCALE)
    uh = uh / (uh.sum() + 1e-12)

    q_routed = np.convolve(q_raw, uh, mode="full")[:len(rain_mm_h)]
    q_in = q_routed + BASEFLOW_M3S
    return q_in


def gate_schedule(u_vec: np.ndarray, time_h: np.ndarray) -> np.ndarray:
    """三阶段闸门开度策略"""
    u1, u2, u3 = u_vec
    u = np.zeros_like(time_h, dtype=float)
    u[time_h < 28] = u1                 # 预泄期
    u[(time_h >= 28) & (time_h < 58)] = u2  # 洪峰期
    u[time_h >= 58] = u3                # 恢复期
    return u


def muskingum_route(i_flow: np.ndarray, dt_h: float, k_h: float, x: float) -> np.ndarray:
    """Muskingum河道演算"""
    den = 2 * k_h * (1 - x) + dt_h
    c0 = (dt_h - 2 * k_h * x) / den
    c1 = (dt_h + 2 * k_h * x) / den
    c2 = (2 * k_h * (1 - x) - dt_h) / den

    q = np.zeros_like(i_flow)
    q[0] = i_flow[0]
    for t in range(1, len(i_flow)):
        q[t] = c0 * i_flow[t] + c1 * i_flow[t - 1] + c2 * q[t - 1]
        q[t] = max(q[t], 0.0)
    return q


def simulate(u_vec: np.ndarray, rain_mm_h: np.ndarray) -> dict:
    """闭环仿真：入流-调度-库容水位-下游流量"""
    q_in = rainfall_to_inflow(rain_mm_h)
    u = gate_schedule(u_vec, TIME_H)

    storage = np.zeros(N)   # 百万m3
    level = np.zeros(N)     # m
    q_rel = np.zeros(N)     # m3/s

    storage[0] = S0_MCM
    level[0] = Z0_M

    for t in range(1, N):
        # 计划下泄 = 开度 * 最大能力，并满足生态下限
        q_plan = max(u[t] * Q_GATE_MAX, Q_ECO_MIN)

        # 物理可放水上限（避免出现负库容）
        available_m3 = storage[t - 1] * 1e6 + q_in[t] * DT_H * 3600.0
        q_phys_max = available_m3 / (DT_H * 3600.0)
        q_rel[t] = min(q_plan, q_phys_max)

        # 水量平衡
        dS_m3 = (q_in[t] - q_rel[t]) * DT_H * 3600.0
        storage[t] = storage[t - 1] + dS_m3 / 1e6

        # 简化水位-库容关系
        level[t] = Z0_M + (storage[t] - S0_MCM) * 1e6 / RES_AREA_M2

    # 下游控制断面入流 = 闸下泄 + 沿程来水（按入库流量25%）
    q_channel_in = q_rel + 0.25 * q_in
    q_down = muskingum_route(q_channel_in, DT_H, K_H, X_MUSKINGUM)

    return {
        "rain": rain_mm_h,
        "qin": q_in,
        "u": u,
        "q_release": q_rel,
        "q_down": q_down,
        "storage": storage,
        "level": level,
    }


# =========================
# 4) KPI评价与优化层
# =========================
def calc_kpi(sim: dict) -> dict:
    qd = sim["q_down"]
    lv = sim["level"]

    return {
        "Peak_Q(m3/s)": float(np.max(qd)),
        "Peak_Time(h)": float(TIME_H[np.argmax(qd)]),
        "Max_Level(m)": float(np.max(lv)),
        "Exceed_Flow_Dur(h)": float(np.sum(qd > SAFE_FLOW) * DT_H),
        "Exceed_Level_Dur(h)": float(np.sum(lv > Z_MAX_M) * DT_H),
        "Below_MinLevel_Dur(h)": float(np.sum(lv < Z_MIN_M) * DT_H),
    }


def objective(u_vec: np.ndarray, rain_mm_h: np.ndarray) -> float:
    sim = simulate(u_vec, rain_mm_h)
    k = calc_kpi(sim)

    # 目标：压低洪峰，同时惩罚超警时长和水位越界
    score = (
        W_PEAK * k["Peak_Q(m3/s)"]
        + W_FLOW_DUR * k["Exceed_Flow_Dur(h)"]
        + W_LEVEL_HIGH * k["Exceed_Level_Dur(h)"]
        + W_LEVEL_LOW * k["Below_MinLevel_Dur(h)"]
    )
    return score


def print_kpi_table(k_base: dict, k_opt: dict) -> None:
    print("\nKPI结果表格")
    print("+----------------------+-------------+-------------+----------------+")
    print("| 指标                 | 基准调度    | 优化调度    | 改善/变化       |")
    print("+----------------------+-------------+-------------+----------------+")
    for key in k_base:
        b = k_base[key]
        o = k_opt[key]
        if key == "Peak_Time(h)":
            imp = f"{(o - b):+.2f} h"
        else:
            imp = "0.00%" if abs(b) < 1e-12 else f"{(b - o) / abs(b) * 100:+.2f}%"
        print(f"| {key:<20} | {b:>11.2f} | {o:>11.2f} | {imp:>14} |")
    print("+----------------------+-------------+-------------+----------------+")


def plot_results(base: dict, opt: dict) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

    axes[0].bar(TIME_H, base["rain"], width=0.9, color="steelblue", alpha=0.8, label="降雨(mm/h)")
    axes[0].set_ylabel("降雨")
    axes[0].set_title("典型流域数字孪生仿真：降雨-产汇流-调度预演")
    axes[0].grid(alpha=0.25)
    axes[0].legend(loc="upper right")

    axes[1].plot(TIME_H, base["qin"], "k--", lw=1.4, label="入库流量")
    axes[1].plot(TIME_H, base["q_down"], color="tomato", lw=2.0, label="下游流量-基准")
    axes[1].plot(TIME_H, opt["q_down"], color="seagreen", lw=2.2, label="下游流量-优化")
    axes[1].axhline(SAFE_FLOW, color="gray", ls=":", lw=1.2, label="安全阈值")
    axes[1].set_ylabel("流量(m3/s)")
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="upper right")

    axes[2].plot(TIME_H, base["level"], color="orange", lw=2.0, label="水位-基准")
    axes[2].plot(TIME_H, opt["level"], color="royalblue", lw=2.2, label="水位-优化")
    axes[2].axhline(Z_MAX_M, color="red", ls="--", lw=1.2, label="最高安全水位")
    axes[2].axhline(Z_MIN_M, color="purple", ls="--", lw=1.2, label="最低运行水位")
    axes[2].set_xlabel("时间(h)")
    axes[2].set_ylabel("水位(m)")
    axes[2].grid(alpha=0.25)
    axes[2].legend(loc="upper right")

    plt.tight_layout()
    plt.savefig('ch08_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch08_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    rain = build_rainfall(TIME_H)

    # 基准方案
    u_base = np.array([0.22, 0.75, 0.35])
    sim_base = simulate(u_base, rain)
    kpi_base = calc_kpi(sim_base)

    # 优化方案
    x0 = np.array([0.30, 0.55, 0.30])
    bounds = [(0.05, 0.95), (0.20, 0.95), (0.05, 0.90)]
    res = minimize(
        objective,
        x0=x0,
        args=(rain,),
        method="SLSQP",
        bounds=bounds,
        options={"maxiter": 120, "ftol": 1e-6, "disp": False},
    )

    u_opt = np.clip(res.x, [b[0] for b in bounds], [b[1] for b in bounds])
    sim_opt = simulate(u_opt, rain)
    kpi_opt = calc_kpi(sim_opt)

    print("优化收敛状态:", res.success)
    print("优化信息:", res.message)
    print("优化闸门参数 [u1, u2, u3] =", np.round(u_opt, 4))

    print_kpi_table(kpi_base, kpi_opt)
    plot_results(sim_base, sim_opt)


if __name__ == "__main__":
    main()
