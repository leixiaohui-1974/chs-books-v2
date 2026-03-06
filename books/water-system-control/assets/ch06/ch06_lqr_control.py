"""
第6章配套仿真：LQR最优控制在耦合双渠池系统中的应用

物理场景：串联双渠池灌溉渠道
- 上游渠池（Pool 1）和下游渠池（Pool 2）通过节制闸连接
- 两个控制输入：u1=上游进水闸开度，u2=池间节制闸开度
- 两个控制目标：h1(上游水位)，h2(下游水位)
- 耦合效应：增大u2排空Pool1、充填Pool2，两水位反向变化
- LQR权重博弈：上游水位优先 vs 下游水位优先
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.linalg as la
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# === 物理参数 ===
# 渠池面积
A1 = 500.0    # Pool 1 水面面积 m^2
A2 = 400.0    # Pool 2 水面面积 m^2

# 线性化流量系数（在工作点附近）
c_d1 = 0.8    # 上游进水闸流量系数
c_d2 = 0.6    # 池间节制闸流量系数
c_leak1 = 0.02  # Pool 1 渗漏/取水系数
c_leak2 = 0.03  # Pool 2 渗漏/取水系数

# 线性化状态空间矩阵
# 状态 x = [δh1, δh2]^T（水位偏差）
# 输入 u = [δu1, δu2]^T（闸门开度偏差）
# dx/dt = Ax + Bu
A_sys = np.array([
    [-(c_leak1 + c_d2) / A1,   c_d2 / A1],     # δh1: 自排 + 出流到Pool2 + 回水效应
    [c_d2 / A2,               -(c_leak2 + c_d2) / A2]  # δh2: 来自Pool1 + 自排
])

B_sys = np.array([
    [c_d1 / A1,  -c_d2 / A1],   # u1进水填Pool1, u2出水排Pool1
    [0.0,         c_d2 / A2]     # u2进水填Pool2
])

print(f"System matrix A:\n{A_sys}")
print(f"Input matrix B:\n{B_sys}")
print(f"Eigenvalues of A: {np.linalg.eigvals(A_sys)}")

# === LQR设计 ===
R = np.diag([1.0, 1.0])  # 控制代价相同

# 策略1: 上游水位优先（保护上游蓄水库）
Q_upstream = np.diag([100.0, 1.0])

# 策略2: 下游水位优先（保障下游灌溉用水）
Q_downstream = np.diag([1.0, 100.0])

# 策略3: 均衡策略
Q_balanced = np.diag([10.0, 10.0])

# 求解CARE
P1 = la.solve_continuous_are(A_sys, B_sys, Q_upstream, R)
K1 = np.linalg.inv(R) @ B_sys.T @ P1

P2 = la.solve_continuous_are(A_sys, B_sys, Q_downstream, R)
K2 = np.linalg.inv(R) @ B_sys.T @ P2

P3 = la.solve_continuous_are(A_sys, B_sys, Q_balanced, R)
K3 = np.linalg.inv(R) @ B_sys.T @ P3

print(f"\nGain K (upstream-first):\n{K1}")
print(f"Gain K (downstream-first):\n{K2}")
print(f"Gain K (balanced):\n{K3}")

# === 仿真 ===
dt = 0.5
t = np.arange(0, 600, dt)
N = len(t)

# 初始状态：上游比目标高0.5m，下游比目标低0.8m（典型的调水场景）
x0 = np.array([0.5, -0.8])

def simulate(K, x0, u_max=2.0):
    x = np.zeros((2, N))
    u = np.zeros((2, N))
    x[:, 0] = x0
    for i in range(1, N):
        u_cmd = -K @ x[:, i-1]
        u[:, i] = np.clip(u_cmd, -u_max, u_max)
        dx = A_sys @ x[:, i-1] + B_sys @ u[:, i]
        x[:, i] = x[:, i-1] + dx * dt
    return x, u

x1, u1_hist = simulate(K1, x0)
x2, u2_hist = simulate(K2, x0)
x3, u3_hist = simulate(K3, x0)

# === 绘图 ===
fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)

# 子图1: Pool 1 水位偏差
ax = axes[0]
ax.plot(t, x1[0, :], 'r--', linewidth=1.5, label='Upstream-First ($Q_{11}$=100)')
ax.plot(t, x2[0, :], 'g-.', linewidth=1.5, label='Downstream-First ($Q_{22}$=100)')
ax.plot(t, x3[0, :], 'b-', linewidth=2, label='Balanced ($Q_{11}$=$Q_{22}$=10)')
ax.axhline(0, color='k', linestyle=':', linewidth=0.8)
ax.set_ylabel('Pool 1 Level Error [m]', fontweight='bold')
ax.set_title('Coupled Dual-Pool LQR: Water Level Regulation', fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 子图2: Pool 2 水位偏差
ax = axes[1]
ax.plot(t, x1[1, :], 'r--', linewidth=1.5, label='Upstream-First')
ax.plot(t, x2[1, :], 'g-.', linewidth=1.5, label='Downstream-First')
ax.plot(t, x3[1, :], 'b-', linewidth=2, label='Balanced')
ax.axhline(0, color='k', linestyle=':', linewidth=0.8)
ax.set_ylabel('Pool 2 Level Error [m]', fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 子图3: 控制输入
ax = axes[2]
ax.plot(t, u1_hist[0, :], 'r--', linewidth=1, label='u1 (Upstream-First)')
ax.plot(t, u1_hist[1, :], 'r:', linewidth=1, label='u2 (Upstream-First)')
ax.plot(t, u3_hist[0, :], 'b-', linewidth=1.5, label='u1 (Balanced)')
ax.plot(t, u3_hist[1, :], 'b:', linewidth=1.5, label='u2 (Balanced)')
ax.axhline(2.0, color='gray', linestyle=':', linewidth=0.8, label='Limit')
ax.axhline(-2.0, color='gray', linestyle=':', linewidth=0.8)
ax.set_xlabel('Time [s]', fontweight='bold')
ax.set_ylabel('Gate Opening $\Delta u$', fontweight='bold')
ax.legend(fontsize=8, ncol=2)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "lqr_control_sim.png"), dpi=300, bbox_inches='tight')

# === 生成对比表格 ===
history = []
snapshots = [10, 30, 60, 120, 300, 500]

for t_val in snapshots:
    idx = int(t_val / dt)
    for label, x_data, u_data in [
        ('Upstream-First', x1, u1_hist),
        ('Downstream-First', x2, u2_hist),
        ('Balanced', x3, u3_hist)
    ]:
        history.append({
            'Time (s)': t_val,
            'Strategy': label,
            'Pool1 Error (m)': round(x_data[0, idx], 3),
            'Pool2 Error (m)': round(x_data[1, idx], 3),
            'u1': round(u_data[0, idx], 3),
            'u2': round(u_data[1, idx], 3)
        })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "lqr_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print(f"\nFigure saved to: {os.path.join(output_dir, 'lqr_control_sim.png')}")
print(f"Table saved to: {os.path.join(output_dir, 'lqr_table.md')}")
print(f"\n{md_table}")
