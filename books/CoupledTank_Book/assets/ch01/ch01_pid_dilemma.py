import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\CoupledTank_Book\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 水务系统中的液位控制之困 (Liquid Level Control Dilemma)
# 模拟单体水箱在传统 PID 控制下，面对大滞后与强耦合时常见的“超调(Overshoot)”和“震荡(Oscillation)”痛点。

# 1. 模拟环境设定
t_end = 200 # 秒
dt = 0.5
time = np.arange(0, t_end, dt)
N = len(time)

# 目标液位 (Setpoint)
H_target = np.ones(N) * 2.0
H_target[60:] = 4.0 # 60秒时要求水位提升至 4.0m

# 2. 物理模型 (积分型对象 + 纯滞后 + 非线性出水)
Area = 2.0 # 水箱截面积 m^2
valve_k = 0.5 # 底部出水阀门阻力系数 (出水正比于 sqrt(H))

# 系统延迟 (泵开启到水流到水箱的管道延迟)
delay_steps = int(4.0 / dt) # 4秒纯滞后

# 3. 模拟传统 PID 痛点
# A: 反应慢且超调的 PI 控制 (调得不好，积分饱和)
# B: 强耦合导致按下一个葫芦浮起一个瓢 (模拟突然的下游需求波动)

H_pid = np.zeros(N)
U_pid = np.zeros(N) # 水泵输入量
H_pid[0] = 2.0
U_pid[0] = valve_k * np.sqrt(2.0) # 维持初始平衡

Kp = 1.0
Ki = 0.05
integral = 0.0

# 引入一个外部强扰动 (下游用户突然打开大阀门抽水)
disturbance = np.zeros(N)
disturbance[260:340] = 0.3 # 130-170秒，突然抽水

for i in range(1, N):
    # a. 读取当前水位并计算误差
    error = H_target[i] - H_pid[i-1]
    
    # 模拟积分抗饱和 (Anti-windup) 
    if not ((U_pid[i-1] == 2.0 and error > 0) or (U_pid[i-1] == 0.0 and error < 0)):
        integral += error * dt
    
    # 计算控制量
    U_cmd = Kp * error + Ki * integral
    
    # 执行机构物理限制 (水泵最大只能抽 2.0 m3/s，最小为 0)
    U_pid[i] = max(0.0, min(2.0, U_cmd))
    
    # b. 物理世界的水位更新
    # 带有纯滞后的进水
    inflow = U_pid[i - delay_steps] if i >= delay_steps else U_pid[0]
    
    # 非线性出水 + 外部扰动
    outflow = valve_k * np.sqrt(max(0, H_pid[i-1])) + disturbance[i]
    
    # 积分环节 dH = (Qin - Qout) / A * dt
    H_pid[i] = H_pid[i-1] + (inflow - outflow) / Area * dt
    H_pid[i] = max(0, H_pid[i]) # 防干烧

# 4. 绘图展示痛点
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# A. 水位追踪曲线 (展示超调与滞后)
ax1.plot(time, H_target, 'k--', linewidth=2, label='Target Level (Setpoint)')
ax1.plot(time, H_pid, 'r-', linewidth=2.5, label='Actual Water Level (PID Control)')

# 标注痛点1：纯滞后导致反应慢
ax1.annotate('Dead Time:\nPump turns on, but water\ntakes 10s to arrive', 
             xy=(65, 2.0), xytext=(35, 3.0),
             arrowprops=dict(facecolor='black', shrink=0.05))

# 标注痛点2：积分饱和导致严重超调
ax1.annotate('Overshoot:\nIntegral windup forces\nlevel above target', 
             xy=(95, np.max(H_pid)), xytext=(110, 4.8),
             arrowprops=dict(facecolor='red', shrink=0.05))

ax1.axvspan(120, 160, color='gray', alpha=0.2, label='External User Draw-off Disturbance')

ax1.set_ylabel('Water Level (m)', fontsize=12)
ax1.set_title('Pain Point 1: Overshoot and Sluggish Response due to Dead Time', fontsize=14)
ax1.legend(loc='lower right')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 控制器动作 (展示执行机构的疯狂)
ax2.plot(time, U_pid, 'b-', linewidth=2, label='Pump Command (Inflow)')
ax2.plot(time, disturbance, 'm:', linewidth=2, label='Downstream Disturbance (Outflow)')
ax2.axhline(3.0, color='r', linestyle=':', label='Pump Saturation Limit')

ax2.annotate('Pump saturated at 100%', xy=(70, 3.0), xytext=(80, 2.5),
             arrowprops=dict(facecolor='blue', shrink=0.05))

ax2.set_xlabel('Time (seconds)', fontsize=12)
ax2.set_ylabel('Flow Rate ($m^3/s$)', fontsize=12)
ax2.set_title('Pain Point 2: Actuator Saturation and Disturbance Rejection Failure', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "pid_dilemma_sim.png"), dpi=300, bbox_inches='tight')

# 生成数据表格
history = [
    {'Time Phase': 't=60s (Setpoint Step)', 'System State': 'Target rises from 2m to 4m', 'Controller Action': 'Pump ramps to 100% instantly', 'Physical Consequence': 'No immediate level change due to 10s pipe delay'},
    {'Time Phase': 't=95s (Overshoot)', 'System State': f"Level peaks at {np.max(H_pid):.2f}m", 'Controller Action': 'Pump finally shuts off', 'Physical Consequence': 'Dangerous overfill (Integral Windup)'},
    {'Time Phase': 't=120s (Disturbance)', 'System State': 'Downstream valve suddenly opens', 'Controller Action': 'Slowly reacts after level drops', 'Physical Consequence': f"Level drops to {np.min(H_pid[120:180]):.2f}m, failing to hold target"}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "pid_pain_points_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch01: The Level Control Dilemma", "Diagram showing a frantic operator looking at a water tank. He opens the pump, but the water takes 10 seconds to arrive through a long pipe. Impatient, he opens it wider. When the water finally arrives, it overflows the tank.")

print("Files generated successfully.")
