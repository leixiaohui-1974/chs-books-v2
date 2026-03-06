import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.integrate import odeint

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\canal-pipeline-control\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 渠道水位 PID 控制仿真
# 建立一维明渠的集总参数(Lumped Parameter)近似模型: 水量平衡方程
# dh/dt = (Qin - Qout) / A_surface
# 考虑长明渠的死区时间 (Dead Time) L_delay = 10s

# 系统参数
A_surface = 50.0  # 渠道等效表面积 m^2
L_delay = 10.0    # 渠道传输的物理死区 s
C_out = 2.0       # 下游闸门出流系数

dt = 0.5
t = np.arange(0, 150, dt)
N = len(t)

# 目标设定值
sp = np.ones(N) * 2.0  # 目标水位 2.0m

# 记录变量
h_actual = np.zeros(N)
u_valve = np.zeros(N)   # 上游进水阀门指令
q_in_delayed = np.zeros(N)

# 初始化状态
h_actual[0] = 0.5 # 初始水位较低
u_valve[0] = C_out * np.sqrt(0.5) # 稳态进水

# PID 控制器参数 (基于带死区的一阶系统整定)
Kp = 8.0
Ki = 0.5
Kd = 2.0
int_e = 0.0
prev_e = sp[0] - h_actual[0]

# --- 模拟控制过程 ---
for i in range(1, N):
    # 1. 传感器获取水位并计算误差
    e = sp[i] - h_actual[i-1]
    
    # 2. PID 计算 (抗积分饱和)
    int_e += e * dt
    de = (e - prev_e) / dt
    u_cmd = Kp * e + Ki * int_e + Kd * de
    
    # 物理阀门限幅 0~10 m3/s
    if u_cmd > 10.0:
        u_cmd = 10.0
        if e > 0: int_e -= e * dt # Anti-windup
    elif u_cmd < 0.0:
        u_cmd = 0.0
        if e < 0: int_e -= e * dt # Anti-windup
        
    u_valve[i] = u_cmd
    prev_e = e
    
    # 3. 水流在渠道中传输 (引入纯滞后死区)
    idx_delayed = i - int(L_delay / dt)
    q_in = u_valve[idx_delayed] if idx_delayed >= 0 else u_valve[0]
    q_in_delayed[i] = q_in
    
    # 4. 渠道物理演进: dh/dt = (Qin - Qout)/A
    q_out = C_out * np.sqrt(max(h_actual[i-1], 0))
    dh = (q_in - q_out) / A_surface * dt
    h_actual[i] = h_actual[i-1] + dh

# 绘图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(t, sp, 'k:', linewidth=2, label='Target Water Level (SP)')
ax1.plot(t, h_actual, 'b-', linewidth=3, label='Actual Water Level (PV)')
ax1.set_ylabel('Water Level $h$ (m)', fontsize=12)
ax1.set_title(f'Single Canal Reach PID Level Control (Delay = {L_delay}s)', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend()

ax2.plot(t, u_valve, 'r--', linewidth=2, label='Upstream Valve Cmd $u(t)$')
ax2.plot(t, q_in_delayed, 'g-', linewidth=2, label='Delayed Inflow at Downstream $Q_{in}(t-L)$')
ax2.set_xlabel('Time (s)', fontsize=12)
ax2.set_ylabel('Flow Rate ($m^3/s$)', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend()

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "canal_pid_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [10, 30, 60, 100, 140]

for t_val in snapshots:
    idx = int(t_val / dt)
    history.append({
        'Time (s)': t_val,
        'Setpoint (m)': sp[idx],
        'Actual Level (m)': round(h_actual[idx], 3),
        'Valve Cmd (m³/s)': round(u_valve[idx], 3),
        'Delayed Inflow (m³/s)': round(q_in_delayed[idx], 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "canal_pid_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
