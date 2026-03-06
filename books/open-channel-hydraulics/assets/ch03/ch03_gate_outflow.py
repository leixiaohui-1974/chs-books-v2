import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 平底矩形明渠闸门出流参数
H0 = 5.0         # 上游水深 (忽略行近流速水头) m
b = 4.0          # 闸孔宽度 m
g = 9.81         # 重力加速度
epsilon = 0.61   # 垂直闸门的近似收缩系数

# 计算流量系数和自由出流流量
def gate_outflow(e):
    # 流量系数
    mu = epsilon / np.sqrt(1 + epsilon * (e / H0))
    # 自由出流流量公式
    Q = mu * e * b * np.sqrt(2 * g * H0)
    # 收缩断面水深
    hc = epsilon * e
    return mu, Q, hc

# 生成用于图表的数据
e_values = np.linspace(0.2, 3.5, 50)
mu_values = []
Q_values = []
hc_values = []

for e in e_values:
    mu, Q, hc = gate_outflow(e)
    mu_values.append(mu)
    Q_values.append(Q)
    hc_values.append(hc)

# 制作表格数据，抽取一些代表性开度
e_table_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
history = []
for e in e_table_values:
    mu, Q, hc = gate_outflow(e)
    Fr_c = (Q / (b * hc)) / np.sqrt(g * hc) # 收缩断面弗劳德数
    history.append({
        'Gate Opening e (m)': round(e, 2),
        'Discharge Coeff μ': round(mu, 4),
        'Discharge Q (m³/s)': round(Q, 2),
        'Contraction Depth hc (m)': round(hc, 2),
        'Froude No. at hc': round(Fr_c, 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "gate_outflow_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# Plotting
fig, ax1 = plt.subplots(figsize=(9, 6))

color = 'tab:blue'
ax1.set_xlabel('Gate Opening $e$ (m)', fontsize=12)
ax1.set_ylabel('Discharge $Q$ ($m^3/s$)', color=color, fontsize=12)
ax1.plot(e_values, Q_values, 'b-', linewidth=2, label='Discharge $Q$')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle='--', alpha=0.6)

ax2 = ax1.twinx()  
color = 'tab:red'
ax2.set_ylabel('Discharge Coefficient $\mu$', color=color, fontsize=12)  
ax2.plot(e_values, mu_values, 'r--', linewidth=2, label='Coefficient $\mu$')
ax2.tick_params(axis='y', labelcolor=color)
# ax2.set_ylim(0.5, 0.65)

fig.tight_layout()  
plt.title(f'Sluice Gate Outflow Characteristics ($H_0 = {H0}m, b = {b}m$)', fontsize=14)

# Combine legends
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

plt.savefig(os.path.join(output_dir, "gate_outflow_curve.png"), dpi=300, bbox_inches='tight')
print("Files generated successfully.")
