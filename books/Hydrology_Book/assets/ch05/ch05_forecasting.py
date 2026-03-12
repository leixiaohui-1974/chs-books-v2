import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Hydrology_Book\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 预报与模拟算法 (Forecasting Algorithms)
# 场景：展示“纯物理概念模型”、“纯数据驱动机器学习(LSTM)”以及“集合概率预报(Ensemble)”在极端洪水预测中的对比。

# 1. 生成合成的物理水文时间序列 (The Hidden Truth)
t_end = 120 # 120 小时预报期
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

np.random.seed(42)

# 降雨强迫 (含有一场未见过的特大暴雨)
rain = np.zeros(N)
rain[20:40] = 5.0 # 普通降雨
rain[70:90] = 25.0 # 极端降雨 (Out of Distribution for ML)

# 真实的隐藏水位 (The Ground Truth)
true_level = np.zeros(N)
base_level = 2.0
true_level[0] = base_level

# 模拟真实的非线性汇流
for i in range(1, N):
    inflow = rain[i] * 1.5
    outflow = 0.5 * (true_level[i-1] - base_level)**1.2 if true_level[i-1] > base_level else 0
    true_level[i] = true_level[i-1] + inflow - outflow + np.random.normal(0, 0.1)

# 2. 纯物理概念模型预报 (Conceptual Physics Model)
# 缺点：参数没调准，存在固定的系统性偏差 (Systematic Bias)
phys_level = np.zeros(N)
phys_level[0] = base_level
for i in range(1, N):
    inflow = rain[i] * 1.2 # 参数低估了产流
    outflow = 0.6 * (phys_level[i-1] - base_level)**1.0 # 错误地假设了线性出流
    phys_level[i] = phys_level[i-1] + inflow - outflow

# 3. 纯数据驱动机器学习预报 (Pure ML Model - LSTM surrogate)
# 缺点：在训练集见过的普通降雨(前40小时)中表现极其完美。
# 但面对从未见过的极端降雨(70-90小时)，产生严重的泛化失效 (Extrapolation Failure)
ml_level = np.zeros(N)
for i in range(N):
    if rain[i] < 10.0:
        # 在小雨区完美拟合历史规律
        ml_level[i] = true_level[i] + np.random.normal(0, 0.05)
    else:
        # 在大雨区，因为没见过，AI的激活函数饱和，给出了极其保守的低估
        ml_level[i] = true_level[i] * 0.6 + 5.0 + np.random.normal(0, 0.2)

# 平滑 ML 输出以模拟真实的自回归预测
ml_level = pd.Series(ml_level).rolling(window=3, min_periods=1).mean().values

# 4. 集合概率预报 (Ensemble Forecast / Grey-box)
# 方法：用物理模型打底，对气象输入进行 50 次微扰 (蒙特卡洛)，生成包络线
n_ensembles = 50
ensemble_levels = np.zeros((n_ensembles, N))

for j in range(n_ensembles):
    # 对降雨进行加性/乘性联合微扰
    perturbed_rain = rain * np.random.uniform(0.8, 1.5, N) + np.random.normal(0, 1.0, N)
    perturbed_rain = np.maximum(0, perturbed_rain)
    
    e_level = np.zeros(N)
    e_level[0] = base_level
    for i in range(1, N):
        inflow = perturbed_rain[i] * 1.5 # 使用修正后的正确参数
        outflow = 0.5 * max(0, e_level[i-1] - base_level)**1.2
        e_level[i] = e_level[i-1] + inflow - outflow
    ensemble_levels[j, :] = e_level

# 计算集合统计量 (5%, 50% Median, 95%)
ens_median = np.median(ensemble_levels, axis=0)
ens_p5 = np.percentile(ensemble_levels, 5, axis=0)
ens_p95 = np.percentile(ensemble_levels, 95, axis=0)

# 5. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

# A. 物理模型与机器学习的极限对决
ax1.plot(time, true_level, 'k-', linewidth=3, label='Ground Truth Water Level')
ax1.plot(time, phys_level, 'g--', linewidth=2, label='Physical Model (Systematic Bias)')
ax1.plot(time, ml_level, 'r-.', linewidth=2, label='Pure ML Model (Extrapolation Failure)')

ax1.axvline(60, color='gray', linestyle=':')
ax1.text(30, 20, 'Normal Event\n(ML wins)', ha='center', fontsize=12)
ax1.text(90, 20, 'Extreme Event\n(ML collapses)', ha='center', fontsize=12)

ax1.set_ylabel('Water Level (m)', fontsize=12)
ax1.set_title('Forecast Rivalry: Physics vs. Machine Learning', fontsize=14)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 集合预报 (概率之美)
ax2.plot(time, true_level, 'k-', linewidth=3, label='Ground Truth Water Level')
ax2.plot(time, ens_median, 'b-', linewidth=2, label='Ensemble Median (P50)')
ax2.fill_between(time, ens_p5, ens_p95, color='blue', alpha=0.2, label='90% Confidence Interval (P5-P95)')

ax2.axhline(15.0, color='red', linestyle='--', linewidth=2, label='Flood Warning Threshold (15m)')

# 标出概率跨过警戒线的时刻
prob_over_warning = np.sum(ensemble_levels > 15.0, axis=0) / n_ensembles
critical_idx = np.where(prob_over_warning > 0.5)[0]
if len(critical_idx) > 0:
    ax2.annotate(f'>50% Probability\nof Flooding!', xy=(time[critical_idx[0]], 15.0), xytext=(time[critical_idx[0]]-30, 22.0),
                 arrowprops=dict(facecolor='red', shrink=0.05))

ax2.set_xlabel('Forecast Horizon (Hours)', fontsize=12)
ax2.set_ylabel('Water Level (m)', fontsize=12)
ax2.set_title('Ensemble Forecast: Embracing Uncertainty with Confidence Intervals', fontsize=14)
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "forecast_algorithms_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 计算两个时段的 RMSE
rmse_phys_1 = np.sqrt(np.mean((phys_level[:60] - true_level[:60])**2))
rmse_ml_1 = np.sqrt(np.mean((ml_level[:60] - true_level[:60])**2))

rmse_phys_2 = np.sqrt(np.mean((phys_level[60:] - true_level[60:])**2))
rmse_ml_2 = np.sqrt(np.mean((ml_level[60:] - true_level[60:])**2))
rmse_ens_2 = np.sqrt(np.mean((ens_median[60:] - true_level[60:])**2))

history = [
    {'Model Type': 'Physical (Conceptual)', 'Normal Event RMSE (m)': round(rmse_phys_1, 2), 'Extreme Event RMSE (m)': round(rmse_phys_2, 2), 'Characteristic': 'Consistent but biased'},
    {'Model Type': 'Machine Learning (LSTM)', 'Normal Event RMSE (m)': round(rmse_ml_1, 2), 'Extreme Event RMSE (m)': round(rmse_ml_2, 2), 'Characteristic': 'Overfits history, fails on extremes'},
    {'Model Type': 'Ensemble (Grey-box)', 'Normal Event RMSE (m)': '-', 'Extreme Event RMSE (m)': round(rmse_ens_2, 2), 'Characteristic': 'Provides 90% Confidence Bounds'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "forecast_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch05: Forecasting Algorithms", "Diagram showing an AI Brain (LSTM) and a Physics Engine (Conceptual Model) combining forces. The AI is fast but fails in unknown weather. The Physics Engine is stable but biased. Together they form an Ensemble Forecast, producing a safe probability cloud instead of a single brittle line.")

print("Files generated successfully.")
