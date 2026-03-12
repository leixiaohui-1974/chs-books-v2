# -*- coding: utf-8 -*-
# 《水-能源-粮食纽带关系》第5章：多系统耦合优化建模
# 功能：构建WEF（水-能源-粮食）耦合优化仿真，输出KPI结果表并生成可视化图形

import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（可直接调参）
# =========================
PARAMS = {
    # 资源与需求
    "W_NATURAL": 120.0,      # 天然可用水量（百万m^3）
    "E_EXTERNAL": 230.0,     # 外部可供能源（GWh）
    "F_DEMAND": 95.0,        # 粮食需求（万吨）
    "E_DEMAND": 120.0,       # 社会能源服务需求（GWh）
    "W_ENV_MIN": 25.0,       # 生态最小需水（百万m^3）

    # 耦合生产系数
    "ALPHA_F": 1.80,         # 粮食生产系数
    "ALPHA_E": 0.90,         # 由水支撑的能源产出系数（如水电等）
    "ALPHA_R": 0.65,         # 能源投入带来的再生水系数

    # 非线性弹性指数（体现规模报酬递减）
    "FOOD_EXP_W": 0.58,
    "FOOD_EXP_E": 0.42,
    "ENERGY_EXP_W": 0.75,
    "REUSE_EXP_E": 0.85,

    # 成本与排放参数
    "COST_W": 0.22,          # 水资源调配成本（归一化）
    "COST_E": 0.38,          # 能源使用成本（归一化）
    "EF_EXT": 0.42,          # 外部供能排放系数
    "EF_OP": 0.18,           # 系统运行排放系数
    "EF_HYDRO_OFFSET": 0.12, # 清洁能源替代减排系数

    # 多目标加权系数（理论框架：加权求和法）
    "W_FOOD": 0.35,          # 粮食保障权重
    "W_ENERGY": 0.30,        # 能源保障权重
    "W_WATER": 0.20,         # 生态水保障权重
    "W_COST": 0.10,          # 成本惩罚权重
    "W_EMISSION": 0.05,      # 排放惩罚权重
}

# 决策变量顺序：x = [W_food, W_energy, E_agri, E_treat]
BOUNDS = [
    (10.0, 100.0),   # W_food：农业用水（百万m^3）
    (5.0, 80.0),     # W_energy：能源系统用水（百万m^3）
    (5.0, 140.0),    # E_agri：农业用能（GWh）
    (0.0, 120.0),    # E_treat：水处理/回用用能（GWh）
]

X0 = np.array([55.0, 28.0, 68.0, 25.0], dtype=float)  # 初值
SCENARIO_FACTORS = np.array([0.80, 0.90, 1.00, 1.10, 1.20])  # 外部供能情景


# =========================
# 2) 系统评价函数
# =========================
def evaluate_system(x, p):
    """根据决策变量计算耦合系统状态与KPI。"""
    W_food, W_energy, E_agri, E_treat = x

    # 防止零值在分数指数下数值不稳定
    W_food = max(W_food, 1e-9)
    W_energy = max(W_energy, 1e-9)
    E_agri = max(E_agri, 1e-9)
    E_treat = max(E_treat, 1e-9)

    # 粮食产出：受农业用水与农业用能共同影响
    food = p["ALPHA_F"] * (W_food ** p["FOOD_EXP_W"]) * (E_agri ** p["FOOD_EXP_E"])

    # 能源子系统产出：用水促进能源产出（可类比水电等）
    hydro_energy = p["ALPHA_E"] * (W_energy ** p["ENERGY_EXP_W"])

    # 再生水：水处理用能转化为回用水
    reused_water = p["ALPHA_R"] * (E_treat ** p["REUSE_EXP_E"])

    # 系统平衡量
    water_available = p["W_NATURAL"] + reused_water
    water_env = water_available - W_food - W_energy
    energy_service = p["E_EXTERNAL"] + hydro_energy - E_agri - E_treat

    # 成本与排放
    cost = p["COST_W"] * (W_food + W_energy) + p["COST_E"] * (E_agri + E_treat)
    emission = (
        p["EF_EXT"] * p["E_EXTERNAL"]
        + p["EF_OP"] * (E_agri + E_treat)
        - p["EF_HYDRO_OFFSET"] * hydro_energy
    )

    # 归一化保障指标（上限截断防止单指标主导）
    s_food = np.clip(food / p["F_DEMAND"], 0.0, 1.5)
    s_energy = np.clip(energy_service / p["E_DEMAND"], 0.0, 1.5)
    s_water = np.clip(water_env / p["W_ENV_MIN"], 0.0, 2.0)

    # 综合可持续指数（多目标加权）
    sustainability = (
        p["W_FOOD"] * s_food
        + p["W_ENERGY"] * s_energy
        + p["W_WATER"] * s_water
        - p["W_COST"] * (cost / 100.0)
        - p["W_EMISSION"] * (emission / 100.0)
    )

    # 耦合协调度：几何平均体现“短板效应”
    coordination = (max(s_food, 1e-6) * max(s_energy, 1e-6) * max(s_water, 1e-6)) ** (1 / 3)

    return {
        "food": food,
        "hydro_energy": hydro_energy,
        "reused_water": reused_water,
        "water_env": water_env,
        "energy_service": energy_service,
        "cost": cost,
        "emission": emission,
        "s_food": s_food,
        "s_energy": s_energy,
        "s_water": s_water,
        "sustainability": sustainability,
        "coordination": coordination,
    }


