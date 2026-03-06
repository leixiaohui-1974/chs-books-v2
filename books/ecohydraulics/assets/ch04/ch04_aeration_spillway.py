import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\ecohydraulics\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 气体溶解传递模型 (Gas Transfer Model) 与 曝气跌水 (Aeration Drop)
# 场景：大坝下泄水体的溶解氧 (Dissolved Oxygen, DO) 极低。
# 模拟水流经过一个阶梯式跌水堰(Stepped Spillway)时，如何从空气中“砸出”溶解氧。

# 物理参数
T_water = 20.0 # 水温 20度
# 查表: 20度下淡水的饱和溶解氧浓度 Cs (Saturation Concentration)
Cs = 9.09 # mg/L

DO_initial = 2.0 # 初始极度缺氧状态 mg/L

# 阶梯式跌水的物理模型
# 利用两相流(水-气)中的氧气传递经验公式
# DO_down = DO_up + E * (Cs - DO_up)
# E 为曝气效率 (Aeration Efficiency)，取决于水头跌落高度 H 和流量
# 经验公式：E = 1 - exp(-k * H)

H_total = 10.0 # 总跌水高度 10m
steps = [1, 2, 5, 10] # 对比不同阶梯数 (把 10m 分成 1 阶, 2阶, 5阶, 10阶)

# 计算不同设计方案下的 DO 恢复情况
results = {}

for num_steps in steps:
    h_step = H_total / num_steps # 每个台阶的高度
    do_current = DO_initial
    do_profile = [do_current]
    
    # 真实的跌水曝气效率是一个复杂的非线性函数。
    # 对于单级跌水，随着高度增加，水流在空中的滞留时间变长，但内部气泡可能达到饱和。
    # 对于多级阶梯跌水，每一次水跃跌落都会引发强烈的空气卷吸(Air Entrainment)和表面更新。
    # 经验模型修改：假设每次水流砸在台阶上时，都会由于剧烈的射流破裂产生一个基础曝气效率 E_base
    # 并且还包含一个与跌落高度相关的指数项。
    
    E_base = 0.10 # 每次碰撞产生的固定最低气液交换效率
    k_transfer = 0.15 
    
    for i in range(num_steps):
        # 计算每一阶的曝气效率 (综合碰撞破碎与空中降落)
        E = E_base + (1 - E_base) * (1 - np.exp(-k_transfer * h_step))
        # 溶解氧更新
        do_current = do_current + E * (Cs - do_current)
        do_profile.append(do_current)
        
    results[num_steps] = {
        'h_step': h_step,
        'profile': do_profile,
        'final_do': do_current,
        'efficiency': (do_current - DO_initial) / (Cs - DO_initial)
    }

# 绘图: 阶梯数对最终溶解氧的恢复效果
plt.figure(figsize=(10, 6))

colors = ['r', 'orange', 'g', 'b']
markers = ['o', 's', '^', 'D']

for i, num_steps in enumerate(steps):
    prof = results[num_steps]['profile']
    # 为了在同一张图里画出跌落过程，我们将x轴设为相对高度百分比或阶数累加
    x_vals = np.linspace(0, H_total, len(prof))
    plt.plot(x_vals, prof, color=colors[i], marker=markers[i], linestyle='-', linewidth=2, markersize=8,
             label=f'{num_steps} Steps (h={H_total/num_steps:.1f}m/step)')

plt.axhline(y=Cs, color='k', linestyle='--', linewidth=2, label=f'Saturation DO ($C_s={Cs} mg/L$)')
plt.axhline(y=5.0, color='r', linestyle=':', linewidth=2, label='Ecological Minimum Limit (5.0 mg/L)')

plt.xlabel('Cumulative Drop Height (m)', fontsize=12)
plt.ylabel('Dissolved Oxygen DO (mg/L)', fontsize=12)
plt.title('Aeration Efficiency over Stepped Spillways', fontsize=14)
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "aeration_spillway_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
for num_steps in steps:
    res = results[num_steps]
    history.append({
        'Number of Steps': num_steps,
        'Height per Step (m)': round(res['h_step'], 1),
        'Initial DO (mg/L)': DO_initial,
        'Final DO (mg/L)': round(res['final_do'], 2),
        'Total Aeration Efficiency E': f"{res['efficiency']*100:.1f}%",
        'Ecological Status': 'Pass' if res['final_do'] >= 5.0 else 'FAIL (Hypoxia)'
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "aeration_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
