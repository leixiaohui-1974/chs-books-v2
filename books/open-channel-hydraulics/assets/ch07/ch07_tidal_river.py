import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch07"
os.makedirs(output_dir, exist_ok=True)

# 矩形渠道感潮河段模拟 (MacCormack 格式求解一维圣维南方程)
# 参数设置
L = 15000.0      # 河道总长 m
b = 50.0         # 矩形底宽 m
S0 = 0.0002      # 底坡 (极缓)
n = 0.025        # 糙率
g = 9.81         # 重力加速度

# 时间与空间步长
dx = 150.0       # 空间步长 150m
dt = 4.0         # 时间步长 4s (满足 Courant 条件, 波速约 6m/s)
nx = int(L / dx) + 1
nt = 3600        # 模拟总步数 (4小时)

# 初始条件 (恒定均匀流)
Q_init = 150.0   # 上游来水恒定流量 m^3/s

# 计算初始均匀流水深
def calc_normal_depth(Q):
    h = 2.0
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

# 初始化变量矩阵
A = np.ones(nx) * (b * h_init)
Q = np.ones(nx) * Q_init

# 潮汐边界参数 (下游)
# 半日潮周期约12小时，为了在短河道内快速看到效果，我们模拟一个2小时的快速潮波或潮汐的涨潮阶段
T_tide = 120 * 60.0 # 2小时周期
Amp_tide = 2.5      # 潮幅 2.5m
h_base = h_init     # 基准水位

history_t = []
history_x0_h = []
history_x7500_h = []
history_x15000_h = []
history_x7500_Q = []

snapshots = [0, 450, 900, 1350, 1800] # 0, 30, 60, 90, 120 minutes
snapshot_data = {}

def get_flux(A_val, Q_val):
    F1 = Q_val
    F2 = (Q_val**2 / A_val) + g * (A_val**2) / (2 * b)
    return np.array([F1, F2])

def get_source(A_val, Q_val):
    h_val = A_val / b
    P_val = b + 2 * h_val
    R_val = A_val / P_val
    Sf = (n**2 * (Q_val/A_val)*abs(Q_val/A_val)) / (R_val**(4/3)) # 注意绝对值处理反向流
    S1 = 0.0
    S2 = g * A_val * (S0 - Sf)
    return np.array([S1, S2])

# 开始时间演进
for t_step in range(nt):
    t_sec = t_step * dt
    
    # 上游边界：流量恒定，水深采用特征线外推 (为简化，假设水位梯度为0或简单外推)
    Q[0] = Q_init
    A[0] = A[1] # 简单的诺依曼边界
    
    # 下游边界：感潮水位 (随时间正弦波动)
    h_tide_current = h_base + Amp_tide * np.sin(2 * np.pi * t_sec / T_tide)
    # 如果水深低于安全值，做截断
    h_tide_current = max(h_tide_current, 0.5)
    A[-1] = b * h_tide_current
    # 下游流量简单外推
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
        
        A_new[i] = max(U_new_val[0], 0.1)
        Q_new[i] = U_new_val[1]
        
    A = np.copy(A_new)
    Q = np.copy(Q_new)
    
    # 记录时间序列
    if t_step % 15 == 0: # 每分钟记录一次
        history_t.append(t_sec / 60.0) # 分钟
        history_x0_h.append(A[0]/b)
        history_x7500_h.append(A[int(nx/2)]/b)
        history_x15000_h.append(A[-1]/b)
        history_x7500_Q.append(Q[int(nx/2)])
    
    # 记录空间快照
    if t_step in snapshots:
        # 将水深转换为水面高程 Z = z_bottom + h
        z_bottom = np.array([(L - x_val) * S0 for x_val in np.linspace(0, L, nx)])
        Z_water = z_bottom + A/b
        snapshot_data[f'T={int(t_sec/60)}min'] = {'x': np.linspace(0, L, nx), 'Z': Z_water, 'Q': np.copy(Q)}

# 绘制时间序列图 (潮位向上游的传播与衰减)
plt.figure(figsize=(10, 6))
plt.plot(history_t, history_x15000_h, 'r-', linewidth=2, label='Downstream Estuary ($x=15km$)')
plt.plot(history_t, history_x7500_h, 'g--', linewidth=2, label='Mid-river ($x=7.5km$)')
plt.plot(history_t, history_x0_h, 'b:', linewidth=2, label='Upstream Boundary ($x=0km$)')
plt.xlabel('Time (minutes)', fontsize=12)
plt.ylabel('Water Depth $h$ (m)', fontsize=12)
plt.title('Tidal Wave Propagation Upstream (Depth vs Time)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "tidal_depth_time.png"), dpi=300, bbox_inches='tight')

# 绘制空间剖面图 (逆向传播的水面线)
plt.figure(figsize=(10, 6))
colors = ['k:', 'b-', 'g--', 'r-.', 'm-']
z_bottom_plot = np.array([(L - x_val) * S0 for x_val in np.linspace(0, L, nx)])

for idx, (t_label, data) in enumerate(snapshot_data.items()):
    plt.plot(data['x'], data['Z'], colors[idx], linewidth=2, label=f'Water Surface at {t_label}')

plt.plot(np.linspace(0, L, nx), z_bottom_plot, 'k-', linewidth=3, label='Channel Bottom')
plt.xlabel('Distance $x$ (m) [Flow Direction ->]', fontsize=12)
plt.ylabel('Elevation $Z$ (m)', fontsize=12)
plt.title('Tidal Bore Moving Upstream (Elevation vs Distance)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.xlim(0, L)
plt.savefig(os.path.join(output_dir, "tidal_bore_profile.png"), dpi=300, bbox_inches='tight')

# 提取关键点生成表格
df_table = []
for idx, (t_label, data) in enumerate(snapshot_data.items()):
    df_table.append({
        'Time': t_label,
        'Estuary Z (m) [x=15km]': round(data['Z'][-1], 2),
        'Mid-river Z (m) [x=7.5km]': round(data['Z'][int(nx/2)], 2),
        'Mid-river Q (m³/s) [x=7.5km]': round(data['Q'][int(nx/2)], 2),
        'Flow Direction': 'Downstream' if data['Q'][int(nx/2)] > 0 else 'Upstream (REVERSED)'
    })

df = pd.DataFrame(df_table)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "tidal_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
