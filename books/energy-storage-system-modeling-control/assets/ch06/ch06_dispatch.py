import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\energy-storage-system-modeling-control\assets\ch06"
os.makedirs(output_dir, exist_ok=True)

# 微电网储能的经济调度与调频 (Economic Dispatch & Peak Shaving)
# 场景：展示储能系统如何利用大容量进行削峰填谷（低买高卖赚电费差价），
# 以及如何同时利用小容量进行电网频率的下垂控制（Droop Control）。

# 1. 模拟环境设定 (24小时日前经济调度，1小时步长)
t_end = 24
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 工业园区的原始负荷曲线 (白天高，半夜低)
load_base = 500 + 400 * np.sin(np.pi * (time - 6) / 12)
load_base = np.maximum(200, load_base) # kW

# 峰谷分时电价 (Time-of-Use Electricity Price) 
# 谷电: 0-7, 23-24 (Price = 0.3)
# 平电: 7-10, 15-18, 21-23 (Price = 0.6)
# 峰电: 10-15, 18-21 (Price = 1.2)
price = np.ones(N) * 0.6
price[0:7] = 0.3; price[23:] = 0.3
price[10:15] = 1.2; price[18:21] = 1.2

# 储能系统参数
E_max = 2000.0 # 电池总容量 kWh
P_max = 500.0 # 逆变器最大充放电功率 kW
soc_init = 0.5
soc_min = 0.1
soc_max = 0.9

# 2. MPC 经济优化：削峰填谷 (Peak Shaving)
# 目标：最小化购电成本
def objective_mpc(p_ess):
    # p_ess 为储能功率，正为放电，负为充电
    E = np.zeros(N)
    E[0] = E_max * soc_init
    penalty = 0
    
    for i in range(1, N):
        E[i] = E[i-1] - p_ess[i-1] * dt
        # 约束：SOC 不能越限
        if E[i] < E_max * soc_min: penalty += 1e6 * (E_max * soc_min - E[i])**2
        if E[i] > E_max * soc_max: penalty += 1e6 * (E[i] - E_max * soc_max)**2
            
    # 并网点购电功率 (负荷减去储能放电)
    p_grid = load_base - p_ess
    # 假设不允许逆向送电卖给电网，超出的部分直接截断
    p_grid = np.maximum(0, p_grid) 
    
    # 购电成本
    cost = np.sum(p_grid * price)
    return cost + penalty

# 约束：功率限制
bounds = [(-P_max, P_max) for _ in range(N)]
p_guess = np.zeros(N)

res = minimize(objective_mpc, p_guess, bounds=bounds, method='L-BFGS-B')
p_ess_opt = res.x

# 计算优化后的电量轨迹和电网购电曲线
E_opt = np.zeros(N)
E_opt[0] = E_max * soc_init
for i in range(1, N):
    E_opt[i] = E_opt[i-1] - p_ess_opt[i-1] * dt
soc_opt = E_opt / E_max
p_grid_opt = np.maximum(0, load_base - p_ess_opt)

# 3. 电网一次调频 (Primary Frequency Regulation via Droop Control)
# 在第 12 小时的某个极其微小的时刻，电网频率突然跌落
freq_sim_time = np.linspace(0, 10, 100) # 模拟 10 秒钟的高频动作
freq_grid = 50.0 - 0.2 * (1 - np.exp(-freq_sim_time / 2)) # 从 50Hz 跌到 49.8Hz

# 下垂控制法则: dP = -K_f * df
K_f = 1000.0 # 频率下垂系数 kW/Hz
p_droop = np.zeros(len(freq_sim_time))
for i in range(len(freq_sim_time)):
    df = freq_grid[i] - 50.0
    # 如果频率低于死区 (比如 49.95Hz)，则立刻出力
    if df < -0.05:
        p_droop[i] = -K_f * (df + 0.05) # 放电支撑电网

# 4. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))

