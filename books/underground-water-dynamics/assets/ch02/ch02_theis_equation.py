import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.special import exp1 # 对应于井函数 W(u) 的基础函数 E1(u)

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\underground-water-dynamics\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 承压含水层泰斯公式 (Theis Equation) 抽水井非稳定流模拟
# 模拟水井抽水引起的地下水位降落漏斗 (Cone of Depression)

# 含水层与水井参数
Q = 0.05          # 抽水流量 m^3/s (约 4320 m^3/d)
T = 0.01          # 导水系数 (Transmissivity) m^2/s
S = 0.0001        # 储水系数 (Storativity) 无量纲
r_w = 0.2         # 抽水井半径 m

# 泰斯井函数 W(u) 
def well_function_W(u):
    return exp1(u)

# 计算降深 s(r, t)
def calculate_drawdown(r, t):
    if t == 0: return 0.0
    u = (r**2 * S) / (4 * T * t)
    s = (Q / (4 * np.pi * T)) * well_function_W(u)
    return s

# 1. 模拟空间降落漏斗 (固定时间，不同距离)
r_values = np.logspace(np.log10(r_w), np.log10(1000), 100) # 从井壁到 1000m 远处
times_to_plot = [3600, 86400, 86400*7] # 1小时, 1天, 7天 (以秒为单位)
time_labels = ['1 Hour', '1 Day', '7 Days']

plt.figure(figsize=(10, 6))

for t, label in zip(times_to_plot, time_labels):
    s_values = [calculate_drawdown(r, t) for r in r_values]
    plt.plot(r_values, s_values, linewidth=2, label=f't = {label}')

plt.xlabel('Distance from Pumping Well $r$ (m)', fontsize=12)
plt.ylabel('Drawdown $s$ (m)', fontsize=12)
plt.title('Cone of Depression Development (Theis Solution)', fontsize=14)
plt.xscale('log') # 距离通常使用对数坐标
plt.gca().invert_yaxis() # 降深向下为正
plt.legend()
plt.grid(True, which="both", ls="--", alpha=0.5)

plt.savefig(os.path.join(output_dir, "cone_of_depression.png"), dpi=300, bbox_inches='tight')

# 2. 模拟观测井的时间序列降深 (固定距离，不同时间)
r_obs = 50.0 # 观测井距离抽水井 50m
time_array_days = np.linspace(0.01, 10, 100) # 模拟 10 天
s_obs_values = [calculate_drawdown(r_obs, t_day * 86400) for t_day in time_array_days]

plt.figure(figsize=(10, 6))
plt.plot(time_array_days, s_obs_values, 'r-', linewidth=2.5, label=f'Observation Well (r = {r_obs}m)')
plt.xlabel('Time $t$ (Days)', fontsize=12)
plt.ylabel('Drawdown $s$ (m)', fontsize=12)
plt.title('Drawdown vs Time at Observation Well', fontsize=14)
plt.gca().invert_yaxis()
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "drawdown_time_series.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
t_table_days = [0.1, 1.0, 3.0, 7.0]
r_table = [r_w, 10.0, 50.0, 200.0] # 井壁, 近处, 观测井, 远处

for t_d in t_table_days:
    row = {'Time (Days)': t_d}
    for r in r_table:
        s_val = calculate_drawdown(r, t_d * 86400)
        row[f'Drawdown at r={r}m'] = round(s_val, 2)
    history.append(row)

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "theis_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
