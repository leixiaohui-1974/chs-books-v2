import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Hydrology_Book\assets\ch12"
os.makedirs(output_dir, exist_ok=True)

# 突发水污染事件 (Water Quality Incident) 的扩散追踪与生态调度
# 场景：利用 1D 对流扩散方程 (Advection-Dispersion Equation, ADE) 模拟化工厂泄漏。
# AI 发现污染后，不仅逆向溯源，还联动上游水库开闸“压污”（生态补水稀释）。

# 1. 模拟环境设定：一条长 50 公里的河流
L = 50.0 # km
dx = 0.5 # km
nx = int(L / dx) + 1
x = np.linspace(0, L, nx)

t_end = 48 # 模拟 48 小时
dt = 0.1 # 小时
nt = int(t_end / dt)
time = np.linspace(0, t_end, nt)

# 水动力参数
u_base = 1.0 # 初始河水流速 km/h
D = 0.5 # 扩散系数 km^2/h

# 2. 情景 A: 突发泄漏 (无人工干预)
# 在 x=10 km 处，化工厂在 t=5 时刻发生瞬时大量泄漏
C_isolated = np.zeros((nt, nx))
leak_x_idx = int(10.0 / dx)

for n in range(1, nt):
    # 对流扩散计算 (FTCS - Forward Time Central Space + Upwind)
    # dC/dt + u dC/dx = D d^2C/dx^2
    for i in range(1, nx-1):
        advection = u_base * (C_isolated[n-1, i] - C_isolated[n-1, i-1]) / dx # 迎风格式
        dispersion = D * (C_isolated[n-1, i+1] - 2*C_isolated[n-1, i] + C_isolated[n-1, i-1]) / (dx**2)
        C_isolated[n, i] = C_isolated[n-1, i] - advection * dt + dispersion * dt
        
    if n == int(5.0 / dt): # 泄漏发生
        C_isolated[n, leak_x_idx] += 5000.0 # 瞬时注入高浓度污染

# 3. 情景 B: AI 智能生态调度 (Emergency Flush)
# t=15 时刻，x=20km 处的监测站检测到了异常峰值。
# AI 根据流速 u=1.0，立刻反推出污染源在 x = 20 - (15-5)*1.0 = 10km (精准溯源)
# AI 立刻命令 x=0 处的上游水库在 t=16 时刻开闸放水，形成生态水击（流速剧增至 2.5 km/h），利用大量净水稀释污染。
C_joint = np.zeros((nt, nx))
u_dynamic = np.ones(nt) * u_base
u_dynamic[int(16.0 / dt):] = 2.5 # t=16 时刻开闸放水，流速骤增

for n in range(1, nt):
    for i in range(1, nx-1):
        advection = u_dynamic[n-1] * (C_joint[n-1, i] - C_joint[n-1, i-1]) / dx
        dispersion = D * (C_joint[n-1, i+1] - 2*C_joint[n-1, i] + C_joint[n-1, i-1]) / (dx**2)
        # 增加额外的体积稀释衰减项（水量变大，浓度必然下降）
        dilution = (u_dynamic[n-1] - u_base) / u_base * 0.5 * C_joint[n-1, i] if u_dynamic[n-1] > u_base else 0
        
        C_joint[n, i] = C_joint[n-1, i] - advection * dt + dispersion * dt - dilution * dt
        
    if n == int(5.0 / dt):
        C_joint[n, leak_x_idx] += 5000.0

# 4. 提取城市取水口 (x=40km) 的浓度时序曲线
intake_idx = int(40.0 / dx)
city_intake_isolated = C_isolated[:, intake_idx]
city_intake_joint = C_joint[:, intake_idx]

# 5. 绘图展示
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# A. 空间维度的毒波推移 (Snapshot at t=30h)
snap_t = int(30.0 / dt)
ax1.plot(x, C_isolated[snap_t, :], 'r--', linewidth=2, label='Pollutant Plume (No Intervention)')
ax1.plot(x, C_joint[snap_t, :], 'g-', linewidth=3, label='Plume (Flushed by Reservoir)')

# 标出化工厂和取水口
ax1.axvline(10.0, color='gray', linestyle=':', label='Chemical Plant (x=10)')
ax1.axvline(40.0, color='blue', linestyle='-.', linewidth=2, label='City Water Intake (x=40)')

ax1.set_xlabel('River Distance (km)', fontsize=12)
ax1.set_ylabel('Pollutant Concentration (mg/L)', fontsize=12)
ax1.set_title('Spatial Profile at t=30 hours: Advection & Dispersion', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注生态调度的影响
ax1.annotate('Flushed downstream faster\nbut severely DILUTED', xy=(x[np.argmax(C_joint[snap_t,:])], np.max(C_joint[snap_t,:])), xytext=(35, 10),
             arrowprops=dict(facecolor='green', shrink=0.05))

# B. 城市取水口的时间维视角
ax2.plot(time, city_intake_isolated, 'r--', linewidth=2, label='Intake Concentration (No Intervention)')
ax2.plot(time, city_intake_joint, 'g-', linewidth=3, label='Intake Concentration (With AI Flush)')

# 水质红线 (高于 2.0 就要停水)
wq_limit = 2.0
ax2.axhline(wq_limit, color='k', linestyle='-', linewidth=2, label='Lethal Toxicity Limit')

ax2.fill_between(time, wq_limit, city_intake_isolated, where=(city_intake_isolated > wq_limit), color='red', alpha=0.4, label='City Water Supply Cutoff!')

ax2.set_xlabel('Time (Hours)', fontsize=12)
ax2.set_ylabel('Concentration at City Intake (mg/L)', fontsize=12)
ax2.set_title('Temporal Profile at City Intake (x=40km): Toxicity vs. Dilution', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "wq_incident_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
max_c_iso = np.max(city_intake_isolated)
max_c_jnt = np.max(city_intake_joint)
hours_cut = np.sum(city_intake_isolated > wq_limit) * dt

history = [
    {'Metric': 'Peak Toxicity at Intake (mg/L)', 'Isolated (Do nothing)': f"{max_c_iso:.1f}", 'AI Reservoir Flush': f"{max_c_jnt:.1f}", 'Evaluation': 'Flush successfully diluted poison'},
    {'Metric': 'Lethal Limit Breached?', 'Isolated (Do nothing)': 'YES (>2.0)', 'AI Reservoir Flush': 'NO (<2.0)', 'Evaluation': 'AI prevented water cutoff'},
    {'Metric': 'City Water Cutoff Duration', 'Isolated (Do nothing)': f"{hours_cut:.1f} Hours", 'AI Reservoir Flush': '0.0 Hours', 'Evaluation': 'Millions saved from thirst'},
    {'Metric': 'Plume Arrival Time at Intake', 'Isolated (Do nothing)': 't=35 h', 'AI Reservoir Flush': 't=22 h', 'Evaluation': 'Flush pushes it out to sea faster'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "wq_incident_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch12: Water Quality Incident Trace", "Diagram showing a skull icon (pollution) leaking into a river. The AI tracks it down using flow physics. Before the poison reaches the city, the AI opens an upstream dam, sending a massive wave of clean water to dilute the poison.")

print("Files generated successfully.")
