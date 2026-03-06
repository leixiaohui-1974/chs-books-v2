import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch07"
os.makedirs(output_dir, exist_ok=True)

# 蒸散发模拟 (Evapotranspiration Modeling)
# 对比简单的温度法 (Hargreaves) 与 严谨的物理能量平衡法 (Penman-Monteith)

# 1. 模拟一天的气象强迫数据 (24小时)
time_hours = np.arange(0, 24, 1.0)
N = len(time_hours)

# 温度 Temperature (°C)
T_mean = 20.0
T_amp = 8.0
T_air = T_mean + T_amp * np.sin(np.pi * (time_hours - 9) / 12)

# 净辐射 Net Radiation (Rn, MJ/m^2/h)
Rn = np.zeros(N)
for i, t in enumerate(time_hours):
    if 6 <= t <= 18: # 白天有太阳
        Rn[i] = 2.5 * np.sin(np.pi * (t - 6) / 12)
    else: # 夜间长波辐射净损失
        Rn[i] = -0.5

# 风速 Wind Speed (m/s) at 2m height
u2 = np.ones(N) * 2.0
u2[12:18] = 4.0 # 下午起风

# 相对湿度 Relative Humidity (%)
RH = 80.0 - 40.0 * np.sin(np.pi * (time_hours - 6) / 12)
RH = np.clip(RH, 30, 100)

# 2. 模型核心参数
gamma = 0.066 # 湿度计常数 kPa/°C
G = 0.082 # 土壤热通量，白天通常为 0.1Rn，这里做简单常数处理

# --- Hargreaves 公式 (极简，仅需温度) ---
# 原公式是日尺度的 ET0 = 0.0023 * (T_mean + 17.8) * (T_max - T_min)^0.5 * Ra
# 我们做一个适合小时尺度的变体模拟曲线
ET_Hargreaves = np.zeros(N)
T_max = np.max(T_air)
T_min = np.min(T_air)
for i in range(N):
    if Rn[i] > 0:
        # 用气温粗略估计辐射驱动
        ET_Hargreaves[i] = 0.0023 * (T_air[i] + 17.8) * np.sqrt(T_max - T_min) * (Rn[i] * 0.408)
    else:
        ET_Hargreaves[i] = 0.0

# --- FAO-56 Penman-Monteith 公式 (严谨的物理热力学) ---
ET_Penman = np.zeros(N)
for i in range(N):
    T = T_air[i]
    
    # 饱和水汽压 (kPa)
    e_s = 0.6108 * np.exp((17.27 * T) / (T + 237.3))
    
    # 实际水汽压 (kPa)
    e_a = e_s * (RH[i] / 100.0)
    
    # 饱和水汽压曲线斜率 (kPa/°C)
    Delta = (4098 * e_s) / ((T + 237.3)**2)
    
    # 辐射项 (Energy Term)
    # Rn 已经是 MJ/m2/h, 需转换。公式中分子第一项为 0.408 * Delta * (Rn - G)
    term_energy = 0.408 * Delta * (Rn[i] - G * (1 if Rn[i]>0 else -1))
    
    # 空气动力学项 (Aerodynamic Term)
    # 公式分子第二项为 gamma * (37 / (T + 273)) * u2 * (e_s - e_a) 适用于小时尺度
    term_aero = gamma * (37.0 / (T + 273.15)) * u2[i] * (e_s - e_a)
    
    # 分母
    denominator = Delta + gamma * (1 + 0.34 * u2[i])
    
    et_val = (term_energy + term_aero) / denominator
    ET_Penman[i] = max(et_val, 0.0) # 防止负值冷凝，简化只算蒸发

# 3. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 气象强迫图
color_T = 'tab:red'
ax1.set_ylabel('Air Temp (°C) / Wind Speed (m/s)', color=color_T, fontsize=12)
ax1.plot(time_hours, T_air, 'r-', linewidth=2, label='Air Temperature')
ax1.plot(time_hours, u2, 'm--', linewidth=2, label='Wind Speed')
ax1.tick_params(axis='y', labelcolor=color_T)

ax1_2 = ax1.twinx()
color_Rn = 'tab:orange'
ax1_2.set_ylabel('Net Radiation (MJ/$m^2$/h)', color=color_Rn, fontsize=12)
ax1_2.fill_between(time_hours, 0, Rn, where=(Rn>0), color='orange', alpha=0.3, label='Solar Net Radiation')
ax1_2.tick_params(axis='y', labelcolor=color_Rn)

ax1.set_title('Meteorological Forcings over 24 Hours', fontsize=14)
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax1_2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.6)

# ET 模型对比图
ax2.plot(time_hours, ET_Hargreaves, 'g--', linewidth=2, label='Hargreaves (Temperature-Based)')
ax2.plot(time_hours, ET_Penman, 'b-', linewidth=3, label='Penman-Monteith (Energy & Aerodynamics)')
ax2.fill_between(time_hours, ET_Hargreaves, ET_Penman, color='gray', alpha=0.2, label='Model Discrepancy due to Wind/Humidity')

ax2.set_xlabel('Time of Day (Hour)', fontsize=12)
ax2.set_ylabel('Evapotranspiration ET0 (mm/h)', fontsize=12)
ax2.set_title('ET0 Estimation: Penman-Monteith vs Hargreaves', fontsize=14)
ax2.set_xticks(np.arange(0, 25, 2))
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# 标注起风时的发散
ax2.annotate('Wind speed peaks.\nPenman captures aerodynamic evaporation.\nHargreaves fails to respond.', 
             xy=(15, ET_Penman[15]), xytext=(7, 0.5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "et_models_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [6, 12, 15, 18, 22] # 早晨, 正午, 下午大风, 傍晚, 夜晚
for idx in snapshots:
    history.append({
        'Hour': idx,
        'Temp (°C)': round(T_air[idx], 1),
        'Radiation Rn': round(Rn[idx], 2),
        'Wind Speed (m/s)': u2[idx],
        'Hargreaves ET (mm/h)': round(ET_Hargreaves[idx], 3),
        'Penman-Monteith ET (mm/h)': round(ET_Penman[idx], 3),
        'Dominant Mechanism': 'Radiation' if idx==12 else ('Aerodynamic (Wind)' if idx==15 else 'None')
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "evapotranspiration_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
