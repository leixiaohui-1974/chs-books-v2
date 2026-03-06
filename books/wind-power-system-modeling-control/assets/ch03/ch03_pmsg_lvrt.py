import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\wind-power-system-modeling-control\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 永磁直驱同步发电机 (PMSG) 全功率变流器控制
# 模拟低电压穿越 (LVRT) 期间，PMSG 如何通过网侧变流器 (GSC) 注入无功功率支撑电网，
# 并通过斩波电路 (Chopper) 消耗多余的有功功率保护直流母线 (DC-Link)。

# 1. 物理参数与模拟设定
t_end = 2.0 # 模拟 2 秒
dt = 0.001  # 1 ms
time = np.arange(0, t_end, dt)
N = len(time)

P_rated = 1.0 # 标幺值 1.0 pu (比如 2MW)
V_dc_nom = 1.0 # 直流母线额定电压 1.0 pu
C_dc = 0.1 # 直流母线电容 (pu)

# 2. 电网电压跌落事件 (Grid Fault / Voltage Dip)
V_grid = np.ones(N)
# 假设在 t=0.5s 发生严重三相短路，电压跌落至 0.2pu，持续 0.6s (至1.1s恢复)
fault_start = 0.5
fault_end = 1.1
dip_level = 0.2

for i in range(N):
    if fault_start <= time[i] < fault_end:
        V_grid[i] = dip_level
    elif time[i] >= fault_end:
        # 电压呈指数恢复
        V_grid[i] = 1.0 - (1.0 - dip_level) * np.exp(-(time[i] - fault_end) / 0.1)

# 3. 状态变量初始化
P_gen = np.ones(N) * 0.9 # 发电机发出的有功功率 (假设风速恒定，一直发电0.9pu)
P_grid = np.zeros(N)     # 送入电网的有功功率
Q_grid = np.zeros(N)     # 送入电网的无功功率
V_dc = np.ones(N) * V_dc_nom
P_chop = np.zeros(N)     # 斩波器消耗的功率

# 网侧变流器 (GSC) 电流限制
I_max = 1.2 # GSC 最大允许过载电流 1.2 pu

# 4. LVRT 控制逻辑演进
for i in range(1, N):
    v = V_grid[i]
    
    # --------------------------
    # GSC 控制策略 (网侧变流器)
    # --------------------------
    if v < 0.9: # 触发低电压穿越
        # 电网规范要求：电压跌落越深，注入的无功电流 Iq 必须越大
        # Iq_ref = k * (0.9 - V)
        k_droop = 2.0
        Iq_ref = min(k_droop * (0.9 - v), I_max)
        
        # 优先保证无功，剩余容量给有功 (Id)
        # Id_ref^2 + Iq_ref^2 <= I_max^2
        Id_max = np.sqrt(max(0, I_max**2 - Iq_ref**2))
        
        # 由于电网电压 v 极低，能送入电网的最大有功 P = v * Id
        P_capacity = v * Id_max
        Id_ref = min(P_gen[i] / v, Id_max) if v > 0.05 else 0.0
        
        P_grid[i] = v * Id_ref
        Q_grid[i] = v * Iq_ref
    else:
        # 正常运行：有功全送，无功为0 (或按调度指令)
        P_capacity = v * I_max
        P_grid[i] = min(P_gen[i], P_capacity)
        Q_grid[i] = 0.0
        
    # --------------------------
    # 直流母线动态与斩波保护 (DC-Link & Chopper)
    # --------------------------
    # 能量平衡：C * V_dc * dV_dc/dt = P_gen - P_grid - P_chop
    # 如果 P_gen > P_grid，多余的能量会冲进电容，导致 V_dc 飙升
    
    # 预测下一个时刻的电压 (如果不加斩波)
    dP = P_gen[i] - P_grid[i]
    V_dc_pred = V_dc[i-1] + (dP / (C_dc * V_dc[i-1])) * dt
    
    # 斩波控制逻辑：如果 V_dc 超过 1.1 pu，启动制动电阻消耗多余能量
    if V_dc_pred > 1.1:
        # 简单比例控制，强制消耗多余功率
        P_chop[i] = dP + (V_dc_pred - 1.1) * 10.0
        # 斩波器物理上限
        P_chop[i] = min(P_chop[i], 1.0) 
    else:
        P_chop[i] = 0.0
        
    # 实际更新 V_dc
    dP_actual = P_gen[i] - P_grid[i] - P_chop[i]
    V_dc[i] = V_dc[i-1] + (dP_actual / (C_dc * V_dc[i-1])) * dt
    V_dc[i] = max(0.1, V_dc[i]) # 防止数值崩溃

