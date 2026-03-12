# -*- coding: utf-8 -*-
"""
教材：《大坝安全监测与智能预警》
章节：第3章 应力应变监测（3.1 基本概念与理论框架）
功能：模拟坝体应力-应变监测，完成参数识别、KPI输出与预警可视化。
"""

import numpy as np
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数定义（可按工程调整）
# =========================
RANDOM_SEED = 2026
N_DAYS = 240                     # 监测时长（天）

# 材料与热力学参数（真值）
E_TRUE = 3.2e4                   # 弹性模量，MPa
ALPHA_T_TRUE = 1.0e-5            # 线膨胀系数，1/℃
CREEP_COEFF = 8e-6               # 徐变系数（应变量级）

# 水位-应力关系参数
H_REF = 100.0                    # 参考水位，m
SIGMA0 = 2.0                     # 基础应力，MPa
K_H1 = 0.12                      # 一次项，MPa/m
K_H2 = 0.004                     # 二次项，MPa/m^2

# 温度与传感器参数
T_REF = 15.0                     # 参考温度，℃
STRAIN_NOISE_STD = 15e-6         # 应变噪声（15 με）
SIGMA_NOISE_STD = 0.08           # 应力噪声（MPa）
STRAIN_DRIFT_PER_DAY = 0.03e-6   # 应变传感器漂移（每天天）

# 信号处理与预警阈值
SG_WINDOW = 21                   # Savitzky-Golay窗口（奇数）
SG_POLYORDER = 3                 # SG多项式阶数
WARN_THRESHOLD = 35e-6           # 残差预警阈值（35 με）


# =========================
# 2) 模型函数与表格打印
# =========================
def strain_model(x_data, e_modulus, alpha_t, bias):
    """应变模型：ε = σ/E + α·ΔT + bias"""
    sigma, delta_t = x_data
    return sigma / e_modulus + alpha_t * delta_t + bias


def print_kpi_table(rows):
    """打印KPI结果表格（纯文本）"""
    headers = ("KPI指标", "数值", "说明")
    table = [headers] + rows
    widths = [max(len(str(r[i])) for r in table) for i in range(3)]

    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    print(line)
    print("| " + " | ".join(str(headers[i]).ljust(widths[i]) for i in range(3)) + " |")
    print(line.replace("-", "="))
    for row in rows:
        print("| " + " | ".join(str(row[i]).ljust(widths[i]) for i in range(3)) + " |")
    print(line)


