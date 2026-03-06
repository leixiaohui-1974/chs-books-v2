import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch08"
os.makedirs(output_dir, exist_ok=True)

# 工业互联网与智慧水务的跨域同态映射 (Cross-domain Mapping)
# 场景：证明“氧化铝多效蒸发器 (Multi-Effect Evaporator)”在物理状态空间方程上，
# 与“流域梯级水库群 (Cascaded Reservoir System)”是完全同构的。
# 这意味着我们可以用同一套 AI 算法来控制这两种截然不同的系统。

# 1. 通用状态空间模型 (Generalized State-Space Model)
# x(t+1) = A * x(t) + B * u(t) + D * w(t)
# 对于蒸发器，x是各个罐的浓度，u是蒸汽阀门，w是进料浓度
# 对于水库群，x是各个水库的水位，u是开闸泄量，w是上游降雨

t_end = 50
time = np.arange(0, t_end)
N = len(time)

# 外部扰动 w(t)：一个冲击信号
disturbance = np.zeros(N)
disturbance[10:20] = 5.0

# 2. 系统A：氧化铝三效蒸发系统 (Alumina 3-Effect Evaporator)
# x: [C1, C2, C3] 各效液料浓度 (g/L)
# 动态方程：dC/dt = (Fin*Cin - Fout*Cout - Evap_rate * C_out) / V
x_alumina = np.zeros((3, N))
x_alumina[:, 0] = [140.0, 180.0, 240.0] # 初始稳态浓度

# u: [S1, S2, S3] 虽然物理上只有S1，但为了映射我们假定内部有调节旁路
u_alumina = np.zeros(N)

for t in range(1, N):
    # 模拟外部扰动 (进料变浓)
    c_in = 140.0 + disturbance[t]
    
    # 假设一个简化的串联传递关系 (First Order ODE)
    tau = 4.0
    x_alumina[0, t] = x_alumina[0, t-1] + (c_in - x_alumina[0, t-1] + u_alumina[t-1]) / tau
    x_alumina[1, t] = x_alumina[1, t-1] + (x_alumina[0, t-1] - x_alumina[1, t-1]) / tau
    x_alumina[2, t] = x_alumina[2, t-1] + (x_alumina[1, t-1] - x_alumina[2, t-1]) / tau

# 3. 系统B：流域梯级水库群 (River Basin 3-Cascade Reservoirs)
# x: [H1, H2, H3] 各水库水位 (m)
# 动态方程：dH/dt = (Qin - Qout) / Area
x_hydro = np.zeros((3, N))
x_hydro[:, 0] = [100.0, 80.0, 50.0] # 初始稳态水位

u_hydro = np.zeros(N)

for t in range(1, N):
    # 模拟外部扰动 (上游暴雨洪水)
    q_rain = 0.0 + disturbance[t]
    
    # 同样是一阶线性衰减水库模型 (完全同构的微分方程)
    tau = 4.0
    x_hydro[0, t] = x_hydro[0, t-1] + (q_rain - x_hydro[0, t-1]*0.01 + u_hydro[t-1]) / tau
    x_hydro[1, t] = x_hydro[1, t-1] + (x_hydro[0, t-1]*0.01 - x_hydro[1, t-1]*0.01) / tau
    x_hydro[2, t] = x_hydro[2, t-1] + (x_hydro[1, t-1]*0.01 - x_hydro[2, t-1]*0.01) / tau

# 为了让波形重合便于可视化比较，我们对它们进行归一化 (Zero-mean, Unit-variance)
def normalize(series):
    return (series - np.mean(series)) / (np.std(series) + 1e-6)

norm_alumina = np.array([normalize(x_alumina[0, :]), normalize(x_alumina[1, :]), normalize(x_alumina[2, :])])
norm_hydro = np.array([normalize(x_hydro[0, :]), normalize(x_hydro[1, :]), normalize(x_hydro[2, :])])

# 4. 绘图：展现跨域的数学同态美学
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 图A: 氧化铝蒸发器内部浓度的传导冲击
ax1.plot(time, normalize(disturbance), 'k--', linewidth=2, label='Disturbance (Thick Feed)')
ax1.plot(time, norm_alumina[0], 'r-', linewidth=2, label='Effect 1 Conc.')
ax1.plot(time, norm_alumina[1], 'g-', linewidth=2, label='Effect 2 Conc.')
ax1.plot(time, norm_alumina[2], 'b-', linewidth=3, label='Effect 3 Conc. (Final)')

ax1.set_xlabel('Time Step', fontsize=12)
ax1.set_ylabel('Normalized State Fluctuation', fontsize=12)
ax1.set_title('System A: Alumina Multi-Effect Evaporators', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 图B: 流域梯级水库水位的传导冲击
ax2.plot(time, normalize(disturbance), 'k--', linewidth=2, label='Disturbance (Rainstorm Flood)')
ax2.plot(time, norm_hydro[0], 'r-', linewidth=2, label='Reservoir 1 Water Level')
ax2.plot(time, norm_hydro[1], 'g-', linewidth=2, label='Reservoir 2 Water Level')
ax2.plot(time, norm_hydro[2], 'b-', linewidth=3, label='Reservoir 3 Water Level')

ax2.set_xlabel('Time Step', fontsize=12)
ax2.set_ylabel('Normalized State Fluctuation', fontsize=12)
ax2.set_title('System B: Cascaded River Basin Reservoirs', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cross_domain_mapping_sim.png"), dpi=300, bbox_inches='tight')

# 生成映射对比字典表格
history = [
    {'Mathematical Abstraction': 'State Variable (X)', 'System A (Alumina Evaporation)': 'Concentration (g/L) & Tank Level (m)', 'System B (Smart Water Basin)': 'Water Level (m) & Water Quality'},
    {'Mathematical Abstraction': 'Control Variable (U)', 'System A (Alumina Evaporation)': 'Steam Valve Opening (%)', 'System B (Smart Water Basin)': 'Sluice Gate Opening (%)'},
    {'Mathematical Abstraction': 'Disturbance (W)', 'System A (Alumina Evaporation)': 'Feed Concentration Surge', 'System B (Smart Water Basin)': 'Upstream Rainstorm / Flood'},
    {'Mathematical Abstraction': 'Dynamic Equation', 'System A (Alumina Evaporation)': 'Mass & Enthalpy Conservation', 'System B (Smart Water Basin)': 'Continuity & Saint-Venant Equations'},
    {'Mathematical Abstraction': 'Optimization Goal', 'System A (Alumina Evaporation)': 'Minimize Steam Ratio (Cost)', 'System B (Smart Water Basin)': 'Minimize Flood Damage / Max Power'},
    {'Mathematical Abstraction': 'AI Algorithm', 'System A (Alumina Evaporation)': 'Model Predictive Control (MPC)', 'System B (Smart Water Basin)': 'Model Predictive Control (MPC)'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "cross_domain_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch08: Cross-Domain Homomorphism", "Diagram showing a mirror reflection. On top is a hot, steamy alumina evaporator factory. Mirrored on the bottom is a cool, green cascade of river dams. An AI brain sits in the middle, using the exact same math equations to control both.")

print("Files generated successfully.")