# 5. 绘图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 电网电压与功率分配
ax1.plot(time, V_grid, 'k-', linewidth=3, label='Grid Voltage ($V_{grid}$)')
ax1.plot(time, P_grid, 'b--', linewidth=2, label='Active Power to Grid ($P_{grid}$)')
ax1.plot(time, Q_grid, 'r-', linewidth=2, label='Reactive Power to Grid ($Q_{grid}$)')

ax1.axvspan(fault_start, fault_end, color='red', alpha=0.1, label='Fault Period')
ax1.set_ylabel('Voltage / Power (pu)', fontsize=12)
ax1.set_title('LVRT: Grid Voltage Dip and Reactive Power Support', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

ax1.annotate('Inject Reactive Power\n(Priority Support)', xy=(0.8, 0.4), xytext=(0.8, 0.8),
             arrowprops=dict(facecolor='red', shrink=0.05), ha='center')

# B. 变流器电流追踪 (网侧 GSC)
I_active = P_grid / V_grid
I_reactive = Q_grid / V_grid
# 处理除以接近 0 的小数值问题
I_active[V_grid < 0.05] = 0
I_reactive[V_grid < 0.05] = 0

ax2.plot(time, I_active, 'b--', linewidth=2, label='Active Current ($I_d$)')
ax2.plot(time, I_reactive, 'r-', linewidth=2, label='Reactive Current ($I_q$)')
ax2.axhline(I_max, color='k', linestyle=':', linewidth=2, label='Converter Max Current Limit ($I_{max}$)')

ax2.set_ylabel('Current (pu)', fontsize=12)
ax2.set_title('Grid-Side Converter Current Limitation', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 直流母线电压与斩波保护
ax3.plot(time, V_dc, 'g-', linewidth=3, label='DC-Link Voltage ($V_{dc}$)')
ax3.fill_between(time, 0, P_chop, color='orange', alpha=0.5, label='Chopper Dissipated Power ($P_{chop}$)')

ax3.axhline(1.1, color='red', linestyle=':', linewidth=2, label='Chopper Activation Threshold (1.1 pu)')
ax3.axhline(1.2, color='black', linestyle='--', linewidth=2, label='Over-voltage Trip Limit (1.2 pu)')

ax3.set_xlabel('Time (seconds)', fontsize=12)
ax3.set_ylabel('DC Voltage / Power (pu)', fontsize=12)
ax3.set_title('DC-Link Protection via Braking Chopper', fontsize=14)
ax3.legend(loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "pmsg_lvrt_sim.png"), dpi=300, bbox_inches='tight')

# 6. 生成对比表格
history = []
snapshots = [0.2, 0.6, 1.0, 1.5]
labels = ["Pre-Fault", "Deep Fault (0.6s)", "Fault Clearing (1.0s)", "Recovered"]

for idx, t_snap in enumerate(snapshots):
    i = int(t_snap / dt)
    history.append({
        'State': labels[idx],
        'Grid Volt (pu)': round(V_grid[i], 2),
        'P_grid (pu)': round(P_grid[i], 2),
        'Q_grid (pu)': round(Q_grid[i], 2),
        'I_reactive (pu)': round(I_reactive[i], 2),
        'DC Volt (pu)': round(V_dc[i], 2),
        'Chopper Power': round(P_chop[i], 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "pmsg_lvrt_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: PMSG & Full Converter", "Diagram of a Permanent Magnet Synchronous Generator (PMSG). Generator is decoupled from the grid via a Full-Scale Back-to-Back Converter with a DC-Link capacitor and a braking chopper circuit in the middle.")

print("Files generated successfully.")
