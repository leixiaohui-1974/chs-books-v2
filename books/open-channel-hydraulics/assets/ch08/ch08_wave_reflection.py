import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch08"
os.makedirs(output_dir, exist_ok=True)

# 矩形渠道波的反射与叠加模拟 (使用线性化的波方程简化模拟突发扰动)
# 简化的一维波动方程 d2h/dt2 = c^2 * d2h/dx2 (适用于小扰动和极小摩擦)
# 采用蛙跳法(Leapfrog)求解

# 参数设置
L = 4000.0       # 渠道总长 m
c = 10.0         # 波速 m/s (相当于水深约10m的重力波)
dx = 20.0        # 空间步长 20m
dt = 1.0         # 时间步长 1s (Courant数 c*dt/dx = 0.5)
nx = int(L / dx) + 1
nt = 800         # 模拟时间 800s

# 初始化水位网格 (h代表相对静水面的水位波动)
h = np.zeros(nx)
h_old = np.zeros(nx)
h_new = np.zeros(nx)

# 在中央产生一个初始的水位突起 (模拟落石或爆炸产生的水涌)
center_idx = int(nx / 2)
width_idx = 10
h[center_idx-width_idx:center_idx+width_idx+1] = np.hanning(2*width_idx+1) * 2.0 # 峰值2m的扰动
h_old[:] = h[:] # 初始动能为0，所以前后时刻水位相同

history_t = []
history_center_h = []
history_boundary_h = []

snapshots = [0, 100, 200, 400, 600, 799] 
snapshot_data = {}

# 开始时间演进
for t_step in range(nt):
    t_sec = t_step * dt
    
    # 内部节点计算
    for i in range(1, nx-1):
        # 波动方程显式差分格式: h_i^{n+1} = 2*h_i^n - h_i^{n-1} + (c*dt/dx)^2 * (h_{i+1}^n - 2*h_i^n + h_{i-1}^n)
        alpha = (c * dt / dx)**2
        h_new[i] = 2 * h[i] - h_old[i] + alpha * (h[i+1] - 2*h[i] + h[i-1])
        
    # 边界条件
    # 假设左端 (x=0) 是开阔水域（透射边界/吸收边界）
    h_new[0] = h[1] # 简单一阶外推吸收
    
    # 假设右端 (x=L) 是绝对刚性挡水墙（全反射边界）
    # 在刚性壁面处，水位的空间导数 dh/dx = 0 (即水质点速度为0)
    h_new[-1] = h_new[-2]
    
    # 状态更新
    h_old[:] = h[:]
    h[:] = h_new[:]
    
    # 记录时间序列
    if t_step % 2 == 0:
        history_t.append(t_sec)
        history_center_h.append(h[center_idx])
        history_boundary_h.append(h[-1])
        
    # 记录空间快照
    if t_step in snapshots:
        snapshot_data[f'T={t_sec}s'] = {'x': np.linspace(0, L, nx), 'h': np.copy(h)}

# 绘制空间波形演进图
plt.figure(figsize=(10, 8))
colors = ['k:', 'b-', 'g--', 'r-', 'm-.', 'c-']
for idx, (t_label, data) in enumerate(snapshot_data.items()):
    plt.plot(data['x'], data['h'], colors[idx], linewidth=2, label=f'Wave at {t_label}')

# 画出右侧的刚性墙体
plt.axvline(x=L, color='k', linewidth=4, label='Rigid Wall (Reflective Boundary)')

plt.xlabel('Distance $x$ (m)', fontsize=12)
plt.ylabel('Water Level Fluctuation $\Delta h$ (m)', fontsize=12)
plt.title('Wave Reflection at a Rigid Boundary', fontsize=14)
plt.legend(loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.xlim(1500, L+50) # 放大右半部分以清晰展示反射
plt.savefig(os.path.join(output_dir, "wave_reflection_profile.png"), dpi=300, bbox_inches='tight')

# 绘制时间序列图
plt.figure(figsize=(10, 6))
plt.plot(history_t, history_center_h, 'b-', linewidth=2, label='Disturbance Origin ($x=2000m$)')
plt.plot(history_t, history_boundary_h, 'r-', linewidth=2, label='Rigid Wall ($x=4000m$)')
plt.xlabel('Time (seconds)', fontsize=12)
plt.ylabel('Water Level Fluctuation $\Delta h$ (m)', fontsize=12)
plt.title('Time Series of Wave Reflection', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "wave_time_series.png"), dpi=300, bbox_inches='tight')

# 提取关键点生成表格
df_table = []
# 寻找刚性壁面处的最大水位
max_wall_h = max(history_boundary_h)
max_wall_time = history_t[history_boundary_h.index(max_wall_h)]

df_table.append({'Event': 'Initial Pulse Creation', 'Time (s)': 0, 'Location': 'x=2000m', 'Max Amplitude (m)': 2.00})
df_table.append({'Event': 'Wave Splitting (Rightward)', 'Time (s)': 100, 'Location': 'x~3000m', 'Max Amplitude (m)': 1.00})
df_table.append({'Event': 'Wave Splitting (Leftward)', 'Time (s)': 100, 'Location': 'x~1000m', 'Max Amplitude (m)': 1.00})
df_table.append({'Event': 'Collision with Rigid Wall', 'Time (s)': max_wall_time, 'Location': 'x=4000m', 'Max Amplitude (m)': round(max_wall_h, 2)})
df_table.append({'Event': 'Reflected Wave Returns', 'Time (s)': max_wall_time + 200, 'Location': 'x=2000m', 'Max Amplitude (m)': 1.00})

df = pd.DataFrame(df_table)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "reflection_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