def objective(x, p):
    """SLSQP默认求最小值，这里对综合可持续指数取负号实现“最大化”目标。"""
    return -evaluate_system(x, p)["sustainability"]


def build_constraints(p):
    """构建约束：生态底线与能源服务底线。"""
    return [
        # 生态需水约束：水结余必须不低于生态阈值
        {
            "type": "ineq",
            "fun": lambda x, p=p: p["W_NATURAL"] + p["ALPHA_R"] * (max(x[3], 0.0) ** p["REUSE_EXP_E"])
                                  - x[0] - x[1] - p["W_ENV_MIN"]
        },
        # 能源保障约束：净能源服务不低于需求
        {
            "type": "ineq",
            "fun": lambda x, p=p: p["E_EXTERNAL"] + p["ALPHA_E"] * (max(x[1], 0.0) ** p["ENERGY_EXP_W"])
                                  - x[2] - x[3] - p["E_DEMAND"]
        },
    ]


def solve_wef(p, x0):
    """求解WEF耦合优化问题。"""
    result = minimize(
        objective,
        x0=x0,
        args=(p,),
        method="SLSQP",
        bounds=BOUNDS,
        constraints=build_constraints(p),
        options={"maxiter": 400, "ftol": 1e-9}
    )
    return result


def print_table(title, rows):
    """打印简洁KPI表格。"""
    print("\n" + title)
    print("-" * 66)
    print(f"{'指标':<24}{'数值':>14}{'单位':>12}")
    print("-" * 66)
    for name, value, unit in rows:
        print(f"{name:<24}{value:>14.3f}{unit:>12}")
    print("-" * 66)


if __name__ == "__main__":
    # 中文显示设置（系统缺少中文字体时会自动回退）
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # =========================
    # 3) 基准情景优化
    # =========================
    res = solve_wef(PARAMS, X0)
    if not res.success:
        raise RuntimeError(f"优化失败：{res.message}")

    x_opt = res.x
    state = evaluate_system(x_opt, PARAMS)

    # 打印最优决策变量
    decision_rows = [
        ("农业用水 W_food", x_opt[0], "百万m^3"),
        ("能源系统用水 W_energy", x_opt[1], "百万m^3"),
        ("农业用能 E_agri", x_opt[2], "GWh"),
        ("水处理用能 E_treat", x_opt[3], "GWh"),
    ]
    print_table("最优决策变量", decision_rows)

    # 打印KPI结果表
    kpi_rows = [
        ("粮食产出", state["food"], "万吨"),
        ("能源净服务", state["energy_service"], "GWh"),
        ("生态结余水量", state["water_env"], "百万m^3"),
        ("再生水量", state["reused_water"], "百万m^3"),
        ("耦合协调度", state["coordination"], "-"),
        ("综合可持续指数", state["sustainability"], "-"),
        ("总成本", state["cost"], "归一化"),
        ("碳排放", state["emission"], "归一化"),
    ]
    print_table("KPI结果表", kpi_rows)

    # =========================
    # 4) 情景分析（外部供能变化）
    # =========================
    ext_energy_list, si_list, food_list = [], [], []
    warm_start = x_opt.copy()

    for factor in SCENARIO_FACTORS:
        p_sc = PARAMS.copy()
        p_sc["E_EXTERNAL"] = PARAMS["E_EXTERNAL"] * factor
        res_sc = solve_wef(p_sc, warm_start)

        if res_sc.success:
            st_sc = evaluate_system(res_sc.x, p_sc)
            ext_energy_list.append(p_sc["E_EXTERNAL"])
            si_list.append(st_sc["sustainability"])
            food_list.append(st_sc["food"])
            warm_start = res_sc.x
        else:
            ext_energy_list.append(p_sc["E_EXTERNAL"])
            si_list.append(np.nan)
            food_list.append(np.nan)

    ext_energy_arr = np.array(ext_energy_list)
    si_arr = np.array(si_list)
    food_arr = np.array(food_list)

    # =========================
    # 5) 可视化
    # =========================
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 图1：基准情景下三系统保障与协调度
    labels = ["粮食保障", "能源保障", "生态水保障", "耦合协调度"]
    values = [state["s_food"], state["s_energy"], state["s_water"], state["coordination"]]
    colors = ["#2a9d8f", "#e9c46a", "#457b9d", "#e76f51"]

    axes[0].bar(labels, values, color=colors)
    axes[0].axhline(1.0, linestyle="--", color="gray", linewidth=1)
    axes[0].set_ylim(0, max(2.1, max(values) * 1.2))
    axes[0].set_title("基准情景：WEF保障指标")
    axes[0].set_ylabel("归一化指标值")

    # 图2：外部供能变化对可持续性与粮食产出的影响
    ax_left = axes[1]
    ax_right = ax_left.twinx()

    line1 = ax_left.plot(ext_energy_arr, si_arr, "o-", color="#2a9d8f", label="综合可持续指数")
    line2 = ax_right.plot(ext_energy_arr, food_arr, "s--", color="#e76f51", label="粮食产出")

    ax_left.set_title("情景分析：外部供能变化")
    ax_left.set_xlabel("外部供能规模 (GWh)")
    ax_left.set_ylabel("综合可持续指数", color="#2a9d8f")
    ax_right.set_ylabel("粮食产出 (万吨)", color="#e76f51")

    # 合并图例
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax_left.legend(lines, labels, loc="best")

    plt.tight_layout()
    plt.savefig('ch05_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch05_simulation_result.png")
# plt.show()  # 禁用弹窗
