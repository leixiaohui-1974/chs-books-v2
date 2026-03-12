# -*- coding: utf-8 -*-
"""
教材：《河流泥沙动力学与河床演变》
章节：第6章 案例（黄河/长江泥沙）- 6.1 基本概念与理论框架
功能：基于“来沙-输沙能力-河床冲淤(Exner)”的简化耦合模型进行多年仿真，
      输出KPI结果表格，并绘制关键过程图。
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键常量与全局参数
# =========================
GRAVITY = 9.81          # 重力加速度 (m/s2)
RHO_W = 1000.0          # 水密度 (kg/m3)
RHO_S = 2650.0          # 泥沙颗粒密度 (kg/m3)
POROSITY = 0.40         # 河床孔隙率 (-)

SEC_PER_DAY = 86400.0
DAYS_PER_YEAR = 365.0
SIM_YEARS = 20
T_END = SIM_YEARS * DAYS_PER_YEAR

# 绘图中文字体设置（若本机无对应字体，会自动回退）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 2) 河流参数（黄河/长江）
# =========================
RIVER_PARAMS = {
    "黄河": {
        "Q_mean": 2200.0,       # 平均流量 (m3/s)
        "q_amp": 0.35,          # 流量季节振幅
        "q_phase": 170.0,       # 流量相位（天）
        "flood_amp": 0.45,      # 洪峰增强幅度
        "flood_center": 220.0,  # 洪峰中心日期（年内第几天）
        "flood_width": 28.0,    # 洪峰宽度（天）

        "qin0": 5.2e4,          # 基准来沙通量 (kg/s)
        "qin_amp": 0.55,        # 来沙季节振幅
        "qin_phase": 175.0,     # 来沙相位（天）
        "trap": 0.35,           # 上游拦沙系数（库坝等影响）

        "S": 1.5e-3,            # 河道坡降
        "B": 450.0,             # 河宽 (m)
        "L": 110e3,             # 控制河段长度 (m)
        "h_ref": 5.5,           # 参考水深 (m)

        "k_cap": 2.2e7,         # 输沙能力系数
        "m": 1.60,              # 流量指数
        "n": 1.20,              # 坡降指数
        "wash_coeff": 0.78,     # 可供输沙系数
        "wash_base": 1500.0,    # 基底冲刷通量 (kg/s)

        "k_entr": 7.5e4,        # 再悬浮系数 (kg/(day·Pa))
        "tau_c": 12.0,          # 起动临界剪切应力 (Pa)
        "k_dep": 0.055,         # 淤积系数 (1/day)

        "M0": 7.0e9,            # 初始悬沙库存 (kg)
        "eta0": 0.0,            # 初始河床高程变化 (m)
    },
    "长江": {
        "Q_mean": 28000.0,
        "q_amp": 0.22,
        "q_phase": 175.0,
        "flood_amp": 0.30,
        "flood_center": 215.0,
        "flood_width": 32.0,

        "qin0": 2.8e4,
        "qin_amp": 0.30,
        "qin_phase": 180.0,
        "trap": 0.62,

        "S": 2.2e-4,
        "B": 1300.0,
        "L": 150e3,
        "h_ref": 11.0,

        "k_cap": 2.6e7,
        "m": 1.55,
        "n": 1.18,
        "wash_coeff": 0.90,
        "wash_base": 3000.0,

        "k_entr": 5.8e4,
        "tau_c": 9.0,
        "k_dep": 0.040,

        "M0": 4.0e9,
        "eta0": 0.0,
    },
}


def process_terms(t, y, p):
    """计算某时刻的水沙过程量。"""
    M_raw, eta = y
    M = max(M_raw, 1.0e5)  # 避免出现非物理负库存

    # 年内日期（用于季节循环）
    day = t % DAYS_PER_YEAR

    # 流量：季节项 + 洪峰项
    season_q = 1.0 + p["q_amp"] * np.sin(2.0 * np.pi * (day - p["q_phase"]) / DAYS_PER_YEAR)
    flood = 1.0 + p["flood_amp"] * np.exp(-0.5 * ((day - p["flood_center"]) / p["flood_width"]) ** 2)
    Q = p["Q_mean"] * max(0.2, season_q) * flood

    # 水深随流量变化（简化幂律）
    h = p["h_ref"] * max(0.2, (Q / p["Q_mean"]) ** 0.40)

    # 控制体积与平均含沙浓度
    volume = p["B"] * p["L"] * h
    C = M / max(volume, 1.0)  # kg/m3

    # 来沙通量（考虑上游拦沙）
    season_in = 1.0 + p["qin_amp"] * np.sin(2.0 * np.pi * (day - p["qin_phase"]) / DAYS_PER_YEAR)
    q_in = p["qin0"] * max(0.1, season_in) * flood * (1.0 - p["trap"])  # kg/s

    # 输沙能力（经验幂律）
    q_cap = p["k_cap"] * (Q / 1000.0) ** p["m"] * (p["S"] ** p["n"])  # kg/s

    # 可供输沙受浓度约束
    q_available = p["wash_coeff"] * C * Q
    q_out = min(q_cap, q_available + p["wash_base"])  # kg/s

    # 河床剪切与再悬浮/淤积
    tau = RHO_W * GRAVITY * h * p["S"]        # Pa
    entr = p["k_entr"] * max(tau - p["tau_c"], 0.0)  # kg/day
    dep = p["k_dep"] * M                       # kg/day

    return {
        "Q": Q,
        "h": h,
        "C": C,
        "q_in": q_in,
        "q_out": q_out,
        "q_cap": q_cap,
        "entr": entr,
        "dep": dep,
    }


def rhs(t, y, p):
    """状态方程：
    dM/dt = (来沙-出沙)*86400 + 再悬浮 - 淤积
    deta/dt = (淤积-再悬浮)/(rho_s*(1-n)*B*L)
    """
    terms = process_terms(t, y, p)
    M_raw = y[0]

    dMdt = (terms["q_in"] - terms["q_out"]) * SEC_PER_DAY + terms["entr"] - terms["dep"]

    # 防止库存已极低时继续向负方向漂移
    if M_raw <= 1.0e5 and dMdt < 0.0:
        dMdt = 0.0

    bed_den = RHO_S * (1.0 - POROSITY) * p["B"] * p["L"]  # kg/m
    detadt = (terms["dep"] - terms["entr"]) / bed_den      # m/day

    return [dMdt, detadt]


def simulate_one_river(name, p, t_eval):
    """对单条河流执行数值积分，并回算过程量。"""
    y0 = [p["M0"], p["eta0"]]
    sol = solve_ivp(
        fun=lambda t, y: rhs(t, y, p),
        t_span=(t_eval[0], t_eval[-1]),
        y0=y0,
        t_eval=t_eval,
        method="RK45",
        max_step=2.0,
        rtol=1e-6,
        atol=1e-9,
    )
    if not sol.success:
        raise RuntimeError(f"{name} 数值积分失败: {sol.message}")

    n = len(sol.t)
    Q = np.zeros(n)
    C = np.zeros(n)
    q_in = np.zeros(n)
    q_out = np.zeros(n)
    q_cap = np.zeros(n)
    dep = np.zeros(n)
    entr = np.zeros(n)

    for i in range(n):
        terms = process_terms(sol.t[i], [sol.y[0, i], sol.y[1, i]], p)
        Q[i] = terms["Q"]
        C[i] = terms["C"]
        q_in[i] = terms["q_in"]
        q_out[i] = terms["q_out"]
        q_cap[i] = terms["q_cap"]
        dep[i] = terms["dep"]
        entr[i] = terms["entr"]

    return {
        "name": name,
        "t": sol.t,
        "M": sol.y[0],
        "eta": sol.y[1],
        "Q": Q,
        "C": C,
        "q_in": q_in,
        "q_out": q_out,
        "q_cap": q_cap,
        "dep": dep,
        "entr": entr,
    }


def compute_kpi(result):
    """计算KPI指标。"""
    t = result["t"]
    years = t[-1] / DAYS_PER_YEAR

    mean_qout = np.mean(result["q_out"])  # kg/s
    export_total = np.trapezoid(result["q_out"] * SEC_PER_DAY, t)  # kg
    export_annual_yt = export_total / years / 1e8                  # 亿吨/年

    mean_C = np.mean(result["C"])  # kg/m3
    delta_eta = result["eta"][-1] - result["eta"][0]  # m

    cap_util = 100.0 * np.mean(result["q_out"] / np.maximum(result["q_cap"], 1e-8))  # %
    net_dep_annual = np.trapezoid(result["dep"] - result["entr"], t) / years / 1e8    # 亿吨/年

    return {
        "mean_qout": mean_qout,
        "export_annual_yt": export_annual_yt,
        "mean_C": mean_C,
        "delta_eta": delta_eta,
        "cap_util": cap_util,
        "net_dep_annual": net_dep_annual,
    }


def print_kpi_table(kpis):
    """打印KPI结果表格。"""
    line = "-" * 118
    print("\nKPI结果表（黄河/长江泥沙仿真）")
    print(line)
    print(
        f"{'河流':<6}"
        f"{'平均输沙量(kg/s)':>18}"
        f"{'年均出境泥沙(亿吨/年)':>22}"
        f"{'平均含沙浓度(kg/m3)':>22}"
        f"{'20年河床变化(m)':>18}"
        f"{'输沙能力利用率(%)':>18}"
        f"{'净淤积(亿吨/年)':>16}"
    )
    print(line)

    for name, k in kpis.items():
        print(
            f"{name:<6}"
            f"{k['mean_qout']:>18.1f}"
            f"{k['export_annual_yt']:>22.3f}"
            f"{k['mean_C']:>22.3f}"
            f"{k['delta_eta']:>18.4f}"
            f"{k['cap_util']:>18.2f}"
            f"{k['net_dep_annual']:>16.3f}"
        )
    print(line)


def plot_results(results):
    """绘制关键过程图。"""
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    ax1, ax2, ax3, ax4 = axes.ravel()

    for name, r in results.items():
        t_year = r["t"] / DAYS_PER_YEAR

        # 图1：前3年出沙过程
        idx = r["t"] <= 3.0 * DAYS_PER_YEAR
        ax1.plot(t_year[idx], r["q_out"][idx], label=name, linewidth=1.8)

        # 图2：20年河床高程变化
        ax2.plot(t_year, r["eta"], label=name, linewidth=1.8)

        # 图3：20年平均含沙浓度
        ax3.plot(t_year, r["C"], label=name, linewidth=1.5)

        # 图4：累计出境泥沙量（亿吨）
        cumulative_export = np.cumsum(r["q_out"] * SEC_PER_DAY) / 1e8
        ax4.plot(t_year, cumulative_export, label=name, linewidth=1.8)

    ax1.set_title("前3年出沙通量过程")
    ax1.set_xlabel("时间（年）")
    ax1.set_ylabel("q_out (kg/s)")
    ax1.grid(alpha=0.3)
    ax1.legend()

    ax2.set_title("20年河床高程变化")
    ax2.set_xlabel("时间（年）")
    ax2.set_ylabel("eta (m)")
    ax2.grid(alpha=0.3)
    ax2.legend()

    ax3.set_title("悬沙平均浓度演化")
    ax3.set_xlabel("时间（年）")
    ax3.set_ylabel("C (kg/m3)")
    ax3.grid(alpha=0.3)
    ax3.legend()

    ax4.set_title("累计出境泥沙量")
    ax4.set_xlabel("时间（年）")
    ax4.set_ylabel("累计泥沙（亿吨）")
    ax4.grid(alpha=0.3)
    ax4.legend()

    fig.suptitle("第6章案例：黄河/长江泥沙-河床演变简化仿真", fontsize=14)
    plt.tight_layout()
    plt.savefig('ch06_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch06_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    t_eval = np.arange(0.0, T_END + 1.0, 1.0)  # 日尺度积分
    results = {}
    kpis = {}

    for name, p in RIVER_PARAMS.items():
        result = simulate_one_river(name, p, t_eval)
        results[name] = result
        kpis[name] = compute_kpi(result)

    print_kpi_table(kpis)
    plot_results(results)


if __name__ == "__main__":
    main()
