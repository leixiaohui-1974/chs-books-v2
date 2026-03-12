**Python仿真脚本（满足你给出的7项要求）**
```python
# -*- coding: utf-8 -*-
"""
《人工智能与水利水电工程》 第10章仿真脚本
功能：仿真AI推理时延接入SCADA后对前池水位闭环控制性能的影响，
输出KPI结果表格，并生成对比图。
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# =========================
# 关键参数定义（可直接调参）
# =========================
SIM_DURATION_S = 7200.0      # 仿真总时长（s）
DT = 0.5                     # 离散步长（s）
TIME = np.arange(0.0, SIM_DURATION_S + DT, DT)

# 前池动力学参数
A_FOREBAY = 900.0            # 前池等效面积（m^2）
H_REF = 5.0                  # 目标水位（m）
H_INIT = 5.0                 # 初始水位（m）

# 入流扰动参数
Q_IN_BASE = 0.72             # 基础入流（m^3/s）
Q_IN_SIN_AMP = 0.02          # 周期扰动振幅（m^3/s）
Q_IN_SIN_PERIOD = 1800.0     # 周期扰动周期（s）
DIST1_START, DIST1_END, DIST1_DELTA = 1200.0, 2400.0, 0.22
DIST2_START, DIST2_END, DIST2_DELTA = 4200.0, 5100.0, -0.10

# 泵站与控制器参数
PUMP_GAIN = 1.6              # 指令到目标出流的增益（m^3/s）
PUMP_TAU = 30.0              # 泵站一阶惯性时间常数（s）
U_BIAS = 0.45                # 平衡工况偏置
U_MIN, U_MAX = 0.0, 1.0      # 控制指令限幅
KP = 2.4                     # PI比例系数
KI = 0.03                    # PI积分系数

# KPI评价参数
SETTLING_BAND = 0.05         # 整定带（m）
ANALYSIS_START_S = 3000.0    # 末段振荡分析起点（s）

# 不同部署方案：时延代表AI推理+通信总时延
SCENARIOS = [
    {"name": "传统PLC基线(0ms)", "delay_s": 0.000, "color": "#1f77b4"},
    {"name": "边缘AI-INT8(24ms)", "delay_s": 0.024, "color": "#2ca02c"},
    {"name": "边缘AI-FP32(120ms)", "delay_s": 0.120, "color": "#ff7f0e"},
    {"name": "云端AI(500ms)", "delay_s": 0.500, "color": "#d62728"},
]


def build_inflow(t: np.ndarray) -> np.ndarray:
    """构造入流：基础流量 + 周期扰动 + 两段阶跃扰动"""
    q_in = Q_IN_BASE + Q_IN_SIN_AMP * np.sin(2.0 * np.pi * t / Q_IN_SIN_PERIOD)
    q_in += np.where((t >= DIST1_START) & (t < DIST1_END), DIST1_DELTA, 0.0)
    q_in += np.where((t >= DIST2_START) & (t < DIST2_END), DIST2_DELTA, 0.0)
    return q_in


def calc_settling_time(error: np.ndarray, t: np.ndarray, band: float) -> float:
    """计算整定时间：最后一次越带后重新进入整定带的时刻"""
    out_idx = np.where(np.abs(error) > band)[0]
    if out_idx.size == 0:
        return 0.0
    last = out_idx[-1]
    if last >= len(t) - 1:
        return np.nan
    return float(t[last + 1])


def calc_tail_osc_amp(signal: np.ndarray, t: np.ndarray, start_t: float) -> float:
    """用SciPy峰谷检测估算末段振荡半振幅"""
    tail = signal[t >= start_t]
    if tail.size < 10:
        return 0.0
    peaks, _ = find_peaks(tail)
    valleys, _ = find_peaks(-tail)
    if peaks.size < 2 or valleys.size < 2:
        return 0.0
    n1 = min(3, peaks.size)
    n2 = min(3, valleys.size)
    p_mean = np.mean(tail[peaks[-n1:]])
    v_mean = np.mean(tail[valleys[-n2:]])
    return float(max(0.0, 0.5 * (p_mean - v_mean)))


def simulate_scenario(name: str, delay_s: float, color: str) -> dict:
    """单场景仿真：含时延PI控制 + 泵站一阶惯性"""
    n = TIME.size
    h = np.zeros(n)
    q_out = np.zeros(n)
    u_cmd = np.zeros(n)
    u_hist = np.full(n, U_BIAS)

    h[0] = H_INIT
    q_out[0] = PUMP_GAIN * U_BIAS
    q_in = build_inflow(TIME)

    delay_steps = int(round(delay_s / DT))
    i_error = 0.0

    for k in range(n - 1):
        # 误差定义：水位高于目标时误差为正，控制器提高出流
        error = h[k] - H_REF
        i_error += error * DT

        # PI控制器（带限幅）
        u_raw = U_BIAS + KP * error + KI * i_error
        u = np.clip(u_raw, U_MIN, U_MAX)

        # 简单抗积分饱和
        if (u != u_raw) and (KI > 1e-12):
            i_error -= 0.3 * error * DT

        u_cmd[k] = u
        u_hist[k] = u

        # 时延通道：当前只读取过去delay_steps步的控制指令
        delayed_idx = max(0, k - delay_steps)
        u_delayed = u_hist[delayed_idx]

        # 泵站出流一阶惯性
        q_target = PUMP_GAIN * u_delayed
        q_out[k + 1] = q_out[k] + DT * (q_target - q_out[k]) / PUMP_TAU

        # 前池水位离散更新
        h[k + 1] = h[k] + DT * (q_in[k] - q_out[k]) / A_FOREBAY
        if h[k + 1] < 0.0:
            h[k + 1] = 0.0

    u_cmd[-1] = u_cmd[-2]
    error = h - H_REF

    kpi = {
        "delay_ms": delay_s * 1000.0,
        "rmse_m": float(np.sqrt(np.mean(error ** 2))),
        "mae_m": float(np.mean(np.abs(error))),
        "overshoot_m": float(max(0.0, np.max(h) - H_REF)),
        "undershoot_m": float(max(0.0, H_REF - np.min(h))),
        "settling_s": float(calc_settling_time(error, TIME, SETTLING_BAND)),
        "tail_amp_m": float(calc_tail_osc_amp(h, TIME, ANALYSIS_START_S)),
        "control_rate_1ps": float(np.mean(np.abs(np.diff(u_cmd))) / DT),
    }

    return {
        "name": name,
        "color": color,
        "delay_s": delay_s,
        "t": TIME,
        "h": h,
        "q_in": q_in,
        "q_out": q_out,
        "u_cmd": u_cmd,
        "error": error,
        "kpi": kpi,
    }


def fmt(x: float, nd: int = 4) -> str:
    if isinstance(x, float) and np.isnan(x):
        return "--"
    return f"{x:.{nd}f}"


def print_kpi_table(results: list) -> None:
    """打印KPI结果表格"""
    print("\nKPI结果表格（第10章：AI时延-控制性能对比）")
    print("| 场景 | 时延(ms) | RMSE(m) | MAE(m) | 超调(m) | 欠调(m) | 整定时间(s) | 末段振幅(m) | 控制动作率(1/s) |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        k = r["kpi"]
        print(
            f"| {r['name']} | {fmt(k['delay_ms'], 1)} | {fmt(k['rmse_m'])} | {fmt(k['mae_m'])} "
            f"| {fmt(k['overshoot_m'])} | {fmt(k['undershoot_m'])} | {fmt(k['settling_s'], 1)} "
            f"| {fmt(k['tail_amp_m'])} | {fmt(k['control_rate_1ps'], 5)} |"
        )


def plot_results(results: list) -> None:
    """生成Matplotlib图"""
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), dpi=120)
    ax1, ax2, ax3, ax4 = axes.flatten()

    # 图1：水位曲线
    for r in results:
        ax1.plot(r["t"], r["h"], lw=1.8, color=r["color"], label=r["name"])
    ax1.axhline(H_REF, color="k", ls="--", lw=1.2, label="目标水位")
    ax1.set_title("前池水位响应")
    ax1.set_xlabel("时间 (s)")
    ax1.set_ylabel("水位 h (m)")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=9)

    # 图2：水位误差
    for r in results:
        ax2.plot(r["t"], r["error"], lw=1.5, color=r["color"], label=r["name"])
    ax2.axhline(SETTLING_BAND, color="#666666", ls="--", lw=1.0)
    ax2.axhline(-SETTLING_BAND, color="#666666", ls="--", lw=1.0)
    ax2.set_title("水位误差 e(t)=h(t)-h_ref")
    ax2.set_xlabel("时间 (s)")
    ax2.set_ylabel("误差 (m)")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=9)

    # 图3：控制指令
    for r in results:
        ax3.plot(r["t"], r["u_cmd"], lw=1.5, color=r["color"], label=r["name"])
    ax3.set_title("控制指令 u(t)")
    ax3.set_xlabel("时间 (s)")
    ax3.set_ylabel("阀门/变频指令")
    ax3.grid(alpha=0.3)
    ax3.legend(fontsize=9)

    # 扰动时间窗标记
    for ax in [ax1, ax2, ax3]:
        ax.axvspan(DIST1_START, DIST1_END, color="orange", alpha=0.12)
        ax.axvspan(DIST2_START, DIST2_END, color="cyan", alpha=0.12)

    # 图4：时延与KPI关系
    delays = np.array([r["kpi"]["delay_ms"] for r in results], dtype=float)
    rmse = np.array([r["kpi"]["rmse_m"] for r in results], dtype=float)
    settling = np.array([r["kpi"]["settling_s"] for r in results], dtype=float)

    ax4.bar(delays, rmse, width=20, color=[r["color"] for r in results], alpha=0.85, label="RMSE")
    ax4.set_title("时延对KPI的影响")
    ax4.set_xlabel("AI推理时延 (ms)")
    ax4.set_ylabel("RMSE (m)")
    ax4.grid(alpha=0.3, axis="y")

    ax4b = ax4.twinx()
    ax4b.plot(delays, settling, "o--", color="black", lw=1.6, label="整定时间")
    ax4b.set_ylabel("整定时间 (s)")

    h1, l1 = ax4.get_legend_handles_labels()
    h2, l2 = ax4b.get_legend_handles_labels()
    ax4.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=9)

    fig.suptitle("《人工智能与水利水电工程》第10章：AI工程化部署时延仿真", fontsize=14)
    fig.tight_layout()
    plt.show()


def main():
    results = [simulate_scenario(**cfg) for cfg in SCENARIOS]
    print_kpi_table(results)
    plot_results(results)


if __name__ == "__main__":
    main()
```

