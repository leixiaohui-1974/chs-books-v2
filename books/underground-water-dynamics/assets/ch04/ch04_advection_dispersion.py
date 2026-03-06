import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\underground-water-dynamics\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 地下水污染对流弥散模拟 (Advection-Dispersion Equation)
# 1D 解析解：一维均匀流场中瞬时点源的浓度分布 (Ogata-Banks 模型的变体)
# 浓度 C(x,t) = (M / sqrt(4 * pi * D_L * t)) * exp( -(x - v*t)^2 / (4 * D_L * t) )

# 参数设置
v_darcy = 0.5     # 达西流速 m/d
n_porosity = 0.25 # 有效孔隙度
v_pore = v_darcy / n_porosity # 真实孔隙流速 (平流速度) m/d

alpha_L = 10.0    # 纵向弥散度 (Longitudinal Dispersivity) m
D_L = alpha_L * v_pore # 纵向水动力弥散系数 m^2/d

M = 1000.0        # 瞬时注入污染物的总量 (单位面积质量) kg/m^2

def calculate_concentration(x, t):
    if t == 0: return 0.0
    # 瞬时点源一维解析解
    coef = M / np.sqrt(4 * np.pi * D_L * t)
    exponent = -((x - v_pore * t)**2) / (4 * D_L * t)
    return coef * np.exp(exponent)

# 1. 模拟空间浓度分布 (固定时间，不同距离)
x_values = np.linspace(-100, 1500, 500)
times_to_plot = [50, 200, 500] # 天
time_labels = ['50 Days', '200 Days', '500 Days']

plt.figure(figsize=(10, 6))

for t, label in zip(times_to_plot, time_labels):
    c_values = [calculate_concentration(x, t) for x in x_values]
    plt.plot(x_values, c_values, linewidth=2.5, label=f't = {label}')
    
    # 标出质心位置
    center_x = v_pore * t
    peak_c = calculate_concentration(center_x, t)
    plt.plot(center_x, peak_c, 'ko', markersize=6)
    plt.vlines(x=center_x, ymin=0, ymax=peak_c, colors='k', linestyles=':')

plt.xlabel('Distance from Source $x$ (m)', fontsize=12)
plt.ylabel('Concentration $C$ ($kg/m^3$)', fontsize=12)
plt.title('1D Pollutant Plume Transport (Advection-Dispersion)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

plt.savefig(os.path.join(output_dir, "plume_spatial_distribution.png"), dpi=300, bbox_inches='tight')

# 2. 模拟观测井的时间序列浓度 (Breakthrough Curve, 穿透曲线)
x_obs = 600.0 # 观测井位于下游 600m 处
time_array = np.linspace(1, 800, 400) # 观察 800 天
c_obs_values = [calculate_concentration(x_obs, t) for t in time_array]

plt.figure(figsize=(10, 6))
plt.plot(time_array, c_obs_values, 'r-', linewidth=3, label=f'Observation Well at $x={x_obs}m$')

# 标出平流到达时间 t = x / v_pore
t_advection = x_obs / v_pore
plt.axvline(x=t_advection, color='k', linestyle='--', label=f'Pure Advection Arrival ($t={t_advection}$ d)')

plt.xlabel('Time $t$ (Days)', fontsize=12)
plt.ylabel('Concentration $C$ ($kg/m^3$)', fontsize=12)
plt.title('Breakthrough Curve at Observation Well', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "breakthrough_curve.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
t_table = [50, 150, 300, 500]

for t in t_table:
    center = v_pore * t
    peak = calculate_concentration(center, t)
    
    # 计算羽流宽度 (定义为浓度大于峰值 1% 的区域)
    # exp(-x^2 / 4Dt) = 0.01 => x^2 = -4Dt * ln(0.01) => x = sqrt(-4Dt * ln(0.01))
    half_width = np.sqrt(-4 * D_L * t * np.log(0.01))
    
    history.append({
        'Time (Days)': t,
        'Plume Center X (m)': round(center, 1),
        'Peak Concentration C_max': round(peak, 2),
        'Plume Spread Width (m)': round(2 * half_width, 1)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "transport_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
