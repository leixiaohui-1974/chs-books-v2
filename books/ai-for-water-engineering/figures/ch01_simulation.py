# -*- coding: utf-8 -*-
"""
教材：《人工智能与水利水电工程》
章节：第1章 AI全景：从机器学习到大模型（1.1 基本概念与理论框架）
功能：以“来水量预测”仿真为例，对比线性模型、非线性特征模型与大模型代理模型的性能差异
"""

import time
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy import optimize, linalg

# =========================
# 1) 关键参数（统一变量定义，便于教学调参）
# =========================
RANDOM_SEED = 42
N_SAMPLES = 720
TRAIN_RATIO = 0.70
VAL_RATIO_IN_TRAIN = 0.20
NOISE_STD = 2.2
N_RANDOM_FEATURES = 180
LAMBDA_BOUNDS = (1e-4, 100.0)

# =========================
# 2) 构造“水文-气象”仿真数据
# =========================
np.random.seed(RANDOM_SEED)
t = np.arange(N_SAMPLES, dtype=float)

# 降雨：月尺度和周尺度周期 + 随机扰动
rain = (
    18
    + 6 * np.sin(2 * np.pi * t / 30)
    + 2 * np.cos(2 * np.pi * t / 7)
    + np.random.normal(0, 1.8, size=N_SAMPLES)
)
rain = np.clip(rain, 0, None)

# 真实来水量：线性项 + 非线性项 + 周期项 + 趋势项 + 噪声
inflow = (
    45
    + 0.75 * rain
    + 0.018 * t
    + 7.5 * np.sin(2 * np.pi * t / 30)
    + 2.8 * np.cos(2 * np.pi * t / 7)
    + 0.012 * rain**2
    + np.random.normal(0, NOISE_STD, size=N_SAMPLES)
)

X_raw = np.column_stack([t, rain])
y = inflow

# =========================
# 3) 按时间顺序划分训练/测试集（符合工程预测场景）
# =========================
split_idx = int(N_SAMPLES * TRAIN_RATIO)
X_train_raw, X_test_raw = X_raw[:split_idx], X_raw[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]
t_test = t[split_idx:]

# =========================
# 4) 模型构造函数
# =========================
def design_linear(X):
    """线性特征：常数项 + 时间 + 降雨"""
    tt = X[:, 0]
    rr = X[:, 1]
    return np.column_stack([np.ones(len(X)), tt, rr])

def design_nonlinear(X):
    """非线性特征：加入二次项与周期项"""
    tt = X[:, 0]
    rr = X[:, 1]
    return np.column_stack([
        np.ones(len(X)),
        tt, rr,
        tt**2, rr**2,
        np.sin(2 * np.pi * tt / 30),
        np.cos(2 * np.pi * tt / 7),
        np.sin(2 * np.pi * tt / 90),
    ])

def make_random_features(X, W, b):
    """大模型代理：随机映射到高维特征空间"""
    return np.cos(X @ W + b)

