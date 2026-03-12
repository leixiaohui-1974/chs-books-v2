#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
书名：《水-能源-粮食纽带关系》
章节：第4章 能-粮耦合建模
功能：构建能-粮双向耦合动力学模型，进行多情景仿真，打印KPI结果表格并生成matplotlib图形。
依赖：numpy, scipy, matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# -----------------------------
# 关键参数（可直接在此修改）
# -----------------------------
SIM_YEARS = 20                  # 仿真年限
N_POINTS = 241                  # 输出点数量（约每月一个点）
TIME_SPAN = (0.0, float(SIM_YEARS))

# 初始状态
E0 = 420.0                      # 初始农业可用能源（PJ）
F0 = 500.0                      # 初始粮食产量（Mt）

# 基准情景参数
BASE_PARAMS = {
    "E0": E0,
    "F0": F0,
    "invest": 24.0,             # 能源系统年净投资项（PJ/年）
    "feedback": 0.08,           # 粮食副产物回馈能源系数（PJ/(Mt·年)）
    "depr": 0.07,               # 能源系统折损率（1/年）
    "e0": 1.20,                 # 初始单位粮食能耗（PJ/Mt）
    "tech": 0.010,              # 能耗技术进步率（1/年）
    "r": 0.070,                 # 粮食系统内生增长率（1/年）
    "K": 760.0,                 # 粮食产量上限（Mt）
    "eff": 0.50,                # 能源盈余转化为增产效率（Mt/PJ）
    "penalty": 0.75,            # 能源短缺导致减产惩罚（Mt/PJ）
    "climate": 0.012            # 气候扰动等综合损失率（1/年）
}

# 其他情景：在基准参数上调整
SCENARIOS = {
    "基准情景": {},
    "效率提升情景": {
        "tech": 0.030,          # 技术进步更快，单位粮食能耗下降更快
        "penalty": 0.60
    },
    "可再生强化情景": {
        "invest": 30.0,         # 更高能源投入
        "feedback": 0.14,       # 更高副产物能源回收效率
        "depr": 0.06
    }
}


def merge_params(base, override):
    """合并参数字典。"""
    p = dict(base)
    p.update(override)
    return p


def nexus_ode(t, y, p):
    """
    能-粮耦合模型：
    dE/dt = invest + feedback*F - depr*E
    dF/dt = r*F*(1-F/K) + eff*max(E-demand,0) - penalty*max(demand-E,0) - climate*F
    demand = e(t)*F, e(t)=e0*exp(-tech*t)
    """
    E, F = y
    E_eff = max(E, 0.0)
    F_eff = max(F, 0.0)

    # 单位粮食能耗随技术进步指数下降
    ei_t = p["e0"] * np.exp(-p["tech"] * t)

    # 粮食系统能源需求
    demand = ei_t * F_eff
    net_energy = E_eff - demand

    # 能源子系统动力学
    dE = p["invest"] + p["feedback"] * F_eff - p["depr"] * E_eff

    # 粮食子系统动力学（内生增长 + 能源盈余/短缺影响 - 气候损失）
    growth = p["r"] * F_eff * (1.0 - F_eff / p["K"])
    bonus = p["eff"] * max(net_energy, 0.0)
    loss = p["penalty"] * max(-net_energy, 0.0) + p["climate"] * F_eff
    dF = growth + bonus - loss

    return [dE, dF]


def simulate_scenario(name, params):
    """执行单情景仿真并返回时序与KPI。"""
    t_eval = np.linspace(TIME_SPAN[0], TIME_SPAN[1], N_POINTS)
    y0 = [params["E0"], params["F0"]]

    sol = solve_ivp(
        fun=lambda t, y: nexus_ode(t, y, params),
        t_span=TIME_SPAN,
        y0=y0,
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-8
    )
    if not sol.success:
        raise RuntimeError(f"{name} 仿真失败：{sol.message}")

    t = sol.t
    E = sol.y[0]
    F = sol.y[1]

    # 衍生量计算
    ei = params["e0"] * np.exp(-params["tech"] * t)
    demand = ei * np.maximum(F, 0.0)
    shortage = np.maximum(demand - E, 0.0)
    gap_rate = shortage / (demand + 1e-9)
    security = E / (demand + 1e-9)  # 能源保障率（>1表示供给充足）

    # 耦合协调度 D（常见构造）
    Ue = (E - E.min()) / (E.max() - E.min() + 1e-9)
    Uf = (F - F.min()) / (F.max() - F.min() + 1e-9)
    C = 2.0 * np.sqrt(Ue * Uf) / (Ue + Uf + 1e-9)
    T = 0.5 * (Ue + Uf)
    D = np.sqrt(C * T)

    kpi = {
        "scenario": name,
        "food_final": float(F[-1]),
        "food_mean": float(np.mean(F)),
        "security_final": float(security[-1]),
        "gap_mean": float(np.mean(gap_rate)),
        "shortage_cum": float(np.trapz(shortage, t)),
        "intensity_mean": float(np.mean(demand / (np.maximum(F, 1e-9)))),
        "coord_final": float(D[-1])
    }

    return {
        "name": name,
        "t": t,
        "E": E,
        "F": F,
        "demand": demand,
        "gap_rate": gap_rate,
        "security": security,
        "D": D,
        "kpi": kpi
    }


