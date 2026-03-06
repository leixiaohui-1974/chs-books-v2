import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\photovoltaic-system-modeling-control\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 最大功率点跟踪 (MPPT) 算法仿真
# 场景：光伏阵列遇到剧烈波动的光照。对比传统 P&O (扰动观察法) 与先进的 INC (电导增量法) 的追踪性能。

# 1. 构建光伏阵列的简化数学黑盒 (环境光照 G -> 当前工作电压 V -> 输出功率 P)
# 假定一个包含随光照漂移的抛物线特性
def get_pv_power(v, g):
    # g 为光照 0~1000 W/m^2
    # 最大功率点电压 V_mp 大约在 300V 左右，随光照略微偏移
    v_mp = 300.0 + (g - 1000) * 0.05
    # 最大功率随光照线性变化
    p_max = 5000.0 * (g / 1000.0)
    
    # 用一个平滑的不对称抛物线拟合 P-V 曲线
    # 在 v_mp 左侧平缓，右侧陡峭下降 (模拟二极管指数下降)
    if v <= v_mp:
        p = p_max * (1 - ((v - v_mp) / v_mp)**2)
    else:
        # 右侧急剧下降，开路电压约在 V_mp + 100
        p = p_max * (1 - ((v - v_mp) / 100.0)**2)
        
    return max(0.0, p)

def get_pv_current(v, g):
    p = get_pv_power(v, g)
    if v > 0: return p / v
    return 0.0

# 2. 仿真环境设置
t_end = 10.0 # 模拟 10 秒
dt = 0.01    # 10ms 步长 (控制周期)
time = np.arange(0, t_end, dt)
N = len(time)

# 创造光照波动 (Irradiance profile)
# 0-3s: 稳定 1000
# 3-5s: 云层遮挡，剧烈下降到 400
# 5-7s: 稳定 400
# 7-9s: 云层散开，迅速回升到 800
# 9-10s: 稳定 800
G_profile = np.ones(N) * 1000.0
for i, t in enumerate(time):
    if 3.0 <= t < 5.0:
        G_profile[i] = 1000.0 - 600.0 * (t - 3.0) / 2.0
    elif 5.0 <= t < 7.0:
        G_profile[i] = 400.0
    elif 7.0 <= t < 9.0:
        G_profile[i] = 400.0 + 400.0 * (t - 7.0) / 2.0
    elif t >= 9.0:
        G_profile[i] = 800.0

# 计算理论最大功率点作为 Benchmark
P_theory_max = np.array([get_pv_power(300.0 + (g - 1000)*0.05, g) for g in G_profile])

# 3. 算法 A: 扰动观察法 (Perturb and Observe, P&O)
# 逻辑：加一点电压，看看功率变大没。变大了就继续加，变小了就减。
V_po = np.zeros(N)
P_po = np.zeros(N)
V_po[0] = 200.0 # 初始电压瞎猜 200V
P_po[0] = get_pv_power(V_po[0], G_profile[0])

step_po = 2.0 # 扰动步长 2V

for i in range(1, N):
    v_prev = V_po[i-1]
    p_prev = P_po[i-1]
    g_curr = G_profile[i]
    
    # 传感器读取当前电压下的新功率
    p_curr = get_pv_power(v_prev, g_curr)
    
    # 判断方向
    dp = p_curr - p_prev
    dv = v_prev - V_po[i-2] if i > 1 else step_po
    
    # 核心 P&O 逻辑
    if dp > 0:
        if dv > 0: direction = 1
        else:      direction = -1
    else:
        if dv > 0: direction = -1
        else:      direction = 1
        
    V_po[i] = v_prev + direction * step_po
    P_po[i] = get_pv_power(V_po[i], g_curr)

# 4. 算法 B: 电导增量法 (Incremental Conductance, INC)
# 逻辑：利用 dP/dV = I + V*(dI/dV) = 0 的极值点特性。
# 比较增量电导 (dI/dV) 和 瞬时电导 (-I/V)
V_inc = np.zeros(N)
P_inc = np.zeros(N)
I_inc = np.zeros(N)
V_inc[0] = 200.0
P_inc[0] = get_pv_power(V_inc[0], G_profile[0])
I_inc[0] = get_pv_current(V_inc[0], G_profile[0])

step_inc = 2.0

