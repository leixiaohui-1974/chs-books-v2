# -*- coding: utf-8 -*-
"""
《数字孪生流域》- 第2章 多源数据融合（遥感/IoT）
2.1 基本概念与理论框架仿真脚本
功能：模拟遥感与IoT观测，完成时间对齐、质量控制、加权融合，输出KPI并绘图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy import interpolate, stats
from scipy.signal import savgol_filter

# =========================
# 1) 关键参数（统一变量化）
# =========================
RANDOM_SEED = 42            # 随机种子，保证复现
SIM_HOURS = 24 * 14         # 仿真时长（小时）
DT = 1.0                    # 时间步长（小时）

RS_INTERVAL = 6             # 遥感采样间隔（小时）
CLOUD_MISS_RATE = 0.25      # 遥感云遮导致缺测率
SIGMA_RS = 0.22             # 遥感随机噪声标准差
RS_SYSTEM_BIAS = 0.08       # 遥感系统偏差（正偏）

SIGMA_IOT = 0.10            # IoT随机噪声标准差
IOT_DRIFT_PER_HOUR = 0.0018 # IoT漂移速率
OUTLIER_RATE = 0.02         # IoT离群点比例
SMOOTH_WINDOW = 11          # IoT平滑窗口（奇数）

np.random.seed(RANDOM_SEED)

# =========================
# 2) 构造“真实状态”（数字孪生中的状态层）
# =========================
t = np.arange(0, SIM_HOURS, DT)

# 真实水位由：缓慢趋势 + 日周期 + 两次洪峰扰动 组成
base = 2.40 + 0.0025 * t
daily_cycle = 0.28 * np.sin(2 * np.pi * t / 24)
flood_event_1 = 0.85 * np.exp(-0.5 * ((t - 95) / 10) ** 2)
flood_event_2 = 0.65 * np.exp(-0.5 * ((t - 220) / 14) ** 2)
truth = base + daily_cycle + flood_event_1 + flood_event_2

# =========================
# 3) 生成IoT观测（高频、含漂移和离群）
# =========================
iot_noise = np.random.normal(0, SIGMA_IOT, size=t.size)
iot_raw = truth + IOT_DRIFT_PER_HOUR * t + iot_noise

# 注入离群点（例如传感器短时故障）
n_outlier = max(1, int(OUTLIER_RATE * t.size))
outlier_idx = np.random.choice(t.size, size=n_outlier, replace=False)
iot_raw[outlier_idx] += np.random.normal(0, 1.2, size=n_outlier)

# IoT质量控制：Z分数剔异常 + Savitzky-Golay平滑
z_score = np.abs(stats.zscore(iot_raw, nan_policy="omit"))
iot_qc = iot_raw.copy()
iot_qc[z_score > 3.0] = np.median(iot_raw)
iot_qc = savgol_filter(iot_qc, window_length=SMOOTH_WINDOW, polyorder=2, mode="interp")

# =========================
# 4) 生成遥感观测（低频、含缺测和系统偏差）
# =========================
rs_t = np.arange(0, SIM_HOURS, RS_INTERVAL, dtype=float)
rs_truth = np.interp(rs_t, t, truth)
rs_raw = rs_truth + RS_SYSTEM_BIAS + np.random.normal(0, SIGMA_RS, size=rs_t.size)

# 云遮缺测
valid_mask = np.random.rand(rs_t.size) > CLOUD_MISS_RATE
if valid_mask.sum() < 2:
    valid_mask[:2] = True  # 极端情况下保证可插值
rs_t_obs = rs_t[valid_mask]
rs_obs = rs_raw[valid_mask]

# 遥感时间对齐到小时尺度（插值）
rs_interp = interpolate.interp1d(
    rs_t_obs, rs_obs, kind="linear", bounds_error=False, fill_value="extrapolate"
)
rs_aligned = rs_interp(t)

# =========================
# 5) 融合前校正（观测层到融合层）
# =========================
# 遥感偏差校正：以IoT质控序列作为参考估计偏差
bias_rs_est = np.median(rs_aligned - iot_qc)
rs_bc = rs_aligned - bias_rs_est

# IoT漂移校正：用“(IoT - 遥感)”对时间做线性回归，去除斜率项
drift_fit = stats.linregress(t, iot_qc - rs_bc)
iot_bc = iot_qc - drift_fit.slope * t

# =========================
# 6) 不确定性加权融合（理论框架核心）
# =========================
# 遥感不确定性：离最近遥感观测越远，不确定性越大
nearest_dist = np.min(np.abs(t[:, None] - rs_t_obs[None, :]), axis=1)
sigma_rs_t = SIGMA_RS * (1.0 + nearest_dist / RS_INTERVAL)

# IoT不确定性：随时间略增长（模拟累积漂移风险）
sigma_iot_t = SIGMA_IOT * (1.0 + 0.7 * (t / SIM_HOURS))

# 权重与融合结果
w_iot = 1.0 / (sigma_iot_t ** 2)
w_rs = 1.0 / (sigma_rs_t ** 2)
w_sum = w_iot + w_rs
fused = (w_iot * iot_bc + w_rs * rs_bc) / w_sum

# =========================
# 7) KPI评价（评价层）
# =========================
def calc_metrics(y_true, y_est):
    err = y_est - y_true
    rmse = np.sqrt(np.mean(err ** 2))
    mae = np.mean(np.abs(err))
    bias = np.mean(err)
    nse = 1 - np.sum(err ** 2) / np.sum((y_true - np.mean(y_true)) ** 2)
    r = np.corrcoef(y_true, y_est)[0, 1]
    return rmse, mae, r, nse, bias

def print_kpi_table(rows):
    print("\n=== KPI结果表（与真实状态对比）===")
    print(f"{'方案':<14}{'RMSE':>10}{'MAE':>10}{'R':>10}{'NSE':>10}{'BIAS':>10}")
    print("-" * 64)
    for name, m in rows:
        print(f"{name:<14}{m[0]:>10.4f}{m[1]:>10.4f}{m[2]:>10.4f}{m[3]:>10.4f}{m[4]:>10.4f}")

m_iot_raw = calc_metrics(truth, iot_raw)
m_rs = calc_metrics(truth, rs_aligned)
m_fused = calc_metrics(truth, fused)

print_kpi_table([
    ("IoT原始", m_iot_raw),
    ("遥感插值", m_rs),
    ("融合结果", m_fused),
])

improve_vs_iot = (m_iot_raw[0] - m_fused[0]) / m_iot_raw[0] * 100
improve_vs_rs = (m_rs[0] - m_fused[0]) / m_rs[0] * 100
print(f"\n融合RMSE相对 IoT原始 改善: {improve_vs_iot:.2f}%")
print(f"融合RMSE相对 遥感插值 改善: {improve_vs_rs:.2f}%")

# =========================
# 8) 绘图展示
# =========================
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# 上图：多源观测与融合结果
axes[0].plot(t, truth, color="black", lw=2.2, label="真实状态")
axes[0].plot(t, iot_raw, color="tab:blue", alpha=0.35, lw=1.0, label="IoT原始")
axes[0].plot(t, iot_bc, color="tab:cyan", alpha=0.95, lw=1.4, label="IoT校正")
axes[0].scatter(rs_t_obs, rs_obs, color="tab:orange", s=20, label="遥感观测(含缺测)")
axes[0].plot(t, rs_bc, color="tab:red", alpha=0.8, lw=1.2, label="遥感对齐校正")
axes[0].plot(t, fused, color="tab:green", lw=2.2, label="融合结果")
axes[0].set_ylabel("水位/归一化单位")
axes[0].set_title("多源数据融合仿真：遥感 + IoT")
axes[0].grid(alpha=0.25)
axes[0].legend(loc="upper left", ncol=3, fontsize=9)

# 下图：动态权重与融合误差
axes[1].plot(t, w_iot / w_sum, color="tab:blue", lw=1.6, label="IoT权重")
axes[1].plot(t, w_rs / w_sum, color="tab:orange", lw=1.6, label="遥感权重")
axes[1].plot(t, np.abs(fused - truth), color="tab:green", lw=1.8, label="融合绝对误差")
axes[1].set_xlabel("时间 / 小时")
axes[1].set_ylabel("权重 / 误差")
axes[1].grid(alpha=0.25)
axes[1].legend(loc="upper right", fontsize=9)

plt.tight_layout()
plt.savefig('ch02_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch02_simulation_result.png")
# plt.show()  # 禁用弹窗