# =========================
# 3) 主流程：仿真 -> 识别 -> KPI -> 绘图
# =========================
def main():
    rng = np.random.default_rng(RANDOM_SEED)
    t = np.arange(N_DAYS)

    # 3.1 工况构造：水位、温度（季节项 + 短周期项 + 洪峰）
    water_level = (
        H_REF
        + 8.0 * np.sin(2 * np.pi * t / 365 + 0.7)
        + 1.2 * np.sin(2 * np.pi * t / 28)
        + 6.5 * np.exp(-0.5 * ((t - 140) / 9.0) ** 2)
    )
    temperature = (
        15.0
        + 12.0 * np.sin(2 * np.pi * (t - 30) / 365)
        + 2.0 * np.sin(2 * np.pi * t / 14)
    )

    # 3.2 理论应力与应变（应力来自水位，附加温度项和徐变项）
    h_delta = water_level - H_REF
    sigma_true = SIGMA0 + K_H1 * h_delta + K_H2 * (h_delta ** 2)
    creep_term = CREEP_COEFF * np.log1p(t)
    strain_true = sigma_true / E_TRUE + ALPHA_T_TRUE * (temperature - T_REF) + creep_term

    # 3.3 观测数据：叠加噪声与漂移
    sigma_obs = sigma_true + rng.normal(0, SIGMA_NOISE_STD, size=N_DAYS)
    strain_obs = (
        strain_true
        + rng.normal(0, STRAIN_NOISE_STD, size=N_DAYS)
        + STRAIN_DRIFT_PER_DAY * t
    )

    # 3.4 信号平滑（抗噪）
    strain_smooth = savgol_filter(strain_obs, window_length=SG_WINDOW, polyorder=SG_POLYORDER)

    # 3.5 参数识别：拟合 E、α、bias
    delta_t = temperature - T_REF
    p0 = (3.0e4, 1.0e-5, 0.0)
    bounds = ([1.0e4, 0.0, -1e-3], [8.0e4, 5.0e-5, 1e-3])
    popt, _ = curve_fit(
        strain_model,
        (sigma_obs, delta_t),
        strain_smooth,
        p0=p0,
        bounds=bounds,
        maxfev=20000
    )
    e_est, alpha_est, bias_est = popt
    strain_fit = strain_model((sigma_obs, delta_t), e_est, alpha_est, bias_est)

    # 3.6 残差与预警
    residual = strain_smooth - strain_fit
    warn_idx = np.where(np.abs(residual) >= WARN_THRESHOLD)[0]

    # 3.7 KPI计算
    rmse = np.sqrt(np.mean((strain_fit - strain_true) ** 2))
    mae = np.mean(np.abs(strain_fit - strain_true))
    sst = np.sum((strain_true - np.mean(strain_true)) ** 2)
    sse = np.sum((strain_true - strain_fit) ** 2)
    r2 = 1 - sse / sst

    kpi_rows = [
        ("弹性模量估计E", f"{e_est:,.1f} MPa", "应力-应变线性刚度"),
        ("线膨胀系数估计α", f"{alpha_est:.3e} 1/℃", "温度致变形能力"),
        ("偏置项bias", f"{bias_est:.3e}", "系统偏移量"),
        ("E相对误差", f"{(e_est - E_TRUE) / E_TRUE * 100:.2f}%", "估计值对真值"),
        ("α相对误差", f"{(alpha_est - ALPHA_T_TRUE) / ALPHA_T_TRUE * 100:.2f}%", "估计值对真值"),
        ("RMSE", f"{rmse * 1e6:.2f} με", "均方根误差"),
        ("MAE", f"{mae * 1e6:.2f} με", "平均绝对误差"),
        ("R²", f"{r2:.4f}", "拟合优度"),
        ("预警点数", f"{len(warn_idx)} / {N_DAYS}", "|残差|超阈值"),
        ("预警率", f"{len(warn_idx) / N_DAYS * 100:.2f}%", "异常占比"),
        ("峰值应力", f"{np.max(sigma_true):.2f} MPa", "全周期最大应力"),
    ]

    print("\n=== 第3章 应力应变监测仿真 KPI结果 ===")
    print_kpi_table(kpi_rows)

    # 3.8 绘图展示
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # 图1：应力与水位
    axes[0].plot(t, sigma_true, label="理论应力 σ_true (MPa)", lw=2)
    axes[0].plot(t, sigma_obs, label="观测应力 σ_obs (MPa)", lw=1, alpha=0.7)
    axr = axes[0].twinx()
    axr.plot(t, water_level, label="水位 H (m)", ls="--", color="tab:green", alpha=0.85)
    axes[0].set_ylabel("应力 (MPa)")
    axr.set_ylabel("水位 (m)")
    axes[0].set_title("坝体工况：应力与水位")
    axes[0].grid(alpha=0.3)
    l1, n1 = axes[0].get_legend_handles_labels()
    l2, n2 = axr.get_legend_handles_labels()
    axes[0].legend(l1 + l2, n1 + n2, loc="upper left")

    # 图2：应变监测与拟合
    axes[1].plot(t, strain_true * 1e6, label="理论应变 ε_true", lw=2)
    axes[1].plot(t, strain_obs * 1e6, label="观测应变 ε_obs", lw=1, alpha=0.4)
    axes[1].plot(t, strain_smooth * 1e6, label="平滑应变 ε_smooth", lw=2)
    axes[1].plot(t, strain_fit * 1e6, label="模型拟合 ε_fit", lw=2, ls="--")
    axes[1].set_ylabel("应变 (με)")
    axes[1].set_title("应变监测与参数识别")
    axes[1].grid(alpha=0.3)
    axes[1].legend(loc="upper left")

    # 图3：残差与预警
    residual_u = residual * 1e6
    thr_u = WARN_THRESHOLD * 1e6
    axes[2].plot(t, residual_u, label="残差 ε_res", color="tab:purple")
    axes[2].axhline(thr_u, color="red", ls="--", label=f"+阈值 ({thr_u:.0f} με)")
    axes[2].axhline(-thr_u, color="red", ls="--", label=f"-阈值 (-{thr_u:.0f} με)")
    if len(warn_idx) > 0:
        axes[2].scatter(t[warn_idx], residual_u[warn_idx], color="red", s=18, label="预警点")
    axes[2].set_ylabel("残差 (με)")
    axes[2].set_xlabel("监测时间 (天)")
    axes[2].set_title("残差预警结果")
    axes[2].grid(alpha=0.3)
    axes[2].legend(loc="upper left")

    fig.tight_layout()
    plt.savefig('ch03_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch03_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
