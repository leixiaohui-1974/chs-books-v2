import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch11"
os.makedirs(output_dir, exist_ok=True)

# 城市化进程对水文响应的影响 (Impact of Human Activities / Urbanization)
# 模拟同一个流域在“自然森林”状态和“高度城市化”状态下面对相同暴雨的产汇流差异

# 1. 模拟参数设定
t_end = 240 # 分钟
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 降雨事件 (重现期50年的典型雷暴)
rain = np.zeros(N)
rain[20:60] = 80.0 / 60.0 # 80 mm/h 持续40分钟

# 2. 模型参数设定
# 场景 A: 原始森林 (Natural Forest)
# 霍顿下渗参数
f0_nat = 60.0 / 60.0 # 极高的初始下渗能力
fc_nat = 15.0 / 60.0 # 较高的稳定下渗率
k_nat = 0.05
# 坡面汇流参数 (植被阻力大，汇流极慢)
k_route_nat = 120.0

# 场景 B: 高度城市化 (Highly Urbanized - 80% impervious)
f0_urb = 10.0 / 60.0 # 极低的下渗能力 (柏油路面)
fc_urb = 2.0 / 60.0  
k_urb = 0.1
# 坡面汇流参数 (水泥排水沟，汇流极快)
k_route_urb = 5.0

def simulate_catchment(f0, fc, k_decay, k_route):
    # 下渗计算
    infiltration_capacity = np.zeros(N)
    runoff_excess = np.zeros(N)
    t_infil = 0.0
    
    for i in range(N):
        if rain[i] > 0:
            f_cap = fc + (f0 - fc) * np.exp(-k_decay * t_infil)
            t_infil += dt
        else:
            f_cap = fc + (f0 - fc) * np.exp(-k_decay * t_infil)
            t_infil = max(0, t_infil - dt * 0.1)
            
        infiltration_capacity[i] = f_cap
        if rain[i] > f_cap:
            runoff_excess[i] = rain[i] - f_cap
        else:
            runoff_excess[i] = 0.0
            
    # 坡面汇流计算 (线性水库近似)
    S_slope = 0.0
    q_out = np.zeros(N)
    for i in range(1, N):
        inflow = runoff_excess[i-1] * dt
        outflow = (S_slope / k_route) * dt
        S_slope = S_slope + inflow - outflow
        q_out[i] = outflow / dt
        
    return runoff_excess, q_out

# 3. 运行两套场景
excess_nat, q_nat = simulate_catchment(f0_nat, fc_nat, k_nat, k_route_nat)
excess_urb, q_urb = simulate_catchment(f0_urb, fc_urb, k_urb, k_route_urb)

# 转换为常用的 mm/h 方便展示
rain_h = rain * 60.0
q_nat_h = q_nat * 60.0
q_urb_h = q_urb * 60.0

# 4. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 图 A: 产流机制的改变 (Infiltration vs Excess)
ax1.plot(time, rain_h, 'b--', linewidth=2, label='Rainfall Intensity')
ax1.fill_between(time, 0, excess_nat * 60, color='green', alpha=0.3, label='Runoff Generation (Forest)')
ax1.plot(time, excess_urb * 60, 'r-', linewidth=2, label='Runoff Generation (Urban)')
ax1.fill_between(time, excess_nat * 60, excess_urb * 60, color='red', alpha=0.2, label='Excess due to Urbanization')
ax1.set_ylabel('Rate (mm/h)', fontsize=12)
ax1.set_title('Impact of Impervious Surfaces on Runoff Generation', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 图 B: 汇流过程线的异化 (The "Flashy" Urban Hydrograph)
ax2.plot(time, q_nat_h, 'g-', linewidth=3, label='Natural Forest Hydrograph (Slow & Low)')
ax2.plot(time, q_urb_h, 'r-', linewidth=3, label='Urbanized Hydrograph (Fast & High)')

# 标注洪峰移动
peak_urb_time = time[np.argmax(q_urb_h)]
peak_urb_val = np.max(q_urb_h)
peak_nat_time = time[np.argmax(q_nat_h)]
peak_nat_val = np.max(q_nat_h)

ax2.annotate('Urban Peak:\nHigher & Earlier', xy=(peak_urb_time, peak_urb_val), xytext=(peak_urb_time+10, peak_urb_val),
             arrowprops=dict(facecolor='red', shrink=0.05))
ax2.annotate('Natural Peak:\nLower & Delayed', xy=(peak_nat_time, peak_nat_val), xytext=(peak_nat_time+10, peak_nat_val),
             arrowprops=dict(facecolor='green', shrink=0.05))

ax2.set_xlabel('Time (minutes)', fontsize=12)
ax2.set_ylabel('Discharge Equivalent (mm/h)', fontsize=12)
ax2.set_title('Hydrograph Alteration: The "Flash Flood" Effect', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "urbanization_impact_sim.png"), dpi=300, bbox_inches='tight')

# 5. 生成对比表格
# 计算总量 (mm)
total_rain = np.sum(rain) * dt
total_runoff_nat = np.sum(q_nat) * dt
total_runoff_urb = np.sum(q_urb) * dt

# 计算洪水质心 (Center of Mass / Centroid Time)
centroid_nat = np.sum(time * q_nat_h) / np.sum(q_nat_h) if np.sum(q_nat_h) > 0 else 0
centroid_urb = np.sum(time * q_urb_h) / np.sum(q_urb_h) if np.sum(q_urb_h) > 0 else 0

history = [
    {'Metric': 'Peak Discharge (mm/h)', 'Natural Forest': round(peak_nat_val, 1), 'Urbanized Basin': round(peak_urb_val, 1), 'Impact': f"Increased by {round(peak_urb_val / peak_nat_val, 1)}X"},
    {'Metric': 'Hydrograph Centroid (min)', 'Natural Forest': int(centroid_nat), 'Urbanized Basin': int(centroid_urb), 'Impact': f"Advanced by {int(centroid_nat - centroid_urb)} min"},
    {'Metric': 'Total Runoff Volume (mm)', 'Natural Forest': round(total_runoff_nat, 1), 'Urbanized Basin': round(total_runoff_urb, 1), 'Impact': f"+{round(total_runoff_urb - total_runoff_nat, 1)} mm"},
    {'Metric': 'Runoff Coefficient (R/P)', 'Natural Forest': f"{total_runoff_nat/total_rain*100:.1f}%", 'Urbanized Basin': f"{total_runoff_urb/total_rain*100:.1f}%", 'Impact': 'More water lost to drains'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "urbanization_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 生成占位图
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch11: Urbanization Impact", "Diagram splitting a watershed in half. Left side is dense forest absorbing rain. Right side is concrete city with rain bouncing off. Shows two hydrograph lines: a slow flat curve for forest, and a terrifying sharp spike for the city.")

print("Files generated successfully.")
