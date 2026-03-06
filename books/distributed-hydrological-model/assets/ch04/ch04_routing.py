import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 坡面汇流与河网汇流 (Kinematic Wave & Muskingum Method)
# 模拟一场暴雨如何在山坡上汇集成流(运动波法)，并进入河道进行坦化演进(马斯金根法)

# 1. 模拟参数设定
t_end = 240 # 模拟时间 240 分钟
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 假设我们在第2章算出来的净雨 (Net Rainfall, 产流量) mm/h
# 将其转换为 mm/min = (L/m^2)/min
net_rain = np.zeros(N)
net_rain[10:40] = 30.0 / 60.0 

# 2. 坡面汇流：一维运动波模型 (Kinematic Wave Approximation)
# 连续性方程: dh/dt + dq/dx = R(t)
# 动量方程 (简化为稳态流关系): q = alpha * h^m
# 采用简化的集总式坡面响应(线性水库法)来逼近
# 坡面响应可以用一个具有非线性/线性出流特性的水库来模拟
k_slope = 15.0 # 坡面滞后时间常数 (分钟)

q_slope = np.zeros(N) # 坡面出流 (m^3/s) 假设坡面面积 A_catchment
A_catchment = 1.0 * 1e6 # 1 km^2 面积

# 简化的坡面线性水库汇流 (Nash Unit Hydrograph 概念)
S_slope = 0.0 # 坡面蓄水量 (mm)
for i in range(1, N):
    inflow_mm = net_rain[i-1] * dt
    # q = S / k (线性关系)
    outflow_mm = (S_slope / k_slope) * dt
    S_slope = S_slope + inflow_mm - outflow_mm
    
    # 转换为物理流量 m^3/s: mm/min * (1m/1000mm) * A_catchment / 60s
    q_slope[i] = (outflow_mm / dt) * (1/1000) * A_catchment / 60.0

# 3. 河网汇流：马斯金根法 (Muskingum Method)
# 河道汇流会对坡面流产生的洪峰进行再次延迟和削峰坦化
# 参数: K (传播时间), X (流量比重系数, 0~0.5)
K_musk = 20.0 # 河道传播时间 20 分钟
X_musk = 0.2  # 典型的自然河道

# 计算马斯金根参数 C0, C1, C2
# q_out[i] = C0*I[i] + C1*I[i-1] + C2*q_out[i-1]
denominator = K_musk * (1 - X_musk) + 0.5 * dt
C0 = (-K_musk * X_musk + 0.5 * dt) / denominator
C1 = (K_musk * X_musk + 0.5 * dt) / denominator
C2 = (K_musk * (1 - X_musk) - 0.5 * dt) / denominator

q_channel = np.zeros(N) # 河道末端出流
q_channel[0] = 0.0

for i in range(1, N):
    q_channel[i] = C0 * q_slope[i] + C1 * q_slope[i-1] + C2 * q_channel[i-1]
    q_channel[i] = max(q_channel[i], 0.0) # 防止数值负数

# 4. 绘图对比
plt.figure(figsize=(10, 6))

# 画净雨过程 (倒置条形图，习惯画法)
ax1 = plt.gca()
ax2 = ax1.twinx()

ax2.bar(time, net_rain * 60, width=dt, color='gray', alpha=0.3, label='Net Rainfall (mm/h)')
ax2.set_ylim(100, 0) # 倒置y轴
ax2.set_ylabel('Net Rainfall (mm/h)', fontsize=12)

# 画流量过程线 (Hydrographs)
ax1.plot(time, q_slope, 'r-.', linewidth=2.5, label='Slope Runoff (Kinematic/Nash)')
ax1.plot(time, q_channel, 'b-', linewidth=3, label=f'Channel Outlet (Muskingum K={K_musk}, X={X_musk})')

ax1.set_xlabel('Time (minutes)', fontsize=12)
ax1.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax1.set_title('Rainfall-Runoff Routing: From Hillslope to Channel', fontsize=14)

# 合并图例
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')
ax1.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "routing_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 找洪峰
peak_rain_time = 25 # 降雨中点
peak_slope_idx = np.argmax(q_slope)
peak_channel_idx = np.argmax(q_channel)

history = [
    {'Process Stage': '1. Net Rainfall (Source)', 'Peak Time (min)': peak_rain_time, 'Peak Value': f"{30.0} mm/h", 'Delay from previous (min)': 0},
    {'Process Stage': '2. Slope Routing (Catchment)', 'Peak Time (min)': time[peak_slope_idx], 'Peak Value': f"{q_slope[peak_slope_idx]:.2f} m³/s", 'Delay from previous (min)': time[peak_slope_idx] - peak_rain_time},
    {'Process Stage': '3. Channel Routing (Outlet)', 'Peak Time (min)': time[peak_channel_idx], 'Peak Value': f"{q_channel[peak_channel_idx]:.2f} m³/s", 'Delay from previous (min)': time[peak_channel_idx] - time[peak_slope_idx]}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "routing_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
