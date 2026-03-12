import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\energy-storage-system-modeling-control\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 锂离子电池的一阶/二阶等效电路模型 (Thevenin Model)
# 场景：展示在动态电流脉冲下，电池电压的欧姆降与极化弛豫现象

# 1. 模型参数 (NMC 锂离子电池估计值)
Q_capacity = 50.0 # 电池容量 (Ah)
R0 = 0.01 # 欧姆内阻 (Ohm)
R1 = 0.015 # 极化内阻 (Ohm)
C1 = 2000.0 # 极化电容 (F)
tau1 = R1 * C1 # 时间常数 (s)

# OCV-SOC 曲线 (简化为一个多项式函数)
def get_ocv(soc):
    # 根据典型 NMC 电池的 OCV-SOC 曲线拟合
    return 3.0 + 1.2 * soc - 0.5 * soc**2 + 0.5 * soc**3

# 2. 模拟环境设定 (HPPC 测试 - 混合脉冲功率特性测试)
t_end = 3600 # 秒
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 设定脉冲放电电流 (放电为正)
I_load = np.zeros(N)
I_load[500:800] = 50.0 # 1C 放电 5 分钟
I_load[1500:1800] = -50.0 # 1C 充电 5 分钟
I_load[2500:3000] = 100.0 # 2C 剧烈放电

# 3. 初始化状态变量
soc = np.zeros(N)
U1 = np.zeros(N) # 极化电压
V_terminal = np.zeros(N) # 端电压
OCV = np.zeros(N)

soc[0] = 0.8 # 初始 SOC 为 80%

# 4. 离散化微分方程求解
for k in range(1, N):
    # a. 安时积分计算 SOC
    soc[k] = soc[k-1] - (I_load[k] * dt) / (Q_capacity * 3600.0)
    
    # b. 更新 OCV
    OCV[k] = get_ocv(soc[k])
    
    # c. 一阶 RC 网络的电压更新 (极化过程)
    # dU1/dt = -U1/(R1*C1) + I/C1
    dU1_dt = -U1[k-1] / tau1 + I_load[k] / C1
    U1[k] = U1[k-1] + dU1_dt * dt
    
    # d. 计算端电压： V_t = OCV - I*R0 - U1
    V_terminal[k] = OCV[k] - I_load[k] * R0 - U1[k]

OCV[0] = get_ocv(soc[0])
V_terminal[0] = OCV[0]

# 5. 绘图展示
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

# A. 电流脉冲
ax1.plot(time, I_load, 'k-', linewidth=2, label='Load Current (A)')
ax1.set_ylabel('Current (A)\n(+Discharge, -Charge)', fontsize=12)
ax1.set_title('HPPC Test Profile (Current Excitation)', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='upper right')

# B. 电压响应
ax2.plot(time, OCV, 'g--', linewidth=2, label='Open Circuit Voltage (OCV)')
ax2.plot(time, V_terminal, 'r-', linewidth=2, label='Terminal Voltage ($V_t$)')

# 标注欧姆压降和极化弛豫
ax2.annotate('Instant Ohmic Drop\n($\Delta V = I \cdot R_0$)', xy=(500, 3.8), xytext=(200, 3.3),
             arrowprops=dict(facecolor='black', shrink=0.05))
ax2.annotate('Polarization Relaxation\n(RC Delay)', xy=(800, 3.9), xytext=(850, 3.5),
             arrowprops=dict(facecolor='blue', shrink=0.05))

ax2.set_ylabel('Voltage (V)', fontsize=12)
ax2.set_title('Battery Voltage Dynamic Response (Thevenin Model)', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='upper right')

# C. 极化电压分解
ax3.plot(time, I_load * R0, 'm-', linewidth=1.5, label='Ohmic Overpotential ($I \cdot R_0$)')
ax3.plot(time, U1, 'b-', linewidth=2, label='Polarization Overpotential ($U_1$)')
ax3.set_xlabel('Time (seconds)', fontsize=12)
ax3.set_ylabel('Overpotential (V)', fontsize=12)
ax3.set_title('Internal Voltage Drops', fontsize=14)
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "thevenin_model_sim.png"), dpi=300, bbox_inches='tight')

# 生成数据表格
history = [
    {'Time Phase': 't=500s (Pulse Start)', 'Current': '50 A (1C)', 'Instant Voltage Drop': f"{50*R0:.2f} V", 'Physical Meaning': 'Ohmic Resistance (Electrolyte)'},
    {'Time Phase': 't=800s (Pulse End)', 'Current': '0 A', 'Polarization Voltage': f"{np.max(U1[:1000]):.3f} V", 'Physical Meaning': 'Diffusion/Charge Transfer limit'},
    {'Time Phase': 't=800~1000s', 'Current': '0 A', 'Voltage Behavior': 'Exponential recovery to OCV', 'Physical Meaning': 'RC Relaxation phase'},
    {'Time Phase': 't=2500s (2C Pulse)', 'Current': '100 A (2C)', 'Instant Voltage Drop': f"{100*R0:.2f} V", 'Physical Meaning': 'Deep voltage sag risks undervoltage limit'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "thevenin_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch02: Equivalent Circuit Model", "Diagram of a Battery Thevenin Model. It shows an ideal voltage source (OCV) in series with a resistor (R0) and an RC network (R1/C1). Current flowing through the resistor causes an instant drop, while the capacitor creates a delayed sluggish response.")

print("Files generated successfully.")
