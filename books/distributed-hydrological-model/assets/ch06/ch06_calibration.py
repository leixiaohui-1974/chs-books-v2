import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch06"
os.makedirs(output_dir, exist_ok=True)

# 分布式水文模型参数率定 (Model Calibration) - 简化 SCE-UA 思想
# 场景：利用历史实测流量，逆向推导新安江模型中无法直接测量的三个关键土壤参数
# 参数1: WM (流域平均蓄水容量) 真实值=120
# 参数2: B (蓄水容量分布指数) 真实值=0.2
# 参数3: KI (壤中流出流系数) 真实值=0.4

# 1. 制造“真实的”观测数据 (带有少量观测噪声)
# 生成 200 小时的降雨数据
np.random.seed(42)
N = 200
P_rain = np.zeros(N)
P_rain[10:30] = 5.0
P_rain[80:110] = 12.0
E_evap = np.ones(N) * 1.0

# 真实的隐蔽参数
WM_true = 120.0
B_true = 0.2
KI_true = 0.4
KG_true = 0.3 # 假设为固定已知值
SM_true = 20.0 # 假设为固定已知值

def run_forward_model(WM, B, KI):
    # 极简版 XAJ
    W_curr = 50.0
    S_free = 0.0
    Q_sim = np.zeros(N)
    
    WMM = WM * (1 + B)
    
    for i in range(N):
        PE = P_rain[i] - E_evap[i]
        
        # 产流
        if PE <= 0:
            R = 0
            W_curr = max(0, W_curr + PE)
        else:
            A = WMM * (1 - (1 - W_curr / WM)**(1 / (1 + B))) if W_curr < WM else WMM
            if A + PE >= WMM:
                R = PE - (WM - W_curr)
                W_curr = WM
            else:
                R = PE - WM + W_curr + WM * (1 - (A + PE) / WMM)**(1 + B)
                W_curr = W_curr + (PE - R)
                
        # 自由水汇流
        S_free += R
        
        if S_free > SM_true:
            Rs = S_free - SM_true
            S_free = SM_true
        else:
            Rs = 0
            
        Ri = S_free * KI
        Rg = S_free * KG_true
        
        S_free = S_free - Ri - Rg
        
        # 总出口流量 (未考虑河道滞后，简化直接叠加)
        Q_sim[i] = Rs + Ri + Rg
        
    return Q_sim

# 生成目标“观测数据”
Q_obs_clean = run_forward_model(WM_true, B_true, KI_true)
Q_obs = Q_obs_clean + np.random.normal(0, 0.5, N) # 加入传感器测量噪声
Q_obs = np.clip(Q_obs, 0, None)

# 2. 目标函数 (纳什效率系数 NSE)
# NSE = 1 - sum((obs - sim)^2) / sum((obs - mean(obs))^2)
# 优化算法通常找极小值，所以我们最小化 1 - NSE
def objective_function(params):
    WM, B, KI = params
    # 物理惩罚边界
    if WM < 50 or WM > 200 or B < 0.01 or B > 1.0 or KI < 0.01 or KI > 0.9:
        return 9999.0
        
    Q_sim = run_forward_model(WM, B, KI)
    
    numerator = np.sum((Q_obs - Q_sim)**2)
    denominator = np.sum((Q_obs - np.mean(Q_obs))**2)
    if denominator == 0: return 9999.0
    
    nse = 1.0 - (numerator / denominator)
    return 1.0 - nse # 最小化目标

# 3. 模拟 SCE-UA 的迭代搜索过程
# 这里使用 scipy.optimize.differential_evolution 代替复杂的 SCE-UA 演示全局寻优
from scipy.optimize import differential_evolution

bounds = [(50, 200), (0.01, 1.0), (0.01, 0.9)]

# 记录优化过程中的历史参数和损失
search_history_params = []
search_history_nse = []

def callback_fn(xk, convergence):
    search_history_params.append(xk.copy())
    # 算出实际的 NSE
    loss = objective_function(xk)
    search_history_nse.append(1.0 - loss)

print("Starting Global Optimization (Calibration)...")
res = differential_evolution(objective_function, bounds, maxiter=50, popsize=15, callback=callback_fn, seed=42)

WM_opt, B_opt, KI_opt = res.x
Q_sim_opt = run_forward_model(WM_opt, B_opt, KI_opt)

# 取优化前(初始盲猜)的模型对比
WM_bad, B_bad, KI_bad = 80.0, 0.8, 0.1
Q_sim_bad = run_forward_model(WM_bad, B_bad, KI_bad)

# 计算最终 NSE
best_nse = 1.0 - objective_function(res.x)
bad_nse = 1.0 - objective_function([WM_bad, B_bad, KI_bad])

# 4. 绘图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# 子图1：水文过程线对比 (Hydrographs)
ax1.plot(Q_obs, 'ko', markersize=4, alpha=0.5, label='Observed Streamflow (with noise)')
ax1.plot(Q_sim_bad, 'r--', linewidth=2, label=f'Uncalibrated Model (NSE={bad_nse:.2f})')
ax1.plot(Q_sim_opt, 'b-', linewidth=3, label=f'Calibrated Model (NSE={best_nse:.2f})')
ax1.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax1.set_title('Hydrological Model Calibration: Simulation vs Observation', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 子图2：参数空间的收敛轨迹 (以 WM 和 B 为例)
wm_traj = [p[0] for p in search_history_params]
b_traj = [p[1] for p in search_history_params]

ax2.plot(wm_traj, b_traj, 'g-o', markersize=6, alpha=0.5, label='Optimizer Search Path')
ax2.plot(WM_bad, B_bad, 'rs', markersize=10, label='Initial Blind Guess')
ax2.plot(WM_opt, B_opt, 'b*', markersize=12, label='Calibrated Optimum')
ax2.plot(WM_true, B_true, 'kP', markersize=12, markerfacecolor='none', markeredgewidth=2, label='True Hidden Parameters')

ax2.set_xlabel('Parameter 1: WM (Soil Capacity)', fontsize=12)
ax2.set_ylabel('Parameter 2: B (Non-uniformity)', fontsize=12)
ax2.set_title('Global Optimization Trajectory in Parameter Space', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "calibration_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = [
    {'Parameter': 'WM (Capacity mm)', 'True (Hidden)': WM_true, 'Blind Guess': WM_bad, 'Calibrated': round(WM_opt, 2), 'Error %': round(abs(WM_opt-WM_true)/WM_true*100, 1)},
    {'Parameter': 'B (Shape Index)', 'True (Hidden)': B_true, 'Blind Guess': B_bad, 'Calibrated': round(B_opt, 3), 'Error %': round(abs(B_opt-B_true)/B_true*100, 1)},
    {'Parameter': 'KI (Interflow Coeff)', 'True (Hidden)': KI_true, 'Blind Guess': KI_bad, 'Calibrated': round(KI_opt, 3), 'Error %': round(abs(KI_opt-KI_true)/KI_true*100, 1)},
    {'Parameter': 'Nash-Sutcliffe Efficiency (NSE)', 'True (Hidden)': '-', 'Blind Guess': f"{bad_nse:.2f} (Poor)", 'Calibrated': f"{best_nse:.2f} (Excellent)", 'Error %': '-'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "calibration_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
