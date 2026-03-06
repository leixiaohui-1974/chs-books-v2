import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 渠道和水流参数
Q = 20.0         # 流量 m^3/s
b = 5.0          # 底宽 m
m = 1.0          # 边坡系数
n = 0.015        # 糙率
S0 = 0.001       # 渠道底坡
g = 9.81         # 重力加速度

# 下游控制水深 (拦河坝造成的雍水)
h_downstream = 3.5 # m
L_total = 2000     # 计算总长度 m
dx = 50            # 空间步长 m (绝对值)

def calc_geometric(h):
    A = (b + m * h) * h
    P = b + 2 * h * np.sqrt(1 + m**2)
    R = A / P
    T = b + 2 * m * h # 水面宽度
    return A, P, R, T

# 使用牛顿法计算正常水深 hn (均匀流)
def solve_hn():
    hn = 1.0
    for _ in range(50):
        A, P, R, T = calc_geometric(hn)
        Q_calc = (1/n) * A * (R**(2/3)) * np.sqrt(S0)
        f = Q_calc - Q
        if abs(f) < 1e-5: return hn
        # 数值导数
        dh = 0.001
        A_d, P_d, R_d, _ = calc_geometric(hn + dh)
        Q_calc_d = (1/n) * A_d * (R_d**(2/3)) * np.sqrt(S0)
        df = (Q_calc_d - Q_calc) / dh
        hn = hn - f / df
    return hn

# 计算临界水深 hc
def solve_hc():
    hc = 1.0
    for _ in range(50):
        A, _, _, T = calc_geometric(hc)
        f = Q**2 * T / (g * A**3) - 1.0
        if abs(f) < 1e-5: return hc
        dh = 0.001
        A_d, _, _, T_d = calc_geometric(hc + dh)
        f_d = Q**2 * T_d / (g * A_d**3) - 1.0
        df = (f_d - f) / dh
        hc = hc - f / df
    return hc

hn = solve_hn()
hc = solve_hc()

# 渐变流微分方程求解 (标准步长法 Standard Step Method)
# 由于是 M1 型壅水曲线，控制断面在下游，计算从下游向上游推进
x_points = [L_total]
h_points = [h_downstream]

x_current = L_total
h_current = h_downstream

history = []
history.append({
    'Distance x (m)': round(x_current, 1),
    'Depth h (m)': round(h_current, 3),
    'Water Elev Z (m)': round(h_current + x_current * S0, 3)
})

while x_current > 0:
    A1, P1, R1, T1 = calc_geometric(h_current)
    V1 = Q / A1
    E1 = h_current + V1**2 / (2 * g)
    Sf1 = (n**2 * V1**2) / (R1**(4/3))
    
    # 预测上游一个步长的水深 (上游水深应该比下游浅，逐渐趋近于 hn)
    h_next = h_current - 0.01 
    x_next = x_current - dx
    
    for _ in range(20): # 迭代求解上游水深
        A2, P2, R2, T2 = calc_geometric(h_next)
        V2 = Q / A2
        E2 = h_next + V2**2 / (2 * g)
        Sf2 = (n**2 * V2**2) / (R2**(4/3))
        
        Sf_avg = (Sf1 + Sf2) / 2.0
        
        # 能量方程平衡: 上游能量 = 下游能量 + 沿程水头损失
        # 上游总水头: Z2 + E2 (其中 Z2 = Z1 + S0 * dx)
        # 下游总水头: Z1 + E1
        # (Z1 + S0*dx) + E2 = Z1 + E1 + Sf_avg * dx
        # E2 = E1 - S0*dx + Sf_avg*dx
        target_E2 = E1 - S0 * dx + Sf_avg * dx
        error = E2 - target_E2
        
        if abs(error) < 1e-5:
            break
        # 简单修正
        h_next = h_next - error * 0.8
        
    x_current = x_next
    h_current = h_next
    x_points.append(x_current)
    h_points.append(h_current)
    
    if int(x_current) % 400 == 0:
        history.append({
            'Distance x (m)': round(x_current, 1),
            'Depth h (m)': round(h_current, 3),
            'Water Elev Z (m)': round(h_current + x_current * S0, 3)
        })

# 翻转数据以符合从上游到下游的顺序
x_points = x_points[::-1]
h_points = h_points[::-1]
history = history[::-1]

# 计算渠底高程和正常/临界水深高程 (设定下游 x=2000 处底高程为 0)
z_bottom = [(L_total - x) * S0 for x in x_points]
z_water = [z + h for z, h in zip(z_bottom, h_points)]
z_hn = [z + hn for z in z_bottom]
z_hc = [z + hc for z in z_bottom]

df = pd.DataFrame(history)
# Update history with correct Z
for i in range(len(history)):
    x_val = history[i]['Distance x (m)']
    h_val = history[i]['Depth h (m)']
    history[i]['Water Elev Z (m)'] = round((L_total - x_val) * S0 + h_val, 3)

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "backwater_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# Plotting M1 Curve
plt.figure(figsize=(10, 6))

plt.plot(x_points, z_water, 'b-', linewidth=2.5, label='M1 Water Surface Profile')
plt.plot(x_points, z_bottom, 'k-', linewidth=3, label='Channel Bottom')
plt.plot(x_points, z_hn, 'g--', alpha=0.7, label=f'Normal Depth ($h_n$={hn:.2f}m)')
plt.plot(x_points, z_hc, 'r:', alpha=0.7, label=f'Critical Depth ($h_c$={hc:.2f}m)')

# 画一个简单的拦河坝示意
plt.fill_between([L_total, L_total+50], [0, 0], [z_bottom[-1]+h_downstream, z_bottom[-1]+h_downstream], color='gray', alpha=0.5, label='Dam/Weir')

plt.xlabel('Distance $x$ (m)', fontsize=12)
plt.ylabel('Elevation $Z$ (m)', fontsize=12)
plt.title(f'M1 Backwater Curve Profile ($S_0={S0}$)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.xlim(0, L_total+50)

# Flip x-axis so flow is from left to right (upstream at 0, downstream at 2000)
# Actually, the data is already upstream=0, downstream=2000. So the dam is at right side.
# Let's ensure the X values really go from 0 to 2000 in the data arrays.


plt.savefig(os.path.join(output_dir, "m1_profile_curve.png"), dpi=300, bbox_inches='tight')
print(f"Files generated successfully. hn={hn:.3f}, hc={hc:.3f}")
