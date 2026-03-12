# -*- coding: utf-8 -*-
# 《水-能源-粮食纽带关系》第6章 案例：流域WEF综合管理
# 功能：基于“6.1 基本概念与理论框架”构建流域WEF耦合仿真与优化，
#      输出KPI结果表格，并生成matplotlib图用于教学展示。

import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（统一变量定义，便于调参与情景分析）
# =========================
N_MONTHS = 12

# 月尺度输入（单位见注释）
INFLOW = np.array([9, 8, 11, 14, 18, 24, 28, 26, 20, 15, 11, 9], dtype=float)  # 来水(百万m3/月)
AGRI_DEMAND = np.array([5, 5, 7, 9, 12, 14, 13, 12, 10, 8, 6, 5], dtype=float)  # 农业需水
ECO_DEMAND = np.array([3.0, 3.0, 3.2, 3.5, 3.8, 4.2, 4.5, 4.3, 4.0, 3.6, 3.2, 3.0], dtype=float)  # 生态需水
URBAN_DEMAND = np.array([2.8, 2.8, 3.0, 3.2, 3.3, 3.5, 3.6, 3.6, 3.4, 3.2, 3.0, 2.9], dtype=float)  # 城镇需水
ENERGY_DEMAND = np.array([11, 10.5, 10.5, 11.2, 12.0, 13.0, 13.5, 13.2, 12.4, 11.8, 11.2, 11.0], dtype=float)  # 净能源需求(GWh)

EXTERNAL_ENERGY = np.array([13.5] * N_MONTHS, dtype=float)  # 外部可获得电力(GWh)

# 水库与调度参数
S0 = 42.0       # 初始库容(百万m3)
S_MIN = 20.0    # 库容下限
S_MAX = 78.0    # 库容上限
R_MAX = 30.0    # 月最大下泄(百万m3)
EVAP_RATE = 0.008  # 蒸发损失系数

# WEF耦合参数
CANAL_EFF = 0.85       # 输配水效率
K_HYDRO = 0.78         # 水电转换系数(GWh/(百万m3))
PUMP_INTENSITY = 0.22  # 提灌耗能系数(GWh/(百万m3))
REUSE_EFF = 0.35       # 再生水回收系数(百万m3/GWh)
GRAIN_TARGET = 120.0   # 年粮食目标(万吨)
FOOD_ELASTICITY = 0.92 # 产量弹性

# 多目标权重（理论框架中的“目标协调”）
W_FOOD = 0.28
W_ENERGY = 0.26
W_ECO = 0.22
W_URBAN = 0.14
W_COORD = 0.10
W_COST = 0.06
W_EMISSION = 0.04

# 成本与碳排参数
WATER_COST = 0.12
ENERGY_COST = 0.55
GRID_EMISSION = 0.62
HYDRO_OFFSET = 0.58


# =========================
# 2) 模型函数
# =========================
def simulate_policy(x):
    """
    给定决策向量，执行12个月仿真。
    决策变量：
    x[0:12]   -> 月下泄量 release_t
    x[12]     -> 农业分水比例 alpha_agri
    x[13]     -> 生态分水比例 beta_eco
    x[14]     -> 再生水用能比例 gamma_reuse
    """
    release = x[:N_MONTHS]
    alpha_agri = x[N_MONTHS]
    beta_eco = x[N_MONTHS + 1]
    gamma_reuse = x[N_MONTHS + 2]

    storage = np.zeros(N_MONTHS + 1)
    storage[0] = S0

    agri_supply = np.zeros(N_MONTHS)
    eco_supply = np.zeros(N_MONTHS)
    urban_supply = np.zeros(N_MONTHS)
    hydro = np.zeros(N_MONTHS)
    net_energy = np.zeros(N_MONTHS)
    pump_energy = np.zeros(N_MONTHS)
    treat_energy = np.zeros(N_MONTHS)
    reused_water = np.zeros(N_MONTHS)

    for t in range(N_MONTHS):
        evap = EVAP_RATE * max(storage[t], 0.0)
        available = storage[t] + INFLOW[t] - evap
        r = release[t]

        # 水电产出：与下泄量和库容水头近似相关
        hydro[t] = K_HYDRO * max(r, 0.0) * np.sqrt(max(storage[t], 1e-6) / S_MAX)
        energy_pool = EXTERNAL_ENERGY[t] + hydro[t]

        # 再生水处理
        treat_energy[t] = gamma_reuse * max(energy_pool, 0.0)
        reused_water[t] = REUSE_EFF * treat_energy[t]

        # 配水
        agri_supply[t] = CANAL_EFF * alpha_agri * r + reused_water[t]
        eco_supply[t] = beta_eco * r
        urban_supply[t] = max(0.0, 1.0 - alpha_agri - beta_eco) * r

        # 能量平衡
        pump_energy[t] = PUMP_INTENSITY * agri_supply[t]
        net_energy[t] = energy_pool - treat_energy[t] - pump_energy[t]

        # 库容递推
        storage[t + 1] = available - r

    return {
        "release": release,
        "storage": storage,
        "agri_supply": agri_supply,
        "eco_supply": eco_supply,
        "urban_supply": urban_supply,
        "hydro": hydro,
        "net_energy": net_energy,
        "pump_energy": pump_energy,
        "treat_energy": treat_energy,
        "reused_water": reused_water,
    }


