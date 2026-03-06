import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\underground-water-dynamics\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 区域地下水流优化管理 (Groundwater Optimization)
# 模拟带有多个抽水井和环境约束的含水层优化问题
# 目标：最大化总抽水量
# 约束：观测点的水位降深不能超过安全阈值

# 参数设置
L_x = 2000.0      # 区域长度 m
L_y = 2000.0      # 区域宽度 m
nx, ny = 40, 40   # 网格
dx = L_x / nx
dy = L_y / ny
T = 0.02          # 导水系数 m^2/s
H0 = 50.0         # 初始稳态水头 m

# 3 个候选抽水井位置 (x_idx, y_idx)
wells = [
    {'name': 'Well_1', 'loc': (10, 10)},
    {'name': 'Well_2', 'loc': (30, 20)},
    {'name': 'Well_3', 'loc': (15, 30)}
]

# 2 个必须保护的环境观测点 (比如湿地、河流边)
obs_points = [
    {'name': 'Wetland', 'loc': (20, 20), 'max_drawdown': 2.0},
    {'name': 'River_Edge', 'loc': (35, 35), 'max_drawdown': 1.5}
]

# 计算单位抽水量 (Q=1) 在全域引起的稳态降深响应矩阵 (Response Matrix)
# 根据叠加原理，多井降深 s_total = sum(Q_i * s_unit_i)
def calculate_unit_response(well_x, well_y):
    # 简化：使用稳态拉普拉斯方程和对数距离公式近似，或者迭代求解
    # s = (Q / 2*pi*T) * ln(R/r)
    # 假设影响半径 R = 2000m
    R_inf = 2000.0
    s_matrix = np.zeros((ny, nx))
    for j in range(ny):
        for i in range(nx):
            dist = np.sqrt(((i - well_x)*dx)**2 + ((j - well_y)*dy)**2)
            if dist < dx/2:
                dist = r_w = 0.3 # 井壁半径
            if dist < R_inf:
                s_matrix[j, i] = (1.0 / (2 * np.pi * T)) * np.log(R_inf / dist)
    return s_matrix

# 生成响应矩阵
response_matrices = []
for well in wells:
    response_matrices.append(calculate_unit_response(well['loc'][0], well['loc'][1]))

# 使用线性规划 (Linear Programming) 寻找最优抽水方案
from scipy.optimize import linprog

# 目标：最大化 Q1+Q2+Q3 -> 最小化 -(Q1+Q2+Q3)
c = [-1, -1, -1]

# 约束条件: A_ub * Q <= b_ub
# 约束1: 观测点降深约束
A_ub = []
b_ub = []

for obs in obs_points:
    ox, oy = obs['loc']
    row = []
    for rm in response_matrices:
        row.append(rm[oy, ox])
    A_ub.append(row)
    b_ub.append(obs['max_drawdown'])

# 约束2: 单井最大产能约束 (例如每口井最多抽 0.1 m^3/s)
bounds = [(0, 0.1), (0, 0.1), (0, 0.1)]

# 求解
res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

Q_opt = res.x
total_Q = -res.fun

# 计算最优方案下的全域水头分布
h_final = np.ones((ny, nx)) * H0
for i, q in enumerate(Q_opt):
    h_final -= q * response_matrices[i]

# 绘制最优水头分布图
X, Y = np.meshgrid(np.linspace(0, L_x, nx), np.linspace(0, L_y, ny))

plt.figure(figsize=(10, 8))
contour = plt.contour(X, Y, h_final, levels=20, cmap='coolwarm')
plt.clabel(contour, inline=True, fontsize=10)

# 标记水井和观测点
for i, well in enumerate(wells):
    plt.plot(well['loc'][0]*dx, well['loc'][1]*dy, 'r^', markersize=12, label=f"Pump {well['name']} (Q={Q_opt[i]:.3f})" if i==0 else "")
    plt.text(well['loc'][0]*dx+50, well['loc'][1]*dy, f"W{i+1}: {Q_opt[i]:.3f} m³/s", color='red', fontweight='bold')

for i, obs in enumerate(obs_points):
    plt.plot(obs['loc'][0]*dx, obs['loc'][1]*dy, 'gD', markersize=10, label="Obs Point (Constraint)" if i==0 else "")
    ox, oy = obs['loc']
    actual_s = H0 - h_final[oy, ox]
    plt.text(ox*dx+50, oy*dy, f"{obs['name']}\nDrop: {actual_s:.2f}m / {obs['max_drawdown']}m", color='green')

plt.xlabel('X Coordinate (m)', fontsize=12)
plt.ylabel('Y Coordinate (m)', fontsize=12)
plt.title(f'Optimized Groundwater Pumping Strategy (Total Q = {total_Q:.3f} m³/s)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.3)
plt.savefig(os.path.join(output_dir, "optimized_flow_field.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
for i, well in enumerate(wells):
    history.append({
        'Component': well['name'],
        'Type': 'Pumping Well',
        'Optimal Value': f"{Q_opt[i]:.3f} m³/s",
        'Constraint / Capacity': "Max 0.100 m³/s"
    })
for i, obs in enumerate(obs_points):
    ox, oy = obs['loc']
    actual_s = H0 - h_final[oy, ox]
    history.append({
        'Component': obs['name'],
        'Type': 'Env Constraint (Drawdown)',
        'Optimal Value': f"{actual_s:.2f} m",
        'Constraint / Capacity': f"Max {obs['max_drawdown']} m"
    })

history.append({
    'Component': 'Total Pumping',
    'Type': 'Objective Function',
    'Optimal Value': f"{total_Q:.3f} m³/s",
    'Constraint / Capacity': "-"
})

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "optimization_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
