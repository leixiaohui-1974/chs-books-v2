import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.integrate import odeint

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\water-system-control\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 串级控制 (Cascade Control) 仿真：水箱液位(主)与进水流量(副)控制系统
# 针对泵站出水阀门具有严重非线性、死区和波动的场景

# 系统参数
A_tank = 2.0     # 水箱横截面积 m^2
C_valve = 0.5    # 底部排水阀流量系数

# 阀门(执行机构)的非线性与死区
def nonlinear_valve_flow(cmd):
    # 死区 10%
    if cmd < 10.0:
        return 0.0
    # 非线性特性
    return 0.02 * (cmd - 10.0)**1.2

# 阀门执行器的一阶惯性
tau_valve = 2.0 

# 控制器参数
# 主控制器 (液位控制) - 慢速
Kp_main = 0.5
Ki_main = 0.05
# 副控制器 (流量控制) - 快速
Kp_sub = 5.0
Ki_sub = 2.0

dt = 0.1
t = np.arange(0, 400, dt)
N = len(t)

# 目标设定
SP_level = np.ones(N) * 5.0

# 状态变量记录
h_single = np.zeros(N)
q_in_single = np.zeros(N)
u_single = np.zeros(N)
int_single = 0.0

h_cascade = np.zeros(N)
q_in_cascade = np.zeros(N)
u_cascade = np.zeros(N)
int_main = 0.0
int_sub = 0.0

# 初始状态
h_single[0] = 1.0
h_cascade[0] = 1.0
u_single[0] = 0.0
u_cascade[0] = 0.0
q_in_single[0] = 0.0
q_in_cascade[0] = 0.0

# 模拟开始
for i in range(1, N):
    # --- 扰动：供水管网压力突变导致相同阀门开度下流量波动 ---
    pressure_dist = 1.0
    if 200 <= t[i] <= 300:
        pressure_dist = 0.6 # 管网失压，流量锐减
        
    # ==========================================
    # 1. 单回路 PID (直接根据液位控制阀门开度)
    # ==========================================
    e_single = SP_level[i] - h_single[i-1]
    int_single += e_single * dt
    u_cmd_single = Kp_main * 5.0 * e_single + Ki_main * 5.0 * int_single # 放大增益以匹配单回路
    u_cmd_single = np.clip(u_cmd_single, 0, 100)
    
    # 阀门动态
    du_single = (u_cmd_single - u_single[i-1]) / tau_valve * dt
    u_single[i] = u_single[i-1] + du_single
    
    # 实际进水流量 (带管网压力扰动)
    q_in_single[i] = nonlinear_valve_flow(u_single[i]) * pressure_dist
    
    # 水箱液位动态 dh/dt = (Qin - Qout)/A
    q_out_single = C_valve * np.sqrt(h_single[i-1])
    dh_single = (q_in_single[i] - q_out_single) / A_tank * dt
    h_single[i] = max(0, h_single[i-1] + dh_single)

    # ==========================================
    # 2. 串级控制 (Cascade PID)
    # ==========================================
    # 主回路 (计算目标进水流量 SP_flow)
    e_main = SP_level[i] - h_cascade[i-1]
    int_main += e_main * dt
    SP_flow = Kp_main * e_main + Ki_main * int_main
    SP_flow = np.clip(SP_flow, 0, 3.0) # 限制最大请求流量
    
    # 副回路 (根据目标流量控制阀门开度)
    # 假设有流量计可以测到实际流量 q_in_cascade[i-1]
    e_sub = SP_flow - q_in_cascade[i-1]
    int_sub += e_sub * dt
    u_cmd_cascade = Kp_sub * e_sub + Ki_sub * int_sub
    u_cmd_cascade = np.clip(u_cmd_cascade, 0, 100)
    
    # 阀门动态
    du_cascade = (u_cmd_cascade - u_cascade[i-1]) / tau_valve * dt
    u_cascade[i] = u_cascade[i-1] + du_cascade
    
    # 实际进水流量 (带管网压力扰动)
    q_in_cascade[i] = nonlinear_valve_flow(u_cascade[i]) * pressure_dist
    
    # 水箱液位动态
    q_out_cascade = C_valve * np.sqrt(h_cascade[i-1])
    dh_cascade = (q_in_cascade[i] - q_out_cascade) / A_tank * dt
    h_cascade[i] = max(0, h_cascade[i-1] + dh_cascade)

# 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(t, h_single, 'r--', linewidth=2, label='Single Loop PID')
ax1.plot(t, h_cascade, 'b-', linewidth=3, label='Cascade Control')
ax1.axhline(5.0, color='k', linestyle=':', label='Level Setpoint')
ax1.axvspan(200, 300, color='gray', alpha=0.2, label='Network Pressure Drop')
ax1.set_ylabel('Tank Level (m)', fontsize=12)
ax1.set_title('Level Response Comparison: Single Loop vs Cascade', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='lower right')

ax2.plot(t, q_in_single, 'r--', linewidth=1.5, label='Inflow Q (Single)')
ax2.plot(t, q_in_cascade, 'b-', linewidth=2, label='Inflow Q (Cascade)')
ax2.set_xlabel('Time (s)', fontsize=12)
ax2.set_ylabel('Inflow Rate $m^3/s$', fontsize=12)
ax2.set_title('Inner Loop Disturbance Rejection', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='lower right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cascade_control_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
time_points = [50, 150, 210, 250, 350]

for tp in time_points:
    idx = int(tp / dt)
    history.append({
        'Time (s)': tp,
        'Event/Phase': 'Startup' if tp < 100 else ('Steady' if tp < 200 else ('Disturbance' if tp < 300 else 'Recovery')),
        'Single PID Level (m)': round(h_single[idx], 3),
        'Cascade Level (m)': round(h_cascade[idx], 3),
        'Single Inflow (m³/s)': round(q_in_single[idx], 3),
        'Cascade Inflow (m³/s)': round(q_in_cascade[idx], 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "cascade_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
