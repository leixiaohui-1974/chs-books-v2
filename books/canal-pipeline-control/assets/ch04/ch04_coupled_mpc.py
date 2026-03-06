import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\canal-pipeline-control\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 渠道与泵站联合调度仿真 (MPC vs PID)
# 场景：具有水波传播迟滞的明渠，其末端直接连接一个恒压供水泵站。
# 目标：当泵站因为城市用水激增而突然大幅提升抽水量时，
#       上游渠道阀门必须及时开大，保证泵站前池水位不跌破最低安全线(防吸空)，同时不漫堤。

# 物理参数
L_delay = 8     # 渠道水流从源头到前池的延迟周期
A_forebay = 30.0 # 前池等效面积 m^2
C_in = 1.0       # 阀门流量系数
dt = 1.0
N_sim = 150

# 设定值与安全边界
sp_level = 3.0    # 目标水位 m
min_safe_level = 1.0 # 泵站安全吸水最低水位

# 扰动：城市用水量 (泵站抽水量)
demand = np.ones(N_sim) * 1.5
demand[30:100] = 5.0 # 突然的用水早高峰

# 1. 传统 PID 控制器仿真 (单回路)
y_pid = np.zeros(N_sim)
u_pid = np.zeros(N_sim)
y_pid[0] = sp_level
u_pid[0] = 1.5 # 稳态

Kp = 5.0
Ki = 0.5
int_err = 0.0

for k in range(1, N_sim):
    err = sp_level - y_pid[k-1]
    int_err += err * dt
    cmd = Kp * err + Ki * int_err
    u_pid[k] = np.clip(cmd, 0, 10.0) # 阀门开度限幅 0~10 m3/s
    
    # 物理演进
    idx_delay = k - L_delay
    q_in = u_pid[idx_delay] if idx_delay >= 0 else u_pid[0]
    q_out = demand[k-1]
    y_pid[k] = y_pid[k-1] + (q_in - q_out) / A_forebay * dt

# 2. 预测控制 (MPC) 仿真
# 由于是前池积分模型: y[k] = y[k-1] + (u[k-1-L] - d[k-1])/A
# MPC 知道未来的 demand 变化 (这在智慧水务中可以通过AI负荷预测得到)
P = 20
M = 5
Q_err = 10.0
R_du = 1.0
u_max = 10.0
u_min = 0.0
du_max = 1.5 # 动作速率限制

y_mpc = np.zeros(N_sim)
u_mpc = np.zeros(N_sim)
y_mpc[0] = sp_level
u_mpc[0] = 1.5

def mpc_cost(du_future, curr_y, past_u, pred_demand, current_k):
    cost = 0
    y_pred = curr_y
    u_hist = list(past_u)
    u_curr = u_hist[-1]
    
    for i in range(P):
        if i < M:
            u_curr += du_future[i]
            # 软约束
            if u_curr > u_max: cost += 1e6 * (u_curr - u_max)**2
            if u_curr < u_min: cost += 1e6 * (u_min - u_curr)**2
        
        u_hist.append(u_curr)
        u_eff = u_hist[-(L_delay+1)]
        d_val = pred_demand[i]
        
        y_pred = y_pred + (u_eff - d_val) / A_forebay * dt
        
        # 极度惩罚跌破安全水位的行为 (防吸空)
        if y_pred < min_safe_level:
            cost += 1e6 * (min_safe_level - y_pred)**2
            
        cost += Q_err * (y_pred - sp_level)**2
        if i < M:
            cost += R_du * du_future[i]**2
            
    return cost

for k in range(1, N_sim - P):
    # 如果还没有足够的历史数据，保持初始状态
    if k <= L_delay:
        past_u = [u_mpc[0]] * (L_delay + 1)
    else:
        past_u = u_mpc[k-L_delay-1:k]
        
    pred_demand = demand[k:k+P]
    du_guess = np.zeros(M)
    bounds = [(-du_max, du_max) for _ in range(M)]
    
    res = minimize(mpc_cost, du_guess, args=(y_mpc[k-1], past_u, pred_demand, k), bounds=bounds, method='L-BFGS-B')
    
    du_opt = res.x[0]
    u_mpc[k] = np.clip(u_mpc[k-1] + du_opt, u_min, u_max)
    
    idx_delay = k - L_delay
    q_in = u_mpc[idx_delay] if idx_delay >= 0 else u_mpc[0]
    q_out = demand[k-1]
    y_mpc[k] = y_mpc[k-1] + (q_in - q_out) / A_forebay * dt

# 补齐尾部
y_mpc[N_sim-P:] = y_mpc[N_sim-P-1]
u_mpc[N_sim-P:] = u_mpc[N_sim-P-1]

# 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

t_plot = np.arange(N_sim-P)

ax1.plot(t_plot, np.ones(len(t_plot))*sp_level, 'k:', linewidth=2, label='Target Level')
ax1.plot(t_plot, np.ones(len(t_plot))*min_safe_level, 'm-.', linewidth=2, label='Minimum Safe Level (Pump Cavitation)')
ax1.plot(t_plot, y_pid[:N_sim-P], 'r--', linewidth=2, label='PID Control (Reactive)')
ax1.plot(t_plot, y_mpc[:N_sim-P], 'b-', linewidth=3, label='MPC (Proactive)')
ax1.axvspan(30, 100, color='gray', alpha=0.2, label='High Demand Disturbance')
ax1.set_ylabel('Forebay Level (m)', fontsize=12)
ax1.set_title('Canal-Pump Coupled Operation: Preventing Pump Cavitation', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注危急时刻
min_pid_val = np.min(y_pid[:N_sim-P])
min_pid_idx = np.argmin(y_pid[:N_sim-P])
if min_pid_val < min_safe_level:
    ax1.plot(min_pid_idx, min_pid_val, 'rX', markersize=10)
    ax1.annotate('PID Crash:\nPump Cavitation!', xy=(min_pid_idx, min_pid_val), xytext=(min_pid_idx+5, min_pid_val-0.5),
                 arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=6))

ax2.plot(t_plot, u_pid[:N_sim-P], 'r--', linewidth=1.5, label='Source Valve Cmd (PID)')
ax2.plot(t_plot, u_mpc[:N_sim-P], 'b-', linewidth=2, label='Source Valve Cmd (MPC)')
ax2.plot(t_plot, demand[:N_sim-P], 'k-.', linewidth=1.5, label='Pump Demand (Disturbance)')
ax2.set_xlabel('Time (s)', fontsize=12)
ax2.set_ylabel('Flow Rate ($m^3/s$)', fontsize=12)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# 标注 MPC 提前动作
ax2.annotate('MPC Pre-fills Canal\nBefore Demand Peak', xy=(22, 5.0), xytext=(5, 7.0),
             arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=6))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "coupled_mpc_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [20, 28, 38, 50, 110]

for idx in snapshots:
    history.append({
        'Time (s)': idx,
        'City Demand': demand[idx],
        'PID Level (m)': round(y_pid[idx], 2),
        'MPC Level (m)': round(y_mpc[idx], 2),
        'PID Valve': round(u_pid[idx], 2),
        'MPC Valve': round(u_mpc[idx], 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "coupled_mpc_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
