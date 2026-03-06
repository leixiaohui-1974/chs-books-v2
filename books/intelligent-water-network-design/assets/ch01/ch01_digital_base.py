import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\intelligent-water-network-design\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 水网数字底座设计 (Digital Twin Base Design)
# 模拟数字底座中“网格化水动力模型”的分辨率(Resolution)对洪峰预测精度与算力消耗的矛盾博弈。
# 展示在数字底座设计时，为什么不能一味追求“高精度”，而需要“变分辨率网格”或“云边协同”。

# 1. 真实物理世界 (The Ground Truth - 假定无限精度)
t_end = 120 # 分钟
dt_truth = 0.1 # 真实物理演进极快
time_truth = np.arange(0, t_end, dt_truth)
N_truth = len(time_truth)

# 制造一场包含多个尖锐微洪峰的极端降雨导致的径流
Q_truth = np.zeros(N_truth)
for i, t in enumerate(time_truth):
    base = 10.0 * np.sin(np.pi * t / 120.0)
    # 模拟局部强对流天气产生的微型“尖刺”洪峰
    spike1 = 20.0 * np.exp(-((t - 30)**2) / 2.0)
    spike2 = 35.0 * np.exp(-((t - 75)**2) / 0.5) # 极窄极高的洪峰
    spike3 = 15.0 * np.exp(-((t - 100)**2) / 5.0)
    Q_truth[i] = max(0, base + spike1 + spike2 + spike3)

# 2. 数字底座建模方案 A：低分辨率宏观网格 (Low-Res Macro Grid)
# 比如 1km x 1km 网格，时间步长 5 分钟
# 优点：算力消耗极小，能快速给出宏观趋势
# 缺点：会把那根细长的“夺命洪峰(spike2)”完全抹平，导致致命漏报
dt_low = 5.0
time_low = np.arange(0, t_end, dt_low)
Q_low = np.zeros(len(time_low))

for i, t in enumerate(time_low):
    # 低分辨率模型相当于在时空上做了一个粗糙的移动平均
    idx_start = int(max(0, t - dt_low/2) / dt_truth)
    idx_end = int(min(t_end, t + dt_low/2) / dt_truth)
    if idx_start < idx_end:
        Q_low[i] = np.mean(Q_truth[idx_start:idx_end]) * 0.8 # 模型通常会低估因为平滑效应
    
# 3. 数字底座建模方案 B：极高分辨率微观网格 (High-Res Micro Grid)
# 比如 5m x 5m 网格，时间步长 0.5 分钟
# 优点：极其精准，完美捕捉所有尖峰
# 缺点：算力消耗是低分辨率的成千上万倍，无法在云端实现全省实时计算
dt_high = 0.5
time_high = np.arange(0, t_end, dt_high)
Q_high = np.zeros(len(time_high))

for i, t in enumerate(time_high):
    idx = int(t / dt_truth)
    # 高精度模型能很好地拟合，但加入微小的数值扩散截断误差
    Q_high[i] = Q_truth[idx] * 0.98 + np.random.normal(0, 0.5)

# 计算算力开销相对值 (O(N_time * N_space) 且空间复杂度正比于分辨率的平方)
# 低分: 1km (1000m), 高分: 5m -> 空间网格数相差 (1000/5)^2 = 40000 倍
# 时间步长相差 5 / 0.5 = 10 倍
# 总算力相差 400,000 倍
cost_low = 1.0
cost_high = 400000.0

# 4. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# A. 精度对比 (Accuracy)
ax1.plot(time_truth, Q_truth, 'k--', linewidth=1.5, alpha=0.5, label='Physical Ground Truth (Infinite Res)')
ax1.plot(time_low, Q_low, 'b-s', linewidth=2, markersize=6, label='Low-Res Base (1km grid, 5min step)')
ax1.plot(time_high, Q_high, 'r-', linewidth=2, alpha=0.8, label='High-Res Base (5m grid, 0.5min step)')

# 标注致命漏报
peak_time = 75
ax1.annotate('Fatal Miss!\nLow-res grid averaged\nout the flash flood', 
             xy=(peak_time, np.interp(peak_time, time_low, Q_low)), 
             xytext=(peak_time - 30, 25),
             arrowprops=dict(facecolor='blue', shrink=0.05))

ax1.annotate('Perfect Capture', 
             xy=(peak_time, np.max(Q_truth)), 
             xytext=(peak_time + 10, 35),
             arrowprops=dict(facecolor='red', shrink=0.05))

ax1.set_xlabel('Time (Minutes)', fontsize=12)
ax1.set_ylabel('Flood Discharge ($m^3/s$)', fontsize=12)
ax1.set_title('Digital Twin Base: Spatial-Temporal Resolution vs Accuracy', fontsize=14)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 算力消耗对比 (Computational Cost - Log Scale)
models = ['Low-Res Base\n(Macro River)', 'High-Res Base\n(City Streets)']
costs = [cost_low, cost_high]
errors = [np.mean(np.abs(np.interp(time_truth, time_low, Q_low) - Q_truth)), 
          np.mean(np.abs(np.interp(time_truth, time_high, Q_high) - Q_truth))]

ax2_twin = ax2.twinx()

bar_width = 0.4
x = np.arange(len(models))

rects1 = ax2.bar(x - bar_width/2, costs, bar_width, color='gray', label='Compute Cost (Relative Units, Log)')
rects2 = ax2_twin.bar(x + bar_width/2, errors, bar_width, color='orange', label='Mean Absolute Error ($m^3/s$)')

ax2.set_yscale('log')
ax2.set_ylabel('Computational Cost (Log Scale)', fontsize=12)
ax2_twin.set_ylabel('Tracking Error ($m^3/s$)', color='orange', fontsize=12)
ax2_twin.tick_params(axis='y', labelcolor='orange')

ax2.set_xticks(x)
ax2.set_xticklabels(models, fontsize=12)
ax2.set_title('The Engineering Dilemma: Accuracy vs Compute Power', fontsize=14)

lines_1, labels_1 = ax2.get_legend_handles_labels()
lines_2, labels_2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
ax2.grid(True, axis='y', linestyle=':', alpha=0.4)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "digital_base_resolution_sim.png"), dpi=300, bbox_inches='tight')

# 5. 生成表格
history = [
    {'Design Choice': 'Low-Res (1km, 5min)', 'Peak Capture': 'Failed (Smooths out flash floods)', 'Compute Demand': 'Minimal (1x CPU)', 'Deployment': 'Provincial Cloud (Macro Routing)'},
    {'Design Choice': 'High-Res (5m, 0.5min)', 'Peak Capture': 'Perfect (Catches sharp spikes)', 'Compute Demand': 'Extreme (400,000x GPUs)', 'Deployment': 'Edge Node (Local City Streets only)'},
    {'Design Choice': 'Dynamic Mesh (Future)', 'Peak Capture': 'Adaptive', 'Compute Demand': 'Moderate', 'Deployment': 'Cloud-Edge Collaborative'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "resolution_tradeoff_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch01: Digital Twin Base Design", "Diagram showing a map divided into a grid. On the left, huge 1km grids are processed quickly by a cloud server, but miss small flooded streets. On the right, a magnifying glass shows a 5m grid calculating water flow around every building, consuming massive GPU power.")

print("Files generated successfully.")
