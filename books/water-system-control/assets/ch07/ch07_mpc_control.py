import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\water-system-control\assets\ch07"
os.makedirs(output_dir, exist_ok=True)

# 模型预测控制 (Model Predictive Control, MPC) 仿真
# 场景：带约束的长距离引水渠末端水位控制
# 渠道具有大迟滞 (Dead Time)，且阀门动作有速度限制 (Rate Constraint)

# 离散时间 FOPDT 模型 (First-Order Plus Dead Time)
# G(s) = K / (T*s + 1) * e^(-L*s)
K = 1.2
T = 10.0
L = 4     # 滞后 4 个采样周期
dt = 1.0

# 状态空间离散化近似 (包含迟滞状态)
# 为简化实现，直接使用差分方程计算预测输出
# y[k] = a*y[k-1] + b*u[k-1-L]
a = np.exp(-dt/T)
b = K * (1 - a)

# MPC 参数
P = 20    # 预测步长 (Prediction Horizon)
M = 5     # 控制步长 (Control Horizon)
Q = 1.0   # 误差惩罚权重
R = 0.5   # 控制增量惩罚权重 (抑制阀门抖动)
du_max = 2.0  # 阀门动作速率约束 (每步最多变 2%)
u_max = 100.0 # 阀门上限
u_min = 0.0   # 阀门下限

# 模拟参数
N_sim = 150
y = np.zeros(N_sim)
u = np.zeros(N_sim)
sp = np.zeros(N_sim)
sp[20:80] = 10.0 # 目标设定值跳变
sp[80:] = 5.0

# 优化目标函数
def mpc_cost(du_future, current_y, past_u, current_sp_traj):
    # du_future 是长度为 M 的控制增量数组
    cost = 0
    y_pred = current_y
    u_hist = list(past_u) # 复制过去和未来的控制序列用于计算迟滞
    
    u_curr = u_hist[-1]
    
    for k in range(P):
        # 确定未来的控制指令
        if k < M:
            u_curr = u_curr + du_future[k]
            # 加上绝对幅值约束惩罚 (软约束处理)
            if u_curr > u_max: cost += 1e5 * (u_curr - u_max)**2
            if u_curr < u_min: cost += 1e5 * (u_min - u_curr)**2
        
        u_hist.append(u_curr)
        
        # 提取起作用的控制输入 (带纯滞后 L)
        u_delayed = u_hist[-(L + 2)] # 考虑离散系统的延迟索引
        
        # 预测下一步输出
        y_pred = a * y_pred + b * u_delayed
        
        # 累加误差代价
        cost += Q * (y_pred - current_sp_traj[k])**2
        
        # 累加控制增量代价
        if k < M:
            cost += R * du_future[k]**2
            
    return cost

# 模拟 MPC 闭环
for k in range(L+1, N_sim - P):
    # 获取当前的设定值轨迹 (假设未来 P 步设定值已知)
    sp_traj = sp[k:k+P]
    
    # 提取过去的控制历史 (用于迟滞系统预测)
    past_u = u[k-L-1:k]
    
    # 初始猜测 (全0增量)
    du_guess = np.zeros(M)
    
    # 速率约束
    bounds = [(-du_max, du_max) for _ in range(M)]
    
    # 求解二次规划 (这里使用 SLSQP 或 L-BFGS-B 处理非线性优化)
    res = minimize(mpc_cost, du_guess, args=(y[k-1], past_u, sp_traj), bounds=bounds, method='L-BFGS-B')
    
    # 执行第一步最优控制增量
    du_opt = res.x[0]
    u[k] = u[k-1] + du_opt
    
    # 强制物理限幅 (Clip)
    u[k] = np.clip(u[k], u_min, u_max)
    
    # 真实系统演进 (加入未建模的随机扰动)
    y[k] = a * y[k-1] + b * u[k-1-L]
    if k == 100: # 突发扰动
        y[k] += 3.0

# 为了对比，加入一个简单的 PI 控制器
y_pi = np.zeros(N_sim)
u_pi = np.zeros(N_sim)
int_err = 0

for k in range(L+1, N_sim - P):
    # PI logic
    err = sp[k] - y_pi[k-1]
    int_err += err * dt
    u_req = 1.5 * err + 0.1 * int_err
    
    # 强制物理约束
    du = u_req - u_pi[k-1]
    du = np.clip(du, -du_max, du_max) # 相同的速率约束
    
    u_pi[k] = np.clip(u_pi[k-1] + du, u_min, u_max)
    
    y_pi[k] = a * y_pi[k-1] + b * u_pi[k-1-L]
    if k == 100: y_pi[k] += 3.0

# 绘制结果图
t_plot = np.arange(0, N_sim - P)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(t_plot, sp[:len(t_plot)], 'k:', linewidth=2, label='Setpoint (SP)')
ax1.plot(t_plot, y_pi[L+1:N_sim-P+L+1], 'r--', linewidth=2, label='Traditional PI Control')
ax1.plot(t_plot, y[L+1:N_sim-P+L+1], 'b-', linewidth=3, label='Model Predictive Control (MPC)')
ax1.set_ylabel('Water Level / Quality (PV)', fontsize=12)
ax1.set_title(f'MPC vs PI: Handling Dead-Time ({L}s) and Constraints', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注 MPC 提前动作的时刻
ax1.annotate('MPC anticipates future SP change\nand acts before t=80', xy=(75, 7.5), xytext=(35, 6),
             arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=6))

ax2.plot(t_plot, u_pi[L+1:N_sim-P+L+1], 'r--', linewidth=1.5, label='PI Valve Cmd')
ax2.plot(t_plot, u[L+1:N_sim-P+L+1], 'b-', linewidth=2, label='MPC Valve Cmd')
ax2.set_xlabel('Time (s)', fontsize=12)
ax2.set_ylabel('Valve Cmd (%)', fontsize=12)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "mpc_control_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [25, 75, 85, 105, 120]

for idx in snapshots:
    real_idx = L+1 + idx
    history.append({
        'Time (s)': idx,
        'Setpoint': sp[idx],
        'PI Level': round(y_pi[real_idx], 2),
        'MPC Level': round(y[real_idx], 2),
        'PI Valve Cmd': round(u_pi[real_idx], 2),
        'MPC Valve Cmd': round(u[real_idx], 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "mpc_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