def calc_kpi(sim):
    """计算KPI指标。"""
    agri_rel = sim["agri_supply"] / AGRI_DEMAND
    eco_rel = sim["eco_supply"] / ECO_DEMAND
    urban_rel = sim["urban_supply"] / URBAN_DEMAND
    energy_rel = sim["net_energy"] / ENERGY_DEMAND

    food_security = np.clip(np.mean(agri_rel), 0.0, 1.3)
    eco_security = np.clip(np.mean(eco_rel), 0.0, 1.2)
    urban_security = np.clip(np.mean(urban_rel), 0.0, 1.2)
    energy_security = np.clip(np.mean(energy_rel), 0.0, 1.2)

    grain_output = GRAIN_TARGET * (food_security ** FOOD_ELASTICITY)
    grain_guarantee = np.clip(grain_output / GRAIN_TARGET, 0.0, 1.3)

    # 协调度：体现“木桶短板效应”
    coordination = (
        max(grain_guarantee, 1e-6)
        * max(energy_security, 1e-6)
        * max(eco_security, 1e-6)
        * max(urban_security, 1e-6)
    ) ** 0.25

    total_cost = WATER_COST * np.sum(sim["release"]) + ENERGY_COST * np.sum(sim["pump_energy"] + sim["treat_energy"])
    emission = GRID_EMISSION * np.sum(EXTERNAL_ENERGY + sim["pump_energy"] + sim["treat_energy"]) - HYDRO_OFFSET * np.sum(sim["hydro"])

    cost_n = total_cost / 200.0
    emis_n = emission / 150.0

    sustainability = (
        W_FOOD * grain_guarantee
        + W_ENERGY * energy_security
        + W_ECO * eco_security
        + W_URBAN * urban_security
        + W_COORD * coordination
        - W_COST * cost_n
        - W_EMISSION * emis_n
    )

    return {
        "grain_output": grain_output,
        "grain_guarantee": grain_guarantee,
        "energy_security": energy_security,
        "eco_security": eco_security,
        "urban_security": urban_security,
        "coordination": coordination,
        "sustainability": sustainability,
        "total_cost": total_cost,
        "emission": emission,
    }


def objective(x):
    """目标函数：最大化综合可持续指数（最小化其负值）。"""
    sim = simulate_policy(x)
    kpi = calc_kpi(sim)

    # 月尺度短缺惩罚，避免仅看年平均掩盖局部风险
    agri_short = np.mean(np.maximum(0.0, 1.0 - sim["agri_supply"] / AGRI_DEMAND))
    eco_short = np.mean(np.maximum(0.0, 1.0 - sim["eco_supply"] / ECO_DEMAND))
    urban_short = np.mean(np.maximum(0.0, 1.0 - sim["urban_supply"] / URBAN_DEMAND))
    energy_short = np.mean(np.maximum(0.0, 1.0 - sim["net_energy"] / ENERGY_DEMAND))
    shortage_penalty = 0.35 * agri_short + 0.25 * eco_short + 0.20 * urban_short + 0.20 * energy_short

    return -(kpi["sustainability"] - shortage_penalty)


def storage_constraints(x):
    """库容约束：每月末库容在[S_MIN, S_MAX]。"""
    s = simulate_policy(x)["storage"][1:]
    lower = s - S_MIN
    upper = S_MAX - s
    return np.concatenate([lower, upper])  # 全部应 >= 0


def share_constraint(x):
    """分配比例约束：农业+生态不超过0.92，给城镇留足空间。"""
    alpha = x[N_MONTHS]
    beta = x[N_MONTHS + 1]
    return 0.92 - alpha - beta


def print_kpi_table(kpi_base, kpi_opt):
    """打印KPI结果表格。"""
    rows = [
        ("粮食产量(万吨)", kpi_base["grain_output"], kpi_opt["grain_output"]),
        ("粮食保障指数(-)", kpi_base["grain_guarantee"], kpi_opt["grain_guarantee"]),
        ("能源保障指数(-)", kpi_base["energy_security"], kpi_opt["energy_security"]),
        ("生态保障指数(-)", kpi_base["eco_security"], kpi_opt["eco_security"]),
        ("城镇供水保障(-)", kpi_base["urban_security"], kpi_opt["urban_security"]),
        ("耦合协调度(-)", kpi_base["coordination"], kpi_opt["coordination"]),
        ("综合可持续指数(-)", kpi_base["sustainability"], kpi_opt["sustainability"]),
        ("总成本(归一化)", kpi_base["total_cost"], kpi_opt["total_cost"]),
        ("碳排放(tCO2e)", kpi_base["emission"], kpi_opt["emission"]),
    ]

    print("\nKPI结果表格：基准情景 vs 优化情景")
    print("-" * 92)
    print(f"{'指标':<24}{'基准值':>14}{'优化值':>14}{'变化(%)':>14}")
    print("-" * 92)
    for name, b, o in rows:
        change = (o - b) / b * 100 if abs(b) > 1e-9 else np.nan
        print(f"{name:<24}{b:>14.3f}{o:>14.3f}{change:>14.2f}")
    print("-" * 92)


