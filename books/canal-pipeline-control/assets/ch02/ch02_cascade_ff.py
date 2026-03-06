import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\canal-pipeline-control\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 串级控制与前馈补偿仿真 (Cascade & Feedforward Control)
# 场景：多渠段梯级调水 (Multi-reach Canal System)
# 扰动：中间农田分水口突然大流量抽水

dt = 1.0
t = np.arange(0, 300, dt)
N = len(t)

# 物理系统参数 (两个渠段)
A1 = 50.0; L1_delay = 5.0
A2 = 40.0; L2_delay = 8.0
C_out1 = 1.5
C_out2 = 2.0

sp2 = np.ones(N) * 2.0 # 最终目标: 渠段2的水位保持 2.0m

# 记录变量 (传统单回路 PID 控制，只看渠段2水位来调渠首闸门)
h1_pid = np.zeros(N)
h2_pid = np.zeros(N)
u_valve_pid = np.zeros(N)
h1_pid[0] = 1.0
h2_pid[0] = 2.0
u_valve_pid[0] = C_out1 * np.sqrt(1.0) # 稳态

# 记录变量 (前馈-串级复合控制)
h1_cas = np.zeros(N)
h2_cas = np.zeros(N)
u_valve_cas = np.zeros(N)
sp1_cmd = np.zeros(N) # 渠段1的目标水位 (由外环决定)
h1_cas[0] = 1.0
h2_cas[0] = 2.0
u_valve_cas[0] = C_out1 * np.sqrt(1.0)

# 外部扰动: 在渠段1和渠段2之间有一个农田分水口
# t=50s 时，农田突然开始抽水 2.0 m3/s
dist_flow = np.zeros(N)
dist_flow[int(50/dt):int(150/dt)] = 2.0

# PID 1: 单回路 (极其迟钝)
Kp_single = 4.0; Ki_single = 0.2
int_e_single = 0.0

# PID 2: 串级外环 (控制 h2，输出 h1 的设定值)
Kp_outer = 1.5; Ki_outer = 0.1
int_e_outer = 0.0

# PID 3: 串级内环 (控制 h1，输出阀门指令)
Kp_inner = 8.0; Ki_inner = 0.5
int_e_inner = 0.0

# 仿真循环
for i in range(1, N):
    
    # ==========================================
    # 1. 单回路 PID (看 h2，动 u)
    # ==========================================
    e_single = sp2[i] - h2_pid[i-1]
    int_e_single += e_single * dt
    u_pid = Kp_single * e_single + Ki_single * int_e_single
    u_valve_pid[i] = np.clip(u_pid, 0, 15)
    
    # 渠段1物理
    idx_d1_pid = i - int(L1_delay/dt)
    q_in1_pid = u_valve_pid[idx_d1_pid] if idx_d1_pid >= 0 else u_valve_pid[0]
    q_out1_pid = C_out1 * np.sqrt(max(h1_pid[i-1], 0))
    h1_pid[i] = h1_pid[i-1] + (q_in1_pid - q_out1_pid - dist_flow[i-1]) / A1 * dt # 扰动在这里抽水
    
    # 渠段2物理
    idx_d2_pid = i - int(L2_delay/dt)
    # 渠段1的出水，经过L2延迟后进入渠段2
    # 实际上由于扰动，真实进入渠段2的水是 q_out1_pid
    # 为了简化死区模型，假定两段独立，中间节点有扰动
    q_in2_pid = q_out1_pid # (忽略中间物理距离，死区算在渠段内)
    q_in2_delayed_pid = q_in2_pid # 简化
    q_out2_pid = C_out2 * np.sqrt(max(h2_pid[i-1], 0))
    h2_pid[i] = h2_pid[i-1] + (q_in2_delayed_pid - q_out2_pid) / A2 * dt

    # ==========================================
    # 2. 串级+前馈 控制
    # ==========================================
    # 外环: 看 h2，决定 h1 的设定值
    e_outer = sp2[i] - h2_cas[i-1]
    int_e_outer += e_outer * dt
    sp1_cmd[i] = 1.0 + Kp_outer * e_outer + Ki_outer * int_e_outer
    sp1_cmd[i] = np.clip(sp1_cmd[i], 0.5, 3.0)
    
    # 内环: 看 h1，决定阀门。加入前馈补偿 (Feedforward)
    # 前馈：如果能测量到农田抽水 dist_flow，直接在阀门处加上这个量
    e_inner = sp1_cmd[i] - h1_cas[i-1]
    int_e_inner += e_inner * dt
    u_cas = Kp_inner * e_inner + Ki_inner * int_e_inner
    
    # 前馈抗扰加成
    ff_compensation = dist_flow[i-1] 
    u_valve_cas[i] = np.clip(u_cas + ff_compensation, 0, 15)
    
    # 渠段1物理
    idx_d1_cas = i - int(L1_delay/dt)
    q_in1_cas = u_valve_cas[idx_d1_cas] if idx_d1_cas >= 0 else u_valve_cas[0]
    q_out1_cas = C_out1 * np.sqrt(max(h1_cas[i-1], 0))
    h1_cas[i] = h1_cas[i-1] + (q_in1_cas - q_out1_cas - dist_flow[i-1]) / A1 * dt
    
    # 渠段2物理
    q_out2_cas = C_out2 * np.sqrt(max(h2_cas[i-1], 0))
    h2_cas[i] = h2_cas[i-1] + (q_out1_cas - q_out2_cas) / A2 * dt

# 绘图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(t, sp2, 'k:', linewidth=2, label='Target Downstream Level')
ax1.plot(t, h2_pid, 'r--', linewidth=2, label='Single PID (Level 2)')
ax1.plot(t, h2_cas, 'b-', linewidth=3, label='Cascade+FF (Level 2)')
ax1.axvspan(50, 150, color='gray', alpha=0.2, label='Mid-stream Disturbance (Farm Pumping)')
ax1.set_ylabel('End Level $h_2$ (m)', fontsize=12)
ax1.set_title('Disturbance Rejection: Single PID vs Cascade with Feedforward', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='lower right')

ax2.plot(t, u_valve_pid, 'r--', linewidth=2, label='Source Valve Cmd (Single)')
ax2.plot(t, u_valve_cas, 'b-', linewidth=2, label='Source Valve Cmd (Cascade+FF)')
ax2.set_xlabel('Time (s)', fontsize=12)
ax2.set_ylabel('Valve Cmd ($m^3/s$)', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cascade_ff_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [40, 60, 100, 160]

for t_val in snapshots:
    idx = int(t_val / dt)
    history.append({
        'Time (s)': t_val,
        'Disturbance': 'Off' if dist_flow[idx] == 0 else 'On (2.0 m³/s)',
        'Single PID Level (m)': round(h2_pid[idx], 3),
        'Cascade Level (m)': round(h2_cas[idx], 3),
        'Single Valve': round(u_valve_pid[idx], 2),
        'Cascade Valve': round(u_valve_cas[idx], 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "cascade_ff_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
