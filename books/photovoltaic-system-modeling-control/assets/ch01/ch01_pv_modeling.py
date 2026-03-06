import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\photovoltaic-system-modeling-control\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 光伏电池物理建模 (Photovoltaic Cell Physical Modeling)
# 模拟单体光伏电池在不同光照(Irradiance)和温度(Temperature)下的 I-V 和 P-V 曲线

# 1. 光伏电池物理参数 (基于经典的单二极管模型 Single Diode Model)
# 标准测试条件 (STC: 1000 W/m^2, 25°C)
k = 1.380649e-23  # 玻尔兹曼常数 J/K
q = 1.60217663e-19 # 电子电荷 C
T_stc = 25 + 273.15 # 298.15 K
G_stc = 1000.0 # W/m^2

# 某商业多晶硅电池板参数
I_sc = 8.21    # 短路电流 A (STC)
V_oc = 32.9    # 开路电压 V (STC)
I_mp = 7.61    # 最大功率点电流 A (STC)
V_mp = 26.3    # 最大功率点电压 V (STC)
K_i = 0.0032   # 电流温度系数 A/K
K_v = -0.123   # 电压温度系数 V/K
N_s = 54       # 串联电池片数
A_ideality = 1.3 # 二极管理想因子

# 为了简化非线性方程求解，我们使用一种显式的近似方法计算 I = f(V)
def calculate_pv_curve(G, T_celsius):
    T = T_celsius + 273.15
    dT = T - T_stc
    
    # 1. 计算光生电流 (Photocurrent)
    I_ph = (I_sc + K_i * dT) * (G / G_stc)
    
    # 2. 计算反向饱和电流 (Reverse Saturation Current)
    # 简化公式，基于 V_oc 的温度漂移
    V_oc_T = V_oc + K_v * dT
    V_t = N_s * k * T / q  # 热电压
    I_rs = I_ph / (np.exp(V_oc_T / (A_ideality * V_t)) - 1.0)
    
    # 3. 扫描电压 V 生成 I-V 和 P-V 曲线
    V_array = np.linspace(0, V_oc_T, 100)
    I_array = np.zeros_like(V_array)
    P_array = np.zeros_like(V_array)
    
    # 忽略串联电阻 Rs 和并联电阻 Rsh 的理想化方程: I = I_ph - I_rs * (exp(V / (A*Vt)) - 1)
    for i, V in enumerate(V_array):
        # 如果包含Rs, Rsh，这是一个隐式方程，需要牛顿迭代。这里为了速度使用理想二极管公式
        I_current = I_ph - I_rs * (np.exp(V / (A_ideality * V_t)) - 1.0)
        I_current = max(0.0, I_current) # 物理限制
        I_array[i] = I_current
        P_array[i] = V * I_current
        
    return V_array, I_array, P_array

# 2. 模拟不同光照强度 (G) 下的表现 (恒温 25°C)
G_levels = [200, 400, 600, 800, 1000] # W/m^2
T_const = 25.0 # °C

# 3. 模拟不同温度 (T) 下的表现 (恒定光照 1000 W/m^2)
T_levels = [10, 25, 40, 55, 70] # °C
G_const = 1000.0

# 4. 绘图
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

# A. 变光照 (I-V)
for G in G_levels:
    V, I, P = calculate_pv_curve(G, T_const)
    ax1.plot(V, I, linewidth=2, label=f'G={G} $W/m^2$')
ax1.set_xlabel('Voltage (V)', fontsize=12)
ax1.set_ylabel('Current (A)', fontsize=12)
ax1.set_title(f'I-V Curve varying Irradiance (T={T_const}°C)', fontsize=14)
ax1.legend()
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 变光照 (P-V) 及其 MPP 连线
mpp_v_g = []
mpp_p_g = []
for G in G_levels:
    V, I, P = calculate_pv_curve(G, T_const)
    ax2.plot(V, P, linewidth=2, label=f'G={G} $W/m^2$')
    # 记录最大功率点 (MPP)
    idx_max = np.argmax(P)
    mpp_v_g.append(V[idx_max])
    mpp_p_g.append(P[idx_max])
    ax2.plot(V[idx_max], P[idx_max], 'k*', markersize=8)

