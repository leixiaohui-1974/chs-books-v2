import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.spatial import Voronoi, voronoi_plot_2d

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 气象降水空间插值模拟 (Spatial Interpolation of Rainfall)
# 场景：一个流域内有 5 个雨量站，我们需要估计整个流域的面平均降雨量。
# 对比 泰森多边形 (Thiessen Polygon, 离散/集总) 与 反距离权重 (IDW, 连续/分布式)

# 1. 定义流域边界和雨量站
basin_size = 100.0 # 100km x 100km
stations = np.array([
    [20, 20],  # Station A
    [80, 30],  # Station B
    [50, 60],  # Station C
    [10, 80],  # Station D
    [90, 90]   # Station E
])
station_names = ['A', 'B', 'C', 'D', 'E']
rainfall = np.array([10.0, 50.0, 25.0, 100.0, 5.0]) # 测得的降雨量 mm

# 2. 泰森多边形法 (Thiessen Polygons)
# 泰森多边形代表了集总式模型的核心思想：将空间强制划分为几个同质的块
vor = Voronoi(stations)

# 3. 反距离权重法 (Inverse Distance Weighting, IDW)
# IDW 代表了分布式模型的核心思想：空间是连续平滑过渡的
grid_size = 1.0
x = np.arange(0, basin_size, grid_size)
y = np.arange(0, basin_size, grid_size)
X, Y = np.meshgrid(x, y)

def idw_interpolation(x_target, y_target, power=2):
    weights = []
    for i in range(len(stations)):
        dist = np.sqrt((x_target - stations[i, 0])**2 + (y_target - stations[i, 1])**2)
        if dist < 1e-4:
            return rainfall[i]
        weights.append(1.0 / (dist**power))
    
    weights = np.array(weights)
    weights /= np.sum(weights)
    return np.sum(weights * rainfall)

Z_idw = np.zeros_like(X)
for i in range(X.shape[0]):
    for j in range(X.shape[1]):
        Z_idw[i, j] = idw_interpolation(X[i, j], Y[i, j], power=2)

# 4. 绘图对比
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 子图1: 泰森多边形
voronoi_plot_2d(vor, ax=ax1, show_vertices=False, line_colors='k', line_width=2, line_alpha=0.6, point_size=0)
for i, txt in enumerate(station_names):
    ax1.plot(stations[i, 0], stations[i, 1], 'ro', markersize=8)
    ax1.annotate(f"{txt}\n{rainfall[i]}mm", (stations[i, 0]+2, stations[i, 1]+2), fontsize=12, weight='bold')

ax1.set_xlim(0, basin_size)
ax1.set_ylim(0, basin_size)
ax1.set_title('Thiessen Polygons (Lumped / Discrete Space)', fontsize=14)
ax1.set_xlabel('X (km)'); ax1.set_ylabel('Y (km)')

# 子图2: IDW
im = ax2.imshow(Z_idw, origin='lower', extent=[0, basin_size, 0, basin_size], cmap='Blues', alpha=0.8)
for i, txt in enumerate(station_names):
    ax2.plot(stations[i, 0], stations[i, 1], 'ro', markersize=8)
    ax2.annotate(f"{txt}", (stations[i, 0]+2, stations[i, 1]+2), fontsize=12, weight='bold')

plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04, label='Rainfall (mm)')
ax2.set_title('Inverse Distance Weighting (Distributed / Continuous Space)', fontsize=14)
ax2.set_xlabel('X (km)'); ax2.set_ylabel('Y (km)')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "spatial_interpolation_sim.png"), dpi=300, bbox_inches='tight')

# 计算面平均降雨量对比
# a. IDW 简单算术平均
idw_mean = np.mean(Z_idw)

# b. 简单算术平均 (假设所有站权重一样)
arithmetic_mean = np.mean(rainfall)

# 生成追踪表格
history = [
    {'Method': 'Arithmetic Mean (算术平均)', 'Areal Average Rainfall (mm)': round(arithmetic_mean, 2), 'Spatial Resolution': 'Zero (Single Point)'},
    {'Method': 'Inverse Distance Weighting (IDW)', 'Areal Average Rainfall (mm)': round(idw_mean, 2), 'Spatial Resolution': f'{int(grid_size)} km Grid (Continuous)'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "interpolation_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
