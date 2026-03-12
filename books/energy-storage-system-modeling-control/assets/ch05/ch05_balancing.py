import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\energy-storage-system-modeling-control\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 电池管理系统 (BMS) 与均衡控制：木桶效应的救赎
# 场景：展示由于电芯单体内阻和容量的不一致性导致的“木桶效应”，
# 以及主动均衡电路 (Active Balancing) 是如何从高电压电芯“偷电”并充给低电压电芯的。

# 1. 模拟环境设定：3串联电芯电池组 (3S1P)
t_end = 3600 # 秒 (1 小时)
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 2. 电芯参数不一致性 (Inconsistency)
# Cell 1: 健康电芯 (容量大，内阻小)
# Cell 2: 老化电芯 (容量小，内阻大) -> 木桶的短板
# Cell 3: 普通电芯
Q_caps = np.array([50.0, 42.0, 48.0]) # Ah
R_ohms = np.array([0.01, 0.02, 0.012]) # Ohm

# 初始 SOC 也存在差异
soc_init = np.array([0.30, 0.25, 0.28])

def get_ocv(soc):
    # 极简 OCV 曲线
    return 3.0 + 1.2 * soc

# 放电电流曲线 (恒流放电 20A)
I_load = np.ones(N) * 20.0

# 3. 情景 A：无均衡控制 (No Balancing) - 木桶效应发作
soc_no_bal = np.zeros((3, N))
soc_no_bal[:, 0] = soc_init
v_no_bal = np.zeros((3, N))

for k in range(1, N):
    for i in range(3):
        # 无均衡时，每个电芯流过的电流完全等于总负载电流
        soc_no_bal[i, k] = soc_no_bal[i, k-1] - (I_load[k] * dt) / (Q_caps[i] * 3600.0)
        v_no_bal[i, k] = get_ocv(soc_no_bal[i, k]) - I_load[k] * R_ohms[i]

v_no_bal[:, 0] = get_ocv(soc_init) - I_load[0] * R_ohms

# 找到什么时候 Cell 2 (短板) 触及了放电截止电压 (2.8V)
cutoff_idx_no_bal = np.where(v_no_bal[1, :] < 2.8)[0][0]

# 4. 情景 B：主动均衡控制 (Active Balancing)
# 均衡逻辑：使用 DC/DC 变换器，将最高 SOC 的电芯电流抽出，注入最低 SOC 的电芯。
# 设定均衡电流能力为最大 5A
soc_bal = np.zeros((3, N))
soc_bal[:, 0] = soc_init
v_bal = np.zeros((3, N))
I_balance = np.zeros((3, N)) # 记录均衡电流 (+代表被注入，-代表被抽出)

max_bal_current = 5.0

for k in range(1, N):
    # 极简的主动均衡算法 (基于 SOC 差异的比例控制)
    mean_soc = np.mean(soc_bal[:, k-1])
    for i in range(3):
        # 与平均值的差异
        delta_soc = mean_soc - soc_bal[i, k-1]
        # P 控制器计算均衡电流
        cmd_i = delta_soc * 100.0 
        I_balance[i, k] = np.clip(cmd_i, -max_bal_current, max_bal_current)
        
    # 为了保证能量守恒 (忽略 DC/DC 损耗)，将总和微调至 0
    I_balance[:, k] -= np.mean(I_balance[:, k])

    for i in range(3):
        # 实际电芯感受到的电流 = 负载电流 - 均衡注入电流
        cell_current = I_load[k] - I_balance[i, k]
        soc_bal[i, k] = soc_bal[i, k-1] - (cell_current * dt) / (Q_caps[i] * 3600.0)
        v_bal[i, k] = get_ocv(soc_bal[i, k]) - cell_current * R_ohms[i]

v_bal[:, 0] = get_ocv(soc_init) - I_load[0] * R_ohms

# 找到均衡情况下，最弱电芯触及 2.8V 的时间
cutoff_idx_bal = np.where(v_bal[1, :] < 2.8)[0][0]

# 5. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 无均衡时的电压急剧恶化
colors = ['g', 'r', 'b']
labels = ['Cell 1 (Strong)', 'Cell 2 (Weak)', 'Cell 3 (Normal)']

for i in range(3):
    ax1.plot(time[:cutoff_idx_no_bal], v_no_bal[i, :cutoff_idx_no_bal], color=colors[i], linewidth=2, label=labels[i])

