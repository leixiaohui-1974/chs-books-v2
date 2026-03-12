"""
第1章仿真：递推最小二乘法（RLS）与遗忘因子
演示RLS在参数突变场景下的跟踪能力，比较不同遗忘因子的效果。
系统模型：一阶线性系统 y(k) = a*y(k-1) + b*u(k-1) + e(k)
参数在 t=5s 时发生突变，模拟设备老化/工况切换。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# ---------- 中文字体配置 ----------
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ---------- 系统参数 ----------
dt = 0.01
T_total = 10.0
time = np.arange(0, T_total, dt)
N = len(time)

# 真实参数：在 t=5s 突变
a_true = np.where(time < 5.0, 0.95, 0.80)
b_true = np.where(time < 5.0, 0.10, 0.25)

# 输入信号：PRBS
np.random.seed(42)
u = np.random.choice([-1.0, 1.0], size=N)

# 生成系统输出
y = np.zeros(N)
noise_std = 0.02
for k in range(1, N):
    y[k] = a_true[k] * y[k-1] + b_true[k] * u[k-1] + np.random.normal(0, noise_std)

# ---------- RLS with different forgetting factors ----------
forgetting_factors = [1.0, 0.99, 0.95]
labels = ['lambda=1.0 (无遗忘)', 'lambda=0.99', 'lambda=0.95']
colors = ['#1565C0', '#4CAF50', '#FF7043']

results = {}

for lf, label in zip(forgetting_factors, labels):
    theta = np.zeros((2, N))
    P = np.eye(2) * 1000.0

    for k in range(1, N):
        phi = np.array([[y[k-1]], [u[k-1]]])
        denom = lf + float(phi.T @ P @ phi)
        K = P @ phi / denom
        err = y[k] - float(phi.T @ theta[:, k-1:k])
        theta[:, k] = theta[:, k-1] + (K * err).flatten()
        P = (P - K @ phi.T @ P) / lf
        # 数值稳定性
        P = (P + P.T) / 2

    results[label] = {
        'a_est': theta[0, :],
        'b_est': theta[1, :],
    }

# ---------- 绘图 ----------
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

for (label, res), color in zip(results.items(), colors):
    axes[0].plot(time, res['a_est'], color=color, linewidth=1.2, label=label)
axes[0].plot(time, a_true, 'k--', linewidth=2, label='真实值 a')
axes[0].set_ylabel('参数 a')
axes[0].set_title('RLS在线辨识 —— 参数a的跟踪（t=5s参数突变）')
axes[0].legend(loc='best')
axes[0].grid(True, alpha=0.3)
axes[0].set_xlim([0, T_total])

for (label, res), color in zip(results.items(), colors):
    axes[1].plot(time, res['b_est'], color=color, linewidth=1.2, label=label)
axes[1].plot(time, b_true, 'k--', linewidth=2, label='真实值 b')
axes[1].set_ylabel('参数 b')
axes[1].set_xlabel('时间 (s)')
axes[1].set_title('RLS在线辨识 —— 参数b的跟踪（t=5s参数突变）')
axes[1].legend(loc='best')
axes[1].grid(True, alpha=0.3)
axes[1].set_xlim([0, T_total])

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "rls_forgetting_factor.png"), dpi=200)
plt.close()

# ---------- 输出KPI ----------
print("=" * 60)
print("第1章仿真结果：RLS遗忘因子对比")
print("=" * 60)

# 取突变后稳态值（t=8~10s）
idx_steady = time >= 8.0
a_true_final = 0.80
b_true_final = 0.25

for label, res in results.items():
    a_final = np.mean(res['a_est'][idx_steady])
    b_final = np.mean(res['b_est'][idx_steady])
    a_err = abs(a_final - a_true_final) / a_true_final * 100
    b_err = abs(b_final - b_true_final) / b_true_final * 100

    # 收敛时间：参数a首次进入真值5%范围的时刻（突变后）
    idx_after = time >= 5.0
    a_after = res['a_est'][idx_after]
    t_after = time[idx_after]
    converged = np.where(np.abs(a_after - a_true_final) < 0.05 * abs(a_true_final))[0]
    t_conv = t_after[converged[0]] - 5.0 if len(converged) > 0 else float('inf')

    print(f"\n{label}:")
    print(f"  a 稳态估计 = {a_final:.4f}, 误差 = {a_err:.2f}%")
    print(f"  b 稳态估计 = {b_final:.4f}, 误差 = {b_err:.2f}%")
    print(f"  突变后收敛时间(a) = {t_conv:.3f} s")

print("\n真实参数(突变后): a = 0.80, b = 0.25")
print(f"噪声标准差: {noise_std}")
print(f"采样间隔: {dt} s")
print(f"仿真总时长: {T_total} s")
