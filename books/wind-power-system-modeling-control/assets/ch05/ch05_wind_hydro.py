import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\wind-power-system-modeling-control\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 风水蓄能联合优化调度 (Wind-Hydro-Storage Cooperative Optimization)
# 场景：风电场功率输出剧烈波动，利用抽水蓄能电站 (Pumped Hydro Storage) 
# 进行“削峰填谷”，以满足电网恒定平滑的调度指令。

# 1. 模拟参数设定 (一天 24 小时)
t_end = 24.0
dt = 0.1 # 6 分钟步长
time = np.arange(0, t_end, dt)
N = len(time)

# 2. 负荷与风电预测 (Load and Wind Profiles)
# 电网调度指令 (平滑负荷曲线，单位 MW)
P_demand = 100.0 + 30.0 * np.sin(np.pi * (time - 8) / 12)

# 风电场实际输出 (剧烈波动)
np.random.seed(42)
# 基础风速趋势
wind_base = 50.0 + 40.0 * np.sin(np.pi * (time - 4) / 12)
# 加入高频波动(湍流)
wind_noise = np.random.normal(0, 15.0, N)
# 滤波平滑一下噪声使之看起来像风
def moving_average(a, n=5):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n
    
wind_noise_smooth = np.pad(moving_average(wind_noise, 10), (9, 0), mode='edge')
P_wind = np.clip(wind_base + wind_noise_smooth, 0, 120.0) # 满发120MW

# 3. 抽水蓄能电站参数 (Pumped Hydro Storage, PHS)
E_max = 5000.0 # 上水库最大容量 MWh
E_min = 20.0  # 死库容 MWh
E_init = 2000.0 # 初始水量 MWh

P_pump_max = 250.0 # 最大抽水功率 MW
P_gen_max = 250.0  # 最大发电功率 MW

eta_pump = 0.8  # 抽水效率
eta_gen = 0.85  # 发电效率

# 4. 实时协同控制逻辑 (Real-time Rule-based Control)
# 目标：让 P_wind + P_hydro_gen - P_hydro_pump 尽量等于 P_demand
P_hydro = np.zeros(N) # 正代表发电(放水)，负代表抽水(蓄能)
E_hydro = np.zeros(N)
E_hydro[0] = E_init

P_grid_actual = np.zeros(N) # 最终送入电网的实际功率

for i in range(1, N):
    # 计算功率缺口
    P_deficit = P_demand[i] - P_wind[i]
    
    # 物理水库储量更新预测
    E_curr = E_hydro[i-1]
    
    if P_deficit > 0:
        # 风电不够，需要蓄能电站发电 (放水)
        # 判断能否发这么多电
        p_gen_req = min(P_deficit, P_gen_max)
        
        # 判断水库里有没有足够的水
        max_energy_can_gen = (E_curr - E_min) * eta_gen
        p_gen_actual = min(p_gen_req, max_energy_can_gen / dt)
        
        P_hydro[i] = p_gen_actual
        # 水库水量减少
        E_hydro[i] = E_curr - (p_gen_actual * dt) / eta_gen
        
    else:
        # 风电太多了，需要蓄能电站抽水 (蓄水)
        p_surplus = -P_deficit
        p_pump_req = min(p_surplus, P_pump_max)
        
        # 判断上水库有没有满
        max_energy_can_pump = (E_max - E_curr) / eta_pump
        p_pump_actual = min(p_pump_req, max_energy_can_pump / dt)
        
        P_hydro[i] = -p_pump_actual
        # 水库水量增加
        E_hydro[i] = E_curr + (p_pump_actual * dt) * eta_pump
        
    # 最终电网收到的功率
    P_grid_actual[i] = P_wind[i] + P_hydro[i]

# 5. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 图 A: 功率平衡曲线
ax1.plot(time, P_demand, 'k-', linewidth=3, label='Grid Demand (Target)')
ax1.plot(time, P_wind, 'c--', linewidth=1.5, alpha=0.8, label='Raw Wind Power')

# 填充平抑区域
ax1.fill_between(time, P_wind, P_grid_actual, where=(P_hydro < 0), color='blue', alpha=0.3, label='Energy Stored (Pumping)')
ax1.fill_between(time, P_wind, P_grid_actual, where=(P_hydro > 0), color='red', alpha=0.3, label='Energy Released (Generating)')

ax1.plot(time, P_grid_actual, 'r-', linewidth=2, label='Actual Delivered Power')

ax1.set_ylabel('Power (MW)', fontsize=12)
ax1.set_title('Wind-Hydro Cooperative Control: Power Smoothing', fontsize=14)
ax1.legend(loc='upper right', ncol=2)
ax1.grid(True, linestyle='--', alpha=0.6)

# 图 B: 抽水蓄能电站水库容量变化
ax2.plot(time, E_hydro, 'b-', linewidth=3, label='Upper Reservoir Energy Level')
ax2.axhline(E_max, color='k', linestyle=':', linewidth=2, label='Max Capacity')
ax2.axhline(E_min, color='r', linestyle=':', linewidth=2, label='Dead Storage (Min)')

# 标注状态
ax2.annotate('Pumping Phase\n(Absorbing excess wind)', xy=(5, E_hydro[int(5/dt)]), xytext=(2, 250),
             arrowprops=dict(facecolor='blue', shrink=0.05))
ax2.annotate('Generating Phase\n(Filling wind deficit)', xy=(18, E_hydro[int(18/dt)]), xytext=(15, 50),
             arrowprops=dict(facecolor='red', shrink=0.05))

ax2.set_xlabel('Time of Day (Hours)', fontsize=12)
ax2.set_ylabel('Stored Energy (MWh)', fontsize=12)
ax2.set_title('Pumped Hydro Storage State of Charge (SOC)', fontsize=14)
ax2.set_xticks(np.arange(0, 25, 2))
ax2.legend(loc='lower right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "wind_hydro_coop_sim.png"), dpi=300, bbox_inches='tight')

# 6. 生成对比表格
# 计算考核指标
error_raw = np.mean(np.abs(P_demand - P_wind))
error_controlled = np.mean(np.abs(P_demand - P_grid_actual))
curtailment = np.sum(np.maximum(0, P_wind - P_demand - (P_hydro<0)*(-P_hydro))) * dt # 未能被水库吸收的弃风
load_shedding = np.sum(np.maximum(0, P_demand - P_grid_actual)) * dt # 未能满足的缺电

history = [
    {'Metric': 'Mean Absolute Tracking Error (MW)', 'Wind Only': round(error_raw, 1), 'Wind + Hydro': round(error_controlled, 1), 'Impact': 'Drastic Smoothing'},
    {'Metric': 'Wind Curtailment (MWh)', 'Wind Only': round(np.sum(np.maximum(0, P_wind - P_demand))*dt, 1), 'Wind + Hydro': round(curtailment, 1), 'Impact': 'Energy Saved'},
    {'Metric': 'Load Shedding / Deficit (MWh)', 'Wind Only': round(np.sum(np.maximum(0, P_demand - P_wind))*dt, 1), 'Wind + Hydro': round(load_shedding, 1), 'Impact': 'Reliability Improved'},
    {'Metric': 'Reservoir Final SOC (MWh)', 'Wind Only': '-', 'Wind + Hydro': round(E_hydro[-1], 1), 'Impact': 'Ready for next day'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "wind_hydro_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch05: Wind-Hydro Hybrid System", "Diagram showing wind turbines connected to a grid alongside a pumped hydro storage facility. When wind power exceeds demand, water is pumped uphill to store energy. When wind dies down, water is released downhill to generate power.")

print("Files generated successfully.")