ax1.axhline(2.8, color='k', linestyle='--', linewidth=2, label='Cutoff Voltage (2.8V)')
ax1.axvline(time[cutoff_idx_no_bal], color='red', linestyle=':', linewidth=2)
ax1.annotate('Weakest Cell hits limit!\nEntire Pack shuts down.', xy=(time[cutoff_idx_no_bal], 2.8), xytext=(time[cutoff_idx_no_bal]-1500, 2.9),
             arrowprops=dict(facecolor='red', shrink=0.05))

ax1.set_ylabel('Voltage (V)', fontsize=12)
ax1.set_title('Without Balancing: The "Wooden Barrel" Effect', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='upper right')

# B. 主动均衡时的电压维持
for i in range(3):
    ax2.plot(time[:cutoff_idx_bal], v_bal[i, :cutoff_idx_bal], color=colors[i], linewidth=2, label=labels[i])

ax2.axhline(2.8, color='k', linestyle='--', linewidth=2, label='Cutoff Voltage (2.8V)')
ax2.axvline(time[cutoff_idx_bal], color='blue', linestyle=':', linewidth=2)
ax2.annotate('Run time extended by sharing energy.', xy=(time[cutoff_idx_bal], 2.8), xytext=(time[cutoff_idx_bal]-1500, 2.9),
             arrowprops=dict(facecolor='blue', shrink=0.05))

ax2.set_ylabel('Voltage (V)', fontsize=12)
ax2.set_title('With Active Balancing: Transferring Energy from Strong to Weak', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 均衡电流的动作过程
ax3.plot(time[:cutoff_idx_bal], I_balance[0, :cutoff_idx_bal], 'g-', linewidth=2, label='Cell 1 (Supplying Energy)')
ax3.plot(time[:cutoff_idx_bal], I_balance[1, :cutoff_idx_bal], 'r-', linewidth=2, label='Cell 2 (Receiving Energy)')
ax3.plot(time[:cutoff_idx_bal], I_balance[2, :cutoff_idx_bal], 'b-', linewidth=2, label='Cell 3 (Neutral)')
ax3.axhline(0, color='k', linestyle='-', linewidth=1)

ax3.set_xlabel('Time (seconds)', fontsize=12)
ax3.set_ylabel('Balancing Current (A)', fontsize=12)
ax3.set_title('Active Balancing Current (DC/DC Transfer)', fontsize=14)
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "bms_balancing_sim.png"), dpi=300, bbox_inches='tight')

# 6. 生成对比表格
# 计算系统实际放出的电量 = 放电时间 * 电流
cap_no_bal = (time[cutoff_idx_no_bal] / 3600.0) * 20.0
cap_bal = (time[cutoff_idx_bal] / 3600.0) * 20.0

history = [
    {'Metric': 'System Shutdown Time', 'No Balancing': f"{time[cutoff_idx_no_bal]:.0f} s", 'Active Balancing': f"{time[cutoff_idx_bal]:.0f} s", 'Impact': 'Operation time extended'},
    {'Metric': 'Usable Capacity (Ah)', 'No Balancing': f"{cap_no_bal:.2f} Ah", 'Active Balancing': f"{cap_bal:.2f} Ah", 'Impact': f"Capacity increased by {cap_bal - cap_no_bal:.2f} Ah"},
    {'Metric': 'Cell 1 (Strong) Final SOC', 'No Balancing': f"{soc_no_bal[0, cutoff_idx_no_bal]*100:.1f}%", 'Active Balancing': f"{soc_bal[0, cutoff_idx_bal]*100:.1f}%", 'Impact': 'Strong cell utilized fully'},
    {'Metric': 'Cell 2 (Weak) Final SOC', 'No Balancing': f"{soc_no_bal[1, cutoff_idx_no_bal]*100:.1f}%", 'Active Balancing': f"{soc_bal[1, cutoff_idx_bal]*100:.1f}%", 'Impact': 'Weak cell protected'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "bms_balancing_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch05: BMS Active Balancing", "Diagram showing three batteries. Battery 1 is full, Battery 2 is almost empty. The BMS uses a DC/DC converter to pump energy out of Battery 1 and inject it directly into Battery 2, preventing the system from shutting down early.")

print("Files generated successfully.")