# A. 经济调度：削峰填谷
ax1.plot(time, load_base, 'k--', linewidth=2, label='Original Load')
ax1.plot(time, p_grid_opt, 'b-', linewidth=3, label='Grid Power (With Storage)')

ax1_twin = ax1.twinx()
ax1_twin.step(time, price, 'orange', where='post', alpha=0.3)
ax1_twin.fill_between(time, 0, price, step='post', color='orange', alpha=0.1, label='Time-of-Use Price')
ax1_twin.set_ylabel('Price (CNY/kWh)', color='orange')
ax1_twin.tick_params(axis='y', labelcolor='orange')

ax1.set_ylabel('Power (kW)', fontsize=12)
ax1.set_title('Peak Shaving: Shifting Load to Cheap Energy Hours', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax1_twin.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc='upper left')

# 标注削峰
ax1.annotate('Peak Shaved\n(Discharging during expensive hours)', xy=(12, p_grid_opt[12]), xytext=(15, 800),
             arrowprops=dict(facecolor='blue', shrink=0.05))

# B. 电池 SOC 轨迹
ax2.plot(time, soc_opt * 100, 'g-', linewidth=2.5, label='Battery SOC')
ax2.axhline(soc_max*100, color='r', linestyle=':', label='Max SOC Limit (90%)')
ax2.axhline(soc_min*100, color='r', linestyle=':', label='Min SOC Limit (10%)')

ax2.set_xlabel('Time of Day (Hour)', fontsize=12)
ax2.set_ylabel('State of Charge (%)', fontsize=12)
ax2.set_title('Energy Arbitrage: Buying Low, Selling High', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='lower right')

# C. 秒级一次调频动作
ax3.plot(freq_sim_time, freq_grid, 'r--', linewidth=2, label='Grid Frequency (Hz)')
ax3.set_ylabel('Frequency (Hz)', color='red', fontsize=12)
ax3.tick_params(axis='y', labelcolor='red')

ax3_twin = ax3.twinx()
ax3_twin.plot(freq_sim_time, p_droop, 'b-', linewidth=3, label='Inverter Fast Response (kW)')
ax3_twin.set_ylabel('Droop Power Injection (kW)', color='blue', fontsize=12)
ax3_twin.tick_params(axis='y', labelcolor='blue')

ax3.set_xlabel('Time (Seconds) [Zoomed in at hour 12]', fontsize=12)
ax3.set_title('Grid-Forming / Droop Control: Millisecond Frequency Support', fontsize=14)
ax3.grid(True, linestyle='--', alpha=0.6)
lines3, labels3 = ax3.get_legend_handles_labels()
lines4, labels4 = ax3_twin.get_legend_handles_labels()
ax3.legend(lines3 + lines4, labels3 + labels4, loc='center right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "dispatch_and_droop_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
cost_no_ess = np.sum(load_base * price)
cost_with_ess = np.sum(p_grid_opt * price)
savings = cost_no_ess - cost_with_ess

history = [
    {'Metric': 'Daily Electricity Bill (CNY)', 'Without Storage': f"¥{cost_no_ess:.1f}", 'With Storage (MPC)': f"¥{cost_with_ess:.1f}", 'Impact': f"Saved ¥{savings:.1f} per day"},
    {'Metric': 'Peak Grid Demand (kW)', 'Without Storage': f"{np.max(load_base):.1f} kW", 'With Storage (MPC)': f"{np.max(p_grid_opt):.1f} kW", 'Impact': 'Reduced transformer capacity needs'},
    {'Metric': 'Frequency Drop (49.8Hz)', 'Without Storage': 'No Support', 'With Storage (MPC)': f"Instantly injects {np.max(p_droop):.1f} kW", 'Impact': 'Prevents grid blackout'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "dispatch_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch06: Microgrid Economic Dispatch", "Diagram showing a battery connected to a factory and the main grid. A dollar sign is shown above the grid. At night (moon icon), the battery sucks power from the grid for cheap. At noon (sun icon), the battery powers the factory, saving massive amounts of money.")

print("Files generated successfully.")
