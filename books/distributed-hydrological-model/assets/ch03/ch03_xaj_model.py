import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 新安江模型核心算法 (Xin'anjiang Model) - 蓄满产流与三水源划分
# 模拟一场典型降雨下，土壤蓄水容量曲线 (Tension Water Capacity Curve) 的产流计算

# 1. 模拟参数设定
t_end = 150 # 模拟时间 150 小时
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 降雨事件 (Rainfall P) 和 蒸散发 (Evapotranspiration E)
P_rain = np.zeros(N)
P_rain[20:60] = 5.0  # 前期降雨，润湿土壤
P_rain[80:120] = 15.0 # 主暴雨

E_evap = np.ones(N) * 1.0 # 恒定蒸散发

# 2. 新安江模型核心参数 (三水源划分)
WM = 120.0  # 流域平均蓄水容量 (mm)
B = 0.2     # 蓄水容量分布曲线指数 (非均匀性参数)
W_init = 30.0 # 初始流域蓄水量 (mm)

# 自由水蓄水容量参数 (用于划分地表/地下径流)
SM = 20.0
EX = 1.0    # 自由水分布指数
KG = 0.3    # 地下水出流系数
KI = 0.4    # 壤中流出流系数

# 3. 状态变量初始化
W_current = W_init
S_free = 0.0 # 初始自由水蓄水量

history_W = np.zeros(N)
history_R_total = np.zeros(N)
history_Rs = np.zeros(N) # 地表径流 Surface Runoff
history_Ri = np.zeros(N) # 壤中流 Interflow
history_Rg = np.zeros(N) # 地下径流 Groundwater Runoff

# 计算蓄水容量曲线的最大值 WMM
WMM = WM * (1 + B)

def calculate_runoff_xaj(PE, W_curr):
    """新安江模型核心：基于抛物线蓄水容量曲线的产流计算"""
    if PE <= 0:
        return 0.0, max(0, W_curr + PE) # 蒸发消耗土壤水
    
    # 当前蓄水量对应的纵坐标 A
    A = WMM * (1 - (1 - W_curr / WM)**(1 / (1 + B)))
    
    if A + PE >= WMM:
        # 全流域蓄满
        R = PE - (WM - W_curr)
        W_next = WM
    else:
        # 部分面积蓄满
        R = PE - WM + W_curr + WM * (1 - (A + PE) / WMM)**(1 + B)
        W_next = W_curr + (PE - R)
        
    return R, W_next

# 4. 模型时序推演
for i in range(N):
    # 净雨 P - E
    PE = P_rain[i] - E_evap[i]
    
    # 产流计算
    R_total, W_next = calculate_runoff_xaj(PE, W_current)
    
    W_current = W_next
    history_W[i] = W_current
    history_R_total[i] = R_total
    
    # 三水源划分 (简化版)
    # R_total 先进入自由水蓄水库 S
    S_free += R_total
    
    # 如果自由水溢出(极其罕见的大暴雨直接产生超渗地表流)
    # 新安江模型通常用自由水蓄水容量曲线划分
    AU = SM * (1 - (1 - S_free/SM)**(1/(1+EX))) if S_free < SM else SM
    if S_free > SM:
        Rs_gen = S_free - SM
        S_free = SM
    else:
        Rs_gen = 0
        
    # 从自由水库中流出壤中流(Ri)和地下水(Rg)
    Ri_gen = S_free * KI
    Rg_gen = S_free * KG
    
    S_free = S_free - Ri_gen - Rg_gen
    
    history_Rs[i] = Rs_gen
    history_Ri[i] = Ri_gen
    history_Rg[i] = Rg_gen

# 5. 绘图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# 降雨与净雨
ax1.bar(time, P_rain, width=dt, color='blue', alpha=0.5, label='Gross Rainfall $P$')
ax1.plot(time, E_evap, 'r--', linewidth=2, label='Evapotranspiration $E$')
ax1.set_ylabel('Rate (mm/h)', fontsize=12)
ax1.set_title('Rainfall and Evapotranspiration Forcing', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 土壤蓄水量动态
ax2.plot(time, history_W, 'g-', linewidth=3, label='Average Soil Moisture $W$')
ax2.axhline(y=WM, color='k', linestyle=':', linewidth=2, label=f'Mean Capacity $WM={WM}$mm')
ax2.fill_between(time, 0, history_W, color='green', alpha=0.2)
ax2.set_ylabel('Soil Water Storage (mm)', fontsize=12)
ax2.set_title('Soil Moisture Accounting (XAJ Model)', fontsize=14)
ax2.legend(loc='lower right')
ax2.grid(True, linestyle='--', alpha=0.6)

# 标注完全蓄满点
sat_idx = np.where(history_W >= WM - 0.1)[0]
if len(sat_idx) > 0:
    t_sat = time[sat_idx[0]]
    ax2.annotate('Basin Fully Saturated\n100% Runoff Area', xy=(t_sat, WM), xytext=(t_sat-40, WM-20),
                 arrowprops=dict(facecolor='black', shrink=0.05))

# 三水源产流
ax3.plot(time, history_Rs, 'r-', linewidth=2, label='Surface Runoff $R_s$')
ax3.plot(time, history_Ri, 'b-.', linewidth=2, label='Interflow $R_i$')
ax3.plot(time, history_Rg, 'k--', linewidth=2, label='Groundwater Runoff $R_g$')
ax3.fill_between(time, 0, history_R_total, color='gray', alpha=0.3, label='Total Runoff $R$')
ax3.set_xlabel('Time (hours)', fontsize=12)
ax3.set_ylabel('Runoff Generation (mm/h)', fontsize=12)
ax3.set_title('Three-Component Runoff Generation (Surface, Interflow, Groundwater)', fontsize=14)
ax3.legend(loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "xaj_model_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [10, 40, 70, 100, 130]

for idx in snapshots:
    history.append({
        'Time (h)': idx,
        'Rainfall P (mm/h)': P_rain[idx],
        'Soil Storage W (mm)': round(history_W[idx], 1),
        'Saturation Deficit (mm)': round(WM - history_W[idx], 1),
        'Total Runoff R (mm/h)': round(history_R_total[idx], 2),
        'Runoff Coefficient R/P': f"{(history_R_total[idx]/P_rain[idx]*100) if P_rain[idx]>0 else 0:.1f}%"
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "xaj_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
