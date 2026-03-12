# -*- coding: utf-8 -*-
"""
教材：《洪水预报与防洪调度》
章节：第7章 蓄滞洪区启用决策（7.1 基本概念与理论框架）
功能：实现“洪水预报-启用判别-分洪调度-风险评估”仿真，
      并用scipy优化蓄滞洪区启用阈值与闸门开度，输出KPI表与图形。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import differential_evolution

# ========================= 关键参数（可调） =========================
SIM_HOURS = 72.0                     # 仿真总时长（h）
DT_H = 0.25                          # 时间步长（h）
DT = DT_H * 3600.0                   # 时间步长（s）
N = int(SIM_HOURS / DT_H) + 1
TIME_H = np.arange(N) * DT_H

# 上游入流过程参数
Q_BASE = 800.0
Q_PEAK1 = 4300.0
Q_PEAK2 = 2600.0
PEAK1_T = 24.0
PEAK2_T = 40.0
SIGMA1 = 6.0
SIGMA2 = 8.5

# 主河道等效蓄泄关系参数
S0 = 3.5e7                           # 初始等效库容（m3）
H0 = 26.0                            # 对应基准水位（m）
STAGE_A = 2.3
STAGE_B = 1.25
H_TAIL = 26.8                        # 下游尾水位（m）
QOUT_COEF = 650.0                    # 主河道出流系数
QOUT_MAX = 6500.0                    # 主河道最大安全泄量（m3/s）

# 蓄滞洪区与闸门参数
VDET_CAP = 8.5e7                     # 蓄滞洪区有效容积（m3）
H_DIV = 29.3                         # 分洪口启动水位基准（m）
H_CLOSE = 28.9                       # 允许关闭分洪口的回落水位（m）
C_DIV = 1450.0                       # 分洪流量系数
GATE_MIN = 0.35
GATE_MAX = 1.00
Q_RET = 60.0                         # 退水能力（m3/s），主河道安全时回排

# 决策触发参数
H_FLOOD = 30.8                       # 下游防护控制水位（m）
H_SAFE = 30.2                        # 主河道安全回排水位（m）
LOOKAHEAD_H = 12.0                   # 预报前瞻时长（h）
LOOKAHEAD_STEPS = int(LOOKAHEAD_H / DT_H)
TRIGGER_PERSIST_H = 1.0              # 超阈持续时长（h）
TRIGGER_PERSIST_STEPS = int(TRIGGER_PERSIST_H / DT_H)
MIN_OPEN_H = 6.0                     # 最小连续启用时长（h）
MIN_OPEN_STEPS = int(MIN_OPEN_H / DT_H)
Q_ALERT = 0.90 * (Q_BASE + Q_PEAK1)  # 入流预警阈值

# 目标函数权重（越小越好）
W_PEAK = 120.0
W_DURATION = 8.0
W_OCCUPY = 10.0
W_DIVERT = 2.0
W_OPEN = 1.2

# 优化参数
OPT_SEED = 42
OPT_MAXITER = 35
OPT_POPSIZE = 12

# 绘图参数
PLOT_SURFACE_NH = 30
PLOT_SURFACE_NG = 24

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def build_inflow(t_h: np.ndarray) -> np.ndarray:
    """构造双峰洪水过程线（m3/s）"""
    pulse1 = Q_PEAK1 * np.exp(-0.5 * ((t_h - PEAK1_T) / SIGMA1) ** 2)
    pulse2 = Q_PEAK2 * np.exp(-0.5 * ((t_h - PEAK2_T) / SIGMA2) ** 2)
    return Q_BASE + pulse1 + pulse2


QIN = build_inflow(TIME_H)


def stage_from_storage(storage: np.ndarray) -> np.ndarray:
    """等效库容-水位关系"""
    return H0 + STAGE_A * np.power(np.maximum(storage, 0.0) / 1.0e8, STAGE_B)


def simulate_policy(h_trigger: float, gate_ratio: float) -> dict:
    """
    在给定策略下仿真：
    - h_trigger：启用阈值水位
    - gate_ratio：闸门相对开度（0~1）
    """
    s = np.zeros(N)                     # 主河道等效库容
    h = np.zeros(N)                     # 主河道控制断面水位
    qout = np.zeros(N)                  # 下泄流量
    qdiv = np.zeros(N)                  # 分洪流量
    vdet = np.zeros(N)                  # 蓄滞洪区已占用容积
    enable = np.zeros(N, dtype=bool)    # 启用状态

    s[0] = S0
    h[0] = stage_from_storage(s[0])

    persist_count = 0
    open_steps = 0
    opened = False

    for k in range(N - 1):
        h[k] = stage_from_storage(s[k])

        # 预报触发：当前水位 + 前瞻入流峰值，形成“预报-规则”决策框架
        q_forecast_peak = np.max(QIN[k:min(N, k + LOOKAHEAD_STEPS)])
        cond_now = (h[k] >= h_trigger) and (q_forecast_peak >= Q_ALERT)

        if not opened:
            persist_count = persist_count + 1 if cond_now else 0
            if persist_count >= TRIGGER_PERSIST_STEPS:
                opened = True
                open_steps = 0
        else:
            # 已启用后，满足最小时长且水位回落才允许关闭
            if (open_steps >= MIN_OPEN_STEPS and h[k] < H_CLOSE) or (vdet[k] >= 0.995 * VDET_CAP):
                opened = False
                persist_count = 0

        enable[k] = opened

        # 主河道下泄能力
        qout[k] = np.clip(
            QOUT_COEF * np.maximum(h[k] - H_TAIL, 0.0) ** 1.5,
            0.0,
            QOUT_MAX
        )

        # 分洪能力（受闸门、河道水位、库容余量三重约束）
        if enable[k] and vdet[k] < VDET_CAP:
            qdiv_capacity = gate_ratio * C_DIV * np.maximum(h[k] - H_DIV, 0.0) ** 1.5
            qdiv_room = (VDET_CAP - vdet[k]) / DT
            qdiv[k] = np.clip(qdiv_capacity, 0.0, max(qdiv_room, 0.0))
        else:
            qdiv[k] = 0.0

        # 退水：只有当主河道回到安全水位以下时才回排
        qret = Q_RET if (vdet[k] > 0.0 and h[k] < H_SAFE) else 0.0

        # 水量平衡
        s[k + 1] = max(s[k] + (QIN[k] - qout[k] - qdiv[k] + qret) * DT, 0.0)
        vdet[k + 1] = np.clip(vdet[k] + (qdiv[k] - qret) * DT, 0.0, VDET_CAP)

        if opened:
            open_steps += 1

    # 补齐最后一步
    h[-1] = stage_from_storage(s[-1])
    qout[-1] = np.clip(QOUT_COEF * np.maximum(h[-1] - H_TAIL, 0.0) ** 1.5, 0.0, QOUT_MAX)
    enable[-1] = enable[-2]
    qdiv[-1] = qdiv[-2]

    # KPI
    exceed = np.maximum(h - H_FLOOD, 0.0)
    peak_exceed = float(np.max(exceed))
    exceed_duration = float(np.sum(exceed > 0.0) * DT_H)
    exceed_integral = float(np.trapz(exceed, TIME_H))
    divert_mcm = float(np.sum(qdiv) * DT / 1e6)
    occupy_ratio = float(np.max(vdet) / VDET_CAP)
    open_duration = float(np.sum(enable) * DT_H)

    # 目标函数：风险代价 + 启用代价
    objective_j = (
        W_PEAK * peak_exceed
        + W_DURATION * exceed_integral
        + W_OCCUPY * occupy_ratio
        + W_DIVERT * (divert_mcm / (VDET_CAP / 1e6))
        + W_OPEN * (open_duration / SIM_HOURS)
    )

    open_idx = np.where(enable)[0]
    first_open_time = float(TIME_H[open_idx[0]]) if len(open_idx) > 0 else np.nan

    return {
        "h": h,
        "qout": qout,
        "qdiv": qdiv,
        "vdet": vdet,
        "enable": enable,
        "peak_h": float(np.max(h)),
        "peak_exceed": peak_exceed,
        "exceed_duration": exceed_duration,
        "divert_mcm": divert_mcm,
        "occupy_ratio": occupy_ratio,
        "first_open_time": first_open_time,
        "open_duration": open_duration,
        "J": float(objective_j),
    }


def objective(x: np.ndarray) -> float:
    """优化器调用的目标函数"""
    h_trigger, gate_ratio = x
    return simulate_policy(h_trigger, gate_ratio)["J"]


def fmt_num(v: float, precision: int = 3) -> str:
    """数值格式化"""
    if np.isnan(v):
        return "--"
    return f"{v:.{precision}f}"


def calc_change(base_val: float, opt_val: float, lower_is_better: bool = True) -> str:
    """计算优化前后变化百分比"""
    if np.isnan(base_val) or np.isnan(opt_val):
        return "--"
    if abs(base_val) < 1e-12:
        return "--"
    if lower_is_better:
        change = (base_val - opt_val) / abs(base_val) * 100.0
    else:
        change = (opt_val - base_val) / abs(base_val) * 100.0
    return f"{change:+.2f}%"


def print_kpi_table(base: dict, opt: dict, best_h: float, best_gate: float):
    """打印KPI表格"""
    rows = [
        ("优化阈值水位 h_trigger (m)", "--", fmt_num(best_h, 3), "--"),
        ("优化闸门开度 gate_ratio (-)", "--", fmt_num(best_gate, 3), "--"),
        ("峰值水位 (m)", fmt_num(base["peak_h"], 3), fmt_num(opt["peak_h"], 3), calc_change(base["peak_h"], opt["peak_h"], True)),
        ("最大超警水深 (m)", fmt_num(base["peak_exceed"], 3), fmt_num(opt["peak_exceed"], 3), calc_change(base["peak_exceed"], opt["peak_exceed"], True)),
        ("超警历时 (h)", fmt_num(base["exceed_duration"], 2), fmt_num(opt["exceed_duration"], 2), calc_change(base["exceed_duration"], opt["exceed_duration"], True)),
        ("分洪总量 (百万m3)", fmt_num(base["divert_mcm"], 3), fmt_num(opt["divert_mcm"], 3), calc_change(base["divert_mcm"], opt["divert_mcm"], True)),
        ("最大占用率 (%)", fmt_num(base["occupy_ratio"] * 100.0, 2), fmt_num(opt["occupy_ratio"] * 100.0, 2), calc_change(base["occupy_ratio"], opt["occupy_ratio"], True)),
        ("首次启用时刻 (h)", fmt_num(base["first_open_time"], 2), fmt_num(opt["first_open_time"], 2), "--"),
        ("启用总历时 (h)", fmt_num(base["open_duration"], 2), fmt_num(opt["open_duration"], 2), calc_change(base["open_duration"], opt["open_duration"], True)),
        ("综合目标函数 J", fmt_num(base["J"], 3), fmt_num(opt["J"], 3), calc_change(base["J"], opt["J"], True)),
    ]

    headers = ("指标", "基准方案", "优化方案", "变化")
    w0 = max(len(headers[0]), max(len(r[0]) for r in rows))
    w1 = max(len(headers[1]), max(len(r[1]) for r in rows))
    w2 = max(len(headers[2]), max(len(r[2]) for r in rows))
    w3 = max(len(headers[3]), max(len(r[3]) for r in rows))

    line = f"+-{'-' * w0}-+-{'-' * w1}-+-{'-' * w2}-+-{'-' * w3}-+"
    print("\n" + "=" * 80)
    print("KPI结果表（第7章：蓄滞洪区启用决策）")
    print("=" * 80)
    print(line)
    print(f"| {headers[0].ljust(w0)} | {headers[1].ljust(w1)} | {headers[2].ljust(w2)} | {headers[3].ljust(w3)} |")
    print(line)
    for r in rows:
        print(f"| {r[0].ljust(w0)} | {r[1].rjust(w1)} | {r[2].rjust(w2)} | {r[3].rjust(w3)} |")
    print(line)


def build_objective_surface(h_bounds, g_bounds, n_h=25, n_g=20):
    """构建目标函数曲面，用于可视化优化景观"""
    hs = np.linspace(h_bounds[0], h_bounds[1], n_h)
    gs = np.linspace(g_bounds[0], g_bounds[1], n_g)
    zz = np.zeros((n_g, n_h))
    for i, g in enumerate(gs):
        for j, h in enumerate(hs):
            zz[i, j] = simulate_policy(h, g)["J"]
    return hs, gs, zz


def plot_results(base: dict, opt: dict, best_h: float, best_gate: float):
    """绘制结果图"""
    hs, gs, zz = build_objective_surface(
        h_bounds=(29.4, 31.2),
        g_bounds=(GATE_MIN, GATE_MAX),
        n_h=PLOT_SURFACE_NH,
        n_g=PLOT_SURFACE_NG
    )

    fig = plt.figure(figsize=(14, 10))

    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(TIME_H, QIN, color="tab:blue", lw=2.0, label="上游入流 Qin")
    ax1.plot(TIME_H, base["qout"], color="gray", lw=1.6, ls="--", label="基准下泄 Qout")
    ax1.plot(TIME_H, opt["qout"], color="tab:green", lw=1.8, label="优化下泄 Qout")
    ax1.plot(TIME_H, opt["qdiv"], color="tab:red", lw=1.8, label="优化分洪 Qdiv")
    ax1.set_title("流量过程线对比")
    ax1.set_xlabel("时间 (h)")
    ax1.set_ylabel("流量 (m3/s)")
    ax1.grid(alpha=0.25)
    ax1.legend(fontsize=9)

    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(TIME_H, base["h"], color="gray", lw=1.7, ls="--", label="基准水位")
    ax2.plot(TIME_H, opt["h"], color="tab:orange", lw=2.0, label="优化水位")
    ax2.axhline(H_FLOOD, color="tab:red", ls="--", lw=1.2, label="防护控制水位")
    ax2.axhline(best_h, color="tab:purple", ls=":", lw=1.4, label="最优启用阈值")
    ax2.fill_between(
        TIME_H, np.min(opt["h"]) - 0.2, np.max(opt["h"]) + 0.2,
        where=opt["enable"], color="gold", alpha=0.18, label="蓄滞洪区启用时段"
    )
    ax2.set_title("控制断面水位与启用时段")
    ax2.set_xlabel("时间 (h)")
    ax2.set_ylabel("水位 (m)")
    ax2.grid(alpha=0.25)
    ax2.legend(fontsize=9)

    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(TIME_H, opt["vdet"] / 1e6, color="tab:cyan", lw=2.0, label="蓄滞洪区占用容积")
    ax3.axhline(VDET_CAP / 1e6, color="black", ls="--", lw=1.2, label="有效容积上限")
    ax3.set_title("蓄滞洪区容积演进")
    ax3.set_xlabel("时间 (h)")
    ax3.set_ylabel("容积 (百万m3)")
    ax3.grid(alpha=0.25)
    ax3.legend(fontsize=9)

    ax4 = plt.subplot(2, 2, 4)
    hm, gm = np.meshgrid(hs, gs)
    cs = ax4.contourf(hm, gm, zz, levels=20, cmap="viridis")
    plt.colorbar(cs, ax=ax4, fraction=0.046, pad=0.04, label="目标函数 J")
    ax4.scatter([best_h], [best_gate], color="red", s=50, label="最优解")
    ax4.set_title("决策变量-目标函数景观")
    ax4.set_xlabel("启用阈值 h_trigger (m)")
    ax4.set_ylabel("闸门开度 gate_ratio (-)")
    ax4.legend(fontsize=9)

    plt.suptitle("第7章 蓄滞洪区启用决策仿真：预报触发 + 优化调度", fontsize=14)
    plt.tight_layout()
    plt.savefig('ch07_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch07_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    # 基准方案：极高阈值 + 最小开度，近似不启用蓄滞洪区
    baseline = simulate_policy(h_trigger=99.0, gate_ratio=GATE_MIN)

    # 优化求解：寻找最优启用阈值与闸门开度
    result = differential_evolution(
        objective,
        bounds=[(29.4, 31.2), (GATE_MIN, GATE_MAX)],
        seed=OPT_SEED,
        maxiter=OPT_MAXITER,
        popsize=OPT_POPSIZE,
        tol=1e-3,
        polish=True
    )
    best_h, best_gate = result.x
    optimized = simulate_policy(best_h, best_gate)

    # 打印KPI并绘图
    print_kpi_table(baseline, optimized, best_h, best_gate)
    plot_results(baseline, optimized, best_h, best_gate)


if __name__ == "__main__":
    main()
