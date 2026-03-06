import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch10"
os.makedirs(output_dir, exist_ok=True)

# 水文模型与水动力学模型耦合 (Hydrological-Hydrodynamic Coupling)
# 场景：山洪爆发流入城市。水文模型负责算山坡产流，水动力学模型负责算城市街道的漫水深度。

# 1. 模拟降雨与水文产流 (Hydrological Model - Lumped)
# 参数
t_end = 120 # 分钟
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

rain = np.zeros(N)
rain[10:40] = 60.0 # 强暴雨 60 mm/h

# 极简水文模型 (非线性水库) 计算汇入城市河道的流量 Q_in
S_catchment = 0.0
Q_in = np.zeros(N)
k_c = 10.0 # 汇流时间常数
for i in range(1, N):
    inflow = rain[i] * dt
    outflow = (S_catchment / k_c)**1.5 * dt # 非线性响应
    S_catchment = S_catchment + inflow - outflow
    Q_in[i] = outflow * 5.0 # 假设面积放大系数

# 2. 一维水动力学模型 (Hydrodynamic Model - 1D Routing approximation)
# 模拟城市主排洪渠 (长度 2000m)
L_channel = 2000.0
nx = 51
dx = L_channel / (nx - 1)
b = 10.0 # 矩形河道宽 10m

# 状态变量: 水深 h
h = np.ones(nx) * 0.5 # 初始水深 0.5m

# 保存特定位置的记录
history_h_mid = []
history_Q_mid = []
snapshots = {}

# 使用隐式/稳定的串联水库法模拟扩散波
# 每个网格视为一个小水库，出流 q = alpha * h^beta
alpha_route = 1.5
beta_route = 1.5

for i_t in range(N):
    Q_in_current = Q_in[i_t] + 1.0 # 加上基流
    
    # 引入微步长防止显式欧拉法爆炸 (每分钟拆分为 60 个 1 秒的步长)
    micro_steps = 60
    dt_micro = 1.0 # 秒
    
    for _ in range(micro_steps):
        h_new = np.copy(h)
        for i in range(nx):
            if i == 0:
                qin = Q_in_current
            else:
                qin = alpha_route * (h[i-1]**beta_route)
                
            qout = alpha_route * (h[i]**beta_route)
            
            # dh/dt = (qin - qout) / (b * dx)
            dh = (qin - qout) / (b * dx) * dt_micro
            h_new[i] = max(0.1, h[i] + dh)
        h = np.copy(h_new)
        
    history_h_mid.append(h[int(nx/2)])
    history_Q_mid.append(alpha_route * (h[int(nx/2)]**beta_route))
    
    if i_t in [0, 30, 50, 70, 100]:
        snapshots[f't={i_t}min'] = np.copy(h)

# 3. 绘图: 水文与水动力解耦对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 图 A: 水文模型的产流 (边界强迫)
ax1.plot(time, Q_in, 'r-', linewidth=3, label='Hydrological Output (Q from Hillslope)')
ax1.fill_between(time, 0, Q_in, color='red', alpha=0.2)
ax1.set_ylabel('Inflow Discharge ($m^3/s$)', fontsize=12)
ax1.set_title('Hydrological Model (Lumped Catchment Runoff Generation)', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='upper right')

# 画降雨倒柱状图
ax1_twin = ax1.twinx()
ax1_twin.bar(time, rain, width=dt, color='blue', alpha=0.3, label='Rainfall')
ax1_twin.set_ylim(80, 0)
ax1_twin.set_ylabel('Rainfall (mm/h)')

# 图 B: 水动力模型的演进 (城市渠道)
colors = ['k:', 'b-', 'g--', 'm-.', 'r-']
x_coords = np.linspace(0, L_channel, nx)
for idx, (t_label, h_prof) in enumerate(snapshots.items()):
    ax2.plot(x_coords, h_prof, colors[idx], linewidth=2, label=f'Water Surface at {t_label}')

ax2.axhline(y=3.0, color='red', linewidth=3, linestyle='-', alpha=0.5, label='City Embankment Level (Flood Limit)')

ax2.set_xlabel('Distance along City Channel (m)', fontsize=12)
ax2.set_ylabel('Water Depth (m)', fontsize=12)
ax2.set_title('Hydrodynamic Model (1D Routing in City Channel)', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "coupling_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
time_points = [20, 40, 60, 80, 100]

for tp in time_points:
    history.append({
        'Time (min)': tp,
        'Rainfall (mm/h)': rain[tp],
        'Hydro Model Out (m³/s)': round(Q_in[tp], 1),
        'Channel Mid Depth (m)': round(history_h_mid[tp], 2),
        'Flood Warning': 'ALERT (Overtopping)' if history_h_mid[tp] > 3.0 else 'Safe'
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "coupling_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch10: Hydrological & Hydrodynamic Coupling", "Diagram showing an upstream mountainous Hydrological Catchment producing a hydrograph (Q vs t), which is then fed into a downstream flat city Hydrodynamic 1D/2D mesh (showing water depth grids).")

print("Files generated successfully.")
