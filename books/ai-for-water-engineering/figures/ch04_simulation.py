# -*- coding: utf-8 -*-
"""
《人工智能与水利水电工程》 第4章
功能：演示“降雨-入库流量预测 + 水库防洪调度优化”一体化仿真，
输出KPI结果表，并绘制关键过程线。
依赖：numpy, scipy, matplotlib
"""

import numpy as np
from scipy import optimize
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1. 关键参数定义（可调）
# =========================
RANDOM_SEED = 42
N_STEPS = 7 * 24              # 仿真时长：7天，1小时步长
DT_HOUR = 1.0
DT_SEC = DT_HOUR * 3600.0

# 水库与运行边界参数
S_INIT = 2.20e8               # 初始库容 m3
S_REF = 2.20e8                # 参考库容 m3
S_MIN = 1.85e8                # 最小允许库容 m3
S_MAX = 2.55e8                # 最大允许库容 m3
H0 = 118.0                    # 参考水位 m
LEVEL_COEF = 1.8e-7           # 库容-水位线性系数 m/m3
H_TARGET = 120.0              # 目标运行水位 m
H_LIMIT = 122.5               # 防洪限制水位 m

R_MIN = 80.0                  # 最小出库 m3/s
R_MAX = 1400.0                # 最大出库 m3/s

# 预测模型参数
LAG_RAIN = 8
LAG_Q = 2
RIDGE_LAMBDA = 15.0
OBS_NOISE_STD = 45.0
KALMAN_A = 0.88
KALMAN_Q_VAR = 120.0
KALMAN_R_VAR = 350.0

# 目标函数权重
W_RELEASE = 1.0e-4
W_LEVEL = 8.0
W_SMOOTH = 6.0e-4
W_EXCEED_H = 4000.0
W_EXCEED_S = 1.0e-12

# 产流参数
BASEFLOW = 120.0
RUNOFF_COEF = 115.0
UH_LEN = 30

np.random.seed(RANDOM_SEED)

# =========================
# 2. 构造降雨与真实入流
# =========================
t = np.arange(N_STEPS)

# 双峰降雨（mm/h）
rain = (
    2.0
    + 22.0 * np.exp(-0.5 * ((t - 42.0) / 8.0) ** 2)
    + 17.0 * np.exp(-0.5 * ((t - 96.0) / 10.0) ** 2)
)
rain += np.clip(np.random.normal(0.0, 1.4, N_STEPS), -2.0, 2.0)
rain = np.maximum(rain, 0.0)

# 简化单位线
uh_t = np.arange(UH_LEN)
uh = (uh_t / 6.0) ** 2 * np.exp(-uh_t / 6.0)
uh = uh / (uh.sum() + 1e-12)

# 真实入流（m3/s）
qin_true = BASEFLOW + RUNOFF_COEF * np.convolve(rain, uh, mode="full")[:N_STEPS]
qin_true = np.maximum(qin_true, 0.0)

# 含噪观测入流（m3/s）
qin_obs = np.maximum(qin_true + np.random.normal(0.0, OBS_NOISE_STD, N_STEPS), 0.0)

# =========================
# 3. 岭回归预测 + 卡尔曼融合
# =========================
def build_features(rain_series, q_hist, q_target, lag_rain, lag_q):
    """构建时滞特征矩阵"""
    max_lag = max(lag_rain, lag_q)
    X, y = [], []
    for i in range(max_lag, len(rain_series)):
        feats = [rain_series[i - j] for j in range(lag_rain)]
        feats += [q_hist[i - j - 1] for j in range(lag_q)]
        X.append(feats)
        y.append(q_target[i])
    return np.array(X), np.array(y), max_lag

X, y, max_lag = build_features(rain, qin_obs, qin_true, LAG_RAIN, LAG_Q)

# 训练/验证切分
split = int(0.70 * len(X))
X_train, y_train = X[:split], y[:split]
I = np.eye(X_train.shape[1])

# 岭回归闭式解
w = np.linalg.solve(X_train.T @ X_train + RIDGE_LAMBDA * I, X_train.T @ y_train)

# 全时段预测
q_model = np.zeros(N_STEPS)
q_model[:max_lag] = qin_obs[:max_lag]
q_model[max_lag:] = np.maximum(X @ w, 0.0)

def kalman_fusion(model_pred, obs, a, q_var, r_var):
    """一维卡尔曼同化：融合模型预测与观测"""
    n = len(model_pred)
    x = np.zeros(n)
    P = np.zeros(n)
    x[0] = obs[0]
    P[0] = 1.0
    for k in range(1, n):
        x_prior = a * x[k - 1] + (1.0 - a) * model_pred[k]
        P_prior = a * a * P[k - 1] + q_var
        K = P_prior / (P_prior + r_var)
        x[k] = x_prior + K * (obs[k] - x_prior)
        P[k] = (1.0 - K) * P_prior
    return np.maximum(x, 0.0)

qin_est = kalman_fusion(q_model, qin_obs, KALMAN_A, KALMAN_Q_VAR, KALMAN_R_VAR)

# =========================
# 4. 调度优化
# =========================
def simulate_storage_level(qin, qout, s0, dt_sec):
    """按水量平衡推进库容与水位"""
    n = len(qin)
    S = np.zeros(n + 1)
    H = np.zeros(n + 1)
    S[0] = s0
    H[0] = H0 + LEVEL_COEF * (S[0] - S_REF)
    for k in range(n):
        S[k + 1] = S[k] + (qin[k] - qout[k]) * dt_sec
        H[k + 1] = H0 + LEVEL_COEF * (S[k + 1] - S_REF)
    return S, H