**800字中文代码解读**
这段程序把第10章“从实验室模型到SCADA工程部署”的关键矛盾转化为可复现实验：同一套水位控制算法，在不同AI推理时延条件下，闭环性能会发生系统性变化。脚本首先在参数区统一定义了物理量、控制器系数、扰动强度和评价指标阈值，这样做的意义是把“工程假设”显式化，便于后续做灵敏度分析、方案复核和参数审计。`build_inflow`函数构造了更接近现场的入流信号，包括基线工况、周期波动和两段阶跃扰动，分别对应日常来水起伏、调度波动和突发工况。核心仿真在`simulate_scenario`中完成，采用离散质量守恒方程更新前池水位：每一步先根据水位误差计算PI控制指令，再经过限幅和简化抗积分饱和，随后引入“时延通道”读取历史控制量，最后通过泵站一阶惯性得到实际出流。该流程对应真实系统中的“控制器计算-通信传输-AI推理-执行机构响应”链路。  
KPI部分不是单一误差，而是面向运行管理的多指标集合：`RMSE`和`MAE`反映整体跟踪精度；`overshoot/undershoot`反映安全边界风险；`settling_s`衡量扰动后恢复速度；`tail_amp_m`借助`scipy.signal.find_peaks`评估后段振荡强度；`control_rate_1ps`表征执行机构动作频率，间接关联设备磨损和能耗。通过这组指标，可以避免“只看精度、不看可运维性”的片面结论。  
`print_kpi_table`按表格形式输出结果，便于直接粘贴到章节实验记录或报告正文。`plot_results`给出四类图：水位响应、误差演化、控制指令变化、时延与KPI关系。前三图用于解释动态过程，第四图用于支持工程决策，即是否值得为更低时延投入边缘算力。脚本场景里“边缘AI-INT8(24ms)”与“云端AI(500ms)”并列，体现了第10章强调的工程化观点：量化与部署不只是模型压缩问题，更是控制稳定性问题。整体上，这段代码把数学模型、控制逻辑、部署差异和评价体系统一到一个可运行闭环中，可作为教材第10章仿真附录的主脚本，也可扩展到泵站群、多节点协同和MLOps在线更新实验。  
（补充：当前会话环境策略拦截了`python`执行命令，因此我无法在终端实际跑图；脚本语法和依赖按标准`numpy/scipy/matplotlib`接口编写。）

## 参考文献

1. Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press.
2. Shen, C. (2018). A Transdisciplinary Review of Deep Learning Research and Its Relevance for Water Resources Scientists. *Water Resources Research*, 54(11), 8558-8593.
3. Kratzert, F., et al. (2018). Rainfall–runoff modelling using Long Short-Term Memory (LSTM) networks. *Hydrology and Earth System Sciences*, 22(11), 6005-6022.
4. Lei et al. (2025b). 自主水网：概念、架构与关键技术. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0079
5. Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077
