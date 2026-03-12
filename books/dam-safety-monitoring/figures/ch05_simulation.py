# -*- coding: utf-8 -*-
"""
教材：《大坝安全监测与预警》
章节：第5章 机器学习异常检测（5.1 基本概念与理论框架）
功能：构建大坝监测多变量仿真数据，注入异常，并用“健康机理回归 + 马氏距离 + 统计阈值”完成异常检测、KPI评估与可视化。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy.stats import chi2
from scipy.signal import savgol_filter
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# ========================= 1) 关键参数定义 =========================
RANDOM_SEED = 2026
N_TOTAL = 1200                    # 总监测点数
TRAIN_RATIO = 0.50               # 前50%作为健康训练段
THRESHOLD_CONFIDENCE = 0.997     # 卡方阈值置信度
EWMA_ALPHA = 0.22                # 分数平滑系数
COV_REG = 1e-6                   # 协方差正则项，防止奇异

# 异常注入参数
ANOMALY_SPIKE_COUNT = 18         # 突刺异常数量
DRIFT_START, DRIFT_END = 820, 980
DRIFT_MAGNITUDE = 2.2
REL_BREAK_START, REL_BREAK_END = 1020, 1120

# 输出参数
SAVE_FIGURE = True
SHOW_FIGURE = True
FIG_PATH = "chapter5_1_anomaly_detection.png"

np.random.seed(RANDOM_SEED)

# ========================= 2) 仿真数据生成 =========================
t = np.arange(N_TOTAL)

# 工况因子：库水位、温度（季节性 + 噪声）
water_level = 100 + 7 * np.sin(2 * np.pi * t / 240) + 0.7 * np.random.randn(N_TOTAL)
temperature = 15 + 10 * np.sin(2 * np.pi * (t + 40) / 365) + 0.9 * np.random.randn(N_TOTAL)

# 响应量：渗流、位移、扬压力（受工况驱动）
seepage = 8.0 + 0.11 * water_level + 0.05 * temperature + 0.002 * (water_level - 100) ** 2 + 0.35 * np.random.randn(N_TOTAL)
displacement = 2.5 + 0.08 * water_level + 0.02 * temperature + 0.0009 * t + 0.28 * np.random.randn(N_TOTAL)
uplift_pressure = 5.0 + 0.09 * water_level + 0.01 * temperature + 0.25 * np.random.randn(N_TOTAL)

# 轻度平滑，模拟工程中常见滤波预处理
seepage = savgol_filter(seepage, 11, 2)
displacement = savgol_filter(displacement, 11, 2)
uplift_pressure = savgol_filter(uplift_pressure, 11, 2)

# ========================= 3) 注入异常并构造标签 =========================
y_true = np.zeros(N_TOTAL, dtype=int)
train_end = int(N_TOTAL * TRAIN_RATIO)

# 3.1 突刺异常（随机瞬时扰动）
spike_idx = np.random.choice(np.arange(train_end, N_TOTAL), size=ANOMALY_SPIKE_COUNT, replace=False)
spike_amp = np.random.choice([3.5, -3.2, 4.0, -3.8], size=ANOMALY_SPIKE_COUNT)
seepage[spike_idx] += spike_amp
uplift_pressure[spike_idx] += 0.8 * spike_amp
y_true[spike_idx] = 1

# 3.2 漂移异常（慢性偏移）
drift = np.linspace(0, DRIFT_MAGNITUDE, DRIFT_END - DRIFT_START)
seepage[DRIFT_START:DRIFT_END] += drift
y_true[DRIFT_START:DRIFT_END] = 1

# 3.3 机理关系失配异常（结构状态变化）
displacement[REL_BREAK_START:REL_BREAK_END] += 1.7 + 0.06 * (
    water_level[REL_BREAK_START:REL_BREAK_END] - np.mean(water_level)
)
y_true[REL_BREAK_START:REL_BREAK_END] = 1

# ========================= 4) 健康机理建模（回归基线） =========================
# 以健康段拟合“工况->响应”的线性机理模型
X_train = np.column_stack([
    np.ones(train_end),
    water_level[:train_end],
    temperature[:train_end],
    t[:train_end]
])
X_all = np.column_stack([
    np.ones(N_TOTAL),
    water_level,
    temperature,
    t
])

beta_seep = np.linalg.lstsq(X_train, seepage[:train_end], rcond=None)[0]
beta_disp = np.linalg.lstsq(X_train, displacement[:train_end], rcond=None)[0]
beta_uplift = np.linalg.lstsq(X_train, uplift_pressure[:train_end], rcond=None)[0]

pred_seep = X_all @ beta_seep
pred_disp = X_all @ beta_disp
pred_uplift = X_all @ beta_uplift

# 残差特征：偏离机理模型的程度
residuals = np.column_stack([
    seepage - pred_seep,
    displacement - pred_disp,
    uplift_pressure - pred_uplift
])

# ========================= 5) 异常分数与告警判决 =========================
# 用健康段残差统计量构造马氏距离分数
mu = residuals[:train_end].mean(axis=0)
cov = np.cov(residuals[:train_end].T) + COV_REG * np.eye(residuals.shape[1])
cov_inv = np.linalg.pinv(cov)

diff = residuals - mu
score = np.einsum("ij,jk,ik->i", diff, cov_inv, diff)

# EWMA平滑，降低噪声引起的误报
score_smooth = np.zeros_like(score)
score_smooth[0] = score[0]
for i in range(1, N_TOTAL):
    score_smooth[i] = EWMA_ALPHA * score[i] + (1 - EWMA_ALPHA) * score_smooth[i - 1]

# 卡方阈值（自由度=残差维度）
dof = residuals.shape[1]
threshold = chi2.ppf(THRESHOLD_CONFIDENCE, df=dof)
y_pred = (score_smooth > threshold).astype(int)

# ========================= 6) KPI计算与表格输出 =========================
def safe_div(a, b):
    return a / b if b != 0 else 0.0

def get_segments(binary_arr):
    """返回连续异常段列表[(start, end), ...]"""
    segs, start = [], None
    for i, v in enumerate(binary_arr):
        if v == 1 and start is None:
            start = i
        if v == 0 and start is not None:
            segs.append((start, i - 1))
            start = None
    if start is not None:
        segs.append((start, len(binary_arr) - 1))
    return segs

TP = int(np.sum((y_true == 1) & (y_pred == 1)))
FP = int(np.sum((y_true == 0) & (y_pred == 1)))
FN = int(np.sum((y_true == 1) & (y_pred == 0)))
TN = int(np.sum((y_true == 0) & (y_pred == 0)))

precision = safe_div(TP, TP + FP)
recall = safe_div(TP, TP + FN)
f1 = safe_div(2 * precision * recall, precision + recall)
accuracy = safe_div(TP + TN, TP + TN + FP + FN)
far = safe_div(FP, FP + TN)          # 误报率
miss_rate = safe_div(FN, FN + TP)    # 漏报率

segments = get_segments(y_true)
delays = []
for s, e in segments:
    idx = np.where(y_pred[s:e + 1] == 1)[0]
    if idx.size > 0:
        delays.append(int(idx[0]))    # 相对段起点延迟
avg_delay = float(np.mean(delays)) if delays else np.nan
event_recall = safe_div(len(delays), len(segments))

kpi_rows = [
    ("TP", TP),
    ("FP", FP),
    ("FN", FN),
    ("TN", TN),
    ("Precision", f"{precision:.4f}"),
    ("Recall", f"{recall:.4f}"),
    ("F1-Score", f"{f1:.4f}"),
    ("Accuracy", f"{accuracy:.4f}"),
    ("False Alarm Rate", f"{far:.4f}"),
    ("Miss Rate", f"{miss_rate:.4f}"),
    ("Event Recall", f"{event_recall:.4f}"),
    ("Avg Detection Delay", f"{avg_delay:.2f}"),
]

print("\n=== 大坝安全监测异常检测 KPI结果表 ===")
print("+----------------------+----------------+")
print("| 指标                 | 数值           |")
print("+----------------------+----------------+")
for k, v in kpi_rows:
    print(f"| {k:<20} | {str(v):<14} |")
print("+----------------------+----------------+")

# ========================= 7) Matplotlib可视化 =========================
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# 子图1：监测响应与真实异常
axes[0].plot(t, seepage, label="渗流量", lw=1.2)
axes[0].plot(t, displacement, label="位移", lw=1.2)
axes[0].plot(t, uplift_pressure, label="扬压力", lw=1.2)
axes[0].set_ylabel("响应值")
axes[0].set_title("大坝监测时序（仿真）与异常区间")
for s, e in segments:
    axes[0].axvspan(s, e, color="tomato", alpha=0.12)
axes[0].legend(loc="upper left", ncol=3)

# 子图2：异常分数与阈值
axes[1].plot(t, score, label="马氏距离(原始)", alpha=0.45)
axes[1].plot(t, score_smooth, label="马氏距离(EWMA)", lw=1.8)
axes[1].axhline(threshold, color="r", ls="--", lw=1.4, label=f"阈值={threshold:.2f}")
axes[1].set_ylabel("异常分数")
axes[1].legend(loc="upper left")

# 子图3：真实标签 vs 模型告警
axes[2].step(t, y_true, where="post", label="真实异常", lw=1.6)
axes[2].step(t, y_pred, where="post", label="模型告警", lw=1.2)
axes[2].set_ylabel("0/1")
axes[2].set_xlabel("时间步")
axes[2].set_ylim(-0.1, 1.2)
axes[2].legend(loc="upper left")

plt.tight_layout()
if SAVE_FIGURE:
    plt.savefig(FIG_PATH, dpi=150)
if SHOW_FIGURE:
    # plt.show()  # 禁用弹窗
plt.close(fig)
