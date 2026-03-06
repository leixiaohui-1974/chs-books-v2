import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch06"
os.makedirs(output_dir, exist_ok=True)

# 典型生产场景模拟与控制 (Typical Production Scenario Simulation)
# 模拟蒸发工序在面临三种典型场景时，智能协同控制系统的多模态切换与响应
# 场景1 (0-60分): 正常稳态下的汽耗比寻优 (省钱模式)
# 场景2 (60-120分): 进料浓度突然剧烈波动 (抗扰模式)
# 场景3 (120-180分): 锅炉跳机导致蒸汽母管压力骤降 (保命安全模式)

# 1. 全局参数设定
N = 180 # 180分钟
time = np.arange(0, N)

# 外部强迫与干扰
feed_conc = np.ones(N) * 140.0
feed_conc[60:90] = 130.0 # 场景2: 进料突然变稀
feed_conc[90:120] = 145.0 # 场景2: 进料回升

steam_pressure = np.ones(N) * 1.0 # 标幺值 1.0
steam_pressure[120:] = 0.4 # 场景3: 蒸汽压力暴跌至40%

# 目标出料浓度
target_conc = 240.0

# 2. 系统状态变量
out_conc = np.ones(N) * 240.0
steam_flow = np.ones(N) * 50.0 # 蒸汽消耗 t/h
feed_flow = np.ones(N) * 300.0 # 进料量 t/h
plant_mode = ["Optimization"] * N

# 3. 动态仿真与状态机控制
# 极其简化的物理响应模型
def evaporate(F_in, C_in, S_flow, S_press):
    # 蒸发量取决于蒸汽流量和压力
    evap_water = S_flow * 2.0 * np.sqrt(S_press)
    out_f = F_in - evap_water
    out_f = max(1.0, out_f)
    return (F_in * C_in) / out_f

for t in range(1, N):
    current_f_conc = feed_conc[t]
    current_s_press = steam_pressure[t]
    
    # ---------------------------------------------
    # 状态机路由 (State Machine Routing)
    # ---------------------------------------------
    if current_s_press < 0.7:
        # 场景 3: 蒸汽压力骤降 -> 触发安全保命模式
        plant_mode[t] = "Emergency Safety"
        # 控制策略：蒸汽压力不够，无法蒸发足够的水。
        # 为了保证出料浓度不暴跌，唯一的办法是“断臂求生”：暴力关小进料阀门
        # 强行维持质量平衡：F_in_new = (S_flow * 2 * sqrt(P)) / (1 - C_in/C_out)
        required_evap_ratio = 1.0 - (current_f_conc / target_conc)
        # 假设蒸汽阀门全开 100 t/h 试图挽救
        steam_flow[t] = 100.0 
        max_evap = steam_flow[t] * 2.0 * np.sqrt(current_s_press)
        feed_flow[t] = max_evap / required_evap_ratio
        
    elif abs(current_f_conc - 140.0) > 2.0:
        # 场景 2: 进料扰动 -> 触发抗扰控制模式 (类似 MPC 强力镇压)
        plant_mode[t] = "Disturbance Rejection"
        feed_flow[t] = 300.0 # 进料保持
        # 动态计算所需的蒸汽量来精确抵消波动
        required_evap = feed_flow[t] * (1.0 - current_f_conc / target_conc)
        steam_flow[t] = required_evap / (2.0 * np.sqrt(current_s_press))
        # 稍微加一点随机扰动模拟控制死区
        steam_flow[t] += np.random.normal(0, 0.5)
        
    else:
        # 场景 1: 稳态 -> 触发汽耗比寻优模式
        plant_mode[t] = "Cost Optimization"
        feed_flow[t] = 300.0
        # 稳态下，优化器通过微调内部闪蒸效率，在保证浓度的前提下缓慢压降蒸汽
        # 模拟蒸汽消耗慢慢下降 (寻找极值点)
        steam_flow[t] = max(45.0, steam_flow[t-1] - 0.1)
        
    # 计算实际物理输出
    out_conc[t] = evaporate(feed_flow[t], current_f_conc, steam_flow[t], current_s_press)

# 4. 绘图展示
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 14), sharex=True)

