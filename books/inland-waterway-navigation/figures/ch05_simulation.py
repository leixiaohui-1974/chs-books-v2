# -*- coding: utf-8 -*-
"""
《内河航道与通航水力学》第5章
功能：防洪-发电-航运多目标协调调度仿真（SLSQP + 水动力近似）
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# =========================
# 1) 关键参数（集中定义）
# =========================
T = 72                       # 仿真总时长（h）
dt = 3600.0                  # 时间步长（s）
time = np.arange(T)

# 水库与调度边界
S_min = 4.0e8                # 最小库容（m3）
S_max = 8.5e8                # 最大库容（m3）
S0 = 6.2e8                   # 初始库容（m3）
S_target = 6.0e8             # 目标末库容（m3）
Q_release_min = 200.0        # 最小下泄（m3/s）
Q_release_max = 2600.0       # 最大小泄（m3/s）
dR_max = 350.0               # 相邻时段最大调节幅值（m3/s）
Q_safe = 2800.0              # 下游防洪安全流量（m3/s）

# 通航水力参数（经验关系）
B = 120.0                    # 代表河宽（m）
h0 = 1.8                     # 基准水深（m）
a_h = 0.015                  # 水深-流量系数
b_h = 0.62                   # 水深-流量指数
h_nav_min = 2.6              # 通航最小水深（m）
u_min, u_max = 0.30, 2.20    # 适航流速区间（m/s）

# 水电参数
rho = 1000.0                 # 水密度（kg/m3）
g = 9.81                     # 重力加速度（m/s2）
eta = 0.90                   # 综合效率
H0 = 26.0                    # 基准水头（m）
kH = 2.5e-8                  # 水头-库容线性化系数（m/m3）

# 图输出参数
SAVE_FIG = True
FIG_PATH = "chapter5_dispatch.png"


# =========================
# 2) 外部驱动过程
# =========================
# 入库流量：日周期 + 两次洪峰扰动
qin = (
    1200.0
    + 350.0 * np.sin(2.0 * np.pi * (time - 6.0) / 24.0)
    + 1700.0 * np.exp(-((time - 32.0) ** 2) / (2.0 * 6.0 ** 2))
    + 900.0 * np.exp(-((time - 52.0) ** 2) / (2.0 * 7.0 ** 2))
)
qin = np.clip(qin, 500.0, None)

# 区间来水
q_trib = 180.0 + 60.0 * np.sin(2.0 * np.pi * (time + 3.0) / 24.0)

# 电网负荷（MW）
P_demand = (
    150.0
    + 70.0 * np.sin(2.0 * np.pi * (time - 5.0) / 24.0)
    + 40.0 * np.sin(4.0 * np.pi * (time - 5.0) / 24.0)
)
P_demand = np.clip(P_demand, 80.0, 280.0)

# 由负荷反推目标流量（前馈目标）
coef_MW_per_Q = eta * rho * g * H0 / 1e6
Q_power_target = np.clip(P_demand / coef_MW_per_Q, Q_release_min, Q_release_max)


# =========================
# 3) 物理子模型
# =========================
def storage_from_release(R):
    """库容连续方程：S(k+1)=S(k)+(Qin-R)dt"""
    S = np.empty(T)
    S[0] = S0
    for k in range(T - 1):
        S[k + 1] = S[k] + (qin[k] - R[k]) * dt
    return S


def hydraulics(R):
    """下游流量、水深、流速近似关系"""
    Qd = R + q_trib
    h = h0 + a_h * np.power(np.maximum(Qd, 1.0), b_h)
    u = Qd / (B * np.maximum(h, 0.2))
    return Qd, h, u


def head_from_storage(S):
    """水头与库容线性化关系"""
    return H0 + kH * (S - S_target)


def power_from_release(R, S):
    """功率与电量计算"""
    H = head_from_storage(S[:-1])
    P = eta * rho * g * H * R[:-1] / 1e6  # MW
    E = np.sum(P) * (dt / 3600.0)          # MWh
    return P, E


# =========================
# 4) 多目标优化（控制器）
# =========================
def objective(R, w):
    """
    J = wf*Jflood + wp*Jpower + wn*Jnav + ws*Jsmooth + wt*Jterminal
    """
    S = storage_from_release(R)
    Qd, h, u = hydraulics(R)

    # 防洪：超安全流量惩罚
    J_flood = np.mean(np.maximum(Qd - Q_safe, 0.0) ** 2) / (Q_safe ** 2)

    # 发电：跟踪功率目标对应的流量
    J_power = np.mean((R - Q_power_target) ** 2) / (Q_release_max ** 2)

    # 通航：水深不足 + 流速越限
    J_depth = np.mean(np.maximum(h_nav_min - h, 0.0) ** 2) / (h_nav_min ** 2)
    J_vel = np.mean(np.maximum(u_min - u, 0.0) ** 2 + np.maximum(u - u_max, 0.0) ** 2) / (u_max ** 2)
    J_nav = 0.7 * J_depth + 0.3 * J_vel

    # 平滑控制：抑制“频繁大幅调节”
    J_smooth = np.mean(np.diff(R) ** 2) / (dR_max ** 2)

    # 终端状态稳定项
    J_terminal = ((S[-1] - S_target) / (S_max - S_min)) ** 2

    return (
        w["flood"] * J_flood
        + w["power"] * J_power
        + w["nav"] * J_nav
        + w["smooth"] * J_smooth
        + w["terminal"] * J_terminal
    )


def optimize_strategy(weights):
    """在硬约束下求解最优时序下泄过程"""
    x0 = np.clip(0.6 * qin + 0.4 * Q_power_target, Q_release_min, Q_release_max)
    bounds = [(Q_release_min, Q_release_max)] * T

    constraints = [
        {"type": "ineq", "fun": lambda R: storage_from_release(R) - S_min},
        {"type": "ineq", "fun": lambda R: S_max - storage_from_release(R)},
        {"type": "ineq", "fun": lambda R: dR_max - np.diff(R)},
        {"type": "ineq", "fun": lambda R: dR_max + np.diff(R)},
    ]

    result = minimize(
        objective,
        x0=x0,
        args=(weights,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-8, "disp": False},
    )

    if not result.success:
        print("[警告] 优化器未完全收敛：", result.message)

    R = result.x
    S = storage_from_release(R)
    Qd, h, u = hydraulics(R)
    P, E = power_from_release(R, S)

    return {"R": R, "S": S, "Qd": Qd, "h": h, "u": u, "P": P, "E": E, "obj": result.fun}


# =========================
# 5) KPI与表格
# =========================
def calc_kpi(res):
    R, S, Qd, h, u, P, E = res["R"], res["S"], res["Qd"], res["h"], res["u"], res["P"], res["E"]
    return {
        "目标函数值": res["obj"],
        "洪峰削减率(%)": 100.0 * (np.max(qin) - np.max(Qd)) / np.max(qin),
        "超安全流量时长(h)": float(np.sum(Qd > Q_safe)),
        "通航水深保证率(%)": 100.0 * np.mean(h >= h_nav_min),
        "适航流速保证率(%)": 100.0 * np.mean((u >= u_min) & (u <= u_max)),
        "发电量(MWh)": E,
        "功率跟踪RMSE(MW)": np.sqrt(np.mean((P - P_demand[:-1]) ** 2)),
        "下泄波动标准差(m3/s)": np.std(np.diff(R)),
        "末库容偏差(亿m3)": (S[-1] - S_target) / 1e8,
    }


def print_kpi_table(kpi_a, kpi_b):
    metrics = list(kpi_a.keys())
    col1, col2, col3 = 24, 18, 18
    line = "-" * (col1 + col2 + col3)
    print("\nKPI结果表（A:发电优先；B:多目标协调）")
    print(line)
    print(f"{'指标':<{col1}}{'策略A':>{col2}}{'策略B':>{col3}}")
    print(line)
    for m in metrics:
        print(f"{m:<{col1}}{kpi_a[m]:>{col2}.3f}{kpi_b[m]:>{col3}.3f}")
    print(line)


# =========================
# 6) 主程序
# =========================
if __name__ == "__main__":
    # 策略A：偏重发电跟踪
    weights_A = {"flood": 0.15, "power": 0.65, "nav": 0.10, "smooth": 0.05, "terminal": 0.05}
    # 策略B：三目标协调
    weights_B = {"flood": 0.35, "power": 0.25, "nav": 0.25, "smooth": 0.10, "terminal": 0.05}

    res_A = optimize_strategy(weights_A)
    res_B = optimize_strategy(weights_B)

    kpi_A = calc_kpi(res_A)
    kpi_B = calc_kpi(res_B)
    print_kpi_table(kpi_A, kpi_B)

    # 绘图
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axs = plt.subplots(4, 1, figsize=(12, 14), sharex=True)

    # 图1：流量过程
    axs[0].plot(time, qin, "k--", lw=1.8, label="入库流量Qin")
    axs[0].plot(time, res_A["R"], lw=1.8, label="下泄A(发电优先)")
    axs[0].plot(time, res_B["R"], lw=1.8, label="下泄B(多目标协调)")
    axs[0].axhline(Q_safe, color="r", ls=":", lw=1.5, label="防洪安全流量")
    axs[0].set_ylabel("流量(m3/s)")
    axs[0].set_title("多目标调度流量过程")
    axs[0].legend(ncol=2)
    axs[0].grid(alpha=0.25)

    # 图2：库容过程
    axs[1].plot(time, res_A["S"] / 1e8, lw=1.8, label="库容A")
    axs[1].plot(time, res_B["S"] / 1e8, lw=1.8, label="库容B")
    axs[1].axhline(S_min / 1e8, color="gray", ls="--", lw=1.2, label="Smin")
    axs[1].axhline(S_max / 1e8, color="gray", ls=":", lw=1.2, label="Smax")
    axs[1].set_ylabel("库容(亿m3)")
    axs[1].set_title("库容约束与动态演化")
    axs[1].legend()
    axs[1].grid(alpha=0.25)

    # 图3：策略B通航指标
    ax3 = axs[2]
    ax3.plot(time, res_B["h"], color="tab:blue", lw=1.8, label="水深h")
    ax3.axhline(h_nav_min, color="tab:blue", ls=":", lw=1.3, label="最小通航水深")
    ax3.set_ylabel("水深(m)", color="tab:blue")
    ax3.tick_params(axis="y", labelcolor="tab:blue")

    ax3b = ax3.twinx()
    ax3b.plot(time, res_B["u"], color="tab:orange", lw=1.6, label="流速u")
    ax3b.axhline(u_min, color="tab:orange", ls="--", lw=1.2, label="u_min")
    ax3b.axhline(u_max, color="tab:orange", ls=":", lw=1.2, label="u_max")
    ax3b.set_ylabel("流速(m/s)", color="tab:orange")
    ax3b.tick_params(axis="y", labelcolor="tab:orange")
    ax3.set_title("策略B通航水力响应")
    ax3.grid(alpha=0.25)

    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3b.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, ncol=2, loc="upper right")

    # 图4：功率跟踪
    axs[3].plot(time[:-1], P_demand[:-1], "k--", lw=1.8, label="负荷需求")
    axs[3].plot(time[:-1], res_A["P"], lw=1.8, label="功率A")
    axs[3].plot(time[:-1], res_B["P"], lw=1.8, label="功率B")
    axs[3].set_xlabel("时间(h)")
    axs[3].set_ylabel("功率(MW)")
    axs[3].set_title("发电功率与负荷匹配")
    axs[3].legend()
    axs[3].grid(alpha=0.25)

    plt.tight_layout()
    if SAVE_FIG:
        plt.savefig(FIG_PATH, dpi=150)
        print(f"图已保存: {FIG_PATH}")
    # plt.show()  # 禁用弹窗
