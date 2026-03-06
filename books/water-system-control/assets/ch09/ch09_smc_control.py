import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\water-system-control\assets\ch09"
os.makedirs(output_dir, exist_ok=True)

# 滑模控制 (Sliding Mode Control, SMC) 仿真
# 针对存在剧烈参数不确定性和外部干扰的混合池水位控制系统
# 状态方程: dx/dt = f(x) + g(x)u + d(t)

# 系统参数 (标称值)
A_nom = 2.0
C_nom = 0.5
dt = 0.05
t = np.arange(0, 50, dt)
N = len(t)

# 真实系统参数 (包含巨大的不确定性)
A_true = 2.0  # 面积不变
# 阀门老化，出水阻力变小，真实流量系数比标称大很多，且随时间漂移
C_true = 0.5 * (1 + 0.5 * np.sin(0.1 * t))

sp = np.ones(N) * 5.0 # 目标液位 5m

# 记录变量
x_smc = np.zeros(N)
u_smc = np.zeros(N)
s_smc = np.zeros(N) # 滑模面

x_pid = np.zeros(N)
u_pid = np.zeros(N)

x_smc[0] = 1.0
x_pid[0] = 1.0

# 外部不可测扰动 (在 t=25s 爆发的强烈入流扰动)
dist = np.zeros(N)
dist[int(25/dt):int(35/dt)] = 2.0

# PID 控制器参数 (基于标称模型整定)
Kp = 2.0
Ki = 0.5
int_pid = 0.0

# 滑模控制器参数
# 定义滑模面: s = c*e + de/dt (由于这是一阶系统，定义为 s = e)
# 控制律: u = u_eq + u_sw
# 等效控制 (Equivalent Control): 消除已知动态
# 切换控制 (Switching Control): 克服不确定性界限 u_sw = K_sw * sign(s)
c_slide = 1.0
K_sw = 3.0 # 鲁棒增益，必须大于系统不确定性的上界

for i in range(1, N):
    # ---------------- PID Control ----------------
    e_pid = sp[i] - x_pid[i-1]
    int_pid += e_pid * dt
    u_pid[i] = Kp * e_pid + Ki * int_pid
    # 物理限幅
    u_pid[i] = np.clip(u_pid[i], 0, 10)
    
    # 真实系统演进 (带有参数漂移 C_true 和未测扰动 dist)
    q_out_pid = C_true[i-1] * np.sqrt(max(x_pid[i-1], 0))
    dx_pid = (u_pid[i] - q_out_pid + dist[i-1]) / A_true
    x_pid[i] = x_pid[i-1] + dx_pid * dt
    
    # ---------------- SMC Control ----------------
    e_smc = sp[i] - x_smc[i-1]
    # 滑模面 s = e (对于一阶系统)
    s = e_smc
    s_smc[i] = s
    
    # 基于标称模型的等效控制 (抵消已知动态使得 ds/dt = 0)
    # dx/dt = (u - C_nom*sqrt(x))/A_nom
    # ds/dt = d(sp - x)/dt = -dx/dt = -(u - C_nom*sqrt(x))/A_nom = 0
    # u_eq = C_nom * sqrt(x)
    u_eq = C_nom * np.sqrt(max(x_smc[i-1], 0))
    
    # 切换控制 (打倒一切扰动和不确定性)
    # 为了避免高频抖振(Chattering)，使用饱和函数 sat(s/phi) 替代 sign(s)
    phi = 0.1 # 边界层厚度
    if abs(s) > phi:
        u_sw = K_sw * np.sign(s)
    else:
        u_sw = K_sw * (s / phi)
        
    u_smc[i] = u_eq + u_sw
    u_smc[i] = np.clip(u_smc[i], 0, 10)
    
    # 真实系统演进
    q_out_smc = C_true[i-1] * np.sqrt(max(x_smc[i-1], 0))
    dx_smc = (u_smc[i] - q_out_smc + dist[i-1]) / A_true
    x_smc[i] = x_smc[i-1] + dx_smc * dt

# 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

ax1.plot(t, sp, 'k:', linewidth=2, label='Target Setpoint')
ax1.plot(t, x_pid, 'r--', linewidth=2, label='PID Control')
ax1.plot(t, x_smc, 'b-', linewidth=3, label='Sliding Mode Control (SMC)')
ax1.axvspan(25, 35, color='gray', alpha=0.2, label='Massive Unmeasured Disturbance')
ax1.set_ylabel('Water Level (m)', fontsize=12)
ax1.set_title('Robustness Test: Severe Parameter Drift and Disturbance', fontsize=14)
ax1.legend(loc='lower right')
ax1.grid(True, linestyle='--', alpha=0.6)

ax2.plot(t, u_pid, 'r--', linewidth=1.5, label='Valve Cmd (PID)')
ax2.plot(t, u_smc, 'b-', linewidth=1.5, label='Valve Cmd (SMC)')
ax2.set_ylabel('Valve Cmd (u)', fontsize=12)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

ax3.plot(t, s_smc, 'g-', linewidth=2, label='Sliding Surface $s(t)$')
ax3.fill_between(t, -phi, phi, color='green', alpha=0.1, label='Boundary Layer $\Phi$')
ax3.set_xlabel('Time (s)', fontsize=12)
ax3.set_ylabel('Sliding Surface Value', fontsize=12)
ax3.legend(loc='upper right')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "smc_robustness_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [10, 20, 30, 40]

for t_val in snapshots:
    idx = int(t_val / dt)
    history.append({
        'Time (s)': t_val,
        'Event/Phase': 'Startup' if t_val < 25 else ('Disturbance' if t_val < 35 else 'Recovery'),
        'True Outflow Coeff (Drifting)': round(C_true[idx], 3),
        'PI Level (m)': round(x_pid[idx], 3),
        'SMC Level (m)': round(x_smc[idx], 3),
        'SMC Sliding Surface s': round(s_smc[idx], 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "smc_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
