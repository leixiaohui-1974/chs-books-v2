import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 复式断面河道参数 (Compound Channel)
S0 = 0.0008      # 河道底坡

# 主槽参数 (Main Channel)
b_m = 20.0       # 底宽 m
m_m = 1.5        # 边坡系数
n_m = 0.025      # 糙率 (天然河道主槽)
z_m = 0.0        # 主槽底高程

# 滩地参数 (Floodplains) - 假设左右对称
b_f = 30.0       # 单侧滩地底宽 m
m_f = 2.0        # 滩地边坡系数
n_f = 0.050      # 糙率 (滩地杂草丛生，糙率很大)
h_bank = 3.0     # 滩地高出主槽底的相对高程 (滩唇高度) m

# 计算复式断面各部分的几何水力参数和流量
def calc_compound_flow(h_total):
    # 如果水深没有漫过主槽，则只有主槽有水
    if h_total <= h_bank:
        A_m = (b_m + m_m * h_total) * h_total
        P_m = b_m + 2 * h_total * np.sqrt(1 + m_m**2)
        R_m = A_m / P_m
        Q_m = (1/n_m) * A_m * (R_m**(2/3)) * np.sqrt(S0)
        return Q_m, Q_m, 0.0, 0.0, A_m
        
    # 如果水深漫滩，则需要分槽计算
    # 1. 主槽部分 (水深为 h_total)
    # 注意：为了简化，一般将滩地以上的主槽垂直水体视为与滩地水体分离，不计侧向剪切力(加假壁)
    A_m = (b_m + m_m * h_bank) * h_bank + (b_m + 2 * m_m * h_bank) * (h_total - h_bank)
    P_m = b_m + 2 * h_bank * np.sqrt(1 + m_m**2) # 不计假壁湿周
    R_m = A_m / P_m
    Q_m = (1/n_m) * A_m * (R_m**(2/3)) * np.sqrt(S0)
    
    # 2. 滩地部分 (两侧合并)
    h_f = h_total - h_bank
    A_f = 2 * ((b_f + m_f * h_f) * h_f)
    P_f = 2 * (b_f + h_f * np.sqrt(1 + m_f**2)) # 不计假壁湿周
    R_f = A_f / P_f
    Q_f = (1/n_f) * A_f * (R_f**(2/3)) * np.sqrt(S0)
    
    Q_total = Q_m + Q_f
    return Q_total, Q_m, Q_f, h_f, A_m + A_f

# 生成不同水深下的水位-流量关系数据 (Stage-Discharge Curve)
h_values = np.linspace(1.0, 6.0, 50)
Q_total_list = []
Q_main_list = []
Q_flood_list = []

for h in h_values:
    Q_t, Q_m, Q_f, _, _ = calc_compound_flow(h)
    Q_total_list.append(Q_t)
    Q_main_list.append(Q_m)
    Q_flood_list.append(Q_f)

# 制作表格数据
h_table = [1.0, 2.0, 3.0, 3.5, 4.0, 5.0, 6.0]
history = []
for h in h_table:
    Q_t, Q_m, Q_f, h_f, A_total = calc_compound_flow(h)
    V_avg = Q_t / A_total if A_total > 0 else 0
    history.append({
        'Total Depth h (m)': round(h, 2),
        'Floodplain Depth (m)': round(h_f, 2),
        'Main Ch Q (m³/s)': round(Q_m, 2),
        'Floodplain Q (m³/s)': round(Q_f, 2),
        'Total Q (m³/s)': round(Q_t, 2),
        'Avg Velocity (m/s)': round(V_avg, 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "compound_flow_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 绘制水位-流量关系曲线 (Rating Curve)
plt.figure(figsize=(9, 7))

plt.plot(Q_total_list, h_values, 'k-', linewidth=3, label='Total Discharge ($Q_{total}$)')
plt.plot(Q_main_list, h_values, 'b--', linewidth=2, label='Main Channel ($Q_{main}$)')
plt.plot(Q_flood_list, h_values, 'g-.', linewidth=2, label='Floodplains ($Q_{flood}$)')

plt.axhline(y=h_bank, color='r', linestyle=':', alpha=0.7, label=f'Bankfull Stage (h={h_bank}m)')

plt.xlabel('Discharge $Q$ ($m^3/s$)', fontsize=12)
plt.ylabel('Water Depth $h$ (m)', fontsize=12)
plt.title('Stage-Discharge Curve for Compound Channel', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

# Annotation for slope break
idx_break = list(h_values).index(next(h for h in h_values if h > h_bank))
plt.annotate('Slope Break due to\nFloodplain Inundation', 
             xy=(Q_total_list[idx_break], h_values[idx_break]), 
             xytext=(Q_total_list[idx_break]+100, h_values[idx_break]-0.5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

plt.savefig(os.path.join(output_dir, "rating_curve.png"), dpi=300, bbox_inches='tight')
print("Files generated successfully.")