# 绘制背景色块表示不同的工作模式
spans = [(0, 60, 'blue', 'Optimization (Save $)'), 
         (60, 120, 'orange', 'Disturbance Rejection (Stable)'), 
         (120, 180, 'red', 'Emergency Safety (Survive)')]

for ax in [ax1, ax2, ax3, ax4]:
    for start, end, color, label in spans:
        if ax == ax1: # 仅在顶层画 label
            ax.axvspan(start, end, facecolor=color, alpha=0.1, label=label)
        else:
            ax.axvspan(start, end, facecolor=color, alpha=0.1)

# A. 外部扰动环境 (Environment)
ax1.plot(time, feed_conc, 'k-', linewidth=2, label='Feed Concentration (g/L)')
ax1.set_ylabel('Feed Conc.', fontsize=12)
ax1.set_title('External Environment & Disturbances', fontsize=14)
ax1.legend(loc='lower left')
ax1.grid(True, linestyle='--', alpha=0.6)

ax1_twin = ax1.twinx()
ax1_twin.plot(time, steam_pressure, 'r--', linewidth=2, label='Main Steam Pressure (pu)')
ax1_twin.set_ylabel('Steam Press.', color='r', fontsize=12)
ax1_twin.tick_params(axis='y', labelcolor='r')
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax1_twin.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

# B. 系统核心质量指标 (Output Quality)
ax2.plot(time, out_conc, 'g-', linewidth=3, label='Actual Output Concentration')
ax2.axhline(target_conc, color='k', linestyle=':', linewidth=2, label='Target (240 g/L)')
ax2.set_ylabel('Output Conc. (g/L)', fontsize=12)
ax2.set_title('Quality Control (Strict Adherence to Red Line)', fontsize=14)
ax2.set_ylim(230, 250)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 蒸汽调节阀门 (Steam Valve)
ax3.plot(time, steam_flow, 'b-', linewidth=2, label='Steam Flow Command (t/h)')
ax3.set_ylabel('Steam Flow (t/h)', fontsize=12)
ax3.set_title('Primary Actuator: Steam Valve', fontsize=14)
ax3.legend(loc='lower right')
ax3.grid(True, linestyle='--', alpha=0.6)

# D. 进料调节阀门 (Feed Valve - 保命手段)
ax4.plot(time, feed_flow, 'm-', linewidth=3, label='Feed Flow Command (t/h)')
ax4.set_xlabel('Time (Minutes)', fontsize=12)
ax4.set_ylabel('Feed Flow (t/h)', fontsize=12)
ax4.set_title('Secondary Actuator: Feed Valve (Emergency Load Shedding)', fontsize=14)
ax4.legend(loc='upper right')
ax4.grid(True, linestyle='--', alpha=0.6)

# 注释说明
ax3.annotate('Optimizer squeezes\nsteam out', xy=(30, 46), xytext=(10, 48), arrowprops=dict(facecolor='blue', shrink=0.05))
ax3.annotate('Violent valve hunting\nto reject disturbance', xy=(75, 43), xytext=(65, 38), arrowprops=dict(facecolor='black', shrink=0.05))
ax4.annotate('Steam drops!\nSystem slashes feed rate\nto prevent catastrophic dilution', xy=(130, 180), xytext=(125, 250), arrowprops=dict(facecolor='red', shrink=0.05))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "scenario_modes_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = [
    {'Scenario': '1. Steady State', 'Time': '0-60 min', 'Active Mode': 'Cost Optimization', 'Primary Action': 'Slowly reducing steam flow', 'Outcome': 'Saved Steam, Conc. Perfect'},
    {'Scenario': '2. Feed Drop', 'Time': '60-120 min', 'Active Mode': 'Disturbance Rejection', 'Primary Action': 'Aggressively tuning steam valve', 'Outcome': 'Absorbed shock, Conc. Stable'},
    {'Scenario': '3. Steam Failure', 'Time': '120-180 min', 'Active Mode': 'Emergency Safety', 'Primary Action': 'Drastically cutting feed flow', 'Outcome': 'Prevented dilution disaster'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "scenario_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch06: Multi-Scenario State Machine", "Diagram showing an AI Control Brain switching gears. In peace time, it picks up pennies (Optimization). During an attack, it raises a shield (Disturbance Rejection). During a severe earthquake, it pulls the emergency brake (Safety Mode).")

print("Files generated successfully.")
