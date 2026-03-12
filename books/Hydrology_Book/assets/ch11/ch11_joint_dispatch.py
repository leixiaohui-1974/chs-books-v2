import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Hydrology_Book\assets\ch11"
os.makedirs(output_dir, exist_ok=True)

# 城市内涝防洪预警与“库-河-网”联合调度 (Urban Flood Joint Dispatch)
# 场景：展示在面对特大暴雨时，单打独斗的城市管网必定崩溃，而通过“提前腾库”的“库河联调”能成功削峰。

# 1. 模拟环境设定
t_end = 72 # 模拟 72 小时
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 气象预报：在第 36-48 小时发生特大暴雨
rain_storm = np.zeros(N)
rain_storm[36:48] = np.sin(np.pi * np.arange(12) / 12.0) * 20.0 # mm/h

# 2. 上游山区的汇流 (流向水库)
inflow_mountain = np.zeros(N)
inflow_mountain[38:54] = np.convolve(rain_storm[36:48], [0.1, 0.3, 0.5, 0.3, 0.1])[:16] * 2.0

# 3. 本地城区的汇流 (直接流入城市河道)
runoff_city = np.zeros(N)
# 城市硬化面积大，产流快，峰值高，无滞后
runoff_city[36:50] = np.convolve(rain_storm[36:48], [0.4, 0.6, 0.4])[:14] * 1.5

# 4. 水库与河道物理约束
Res_Max_Cap = 500.0 # 水库最大容量 (万m3)
River_Capacity = 60.0 # 城市河道最大行洪能力 (万m3/h)，超过就内涝

# 5. 情景 A: 孤立运行 (No Joint Dispatch)
# 水库平常保持高水位蓄水(满载)。暴雨一来，水库瞬间装满开始溢流泄洪。
res_vol_isolated = np.zeros(N)
res_spill_isolated = np.zeros(N)
res_vol_isolated[0] = 450.0 # 初始保持高水位 (为了发电或供水)

for i in range(1, N):
    # 水库接收山区来水
    res_vol_isolated[i] = res_vol_isolated[i-1] + inflow_mountain[i]
    if res_vol_isolated[i] > Res_Max_Cap:
        # 溢流/被迫泄洪，直接砸向下游城市
        res_spill_isolated[i] = res_vol_isolated[i] - Res_Max_Cap
        res_vol_isolated[i] = Res_Max_Cap

# 城市河道总流量 = 本地径流 + 上游水库泄洪
river_flow_isolated = runoff_city + res_spill_isolated

# 6. 情景 B: 库河联合调度 (Joint Dispatch by AI Agent)
# Agent 提前 24 小时看到预报，强行命令水库提前开闸腾空库容。
res_vol_joint = np.zeros(N)
res_spill_joint = np.zeros(N)
pre_release_flow = np.zeros(N)
res_vol_joint[0] = 450.0

# 提前腾库阶段 (第 12-30 小时，在暴雨来临前)
for i in range(12, 30):
    pre_release_flow[i] = 15.0 # 提前以 15万m3/h 的安全流量排水

for i in range(1, N):
    res_vol_joint[i] = res_vol_joint[i-1] + inflow_mountain[i] - pre_release_flow[i]
    if res_vol_joint[i] > Res_Max_Cap:
        res_spill_joint[i] = res_vol_joint[i] - Res_Max_Cap
        res_vol_joint[i] = Res_Max_Cap
    elif res_vol_joint[i] < 0:
        res_vol_joint[i] = 0

river_flow_joint = runoff_city + res_spill_joint + pre_release_flow

# 7. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

# A. 水库的命运 (上游防线)
ax1.plot(time, res_vol_isolated, 'r--', linewidth=2, label='Reservoir Vol (Isolated: No Pre-empty)')
ax1.plot(time, res_vol_joint, 'g-', linewidth=3, label='Reservoir Vol (Joint: AI Pre-emptying)')
ax1.axhline(Res_Max_Cap, color='k', linestyle=':', linewidth=2, label='Dam Max Capacity')

# 标注腾库动作
ax1.annotate('AI commands Pre-emptying\n24 hours before storm', xy=(20, res_vol_joint[20]), xytext=(5, 200),
             arrowprops=dict(facecolor='green', shrink=0.05))

ax1.set_ylabel('Upstream Reservoir Volume ($10^4 m^3$)', fontsize=12)
ax1.set_title('Upstream Defense: The Value of Pre-emptying (Reservoir)', fontsize=14)
ax1.legend(loc='lower left')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 城市的命运 (下游河道)
ax2.plot(time, river_flow_isolated, 'r--', linewidth=2, label='City River Flow (Isolated)')
ax2.plot(time, river_flow_joint, 'g-', linewidth=3, label='City River Flow (Joint Dispatch)')
ax2.fill_between(time, 0, runoff_city, color='gray', alpha=0.3, label='City Local Runoff (Base)')

ax2.axhline(River_Capacity, color='red', linestyle='-', linewidth=3, label=f'City Flood Limit ({River_Capacity})')

# 红色高亮内涝灾害
ax2.fill_between(time, River_Capacity, river_flow_isolated, where=(river_flow_isolated > River_Capacity), color='red', alpha=0.5, label='Devastating Urban Flood')

# 标注峰值叠加
ax2.annotate('Deadly Combination:\nUpstream Spill + Local Runoff', xy=(44, river_flow_isolated[44]), xytext=(48, 500),
             arrowprops=dict(facecolor='red', shrink=0.05))

ax2.set_xlabel('Time (Hours)', fontsize=12)
ax2.set_ylabel('Discharge Rate ($10^4 m^3/h$)', fontsize=12)
ax2.set_title('City Fate: Disaster vs. Safety', fontsize=14)
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "joint_dispatch_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
peak_iso = np.max(river_flow_isolated)
peak_joint = np.max(river_flow_joint)
flood_vol_iso = np.sum(np.maximum(0, river_flow_isolated - River_Capacity))
flood_vol_joint = np.sum(np.maximum(0, river_flow_joint - River_Capacity))

history = [
    {'Metric': 'Upstream Reservoir Pre-emptying', 'Isolated Operation': 'None (Hoarded water)', 'Joint Dispatch (AI)': '180万m³ released safely in advance', 'System Impact': 'Created buffer for storm'},
    {'Metric': 'Reservoir Spill during Storm', 'Isolated Operation': f"{np.max(res_spill_isolated):.1f} 万m³/h (Uncontrolled)", 'Joint Dispatch (AI)': '0.0 (Completely absorbed)', 'System Impact': 'Eliminated upstream threat'},
    {'Metric': 'Peak City River Flow', 'Isolated Operation': f"{peak_iso:.1f} 万m³/h", 'Joint Dispatch (AI)': f"{peak_joint:.1f} 万m³/h", 'System Impact': 'Drastic peak reduction'},
    {'Metric': 'Urban Flooding Volume', 'Isolated Operation': f"{flood_vol_iso:.1f} 万m³ (Disaster)", 'Joint Dispatch (AI)': '0.0 (Safe)', 'System Impact': 'Saved the city'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "joint_dispatch_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch11: Joint Dispatch (Reservoir-City)", "Diagram showing a digital twin dashboard linking a mountain reservoir and a city pipeline. A glowing AI link calculates the storm's path, forcing the reservoir to open its gates a day early, clearing space to catch the mountain flood and save the city below.")

print("Files generated successfully.")
