import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import fsolve

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch09"
os.makedirs(output_dir, exist_ok=True)

# 倒虹吸管水力计算 (Inverted Siphon)
# 稳态能量守恒与局部水头损失

# 参数设置
Q = 12.0          # 设计流量 m^3/s
L = 800.0         # 倒虹吸管总长 m
D = 2.5           # 管道内径 m
n = 0.013         # 混凝土管糙率
g = 9.81          # 重力加速度

# 局部损失系数
K_entrance = 0.5  # 进口损失系数
K_exit = 1.0      # 出口损失系数
K_bends = 2 * 0.2 # 两个弯头损失系数

# 管道几何参数
A = np.pi * (D**2) / 4.0
P = np.pi * D
R = A / P
V = Q / A

# 沿程摩擦损失 (达西-魏斯巴赫公式或曼宁公式变形)
# 这里使用曼宁公式的变形 h_f = (n^2 * V^2 * L) / (R^(4/3))
hf_friction = (n**2 * V**2 * L) / (R**(4/3))

# 局部水头损失 h_m = K * (V^2 / 2g)
hm_entrance = K_entrance * (V**2 / (2*g))
hm_exit = K_exit * (V**2 / (2*g))
hm_bends = K_bends * (V**2 / (2*g))
hm_total = hm_entrance + hm_exit + hm_bends

# 总水头损失
H_total_loss = hf_friction + hm_total

# 绘制不同流量下的水头损失关系曲线
Q_values = np.linspace(2.0, 20.0, 50)
hf_list = []
hm_list = []
H_total_list = []

for q in Q_values:
    v_q = q / A
    hf_q = (n**2 * v_q**2 * L) / (R**(4/3))
    hm_q = (K_entrance + K_exit + K_bends) * (v_q**2 / (2*g))
    hf_list.append(hf_q)
    hm_list.append(hm_q)
    H_total_list.append(hf_q + hm_q)

# 制作表格数据
Q_table = [5.0, 8.0, 10.0, 12.0, 15.0, 18.0]
history = []
for q in Q_table:
    v_q = q / A
    hf_q = (n**2 * v_q**2 * L) / (R**(4/3))
    hm_q = (K_entrance + K_exit + K_bends) * (v_q**2 / (2*g))
    history.append({
        'Discharge Q (m³/s)': round(q, 1),
        'Velocity V (m/s)': round(v_q, 2),
        'Friction Loss hf (m)': round(hf_q, 3),
        'Minor Loss hm (m)': round(hm_q, 3),
        'Total Head Loss H (m)': round(hf_q + hm_q, 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "siphon_loss_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# Plotting Head Loss Curve
plt.figure(figsize=(9, 6))

plt.plot(Q_values, H_total_list, 'k-', linewidth=3, label='Total Head Loss $\Delta H$')
plt.plot(Q_values, hf_list, 'b--', linewidth=2, label='Friction Loss $h_f$')
plt.plot(Q_values, hm_list, 'r-.', linewidth=2, label='Minor Losses $h_m$')

plt.axvline(x=Q, color='g', linestyle=':', label=f'Design Discharge Q={Q} m³/s')
plt.plot(Q, H_total_loss, 'go', markersize=8)

plt.xlabel('Discharge $Q$ ($m^3/s$)', fontsize=12)
plt.ylabel('Head Loss (m)', fontsize=12)
plt.title(f'Inverted Siphon Head Loss vs Discharge (L={L}m, D={D}m)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

plt.savefig(os.path.join(output_dir, "siphon_loss_curve.png"), dpi=300, bbox_inches='tight')

# 画一个倒虹吸的水力坡度线示意图 (HGL & EGL)
plt.figure(figsize=(12, 6))
# 空间坐标: 0(进口), 100(下沉), 700(平移末), 800(出口)
x_coords = [0, 50, 750, 800]
# 管底高程
z_pipe = [100.0, 50.0, 50.0, 95.0]
# 水面高程(EGL)
z_egl = [100.0 + D + H_total_loss, 
         100.0 + D + H_total_loss - hm_entrance - hf_friction*(50/800),
         100.0 + D + H_total_loss - hm_entrance - hm_bends/2 - hf_friction*(750/800),
         100.0 + D] # 假设下游水位恰好淹没管口

# 水力坡度线 (HGL = EGL - V^2/2g)
v_head = V**2 / (2*g)
z_hgl = [z - v_head for z in z_egl]

plt.plot(x_coords, z_pipe, 'k-', linewidth=5, label='Inverted Siphon Pipe')
plt.plot(x_coords, z_egl, 'r-', linewidth=2, label='Energy Grade Line (EGL)')
plt.plot(x_coords, z_hgl, 'b--', linewidth=2, label='Hydraulic Grade Line (HGL)')

plt.fill_between(x_coords, z_pipe, z_hgl, color='cyan', alpha=0.2, label='Pressurized Water')

plt.xlabel('Distance $x$ (m)', fontsize=12)
plt.ylabel('Elevation $Z$ (m)', fontsize=12)
plt.title('Energy Grade Line and Hydraulic Grade Line for Inverted Siphon', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

plt.savefig(os.path.join(output_dir, "siphon_hgl_egl.png"), dpi=300, bbox_inches='tight')

print("Files generated successfully.")