for i in range(1, N):
    v_curr = V_inc[i-1]
    i_curr = get_pv_current(v_curr, G_profile[i])
    
    v_prev = V_inc[i-2] if i > 1 else v_curr - 0.1
    i_prev = I_inc[i-2] if i > 1 else i_curr
    
    dv = v_curr - v_prev
    di = i_curr - i_prev
    
    # 核心 INC 逻辑
    if dv == 0:
        if di == 0:
            v_next = v_curr
        elif di > 0:
            v_next = v_curr + step_inc
        else:
            v_next = v_curr - step_inc
    else:
        # dI/dV vs -I/V
        conductance_inc = di / dv
        conductance_inst = -i_curr / v_curr
        
        # 为了防抖动，设置一个小小的阈值 epsilon
        eps = 0.005
        
        if abs(conductance_inc - conductance_inst) < eps:
            v_next = v_curr # 已经到达顶点，停止抖动
        elif conductance_inc > conductance_inst:
            v_next = v_curr + step_inc # 在顶点左边，增加电压
        else:
            v_next = v_curr - step_inc # 在顶点右边，减小电压
            
    V_inc[i] = v_next
    I_inc[i] = get_pv_current(V_inc[i], G_profile[i])
    P_inc[i] = V_inc[i] * I_inc[i]

# 5. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# A. 太阳光照扰动 (Environment)
ax1.plot(time, G_profile, 'k-', linewidth=3, label='Solar Irradiance ($W/m^2$)')
ax1.set_ylabel('Irradiance ($W/m^2$)', fontsize=12)
ax1.set_title('Rapid Weather Disturbance (Cloud Passing)', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注天气
ax1.text(1.5, 950, 'Clear Sky', fontsize=12, ha='center', bbox=dict(facecolor='white', alpha=0.8))
ax1.text(4.0, 700, 'Cloud Blocking', fontsize=12, ha='center', bbox=dict(facecolor='gray', alpha=0.3))
ax1.text(6.0, 450, 'Heavy Cloud', fontsize=12, ha='center', bbox=dict(facecolor='gray', alpha=0.8))

# B. 功率追踪对比 (MPPT Performance)
ax2.plot(time, P_theory_max, 'g--', linewidth=3, alpha=0.5, label='Theoretical Max Power (Oracle)')
ax2.plot(time, P_po, 'r-', linewidth=2, alpha=0.8, label='P&O (Perturb & Observe)')
ax2.plot(time, P_inc, 'b-', linewidth=2, alpha=0.8, label='INC (Incremental Conductance)')

ax2.set_xlabel('Time (seconds)', fontsize=12)
ax2.set_ylabel('Power Output (W)', fontsize=12)
ax2.set_title('MPPT Tracking Performance: P&O vs INC', fontsize=14)
ax2.legend(loc='lower left')
ax2.grid(True, linestyle='--', alpha=0.6)

# 放大一个稳态窗口展示 P&O 的震荡缺陷
inset_ax = ax2.inset_axes([0.65, 0.45, 0.3, 0.3])
inset_ax.plot(time, P_theory_max, 'g--', linewidth=3, alpha=0.5)
inset_ax.plot(time, P_po, 'r-', linewidth=2)
inset_ax.plot(time, P_inc, 'b-', linewidth=2)
inset_ax.set_xlim(1.0, 1.5)
inset_ax.set_ylim(4970, 5010)
inset_ax.set_title('Steady-state Oscillation')
inset_ax.grid(True, linestyle=':')
ax2.indicate_inset_zoom(inset_ax, edgecolor="black")

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "mppt_algorithms_sim.png"), dpi=300, bbox_inches='tight')

# 6. 生成对比表格
# 计算动态追踪效率 (Dynamic Tracking Efficiency)
eff_po = np.sum(P_po) / np.sum(P_theory_max) * 100
eff_inc = np.sum(P_inc) / np.sum(P_theory_max) * 100

# 统计误判次数 (光照变化时 P&O 容易走错方向)
# 简单的衡量方法：计算偏离理论点超过 100W 的时间步数
loss_po = len(np.where(P_theory_max - P_po > 100)[0])
loss_inc = len(np.where(P_theory_max - P_inc > 100)[0])

history = [
    {'Algorithm': 'P&O (Perturb & Observe)', 'Steady-State Behavior': 'Continuous Oscillation', 'Response to Cloud Shadow': 'Confused / Drift', 'Overall Tracking Efficiency': f"{eff_po:.2f}%", 'Severe Loss Steps': loss_po},
    {'Algorithm': 'INC (Incremental Conductance)', 'Steady-State Behavior': 'Perfectly Locked', 'Response to Cloud Shadow': 'Accurate Tracking', 'Overall Tracking Efficiency': f"{eff_inc:.2f}%", 'Severe Loss Steps': loss_inc}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "mppt_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch02: MPPT Control Logic", "Diagram showing a hill-climbing robot (the MPPT algorithm) walking blindly on a curved mountain (the P-V curve). It takes a step, checks if it went higher, and decides the next step to reach the absolute peak power.")

print("Files generated successfully.")
