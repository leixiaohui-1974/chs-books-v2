import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\ecohydraulics\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 梯级水库生态流态调度优化 (Cascaded Reservoirs Ecological Dispatch Optimization)
# 场景：两个串联的梯级水库。
# 目标：满足下游人类的总耗水需求，同时使得释放到河道中的流量尽可能模拟天然流量的“季节性脉冲” (Ecological Flow Regime)。

# 全年 12 个月
months = np.arange(1, 13)

# 1. 目标天然流量脉冲 (Natural Flow Regime) - 双峰型河流 (春汛+夏汛)
# 鱼类依赖这种特定的流量脉冲来触发产卵
natural_regime = np.array([20, 25, 45, 90, 70, 60, 110, 130, 80, 50, 30, 20])

# 2. 水库参数与初始条件
V1_max = 500.0; V1_min = 100.0
V2_max = 300.0; V2_min = 50.0

V1_init = 300.0
V2_init = 200.0

# 逐月天然来水 (Inflow to Reservoir 1)
inflow_1 = np.array([15, 20, 50, 100, 80, 70, 120, 140, 90, 60, 35, 25])
# 水库1到水库2之间的区间天然来水
inflow_2 = np.array([5, 5, 10, 20, 15, 15, 30, 30, 20, 10, 5, 5])

# 人类用水刚性需求 (每月必须从水库2提取的农业/工业水量)
human_demand = np.array([10, 15, 40, 60, 80, 70, 50, 40, 30, 20, 15, 10])

# --- 优化模型 ---
# 决策变量：水库1的下泄量 R1[12]，水库2的下泄量 R2[12] (释放到下游天然河道的水)
# 共 24 个决策变量

def objective_function(vars):
    R1 = vars[0:12]
    R2 = vars[12:24]
    
    cost = 0.0
    V1 = V1_init
    V2 = V2_init
    
    for t in range(12):
        # 水量平衡
        V1_next = V1 + inflow_1[t] - R1[t]
        # 水库2的入水 = 水库1的下泄 + 区间来水
        V2_next = V2 + R1[t] + inflow_2[t] - R2[t] - human_demand[t]
        
        # 惩罚违反水库物理容量约束 (死水位和防洪高水位)
        if V1_next < V1_min: cost += 1e5 * (V1_min - V1_next)**2
        if V1_next > V1_max: cost += 1e5 * (V1_next - V1_max)**2
        if V2_next < V2_min: cost += 1e5 * (V2_min - V2_next)**2
        if V2_next > V2_max: cost += 1e5 * (V2_next - V2_max)**2
        
        # 目标 1: 强烈逼迫水库2的下泄流量 R2(t) 贴合大自然的天然流量脉冲 natural_regime
        # (生态修复的核心)
        cost += 10.0 * (R2[t] - natural_regime[t])**2
        
        # 目标 2: 平滑水库1的下泄，避免内部渠道剧烈波动
        if t > 0:
            cost += 1.0 * (R1[t] - R1[t-1])**2
            
        V1 = V1_next
        V2 = V2_next
        
    # 年末水位回归惩罚 (保证可持续性)
    cost += 100.0 * (V1 - V1_init)**2
    cost += 100.0 * (V2 - V2_init)**2
    
    return cost

# 初始猜测 (平分)
initial_guess = np.concatenate((inflow_1, natural_regime))

# 流量非负约束
bounds = [(0, 300) for _ in range(24)]

res = minimize(objective_function, initial_guess, bounds=bounds, method='L-BFGS-B')

# --- 提取最优解 ---
R1_opt = res.x[0:12]
R2_opt = res.x[12:24]

# 计算对比：如果是“自私发电/供水调度”(完全抹平生态脉冲，只为了稳定供水)
R2_selfish = np.ones(12) * (np.sum(inflow_1) + np.sum(inflow_2) - np.sum(human_demand)) / 12.0

# 计算最优状态下的水库库容变化
V1_opt_traj = [V1_init]
V2_opt_traj = [V2_init]
for t in range(12):
    V1_next = V1_opt_traj[-1] + inflow_1[t] - R1_opt[t]
    V2_next = V2_opt_traj[-1] + R1_opt[t] + inflow_2[t] - R2_opt[t] - human_demand[t]
    V1_opt_traj.append(V1_next)
    V2_opt_traj.append(V2_next)

# --- 绘图 ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 流量脉冲恢复图
ax1.plot(months, natural_regime, 'g--', linewidth=3, label='Target Natural Flow Regime (Eco-Pulse)')
ax1.plot(months, R2_selfish, 'r:', linewidth=2, label='Selfish Dispatch (Constant Flow - Ecological Death)')
ax1.plot(months, R2_opt, 'b-', linewidth=3, label='Optimized Eco-Dispatch (Reservoir 2 Release)')

# 标注生态春汛和夏汛
ax1.axvspan(3.5, 4.5, color='green', alpha=0.2, label='Spring Spawning Pulse')
ax1.axvspan(6.5, 8.5, color='blue', alpha=0.2, label='Summer Flood Pulse')

ax1.set_ylabel('Flow Rate ($m^3/s$)', fontsize=12)
ax1.set_title('Re-establishing the Natural Flow Regime via Optimization', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='upper right')

# 水库库容“代偿”图
ax2.plot(months, V1_opt_traj[:-1], 'c-', marker='o', linewidth=2, label='Reservoir 1 Volume')
ax2.plot(months, V2_opt_traj[:-1], 'm-', marker='s', linewidth=2, label='Reservoir 2 Volume')
ax2.plot(months, human_demand, 'k-.', linewidth=2, label='Human Rigid Demand (Extraction)')

ax2.set_xlabel('Month', fontsize=12)
ax2.set_ylabel('Reservoir Storage Volume', fontsize=12)
ax2.set_title('Reservoirs Act as "Buffers" to Absorb Human Demand', fontsize=14)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "flow_regime_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [1, 4, 5, 8, 11] # 挑几个代表性月份

for m in snapshots:
    idx = m - 1
    eco_error = abs(R2_opt[idx] - natural_regime[idx]) / natural_regime[idx] * 100
    selfish_error = abs(R2_selfish[idx] - natural_regime[idx]) / natural_regime[idx] * 100
    
    history.append({
        'Month': m,
        'Target Natural Pulse (m³/s)': round(natural_regime[idx], 1),
        'Selfish Dispatch (m³/s)': round(R2_selfish[idx], 1),
        'Optimized Eco-Release (m³/s)': round(R2_opt[idx], 1),
        'Human Demand (m³/s)': human_demand[idx],
        'Eco-Fidelity (Error %)': f"{eco_error:.1f}%"
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "eco_dispatch_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