def calc_metrics(y_true, y_pred):
    """计算 KPI：RMSE、MAE、R2"""
    err = y_true - y_pred
    rmse = np.sqrt(np.mean(err**2))
    mae = np.mean(np.abs(err))
    ss_res = np.sum(err**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    r2 = 1 - ss_res / ss_tot
    return rmse, mae, r2

results = []
pred_dict = {}

# =========================
# 5) 模型A：线性模型（机器学习基础）
# =========================
start = time.perf_counter()
Phi_tr = design_linear(X_train_raw)
Phi_te = design_linear(X_test_raw)
w_lin, *_ = linalg.lstsq(Phi_tr, y_train)
yhat_lin = Phi_te @ w_lin
cost_lin = time.perf_counter() - start

rmse, mae, r2 = calc_metrics(y_test, yhat_lin)
results.append(("线性模型", rmse, mae, r2, cost_lin, len(w_lin)))
pred_dict["线性模型"] = yhat_lin

# =========================
# 6) 模型B：非线性特征模型（特征工程）
# =========================
start = time.perf_counter()
Phi_tr2 = design_nonlinear(X_train_raw)
Phi_te2 = design_nonlinear(X_test_raw)
w_nonlin, *_ = linalg.lstsq(Phi_tr2, y_train)
yhat_nonlin = Phi_te2 @ w_nonlin
cost_nonlin = time.perf_counter() - start

rmse, mae, r2 = calc_metrics(y_test, yhat_nonlin)
results.append(("非线性特征模型", rmse, mae, r2, cost_nonlin, len(w_nonlin)))
pred_dict["非线性特征模型"] = yhat_nonlin

# =========================
# 7) 模型C：大模型代理（随机特征 + Ridge + 调参）
# =========================
start = time.perf_counter()

rng = np.random.default_rng(RANDOM_SEED)
W = rng.normal(0, 0.03, size=(X_train_raw.shape[1], N_RANDOM_FEATURES))
b = rng.uniform(0, 2 * np.pi, size=(N_RANDOM_FEATURES,))

Z_all = make_random_features(X_train_raw, W, b)
Z_test = make_random_features(X_test_raw, W, b)

n_train = len(Z_all)
n_val = int(n_train * VAL_RATIO_IN_TRAIN)
n_subtr = n_train - n_val

Z_subtr, Z_val = Z_all[:n_subtr], Z_all[n_subtr:]
y_subtr, y_val = y_train[:n_subtr], y_train[n_subtr:]

# 用 scipy.optimize 在对数空间搜索最优正则系数
def val_rmse(log10_lambda):
    lam = 10 ** log10_lambda
    A = Z_subtr.T @ Z_subtr + lam * np.eye(Z_subtr.shape[1])
    b_vec = Z_subtr.T @ y_subtr
    w = linalg.solve(A, b_vec, assume_a='pos')
    y_val_pred = Z_val @ w
    return np.sqrt(np.mean((y_val - y_val_pred) ** 2))

opt = optimize.minimize_scalar(
    val_rmse,
    bounds=(np.log10(LAMBDA_BOUNDS[0]), np.log10(LAMBDA_BOUNDS[1])),
    method='bounded'
)
best_lambda = 10 ** opt.x

A_full = Z_all.T @ Z_all + best_lambda * np.eye(Z_all.shape[1])
b_full = Z_all.T @ y_train
w_big = linalg.solve(A_full, b_full, assume_a='pos')
yhat_big = Z_test @ w_big
cost_big = time.perf_counter() - start

rmse, mae, r2 = calc_metrics(y_test, yhat_big)
results.append(("大模型代理", rmse, mae, r2, cost_big, len(w_big)))
pred_dict["大模型代理"] = yhat_big

# =========================
# 8) 打印 KPI 结果表格
# =========================
print("\nKPI结果表（来水量预测）")
print("-" * 88)
print(f"{'模型':<16}{'RMSE':>10}{'MAE':>10}{'R2':>10}{'训练耗时(s)':>16}{'参数量':>12}")
print("-" * 88)
for name, rmse, mae, r2, tcost, nparam in results:
    print(f"{name:<16}{rmse:>10.3f}{mae:>10.3f}{r2:>10.3f}{tcost:>16.4f}{nparam:>12d}")
print("-" * 88)
print(f"大模型代理最优正则系数 lambda = {best_lambda:.6f}")

# =========================
# 9) 绘图（matplotlib）
# =========================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))

# 图1：测试集预测曲线
axes[0].plot(t_test, y_test, color='black', linewidth=2.0, label='真实来水量')
axes[0].plot(t_test, pred_dict["线性模型"], linestyle='--', label='线性模型')
axes[0].plot(t_test, pred_dict["非线性特征模型"], linestyle='-.', label='非线性特征模型')
axes[0].plot(t_test, pred_dict["大模型代理"], linestyle=':', linewidth=2.2, label='大模型代理')
axes[0].set_title("测试集预测对比")
axes[0].set_xlabel("时间 / 天")
axes[0].set_ylabel("来水量（相对单位）")
axes[0].grid(alpha=0.25)
axes[0].legend()

# 图2：KPI 对比（RMSE + R2）
names = [r[0] for r in results]
rmse_vals = [r[1] for r in results]
r2_vals = [r[3] for r in results]
x = np.arange(len(names))

axes[1].bar(x, rmse_vals, width=0.55, alpha=0.82, label='RMSE')
axes[1].set_xticks(x)
axes[1].set_xticklabels(names, rotation=15)
axes[1].set_ylabel("RMSE（越小越好）")
axes[1].set_title("KPI对比：误差与拟合优度")
axes[1].grid(axis='y', alpha=0.25)

ax2 = axes[1].twinx()
ax2.plot(x, r2_vals, color='tab:red', marker='o', linewidth=2, label='R2')
ax2.set_ylabel("R2（越大越好）")
ax2.set_ylim(0.0, 1.05)

h1, l1 = axes[1].get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
axes[1].legend(h1 + h2, l1 + l2, loc='lower right')

plt.tight_layout()
plt.savefig('ch01_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch01_simulation_result.png")
# plt.show()  # 禁用弹窗
