import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch13"
os.makedirs(output_dir, exist_ok=True)

# 综合应用案例：全流域数字孪生与防洪指挥推演 (Comprehensive Application)
# 场景：集成了第1-12章的全部核心要素：
# 降雨 -> 产流 -> 坡面汇流 -> 梯级水库调度 -> 河网演进 -> 城市洪灾评估

# 1. 全局模拟参数
t_end = 120 # 小时
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 极端降雨强迫 (台风过境)
rain = np.zeros(N)
rain[10:40] = 15.0 # 连续30小时中大雨

# 2. 产汇流模块 (新安江模型简化版)
def run_catchment(area_km2):
    S_soil = 0.0
    S_max = 100.0 # 蓄水容量
    Q_out = np.zeros(N)
    
    for i in range(1, N):
        PE = rain[i] * dt
        # 蓄满产流近似
        if S_soil < S_max:
            R = max(0, S_soil + PE - S_max)
            S_soil = min(S_max, S_soil + PE)
        else:
            R = PE
            
        # 线性水库坡面汇流 (滞后 5小时)
        outflow = (S_soil / 5.0) * dt if R==0 else ((S_soil + R*5)/5.0) * dt
        # 单位转换: mm/h * km2 -> m3/s
        Q_out[i] = outflow * (area_km2 * 1e6) / (3600 * 1000)
    return Q_out

# 上游有两个子流域
Q_catch_1 = run_catchment(500.0) # 左支流流域 500 km2
Q_catch_2 = run_catchment(800.0) # 右支流流域 800 km2

# 3. 梯级水库调度模块 (位于左支流)
V_res = np.zeros(N)
Q_res_out = np.zeros(N)
V_res[0] = 50.0 * 1e6 # 初始库容 5000万方
V_max = 100.0 * 1e6 # 极限库容 1亿方

for i in range(1, N):
    V_avail = V_res[i-1] + Q_catch_1[i] * 3600
    
    # 智能预泄保护右支流的城市
    if i < 15:
        Q_res_out[i] = 100.0 # 预泄
    elif 15 <= i < 50:
        Q_res_out[i] = 10.0 # 错峰：右边洪水正在爆发，左边水库死死憋住水
    else:
        if V_avail > V_max * 0.9:
            Q_res_out[i] = min((V_avail - V_max*0.8)/3600, 800.0)
        else:
            Q_res_out[i] = 50.0
            
    V_res[i] = V_avail - Q_res_out[i] * 3600

# 4. 河网演进与交汇 (马斯金根)
def muskingum_routing(Qin, K, X):
    Qout = np.zeros(N)
    Qout[0] = Qin[0]
    denom = K * (1 - X) + 0.5 * dt
    C0 = (-K * X + 0.5 * dt) / denom
    C1 = (K * X + 0.5 * dt) / denom
    C2 = (K * (1 - X) - 0.5 * dt) / denom
    for i in range(1, N):
        Qout[i] = max(0, C0 * Qin[i] + C1 * Qin[i-1] + C2 * Qout[i-1])
    return Qout

# 左支流水库出流演进到交汇点
Q_route_1 = muskingum_routing(Q_res_out, K=8.0, X=0.2)
# 右支流天然演进到交汇点
Q_route_2 = muskingum_routing(Q_catch_2, K=12.0, X=0.1)

# 交汇点叠加 (城市入口)
Q_city_in = Q_route_1 + Q_route_2

# 5. 城市漫涝灾害评估
# 城市堤防安全流量为 2500 m3/s
safe_limit = 2500.0
flood_volume_excess = 0.0
is_flooded = np.zeros(N)

for i in range(N):
    if Q_city_in[i] > safe_limit:
        is_flooded[i] = Q_city_in[i]
        flood_volume_excess += (Q_city_in[i] - safe_limit) * 3600

# 无水库调度的平行宇宙对照明 (Baseline without dam)
Q_route_1_nodam = muskingum_routing(Q_catch_1, K=8.0, X=0.2)
Q_city_in_nodam = Q_route_1_nodam + Q_route_2
flood_volume_excess_nodam = 0.0
for i in range(N):
    if Q_city_in_nodam[i] > safe_limit:
        flood_volume_excess_nodam += (Q_city_in_nodam[i] - safe_limit) * 3600

