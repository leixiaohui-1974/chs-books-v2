# -*- coding: utf-8 -*-
"""
《流域数字孪生与智能决策》第6章（6.1 基本概念与理论框架）
功能：构建 xIL（MiL/SiL/HiL）验证流程仿真，输出KPI结果表，并生成matplotlib对比图。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy import signal

# =========================
# 1) 关键参数定义（集中管理）
# =========================
DT = 1.0                      # 仿真步长（秒，示意）
T_END = 360.0                 # 仿真总时长
TIME = np.arange(0.0, T_END + DT, DT)

SEED = 2026                   # 全局随机种子
LEVEL_INIT = 0.35             # 初始水位（归一化）
LEVEL_MIN, LEVEL_MAX = 0.10, 1.25  # 安全边界

# 被控对象名义参数：dy/dt = -a*y + b*u + d
A_NOM = 0.018
B_NOM = 0.11

# PI 控制器参数
KP = 1.90
KI = 0.06
INT_MIN, INT_MAX = -10.0, 10.0  # 积分抗饱和

# 执行器默认限制
U_MIN, U_MAX = -2.5, 2.5


def build_reference(t: np.ndarray) -> np.ndarray:
    """构建目标轨迹：阶跃+缓慢周期项，模拟调度目标变化。"""
    ref = np.where(t < 80.0, 0.55, 0.90)
    ref = np.where(t > 240.0, 0.75, ref)
    ref = ref + 0.03 * np.sin(2.0 * np.pi * t / 120.0)
    return ref


def build_disturbance(t: np.ndarray, seed: int) -> np.ndarray:
    """构建扰动：低频随机扰动 + 两次脉冲事件，模拟来水不确定性。"""
    rng = np.random.default_rng(seed)
    white = rng.normal(0.0, 1.0, size=t.size)

    # 用 scipy 生成低通扰动（体现流域过程惯性）
    b, a = signal.butter(2, 0.05)
    colored = signal.lfilter(b, a, white)

    pulse_1 = 0.22 * np.exp(-((t - 110.0) / 16.0) ** 2)
    pulse_2 = -0.18 * np.exp(-((t - 275.0) / 18.0) ** 2)
    return 0.06 * colored + pulse_1 + pulse_2


def quantize(value: float, step: float) -> float:
    """量化函数：step<=0 时不量化。"""
    if step <= 0.0:
        return value
    return float(np.round(value / step) * step)


def settling_time_first_step(
    t: np.ndarray,
    y: np.ndarray,
    target: float = 0.90,
    start: float = 80.0,
    end: float = 220.0,
    tol: float = 0.03,
    window: int = 20,
) -> float:
    """计算首个阶跃的调节时间（连续 window 个点落入容差带）。"""
    idx = np.where((t >= start) & (t <= end))[0]
    if idx.size <= window:
        return np.nan

    for i in idx[:-window]:
        if np.all(np.abs(y[i:i + window] - target) <= tol):
            return float(t[i])
    return np.nan


def compute_kpis(t: np.ndarray, r: np.ndarray, y: np.ndarray, u: np.ndarray) -> dict:
    """计算KPI指标。"""
    e = r - y
    rmse = float(np.sqrt(np.mean(e ** 2)))
    iae = float(np.sum(np.abs(e)) * DT)
    safe_rate = float(np.mean((y >= LEVEL_MIN) & (y <= LEVEL_MAX)) * 100.0)
    max_abs_u = float(np.max(np.abs(u)))
    control_energy = float(np.sum(u ** 2) * DT)

    step_mask = (t >= 80.0) & (t <= 220.0)
    if np.any(step_mask):
        peak_y = float(np.max(y[step_mask]))
        overshoot = max(0.0, (peak_y - 0.90) / 0.90 * 100.0)
    else:
        overshoot = np.nan

    ts = settling_time_first_step(t, y)

    return {
        "RMSE": rmse,
        "IAE": iae,
        "SafeRate_pct": safe_rate,
        "Overshoot_pct": float(overshoot),
        "SettlingTime_s": ts,
        "MaxAbsU": max_abs_u,
        "ControlEnergy": control_energy,
    }


def simulate_xil(name: str, cfg: dict, r: np.ndarray, d: np.ndarray) -> dict:
    """统一 xIL 仿真内核：通过 cfg 注入不同阶段特征。"""
    rng = np.random.default_rng(cfg["seed"])

    y = np.zeros_like(r)
    y_meas = np.zeros_like(r)
    u_cmd = np.zeros_like(r)
    u_apply = np.zeros_like(r)

    y[0] = LEVEL_INIT
    integ = 0.0
    last_cmd = 0.0

    delay_steps = int(cfg["delay_steps"])
    delay_buffer = np.zeros(delay_steps + 1)

    for k in range(1, len(r)):
        # 传感器测量（噪声 + 量化）
        noise = rng.normal(0.0, cfg["sensor_noise"])
        y_meas[k - 1] = y[k - 1] + noise
        y_ctrl = quantize(y_meas[k - 1], cfg["y_quant"])

        # 通信丢包：丢包则维持上一控制命令
        err = r[k - 1] - y_ctrl
        if rng.random() >= cfg["packet_loss"]:
            integ = np.clip(integ + err * DT, INT_MIN, INT_MAX)
            raw_u = KP * err + KI * integ
            raw_u = quantize(raw_u, cfg["u_quant"])
            last_cmd = float(np.clip(raw_u, cfg["u_min"], cfg["u_max"]))

        u_cmd[k - 1] = last_cmd

        # 通信时延建模
        delay_buffer = np.roll(delay_buffer, 1)
        delay_buffer[0] = last_cmd
        u_k = delay_buffer[-1]
        u_apply[k - 1] = u_k

        # 参数偏差建模（硬件/现场对象与模型不一致）
        a_real = A_NOM * (1.0 + cfg["a_bias"])
        b_real = B_NOM * (1.0 + cfg["b_bias"])

        dydt = -a_real * y[k - 1] + b_real * u_k + d[k - 1]
        y[k] = y[k - 1] + DT * dydt

    y_meas[-1] = y[-1] + rng.normal(0.0, cfg["sensor_noise"])
    u_cmd[-1] = u_cmd[-2]
    u_apply[-1] = u_apply[-2]

    return {
        "name": name,
        "t": TIME,
        "r": r,
        "y": y,
        "y_meas": y_meas,
        "u_cmd": u_cmd,
        "u_apply": u_apply,
        "dist": d,
        "kpi": compute_kpis(TIME, r, y, u_apply),
    }


def print_kpi_table(results: list) -> None:
    """打印KPI表格。"""
    print("\n=== 第6章 xIL验证流程 KPI结果表 ===")
    header = "{:<8}{:>10}{:>10}{:>12}{:>12}{:>14}{:>10}{:>12}".format(
        "阶段", "RMSE", "IAE", "安全率%", "超调%", "调节时间(s)", "最大|u|", "控制能量"
    )
    print(header)
    print("-" * len(header))
    for item in results:
        k = item["kpi"]
        ts = "未收敛" if np.isnan(k["SettlingTime_s"]) else f"{k['SettlingTime_s']:.1f}"
        line = "{:<8}{:>10.4f}{:>10.3f}{:>12.2f}{:>12.2f}{:>14}{:>10.3f}{:>12.3f}".format(
            item["name"],
            k["RMSE"],
            k["IAE"],
            k["SafeRate_pct"],
            k["Overshoot_pct"],
            ts,
            k["MaxAbsU"],
            k["ControlEnergy"],
        )
        print(line)


def plot_results(results: list) -> None:
    """绘制 xIL 对比图：水位、控制量、误差。"""
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    colors = {"MiL": "#1f77b4", "SiL": "#ff7f0e", "HiL": "#2ca02c"}

    # 图1：输出水位对比
    axes[0].plot(results[0]["t"], results[0]["r"], "k--", linewidth=2, label="参考轨迹 r")
    for item in results:
        axes[0].plot(item["t"], item["y"], color=colors[item["name"]], linewidth=2, label=f"{item['name']} 输出")
    axes[0].axhline(LEVEL_MIN, color="r", linestyle=":", linewidth=1.5, label="安全下限")
    axes[0].axhline(LEVEL_MAX, color="r", linestyle="--", linewidth=1.5, label="安全上限")
    axes[0].set_ylabel("水位（归一化）")
    axes[0].set_title("xIL验证流程：水位响应对比")
    axes[0].grid(alpha=0.3)
    axes[0].legend(ncol=3)

    # 图2：执行器输入对比
    for item in results:
        axes[1].plot(item["t"], item["u_apply"], color=colors[item["name"]], linewidth=2, label=f"{item['name']} 控制输入")
    axes[1].set_ylabel("控制量 u")
    axes[1].set_title("控制输入对比")
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    # 图3：跟踪误差对比
    for item in results:
        err = item["r"] - item["y"]
        axes[2].plot(item["t"], err, color=colors[item["name"]], linewidth=2, label=f"{item['name']} 误差")
    axes[2].set_ylabel("误差 e=r-y")
    axes[2].set_xlabel("时间（s）")
    axes[2].set_title("跟踪误差对比")
    axes[2].grid(alpha=0.3)
    axes[2].legend()

    fig.tight_layout()
    plt.savefig('ch06_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch06_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    # 统一参考轨迹与扰动
    ref = build_reference(TIME)
    dist = build_disturbance(TIME, SEED)

    # xIL阶段配置：从理想到接近工程真实
    scenario_cfg = {
        "MiL": {
            "seed": 11,
            "delay_steps": 0,
            "sensor_noise": 0.000,
            "y_quant": 0.000,
            "u_quant": 0.000,
            "packet_loss": 0.00,
            "u_min": U_MIN,
            "u_max": U_MAX,
            "a_bias": 0.00,
            "b_bias": 0.00,
        },
        "SiL": {
            "seed": 22,
            "delay_steps": 1,
            "sensor_noise": 0.003,
            "y_quant": 0.002,
            "u_quant": 0.005,
            "packet_loss": 0.00,
            "u_min": U_MIN,
            "u_max": U_MAX,
            "a_bias": 0.03,
            "b_bias": -0.02,
        },
        "HiL": {
            "seed": 33,
            "delay_steps": 3,
            "sensor_noise": 0.012,
            "y_quant": 0.005,
            "u_quant": 0.010,
            "packet_loss": 0.05,
            "u_min": -2.0,
            "u_max": 2.0,
            "a_bias": 0.08,
            "b_bias": -0.07,
        },
    }

    results = []
    for name in ["MiL", "SiL", "HiL"]:
        results.append(simulate_xil(name, scenario_cfg[name], ref, dist))

    print_kpi_table(results)
    plot_results(results)


if __name__ == "__main__":
    main()
