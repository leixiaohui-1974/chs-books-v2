import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch10"
os.makedirs(output_dir, exist_ok=True)

# 水锤现象模拟 (Water Hammer)
# 特征线法 (Method of Characteristics, MOC) 求解有压管流瞬态

# 参数设置
L = 2000.0       # 管道总长 m
D = 1.0          # 管道内径 m
a = 1000.0       # 水击波速 m/s (取决于管材和水的体积弹性模量)
f = 0.02         # 达西阻力系数
H0 = 100.0       # 上游水库恒定水头 m
V0 = 2.5         # 初始稳态流速 m/s
g = 9.81         # 重力加速度

# 计算初始稳态水头分布
A = np.pi * (D**2) / 4.0
H_init = np.zeros(0) # 稍后初始化
V_init = np.ones(0) * V0

# 阀门关闭时间 (Tc)
Tc = 4.0         # 阀门完全关闭所需时间 s (线性关闭)
# 水击相长 Tr = 2L/a = 2*2000/1000 = 4.0s
# 这里设 Tc = Tr，属于间接水击的临界情况

# 时空网格剖分 (必须满足 Courant 条件: dx = a * dt)
nx = 51          # 节点数
dx = L / (nx - 1)
dt = dx / a      # dt = 40 / 1000 = 0.04s
nt = int(20.0 / dt) # 模拟 20 秒 (包含5个相长周期)

# 初始化矩阵
H = np.zeros((nt, nx))
V = np.zeros((nt, nx))

# 稳态初始条件
for i in range(nx):
    x = i * dx
    V[0, i] = V0
    # 扣除沿程损失: H(x) = H0 - f * (L/D) * (V0^2 / 2g) * (x/L)
    hf_x = f * (x / D) * (V0**2 / (2 * g))
    H[0, i] = H0 - hf_x

# 阀门开度衰减函数 (Tau)
def tau(t):
    if t <= Tc:
        return 1.0 - t / Tc # 线性关闭
    else:
        return 0.0 # 完全关闭

# 阀门流量系数 Kv
Kv = V0 / np.sqrt(H[0, -1])

# MOC 摩擦项系数 
R_f = f * dx / (2 * g * D)
# 水击阻抗
B = a / g

# 开始时间演进
for n in range(1, nt):
    t = n * dt
    
    # 内部节点计算
    for i in range(1, nx-1):
        # 正特征线 C+方程 (从 i-1, n-1 推导)
        Cp = H[n-1, i-1] + B * V[n-1, i-1] - R_f * V[n-1, i-1] * abs(V[n-1, i-1])
        Cm = H[n-1, i+1] - B * V[n-1, i+1] + R_f * V[n-1, i+1] * abs(V[n-1, i+1])
        
        # 求解 H_i^n 和 V_i^n
        H[n, i] = (Cp + Cm) / 2.0
        V[n, i] = (Cp - Cm) / (2.0 * B)
        
    # 上游边界条件 (水库，水头恒定)
    H[n, 0] = H0
    Cm_us = H[n-1, 1] - B * V[n-1, 1] + R_f * V[n-1, 1] * abs(V[n-1, 1])
    V[n, 0] = (H[n, 0] - Cm_us) / B
    
    # 下游边界条件 (阀门动态关闭)
    Cp_ds = H[n-1, nx-2] + B * V[n-1, nx-2] - R_f * V[n-1, nx-2] * abs(V[n-1, nx-2])
    tau_val = tau(t)
    
    if tau_val <= 0:
        V[n, nx-1] = 0.0
        H[n, nx-1] = Cp_ds
    else:
        # 求解二次方程 V = tau * Kv * sqrt(H), H = Cp - B*V
        # V^2 + B*(tau*Kv)^2 * V - (tau*Kv)^2 * Cp = 0
        K_val = (tau_val * Kv)**2
        Cv = K_val * B / 2.0
        discriminant = Cv**2 + K_val * Cp_ds
        
        if discriminant < 0:
            V_sol = 0
            H_sol = Cp_ds
        else:
            V_sol = -Cv + np.sqrt(discriminant)
            H_sol = Cp_ds - B * V_sol
            
        V[n, nx-1] = V_sol
        H[n, nx-1] = H_sol

# 记录时间序列
time_array = np.arange(nt) * dt
history_valve_H = H[:, -1]
history_valve_V = V[:, -1]
history_mid_H = H[:, int(nx/2)]

# 提取关键点生成表格
df_table = []
snapshots_t = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
for t_snap in snapshots_t:
    idx = int(t_snap / dt)
    if idx >= nt: idx = nt - 1
    df_table.append({
        'Time (s)': t_snap,
        'Valve Opening τ': round(tau(t_snap), 2),
        'Valve Velocity (m/s)': round(V[idx, -1], 2),
        'Valve Pressure Head H (m)': round(H[idx, -1], 2),
        'Midpoint Pressure H (m)': round(H[idx, int(nx/2)], 2)
    })

df = pd.DataFrame(df_table)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "water_hammer_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 绘制时间序列图 (阀门处水锤压力振荡)
plt.figure(figsize=(10, 6))
plt.plot(time_array, history_valve_H, 'r-', linewidth=2, label='Pressure Head at Valve (x=2000m)')
plt.plot(time_array, history_mid_H, 'b--', linewidth=1.5, label='Pressure Head at Midpoint (x=1000m)')
plt.axhline(y=H0, color='k', linestyle=':', label=f'Static Reservoir Head (H0={H0}m)')

plt.xlabel('Time (seconds)', fontsize=12)
plt.ylabel('Pressure Head $H$ (m)', fontsize=12)
plt.title(f'Water Hammer Transients due to Valve Closure (Tc={Tc}s, Tr=4s)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "hammer_pressure_time.png"), dpi=300, bbox_inches='tight')

# 绘制管道内部的包络线 (最大/最小水头)
max_H = np.max(H, axis=0)
min_H = np.min(H, axis=0)
x_coords = np.linspace(0, L, nx)

plt.figure(figsize=(10, 6))
plt.plot(x_coords, max_H, 'r-', linewidth=2, label='Maximum Transient Head Envelope')
plt.plot(x_coords, min_H, 'b-', linewidth=2, label='Minimum Transient Head Envelope')
plt.plot(x_coords, H[0, :], 'k--', linewidth=2, label='Initial Steady HGL')

plt.fill_between(x_coords, min_H, max_H, color='red', alpha=0.1, label='Transient Fluctuation Zone')

plt.xlabel('Distance from Reservoir $x$ (m)', fontsize=12)
plt.ylabel('Pressure Head $H$ (m)', fontsize=12)
plt.title('Water Hammer Pressure Envelopes Along the Pipeline', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "hammer_envelope.png"), dpi=300, bbox_inches='tight')

print("Files generated successfully.")
