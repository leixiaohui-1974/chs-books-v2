import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\water-system-control\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 灰盒建模与系统辨识 (Gray-Box Modeling & System Identification)
# 模拟一阶惯性加纯滞后系统 (FOPDT: First-Order Plus Dead Time) 的参数辨识

# 1. 生成带有高斯噪声的真实工厂数据 (Plant Data)
# 真实的隐藏物理参数
K_true = 2.5       # 静态增益 (Gain)
T_true = 15.0      # 时间常数 (Time Constant) s
L_true = 8.0       # 纯滞后时间 (Dead Time) s

dt = 0.5
time = np.arange(0, 100, dt)
N = len(time)

# 阶跃输入信号 (在 t=10s 时阀门从 0 变到 10%)
u_step = np.zeros(N)
step_time = 10.0
u_step[time >= step_time] = 10.0

# 真实系统的响应求解 (解析解)
y_true = np.zeros(N)
for i, t in enumerate(time):
    if t >= step_time + L_true:
        y_true[i] = K_true * 10.0 * (1 - np.exp(-(t - step_time - L_true) / T_true))

# 加上测量噪声 (模拟真实的液位雷达波动)
np.random.seed(42)
noise = np.random.normal(0, 0.5, N)
y_measured = y_true + noise

# 2. 灰盒系统辨识优化算法
# 定义 FOPDT 模型的预测函数
def fopdt_model(params, t_array, u_array, t_step):
    K, Tau, L = params
    y_pred = np.zeros(len(t_array))
    for i, t in enumerate(t_array):
        if t >= t_step + L:
            y_pred[i] = K * 10.0 * (1 - np.exp(-(t - t_step - L) / max(Tau, 0.1))) # 防止除以0
    return y_pred

# 定义损失函数 (最小化预测值与测量值的残差平方和 SSE)
def objective_function(params):
    K, Tau, L = params
    
    # 物理硬约束 (参数不能为负)
    if K <= 0 or Tau <= 0 or L <= 0:
        return 1e9
        
    y_pred = fopdt_model(params, time, u_step, step_time)
    sse = np.sum((y_measured - y_pred)**2)
    return sse

# 初始猜测值 (比如随便猜一个)
initial_guess = [1.0, 5.0, 2.0]

# 调用 scipy 优化器寻找最优参数
# 使用 Nelder-Mead 寻找全局近似最优，或使用 BFGS
result = minimize(objective_function, initial_guess, method='Nelder-Mead', options={'maxiter': 2000})

K_opt, T_opt, L_opt = result.x
y_optimized = fopdt_model(result.x, time, u_step, step_time)

# 3. 生成辨识结果对比图
plt.figure(figsize=(10, 8))

# 子图1：阶跃输入
plt.subplot(2, 1, 1)
plt.plot(time, u_step, 'k-', linewidth=2, label='Valve Step Input u(t)')
plt.ylabel('Valve Command (%)', fontsize=12)
plt.title('System Identification: Step Response Experiment', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# 子图2：系统响应与辨识模型拟合
plt.subplot(2, 1, 2)
plt.scatter(time, y_measured, color='gray', s=10, alpha=0.5, label='Noisy Plant Measurements (SCADA Data)')
plt.plot(time, y_true, 'g--', linewidth=2, label=f'True Hidden Dynamics (K={K_true}, T={T_true}, L={L_true})')
plt.plot(time, y_optimized, 'b-', linewidth=3, label=f'Identified Gray-Box Model (K={K_opt:.2f}, T={T_opt:.2f}, L={L_opt:.2f})')

plt.xlabel('Time (s)', fontsize=12)
plt.ylabel('Process Variable y(t)', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "system_id_sim.png"), dpi=300, bbox_inches='tight')

# 4. 生成参数辨识对比矩阵
history = [
    {'Parameter': 'Static Gain K (m/%)', 'True Value': K_true, 'Identified Value': round(K_opt, 3), 'Error %': round(abs(K_opt-K_true)/K_true*100, 2)},
    {'Parameter': 'Time Constant T (s)', 'True Value': T_true, 'Identified Value': round(T_opt, 3), 'Error %': round(abs(T_opt-T_true)/T_true*100, 2)},
    {'Parameter': 'Dead Time L (s)', 'True Value': L_true, 'Identified Value': round(L_opt, 3), 'Error %': round(abs(L_opt-L_true)/L_true*100, 2)}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "sysid_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
