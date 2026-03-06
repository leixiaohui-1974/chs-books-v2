import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 产流机制模拟 (Runoff Generation Mechanisms)
# 模拟霍顿 (Horton) 下渗曲线与超渗产流 (Infiltration Excess / Hortonian Overland Flow)
# 以及蓄满产流 (Saturation Excess / Dunne Overland Flow) 

# 1. 模拟参数设定
t_end = 120 # 模拟时间 120 分钟
dt = 1.0 # 步长 1 分钟
time = np.arange(0, t_end, dt)
N = len(time)

# 降雨事件 (Rainfall Event) - mm/hr 转换为 mm/min
rainfall_rate = np.zeros(N)
rainfall_rate[10:40] = 50.0 / 60.0 # 前半段暴雨 50 mm/h
rainfall_rate[40:80] = 10.0 / 60.0 # 中段小雨 10 mm/h
rainfall_rate[80:110] = 80.0 / 60.0 # 后半段特大暴雨 80 mm/h

# 2. 霍顿下渗模型 (Horton Infiltration Model)
# f(t) = fc + (f0 - fc) * exp(-k*t)
f0 = 40.0 / 60.0 # 初始下渗率 40 mm/h
fc = 5.0 / 60.0  # 稳定下渗率 5 mm/h
k_decay = 0.05   # 下渗衰减系数 min^-1

# 蓄水能力模型 (土壤最大蓄水量)
S_max = 15.0 # 整个土柱最大可以蓄水 15 mm
S_current = 0.0 # 当前土壤含水量

# 记录变量
infiltration_capacity = np.zeros(N)
actual_infiltration = np.zeros(N)
runoff_hortonian = np.zeros(N) # 超渗产流
runoff_saturation = np.zeros(N) # 蓄满产流
soil_moisture = np.zeros(N)

# 3. 产流过程计算
t_infiltration = 0.0 # 有效下渗累积时间

for i in range(N):
    # 霍顿下渗能力曲线 (仅在有雨时衰减)
    if rainfall_rate[i] > 0:
        f_cap = fc + (f0 - fc) * np.exp(-k_decay * t_infiltration)
        t_infiltration += dt
    else:
        # 雨停后土壤稍微恢复下渗能力 (简化处理)
        f_cap = fc + (f0 - fc) * np.exp(-k_decay * t_infiltration)
        t_infiltration = max(0, t_infiltration - dt * 0.2)
        
    infiltration_capacity[i] = f_cap
    
    # a) 计算超渗产流 (Infiltration Excess)
    if rainfall_rate[i] > f_cap:
        runoff_hortonian[i] = rainfall_rate[i] - f_cap
        actual_infil = f_cap
    else:
        runoff_hortonian[i] = 0.0
        actual_infil = rainfall_rate[i]
        
    actual_infiltration[i] = actual_infil
    
    # b) 土壤蓄水更新与蓄满产流 (Saturation Excess)
    # 渗入土壤的水会增加含水量
    S_current += actual_infil * dt
    
    if S_current > S_max:
        # 超过土壤蓄水极限的部分，全部转化为蓄满产流
        runoff_saturation[i] = (S_current - S_max) / dt
        S_current = S_max # 扣除溢出部分
        # 并且此时实际下渗被迫中止(无法再渗)
        actual_infiltration[i] = 0.0
    else:
        runoff_saturation[i] = 0.0
        
    soil_moisture[i] = S_current

# 转换为 mm/hr 方便绘图展示
rainfall_hr = rainfall_rate * 60.0
f_cap_hr = infiltration_capacity * 60.0
runoff_hort_hr = runoff_hortonian * 60.0
runoff_sat_hr = runoff_saturation * 60.0

# 4. 绘图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 子图1：降雨、下渗能力与产流机制
ax1.bar(time, rainfall_hr, width=dt, color='blue', alpha=0.3, label='Rainfall Intensity')
ax1.plot(time, f_cap_hr, 'k-', linewidth=3, label='Horton Infiltration Capacity $f_p$')

# 填充超渗产流区域 (降雨 > 下渗能力)
ax1.fill_between(time, f_cap_hr, rainfall_hr, where=(rainfall_hr > f_cap_hr), color='red', alpha=0.5, label='Hortonian Runoff (Infiltration Excess)')

# 画出蓄满产流的区域 (土壤满了以后，所有下渗的水都被迫排出地表)
# 因为蓄满后 actual_infiltration=0, f_cap 仍有值，画出此时的强迫产流
ax1.fill_between(time, 0, runoff_sat_hr, color='orange', alpha=0.7, label='Dunne Runoff (Saturation Excess)')

ax1.set_ylabel('Rate (mm/hr)', fontsize=12)
ax1.set_title('Runoff Generation Mechanisms: Hortonian vs Saturation Excess', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 子图2：土壤含水量动态
ax2.plot(time, soil_moisture, 'g-', linewidth=3, label='Soil Moisture Storage')
ax2.axhline(y=S_max, color='r', linestyle='--', linewidth=2, label=f'Maximum Storage Capacity ($S_{{max}}={S_max}mm$)')

# 标注蓄满时刻
sat_idx = np.where(soil_moisture >= S_max)[0]
if len(sat_idx) > 0:
    first_sat = time[sat_idx[0]]
    ax2.axvline(x=first_sat, color='orange', linestyle=':')
    ax2.annotate('Soil becomes fully saturated here.\nAll further infiltration turns into Dunne runoff.', 
                 xy=(first_sat, S_max), xytext=(first_sat-40, S_max-5),
                 arrowprops=dict(facecolor='orange', shrink=0.05))

ax2.set_xlabel('Time (minutes)', fontsize=12)
ax2.set_ylabel('Storage (mm)', fontsize=12)
ax2.legend(loc='lower right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "runoff_generation_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [20, 50, 90, 100]

for idx in snapshots:
    history.append({
        'Time (min)': idx,
        'Rainfall (mm/h)': round(rainfall_hr[idx], 1),
        'Infil Capacity fp (mm/h)': round(f_cap_hr[idx], 1),
        'Hortonian Runoff (mm/h)': round(runoff_hort_hr[idx], 1),
        'Soil Storage (mm)': round(soil_moisture[idx], 1),
        'Saturation Runoff (mm/h)': round(runoff_sat_hr[idx], 1)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "runoff_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
