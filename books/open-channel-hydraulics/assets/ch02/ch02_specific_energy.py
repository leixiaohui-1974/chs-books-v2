import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import fsolve

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 矩形渠道参数
Q = 30.0         # 流量 m^3/s
b = 6.0          # 底宽 m
g = 9.81         # 重力加速度
q = Q / b        # 单宽流量 m^2/s

# 临界水深和临界底能
h_c = (q**2 / g)**(1/3)
E_min = 1.5 * h_c

# 计算比能
def specific_energy(h):
    return h + (q**2) / (2 * g * h**2)

# 给定一个目标比能，寻找对应的急流水深和缓流水深
E_target = E_min + 1.0

# 优化求解交替水深
def energy_diff(h, E_tgt):
    return specific_energy(h) - E_tgt

# 急流(浅水)水深初值
h_super_guess = 0.5 * h_c
h_super = fsolve(energy_diff, h_super_guess, args=(E_target,))[0]

# 缓流(深水)水深初值
h_sub_guess = 2.0 * h_c
h_sub = fsolve(energy_diff, h_sub_guess, args=(E_target,))[0]

# 生成用于图表的数据
h_values = np.linspace(0.4, 4.0, 100)
E_values = specific_energy(h_values)

# 制作表格数据，抽取一些代表性点
h_table_values = [0.5, 0.8, h_super, h_c, 1.8, h_sub, 3.5]
history = []
for h in sorted(h_table_values):
    E = specific_energy(h)
    V = q / h
    Fr = V / np.sqrt(g * h)
    flow_state = "临界流 (Critical)" if abs(Fr - 1.0) < 0.05 else ("急流 (Supercritical)" if Fr > 1 else "缓流 (Subcritical)")
    history.append({
        'Depth h (m)': round(h, 3),
        'Specific Energy E (m)': round(E, 3),
        'Velocity V (m/s)': round(V, 3),
        'Froude No.': round(Fr, 3),
        'Flow State': flow_state
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "specific_energy_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# Plotting specific energy curve
plt.figure(figsize=(8, 10))
plt.plot(E_values, h_values, 'b-', linewidth=2, label='Specific Energy Curve')
plt.plot([0, 5], [0, 5], 'k--', alpha=0.5, label='E = h (Asymptote)')

# 标注临界点
plt.plot(E_min, h_c, 'ro', markersize=8, label=f'Critical Point ($h_c={h_c:.2f}m, E_{{min}}={E_min:.2f}m$)')

# 标注目标比能和对应的两个水深
plt.axvline(x=E_target, color='g', linestyle=':', alpha=0.7)
plt.plot(E_target, h_super, 'go', markersize=6, label=f'Supercritical Depth ($h_1={h_super:.2f}m$)')
plt.plot(E_target, h_sub, 'mo', markersize=6, label=f'Subcritical Depth ($h_2={h_sub:.2f}m$)')

plt.xlabel('Specific Energy E (m)', fontsize=12)
plt.ylabel('Flow Depth h (m)', fontsize=12)
plt.title('Specific Energy Curve for Rectangular Channel', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.xlim(1, 5)
plt.ylim(0, 4)

plt.savefig(os.path.join(output_dir, "specific_energy_curve.png"), dpi=300, bbox_inches='tight')
print(f"Files generated successfully. Critical h_c={h_c:.3f}, E_min={E_min:.3f}. Conjugate depths: h_super={h_super:.3f}, h_sub={h_sub:.3f}")
