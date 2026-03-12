import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import math

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Hydrology_Book\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 核心水文能力仿真：降雨径流计算、河道汇流与预警 (Rainfall-Runoff, Routing & Warning)
# 场景：展示一个典型小流域从“天上下雨”到“地上产流”，再到“河道坦化演进”，最后触发“城市预警”的全生命周期。

# 1. 模拟环境与输入
t_end = 240 # 分钟
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 降雨事件 (强对流暴雨)
rain = np.zeros(N)
rain[20:60] = 50.0 / 60.0 # 50 mm/h 持续 40 分钟

# 2. 产流计算 (Runoff Generation) - 采用极其经典的 SCS 曲线数法 (SCS-CN Method) 简化版
CN = 80.0 # 曲线数 (反映土壤和植被，越大越容易产流)
S_storage = (25400.0 / CN) - 254.0 # 最大潜在蓄水量 mm
Ia = 0.2 * S_storage # 初损量 mm

accumulated_rain = np.cumsum(rain * dt) # 累积降雨量 P
accumulated_runoff = np.zeros(N)

for i in range(N):
    P = accumulated_rain[i]
    if P > Ia:
        # SCS 公式：Q = (P - Ia)^2 / (P - Ia + S)
        accumulated_runoff[i] = (P - Ia)**2 / (P - Ia + S_storage)
    else:
        accumulated_runoff[i] = 0.0

# 差分求出每个时刻的净雨 (产流率 mm/min)
net_rain = np.zeros(N)
net_rain[1:] = np.diff(accumulated_runoff) / dt

# 3. 坡面与河网汇流 (Routing) - 采用纳什瞬时单位线 (Nash IUH)
n_reservoirs = 3
k_routing = 10.0 # 每个水库的滞后时间常数
# 利用伽马分布解析解生成单位线
u_t = (time / k_routing)**(n_reservoirs - 1) * np.exp(-time / k_routing) / (k_routing * math.factorial(n_reservoirs - 1))
u_t = u_t / np.sum(u_t) # 归一化

# 卷积运算得到出口流量过程线 (m^3/s)
catchment_area = 5.0 # 流域面积 5 km^2
# 净雨 mm/min 转换为 m/s 乘上 面积 m^2
volume_in_m3_s = net_rain * (1/1000) * (catchment_area * 1e6) / 60.0

Q_outlet = np.convolve(volume_in_m3_s, u_t)[:N]

# 4. 预警触发 (Event Detection & What-if)
warning_threshold = 20.0 # m^3/s
danger_threshold = 30.0

# What-if 场景：如果这不是森林(CN=80)，而是完全硬化的城市(CN=95)
CN_urban = 95.0
S_urb = (25400.0 / CN_urban) - 254.0
Ia_urb = 0.2 * S_urb

acc_runoff_urb = np.zeros(N)
for i in range(N):
    P = accumulated_rain[i]
    if P > Ia_urb:
        acc_runoff_urb[i] = (P - Ia_urb)**2 / (P - Ia_urb + S_urb)

net_rain_urb = np.zeros(N)
net_rain_urb[1:] = np.diff(acc_runoff_urb) / dt
vol_urb = net_rain_urb * (1/1000) * (catchment_area * 1e6) / 60.0
# 城市汇流速度极快，n=2, k=5
u_t_urb = (time / 5.0)**(2 - 1) * np.exp(-time / 5.0) / (5.0 * math.factorial(2 - 1))
u_t_urb = u_t_urb / np.sum(u_t_urb)
Q_outlet_urban = np.convolve(vol_urb, u_t_urb)[:N]

# 5. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# A. 天空降雨与地面产流剥离 (SCS-CN)
ax1.plot(time, accumulated_rain, 'b--', linewidth=2, label='Accumulated Rainfall $P$ (Sky)')
ax1.plot(time, accumulated_runoff, 'g-', linewidth=3, label='Accumulated Runoff $Q$ (Natural Basin, CN=80)')
ax1.plot(time, acc_runoff_urb, 'r-', linewidth=2, label='Accumulated Runoff $Q$ (Urban Basin, CN=95)')

ax1.fill_between(time, accumulated_runoff, accumulated_rain, color='gray', alpha=0.2, label='Infiltration & Loss (Soil Sponge)')

ax1.set_ylabel('Depth (mm)', fontsize=12)
ax1.set_title('Rainfall-Runoff Transformation (SCS-CN Core Capability)', fontsize=14)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注初损
ax1.annotate('Initial Abstraction $I_a$\n(Trees & dry soil absorb first drops)', 
             xy=(25, accumulated_rain[25]), xytext=(40, 5),
             arrowprops=dict(facecolor='black', shrink=0.05))

# B. 汇流演进与预警红线 (Routing & Warning)
ax2.plot(time, Q_outlet, 'g-', linewidth=3, label='Streamflow (Natural Basin)')
ax2.plot(time, Q_outlet_urban, 'r--', linewidth=2, label='Streamflow (What-if: Urbanization)')

ax2.axhline(warning_threshold, color='orange', linestyle=':', linewidth=2, label='Yellow Warning Line')
ax2.axhline(danger_threshold, color='red', linestyle='--', linewidth=2, label='Red Danger Line')

# 红色填充标出灾难时间段
ax2.fill_between(time, danger_threshold, Q_outlet_urban, where=(Q_outlet_urban > danger_threshold), color='red', alpha=0.3, label='Flash Flood Disaster')

ax2.set_xlabel('Time (Minutes)', fontsize=12)
ax2.set_ylabel('Discharge $Q$ ($m^3/s$)', fontsize=12)
ax2.set_title('River Routing and Scenario What-if (Urbanization Flash Flood)', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "core_hydrology_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 统计核心指标
history = [
    {'Metric': 'Total Runoff Generated (mm)', 'Natural (CN=80)': round(accumulated_runoff[-1], 1), 'What-if Urban (CN=95)': round(acc_runoff_urb[-1], 1), 'Impact': 'Urbanization blocks infiltration'},
    {'Metric': 'Peak Discharge ($m^3/s$)', 'Natural (CN=80)': round(np.max(Q_outlet), 1), 'What-if Urban (CN=95)': round(np.max(Q_outlet_urban), 1), 'Impact': 'Violent flash flood peak'},
    {'Metric': 'Time to Peak (min)', 'Natural (CN=80)': time[np.argmax(Q_outlet)], 'What-if Urban (CN=95)': time[np.argmax(Q_outlet_urban)], 'Impact': 'Zero reaction time for city'},
    {'Metric': 'Red Warning Status', 'Natural (CN=80)': 'Safe', 'What-if Urban (CN=95)': 'Triggered!', 'Impact': 'Requires immediate dispatch'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "hydrology_features_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: Core Hydrology Features", "Diagram showing rain clouds pouring water on two landscapes. Top landscape is a natural forest where roots absorb water. Bottom landscape is a concrete city where water bounces off, forming a violent flash flood that triggers red warning sirens.")

print("Files generated successfully.")
