# -*- coding: utf-8 -*-
"""
教材：《船闸调度优化与自动化》
章节：第1章 船闸水力学（充泄水）- 1.1 基本概念与理论框架
功能：构建船闸充水/泄水的一维简化水力学仿真，优化阀门开启策略，输出KPI并绘图。
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数定义（可直接调）
# =========================
G = 9.81                    # 重力加速度(m/s^2)
RHO = 1000.0                # 水密度(kg/m^3)
A_LOCK = 34.0 * 280.0       # 闸室水面面积(m^2)，示例：34m x 280m
A_CULVERT_MAX = 7.5         # 输水廊道等效最大过水面积(m^2)
CD = 0.78                   # 流量系数(综合局部损失)

H_UP = 12.0                 # 上游水位(m)
H_DOWN = 5.0                # 下游水位(m)
H0_FILL = H_DOWN            # 充水初始闸室水位(m)
H0_DRAIN = H_UP             # 泄水初始闸室水位(m)
H_TOL = 0.01                # 终止判据水位容差(m)

T_MAX = 5000.0              # 单次仿真最大时长(s)
T_OPEN_BASELINE = 120.0     # 基准方案：阀门全开时间(s)
T_OPEN_MIN = 30.0           # 优化搜索下界(s)
T_OPEN_MAX = 600.0          # 优化搜索上界(s)

MAX_RATE_FILL = 0.030       # 充水允许最大水位变化速率(m/s)
MAX_RATE_DRAIN = 0.028      # 泄水允许最大水位变化速率(m/s)

PARAMS = {
    "G": G, "RHO": RHO, "A_LOCK": A_LOCK, "A_CULVERT_MAX": A_CULVERT_MAX, "CD": CD,
    "H_UP": H_UP, "H_DOWN": H_DOWN, "H0_FILL": H0_FILL, "H0_DRAIN": H0_DRAIN,
    "H_TOL": H_TOL, "T_MAX": T_MAX,
    "T_OPEN_BASELINE": T_OPEN_BASELINE, "T_OPEN_MIN": T_OPEN_MIN, "T_OPEN_MAX": T_OPEN_MAX,
    "MAX_RATE_FILL": MAX_RATE_FILL, "MAX_RATE_DRAIN": MAX_RATE_DRAIN
}


def valve_opening(t, t_open):
    """阀门开启规律：smoothstep（0->1平滑过渡）"""
    x = np.clip(np.asarray(t, dtype=float) / max(t_open, 1e-6), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def simulate_operation(mode, t_open, p):
    """仿真单个工况：mode='fill'(充水) 或 'drain'(泄水)"""
    if mode not in ("fill", "drain"):
        raise ValueError("mode 必须为 'fill' 或 'drain'")

    h0 = p["H0_FILL"] if mode == "fill" else p["H0_DRAIN"]

    # 微分方程：dh/dt = Q/A_lock
    def rhs(t, y):
        h = y[0]
        open_ratio = float(valve_opening(t, t_open))
        if mode == "fill":
            dH = max(p["H_UP"] - h, 0.0)
            q = p["CD"] * p["A_CULVERT_MAX"] * open_ratio * np.sqrt(2.0 * p["G"] * dH)
        else:
            dH = max(h - p["H_DOWN"], 0.0)
            q = -p["CD"] * p["A_CULVERT_MAX"] * open_ratio * np.sqrt(2.0 * p["G"] * dH)
        return [q / p["A_LOCK"]]

    # 事件终止：达到目标水位附近即停止
    if mode == "fill":
        def reach_target(t, y):
            return y[0] - (p["H_UP"] - p["H_TOL"])
        reach_target.direction = 1
    else:
        def reach_target(t, y):
            return y[0] - (p["H_DOWN"] + p["H_TOL"])
        reach_target.direction = -1
    reach_target.terminal = True

    sol = solve_ivp(
        rhs, (0.0, p["T_MAX"]), [h0],
        events=reach_target, max_step=2.0, rtol=1e-6, atol=1e-8
    )

    t = sol.t
    h = sol.y[0]
    open_ratio = valve_opening(t, t_open)

    if mode == "fill":
        dH = np.maximum(p["H_UP"] - h, 0.0)
        q_sign = 1.0
    else:
        dH = np.maximum(h - p["H_DOWN"], 0.0)
        q_sign = -1.0

    q = q_sign * p["CD"] * p["A_CULVERT_MAX"] * open_ratio * np.sqrt(2.0 * p["G"] * dH)
    dhdt = q / p["A_LOCK"]

    # KPI计算
    finish_time = float(t[-1])
    peak_q = float(np.max(np.abs(q)))
    max_rate_mpm = float(np.max(np.abs(dhdt)) * 60.0)  # m/min
    water_volume = float(np.trapezoid(np.abs(q), t))   # m^3
    energy_loss_mj = float(np.trapezoid(np.abs(q) * dH * p["RHO"] * p["G"], t) / 1e6)

    kpi = {
        "完成时间(s)": finish_time,
        "峰值流量(m3/s)": peak_q,
        "最大水位变化速率(m/min)": max_rate_mpm,
        "过闸水量(m3)": water_volume,
        "水力耗散能(MJ)": energy_loss_mj
    }
    return t, h, q, open_ratio, dhdt, kpi


def objective_open_time(t_open, mode, p):
    """优化目标：最短完成时间 + 超速惩罚"""
    _, _, _, _, dhdt, kpi = simulate_operation(mode, t_open, p)
    limit = p["MAX_RATE_FILL"] if mode == "fill" else p["MAX_RATE_DRAIN"]
    exceed = max(0.0, float(np.max(np.abs(dhdt)) - limit))
    penalty = 1e8 * exceed * exceed
    return kpi["完成时间(s)"] + penalty


def optimize_open_time(mode, p):
    res = minimize_scalar(
        objective_open_time,
        bounds=(p["T_OPEN_MIN"], p["T_OPEN_MAX"]),
        method="bounded",
        args=(mode, p),
        options={"xatol": 1.0}
    )
    return float(res.x)


def print_kpi_table(rows):
    print("\n=== KPI结果表（船闸充泄水仿真）===")
    print("工况\t方案\t阀门全开时间(s)\t完成时间(s)\t峰值流量(m3/s)\t最大水位变化速率(m/min)\t过闸水量(m3)\t水力耗散能(MJ)")
    for r in rows:
        print(
            f"{r['工况']}\t{r['方案']}\t"
            f"{r['阀门全开时间(s)']:.1f}\t\t"
            f"{r['完成时间(s)']:.1f}\t\t"
            f"{r['峰值流量(m3/s)']:.2f}\t\t"
            f"{r['最大水位变化速率(m/min)']:.3f}\t\t\t"
            f"{r['过闸水量(m3)']:.1f}\t\t"
            f"{r['水力耗散能(MJ)']:.2f}"
        )


def plot_results(curves):
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex="col")
    mode_title = {"fill": "充水过程", "drain": "泄水过程"}

    for col, mode in enumerate(["fill", "drain"]):
        base = curves[(mode, "基准")]
        opt = curves[(mode, "优化")]

        # 水位曲线
        axes[0, col].plot(base["t"] / 60.0, base["h"], "--", lw=1.8, label="基准")
        axes[0, col].plot(opt["t"] / 60.0, opt["h"], "-", lw=2.2, label="优化")
        axes[0, col].set_title(mode_title[mode])
        axes[0, col].set_ylabel("闸室水位 h (m)")
        axes[0, col].grid(alpha=0.3)
        axes[0, col].legend()

        # 流量曲线
        axes[1, col].plot(base["t"] / 60.0, base["q"], "--", lw=1.8, label="基准")
        axes[1, col].plot(opt["t"] / 60.0, opt["q"], "-", lw=2.2, label="优化")
        axes[1, col].set_ylabel("流量 Q (m³/s)")
        axes[1, col].set_xlabel("时间 (min)")
        axes[1, col].grid(alpha=0.3)

    fig.suptitle("船闸充泄水水力学仿真：基准方案 vs 优化方案", fontsize=13)
    plt.tight_layout()
    plt.savefig('ch01_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch01_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    rows = []
    curves = {}

    for mode in ["fill", "drain"]:
        t_open_opt = optimize_open_time(mode, PARAMS)
        for plan_name, t_open in [("基准", PARAMS["T_OPEN_BASELINE"]), ("优化", t_open_opt)]:
            t, h, q, open_ratio, dhdt, kpi = simulate_operation(mode, t_open, PARAMS)

            row = {
                "工况": "充水" if mode == "fill" else "泄水",
                "方案": plan_name,
                "阀门全开时间(s)": t_open,
                "完成时间(s)": kpi["完成时间(s)"],
                "峰值流量(m3/s)": kpi["峰值流量(m3/s)"],
                "最大水位变化速率(m/min)": kpi["最大水位变化速率(m/min)"],
                "过闸水量(m3)": kpi["过闸水量(m3)"],
                "水力耗散能(MJ)": kpi["水力耗散能(MJ)"]
            }
            rows.append(row)

            curves[(mode, plan_name)] = {
                "t": t, "h": h, "q": q, "open_ratio": open_ratio, "dhdt": dhdt
            }

    print_kpi_table(rows)
    plot_results(curves)


if __name__ == "__main__":
    main()
