import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 氧化铝蒸发工序痛点模拟 (Pain Points of Alumina Evaporation)
# 模拟人工控制下的浓度波动、高汽耗以及结疤(Scaling)导致的传热系数下降

# 1. 模拟时间设定 (连续运行 30 天)
days = 30
dt = 0.1 # 步长 0.1 天
time = np.arange(0, days, dt)
N = len(time)

np.random.seed(42)

# 2. 模拟结疤恶化效应 (Scaling Effect on Heat Transfer)
# 传热系数 K 随着天数指数/线性衰减
K_initial = 1200.0 # W/(m^2*K)
scaling_rate = 15.0 # 每天下降 15
K_actual = K_initial - scaling_rate * time + np.random.normal(0, 10, N)

# 3. 模拟进料波动 (Feed Disturbance)
# 进料浓度 (g/L)
feed_conc = 140.0 + 10.0 * np.sin(2 * np.pi * time / 5) + np.random.normal(0, 3, N)

# 4. 人工操作调度模拟 (Manual Control)
# 目标出料浓度为 240 g/L。操作员通过调节新鲜蒸汽量来控制浓度。
# 但是人工调节有滞后，而且往往过度调节 (Over-reaction)
target_conc = 240.0
steam_flow = np.zeros(N)
steam_flow[0] = 50.0 # 吨/小时

out_conc = np.zeros(N)
out_conc[0] = 230.0

# 汽耗比 (Steam Consumption Ratio) = 消耗蒸汽吨数 / 蒸发水量吨数
steam_ratio = np.zeros(N)

for i in range(1, N):
    # a. 物理传热过程 (简化)
    # 蒸发量正比于传热系数 K 和蒸汽量
    evap_water = (K_actual[i] / K_initial) * steam_flow[i-1] * 2.5 
    
    # b. 质量守恒计算出料浓度
    # 进料量设为恒定 300 t/h
    feed_flow = 300.0
    out_flow = feed_flow - evap_water
    if out_flow <= 0: out_flow = 1.0 # 防御
    
    current_out_conc = (feed_flow * feed_conc[i]) / out_flow
    out_conc[i] = current_out_conc
    
    # 计算实际汽耗比
    steam_ratio[i] = steam_flow[i-1] / evap_water if evap_water > 0 else 0
    
    # c. 人工反馈调节 (每 0.5 天人工看一次表)
    if i % 5 == 0:
        error = target_conc - current_out_conc
        # 人工拍脑袋加减蒸汽 (容易过冲，引入较小比例)
        adjustment = 0.2 * error 
        
        # 因为传热系数 K 下降，为了达到同样的蒸发量，操作员被迫不断增加蒸汽基础量
        k_compensation = (K_initial / K_actual[i]) * 50.0
        
        steam_flow[i] = k_compensation + adjustment
        # 物理阀门限制
        steam_flow[i] = max(20.0, min(steam_flow[i], 120.0))
    else:
        steam_flow[i] = steam_flow[i-1]

# 5. 绘图展示痛点
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 结疤导致的传热系数下降
ax1.plot(time, K_actual, 'k-', linewidth=2, label='Overall Heat Transfer Coefficient $K$')
ax1.set_ylabel('Heat Transfer $K$ (W/$m^2$K)', fontsize=12)
ax1.set_title('Pain Point 1: Severe Scaling (结疤) reducing efficiency over time', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 人工控制导致的浓度剧烈波动
ax2.plot(time, out_conc, 'r-', linewidth=2, label='Actual Output Concentration')
ax2.axhline(target_conc, color='g', linestyle='--', linewidth=3, label='Target (240 g/L)')
ax2.axhspan(235, 245, color='green', alpha=0.2, label='Acceptable Range')

ax2.set_ylabel('Concentration (g/L)', fontsize=12)
ax2.set_title('Pain Point 2: Poor Manual Control under Feed Disturbances', fontsize=14)
ax2.legend(loc='lower right')
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 汽耗比飙升
# 平滑一下画线
steam_ratio_smooth = pd.Series(steam_ratio).rolling(window=10, min_periods=1).mean()
ax3.plot(time, steam_ratio_smooth, 'b-', linewidth=3, label='Steam Consumption Ratio (汽耗比)')
ax3.set_xlabel('Operation Time (Days)', fontsize=12)
ax3.set_ylabel('Steam Ratio (t/t)', fontsize=12)
ax3.set_title('Pain Point 3: Skyrocketing Energy Cost to maintain production', fontsize=14)
ax3.legend(loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)

# 标注恶化点
ax3.annotate('Boilers forced to pump more steam\nas pipes get clogged by scale', 
             xy=(25, steam_ratio_smooth.iloc[250]), xytext=(10, steam_ratio_smooth.iloc[250]+0.05),
             arrowprops=dict(facecolor='blue', shrink=0.05))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "evaporation_pain_points.png"), dpi=300, bbox_inches='tight')

# 生成数据表格
history = []
snapshots = [1, 10, 20, 29] # 第 1, 10, 20, 29 天

for day in snapshots:
    idx = int(day / dt)
    history.append({
        'Day': day,
        'Heat Transfer K': round(K_actual[idx], 0),
        'Output Conc. (g/L)': round(out_conc[idx], 1),
        'Steam Flow (t/h)': round(steam_flow[idx], 1),
        'Steam Ratio (t/t)': round(steam_ratio[idx], 3),
        'Plant Status': 'Clean & Efficient' if day < 5 else ('Scaling begins' if day < 15 else 'Severe Scaling (Clean required)')
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "pain_points_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch01: Alumina Evaporation Pain Points", "Diagram showing a massive multi-effect evaporator. Steam enters from the left to boil liquor. Over time, thick scale (结疤) builds up on the pipes, blocking heat transfer. An exhausted operator tries to manually turn a steam valve but fails to stabilize the output.")

print("Files generated successfully.")
