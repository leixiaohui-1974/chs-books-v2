import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\photovoltaic-system-modeling-control\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 微电网孤岛运行与下垂控制 (Microgrid Islanding & Droop Control)
# 场景：主电网断电，两台光伏/储能逆变器组成孤岛微电网。
# 利用 P-f 和 Q-V 下垂控制实现无通信的功率均分。

# 1. 模拟参数设定
t_end = 5.0 # 秒
dt = 0.001
time = np.arange(0, t_end, dt)
N = len(time)

# 额定参数
f_nom = 50.0 # Hz
V_nom = 311.0 # V peak

# 逆变器参数 (Droop coefficients)
# 逆变器 1 (大容量)
kp1 = 0.005 # P-f 下垂系数 Hz/W
kq1 = 0.02  # Q-V 下垂系数 V/Var
# 逆变器 2 (小容量)
kp2 = 0.01  # P-f 下垂系数 Hz/W (是1的两倍，代表容量是1的一半)
kq2 = 0.04  # Q-V 下垂系数 V/Var

# 2. 负荷需求 (Load Demand)
P_load = np.ones(N) * 200.0 # 初始总有功需求 200W
Q_load = np.ones(N) * 50.0  # 初始总无功需求 50Var

# t=2.0s 投入一个大负载
P_load[time >= 2.0] += 300.0 # 总有功 500W
Q_load[time >= 2.0] += 150.0 # 总无功 200Var

# 3. 动态状态变量
f_sys = np.ones(N) * f_nom
V_sys = np.ones(N) * V_nom

P1 = np.zeros(N)
Q1 = np.zeros(N)
P2 = np.zeros(N)
Q2 = np.zeros(N)

# 初始稳态功率
P1[0] = 200.0 * (1/kp1) / (1/kp1 + 1/kp2)
P2[0] = 200.0 * (1/kp2) / (1/kp1 + 1/kp2)
Q1[0] = 50.0 * (1/kq1) / (1/kq1 + 1/kq2)
Q2[0] = 50.0 * (1/kq2) / (1/kq1 + 1/kq2)

# 低通滤波器时间常数 (模拟逆变器功率测量的延迟)
tau = 0.05 

for i in range(1, N):
    # a. 下垂控制方程 (Droop Equations)
    # f = f_nom - kp * P
    # V = V_nom - kq * Q
    
    # 物理上，所有逆变器连在一起，系统频率和电压必须是一致的
    # f_sys = f_nom - kp1*P1 = f_nom - kp2*P2
    # P1 + P2 = P_load
    
    # 我们用动态过程模拟这种收敛
    # 假设微电网的频率响应由等效惯性或逆变器群控制产生
    # P_sys_gen = P1 + P2
    # df/dt ~ (P_sys_gen - P_load)
    
    # 这里使用一种简化的准稳态代数逼近，加上低通滤波模拟暂态
    # 稳态时：P1 = (f_nom - f) / kp1, P2 = (f_nom - f) / kp2
    # (f_nom - f)*(1/kp1 + 1/kp2) = P_load
    f_target = f_nom - P_load[i] / (1/kp1 + 1/kp2)
    V_target = V_nom - Q_load[i] / (1/kq1 + 1/kq2)
    
    # 频率和电压的惯性演进
    f_sys[i] = f_sys[i-1] + (f_target - f_sys[i-1]) * (dt / tau)
    V_sys[i] = V_sys[i-1] + (V_target - V_sys[i-1]) * (dt / tau)
    
    # 逆变器根据感知到的电网频率和电压，自动调整输出功率
    P1_target = (f_nom - f_sys[i]) / kp1
    P2_target = (f_nom - f_sys[i]) / kp2
    
    Q1_target = (V_nom - V_sys[i]) / kq1
    Q2_target = (V_nom - V_sys[i]) / kq2
    
    P1[i] = P1[i-1] + (P1_target - P1[i-1]) * (dt / tau)
    P2[i] = P2[i-1] + (P2_target - P2[i-1]) * (dt / tau)
    
    Q1[i] = Q1[i-1] + (Q1_target - Q1[i-1]) * (dt / tau)
    Q2[i] = Q2[i-1] + (Q2_target - Q2[i-1]) * (dt / tau)