def objective(qout, qin_forecast):
    """综合目标：削峰、控水位、平滑闸门，并惩罚超限"""
    S, H = simulate_storage_level(qin_forecast, qout, S_INIT, DT_SEC)
    dq = np.diff(qout, prepend=qout[0])

    j_release = W_RELEASE * np.sum(qout ** 2)
    j_level = W_LEVEL * np.sum((H[1:] - H_TARGET) ** 2)
    j_smooth = W_SMOOTH * np.sum(dq ** 2)

    pen_h = W_EXCEED_H * np.sum(np.maximum(0.0, H[1:] - H_LIMIT) ** 2)
    pen_s_low = W_EXCEED_S * np.sum(np.maximum(0.0, S_MIN - S[1:]) ** 2)
    pen_s_high = W_EXCEED_S * np.sum(np.maximum(0.0, S[1:] - S_MAX) ** 2)

    return j_release + j_level + j_smooth + pen_h + pen_s_low + pen_s_high

qout0 = np.clip(np.full(N_STEPS, np.mean(qin_est)), R_MIN, R_MAX)
bounds = [(R_MIN, R_MAX)] * N_STEPS

res = optimize.minimize(
    objective,
    qout0,
    args=(qin_est,),
    method="L-BFGS-B",
    bounds=bounds,
    options={"maxiter": 500, "ftol": 1e-9}
)

qout_opt = np.clip(res.x, R_MIN, R_MAX)

# 用真实入流评估调度结果
S_true, H_true = simulate_storage_level(qin_true, qout_opt, S_INIT, DT_SEC)

# =========================
# 5. KPI评估与表格打印
# =========================
def nse(y_true, y_sim):
    den = np.sum((y_true - np.mean(y_true)) ** 2)
    if den < 1e-12:
        return np.nan
    return 1.0 - np.sum((y_true - y_sim) ** 2) / den

rmse = np.sqrt(np.mean((qin_true - qin_est) ** 2))
nse_val = nse(qin_true, qin_est)
peak_clip_rate = (np.max(qin_true) - np.max(qout_opt)) / np.max(qin_true) * 100.0
max_level = np.max(H_true[1:])
hours_over_limit = np.sum(H_true[1:] > H_LIMIT)
storage_violation_hours = np.sum((S_true[1:] < S_MIN) | (S_true[1:] > S_MAX))
mean_release = np.mean(qout_opt)

kpis = [
    ("入流预测NSE", nse_val, "-"),
    ("入流预测RMSE", rmse, "m3/s"),
    ("峰值削减率", peak_clip_rate, "%"),
    ("最高库水位", max_level, "m"),
    ("超限时长", float(hours_over_limit), "h"),
    ("库容越界时长", float(storage_violation_hours), "h"),
    ("平均出库流量", mean_release, "m3/s"),
    ("优化是否收敛", 1.0 if res.success else 0.0, "1=是"),
]

print("\n" + "=" * 68)
print("KPI结果表（第4章：洪水预报与智能调度仿真）")
print("=" * 68)
print(f"{'指标':<22}{'数值':>18}{'单位':>12}")
print("-" * 68)
for name, value, unit in kpis:
    print(f"{name:<22}{value:>18.4f}{unit:>12}")
print("=" * 68)

# =========================
# 6. 绘图
# =========================
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

fig = plt.figure(figsize=(12, 10))

# 图1：降雨与入流
ax1 = plt.subplot(3, 1, 1)
ax1.bar(t, rain, color="#6baed6", alpha=0.65, label="降雨")
ax1.set_ylabel("降雨 (mm/h)")
ax1.set_xlim(0, N_STEPS - 1)
ax1.grid(alpha=0.25)

ax1b = ax1.twinx()
ax1b.plot(t, qin_true, color="#111111", lw=1.8, label="真实入流")
ax1b.plot(t, qin_est, color="#e34a33", lw=1.6, ls="--", label="融合估计入流")
ax1b.set_ylabel("入流 (m3/s)")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1b.get_legend_handles_labels()
ax1b.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
ax1.set_title("第4章仿真：降雨-入流预测与水库调度")

# 图2：入流与优化出库
ax2 = plt.subplot(3, 1, 2)
ax2.plot(t, qin_true, color="#2c7fb8", lw=1.7, label="真实入流")
ax2.plot(t, qout_opt, color="#f16913", lw=1.8, label="优化出库")
ax2.set_ylabel("流量 (m3/s)")
ax2.grid(alpha=0.25)
ax2.legend(loc="upper right")

# 图3：库水位过程
ax3 = plt.subplot(3, 1, 3)
ax3.plot(t, H_true[1:], color="#238b45", lw=1.8, label="库水位")
ax3.axhline(H_TARGET, color="#756bb1", ls="--", lw=1.2, label="目标水位")
ax3.axhline(H_LIMIT, color="#cb181d", ls="--", lw=1.2, label="限制水位")
ax3.set_ylabel("水位 (m)")
ax3.set_xlabel("时段 (h)")
ax3.grid(alpha=0.25)
ax3.legend(loc="upper right")

plt.tight_layout()
plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗
