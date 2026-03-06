import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\canal-pipeline-control\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 动态矩阵控制 (Dynamic Matrix Control, DMC) 仿真
# 针对渠道流量控制的纯滞后和非参数化阶跃响应模型

# 系统物理参数 (FOPDT 模型表示)
K_sys = 1.5
T_sys = 20.0
L_delay = 10 # 延迟10个采样周期
dt = 1.0

# 1. 获取系统的阶跃响应模型 (Step Response Model, SRM)
N_horizon = 60 # 建模时域
step_response = np.zeros(N_horizon)
for i in range(N_horizon):
    t = i * dt
    if i >= L_delay:
        step_response[i] = K_sys * (1 - np.exp(-(t - L_delay * dt) / T_sys))

# 动态矩阵 A 的构建 (Dynamic Matrix)
P = 30 # 预测时域 (Prediction Horizon)
M = 5  # 控制时域 (Control Horizon)
A_matrix = np.zeros((P, M))
for i in range(P):
    for j in range(M):
        if i >= j:
            idx = i - j
            if idx < N_horizon:
                A_matrix[i, j] = step_response[idx]
            else:
                A_matrix[i, j] = step_response[-1] # 保持稳态值

# 2. DMC 控制器参数
Q = np.eye(P) * 1.0     # 误差惩罚权重
R = np.eye(M) * 5.0     # 控制增量惩罚权重 (抑制剧烈动作)

# 计算反馈控制律矩阵: K_dmc = (A^T Q A + R)^(-1) A^T Q
K_dmc = np.linalg.inv(A_matrix.T @ Q @ A_matrix + R) @ A_matrix.T
# 实际上我们只需要 K_dmc 的第一行来算当前的 \Delta u
k_row = K_dmc[0, :]

# 3. 仿真过程
N_sim = 150
y = np.zeros(N_sim) # 真实系统输出
u = np.zeros(N_sim) # 控制输入
sp = np.zeros(N_sim) # 设定值
sp[20:100] = 5.0
sp[100:] = 2.0

# 记录无 DMC 的常规 PI 比较
y_pi = np.zeros(N_sim)
u_pi = np.zeros(N_sim)

# DMC 状态变量
# 预测向量 N_horizon 维度
y_pred_free = np.zeros(N_horizon)
# 预测误差修正系数
h_corr = np.ones(N_horizon) # 简化：全向量平移修正

int_pi = 0.0

for k in range(1, N_sim):
    # ---------------- DMC ----------------
    # 1. 测量当前实际输出
    y_actual = y[k-1]
    
    # 2. 反馈校正 (Feedback Correction)
    # 计算实际值与预测值的误差
    err_meas = y_actual - y_pred_free[0]
    # 更新未来的自由响应
    y_pred_free = y_pred_free + h_corr * err_meas
    
    # 3. 优化计算 (Optimization)
    # 获取未来 P 步的设定值轨迹
    sp_traj = np.ones(P) * sp[k] if k < N_sim - P else np.ones(P) * sp[-1]
    
    # 计算误差向量 E = SP - Y_free
    E_vec = sp_traj - y_pred_free[:P]
    
    # 计算当前控制增量
    du = np.dot(k_row, E_vec)
    
    # 限幅处理
    u[k] = u[k-1] + du
    u[k] = np.clip(u[k], 0, 10.0)
    # 重新计算实际执行的 du (因为限幅了)
    du_actual = u[k] - u[k-1]
    
    # 4. 预测未来 (Prediction for next step)
    # 自由响应移位 (移出过去的时间步)
    for i in range(N_horizon - 1):
        y_pred_free[i] = y_pred_free[i+1]
    y_pred_free[-1] = y_pred_free[-2] # 最后一步保持
    
    # 叠加由于当前动作产生的强制响应
    for i in range(N_horizon):
        a_val = step_response[i]
        y_pred_free[i] += a_val * du_actual
        
    # 真实系统演进 (FOPDT)
    idx_delay = k - L_delay
    u_eff = u[idx_delay] if idx_delay >= 0 else 0.0
    y[k] = y[k-1] + (dt / T_sys) * (K_sys * u_eff - y[k-1])
    
    # ---------------- 传统 PI 比较 ----------------
    e_pi = sp[k] - y_pi[k-1]
    int_pi += e_pi * dt
    u_pi[k] = np.clip(0.5 * e_pi + 0.02 * int_pi, 0, 10.0)
    
    idx_delay_pi = k - L_delay
    u_eff_pi = u_pi[idx_delay_pi] if idx_delay_pi >= 0 else 0.0
    y_pi[k] = y_pi[k-1] + (dt / T_sys) * (K_sys * u_eff_pi - y_pi[k-1])

# 绘图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(np.arange(N_sim), sp, 'k:', linewidth=2, label='Target Flow SP')
ax1.plot(np.arange(N_sim), y_pi, 'r--', linewidth=2, label=f'Traditional PI Control (Delay={L_delay}s)')
ax1.plot(np.arange(N_sim), y, 'b-', linewidth=3, label='Dynamic Matrix Control (DMC)')
ax1.set_ylabel('Canal Flow Rate (m³/s)', fontsize=12)
ax1.set_title('Data-Driven Predictive Control: DMC vs PI', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='lower right')

ax2.plot(np.arange(N_sim), u_pi, 'r--', linewidth=1.5, label='Valve Cmd (PI)')
ax2.plot(np.arange(N_sim), u, 'b-', linewidth=2, label='Valve Cmd (DMC)')
ax2.set_xlabel('Time Steps', fontsize=12)
ax2.set_ylabel('Valve Cmd (0-10)', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "dmc_control_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [25, 45, 80, 105, 125]

for idx in snapshots:
    history.append({
        'Time Step': idx,
        'Setpoint': sp[idx],
        'PI Flow Response': round(y_pi[idx], 2),
        'DMC Flow Response': round(y[idx], 2),
        'PI Valve Cmd': round(u_pi[idx], 2),
        'DMC Valve Cmd': round(u[idx], 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "dmc_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
