import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\wind-power-system-modeling-control\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 双馈感应发电机 (DFIG) 定子磁链定向矢量控制 (Stator Flux Oriented Control)
# 模拟转子侧变流器 (RSC) 如何通过控制转子电流 (ird, irq) 来独立解耦控制定子有功功率(Ps)和无功功率(Qs)

# 1. DFIG 物理参数 (基于 2MW 级风机)
Rs = 0.01   # 定子电阻 (pu)
Rr = 0.01   # 转子电阻 (pu)
Lm = 3.0    # 激磁电感 (pu)
Lls = 0.1   # 定子漏感 (pu)
Llr = 0.1   # 转子漏感 (pu)
Ls = Lm + Lls
Lr = Lm + Llr

omega_s = 1.0 # 电网同步角速度 (pu) = 2*pi*50 Hz
Vs = 1.0 # 电网电压 (pu)

# 在定子磁链定向下，简化公式：
# 磁链 Psi_s = Vs / omega_s (假定 Rs = 0)
Psi_s = Vs / omega_s
# 有功功率 Ps = - (3/2) * (Lm / Ls) * Vs * irq
# 无功功率 Qs = (3/2) * (Vs * Psi_s / Ls) - (3/2) * (Lm / Ls) * Vs * ird

# 为方便，使用标幺值计算，去掉 (3/2) 系数
def calc_power(ird, irq):
    Ps = - (Lm / Ls) * Vs * irq
    Qs = (Vs * Psi_s / Ls) - (Lm / Ls) * Vs * ird
    return Ps, Qs

# 2. 模拟控制时间序列
t_end = 5.0 # 秒
dt = 0.005
time = np.arange(0, t_end, dt)
N = len(time)

# 目标指令 (References)
# 前 1 秒：待机
# 1-3 秒：有功功率 Ps 阶跃响应 (风速突然增加)
# 3-5 秒：无功功率 Qs 阶跃响应 (电网要求支撑电压)
Ps_ref = np.zeros(N)
Ps_ref[time >= 1.0] = 0.8 # 达到 0.8 pu 有功
Qs_ref = np.zeros(N)
Qs_ref[time >= 3.0] = -0.3 # 吸收 0.3 pu 无功

# PI 控制器参数
Kp_p = 2.0; Ki_p = 10.0
Kp_q = 2.0; Ki_q = 10.0

# 状态变量
Ps_actual = np.zeros(N)
Qs_actual = np.zeros(N)
irq_ref = np.zeros(N)
ird_ref = np.zeros(N)
irq_actual = np.zeros(N)
ird_actual = np.zeros(N)

# 转子电流内部环的近似 (一阶惯性环节)
tau_i = 0.02 # 电流环响应时间 20ms

int_err_p = 0.0
int_err_q = 0.0

# 3. 仿真循环
for i in range(1, N):
    # 外环：功率控制 -> 产生转子电流参考值 (ird*, irq*)
    err_p = Ps_ref[i] - Ps_actual[i-1]
    int_err_p += err_p * dt
    irq_ref[i] = -(Kp_p * err_p + Ki_p * int_err_p) # Ps 与 irq 成反比
    
    err_q = Qs_ref[i] - Qs_actual[i-1]
    int_err_q += err_q * dt
    # 因为 Qs = C1 - C2 * ird, 所以 ird 增加会导致 Qs 减小
    ird_ref[i] = -(Kp_q * err_q + Ki_q * int_err_q) 
    
    # 内环：电流响应 (近似为一阶延迟)
    irq_actual[i] = irq_actual[i-1] + (irq_ref[i] - irq_actual[i-1]) * (dt / tau_i)
    ird_actual[i] = ird_actual[i-1] + (ird_ref[i] - ird_actual[i-1]) * (dt / tau_i)
    
    # 物理计算：输出功率
    Ps_actual[i], Qs_actual[i] = calc_power(ird_actual[i], irq_actual[i])

# 4. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 图 A: 有功/无功解耦跟踪 (Decoupled Power Tracking)
ax1.plot(time, Ps_ref, 'b--', linewidth=2, label='Active Power Reference $P_s^*$')
ax1.plot(time, Ps_actual, 'b-', linewidth=3, alpha=0.7, label='Actual Active Power $P_s$')
ax1.plot(time, Qs_ref, 'r--', linewidth=2, label='Reactive Power Reference $Q_s^*$')
ax1.plot(time, Qs_actual, 'r-', linewidth=3, alpha=0.7, label='Actual Reactive Power $Q_s$')

ax1.set_ylabel('Power (pu)', fontsize=12)
ax1.set_title('DFIG Stator Flux Oriented Control: Decoupled P/Q Tracking', fontsize=14)
ax1.legend(loc='lower right', ncol=2)
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注解耦特性
ax1.annotate('Active power step\nNo impact on Q', xy=(1.2, 0.8), xytext=(0.2, 0.5),
             arrowprops=dict(facecolor='blue', shrink=0.05))
ax1.annotate('Reactive power step\nNo impact on P', xy=(3.2, -0.3), xytext=(2.2, 0.0),
             arrowprops=dict(facecolor='red', shrink=0.05))

# 图 B: 转子电流 d/q 轴分量 (Rotor Currents)
ax2.plot(time, irq_actual, 'b-', linewidth=2, label='q-axis Rotor Current $i_{rq}$ (Controls P)')
ax2.plot(time, ird_actual, 'r-', linewidth=2, label='d-axis Rotor Current $i_{rd}$ (Controls Q)')

ax2.set_xlabel('Time (seconds)', fontsize=12)
ax2.set_ylabel('Rotor Current (pu)', fontsize=12)
ax2.set_title('Rotor Current Components (dq reference frame)', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "dfig_vector_control_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [0.5, 2.0, 4.0]
labels = ["Standby", "Active Power Step", "Reactive Power Step"]

for idx, t_snap in enumerate(snapshots):
    i = int(t_snap / dt)
    history.append({
        'State': labels[idx],
        'Time (s)': t_snap,
        'Ps Ref (pu)': Ps_ref[i],
        'Ps Actual (pu)': round(Ps_actual[i], 3),
        'Qs Ref (pu)': Qs_ref[i],
        'Qs Actual (pu)': round(Qs_actual[i], 3),
        'irq (q-axis current)': round(irq_actual[i], 3),
        'ird (d-axis current)': round(ird_actual[i], 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "dfig_control_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch02: DFIG Vector Control", "Diagram of a Doubly-Fed Induction Generator. Stator is connected directly to grid. Rotor is connected via a back-to-back converter. Shows coordinate transformation from abc to dq axes for decoupled P/Q control.")

print("Files generated successfully.")
