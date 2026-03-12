import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\energy-storage-system-modeling-control\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 电池荷电状态 (SOC) 估计：安时积分法的灾难与卡尔曼滤波的救赎
# 场景：展示由于电流传感器白噪声，单纯的安时积分法(Coulomb Counting)会如何随时间漂移。
# 并展示扩展卡尔曼滤波(EKF)如何利用观测到的电压将 SOC 拉回正轨。

# 1. 物理环境与真实状态 (Ground Truth)
t_end = 3600 # 模拟 1 小时放电
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 电池真值参数
Q_true = 50.0 # Ah
soc_true = np.zeros(N)
soc_true[0] = 0.90 # 真实初始电量 90%

# OCV 曲线
def get_ocv(s):
    return 3.0 + 1.2 * s - 0.5 * s**2 + 0.5 * s**3

def get_ocv_derivative(s):
    return 1.2 - 1.0 * s + 1.5 * s**2

# 生成动态放电工况 (DST工况变体)
current_true = 10.0 + 20.0 * np.sin(2 * np.pi * time / 600)
for k in range(1, N):
    soc_true[k] = soc_true[k-1] - (current_true[k] * dt) / (Q_true * 3600.0)

# 真实端电压 (包含一个固定内阻 0.01)
R_true = 0.01
V_true = get_ocv(soc_true) - current_true * R_true

# 2. 传感器的劣根性 (Noisy Measurements)
# 电流传感器有一个极其微小但致命的偏差 (Offset) 和白噪声
current_measured = current_true + 0.5 + np.random.normal(0, 0.2, N) 
# 电压传感器只有白噪声
V_measured = V_true + np.random.normal(0, 0.01, N)

# 3. 算法 A：传统的安时积分法 (Coulomb Counting)
soc_cc = np.zeros(N)
soc_cc[0] = 0.80 # 极糟糕的初始估计 (80%)，CC算法永远无法纠正初值错误

for k in range(1, N):
    soc_cc[k] = soc_cc[k-1] - (current_measured[k] * dt) / (Q_true * 3600.0)

# 4. 算法 B：扩展卡尔曼滤波 (EKF)
soc_ekf = np.zeros(N)
soc_ekf[0] = 0.80 # 同样糟糕的初始估计

P = 0.1 # 初始协方差
Q = 1e-6 # 状态方程噪声方差 (信任方程的程度)
R_cov = 0.01 # 测量方程噪声方差 (信任电压传感器的程度)

for k in range(1, N):
    # a. 时间更新 (Predict) - 听电流计的话
    soc_pred = soc_ekf[k-1] - (current_measured[k] * dt) / (Q_true * 3600.0)
    A = 1.0 # 状态转移矩阵的雅可比 (线性模型，所以是 1)
    P_pred = A * P * A + Q
    
    # b. 观测更新 (Correct) - 听电压计的话
    # 根据预测的 SOC 算出一个“我以为的端电压”
    V_pred = get_ocv(soc_pred) - current_measured[k] * R_true
    
    # 计算观测矩阵 H = dV/dSOC (通过求导)
    H = get_ocv_derivative(soc_pred)
    
    # 计算卡尔曼增益 K (我该信谁？)
    K = P_pred * H / (H * P_pred * H + R_cov)
    
    # 状态修正 (闭环纠偏)
    soc_ekf[k] = soc_pred + K * (V_measured[k] - V_pred)
    
    # 协方差更新
    P = (1 - K * H) * P_pred

# 5. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# A. SOC 漂移与纠偏对比图
ax1.plot(time, soc_true * 100, 'k-', linewidth=3, label='Ground Truth SOC (%)')
ax1.plot(time, soc_cc * 100, 'r--', linewidth=2, label='Coulomb Counting (Drifting)')
ax1.plot(time, soc_ekf * 100, 'g-', linewidth=2.5, label='EKF Filtered SOC')

# 标注初值错误和漂移
ax1.annotate('Initial Error (10%)\nCC cannot recover', xy=(0, 80), xytext=(500, 75),
             arrowprops=dict(facecolor='red', shrink=0.05))
ax1.annotate('EKF converges rapidly\nusing Voltage feedback', xy=(200, soc_ekf[200]*100), xytext=(600, 85),
             arrowprops=dict(facecolor='green', shrink=0.05))
# 标注积分漂移
ax1.annotate('Sensor Offset causes\nIntegration Drift', xy=(3500, soc_cc[3500]*100), xytext=(2500, 78),
             arrowprops=dict(facecolor='red', shrink=0.05))

ax1.set_ylabel('State of Charge (SOC) %', fontsize=12)
ax1.set_title('SOC Estimation: Open-loop Drift vs. Closed-loop Convergence', fontsize=14)
ax1.legend(loc='lower left')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 电压传感器的残差分析 (Innovation)
residual = V_measured - (get_ocv(soc_ekf) - current_measured * R_true)
ax2.plot(time, residual, 'b-', linewidth=1, alpha=0.5, label='EKF Voltage Residual (Innovation)')
ax2.axhline(0, color='k', linestyle='-')

ax2.set_xlabel('Time (seconds)', fontsize=12)
ax2.set_ylabel('Voltage Error (V)', fontsize=12)
ax2.set_title('Kalman Innovation (Difference between expected and actual voltage)', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "ekf_soc_estimation_sim.png"), dpi=300, bbox_inches='tight')

# 6. 生成对比表格
rmse_cc = np.sqrt(np.mean((soc_cc - soc_true)**2)) * 100
rmse_ekf = np.sqrt(np.mean((soc_ekf - soc_true)**2)) * 100

history = [
    {'Metric': 'Initial State Error Recovery', 'Coulomb Counting (CC)': 'Failed (Permanent 10% offset)', 'Extended Kalman Filter (EKF)': 'Recovered in ~200 seconds'},
    {'Metric': 'Current Sensor Offset Drift', 'Coulomb Counting (CC)': 'Accumulates over time (Fatal)', 'Extended Kalman Filter (EKF)': 'Compensated by voltage feedback'},
    {'Metric': 'Overall RMSE (%)', 'Coulomb Counting (CC)': f"{rmse_cc:.2f}%", 'Extended Kalman Filter (EKF)': f"{rmse_ekf:.2f}%"}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "soc_estimation_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 占位图生成
def create_schematic(path, title, description):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (1024, 512), color=(240, 245, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 1014, 502], outline=(100, 100, 150), width=3)
    try: font_title = ImageFont.truetype('arial.ttf', 36); font_desc = ImageFont.truetype('arial.ttf', 24)
    except: font_title = ImageFont.load_default(); font_desc = ImageFont.load_default()
    d.text((40, 40), title, fill=(20, 40, 100), font=font_title)
    
    words = description.split()
    lines, current_line = [], []
    for word in words:
        current_line.append(word)
        if len(current_line) > 12: lines.append(' '.join(current_line)); current_line = []
    if current_line: lines.append(' '.join(current_line))
        
    y_offset = 120
    for line in lines:
        d.text((40, y_offset), line, fill=(50, 50, 50), font=font_desc)
        y_offset += 35
    img.save(path)

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: SOC Estimation via EKF", "Diagram showing an AI Brain (Kalman Filter). It holds two pieces of paper: one says 'Current Integrator' (which is drifting away) and the other says 'Voltage Map'. The Brain mathematically combines them to find the TRUE battery level.")

print("Files generated successfully.")
