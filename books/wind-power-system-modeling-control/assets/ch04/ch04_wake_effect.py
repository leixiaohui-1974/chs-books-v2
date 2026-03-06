import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\wind-power-system-modeling-control\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 风电场尾流效应与协同控制 (Wake Effect & Farm Cooperative Control)
# 模拟一个 3 台风机串联阵列的尾流影响，并对比“贪婪控制”与“协同控制”的发电量差异

# 1. 物理参数
D = 80.0     # 风机叶轮直径 (m)
R = D / 2.0  # 半径
A = np.pi * R**2 # 扫风面积
rho = 1.225  # 空气密度 (kg/m^3)
U0 = 10.0    # 自由流初始风速 (m/s)

# Jensen 尾流模型参数
k_wake = 0.05 # 尾流衰减常数 (陆上风电场典型值 0.04-0.07)
spacing = 5 * D # 风机间距为 5 倍直径

# 简化风机功率模型
# 假设 Cp 是推力系数 Ct 的函数。理想状态下 Cp = 4 * a * (1-a)^2, Ct = 4 * a * (1-a)，其中 a 为轴向诱导因子
# 为方便计算，利用参数化多项式或直接查表。我们这里采用解析关系：
# 假设风机可以通过变桨或改变转速来调节推力系数 Ct
def calc_cp_from_ct(ct):
    # a = 0.5 * (1 - sqrt(1 - ct))
    if ct >= 1.0: ct = 0.99
    a = 0.5 * (1 - np.sqrt(1 - ct))
    cp = 4 * a * (1 - a)**2
    return max(0.0, cp)

# 2. Jensen 尾流模型 (单尾流)
# 计算下游 x 处的风速 U_x = U_in * [1 - (1 - sqrt(1 - Ct)) / (1 + k*x/R)^2]
def jensen_wake(U_in, Ct, x):
    if Ct >= 1.0: Ct = 0.99
    deficit = (1 - np.sqrt(1 - Ct)) / (1 + k_wake * x / R)**2
    U_out = U_in * (1 - deficit)
    return U_out

# 3. 模拟场景 A: 贪婪控制 (Greedy Control)
# 每台风机都自私地追求自己单机的功率最大化
# 单机理论最大 Cp 出现在 a=1/3 时，此时 Ct = 4*(1/3)*(2/3) = 8/9 = 0.888
Ct_greedy = 0.888
Cp_greedy = calc_cp_from_ct(Ct_greedy)

# 第一台风机 (WT1)
U1_greedy = U0
P1_greedy = 0.5 * rho * A * U1_greedy**3 * Cp_greedy

# 第二台风机 (WT2) 处于 WT1 的尾流中
U2_greedy = jensen_wake(U1_greedy, Ct_greedy, spacing)
P2_greedy = 0.5 * rho * A * U2_greedy**3 * Cp_greedy

# 第三台风机 (WT3) 处于 WT2 的尾流中 (叠加简化，假设尾流完全重合，使用深层跌落)
# 严格来说应该用平方和叠加，这里用简单的连乘序列逼近串联单行
U3_greedy = jensen_wake(U2_greedy, Ct_greedy, spacing)
P3_greedy = 0.5 * rho * A * U3_greedy**3 * Cp_greedy

Total_P_greedy = P1_greedy + P2_greedy + P3_greedy

# 4. 模拟场景 B: 协同控制 (Cooperative Control)
# 前排风机主动降低效率 (减小 Ct，例如通过偏航或变桨)，让更多风漏给后排
# 手动设置一个优化的 Ct 策略 (WT1 牺牲很多，WT2 牺牲一点，WT3 贪婪)
Ct_coop = [0.65, 0.75, 0.888]

# 第一台风机 (WT1)
U1_coop = U0
P1_coop = 0.5 * rho * A * U1_coop**3 * calc_cp_from_ct(Ct_coop[0])

# 第二台风机 (WT2)
U2_coop = jensen_wake(U1_coop, Ct_coop[0], spacing)
P2_coop = 0.5 * rho * A * U2_coop**3 * calc_cp_from_ct(Ct_coop[1])

# 第三台风机 (WT3)
U3_coop = jensen_wake(U2_coop, Ct_coop[1], spacing)
P3_coop = 0.5 * rho * A * U3_coop**3 * calc_cp_from_ct(Ct_coop[2])

Total_P_coop = P1_coop + P2_coop + P3_coop