def print_kpi_table(results):
    """打印KPI表格（纯文本对齐）。"""
    headers = [
        "情景",
        "末期粮食产量(Mt)",
        "平均粮食产量(Mt)",
        "末期能源保障率",
        "平均能源缺口率",
        "累计能源缺口(PJ·年)",
        "平均单位粮食能耗(PJ/Mt)",
        "末期耦合协调度D"
    ]

    rows = []
    for r in results:
        k = r["kpi"]
        rows.append([
            k["scenario"],
            f"{k['food_final']:.4f}",
            f"{k['food_mean']:.4f}",
            f"{k['security_final']:.4f}",
            f"{k['gap_mean']:.4f}",
            f"{k['shortage_cum']:.4f}",
            f"{k['intensity_mean']:.4f}",
            f"{k['coord_final']:.4f}"
        ])

    widths = []
    for i, h in enumerate(headers):
        w = len(h)
        for row in rows:
            w = max(w, len(row[i]))
        widths.append(w + 2)

    line = "+" + "+".join("-" * w for w in widths) + "+"
    print("\nKPI结果表格")
    print(line)
    print("|" + "|".join(f"{h:^{w}}" for h, w in zip(headers, widths)) + "|")
    print(line)
    for row in rows:
        print("|" + "|".join(f"{c:^{w}}" for c, w in zip(row, widths)) + "|")
    print(line)


def plot_results(results):
    """绘制四联图：粮食演化、供需对比、耦合协调度、能源缺口率。"""
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))

    # 1) 粮食产量演化
    for r in results:
        ax[0, 0].plot(r["t"], r["F"], linewidth=2, label=r["name"])
    ax[0, 0].set_title("粮食产量演化")
    ax[0, 0].set_xlabel("时间（年）")
    ax[0, 0].set_ylabel("粮食产量（Mt）")
    ax[0, 0].grid(alpha=0.3)
    ax[0, 0].legend()

    # 2) 基准情景下能源供需对比
    base = results[0]
    ax[0, 1].plot(base["t"], base["E"], linewidth=2, label="能源供给 E(t)")
    ax[0, 1].plot(base["t"], base["demand"], "--", linewidth=2, label="粮食系统能源需求 e(t)F(t)")
    ax[0, 1].set_title("基准情景能源供需对比")
    ax[0, 1].set_xlabel("时间（年）")
    ax[0, 1].set_ylabel("能源（PJ）")
    ax[0, 1].grid(alpha=0.3)
    ax[0, 1].legend()

    # 3) 耦合协调度
    for r in results:
        ax[1, 0].plot(r["t"], r["D"], linewidth=2, label=r["name"])
    ax[1, 0].set_title("耦合协调度 D")
    ax[1, 0].set_xlabel("时间（年）")
    ax[1, 0].set_ylabel("D 值")
    ax[1, 0].set_ylim(0.0, 1.05)
    ax[1, 0].grid(alpha=0.3)
    ax[1, 0].legend()

    # 4) 能源缺口率
    for r in results:
        ax[1, 1].plot(r["t"], r["gap_rate"], linewidth=2, label=r["name"])
    ax[1, 1].set_title("能源缺口率")
    ax[1, 1].set_xlabel("时间（年）")
    ax[1, 1].set_ylabel("缺口率")
    ax[1, 1].set_ylim(0.0, 1.0)
    ax[1, 1].grid(alpha=0.3)
    ax[1, 1].legend()

    plt.tight_layout()
    plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    results = []
    for name, override in SCENARIOS.items():
        params = merge_params(BASE_PARAMS, override)
        results.append(simulate_scenario(name, params))

    print_kpi_table(results)
    plot_results(results)


if __name__ == "__main__":
    main()
