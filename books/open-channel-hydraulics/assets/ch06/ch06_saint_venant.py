import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch06"
os.makedirs(output_dir, exist_ok=True)

# 矩形渠道一维圣维南方程组有限差分法 (MacCormack 格式) - 洪波演进
# 参数设置
L = 10000.0      # 渠道总长 m
b = 10.0         # 矩形底宽 m
S0 = 0.001       # 底坡
n = 0.025        # 糙率
g = 9.81         # 重力加速度

# 时间与空间步长
dx = 100.0       # 空间步长 100m
dt = 5.0         # 时间步长 5s (满足 Courant 条件)
nx = int(L / dx) + 1
nt = 800         # 模拟总步数 (约 1.1 小时)

# 初始条件 (恒定均匀流)
Q_init = 20.0    # 初始流量 m^3/s

# 计算初始均匀流水深 (牛顿法)
def calc_normal_depth(Q):
    h = 1.0
    for _ in range(50):
        A = b * h
        P = b + 2 * h
        R = A / P
        Q_calc = (1/n) * A * (R**(2/3)) * np.sqrt(S0)
        f = Q_calc - Q
        if abs(f) < 1e-4: return h
        dh = 0.001
        A_d = b * (h + dh)
        P_d = b + 2 * (h + dh)
        R_d = A_d / P_d
        Q_calc_d = (1/n) * A_d * (R_d**(2/3)) * np.sqrt(S0)
        df = (Q_calc_d - Q_calc) / dh
        h = h - f / df
    return h

h_init = calc_normal_depth(Q_init)

# 初始化变量矩阵 (守恒型变量 U = [A, Q])
A = np.ones(nx) * (b * h_init)
Q = np.ones(nx) * Q_init

# 记录历史数据用于绘图
history_t = []
history_x5000_Q = []
history_x5000_h = []

# 提取关键时间点的空间分布
snapshots = [0, 200, 400, 600, 799] 
snapshot_data = {}

def get_flux(A_val, Q_val):
    # F = [Q, Q^2/A + g*I1]
    # 对矩形渠道，I1 对水面的静水压力项近似为 h^2 * b / 2 = A^2 / (2b)
    F1 = Q_val
    F2 = (Q_val**2 / A_val) + g * (A_val**2) / (2 * b)
    return np.array([F1, F2])

def get_source(A_val, Q_val):
    # S = [0, gA(S0 - Sf)]
    h_val = A_val / b
    P_val = b + 2 * h_val
    R_val = A_val / P_val
    Sf = (n**2 * (Q_val/A_val)**2) / (R_val**(4/3))
    S1 = 0.0
    S2 = g * A_val * (S0 - Sf)
    return np.array([S1, S2])

# 开始时间演进
for t_step in range(nt):
    t_sec = t_step * dt
    
    # 边界条件：上游注入洪水波 (正弦波叠加)
    if t_sec < 1800: # 前半小时涨水
        Q[0] = Q_init + 30.0 * np.sin(np.pi * t_sec / 1800.0) 
    else:
        Q[0] = Q_init
    
    # 上游水深采用特征线法外推或简单假设为正常水深关系 (简化处理)
    A[0] = b * calc_normal_depth(Q[0])
    
    # 下游边界：开放边界 (零梯度)
    A[-1] = A[-2]
    Q[-1] = Q[-2]
    
    A_new = np.copy(A)
    Q_new = np.copy(Q)
    
    # MacCormack Predictor Step (向前差分)
    A_star = np.copy(A)
    Q_star = np.copy(Q)
    for i in range(1, nx-1):
        U_i = np.array([A[i], Q[i]])
        F_i = get_flux(A[i], Q[i])
        F_i1 = get_flux(A[i+1], Q[i+1])
        S_i = get_source(A[i], Q[i])
        
        U_star = U_i - (dt/dx) * (F_i1 - F_i) + dt * S_i
        A_star[i] = U_star[0]
        Q_star[i] = U_star[1]
        
    # MacCormack Corrector Step (向后差分)
    for i in range(1, nx-1):
        U_i = np.array([A[i], Q[i]])
        F_star_i = get_flux(A_star[i], Q_star[i])
        F_star_im1 = get_flux(A_star[i-1], Q_star[i-1])
        S_star_i = get_source(A_star[i], Q_star[i])
        
        U_new_val = 0.5 * (U_i + np.array([A_star[i], Q_star[i]]) - (dt/dx) * (F_star_i - F_star_im1) + dt * S_star_i)
        
        # 数值稳定性保护
        A_new[i] = max(U_new_val[0], 0.1)
        Q_new[i] = U_new_val[1]
        
    A = np.copy(A_new)
    Q = np.copy(Q_new)
    
    # 记录中点 (x=5000m) 的时间序列
    mid_idx = int(nx / 2)
    history_t.append(t_sec / 60.0) # 分钟
    history_x5000_Q.append(Q[mid_idx])
    history_x5000_h.append(A[mid_idx] / b)
    
    # 记录空间快照
    if t_step in snapshots:
        snapshot_data[f'T={int(t_sec/60)}min'] = {'x': np.linspace(0, L, nx), 'Q': np.copy(Q), 'h': A/b}

# 绘制时间序列过程线 (Hydrograph)
plt.figure(figsize=(10, 6))
plt.plot(history_t, history_x5000_Q, 'b-', linewidth=2.5, label='Discharge $Q$ at $x=5000m$')
plt.xlabel('Time (minutes)', fontsize=12)
plt.ylabel('Discharge $Q$ ($m^3/s$)', fontsize=12)
plt.title('Flood Hydrograph at Midpoint (Saint-Venant Routing)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.savefig(os.path.join(output_dir, "flood_hydrograph.png"), dpi=300, bbox_inches='tight')

# 绘制空间演进过程 (Wave Propagation)
plt.figure(figsize=(10, 6))
colors = ['k:', 'b-', 'g--', 'r-.', 'm-']
for idx, (t_label, data) in enumerate(snapshot_data.items()):
    plt.plot(data['x'], data['Q'], colors[idx], linewidth=2, label=f'Wave at {t_label}')

plt.xlabel('Distance $x$ (m)', fontsize=12)
plt.ylabel('Discharge $Q$ ($m^3/s$)', fontsize=12)
plt.title('Flood Wave Propagation along the Channel', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "wave_propagation.png"), dpi=300, bbox_inches='tight')

# 生成对比表格 (洪峰衰减与延迟)
# 找出 x=0 和 x=5000m 处的洪峰时间和峰值
peak_Q_0 = Q_init + 30.0 # 根据正弦波设定
peak_t_0 = 15.0 # 分钟 (正弦波在1800s也就是30min结束，峰值在15min)

peak_idx_5000 = np.argmax(history_x5000_Q)
peak_Q_5000 = history_x5000_Q[peak_idx_5000]
peak_t_5000 = history_t[peak_idx_5000]

md_content = f"""
| 观测点位置 | 洪峰到达时间 (min) | 洪峰流量 ($m^3/s$) | 洪峰水深 ($m$) | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| 上游起点 ($x=0m$) | {peak_t_0:.1f} | {peak_Q_0:.2f} | {calc_normal_depth(peak_Q_0):.2f} | 洪水原发地 |
| 渠道中点 ($x=5000m$) | {peak_t_5000:.1f} | {peak_Q_5000:.2f} | {history_x5000_h[peak_idx_5000]:.2f} | 波形发生坦化与平移 |
"""

with open(os.path.join(output_dir, "wave_routing_table.md"), "w", encoding="utf-8") as f:
    f.write(md_content)

print("Files generated successfully.")
