# -*- coding: utf-8 -*-
"""
教材：《内河航道与通航水力学》
第6章 案例：长江航道/运河
功能：基于6.1 基本概念与理论框架，仿真长江航道与运河在全年来流变化下的
      水深、流速、弗劳德数和通航KPI，并输出表格与图形。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# --------------------- 绘图中文显示 ---------------------
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# --------------------- 全局关键参数 ---------------------
G = 9.81                 # 重力加速度(m/s^2)
DAYS = 365               # 仿真天数
SEED = 42                # 随机种子（保证复现）
NOISE_STD_RATIO = 0.10   # 日流量随机扰动比例
Q_FLOOR_RATIO = 0.35     # 最低流量比例（避免非物理负值）

np.random.seed(SEED)

# --------------------- 航道参数（可直接改） ---------------------
SECTIONS = {
    "长江航道": {
        "b": 120.0,         # 底宽(m)
        "m": 3.0,           # 边坡系数(1:m)
        "n": 0.028,         # 曼宁糙率
        "S0": 8.0e-5,       # 底坡
        "depth_req": 4.5,   # 通航需求最小水深(m)
        "depth_reg": 0.0,   # 工程调节等效增深(m)
        "Q_mean": 32000.0,  # 年平均流量(m^3/s)
        "Q_amp": 0.45,      # 季节振幅
        "phase": 170,       # 季节相位(天)
        "v_opt": 1.8,       # 适宜流速(m/s)
        "v_sigma": 0.9,     # 流速偏离惩罚尺度
        "v_limit": 3.2,     # 警戒流速(m/s)
        "cap_design": 520,  # 设计通过能力(艘/日)
        "lock_cap": np.inf, # 闸室约束上限(艘/日)
        "ship_ton": 2200.0  # 单船平均载重(t)
    },
    "运河": {
        "b": 55.0,
        "m": 2.0,
        "n": 0.020,
        "S0": 2.2e-5,
        "depth_req": 3.2,
        "depth_reg": 0.8,   # 运河水位控制等效增深
        "Q_mean": 950.0,
        "Q_amp": 0.22,
        "phase": 155,
        "v_opt": 1.2,
        "v_sigma": 0.5,
        "v_limit": 2.2,
        "cap_design": 260,
        "lock_cap": 210.0,  # 运河闸室能力瓶颈
        "ship_ton": 850.0
    }
}


# --------------------- 水力学基础函数 ---------------------
def area_trapezoid(y, b, m):
    """梯形断面过水面积A"""
    return (b + m * y) * y


def wetted_perimeter(y, b, m):
    """梯形断面湿周P"""
    return b + 2.0 * y * np.sqrt(1.0 + m**2)


def top_width(y, b, m):
    """梯形断面水面宽T"""
    return b + 2.0 * m * y


def manning_discharge(y, b, m, n, S0):
    """曼宁公式：给定水深计算流量"""
    A = area_trapezoid(y, b, m)
    P = wetted_perimeter(y, b, m)
    R = A / P
    return (1.0 / n) * A * (R ** (2.0 / 3.0)) * np.sqrt(S0)


def solve_normal_depth(Q, p):
    """由流量Q反算正常水深y（SciPy求根）"""
    if Q <= 0:
        return 0.05

    def f(y):
        return manning_discharge(y, p["b"], p["m"], p["n"], p["S0"]) - Q

    y_low, y_high = 0.05, 40.0
    while f(y_high) < 0 and y_high < 200:
        y_high *= 1.5

    try:
        return brentq(f, y_low, y_high)
    except ValueError:
        # 极端工况兜底：返回上界，避免程序中断
        return y_high


# --------------------- 来流与仿真 ---------------------
def generate_discharge_series(p, days=DAYS):
    """全年日流量序列：季节项 + 随机扰动"""
    t = np.arange(days)
    seasonal = 1.0 + p["Q_amp"] * np.sin(2.0 * np.pi * (t - p["phase"]) / days)
    noise = np.random.normal(0.0, NOISE_STD_RATIO, size=days)
    q = p["Q_mean"] * (seasonal + noise)
    q = np.clip(q, p["Q_mean"] * Q_FLOOR_RATIO, None)
    return t + 1, q


def simulate_section(name, p):
    """单条航道年度仿真"""
    day, Q = generate_discharge_series(p)

    depth = np.zeros_like(Q)
    velocity = np.zeros_like(Q)
    froude = np.zeros_like(Q)
    capacity = np.zeros_like(Q)

    for i, qi in enumerate(Q):
        # 1) 反算天然水深
        y = solve_normal_depth(qi, p)

        # 2) 叠加工程调节等效增深
        y_eff = y + p["depth_reg"]

        # 3) 计算流速/弗劳德数
        A = area_trapezoid(y_eff, p["b"], p["m"])
        T = top_width(y_eff, p["b"], p["m"])
        Dh = A / T
        v = qi / A
        fr = v / np.sqrt(G * Dh)

        # 4) 计算水动力限制下的日通过能力
        depth_factor = np.clip(y_eff / p["depth_req"], 0.0, 1.35)
        velocity_factor = np.exp(-((v - p["v_opt"]) / p["v_sigma"]) ** 2)
        hydro_cap = p["cap_design"] * depth_factor * velocity_factor

        # 5) 叠加闸室瓶颈
        daily_cap = min(hydro_cap, p["lock_cap"])

        depth[i] = y_eff
        velocity[i] = v
        froude[i] = fr
        capacity[i] = daily_cap

    kpi = {
        "航道": name,
        "平均流量": float(np.mean(Q)),
        "平均水深": float(np.mean(depth)),
        "最小水深": float(np.min(depth)),
        "通航保证率": float(np.mean(depth >= p["depth_req"]) * 100.0),
        "平均流速": float(np.mean(velocity)),
        "亚临界比例": float(np.mean(froude < 1.0) * 100.0),
        "高流速天数": int(np.sum(velocity > p["v_limit"])),
        "平均通过能力": float(np.mean(capacity)),
        "年货运量(百万吨)": float(np.sum(capacity) * p["ship_ton"] / 1e6),
        "depth_req": p["depth_req"]
    }

    return {
        "day": day, "Q": Q, "depth": depth, "velocity": velocity,
        "froude": froude, "capacity": capacity, "kpi": kpi
    }


# --------------------- KPI表格与绘图 ---------------------
def print_kpi_table(results):
    headers = [
        "航道", "平均流量(m3/s)", "平均水深(m)", "最小水深(m)",
        "通航保证率(%)", "平均流速(m/s)", "Fr<1比例(%)",
        "高流速天数", "平均能力(艘/日)", "年货运量(百万吨)"
    ]
    print("\n=== KPI结果表 ===")
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")

    for r in results:
        k = r["kpi"]
        row = [
            k["航道"], f"{k['平均流量']:.1f}", f"{k['平均水深']:.2f}", f"{k['最小水深']:.2f}",
            f"{k['通航保证率']:.1f}", f"{k['平均流速']:.2f}", f"{k['亚临界比例']:.1f}",
            f"{k['高流速天数']}", f"{k['平均通过能力']:.1f}", f"{k['年货运量(百万吨)']:.2f}"
        ]
        print("| " + " | ".join(row) + " |")


def plot

---

## 仿真代码解读

> 本节由Codex引擎生成，提供本章核心算法的Python实现与解读。

