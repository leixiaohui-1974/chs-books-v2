"""
第2章仿真：永磁同步电机（PMSM）参数在线辨识
基于d-q坐标系的PMSM模型，使用RLS辨识定子电阻Rs和d轴电感Ld。
模拟温度升高导致Rs漂移的场景。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ---------- PMSM 参数 ----------
# 额定参数（25°C）
Rs_nominal = 1.2       # 定子电阻 (Ohm)
Ld_nominal = 8.5e-3    # d轴电感 (H)
Lq_nominal = 12.0e-3   # q轴电感 (H)
psi_f = 0.175           # 永磁体磁链 (Wb)
p = 4                   # 极对数
J = 0.0008              # 转动惯量 (kg*m^2)

# 仿真参数
dt = 50e-6  # 50us采样
T_total = 2.0
time = np.arange(0, T_total, dt)
N = len(time)

# Rs 随温度线性漂移：从1.2升至1.56 (30%增幅，模拟80°C温升)
Rs_true = Rs_nominal * (1 + 0.3 * time / T_total)
Ld_true = Ld_nominal * np.ones(N)  # Ld保持恒定

# 电机转速 (rad/s electrical)
omega_e = 2 * np.pi * 100  # 电角速度 100Hz

# d-q轴电压方程 (离散化)
# v_d = Rs*i_d + Ld*di_d/dt - omega_e*Lq*i_q
# v_q = Rs*i_q + Lq*di_q/dt + omega_e*Ld*i_d + omega_e*psi_f

# 控制输入：id=0控制（典型PMSM矢量控制）
# 注入小幅PRBS扰动以保证持续激励
np.random.seed(123)
i_d = np.zeros(N)
i_q = 5.0 * np.ones(N)  # 5A额定负载电流

# 添加PRBS激励
prbs_d = 0.5 * np.random.choice([-1, 1], size=N)
prbs_q = 0.3 * np.random.choice([-1, 1], size=N)

# 计算电压（正向模型）
v_d = np.zeros(N)
v_q = np.zeros(N)

for k in range(1, N):
    di_d = prbs_d[k] / Ld_nominal  # 电流变化
    di_q = prbs_q[k] / Lq_nominal
    i_d[k] = i_d[k-1] + di_d * dt
    i_q[k] = i_q[k-1] + di_q * dt

    v_d[k] = Rs_true[k] * i_d[k] + Ld_true[k] * (i_d[k] - i_d[k-1]) / dt - omega_e * Lq_nominal * i_q[k]
    v_q[k] = Rs_true[k] * i_q[k] + Lq_nominal * (i_q[k] - i_q[k-1]) / dt + omega_e * Ld_true[k] * i_d[k] + omega_e * psi_f

# 添加测量噪声
noise_v = 0.1
v_d_meas = v_d + np.random.normal(0, noise_v, N)
v_q_meas = v_q + np.random.normal(0, noise_v, N)

# ---------- RLS 辨识 Rs 和 Ld ----------
# 简化d轴模型：v_d + omega_e*Lq*i_q = Rs*i_d + Ld*di_d/dt
# 令 y = v_d + omega_e*Lq*i_q, phi = [i_d, di_d/dt]^T, theta = [Rs, Ld]^T

theta_est = np.zeros((2, N))
theta_est[:, 0] = [1.0, 5e-3]  # 初始猜测
P_rls = np.eye(2) * 1e4
lam = 0.998

Rs_est = np.zeros(N)
Ld_est = np.zeros(N)

for k in range(2, N):
    di_dt = (i_d[k] - i_d[k-1]) / dt
    y_k = v_d_meas[k] + omega_e * Lq_nominal * i_q[k]
    phi = np.array([[i_d[k]], [di_dt]])

    denom = lam + float(phi.T @ P_rls @ phi)
    K = P_rls @ phi / denom
    err = y_k - float(phi.T @ theta_est[:, k-1:k])
    theta_est[:, k] = theta_est[:, k-1] + (K * err).flatten()
    P_rls = (P_rls - K @ phi.T @ P_rls) / lam
    P_rls = (P_rls + P_rls.T) / 2

Rs_est = theta_est[0, :]
Ld_est = theta_est[1, :]

# ---------- 降采样绘图 ----------
ds = 20  # 降采样因子
t_plot = time[::ds]
Rs_true_plot = Rs_true[::ds]
Rs_est_plot = Rs_est[::ds]
Ld_true_plot = Ld_true[::ds] * 1e3
Ld_est_plot = Ld_est[::ds] * 1e3

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(t_plot, Rs_true_plot, 'k--', linewidth=2, label='真实值 Rs')
ax1.plot(t_plot, Rs_est_plot, '#1565C0', linewidth=1.2, label='RLS估计值 Rs')
ax1.set_ylabel('定子电阻 Rs (Ohm)')
ax1.set_title('PMSM定子电阻在线辨识 —— 温度漂移跟踪')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xlim([0, T_total])

ax2.plot(t_plot, Ld_true_plot, 'k--', linewidth=2, label='真实值 Ld')
ax2.plot(t_plot, Ld_est_plot, '#FF7043', linewidth=1.2, label='RLS估计值 Ld')
ax2.set_ylabel('d轴电感 Ld (mH)')
ax2.set_xlabel('时间 (s)')
ax2.set_title('PMSM d轴电感在线辨识')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xlim([0, T_total])
ax2.set_ylim([0, 20])

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "pmsm_rls_identification.png"), dpi=200)
plt.close()

# ---------- 输出KPI ----------
print("=" * 60)
print("第2章仿真结果：PMSM参数在线辨识")
print("=" * 60)

# 取最后0.2s稳态
idx_end = time >= 1.8
Rs_final_true = np.mean(Rs_true[idx_end])
Rs_final_est = np.mean(Rs_est[idx_end])
Ld_final_est = np.mean(Ld_est[idx_end])

Rs_err = abs(Rs_final_est - Rs_final_true) / Rs_final_true * 100
Ld_err = abs(Ld_final_est - Ld_nominal) / Ld_nominal * 100

# 收敛时间
idx_conv = np.where(np.abs(Rs_est[100:] - Rs_true[100:]) / Rs_true[100:] < 0.05)[0]
t_conv = time[idx_conv[0] + 100] if len(idx_conv) > 0 else float('inf')

print(f"\n定子电阻 Rs:")
print(f"  额定值(25C) = {Rs_nominal} Ohm")
print(f"  终值(温漂后真实) = {Rs_final_true:.3f} Ohm")
print(f"  终值(RLS估计) = {Rs_final_est:.3f} Ohm")
print(f"  相对误差 = {Rs_err:.2f}%")
print(f"  收敛时间 = {t_conv*1000:.1f} ms")

print(f"\nd轴电感 Ld:")
print(f"  真实值 = {Ld_nominal*1e3:.1f} mH")
print(f"  终值(RLS估计) = {Ld_final_est*1e3:.2f} mH")
print(f"  相对误差 = {Ld_err:.2f}%")

print(f"\n温度漂移幅度: Rs从{Rs_nominal}升至{Rs_true[-1]:.3f} Ohm (+{(Rs_true[-1]/Rs_nominal-1)*100:.0f}%)")
print(f"电角速度: {omega_e/(2*np.pi):.0f} Hz")
print(f"采样频率: {1/dt/1000:.0f} kHz")
print(f"遗忘因子: {lam}")