# 5. 绘图对比
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 图 A: 风速沿阵列的跌落 (Wind Speed Deficit)
turbines = ['WT1 (Front)', 'WT2 (Middle)', 'WT3 (Rear)']
x_pos = [0, spacing, 2*spacing]
U_greedy_list = [U1_greedy, U2_greedy, U3_greedy]
U_coop_list = [U1_coop, U2_coop, U3_coop]

ax1.plot(x_pos, U_greedy_list, 'ro-', markersize=10, linewidth=2, label='Greedy Control')
ax1.plot(x_pos, U_coop_list, 'bo-', markersize=10, linewidth=3, label='Cooperative Control')
ax1.axhline(U0, color='k', linestyle='--', label='Free Stream Velocity ($U_0$)')

for i, txt in enumerate(turbines):
    ax1.annotate(txt, (x_pos[i], U0 + 0.2), ha='center', fontsize=10)

ax1.set_xticks(x_pos)
ax1.set_xticklabels(['0D', '5D', '10D'])
ax1.set_xlabel('Downstream Distance (x)', fontsize=12)
ax1.set_ylabel('Incident Wind Speed (m/s)', fontsize=12)
ax1.set_title('Wake Effect: Wind Speed Recovery', fontsize=14)
ax1.legend(loc='lower left')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注 WT1 放弃的能量让后面的风速更高
ax1.annotate('WT1 reduces thrust,\nallowing wind to pass', xy=(x_pos[1], U_coop_list[1]), xytext=(x_pos[1]-100, U_coop_list[1]+1.0),
             arrowprops=dict(facecolor='blue', shrink=0.05))

# 图 B: 各风机发电量对比与总发电量 (Power Output)
width = 0.35
x_idx = np.arange(len(turbines))
P_greedy_list = [P1_greedy/1000, P2_greedy/1000, P3_greedy/1000] # kW
P_coop_list = [P1_coop/1000, P2_coop/1000, P3_coop/1000] # kW

rects1 = ax2.bar(x_idx - width/2, P_greedy_list, width, label='Greedy Control', color='red', alpha=0.7)
rects2 = ax2.bar(x_idx + width/2, P_coop_list, width, label='Cooperative Control', color='blue', alpha=0.7)

# 添加总功率虚线横杠 (通过均值线或者文本展示，这里用文本)
ax2.set_xticks(x_idx)
ax2.set_xticklabels(turbines)
ax2.set_ylabel('Power Output (kW)', fontsize=12)
ax2.set_title('Individual Power & Farm Total Synergy', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, axis='y', linestyle='--', alpha=0.6)

# 标注增益
gain_percent = (Total_P_coop - Total_P_greedy) / Total_P_greedy * 100
ax2.text(1, max(P_greedy_list)*0.9, f"Total Farm Output:\nGreedy: {Total_P_greedy/1000:.1f} kW\nCoop: {Total_P_coop/1000:.1f} kW\nGain: +{gain_percent:.1f}%", 
         bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'), fontsize=12, ha='center')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "wake_cooperative_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = [
    {'Turbine': 'WT1 (Front)', 'Greedy Thrust Ct': 0.89, 'Greedy Power (kW)': round(P1_greedy/1000, 1), 'Coop Thrust Ct': Ct_coop[0], 'Coop Power (kW)': round(P1_coop/1000, 1), 'Status': 'Sacrificed'},
    {'Turbine': 'WT2 (Middle)', 'Greedy Thrust Ct': 0.89, 'Greedy Power (kW)': round(P2_greedy/1000, 1), 'Coop Thrust Ct': Ct_coop[1], 'Coop Power (kW)': round(P2_coop/1000, 1), 'Status': 'Benefited'},
    {'Turbine': 'WT3 (Rear)', 'Greedy Thrust Ct': 0.89, 'Greedy Power (kW)': round(P3_greedy/1000, 1), 'Coop Thrust Ct': Ct_coop[2], 'Coop Power (kW)': round(P3_coop/1000, 1), 'Status': 'Highly Benefited'},
    {'Turbine': 'FARM TOTAL', 'Greedy Thrust Ct': '-', 'Greedy Power (kW)': round(Total_P_greedy/1000, 1), 'Coop Thrust Ct': '-', 'Coop Power (kW)': round(Total_P_coop/1000, 1), 'Status': f"Net Gain: +{gain_percent:.1f}%"}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "wake_control_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch04: Wind Farm Wake Effect", "Diagram showing an array of three wind turbines. Wind blows from left to right. The first turbine extracts energy, creating a slow, turbulent 'wake' behind it, reducing the wind speed available for the downstream turbines.")

print("Files generated successfully.")
