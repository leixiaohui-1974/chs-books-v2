import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 梯形渠道参数
Q_target = 50.0  # 目标流量 m^3/s
b = 5.0          # 底宽 m
m = 1.5          # 边坡系数
S0 = 0.0005      # 底坡
n = 0.015        # 曼宁糙率
g = 9.81         # 重力加速度

def manning_equation(h):
    A = (b + m * h) * h
    P = b + 2 * h * np.sqrt(1 + m**2)
    R = A / P
    return (1.0 / n) * A * (R**(2/3)) * np.sqrt(S0)

def froude_number(h, Q):
    A = (b + m * h) * h
    v = Q / A
    D = A / (b + 2 * m * h)
    return v / np.sqrt(g * D)

def solve_normal_depth(Q, h_guess=1.0, tol=1e-5, max_iter=100):
    h = h_guess
    history = []
    
    for i in range(max_iter):
        Q_calc = manning_equation(h)
        Fr = froude_number(h, Q_calc)
        history.append({
            'Iteration': i,
            'Depth (m)': round(h, 4),
            'Calculated Q (m³/s)': round(Q_calc, 4),
            'Froude No.': round(Fr, 4)
        })
        
        error = Q_calc - Q
        if abs(error) < tol:
            return h, i, history
            
        # 数值导数
        dh = 0.001
        dQ_dh = (manning_equation(h + dh) - Q_calc) / dh
        h_new = h - error / dQ_dh
        # 【安全护栏】防止迭代进入负水深禁区
        h = max(h_new, 0.01)
        
    return h, max_iter, history

# 执行求解
h_normal, iterations, history = solve_normal_depth(Q_target)

# Convert history to DataFrame and save as markdown table
df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "iteration_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

color = 'tab:blue'
ax1.set_xlabel('Iteration')
ax1.set_ylabel('Depth (m)', color=color)
ax1.plot(df['Iteration'], df['Depth (m)'], marker='o', color=color, label='Depth')
ax1.tick_params(axis='y', labelcolor=color)
ax1.axhline(y=h_normal, color='b', linestyle='--', alpha=0.5, label='Converged Depth')
ax1.set_xticks(df['Iteration'])

ax2 = ax1.twinx()  
color = 'tab:red'
ax2.set_ylabel('Calculated Q ($m^3/s$)', color=color)  
ax2.plot(df['Iteration'], df['Calculated Q (m³/s)'], marker='s', color=color, label='Calc Q')
ax2.tick_params(axis='y', labelcolor=color)
ax2.axhline(y=Q_target, color='r', linestyle='--', alpha=0.5, label='Target Q')

fig.tight_layout()  
plt.title('Newton-Raphson Convergence for Normal Depth')
# Combine legends
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

plt.savefig(os.path.join(output_dir, "newton_iteration_sim.png"), dpi=300)
print("Files generated successfully.")