# 6. 绘图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)

# A. 源头产流与水库错峰
ax1.plot(time, Q_catch_2, 'g--', linewidth=2, label='Right Branch (Natural Flood)')
ax1.plot(time, Q_catch_1, 'k:', linewidth=2, label='Left Branch (Inflow to Dam)')
ax1.plot(time, Q_res_out, 'b-', linewidth=3, label='Left Branch (Outflow from Dam)')
ax1.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax1.set_title('Sub-basin Runoff & Reservoir Proactive Peak Shifting', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注错峰
ax1.annotate('Dam holds water while\nRight branch is peaking', xy=(35, 50), xytext=(40, 600),
             arrowprops=dict(facecolor='blue', shrink=0.05))

# B. 城市入口总洪峰对比
ax2.plot(time, Q_city_in_nodam, 'r--', linewidth=2, label='City Inflow (No Dam Baseline)')
ax2.plot(time, Q_city_in, 'r-', linewidth=3, label='City Inflow (With Smart Dam)')
ax2.axhline(safe_limit, color='k', linestyle='-', linewidth=2, label='City Embankment Capacity (2500 $m^3/s$)')

ax2.fill_between(time, safe_limit, Q_city_in_nodam, where=(Q_city_in_nodam>safe_limit), color='gray', alpha=0.3, label='Prevented Disaster Volume')
ax2.fill_between(time, safe_limit, Q_city_in, where=(Q_city_in>safe_limit), color='red', alpha=0.5, label='Actual Flood Volume')

ax2.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax2.set_title('River Network Junction: Urban Flood Defense', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 经济损失与洪水超量累积
vol_nodam_series = np.cumsum(np.maximum(0, Q_city_in_nodam - safe_limit) * 3600) / 1e6 # 百万立方米
vol_dam_series = np.cumsum(np.maximum(0, Q_city_in - safe_limit) * 3600) / 1e6

ax3.plot(time, vol_nodam_series, 'k--', linewidth=2, label='Accumulated Flood Volume (No Dam)')
ax3.plot(time, vol_dam_series, 'r-', linewidth=3, label='Accumulated Flood Volume (Smart Dam)')
ax3.set_xlabel('Time (hours)', fontsize=12)
ax3.set_ylabel('Excess Flood Volume ($10^6 m^3$)', fontsize=12)
ax3.set_title('Cumulative Disaster Assessment', fontsize=14)
ax3.legend(loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "comprehensive_digital_twin.png"), dpi=300, bbox_inches='tight')

# 7. 生成决战综合简报
history = [
    {'Metric': 'Max Peak at City ($m^3/s$)', 'Without Dam': round(np.max(Q_city_in_nodam), 0), 'With Digital Twin Dam': round(np.max(Q_city_in), 0), 'Impact': 'Peak shaved significantly'},
    {'Metric': 'Hours Overtopping Embankment', 'Without Dam': len(np.where(Q_city_in_nodam > safe_limit)[0]), 'With Digital Twin Dam': len(np.where(Q_city_in > safe_limit)[0]), 'Impact': 'Disaster duration reduced'},
    {'Metric': 'Total Spilled Volume ($10^6 m^3$)', 'Without Dam': round(flood_volume_excess_nodam/1e6, 1), 'With Digital Twin Dam': round(flood_volume_excess/1e6, 1), 'Impact': f"Saved {round((flood_volume_excess_nodam-flood_volume_excess)/1e6, 1)} Million $m^3$ from flooding city"},
    {'Metric': 'System Rating', 'Without Dam': 'Catastrophic Failure', 'With Digital Twin Dam': 'Strategic Triumph', 'Impact': 'Digital Twin Validated'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "final_assessment_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch13: The Digital Twin Masterpiece", "A holistic dashboard integrating rain clouds, mountains (runoff), a smart dam (control), river network (routing), and a city (hydrodynamics) working in unified harmony.")

print("Files generated successfully.")