# 4. 绘图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 孤岛微电网系统频率与电压 (System f and V)
ax1.plot(time, f_sys, 'r-', linewidth=3, label='System Frequency ($f$)')
ax1.axhline(f_nom, color='k', linestyle=':', label='Nominal Freq (50Hz)')

ax1_twin = ax1.twinx()
ax1_twin.plot(time, V_sys, 'b--', linewidth=2, label='System Voltage ($V$)')
ax1_twin.axhline(V_nom, color='gray', linestyle=':', label='Nominal Volt (311V)')

ax1.set_ylabel('Frequency (Hz)', color='r', fontsize=12)
ax1_twin.set_ylabel('Voltage (V peak)', color='b', fontsize=12)
ax1.tick_params(axis='y', labelcolor='r')
ax1_twin.tick_params(axis='y', labelcolor='b')

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax1_twin.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='lower left')
ax1.set_title('Microgrid Islanding: Droop-induced f & V Deviations', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)

ax1.annotate('Load steps up\ncausing f & V drop', xy=(2.0, f_sys[int(2.1/dt)]), xytext=(0.5, 49.0),
             arrowprops=dict(facecolor='black', shrink=0.05))

# B. 有功功率自动按比例均分 (Active Power Sharing)
ax2.plot(time, P_load, 'k--', linewidth=2, label='Total Load Demand')
ax2.plot(time, P1, 'r-', linewidth=3, label='INV 1 Active Power ($k_{p1}=0.005$)')
ax2.plot(time, P2, 'b-', linewidth=2, label='INV 2 Active Power ($k_{p2}=0.010$)')

ax2.set_ylabel('Active Power (W)', fontsize=12)
ax2.set_title('P-f Droop Control: Proportional Active Power Sharing (2:1 Ratio)', fontsize=14)
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 无功功率自动按比例均分 (Reactive Power Sharing)
ax3.plot(time, Q_load, 'k--', linewidth=2, label='Total Reactive Demand')
ax3.plot(time, Q1, 'r-', linewidth=3, label='INV 1 Reactive Power ($k_{q1}=0.02$)')
ax3.plot(time, Q2, 'b-', linewidth=2, label='INV 2 Reactive Power ($k_{q2}=0.04$)')

ax3.set_xlabel('Time (seconds)', fontsize=12)
ax3.set_ylabel('Reactive Power (Var)', fontsize=12)
ax3.set_title('Q-V Droop Control: Proportional Reactive Power Sharing', fontsize=14)
ax3.legend(loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "droop_control_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 提取稳态值
idx_1 = int(1.5 / dt) # t=1.5s
idx_2 = int(4.5 / dt) # t=4.5s

history = [
    {'Scenario': 'Light Load (t<2s)', 'Sys Freq (Hz)': round(f_sys[idx_1], 2), 'Sys Volt (V)': round(V_sys[idx_1], 1), 'INV1 Power (W)': round(P1[idx_1], 1), 'INV2 Power (W)': round(P2[idx_1], 1), 'Power Sharing Ratio': f"{round(P1[idx_1]/P2[idx_1], 1)}:1"},
    {'Scenario': 'Heavy Load (t>2s)', 'Sys Freq (Hz)': round(f_sys[idx_2], 2), 'Sys Volt (V)': round(V_sys[idx_2], 1), 'INV1 Power (W)': round(P1[idx_2], 1), 'INV2 Power (W)': round(P2[idx_2], 1), 'Power Sharing Ratio': f"{round(P1[idx_2]/P2[idx_2], 1)}:1"}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "droop_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch04: Microgrid Droop Control", "Diagram showing an isolated microgrid cut off from the main grid. Two inverters are powering a city. They have no communication wire between them, but they perfectly share the load by 'listening' to the tiny drops in frequency and voltage.")

print("Files generated successfully.")
