import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\ecohydraulics\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 栖息地适用性模拟 (Habitat Suitability Index, HSI) - 类似 PHABSIM 的一维映射
# 场景：评估不同流量下，某个具有深槽和浅滩的自然河流横截面对特定目标鱼类(比如成年鳟鱼)的适用性

# 1. 目标鱼类的适宜性曲线 (Suitability Curves)
# 深度适宜性 (Depth HSI): 0~0.2m 极差, 0.5~1.0m 最佳, >1.5m 逐渐变差
def hsi_depth(d):
    if d <= 0.1: return 0.0
    elif d <= 0.5: return (d - 0.1) / 0.4
    elif d <= 1.0: return 1.0
    elif d <= 2.0: return max(0.0, 1.0 - (d - 1.0) / 1.0)
    else: return 0.0

# 流速适宜性 (Velocity HSI): 0~0.2m/s 适中(但不如流动水), 0.3~0.7m/s 最佳, >1.2m/s 太快无法休息
def hsi_velocity(v):
    if v <= 0.2: return 0.5 + 2.5 * v
    elif v <= 0.7: return 1.0
    elif v <= 1.2: return max(0.0, 1.0 - (v - 0.7) / 0.5)
    else: return 0.0

# 2. 河流横截面物理建模 (Cross-section Geometry)
# 宽度 20m，左边浅滩，中间深槽，右边陡岸
x = np.linspace(0, 20, 100)
# 地形高程 z_bed
z_bed = np.zeros_like(x)
for i, xi in enumerate(x):
    if xi <= 8:
        z_bed[i] = 2.0 - 0.1 * xi # 左侧缓坡浅滩
    elif xi <= 15:
        z_bed[i] = 1.2 - 0.5 * np.sin(np.pi * (xi - 8) / 7) # 中间深槽 (最深处 z=0.7)
    else:
        z_bed[i] = 1.2 + 0.3 * (xi - 15) # 右侧陡岸

# 糙率分布 (浅滩杂草多n=0.04，深槽卵石n=0.03)
n_roughness = np.where(x <= 8, 0.04, np.where(x <= 15, 0.03, 0.05))
S0 = 0.001 # 纵向底坡

# 3. 水动力学计算与 WUA 积分
# 计算特定水位 (Water Surface Elevation, WSE) 下的面积、流速和加权可用面积 (Weighted Usable Area, WUA)
def calculate_wua_at_wse(wse):
    depths = wse - z_bed
    depths[depths < 0] = 0 # 没水的地方深度为0
    
    # 计算面积和湿周 (为了简化，使用垂线分条法)
    dx = x[1] - x[0]
    WUA = 0.0
    total_Q = 0.0
    
    # 记录该水位下的各点流速和 HSI，用于绘图
    v_dist = np.zeros_like(x)
    hsi_tot_dist = np.zeros_like(x)
    
    for i in range(len(x)):
        if depths[i] > 0.01:
            # 局部曼宁公式估算局部流速 (假设流线平行)
            v_local = (1.0 / n_roughness[i]) * (depths[i]**(2/3)) * np.sqrt(S0)
            dq = v_local * depths[i] * dx
            total_Q += dq
            v_dist[i] = v_local
            
            # 计算局部组合栖息地适宜性指数 (Composite HSI)
            hsi_d = hsi_depth(depths[i])
            hsi_v = hsi_velocity(v_local)
            # 几何平均法: HSI = sqrt(HSI_d * HSI_v)
            hsi_tot = np.sqrt(hsi_d * hsi_v)
            hsi_tot_dist[i] = hsi_tot
            
            # 积分 WUA (面积 * 适宜度)
            WUA += dx * hsi_tot
            
    return total_Q, WUA, depths, v_dist, hsi_tot_dist

# 4. 扫描不同水位，寻找最佳生态流量
wse_array = np.linspace(1.0, 3.5, 30) # 水位从 1.0m (快干了) 到 3.5m (大水)
Q_list = []
WUA_list = []

for wse in wse_array:
    Q, WUA, _, _, _ = calculate_wua_at_wse(wse)
    Q_list.append(Q)
    WUA_list.append(WUA)

# 找出最优流量 (Max WUA)
opt_idx = np.argmax(WUA_list)
Q_opt = Q_list[opt_idx]
WUA_max = WUA_list[opt_idx]

# 5. 可视化绘图
# 图 A: 流量-WUA 关系曲线
plt.figure(figsize=(10, 5))
plt.plot(Q_list, WUA_list, 'b-', linewidth=3)
plt.plot(Q_opt, WUA_max, 'ro', markersize=10, label=f'Optimal Flow = {Q_opt:.1f} m³/s')
plt.axvline(x=Q_opt, color='r', linestyle='--')
plt.xlabel('Discharge $Q$ ($m^3/s$)', fontsize=12)
plt.ylabel('Weighted Usable Area (WUA) $m^2/m$', fontsize=12)
plt.title('Habitat - Flow Relationship (PHABSIM concept)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.savefig(os.path.join(output_dir, "wua_flow_curve.png"), dpi=300, bbox_inches='tight')

# 图 B: 最优流量下的横截面生境质量分布
Q_target, WUA_target, d_opt, v_opt, hsi_opt = calculate_wua_at_wse(wse_array[opt_idx])

fig, ax1 = plt.subplots(figsize=(12, 6))

# 画地形和水位
ax1.fill_between(x, 0, z_bed, color='saddlebrown', alpha=0.8, label='River Bed')
ax1.fill_between(x, z_bed, wse_array[opt_idx], where=(wse_array[opt_idx] > z_bed), color='cyan', alpha=0.3, label='Water')
ax1.plot(x, np.ones_like(x)*wse_array[opt_idx], 'b-', linewidth=2)
ax1.set_xlabel('Distance Across Channel (m)', fontsize=12)
ax1.set_ylabel('Elevation (m)', fontsize=12)

# 在水面上方用颜色或热力条展示 HSI
# 为了直观，我们画一条漂浮在水面上方的散点图，颜色深浅代表 HSI
sc = ax1.scatter(x, np.ones_like(x)*wse_array[opt_idx] + 0.2, c=hsi_opt, cmap='RdYlGn', s=100, vmin=0, vmax=1)
plt.colorbar(sc, ax=ax1, label='Habitat Suitability Index (0=Dead, 1=Perfect)')

plt.title(f'Cross-section Habitat Quality at Optimal Flow ({Q_opt:.1f} m³/s)', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cross_section_habitat.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [5, 10, opt_idx, 20, 28] # 挑几个流量点
for idx in snapshots:
    history.append({
        'Water Surface Elev (m)': round(wse_array[idx], 2),
        'River Discharge Q (m³/s)': round(Q_list[idx], 2),
        'Weighted Usable Area WUA': round(WUA_list[idx], 2),
        'Habitat Rating': 'Optimal' if idx == opt_idx else ('Poor' if WUA_list[idx] < 0.5*WUA_max else 'Fair')
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "phabsim_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