ax2.plot(mpp_v_g, mpp_p_g, 'k--', linewidth=1.5, alpha=0.5, label='MPP Trajectory')
ax2.set_xlabel('Voltage (V)', fontsize=12)
ax2.set_ylabel('Power (W)', fontsize=12)
ax2.set_title('P-V Curve varying Irradiance (Power tracking)', fontsize=14)
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 变温度 (I-V)
for T in T_levels:
    V, I, P = calculate_pv_curve(G_const, T)
    ax3.plot(V, I, linewidth=2, label=f'T={T}°C')
ax3.set_xlabel('Voltage (V)', fontsize=12)
ax3.set_ylabel('Current (A)', fontsize=12)
ax3.set_title(f'I-V Curve varying Temperature (G={G_const} $W/m^2$)', fontsize=14)
ax3.legend()
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.annotate('Voltage severely\ndrops with heat', xy=(25, 2), xytext=(15, 2.5),
             arrowprops=dict(facecolor='red', shrink=0.05))

# D. 变温度 (P-V) 及其 MPP 连线
mpp_v_t = []
mpp_p_t = []
for T in T_levels:
    V, I, P = calculate_pv_curve(G_const, T)
    ax4.plot(V, P, linewidth=2, label=f'T={T}°C')
    idx_max = np.argmax(P)
    mpp_v_t.append(V[idx_max])
    mpp_p_t.append(P[idx_max])
    ax4.plot(V[idx_max], P[idx_max], 'k*', markersize=8)

ax4.plot(mpp_v_t, mpp_p_t, 'k--', linewidth=1.5, alpha=0.5, label='MPP Trajectory')
ax4.set_xlabel('Voltage (V)', fontsize=12)
ax4.set_ylabel('Power (W)', fontsize=12)
ax4.set_title('P-V Curve varying Temperature (Thermal loss)', fontsize=14)
ax4.legend()
ax4.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "pv_characteristics_sim.png"), dpi=300, bbox_inches='tight')

# 5. 生成极值追踪表格
history = []
# 选取几个典型状态
states = [(1000, 25, "STC (Ideal)"), (1000, 70, "Hot Summer Desert"), (200, 25, "Heavy Cloud")]
for G, T, desc in states:
    V, I, P = calculate_pv_curve(G, T)
    idx = np.argmax(P)
    history.append({
        'Environment': desc,
        'Irradiance ($W/m^2$)': G,
        'Temp (°C)': T,
        'Max Power (W)': round(P[idx], 1),
        'Optimal Voltage $V_{mp}$': round(V[idx], 1),
        'Short Circuit $I_{sc}$': round(I[0], 2),
        'Open Circuit $V_{oc}$': round(V[-1], 1)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "pv_physics_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 占位图生成
def create_schematic(path, title, description):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (1024, 512), color=(240, 245, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 1014, 502], outline=(100, 100, 150), width=3)
    try: font_title = ImageFont.truetype('arial.ttf', 36); font_desc = ImageFont.truetype('arial.ttf', 24)
    except: font_title = ImageFont.load_default(); font_desc = ImageFont.load_default()
    d.text((40, 40), title, fill=(20, 40, 100), font=font_title)
    
    words = description.split()
    lines, current_line = [], []
    for word in words:
        current_line.append(word)
        if len(current_line) > 12: lines.append(' '.join(current_line)); current_line = []
    if current_line: lines.append(' '.join(current_line))
        
    y_offset = 120
    for line in lines:
        d.text((40, y_offset), line, fill=(50, 50, 50), font=font_desc)
        y_offset += 35
    img.save(path)

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch01: Photovoltaic Cell Physics", "Diagram showing a semiconductor PN junction inside a solar panel. Photons from the sun hit the silicon, knocking electrons loose to create a photocurrent (I_ph). A parallel diode shows the internal current leakage mechanism.")

print("Files generated successfully.")
