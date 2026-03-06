import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\water-system-control\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 卡尔曼滤波 (Kalman Filter) 软测量与状态估计
# 场景：超声波液位计被强烈的表面水波纹(高斯噪声)干扰，且偶尔有飞鸟飞过导致脉冲干扰
# 状态方程：水箱液位模型 dh/dt = (Qin - Qout)/A

# 系统参数
A_tank = 2.0
C_valve = 0.5
dt = 0.1
t = np.arange(0, 100, dt)
N = len(t)

# 真实物理状态 (True State)
x_true = np.zeros(N)
x_true[0] = 1.0

# 控制输入 (已知)
u_in = np.ones(N) * 0.8 # 恒定进水
u_in[300:600] = 0.2 # 突然减少进水
u_in[800:] = 1.0 # 增加进水

# 过程噪声 (Process Noise) - 代表模型未知的扰动，例如阀门轻微泄漏
Q_proc = 1e-4
w_proc = np.random.normal(0, np.sqrt(Q_proc), N)

# 测量噪声 (Measurement Noise) - 雷达被水波纹严重干扰
R_meas = 0.05
v_meas = np.random.normal(0, np.sqrt(R_meas), N)

# 生成真实状态和带噪测量值
z_meas = np.zeros(N)

for i in range(1, N):
    # 真实非线性动态
    q_out = C_valve * np.sqrt(max(x_true[i-1], 0.01))
    dx = (u_in[i-1] - q_out) / A_tank * dt + w_proc[i-1]
    x_true[i] = x_true[i-1] + dx
    
    # 传感器测量 (加入飞鸟等脉冲异常点)
    z_meas[i] = x_true[i] + v_meas[i]
    if i == 200 or i == 700:
        z_meas[i] += 2.0 # 飞鸟导致雷达反射提前

# --- 扩展卡尔曼滤波 (Extended Kalman Filter, EKF) ---
x_est = np.zeros(N)
P_est = np.zeros(N) # 误差协方差
x_est[0] = 1.0
P_est[0] = 1.0

for i in range(1, N):
    # 1. 预测步 (Predict)
    # 利用非线性物理方程向前推演
    q_out_est = C_valve * np.sqrt(max(x_est[i-1], 0.01))
    x_pred = x_est[i-1] + (u_in[i-1] - q_out_est) / A_tank * dt
    
    # 计算雅可比矩阵 F = df/dx
    # f(x) = x + (u - c*sqrt(x))/A * dt
    # df/dx = 1 - (c * dt) / (2 * A * sqrt(x))
    F = 1.0 - (C_valve * dt) / (2.0 * A_tank * np.sqrt(max(x_est[i-1], 0.01)))
    
    P_pred = F * P_est[i-1] * F + Q_proc
    
    # 2. 更新步 (Update) - 仅当传感器数据看起来合理时更新 (摒弃异常值)
    # 测量残差 (Innovation)
    y = z_meas[i] - x_pred
    
    # 简单的异常值剔除逻辑 (如果测量值偏离预测值超过 0.5m，就不信任测量)
    if abs(y) > 0.5:
        # 异常情况，纯依靠物理模型预测
        x_est[i] = x_pred
        P_est[i] = P_pred
    else:
        # 正常情况，卡尔曼增益混合模型和传感器
        H = 1.0 # 测量矩阵
        S = H * P_pred * H + R_meas
        K = P_pred * H / S # 卡尔曼增益
        
        x_est[i] = x_pred + K * y
        P_est[i] = (1 - K * H) * P_pred

# 生成对比图表
plt.figure(figsize=(10, 6))

plt.plot(t, z_meas, 'gray', marker='.', linestyle='None', alpha=0.5, label='Raw Noisy Sensor Data (Radar)')
plt.plot(t, x_true, 'k-', linewidth=2, label='True Hidden Water Level')
plt.plot(t, x_est, 'r-', linewidth=2.5, label='Kalman Filter Estimation')

# 圈出被成功剔除的异常点
plt.plot(t[200], z_meas[200], 'ro', markersize=10, markerfacecolor='none', markeredgewidth=2)
plt.plot(t[700], z_meas[700], 'ro', markersize=10, markerfacecolor='none', markeredgewidth=2)
plt.annotate('Bird Interference\nSuccessfully Rejected', xy=(t[200], z_meas[200]), xytext=(t[200]+5, z_meas[200]),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

plt.xlabel('Time (s)', fontsize=12)
plt.ylabel('Water Level (m)', fontsize=12)
plt.title('Extended Kalman Filter for Level Estimation and Outlier Rejection', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "kalman_filter_sim.png"), dpi=300, bbox_inches='tight')

# 提取关键点对比数据
history = []
snapshots = [50, 200, 350, 700, 850]
for idx in snapshots:
    history.append({
        'Time Step (s)': t[idx],
        'True State (m)': round(x_true[idx], 3),
        'Raw Sensor (m)': round(z_meas[idx], 3),
        'EKF Estimate (m)': round(x_est[idx], 3),
        'Estimation Error (m)': round(abs(x_true[idx] - x_est[idx]), 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "kalman_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