def plot_results(sim_base, sim_opt, kpi_base, kpi_opt):
    """生成matplotlib图。"""
    months = np.arange(1, N_MONTHS + 1)

    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 1, figsize=(12, 9))

    # 图1：月过程（来水、下泄、库容）
    ax1 = axes[0]
    ax1.plot(months, INFLOW, "o-", label="来水", color="#1f77b4")
    ax1.plot(months, sim_base["release"], "--", label="基准下泄", color="#7f7f7f")
    ax1.plot(months, sim_opt["release"], "s-", label="优化下泄", color="#ff7f0e")
    ax1.set_ylabel("水量(百万m3/月)")
    ax1.set_title("流域调度过程：来水-下泄-库容")
    ax1.grid(alpha=0.25)

    ax1b = ax1.twinx()
    ax1b.plot(months, sim_opt["storage"][1:], "^-", color="#2ca02c", label="优化月末库容")
    ax1b.set_ylabel("库容(百万m3)")

    lines = ax1.get_lines() + ax1b.get_lines()
    labels = [ln.get_label() for ln in lines]
    ax1.legend(lines, labels, loc="upper left", ncol=2)

    # 图2：KPI对比
    ax2 = axes[1]
    labels_kpi = ["粮食", "能源", "生态", "城镇", "协调", "可持续"]
    base_vals = [
        kpi_base["grain_guarantee"],
        kpi_base["energy_security"],
        kpi_base["eco_security"],
        kpi_base["urban_security"],
        kpi_base["coordination"],
        kpi_base["sustainability"],
    ]
    opt_vals = [
        kpi_opt["grain_guarantee"],
        kpi_opt["energy_security"],
        kpi_opt["eco_security"],
        kpi_opt["urban_security"],
        kpi_opt["coordination"],
        kpi_opt["sustainability"],
    ]
    idx = np.arange(len(labels_kpi))
    width = 0.35
    ax2.bar(idx - width / 2, base_vals, width=width, label="基准", color="#b0b0b0")
    ax2.bar(idx + width / 2, opt_vals, width=width, label="优化", color="#4c78a8")
    ax2.axhline(1.0, ls="--", lw=1, color="gray")
    ax2.set_xticks(idx)
    ax2.set_xticklabels(labels_kpi)
    ax2.set_ylabel("指数值(-)")
    ax2.set_title("WEF关键KPI对比")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.25)

    plt.tight_layout()
    plt.savefig('ch06_simulation_result.png', dpi=300)
    # plt.show()  # 禁用弹窗


def main():
    # 基准策略（可按教学需要修改）
    release_base = np.array([9, 9, 10, 11, 13, 16, 18, 17, 15, 13, 11, 10], dtype=float)
    x_base = np.concatenate([release_base, np.array([0.56, 0.24, 0.16])])

    # 待优化变量边界
    bounds = [(4.0, R_MAX)] * N_MONTHS + [(0.40, 0.75), (0.15, 0.40), (0.05, 0.35)]

    constraints = [
        {"type": "ineq", "fun": storage_constraints},
        {"type": "ineq", "fun": share_constraint},
    ]

    res = minimize(
        objective,
        x0=x_base.copy(),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-8},
    )

    if not res.success:
        raise RuntimeError(f"优化失败: {res.message}")

    x_opt = res.x
    sim_base = simulate_policy(x_base)
    sim_opt = simulate_policy(x_opt)
    kpi_base = calc_kpi(sim_base)
    kpi_opt = calc_kpi(sim_opt)

    # 输出关键决策参数
    print("最优关键参数：")
    print(f"农业分水比例 alpha_agri = {x_opt[N_MONTHS]:.3f}")
    print(f"生态分水比例 beta_eco   = {x_opt[N_MONTHS + 1]:.3f}")
    print(f"再生水用能比例 gamma    = {x_opt[N_MONTHS + 2]:.3f}")
    print(f"年总下泄量               = {np.sum(x_opt[:N_MONTHS]):.3f} 百万m3")

    # 输出KPI表
    print_kpi_table(kpi_base, kpi_opt)

    # 绘图
    plot_results(sim_base, sim_opt, kpi_base, kpi_opt)


if __name__ == "__main__":
    main()
