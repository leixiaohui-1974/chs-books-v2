import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\photovoltaic-system-modeling-control\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 水光互补与水面光伏联合仿真 (Hydro-PV Hybrid System & Floating PV)
# 场景：展示水面光伏的“温度红利”以及水电站对光伏“锯齿波”的平抑作用

# 1. 模拟参数设定 (一天 24 小时，1 分钟步长)
t_end = 24.0
dt = 1.0 / 60.0 # 1 分钟
time = np.arange(0, t_end, dt)
N = len(time)

np.random.seed(42)

# 2. 气象模型 (温度与光照)
# 环境气温 (Ambient Temp)
T_amb = 25.0 + 10.0 * np.sin(np.pi * (time - 8) / 12)

# 光照强度 (带有高频云层遮挡毛刺)
G_base = np.maximum(0, 1000.0 * np.sin(np.pi * (time - 6) / 12))
# 在白天 8点到 16点之间加入云层
clouds = np.ones(N)
for t_idx, t in enumerate(time):
    if 8.0 < t < 16.0:
        if np.random.rand() < 0.05: # 5% 的概率出现一片云
            clouds[t_idx:min(t_idx+15, N)] = 0.3 + 0.3 * np.random.rand()

G_actual = G_base * clouds

# 3. 光伏板温度模型 (Thermal Model)
# 陆上光伏 (Ground-mounted PV)：缺乏散热，温度极高
# 水面光伏 (Floating PV)：水体比热容大，蒸发带走热量，温度显著降低
T_pv_ground = np.zeros(N)
T_pv_floating = np.zeros(N)

# 简单的稳态热平衡方程近似: T_pv = T_amb + (NOCT - 20) / 800 * G
NOCT_ground = 45.0
NOCT_floating = 38.0 # 水面散热好，NOCT 等效降低

for i in range(N):
    T_pv_ground[i] = T_amb[i] + (NOCT_ground - 20.0) / 800.0 * G_actual[i]
    T_pv_floating[i] = T_amb[i] + (NOCT_floating - 20.0) / 800.0 * G_actual[i]

# 4. 光伏发电量模型 (含温度衰减)
# P = P_rated * (G/1000) * [1 + gamma * (T_pv - 25)]
P_rated = 100.0 # 100 MW
gamma = -0.004  # 温度系数 -0.4% / °C

P_ground = np.zeros(N)
P_floating = np.zeros(N)

for i in range(N):
    if G_actual[i] > 0:
        P_ground[i] = P_rated * (G_actual[i] / 1000.0) * (1.0 + gamma * (T_pv_ground[i] - 25.0))
        P_floating[i] = P_rated * (G_actual[i] / 1000.0) * (1.0 + gamma * (T_pv_floating[i] - 25.0))

# 5. 水光互补平抑 (Hydro-PV Hybrid Control)
# 目标电网指令 (平滑曲线)
P_demand = 80.0 + 40.0 * np.sin(np.pi * (time - 6) / 12) # 80~120MW

# 水电站出力的响应 (由于水轮机有水锤效应，不能瞬间跳变，用一阶惯性模拟)
# P_hydro_target = P_demand - P_floating
tau_hydro = 0.5 # 水电响应时间常数 30 分钟 (比较缓慢)
P_hydro = np.zeros(N)
P_hydro[0] = max(0, P_demand[0] - P_floating[0])

for i in range(1, N):
    target = max(0, P_demand[i] - P_floating[i])
    P_hydro[i] = P_hydro[i-1] + (target - P_hydro[i-1]) * (dt / tau_hydro)
    # 水电装机容量限制
    P_hydro[i] = min(P_hydro[i], 150.0)

# 系统总输出
P_total_hybrid = P_floating + P_hydro

# 6. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 水面光伏的“温度红利”
ax1.plot(time, T_pv_ground, 'r-', linewidth=2, alpha=0.7, label='Ground PV Temp (°C)')
ax1.plot(time, T_pv_floating, 'b-', linewidth=3, label='Floating PV Temp (°C)')
ax1.plot(time, T_amb, 'k:', linewidth=2, label='Ambient Air Temp (°C)')

