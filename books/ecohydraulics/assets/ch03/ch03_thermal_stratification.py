import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\ecohydraulics\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 水温分层与生态调度 (Water Temperature Stratification and Eco-dispatch)
# 场景：一座深水库在夏天会形成强烈的温度分层。
# 表层水温高，底层水温极低。通过叠梁门(多层取水口)调节下泄水温，以满足下游鱼类繁殖需求。

# 1. 模拟夏季深水库的水温垂直分布剖面 (Thermal Stratification Profile)
depths = np.linspace(0, 100, 200) # 水库深度从 0(表面) 到 100m(库底)
T_surface = 25.0
T_bottom = 4.0
thermocline_depth = 20.0 # 温跃层深度
thermocline_thickness = 10.0

# 使用 Logistic 函数平滑模拟温跃层
temp_profile = T_bottom + (T_surface - T_bottom) / (1 + np.exp((depths - thermocline_depth) / (thermocline_thickness / 4)))

# 2. 叠梁门 (Multi-level Intake) 混合模型
# 假设大坝有 3 个取水口
intakes = {
    'Upper': {'depth': 5.0, 'flow_capacity': 50.0},
    'Middle': {'depth': 25.0, 'flow_capacity': 50.0},
    'Lower': {'depth': 60.0, 'flow_capacity': 50.0}
}

# 提取各取水口的实际水温
for name, data in intakes.items():
    idx = np.argmin(np.abs(depths - data['depth']))
    intakes[name]['temp'] = temp_profile[idx]

# 目标：下游需要 Q = 60 m^3/s 的流量，且目标水温为 16.0 摄氏度
Q_target = 60.0
T_target = 16.0

# 优化计算：寻找 Upper, Middle, Lower 的最佳流量组合 (Q_u, Q_m, Q_l)
# 满足: Q_u + Q_m + Q_l = Q_target
# 满足: (Q_u*T_u + Q_m*T_m + Q_l*T_l) / Q_target 约等于 T_target
# 且每个口的流量不超过 capacity

# 使用蒙特卡洛粗搜 + 局部贪心寻找最优解
best_error = 1e9
best_combination = (0, 0, 0)
best_mixed_T = 0

# 遍历可能的流量组合 (离散化步长为 1.0 m3/s)
for q_u in np.arange(0, intakes['Upper']['flow_capacity'] + 1, 1.0):
    for q_m in np.arange(0, intakes['Middle']['flow_capacity'] + 1, 1.0):
        q_l = Q_target - q_u - q_m
        if 0 <= q_l <= intakes['Lower']['flow_capacity']:
            # 计算混合水温 (能量守恒近似，忽略密度微小差异)
            mixed_T = (q_u * intakes['Upper']['temp'] + q_m * intakes['Middle']['temp'] + q_l * intakes['Lower']['temp']) / Q_target
            error = abs(mixed_T - T_target)
            if error < best_error:
                best_error = error
                best_combination = (q_u, q_m, q_l)
                best_mixed_T = mixed_T

# 3. 绘图
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 7))

# 图 A: 水库水温剖面
ax1.plot(temp_profile, depths, 'b-', linewidth=3)
ax1.invert_yaxis() # 深度向下增加
ax1.set_xlabel('Water Temperature ($^\circ$C)', fontsize=12)
ax1.set_ylabel('Depth below surface (m)', fontsize=12)
ax1.set_title('Reservoir Thermal Stratification in Summer', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注取水口
colors = ['red', 'orange', 'cyan']
for (name, data), c in zip(intakes.items(), colors):
    ax1.plot(data['temp'], data['depth'], marker='s', color=c, markersize=12, label=f"{name} Intake ({data['temp']:.1f}$^\circ$C)")
    ax1.axhline(data['depth'], color=c, linestyle=':', alpha=0.5)

ax1.axhspan(15, 30, color='gray', alpha=0.2, label='Thermocline (Metalimnion)')
ax1.legend(loc='lower left')

# 图 B: 流量分配饼图 (最佳调度方案)
labels = [f"Upper Intake\n({best_combination[0]} m³/s)", 
          f"Middle Intake\n({best_combination[1]} m³/s)", 
          f"Lower Intake\n({best_combination[2]} m³/s)"]
sizes = [best_combination[0], best_combination[1], best_combination[2]]

# 过滤掉流量为0的口
labels_plot = [l for l, s in zip(labels, sizes) if s > 0]
sizes_plot = [s for s in sizes if s > 0]
colors_plot = [c for c, s in zip(colors, sizes) if s > 0]

ax2.pie(sizes_plot, labels=labels_plot, colors=colors_plot, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
ax2.axis('equal') 
ax2.set_title(f'Optimal Dispatch for T_target = {T_target}$^\circ$C\n(Resulting T = {best_mixed_T:.2f}$^\circ$C)', fontsize=14)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "thermal_stratification_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
# 加入几个其他目标温度的对比
targets_test = [10.0, 16.0, 22.0]
for tt in targets_test:
    best_err = 1e9
    b_comb = (0,0,0)
    b_mT = 0
    for q_u in np.arange(0, 51, 1.0):
        for q_m in np.arange(0, 51, 1.0):
            q_l = Q_target - q_u - q_m
            if 0 <= q_l <= 50:
                mT = (q_u * intakes['Upper']['temp'] + q_m * intakes['Middle']['temp'] + q_l * intakes['Lower']['temp']) / Q_target
                err = abs(mT - tt)
                if err < best_err:
                    best_err = err
                    b_comb = (q_u, q_m, q_l)
                    b_mT = mT
                    
    history.append({
        'Target Temp (°C)': tt,
        'Upper Valve (m³/s)': round(b_comb[0], 1),
        'Middle Valve (m³/s)': round(b_comb[1], 1),
        'Lower Valve (m³/s)': round(b_comb[2], 1),
        'Actual Mixed Temp (°C)': round(b_mT, 2),
        'Status': 'Achieved' if best_err < 0.5 else 'Limited by Capacity'
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "thermal_dispatch_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
