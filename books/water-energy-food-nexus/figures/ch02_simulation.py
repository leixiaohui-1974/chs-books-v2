# -*- coding: utf-8 -*-
"""
教材：《水-能-粮纽带系统建模》
章节：第2章 水-能耦合建模（2.1 基本概念与理论框架）
功能：构建水-能双系统耦合动态仿真，输出KPI结果表格并绘制过程图
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# =========================
# 1) 关键参数定义（可直接调参）
# =========================
SIM_DAYS = 365                      # 仿真时长（天）
TIME_SPAN = (0, SIM_DAYS)
T_EVAL = np.arange(0, SIM_DAYS + 1, 1)

# 初始状态：可用水量、可用能量储备
W0 = 150.0                          # 百万m^3
E0 = 120.0                          # GWh

# 基础需求与增长
BASE_W_DEMAND = 0.42                # 基础需水（百万m^3/天）
BASE_E_DEMAND = 0.35                # 基础需能（GWh/天）
GROWTH_W = 0.0007                   # 需水日增长率
GROWTH_E = 0.0008                   # 需能日增长率
SEASON_W = 0.12                     # 需水季节波动幅度
SEASON_E = 0.10                     # 需能季节波动幅度

# 外部补给（入流/发电）与季节波动
BASE_W_INFLOW = 0.68                # 来水补给（百万m^3/天）
BASE_E_GEN = 0.62                   # 发电补给（GWh/天）
INFLOW_SEASON = 0.25
GEN_SEASON = 0.15
PHASE_W = 0.3                       # 相位（弧度）
PHASE_E = 1.0

# 系统供给能力（与存量成比例）
K_W = 0.015                         # 水系统最大供给系数（1/天）
K_E = 0.018                         # 能源系统最大供给系数（1/天）

# 水-能耦合参数
ALPHA_WE = 0.55                     # 每单位供水需要的能量（GWh / 百万m^3）
BETA_EW = 0.38                      # 每单位供能需要的水量（百万m^3 / GWh）

# 过程损耗与回用
REUSE_RATE = 0.12                   # 供水回用比例
LOSS_W = 0.0010                     # 水系统自然损耗（1/天）
LOSS_E = 0.0008                     # 能源系统自然损耗（1/天）


# =========================
# 2) 需求与补给函数
# =========================
def water_demand(t):
    """基础需水：增长 + 季节波动"""
    return BASE_W_DEMAND * (1 + GROWTH_W * t) * (1 + SEASON_W * np.sin(2 * np.pi * t / 365))


def energy_demand(t):
    """基础需能：增长 + 季节波动"""
    return BASE_E_DEMAND * (1 + GROWTH_E * t) * (1 + SEASON_E * np.cos(2 * np.pi * t / 365 + 0.5))


def water_inflow(t):
    """外部来水补给"""
    return BASE_W_INFLOW * (1 + INFLOW_SEASON * np.sin(2 * np.pi * t / 365 + PHASE_W))


def energy_generation(t):
    """外部发电补给"""
    return BASE_E_GEN * (1 + GEN_SEASON * np.cos(2 * np.pi * t / 365 + PHASE_E))


# =========================
# 3) 耦合供给求解（固定点迭代）
# =========================
def coupled_supply(W, E, d_w, d_e, n_iter=20):
    """
    在给定存量 W,E 下，求解耦合后的供水/供能：
    - 能源需求 = 基础需能 + 供水耗能
    - 供水需求 = 基础需水 + 发电耗水
    """
    max_w = max(K_W * max(W, 0.0), 0.0)
    max_e = max(K_E * max(E, 0.0), 0.0)

    # 初始化：先按基础需求估计
    s_w = min(d_w, max_w)
    s_e = min(d_e, max_e)

    for _ in range(n_iter):
        e_req = d_e + ALPHA_WE * s_w
        s_e_new = min(e_req, max_e)

        w_req = d_w + BETA_EW * s_e_new
        s_w_new = min(w_req, max_w)

        if abs(s_w_new - s_w) < 1e-9 and abs(s_e_new - s_e) < 1e-9:
            s_w, s_e = s_w_new, s_e_new
            break
        s_w, s_e = s_w_new, s_e_new

    # 输出需求侧总请求（用于压力指标）
    final_e_req = d_e + ALPHA_WE * s_w
    final_w_req = d_w + BETA_EW * s_e
    return s_w, s_e, final_w_req, final_e_req


# =========================
# 4) 动态方程
# =========================
def nexus_ode(t, y):
    """状态变量 y=[W, E]"""
    W, E = y
    d_w = water_demand(t)
    d_e = energy_demand(t)

    s_w, s_e, _, _ = coupled_supply(W, E, d_w, d_e)

    # 水量变化：来水 - 供水 + 回用 - 损耗
    dWdt = water_inflow(t) - s_w + REUSE_RATE * s_w - LOSS_W * W
    # 能量变化：发电 - 供能 - 损耗
    dEdt = energy_generation(t) - s_e - LOSS_E * E
    return [dWdt, dEdt]


# =========================
# 5) 主程序：求解、KPI、绘图
# =========================
def main():
    # 中文显示设置（若本机无中文字体，图仍可运行）
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    # 求解常微分方程
    sol = solve_ivp(
        nexus_ode,
        TIME_SPAN,
        [W0, E0],
        t_eval=T_EVAL,
        method="RK45",
        max_step=1.0,
        rtol=1e-6,
        atol=1e-8
    )
    if not sol.success:
        raise RuntimeError(f"积分失败：{sol.message}")

    t = sol.t
    W = sol.y[0]
    E = sol.y[1]

    # 后处理：逐时刻计算需求、供给、压力
    d_w_arr, d_e_arr = [], []
    s_w_arr, s_e_arr = [], []
    w_req_arr, e_req_arr = [], []
    for i in range(len(t)):
        d_w = water_demand(t[i])
        d_e = energy_demand(t[i])
        s_w, s_e, w_req, e_req = coupled_supply(W[i], E[i], d_w, d_e)
        d_w_arr.append(d_w)
        d_e_arr.append(d_e)
        s_w_arr.append(s_w)
        s_e_arr.append(s_e)
        w_req_arr.append(w_req)
        e_req_arr.append(e_req)

    d_w_arr = np.array(d_w_arr)
    d_e_arr = np.array(d_e_arr)
    s_w_arr = np.array(s_w_arr)
    s_e_arr = np.array(s_e_arr)
    w_req_arr = np.array(w_req_arr)
    e_req_arr = np.array(e_req_arr)

    # 耦合耗用项
    energy_for_water = ALPHA_WE * s_w_arr
    water_for_energy = BETA_EW * s_e_arr

    # KPI 计算
    water_rel = np.mean(s_w_arr >= d_w_arr) * 100.0
    energy_rel = np.mean(s_e_arr >= d_e_arr) * 100.0
    avg_w_short = np.mean(np.maximum(0.0, d_w_arr - s_w_arr))
    avg_e_short = np.mean(np.maximum(0.0, d_e_arr - s_e_arr))
    coupling_e_share = np.mean(energy_for_water / (s_e_arr + 1e-9)) * 100.0
    coupling_w_share = np.mean(water_for_energy / (s_w_arr + 1e-9)) * 100.0

    water_stress = w_req_arr / (K_W * np.maximum(W, 1e-9))
    energy_stress = e_req_arr / (K_E * np.maximum(E, 1e-9))
    nexus_risk = np.mean((np.clip(water_stress, 0, 2) + np.clip(energy_stress, 0, 2)) / 2) * 50.0

    kpi_table = [
        ("水系统可靠性(%)", water_rel),
        ("能源系统可靠性(%)", energy_rel),
        ("平均供水缺口(百万m^3/天)", avg_w_short),
        ("平均供能缺口(GWh/天)", avg_e_short),
        ("供水耗能占供能比例(%)", coupling_e_share),
        ("发电耗水占供水比例(%)", coupling_w_share),
        ("末期可用水量(百万m^3)", W[-1]),
        ("末期可用能量(GWh)", E[-1]),
        ("纽带综合风险指数(0-100)", nexus_risk),
    ]

    # 打印 KPI 表格
    print("\n=== 水-能耦合建模 KPI 结果 ===")
    print(f"{'指标':<24} {'数值':>14}")
    print("-" * 40)
    for name, value in kpi_table:
        print(f"{name:<24} {value:>14.4f}")

    # 绘图
    fig, axs = plt.subplots(2, 2, figsize=(13, 9))

    # 图1：系统存量
    axs[0, 0].plot(t, W, label="可用水量 W", lw=2)
    axs[0, 0].plot(t, E, label="可用能量 E", lw=2)
    axs[0, 0].set_title("系统存量演化")
    axs[0, 0].set_xlabel("时间（天）")
    axs[0, 0].set_ylabel("存量")
    axs[0, 0].grid(alpha=0.3)
    axs[0, 0].legend()

    # 图2：水系统需求-供给
    axs[0, 1].plot(t, d_w_arr, label="基础需水", lw=2)
    axs[0, 1].plot(t, s_w_arr, label="实际供水", lw=2)
    axs[0, 1].plot(t, water_for_energy, label="发电耗水", lw=1.8, ls="--")
    axs[0, 1].set_title("水系统耦合过程")
    axs[0, 1].set_xlabel("时间（天）")
    axs[0, 1].set_ylabel("百万m^3/天")
    axs[0, 1].grid(alpha=0.3)
    axs[0, 1].legend()

    # 图3：能源系统需求-供给
    axs[1, 0].plot(t, d_e_arr, label="基础需能", lw=2)
    axs[1, 0].plot(t, s_e_arr, label="实际供能", lw=2)
    axs[1, 0].plot(t, energy_for_water, label="供水耗能", lw=1.8, ls="--")
    axs[1, 0].set_title("能源系统耦合过程")
    axs[1, 0].set_xlabel("时间（天）")
    axs[1, 0].set_ylabel("GWh/天")
    axs[1, 0].grid(alpha=0.3)
    axs[1, 0].legend()

    # 图4：压力指标
    axs[1, 1].plot(t, water_stress, label="水压力指数", lw=2)
    axs[1, 1].plot(t, energy_stress, label="能压力指数", lw=2)
    axs[1, 1].axhline(1.0, color="r", ls="--", lw=1.2, label="临界值=1")
    axs[1, 1].set_title("系统压力与风险信号")
    axs[1, 1].set_xlabel("时间（天）")
    axs[1, 1].set_ylabel("无量纲")
    axs[1, 1].grid(alpha=0.3)
    axs[1, 1].legend()

    plt.tight_layout()
    plt.savefig('ch02_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch02_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