ax1.fill_between(time, T_pv_ground, T_pv_floating, color='blue', alpha=0.1, label='Cooling Benefit from Water')

ax1.set_ylabel('Temperature (°C)', fontsize=12)
ax1.set_title('Floating PV (FPV): Natural Water Cooling Effect', fontsize=14)
ax1.legend(loc='upper left', ncol=2)
ax1.grid(True, linestyle='--', alpha=0.6)

ax1.annotate('Up to 10°C cooler\nthan land arrays', xy=(12, T_pv_floating[int(12/dt)]), xytext=(8, 60),
             arrowprops=dict(facecolor='blue', shrink=0.05))

# B. 发电量提升 (Power Gain)
ax2.plot(time, P_ground, 'r-', linewidth=2, alpha=0.7, label='Ground PV Power (MW)')
ax2.plot(time, P_floating, 'b-', linewidth=2, label='Floating PV Power (MW)')

ax2.set_ylabel('Power Generation (MW)', fontsize=12)
ax2.set_title('Efficiency Gain due to Temperature Reduction', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# 放大一个正午峰值对比
inset_ax = ax2.inset_axes([0.1, 0.45, 0.3, 0.4])
inset_ax.plot(time, P_ground, 'r-', linewidth=2)
inset_ax.plot(time, P_floating, 'b-', linewidth=2)
inset_ax.fill_between(time, P_ground, P_floating, color='blue', alpha=0.3)
inset_ax.set_xlim(11.5, 12.5)
inset_ax.set_ylim(80, 95)
inset_ax.set_title('Noon Peak (+4% Power)')
inset_ax.grid(True, linestyle=':')
ax2.indicate_inset_zoom(inset_ax, edgecolor="black")

# C. 水光互补调度 (Hydro-PV Synergy)
ax3.plot(time, P_demand, 'k--', linewidth=2, label='Grid Demand Target')
ax3.plot(time, P_floating, 'y-', linewidth=1.5, alpha=0.8, label='FPV Power (Volatile)')
ax3.plot(time, P_hydro, 'c-', linewidth=2, label='Hydro Power (Compensator)')
ax3.plot(time, P_total_hybrid, 'g-', linewidth=3, label='Total Hybrid Output to Grid')

ax3.set_xlabel('Time of Day (Hours)', fontsize=12)
ax3.set_ylabel('Power (MW)', fontsize=12)
ax3.set_title('Hydro-PV Synergy: Taming the Solar Sawtooth', fontsize=14)
ax3.set_xticks(np.arange(0, 25, 2))
ax3.legend(loc='upper right', ncol=2)
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "hydro_pv_synergy_sim.png"), dpi=300, bbox_inches='tight')

# 7. 生成对比表格
# 计算全天总发电量 (MWh)
E_ground = np.sum(P_ground) * dt
E_floating = np.sum(P_floating) * dt
gain_percent = (E_floating - E_ground) / E_ground * 100 if E_ground > 0 else 0

history = [
    {'Metric': 'Max Panel Temp (°C)', 'Baseline (Ground/PV Only)': round(np.max(T_pv_ground), 1), 'Smart System (Floating/Hybrid)': round(np.max(T_pv_floating), 1), 'Benefit': 'Extended Lifespan'},
    {'Metric': 'Daily Energy Yield (MWh)', 'Baseline (Ground/PV Only)': round(E_ground, 1), 'Smart System (Floating/Hybrid)': round(E_floating, 1), 'Benefit': f"+{round(gain_percent, 1)}% Revenue"},
    {'Metric': 'Grid Tracking Error (MW)', 'Baseline (Ground/PV Only)': round(np.mean(np.abs(P_demand - P_floating)), 1), 'Smart System (Floating/Hybrid)': round(np.mean(np.abs(P_demand - P_total_hybrid)), 1), 'Benefit': 'Grid Friendly Power'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "fpv_synergy_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch05: Floating PV & Hydro Synergy", "Diagram showing solar panels floating on a reservoir next to a hydroelectric dam. The water cools the panels (boosting efficiency), while the dam acts as a massive battery, opening its gates to generate power instantly whenever a cloud covers the sun.")

print("Files generated successfully.")
