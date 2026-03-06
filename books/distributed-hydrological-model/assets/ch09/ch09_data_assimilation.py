import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch09"
os.makedirs(output_dir, exist_ok=True)

# 水文模型在线状态辨识与数据同化 (Data Assimilation)
# 场景：水文模型在长时间运行后，由于降雨输入的微小误差累积，土壤湿度(Soil Moisture)状态会“跑偏”。
# 利用卫星遥感(Satellite)提供的偶尔、且带有噪声的观测数据，通过卡尔曼滤波(Kalman Filter)纠正模型状态。

# 1. 模拟参数设定 (30天)
t_end = 30
dt = 1
time = np.arange(0, t_end, dt)
N = len(time)

np.random.seed(42)

# 2. 制造“真实的”隐藏世界 (The True Hidden State)
# 假设真实的土壤含水量动态：下雨增加，蒸发减少
true_soil = np.zeros(N)
true_soil[0] = 50.0 # 初始 50 mm
rain_events = np.zeros(N)
rain_events[[5, 6, 15, 16, 17, 25]] = [10, 15, 20, 25, 10, 30] # 真实降雨
evap_rate = 2.0 # 每天蒸发 2 mm

for i in range(1, N):
    true_soil[i] = max(0, true_soil[i-1] + rain_events[i] - evap_rate)

# 3. 水文模型 (带偏见的开环预报 - Open Loop)
# 假设气象局的雨量计有 20% 的漏测误差 (降雨输入偏小)
model_soil = np.zeros(N)
model_soil[0] = 50.0 
rain_measured = rain_events * 0.8 # 漏测了 20% 的降雨

for i in range(1, N):
    model_soil[i] = max(0, model_soil[i-1] + rain_measured[i] - evap_rate)

# 4. 卫星观测数据 (稀疏且充满噪声)
# 卫星每隔 3 天过境一次，测一次土壤湿度，传感器噪声极大 (标准差 8 mm)
obs_interval = 3
obs_time = np.arange(0, t_end, obs_interval)
obs_noise_std = 8.0
observations = true_soil[obs_time] + np.random.normal(0, obs_noise_std, len(obs_time))

# 5. 数据同化 - 一维卡尔曼滤波 (1D Kalman Filter)
# 状态方程：x(k) = x(k-1) + u(k) + w(k), w~N(0, Q)
# 观测方程：z(k) = x(k) + v(k), v~N(0, R)
kf_soil = np.zeros(N)
kf_soil[0] = 50.0
P_cov = 5.0 # 初始协方差(不确定性)
Q_err = 2.0 # 模型过程噪声方差 (对每天模型推进的不信任度)
R_err = obs_noise_std**2 # 观测噪声方差 (64.0)

for i in range(1, N):
    # a. 预测步 (Forecast step) - 跟着水文模型走
    x_pred = max(0, kf_soil[i-1] + rain_measured[i] - evap_rate)
    P_pred = P_cov + Q_err
    
    # b. 更新步 (Update/Analysis step) - 当有卫星数据时
    if i in obs_time:
        z = observations[np.where(obs_time == i)[0][0]]
        # 计算卡尔曼增益 Kalman Gain
        K = P_pred / (P_pred + R_err)
        # 融合纠偏
        x_est = x_pred + K * (z - x_pred)
        # 更新协方差 (不确定性缩小)
        P_cov = (1 - K) * P_pred
    else:
        # 如果没有观测数据，预测就是最佳估计，不确定性持续放大
        x_est = x_pred
        P_cov = P_pred
        
    kf_soil[i] = x_est

# 6. 绘图对比
fig, ax1 = plt.subplots(figsize=(12, 6))

# 画出隐藏真相
ax1.plot(time, true_soil, 'k-', linewidth=3, alpha=0.5, label='Hidden True State (Unknown)')

# 画出纯瞎猜的模型(Open Loop)
ax1.plot(time, model_soil, 'r--', linewidth=2, label='Open Loop Model (Biased forcing)')

# 画出粗糙的卫星观测点
ax1.plot(obs_time, observations, 'go', markersize=8, label='Satellite Observations (Noisy, Sparse)')

# 画出同化后的智能追踪曲线
ax1.plot(time, kf_soil, 'b-', linewidth=3, label='Assimilated State (Kalman Filter)')

# 标注一下同化瞬间的强行拉拽
ax1.annotate('Kalman Filter drags\nthe biased model back', xy=(18, kf_soil[18]), xytext=(12, kf_soil[18]-15),
             arrowprops=dict(facecolor='blue', shrink=0.05))

ax1.set_xlabel('Time (Days)', fontsize=12)
ax1.set_ylabel('Soil Moisture (mm)', fontsize=12)
ax1.set_title('Data Assimilation: Merging Faulty Model with Noisy Satellites', fontsize=14)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "data_assimilation_sim.png"), dpi=300, bbox_inches='tight')

# 7. 生成对比表格
# 计算不同方式与“真实世界”的误差 (RMSE)
def rmse(predictions, targets):
    return np.sqrt(np.mean((predictions - targets) ** 2))

rmse_model = rmse(model_soil, true_soil)
rmse_kf = rmse(kf_soil, true_soil)

# 仅计算观测点处的 RMSE
rmse_obs = rmse(observations, true_soil[obs_time])

history = [
    {'Method': 'Open Loop Model (Only Physics)', 'Information Source': 'Biased Rainfall Input', 'RMSE (mm)': round(rmse_model, 2), 'Evaluation': 'Drifts away over time'},
    {'Method': 'Satellite Observation (Only Data)', 'Information Source': 'Sensor Measurements', 'RMSE (mm)': round(rmse_obs, 2), 'Evaluation': 'Too noisy and sparse'},
    {'Method': 'Data Assimilation (Kalman Filter)', 'Information Source': 'Physics + Data Fusion', 'RMSE (mm)': round(rmse_kf, 2), 'Evaluation': 'Best Estimate'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "assimilation_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
