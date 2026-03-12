# -*- coding: utf-8 -*-
"""
教材：《洪水预报与防洪调度》
章节：第3章 洪水预报实时校正（3.1 基本概念与理论框架）
功能：构建“基础洪水预报 + 卡尔曼实时校正”仿真，输出KPI表格并绘制过程线图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# =========================
# 1) 关键参数（便于教学与调参）
# =========================
RANDOM_SEED = 42
N_STEPS = 240                 # 仿真总时段（小时）
DT = 1.0                      # 时间步长（小时）
CALIB_RATIO = 0.45            # 前段用于率定比例

# 真实流域参数（用于构造“真值”）
A_TRUE = 0.86                 # 线性蓄泄系数
B_TRUE = 1.65                 # 降雨-径流转换系数
PROCESS_NOISE_STD = 2.5       # 过程噪声标准差（m3/s）
OBS_NOISE_STD = 7.0           # 观测噪声标准差（m3/s）

# 实时校正参数（偏差状态卡尔曼）
PHI = 0.72                    # 偏差AR(1)系数
Q_VAR = 8.0                   # 状态噪声方差
R_VAR = OBS_NOISE_STD ** 2    # 观测噪声方差


def run_linear_reservoir(a, b, rain):
    """线性蓄泄模型：Q_t = a*Q_{t-1} + b*P_t"""
    q = np.zeros_like(rain, dtype=float)
    for t in range(1, len(rain)):
        q[t] = a * q[t - 1] + b * rain[t]
    return np.clip(q, 0.0, None)


def calc_metrics(y_true, y_pred):
    """计算KPI指标"""
    eps = 1e-6
    err = y_true - y_pred
    rmse = np.sqrt(np.mean(err ** 2))
    mae = np.mean(np.abs(err))
    nse = 1.0 - np.sum(err ** 2) / (np.sum((y_true - np.mean(y_true)) ** 2) + eps)
    pbias = 100.0 * np.sum(y_pred - y_true) / (np.sum(y_true) + eps)
    peak_err = 100.0 * (np.max(y_pred) - np.max(y_true)) / (np.max(y_true) + eps)
    return rmse, mae, nse, pbias, peak_err


def print_kpi_table(kpi_base, kpi_corr, a_est, b_est, converged):
    headers = ["方案", "RMSE", "MAE", "NSE", "PBIAS(%)", "PeakErr(%)"]
    print("\n" + "=" * 76)
    print(f"{headers[0]:<14}{headers[1]:>10}{headers[2]:>10}{headers[3]:>10}{headers[4]:>14}{headers[5]:>14}")
    print("-" * 76)
    print(f"{'基础预报':<14}{kpi_base[0]:>10.2f}{kpi_base[1]:>10.2f}{kpi_base[2]:>10.3f}{kpi_base[3]:>14.2f}{kpi_base[4]:>14.2f}")
    print(f"{'实时校正预报':<14}{kpi_corr[0]:>10.2f}{kpi_corr[1]:>10.2f}{kpi_corr[2]:>10.3f}{kpi_corr[3]:>14.2f}{kpi_corr[4]:>14.2f}")
    print("=" * 76)
    print(f"率定参数: A_EST={a_est:.4f}, B_EST={b_est:.4f}, 优化收敛={converged}")


def main():
    np.random.seed(RANDOM_SEED)
    t = np.arange(N_STEPS) * DT

    # =========================
    # 2) 构造降雨与真值流量
    # =========================
    # 间歇性降雨 + 暴雨脉冲
    rain = np.random.gamma(shape=0.55, scale=9.0, size=N_STEPS)
    rain *= (np.random.rand(N_STEPS) < 0.35)
    storm_centers = [55, 120, 175, 210]
    for c in storm_centers:
        rain += 22.0 * np.exp(-0.5 * ((np.arange(N_STEPS) - c) / 4.0) ** 2)
    rain = np.clip(rain, 0.0, None)

    # 真实流量（系统状态）+ 观测噪声
    q_true = np.zeros(N_STEPS, dtype=float)
    for k in range(1, N_STEPS):
        q_true[k] = A_TRUE * q_true[k - 1] + B_TRUE * rain[k] + np.random.normal(0, PROCESS_NOISE_STD)
    q_true = np.clip(q_true, 0.0, None)

    q_obs = q_true + np.random.normal(0, OBS_NOISE_STD, size=N_STEPS)
    q_obs = np.clip(q_obs, 0.0, None)

    # =========================
    # 3) 基础模型率定（历史段）
    # =========================
    n_calib = int(N_STEPS * CALIB_RATIO)

    def loss(params):
        a, b = params
        q_sim = run_linear_reservoir(a, b, rain[:n_calib])
        return np.sqrt(np.mean((q_obs[:n_calib] - q_sim) ** 2))

    init = np.array([0.78, 1.10], dtype=float)
    bounds = [(0.60, 0.98), (0.50, 3.00)]
    opt = minimize(loss, x0=init, method="L-BFGS-B", bounds=bounds)
    a_est, b_est = opt.x

    q_fcst = run_linear_reservoir(a_est, b_est, rain)

    # =========================
    # 4) 实时校正（偏差状态卡尔曼滤波）
    # =========================
    # 状态: bias_k = q_obs_k - q_fcst_k
    # 预测: bias_k = PHI*bias_{k-1} + w_k
    # 更新: res_k = bias_k + v_k, res_k = q_obs_k - q_fcst_k
    bias_est = np.zeros(N_STEPS, dtype=float)
    p_var = np.zeros(N_STEPS, dtype=float)
    q_corr = np.zeros(N_STEPS, dtype=float)

    bias_est[0] = 0.0
    p_var[0] = 60.0
    q_corr[0] = max(q_fcst[0] + bias_est[0], 0.0)

    for k in range(1, N_STEPS):
        bias_pred = PHI * bias_est[k - 1]
        p_pred = PHI ** 2 * p_var[k - 1] + Q_VAR

        residual_obs = q_obs[k] - q_fcst[k]
        kalman_gain = p_pred / (p_pred + R_VAR)

        bias_est[k] = bias_pred + kalman_gain * (residual_obs - bias_pred)
        p_var[k] = (1.0 - kalman_gain) * p_pred
        q_corr[k] = q_fcst[k] + bias_est[k]

    q_corr = np.clip(q_corr, 0.0, None)

    # =========================
    # 5) KPI结果表格
    # =========================
    kpi_base = calc_metrics(q_true, q_fcst)
    kpi_corr = calc_metrics(q_true, q_corr)
    print_kpi_table(kpi_base, kpi_corr, a_est, b_est, opt.success)

    # =========================
    # 6) Matplotlib绘图
    # =========================
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(
        3, 1, figsize=(12, 9), sharex=True,
        gridspec_kw={"height_ratios": [1.1, 2.3, 1.3]}
    )

    # (a) 降雨柱状图（倒置，符合常见水文图表达）
    axes[0].bar(t, rain, width=0.9, color="#4C9BE8", alpha=0.85, label="降雨")
    axes[0].invert_yaxis()
    axes[0].set_ylabel("雨量 (mm/h)")
    axes[0].legend(loc="upper right")
    axes[0].grid(alpha=0.25)

    # (b) 流量过程线
    axes[1].plot(t, q_true, color="black", lw=2.1, label="真实流量")
    axes[1].plot(t, q_obs, color="gray", lw=1.0, alpha=0.5, label="观测流量")
    axes[1].plot(t, q_fcst, color="#D95F02", lw=1.8, label="基础预报")
    axes[1].plot(t, q_corr, color="#1B9E77", lw=2.0, label="实时校正预报")
    axes[1].set_ylabel("流量 (m³/s)")
    axes[1].set_title("第3章 洪水预报实时校正：模型预测 + 状态更新")
    axes[1].legend(ncol=2)
    axes[1].grid(alpha=0.25)

    # (c) 误差对比
    err_base = q_true - q_fcst
    err_corr = q_true - q_corr
    axes[2].plot(t, err_base, color="#D95F02", lw=1.4, label="基础误差")
    axes[2].plot(t, err_corr, color="#1B9E77", lw=1.4, label="校正后误差")
    axes[2].axhline(0, color="k", lw=0.8)
    axes[2].set_ylabel("误差 (m³/s)")
    axes[2].set_xlabel("时间 (h)")
    axes[2].legend()
    axes[2].grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig('ch03_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch03_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
