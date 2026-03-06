import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.integrate import odeint

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\CoupledTank_Book\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 双容水箱物理建模 (Coupled Tank Physical Modeling)
# 模拟两个非线性耦合水箱的动态响应，使用 ODE (常微分方程) 求解器

# 1. 物理参数设定
A1 = 1.0 # 水箱1 截面积 m^2
A2 = 1.0 # 水箱2 截面积 m^2
a12 = 0.05 # 水箱1到2之间连接阀门的流通面积 m^2
a2 = 0.04 # 水箱2出水阀门的流通面积 m^2
g = 9.81 # 重力加速度

# 2. 定义状态空间常微分方程 (State-Space ODE)
# dh1/dt = (Qin - q12) / A1
# dh2/dt = (q12 - qout) / A2
# 其中 q12 = a12 * sign(h1-h2) * sqrt(2g |h1-h2|)
#      qout = a2 * sqrt(2g h2)
def coupled_tank_dynamics(h, t, Qin):
    h1, h2 = h
    
    # 物理限制：水位不能小于 0
    h1 = max(0, h1)
    h2 = max(0, h2)
    
    # 计算水箱间的耦合流量 q12
    delta_h = h1 - h2
    q12 = a12 * np.sign(delta_h) * np.sqrt(2 * g * abs(delta_h))
    
    # 计算水箱2的出水流量 qout
    qout = a2 * np.sqrt(2 * g * h2)
    
    # 质量守恒差分
    dh1_dt = (Qin(t) - q12) / A1
    dh2_dt = (q12 - qout) / A2
    
    # 如果水位为 0 且导数小于 0，强制导数为 0 防止出现负水位
    if h1 <= 0 and dh1_dt < 0: dh1_dt = 0
    if h2 <= 0 and dh2_dt < 0: dh2_dt = 0
        
    return [dh1_dt, dh2_dt]

# 3. 模拟时间轴
t_end = 200 # 200秒
time = np.linspace(0, t_end, 1000)

# 4. 构建输入强迫曲线 (Step Input and Interruption)
def input_Qin(t):
    if t < 10:
        return 0.0
    elif 10 <= t < 100:
        return 0.5 # m^3/s
    elif 100 <= t < 150:
        return 0.0 # 突然关泵 (扰动)
    else:
        return 0.3 # 恢复较小的进水

# 5. 使用 scipy.integrate.odeint 求解非线性系统
h_init = [0.0, 0.0] # 初始空箱
h_result = odeint(coupled_tank_dynamics, h_init, time, args=(input_Qin,))

h1_traj = h_result[:, 0]
h2_traj = h_result[:, 1]

# 反算流量用于分析
Qin_traj = np.array([input_Qin(t) for t in time])
q12_traj = a12 * np.sign(h1_traj - h2_traj) * np.sqrt(2 * g * np.abs(h1_traj - h2_traj))
qout_traj = a2 * np.sqrt(2 * g * h2_traj)

# 6. 绘图展示非线性与耦合
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# A. 水位响应曲线 (非线性与二阶滞后)
ax1.plot(time, h1_traj, 'r-', linewidth=3, label='Tank 1 Level ($h_1$)')
ax1.plot(time, h2_traj, 'b-', linewidth=2, label='Tank 2 Level ($h_2$)')
ax1.set_ylabel('Water Level (m)', fontsize=12)
ax1.set_title('Nonlinear Coupled Dynamics: Water Level Response', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注二阶延迟
ax1.annotate('Tank 2 lags behind\nTank 1 (2nd Order)', 
             xy=(25, h2_traj[125]), xytext=(35, 1.0),
             arrowprops=dict(facecolor='blue', shrink=0.05))

# 标注非线性排空
ax1.annotate('Slower drainage at low levels\n(Torricelli $Q \propto \sqrt{h}$)', 
             xy=(140, 0.5), xytext=(120, 2.0),
             arrowprops=dict(facecolor='black', shrink=0.05))

# B. 流量守恒分析
ax2.fill_between(time, 0, Qin_traj, color='gray', alpha=0.3, label='Pump Inflow ($Q_{in}$)')
ax2.plot(time, q12_traj, 'm--', linewidth=2, label='Coupling Flow ($q_{12}$)')
ax2.plot(time, qout_traj, 'g-', linewidth=2, label='System Outflow ($q_{out}$)')

ax2.set_xlabel('Time (seconds)', fontsize=12)
ax2.set_ylabel('Flow Rate ($m^3/s$)', fontsize=12)
ax2.set_title('Mass Conservation & Energy Transfer', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "coupled_dynamics_sim.png"), dpi=300, bbox_inches='tight')

# 生成数据表格
history = []
snapshots = [20, 80, 110, 180]
labels = ["Initial Rise", "Steady State 1", "Pump Failure", "Steady State 2"]

for idx, t_snap in enumerate(snapshots):
    time_idx = np.argmin(np.abs(time - t_snap))
    history.append({
        'State': labels[idx],
        'Time (s)': t_snap,
        'Qin (m³/s)': round(Qin_traj[time_idx], 2),
        'h1 (m)': round(h1_traj[time_idx], 2),
        'h2 (m)': round(h2_traj[time_idx], 2),
        'q12 (m³/s)': round(q12_traj[time_idx], 2),
        'qout (m³/s)': round(qout_traj[time_idx], 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "dynamics_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch02: Coupled Tank Physics", "Diagram of two water tanks connected by a pipe. Water pumps into Tank 1. It flows into Tank 2 through a valve (coupling effect). Finally, it drains out of Tank 2. The math model shows ODEs governing the mass balance.")

print("Files generated successfully.")
