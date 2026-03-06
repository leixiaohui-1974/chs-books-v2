import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch08"
os.makedirs(output_dir, exist_ok=True)

# 模型不确定性分析 (Uncertainty Analysis)
# 演示 GLUE 方法 (Generalized Likelihood Uncertainty Estimation) 在水文参数评估中的应用
# “异物同效” (Equifinality) 现象可视化

np.random.seed(101)

# 1. 构建一个简化的水文响应面 (Response Surface)
# 假设我们有两个未知参数:
# Param 1: x (例如土壤下渗率) [0, 10]
# Param 2: y (例如河道糙率) [0, 10]
# 真实的隐藏最优解在 (x=7, y=3) 处。
# 但是由于观测数据有误差，在 (x=3, y=8) 处也存在一个能产生同样好结果的“假极值点”(异物同效)。

def model_performance(x, y):
    # 构造一个双峰分布的效率系数曲面 (类似 NSE)
    # Peak 1 at (7, 3)
    peak1 = np.exp(-((x-7)**2 + (y-3)**2)/4.0)
    # Peak 2 at (3, 8)
    peak2 = np.exp(-((x-3)**2 + (y-8)**2)/3.0)
    # 加上一个极其复杂的背景非线性
    background = 0.1 * np.sin(x) * np.cos(y)
    
    perf = 0.5 + 0.45 * max(peak1, peak2 * 0.95) + background
    return min(perf, 1.0)

# 2. GLUE 蒙特卡洛抽样 (Monte Carlo Sampling)
n_samples = 5000
sampled_x = np.random.uniform(0, 10, n_samples)
sampled_y = np.random.uniform(0, 10, n_samples)
performances = np.array([model_performance(x, y) for x, y in zip(sampled_x, sampled_y)])

# 3. GLUE 阈值截断 (Thresholding)
# 设定可接受模型阈值 (Behavioral Models Threshold)
threshold_nse = 0.85

# 筛选出 Behavioral Models
behavioral_idx = np.where(performances >= threshold_nse)[0]
non_behavioral_idx = np.where(performances < threshold_nse)[0]

beh_x = sampled_x[behavioral_idx]
beh_y = sampled_y[behavioral_idx]
beh_perf = performances[behavioral_idx]

# 将性能(NSE)转化为似然权重 (Likelihood Weights)
likelihoods = beh_perf - threshold_nse
likelihoods = likelihoods / np.sum(likelihoods) # 归一化

# 4. 基于似然权重的预测不确定性区间 (Prediction Uncertainty Bounds)
# 为了演示，我们假设模型输出 Q = x * t + y * sin(t) (简化的线性/非线性输出组合)
t_arr = np.linspace(0, 10, 50)
predictions = np.zeros((len(behavioral_idx), len(t_arr)))

for i, (x_val, y_val) in enumerate(zip(beh_x, beh_y)):
    # 模拟水文过程线
    # 这里用一个包含两个参数的假函数模拟随时间变化的流量
    predictions[i, :] = 10 + x_val * np.sin(t_arr) + y_val * np.cos(t_arr * 0.5)

# 计算 95% 置信区间 (5% - 95% 分位数)
# 注意：严格的 GLUE 应该基于 likelihoods 的累积分布，这里使用加权百分位数近似或为了绘图直观采用集合统计
q_5 = np.percentile(predictions, 5, axis=0)
q_95 = np.percentile(predictions, 95, axis=0)
q_median = np.median(predictions, axis=0)

# 假设真实的观测过程线 (带有少量噪声)
true_x, true_y = 7.0, 3.0
obs_q = 10 + true_x * np.sin(t_arr) + true_y * np.cos(t_arr * 0.5) + np.random.normal(0, 1.5, len(t_arr))

# 5. 绘图
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 图 A: 参数空间中的异物同效 (Equifinality in Parameter Space)
sc1 = ax1.scatter(sampled_x[non_behavioral_idx], sampled_y[non_behavioral_idx], c='gray', s=5, alpha=0.3, label='Non-Behavioral Models')
sc2 = ax1.scatter(beh_x, beh_y, c=beh_perf, cmap='autumn_r', s=20, label=f'Behavioral Models (NSE > {threshold_nse})')
plt.colorbar(sc2, ax=ax1, label='Model Performance (NSE)')

ax1.plot(7, 3, 'k*', markersize=15, label='True Parameter Point A')
ax1.plot(3, 8, 'k*', markersize=15, label='Equifinal Parameter Point B')

ax1.set_xlabel('Parameter X (e.g., Infiltration Rate)', fontsize=12)
ax1.set_ylabel('Parameter Y (e.g., Channel Roughness)', fontsize=12)
ax1.set_title("Equifinality: Multiple 'Good' Parameter Sets", fontsize=14)
ax1.legend(loc='lower left')

# 图 B: 预测不确定性区间 (Uncertainty Bounds)
ax2.plot(t_arr, obs_q, 'ko', markersize=5, label='Observed Streamflow')
ax2.fill_between(t_arr, q_5, q_95, color='orange', alpha=0.4, label='95% Prediction Uncertainty Bounds')
ax2.plot(t_arr, q_median, 'r-', linewidth=2, label='Median Prediction')

ax2.set_xlabel('Time (days)', fontsize=12)
ax2.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax2.set_title('GLUE Output: Uncertainty Bounds rather than a Single Line', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "glue_uncertainty_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 提取 Peak 1 和 Peak 2 的代表性参数
# 手动找靠近 Peak 1 (7, 3) 的局部最优
peak1_mask = (beh_x > 5) & (beh_y < 5)
if np.any(peak1_mask):
    idx_p1 = np.where(peak1_mask)[0][np.argmax(beh_perf[peak1_mask])]
    best_p1_x, best_p1_y = beh_x[idx_p1], beh_y[idx_p1]
else:
    best_p1_x, best_p1_y = 7.0, 3.0

# 手动找靠近 Peak 2 (3, 8) 的局部最优
peak2_mask = (beh_x < 5) & (beh_y > 5)
if np.any(peak2_mask):
    idx_p2 = np.where(peak2_mask)[0][np.argmax(beh_perf[peak2_mask])]
    best_p2_x, best_p2_y = beh_x[idx_p2], beh_y[idx_p2]
else:
    best_p2_x, best_p2_y = 3.0, 8.0

history = [
    {'Parameter Set Type': 'True Hidden Law (A)', 'Param X': 7.0, 'Param Y': 3.0, 'Resulting NSE': round(model_performance(7,3), 3)},
    {'Parameter Set Type': 'Identified Peak 1 (Global)', 'Param X': round(best_p1_x, 2), 'Param Y': round(best_p1_y, 2), 'Resulting NSE': round(np.max(beh_perf), 3)},
    {'Parameter Set Type': 'Identified Peak 2 (Equifinal)', 'Param X': round(best_p2_x, 2), 'Param Y': round(best_p2_y, 2), 'Resulting NSE': round(beh_perf[idx_p2], 3)}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "glue_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 用 python 生成一张不带依赖的简单的网络拓扑架构图作为占位符
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch08: GLUE Uncertainty", "Diagram illustrating Equifinality. Many different parameter sets lead to the same model output. A confidence interval is drawn around the hydrograph.")

print("Files generated successfully.")
