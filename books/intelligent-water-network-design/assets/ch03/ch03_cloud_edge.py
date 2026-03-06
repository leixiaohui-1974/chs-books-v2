import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\intelligent-water-network-design\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 云边端协同调度 (Cloud-Edge-Device Collaborative Dispatch)
# 场景：模拟城市发生暴雨内涝。
# 端(Device)：水泵，负责抽水。
# 边(Edge)：泵站控制柜，负责极速响应防止水位漫溢。
# 云(Cloud)：城市级大脑，负责看全局天气预报，提前下达“预排空”指令。

# 1. 模拟环境设定 (120 分钟)
t_end = 120
dt = 1.0 # 1分钟步长
time = np.arange(0, t_end, dt)
N = len(time)

# 极端暴雨强迫 (Storm intensity)
# 前 40 分钟无雨，40-60 分钟短时特大暴雨
rainfall = np.zeros(N)
rainfall[40:60] = 50.0 * np.sin(np.pi * (time[40:60] - 40) / 20.0) # 钟形暴雨

# 蓄水池物理模型
# dH/dt = (Rain_inflow - Pump_outflow) / Area
Area = 1000.0 # m^2
H_max = 5.0 # 危险漫溢水位 m
H_min = 1.0 # 停泵水位 (防止干抽) m
H_init = 3.5 # 初始水位偏高，处于随时准备排洪的状态

Pump_Capacity = 300.0 # 水泵最大抽水量 m^3/min

# 2. 方案 A：纯边缘控制 (Edge-Only, 只有反应能力)
# 逻辑：水位超过 4.0m 就全开水泵，低于 1.0m 关泵
H_edge = np.zeros(N)
P_edge = np.zeros(N) # 泵的状态 0-1
H_edge[0] = H_init

for i in range(1, N):
    # 降雨入流转换 (极其庞大的汇水面积)
    Q_in = rainfall[i] * 10.0 
    
    # 边缘逻辑 (本地阈值控制)
    if H_edge[i-1] > 4.0:
        P_edge[i] = 1.0
    elif H_edge[i-1] < 1.0:
        P_edge[i] = 0.0
    else:
        P_edge[i] = P_edge[i-1] # 保持状态
        
    Q_out = P_edge[i] * Pump_Capacity
    
    # 物理更新
    H_edge[i] = H_edge[i-1] + (Q_in - Q_out) / Area
    H_edge[i] = max(0, H_edge[i])

# 3. 方案 B：云边端协同控制 (Cloud-Edge Collaborative)
# 逻辑：云端看到了天气预报，提前 40 分钟下发“强制排空”指令给边缘节点。
# 边缘节点接到指令后，立刻抽水直到安全底线。暴雨来临时，边缘再次接管实时控制。
H_collab = np.zeros(N)
P_collab = np.zeros(N)
H_collab[0] = H_init

# 云端下发的全局策略指令
cloud_command = np.zeros(N)
cloud_command[0:40] = 1.0 # 暴雨前强行预排空

for i in range(1, N):
    Q_in = rainfall[i] * 10.0
    
    # 协同逻辑
    if cloud_command[i] == 1.0:
        # 云端强干预：预排空，除非到了死水位
        if H_collab[i-1] > 1.1:
            P_collab[i] = 1.0
        else:
            P_collab[i] = 0.0
    else:
        # 暴雨期间，云端通讯可能中断，边缘节点重新接管生命线
        if H_collab[i-1] > 4.0:
            P_collab[i] = 1.0
        elif H_collab[i-1] < 1.0:
            P_collab[i] = 0.0
        else:
            P_collab[i] = P_collab[i-1]
            
    Q_out = P_collab[i] * Pump_Capacity
    H_collab[i] = H_collab[i-1] + (Q_in - Q_out) / Area
    H_collab[i] = max(0, H_collab[i])

