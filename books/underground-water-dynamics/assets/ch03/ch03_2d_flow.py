import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\underground-water-dynamics\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 二维潜水含水层恒定流模拟 (有限差分法)
# 模拟矩形岛屿/地块，中心有一口抽水井，四周被恒定水位的河流环绕

# 参数设置
L_x = 1000.0      # 区域长度 (x方向) m
L_y = 1000.0      # 区域宽度 (y方向) m
nx = 50           # x方向网格数
ny = 50           # y方向网格数
dx = L_x / nx
dy = L_y / ny

K = 0.005         # 渗透系数 m/s
H_river = 15.0    # 边界河流恒定水位 m (相对于潜水底板)
Z_bottom = 0.0    # 底板高程 m

# 抽水井参数
well_x_idx = int(nx / 2)
well_y_idx = int(ny / 2)
Q_well = 0.1      # 抽水流量 m^3/s

# 降雨补给 (Recharge)
W_recharge = 0.0000001 # 降雨补给率 m/s

# 初始化水头矩阵
h = np.ones((ny, nx)) * H_river
h_new = np.ones((ny, nx)) * H_river

# 采用 Gauss-Seidel 迭代法求解二维 Boussinesq 方程 (非线性，因为透水厚度随 h 变化)
# d/dx(K*h*dh/dx) + d/dy(K*h*dh/dy) + W - Q_well = 0
# 使用简化的线性化迭代或者逐次超松弛 (SOR)

max_iter = 2000
tolerance = 1e-4

# 迭代求解
for iteration in range(max_iter):
    max_diff = 0.0
    
    for j in range(1, ny-1):
        for i in range(1, nx-1):
            # 采用透水厚度的算术平均值计算导水系数 T
            T_E = K * (h[j, i+1] + h[j, i]) / 2.0
            T_W = K * (h[j, i-1] + h[j, i]) / 2.0
            T_N = K * (h[j+1, i] + h[j, i]) / 2.0
            T_S = K * (h[j-1, i] + h[j, i]) / 2.0
            
            # 处理源汇项 (W_recharge 是面源，Q_well 是点汇)
            source_term = W_recharge * dx * dy
            if i == well_x_idx and j == well_y_idx:
                source_term -= Q_well
                
            # 五点差分格式求解 h[j, i]
            # (T_E * (h[i+1]-h[i])/dx^2 + T_W * (h[i-1]-h[i])/dx^2 + ...) = -source_term/(dx*dy)
            # 假定 dx = dy
            sum_T = T_E + T_W + T_N + T_S
            
            h_new_val = (T_E * h[j, i+1] + T_W * h[j, i-1] + T_N * h[j+1, i] + T_S * h[j-1, i] + source_term) / sum_T
            
            diff = abs(h_new_val - h[j, i])
            if diff > max_diff:
                max_diff = diff
                
            h[j, i] = h_new_val
            
    # 边界条件处理 (四周恒定水头 H_river)
    # 在初始化时已经赋值，循环中不需要再动
    
    if max_diff < tolerance:
        print(f"Converged at iteration {iteration}")
        break

# 绘制地下水流场等值线图 (等水头线)
X, Y = np.meshgrid(np.linspace(0, L_x, nx), np.linspace(0, L_y, ny))

plt.figure(figsize=(10, 8))
contour = plt.contour(X, Y, h, levels=20, cmap='viridis')
plt.clabel(contour, inline=True, fontsize=10)
plt.colorbar(contour, label='Groundwater Head (m)')

# 绘制流线 (流速矢量)
# v_x = -K * dh/dx, v_y = -K * dh/dy
grad_x = np.gradient(h, dx, axis=1)
grad_y = np.gradient(h, dy, axis=0)
v_x = -K * grad_x
v_y = -K * grad_y

# 跳过一些点以使箭头清晰
step = 3
plt.quiver(X[::step, ::step], Y[::step, ::step], v_x[::step, ::step], v_y[::step, ::step], 
           color='gray', alpha=0.6, width=0.003, label='Flow Vectors')

plt.plot(well_x_idx * dx, well_y_idx * dy, 'ro', markersize=10, label='Pumping Well')

plt.xlabel('X Coordinate (m)', fontsize=12)
plt.ylabel('Y Coordinate (m)', fontsize=12)
plt.title('2D Groundwater Flow Field (Unconfined Aquifer with Pumping)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.3)
plt.savefig(os.path.join(output_dir, "groundwater_flow_field.png"), dpi=300, bbox_inches='tight')

# 绘制中心截面 (y = 500m) 的水位降落曲线
x_profile = np.linspace(0, L_x, nx)
h_profile = h[well_y_idx, :]

plt.figure(figsize=(10, 6))
plt.plot(x_profile, h_profile, 'b-', linewidth=3, label='Water Table Profile')
plt.axhline(y=H_river, color='k', linestyle='--', label=f'Boundary River Level ({H_river}m)')
plt.axvline(x=500, color='r', linestyle=':', label='Well Location')
plt.fill_between(x_profile, 0, h_profile, color='cyan', alpha=0.2, label='Saturated Zone')

plt.xlabel('Distance X (m)', fontsize=12)
plt.ylabel('Water Table Elevation $H$ (m)', fontsize=12)
plt.title('Cross-section of Water Table at Y=500m', fontsize=14)
plt.ylim(0, H_river + 2)
plt.legend(loc='lower left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "cross_section_profile.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
x_points = [0, 100, 300, 480, 500] # 从边界到井
for xp in x_points:
    idx = int(xp / dx)
    h_val = h[well_y_idx, idx]
    history.append({
        'Location X (m)': xp,
        'Distance to Well r (m)': abs(500 - xp),
        'Water Table Elevation (m)': round(h_val, 2),
        'Drawdown (m)': round(H_river - h_val, 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "flow_field_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
