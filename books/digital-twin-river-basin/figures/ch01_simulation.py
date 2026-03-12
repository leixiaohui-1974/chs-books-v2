"""
教材：《数字孪生流域》
章节：第1章 数字孪生流域总体架构（1.1 基本概念与理论框架）
功能：构建“物理流域-数字孪生模型-数据同化-KPI评估”的简化仿真闭环
依赖：numpy / scipy / matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

# =========================
# 1) 关键参数定义（可调）
# =========================
RANDOM_SEED = 42
HOURS = 240                    # 仿真总时长（小时）
DT = 1.0                       # 时间步长（小时）

# 真实流域参数（物理体）
C_RAIN_TRUE = 0.42             # 降雨转化为蓄量系数
K_OUT_TRUE = 0.085             # 出流系数
ALPHA_TRUE = 1.35              # 非线性指数
PROCESS_NOISE_STD = 1.8        # 过程噪声标准差

# 孪生模型参数（故意设定偏差，体现“模型-现实差异”）
C_RAIN_MODEL = 0.38
K_OUT_MODEL = 0.079
ALPHA_MODEL = 1.25

# 观测与同化参数（感知层 + 同步校正）
OBS_NOISE_STD = 3.0
GAIN_BASE = 0.55               # 同化增益基值
SENS_EPS = 1e-4                # 敏感度下限，避免除零
MAX_CORRECTION = 8.0           # 单步修正上限，增强稳定性

# KPI预警阈值
WARN_THRESHOLD = 55.0          # 流量阈值（m^3/s）

# =========================
# 2) 构造降雨过程（外部驱动）
# =========================
np.random.seed(RANDOM_SEED)
t = np.arange(HOURS)

rain = np.zeros(HOURS)
rain[20:60] = np.linspace(0, 18, 40)                          # 第一场雨上升段
rain[60:110] = np.linspace(18, 4, 50)                         # 第一场雨衰减段
rain[130:170] = 8 + 3 * np.sin(np.linspace(0, np.pi, 40))     # 第二场雨
rain += np.random.gamma(shape=1.2, scale=0.6, size=HOURS)     # 背景随机降雨
rain = np.clip(rain, 0, None)

# =========================
# 3) 真实流域（物理体）仿真
# =========================
S_true = np.zeros(HOURS)   # 流域蓄量
Q_true = np.zeros(HOURS)   # 真实出流
S_true[0] = 40.0

for i in range(HOURS - 1):
    Q_true[i] = K_OUT_TRUE * max(S_true[i], 0.0) ** ALPHA_TRUE
    S_next = (
        S_true[i]
        + C_RAIN_TRUE * rain[i]
        - Q_true[i] * DT
        + np.random.normal(0.0, PROCESS_NOISE_STD)
    )
    S_true[i + 1] = max(S_next, 0.0)

Q_true[-1] = K_OUT_TRUE * max(S_true[-1], 0.0) ** ALPHA_TRUE

# =========================
# 4) 观测层（传感器）仿真 + 预处理
# =========================
Q_obs_raw = Q_true + np.random.normal(0.0, OBS_NOISE_STD, size=HOURS)

# Savitzky-Golay平滑：体现“感知数据预处理”
window = 11 if HOURS >= 11 else (HOURS // 2 * 2 + 1)
Q_obs = savgol_filter(Q_obs_raw, window_length=window, polyorder=2, mode="interp")

# =========================
# 5) 开环模型（无同化）仿真
# =========================
S_open = np.zeros(HOURS)
Q_open = np.zeros(HOURS)
S_open[0] = 30.0

for i in range(HOURS - 1):
    Q_open[i] = K_OUT_MODEL * max(S_open[i], 0.0) ** ALPHA_MODEL
    S_open[i + 1] = max(S_open[i] + C_RAIN_MODEL * rain[i] - Q_open[i] * DT, 0.0)

Q_open[-1] = K_OUT_MODEL * max(S_open[-1], 0.0) ** ALPHA_MODEL

# =========================
# 6) 数字孪生（带同化）仿真
# =========================
S_twin = np.zeros(HOURS)
Q_twin = np.zeros(HOURS)
Q_prior = np.zeros(HOURS)       # 同化前预测流量
innovation = np.zeros(HOURS)    # 观测-预测残差

S_twin[0] = 30.0

for i in range(HOURS):
    # 先用当前状态做预测（先验）
    Q_prior[i] = K_OUT_MODEL * max(S_twin[i], 0.0) ** ALPHA_MODEL
    innovation[i] = Q_obs[i] - Q_prior[i]

    # 流量对蓄量的局部敏感度：dQ/dS
    sensitivity = K_OUT_MODEL * ALPHA_MODEL * max(S_twin[i], 1e-6) ** (ALPHA_MODEL - 1)

    # 自适应增益：残差越大，增益适度收缩
    gain = GAIN_BASE / (1.0 + abs(innovation[i]) / (OBS_NOISE_STD + 1e-9))

    # 由流量残差反推状态修正量（简化同化）
    correction = gain * innovation[i] / max(sensitivity, SENS_EPS)
    correction = np.clip(correction, -MAX_CORRECTION, MAX_CORRECTION)

    # 后验状态更新
    S_twin[i] = max(S_twin[i] + correction, 0.0)
    Q_twin[i] = K_OUT_MODEL * max(S_twin[i], 0.0) ** ALPHA_MODEL

    # 推进一步到下一时刻
    if i < HOURS - 1:
        S_twin[i + 1] = max(S_twin[i] + C_RAIN_MODEL * rain[i] - Q_twin[i] * DT, 0.0)

# =========================
# 7) KPI 计算
# =========================
def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def nse(y_true, y_pred):
    den = np.sum((y_true - np.mean(y_true)) ** 2)
    if den < 1e-12:
        return np.nan
    return float(1.0 - np.sum((y_true - y_pred) ** 2) / den)

rmse_open = rmse(Q_true, Q_open)
rmse_twin = rmse(Q_true, Q_twin)
nse_open = nse(Q_true, Q_open)
nse_twin = nse(Q_true, Q_twin)

peak_true = float(np.max(Q_true))
peak_twin = float(np.max(Q_twin))
peak_bias_pct = 100.0 * (peak_twin - peak_true) / max(peak_true, 1e-9)

peak_true_idx = int(np.argmax(Q_true))
peak_twin_idx = int(np.argmax(Q_twin))
peak_time_error_h = abs(peak_twin_idx - peak_true_idx) * DT

improve_rmse_pct = 100.0 * (rmse_open - rmse_twin) / max(rmse_open, 1e-9)

true_warn = Q_true >= WARN_THRESHOLD
twin_warn = Q_twin >= WARN_THRESHOLD
tp = int(np.sum(true_warn & twin_warn))
fp = int(np.sum(~true_warn & twin_warn))
fn = int(np.sum(true_warn & ~twin_warn))

precision = tp / (tp + fp + 1e-12)
recall = tp / (tp + fn + 1e-12)
f1 = 2 * precision * recall / (precision + recall + 1e-12)

# =========================
# 8) 打印KPI结果表格
# =========================
rows = [
    ("RMSE(开环)", rmse_open, "m^3/s"),
    ("RMSE(孪生同化)", rmse_twin, "m^3/s"),
    ("RMSE改进率", improve_rmse_pct, "%"),
    ("NSE(开环)", nse_open, "-"),
    ("NSE(孪生同化)", nse_twin, "-"),
    ("洪峰流量偏差", peak_bias_pct, "%"),
    ("洪峰时刻误差", peak_time_error_h, "h"),
    ("预警Precision", precision, "-"),
    ("预警Recall", recall, "-"),
    ("预警F1", f1, "-"),
]

print("=" * 72)
print(f"{'KPI指标':<22}{'数值':>18}{'单位':>12}")
print("-" * 72)
for name, value, unit in rows:
    print(f"{name:<22}{value:>18.4f}{unit:>12}")
print("=" * 72)

# =========================
# 9) 结果可视化
# =========================
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# 子图1：降雨
axes[0].bar(t, rain, color="#4C78A8", alpha=0.85, width=1.0)
axes[0].set_ylabel("降雨 (mm/h)")
axes[0].set_title("数字孪生流域：感知-模型-同化-评估仿真")
axes[0].grid(alpha=0.25)

# 子图2：流量对比
axes[1].plot(t, Q_true, label="真实流量", linewidth=2.2, color="#2E7D32")
axes[1].plot(t, Q_open, label="开环模型", linewidth=1.8, linestyle="--", color="#E07A5F")
axes[1].plot(t, Q_twin, label="孪生同化", linewidth=2.0, color="#1F77B4")
axes[1].plot(t, Q_obs, label="观测(平滑后)", linewidth=1.2, alpha=0.7, color="#7F7F7F")
axes[1].axhline(WARN_THRESHOLD, color="red", linestyle=":", linewidth=1.2, label="预警阈值")
axes[1].set_ylabel("流量 (m^3/s)")
axes[1].legend(loc="upper right", ncol=3, fontsize=9)
axes[1].grid(alpha=0.25)

# 子图3：误差演化
err_open = np.abs(Q_open - Q_true)
err_twin = np.abs(Q_twin - Q_true)
axes[2].plot(t, err_open, label="|开环误差|", linestyle="--", color="#E07A5F")
axes[2].plot(t, err_twin, label="|孪生误差|", color="#1F77B4")
axes[2].set_xlabel("时间 (h)")
axes[2].set_ylabel("绝对误差 (m^3/s)")
axes[2].legend(loc="upper right")
axes[2].grid(alpha=0.25)

plt.tight_layout()
plt.savefig('ch01_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch01_simulation_result.png")
# plt.show()  # 禁用弹窗