# 4. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 气象预报与云端指令
ax1.fill_between(time, 0, rainfall, color='gray', alpha=0.3, label='Actual Rainstorm')
ax1.plot(time, cloud_command * 50.0, 'b--', linewidth=3, label='Cloud Command (Pre-empty Signal)')
ax1.set_ylabel('Rain / Signal', fontsize=12)
ax1.set_title('Cloud Layer: Weather Forecasting & Strategic Commands', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

ax1.annotate('Cloud AI predicts rain\nSends Pre-empty command', xy=(20, 50), xytext=(5, 30),
             arrowprops=dict(facecolor='blue', shrink=0.05))

# B. 水位防线对比 (生死时速)
ax2.plot(time, H_edge, 'r-', linewidth=2, label='Edge-Only Control (Reactive)')
ax2.plot(time, H_collab, 'g-', linewidth=3, label='Cloud-Edge Control (Proactive)')
ax2.axhline(H_max, color='k', linestyle=':', linewidth=2, label='Disaster Level (5.0m)')
ax2.axhline(H_min, color='gray', linestyle='-.', linewidth=2, label='Pump Protection Level (1.0m)')

# 标出漫溢区
overtop_idx = np.where(H_edge > H_max)[0]
if len(overtop_idx) > 0:
    ax2.fill_between(time, H_max, H_edge, where=(H_edge>H_max), color='red', alpha=0.5, label='City Flooded (Disaster)')

ax2.set_ylabel('Water Level (m)', fontsize=12)
ax2.set_title('Edge Layer: Physics execution & Survival Battle', fontsize=14)
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.6)

ax2.annotate('Edge alone fails\ndue to high initial water', xy=(65, H_max), xytext=(70, H_max+1.0),
             arrowprops=dict(facecolor='red', shrink=0.05))
ax2.annotate('Cloud-Edge synergy\nsurvives perfectly', xy=(65, H_collab[65]), xytext=(70, 2.0),
             arrowprops=dict(facecolor='green', shrink=0.05))

# C. 设备端动作 (Pump Status)
ax3.plot(time, P_edge, 'r-', linewidth=2, alpha=0.7, label='Pump Status (Edge-Only)')
ax3.plot(time, P_collab + 0.05, 'g-', linewidth=2, alpha=0.7, label='Pump Status (Collab - shifted for visibility)')
ax3.set_xlabel('Time (Minutes)', fontsize=12)
ax3.set_ylabel('Pump On/Off', fontsize=12)
ax3.set_title('Device Layer: IoT Actuator Status', fontsize=14)
ax3.set_yticks([0, 1])
ax3.set_yticklabels(['OFF', 'ON'])
ax3.legend(loc='center right')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cloud_edge_synergy_sim.png"), dpi=300, bbox_inches='tight')

# 5. 生成对比表格
# 计算漫溢量
vol_edge = np.sum(np.maximum(0, H_edge - H_max)) * Area
vol_collab = np.sum(np.maximum(0, H_collab - H_max)) * Area

history = [
    {'Architecture': 'Edge-Only (Reactive)', 'Pre-storm Level': f"{H_edge[40]:.1f} m", 'Max Peak Level': f"{np.max(H_edge):.2f} m", 'Flood Disaster': 'YES (Overtopped)'},
    {'Architecture': 'Cloud-Edge (Proactive)', 'Pre-storm Level': f"{H_collab[40]:.1f} m", 'Max Peak Level': f"{np.max(H_collab):.2f} m", 'Flood Disaster': 'NO (Safe Margin)'},
    {'Architecture': 'Core Philosophy', 'Pre-storm Level': 'AI created buffer zone', 'Max Peak Level': 'Edge secured the bottom line', 'Flood Disaster': 'Systematic Resilience'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "cloud_edge_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: Cloud-Edge-Device Synergy", "Diagram showing three layers. Cloud (Top) looks at weather satellite data and sends early warnings. Edge Box (Middle) sits near the street, ready to react in milliseconds if water rises. Device (Bottom) is a heavy water pump waiting for commands.")

print("Files generated successfully.")
