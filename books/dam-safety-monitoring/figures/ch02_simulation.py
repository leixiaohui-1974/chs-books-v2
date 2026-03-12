# -*- coding: utf-8 -*-
"""
书名：《大坝安全监测与智能预警》
章节：第2章 渗流渗压监测与分析（2.1 基本概念与理论框架）
功能：基于达西定律+监测响应模型，完成渗压时序仿真、参数辨识、KPI评估与预警可视化
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy import signal, optimize, stats
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（统一变量定义）
# =========================
RANDOM_SEED = 42
N_DAYS = 240                 # 仿真总天数
TRAIN_DAYS = 130             # 标定期长度

DAM_LENGTH = 60.0            # 断面长度(m)
SENSOR_POS = np.array([6, 18, 35, 52], dtype=float)   # 测压管位置(m)
SENSOR_NAME = ["P1", "P2", "P3", "P4"]

H_DOWN = 92.0                # 下游特征水位(m)
AREA = 45.0                  # 有效过流面积(m^2)
K_TRUE = 2.4e-6              # 合成真实渗透系数(m/s)

INF_TAU = 8.0                # 降雨入渗记忆时间常数(天)
NOISE_STD = 0.06             # 渗压观测噪声(m)
FLOW_NOISE_STD = 5e-6        # 渗流观测噪声(m/s)

Z_THRESH = 2.5               # 残差Z分数阈值
CONSECUTIVE_DAYS = 3         # 连续超阈值天数
GRADIENT_THRESH = 0.22       # 坡降阈值(m/m)

PLOT_SAVE_PATH = "dam_seepage_sim.png"

np.random.seed(RANDOM_SEED)
days = np.arange(N_DAYS)

# =========================
# 2) 构造外部驱动（库水位、降雨）
# =========================
h_up = (
    100.0
    + 2.6 * np.sin(2 * np.pi * days / 120)
    + 0.7 * np.sin(2 * np.pi * days / 27)
)
# 两次洪峰过程
h_up += 2.8 * np.exp(-0.5 * ((days - 85) / 7) ** 2)
h_up += 2.1 * np.exp(-0.5 * ((days - 170) / 10) ** 2)

rain = np.random.gamma(shape=1.2, scale=4.0, size=N_DAYS)  # mm/day
rain[78:84] += np.array([12, 20, 35, 28, 16, 10])
rain[160:166] += np.array([8, 18, 30, 24, 14, 9])

# =========================
# 3) 理论框架：线性水头 + 入渗记忆
# =========================
# 线性水头分布 h(x,t)=H_up-(H_up-H_down)*x/L
head_linear = h_up[None, :] - (h_up - H_DOWN)[None, :] * (SENSOR_POS[:, None] / DAM_LENGTH)

# 指数核卷积模拟入渗“滞后+衰减”
kernel_t = np.arange(0, 35)
kernel = np.exp(-kernel_t / INF_TAU)
kernel /= kernel.sum()
infiltration = signal.fftconvolve(rain, kernel, mode="full")[:N_DAYS]

# 设定“真实”测点响应参数（用于生成合成监测值）
a_true = np.array([0.96, 0.90, 0.86, 0.80])        # 对库水位敏感度
b_true = np.array([0.018, 0.022, 0.026, 0.030])    # 对入渗敏感度
c_true = np.array([0.45, 0.35, 0.20, 0.10])        # 偏置项
lag_true = np.array([1, 2, 3, 4])                  # 入渗滞后(天)

u_true = np.zeros((len(SENSOR_POS), N_DAYS))
for i in range(len(SENSOR_POS)):
    infil_shift = np.roll(infiltration, lag_true[i])
    infil_shift[:lag_true[i]] = infiltration[0]
    u_true[i] = a_true[i] * head_linear[i] + b_true[i] * infil_shift + c_true[i]

# 注入异常：150~180天下游测点抬升（模拟局部渗透通道）
anomaly_mask = (days >= 150) & (days <= 180)
u_true[2, anomaly_mask] += 0.45
u_true[3, anomaly_mask] += 0.70

# 观测值 = 真值 + 噪声
u_obs = u_true + np.random.normal(0, NOISE_STD, size=u_true.shape)

# =========================
# 4) 参数辨识（curve_fit）
# =========================
def response_model(xdata, a, b, c):
    head_x, infil_x = xdata
    return a * head_x + b * infil_x + c

u_pred = np.zeros_like(u_obs)
fit_param = []

for i in range(len(SENSOR_POS)):
    infil_shift = np.roll(infiltration, lag_true[i])
    infil_shift[:lag_true[i]] = infiltration[0]

    x_train = (head_linear[i, :TRAIN_DAYS], infil_shift[:TRAIN_DAYS])
    y_train = u_obs[i, :TRAIN_DAYS]

    popt, _ = optimize.curve_fit(
        response_model,
        x_train,
        y_train,
        p0=[0.9, 0.02, 0.2],
        bounds=([0.0, 0.0, -10.0], [2.0, 1.0, 10.0]),
        maxfev=20000,
    )
    fit_param.append(popt)

    u_pred[i] = response_model((head_linear[i], infil_shift), *popt)

fit_param = np.array(fit_param)  # 列: a,b,c

# =========================
# 5) 反演渗透系数K（达西定律）
# =========================
grad_true = (u_true[0] - u_true[-1]) / (SENSOR_POS[-1] - SENSOR_POS[0])  # i
q_obs = K_TRUE * AREA * grad_true + np.random.normal(0, FLOW_NOISE_STD, size=N_DAYS)

reg = stats.linregress(grad_true, q_obs / AREA)
K_EST = reg.slope
K_R2 = reg.rvalue ** 2

# =========================
# 6) 预警判别
# =========================
focus = 3  # P4
residual = u_obs[focus] - u_pred[focus]
z = (residual - residual.mean()) / (residual.std(ddof=1) + 1e-12)

raw_alarm = np.abs(z) > Z_THRESH
count = np.convolve(raw_alarm.astype(int), np.ones(CONSECUTIVE_DAYS, dtype=int), mode="same")
alarm = count >= CONSECUTIVE_DAYS

grad_pred = (u_pred[0] - u_pred[-1]) / (SENSOR_POS[-1] - SENSOR_POS[0])
grad_alarm = np.abs(grad_pred) > GRADIENT_THRESH

# =========================
# 7) KPI表格打印
# =========================
def calc_metrics(y, yhat):
    err = y - yhat
    rmse = np.sqrt(np.mean(err ** 2))
    mae = np.mean(np.abs(err))
    ss_res = np.sum(err ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2) + 1e-12
    r2 = 1 - ss_res / ss_tot
    nse = 1 - ss_res / ss_tot
    return rmse, mae, r2, nse

tp = np.sum(alarm & anomaly_mask)
fp = np.sum(alarm & (~anomaly_mask))
fn = np.sum((~alarm) & anomaly_mask)
precision = tp / (tp + fp + 1e-12)
recall = tp / (tp + fn + 1e-12)

print("\n=== 渗压模型KPI结果表 ===")
print(f"{'测点':<6}{'RMSE(m)':>10}{'MAE(m)':>10}{'R2':>10}{'NSE':>10}{'a(拟合)':>12}{'b(拟合)':>12}")
for i, name in enumerate(SENSOR_NAME):
    rmse, mae, r2, nse = calc_metrics(u_obs[i], u_pred[i])
    print(f"{name:<6}{rmse:>10.4f}{mae:>10.4f}{r2:>10.4f}{nse:>10.4f}{fit_param[i,0]:>12.4f}{fit_param[i,1]:>12.4f}")

print("\n=== 预警与参数反演KPI ===")
print(f"K_true = {K_TRUE:.3e} m/s")
print(f"K_est  = {K_EST:.3e} m/s, 回归R2 = {K_R2:.4f}")
print(f"残差预警: Precision = {precision:.4f}, Recall = {recall:.4f}, 报警天数 = {alarm.sum()}")
print(f"坡降阈值: |i| > {GRADIENT_THRESH:.3f}, 超阈值天数 = {grad_alarm.sum()}")

# =========================
# 8) matplotlib绘图
# =========================
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)

# 图1：驱动与拟合
ax = axes[0]
ax2 = ax.twinx()
ax.plot(days, h_up, color="tab:blue", lw=1.8, label="上游水位 H_up")
ax2.bar(days, rain, color="tab:gray", alpha=0.25, width=1.0, label="降雨")
ax.plot(days, u_obs[focus], color="tab:red", lw=1.2, alpha=0.85, label="P4观测渗压")
ax.plot(days, u_pred[focus], color="tab:green", lw=1.8, label="P4模型渗压")
ax.set_ylabel("水位/水头(m)")
ax2.set_ylabel("降雨(mm/day)")
ax.set_title("渗压监测仿真：驱动项与模型拟合(P4)")
for t in [150, 180]:
    ax.axvline(t, color="k", ls="--", lw=0.8, alpha=0.5)
l1, n1 = ax.get_legend_handles_labels()
l2, n2 = ax2.get_legend_handles_labels()
ax.legend(l1 + l2, n1 + n2, loc="upper left", ncol=2, fontsize=9)

# 图2：残差统计预警
ax = axes[1]
ax.plot(days, z, color="tab:purple", lw=1.5, label="P4残差Z分数")
ax.axhline(Z_THRESH, color="tab:red", ls="--", lw=1.0, label="Z阈值")
ax.axhline(-Z_THRESH, color="tab:red", ls="--", lw=1.0)
ax.fill_between(days, -4, 4, where=anomaly_mask, color="orange", alpha=0.20, label="真实异常区间")
ax.scatter(days[alarm], z[alarm], color="red", s=18, label="报警点")
ax.set_ylabel("Z-score")
ax.set_ylim(-4, 4)
ax.set_title("异常识别：残差统计预警")
ax.legend(loc="upper left", ncol=2, fontsize=9)

# 图3：坡降阈值判别
ax = axes[2]
ax.plot(days, grad_pred, color="tab:brown", lw=1.6, label="预测渗透坡降 i")
ax.axhline(GRADIENT_THRESH, color="tab:red", ls="--", lw=1.0, label="坡降阈值")
ax.axhline(-GRADIENT_THRESH, color="tab:red", ls="--", lw=1.0)
ax.scatter(days[grad_alarm], grad_pred[grad_alarm], color="tab:red", s=16, label="坡降超阈值")
ax.fill_between(days, -0.4, 0.4, where=anomaly_mask, color="orange", alpha=0.18)
ax.set_ylabel("i(m/m)")
ax.set_xlabel("时间(day)")
ax.set_title("断面渗透坡降与阈值判别")
ax.legend(loc="upper left", ncol=2, fontsize=9)

plt.tight_layout()
plt.savefig(PLOT_SAVE_PATH, dpi=150)
# plt.show()  # 禁用弹窗
