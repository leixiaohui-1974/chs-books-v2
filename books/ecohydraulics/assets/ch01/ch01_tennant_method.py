import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\ecohydraulics\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# Tennant 法 (Montana 法) 计算河流生态基流
# 这是一个经典的基于历史平均流量百分比的生态水力学模型

# 1. 构造一个典型北半球温带河流的多年平均月流量 (Mean Annual Runoff, MAR) 数据
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# 单位: m^3/s
monthly_flow = np.array([12.0, 15.0, 35.0, 60.0, 85.0, 110.0, 150.0, 130.0, 80.0, 45.0, 25.0, 15.0])

MAR = np.mean(monthly_flow)

# Tennant 法的参数体系
# 一般划分为两个时期：一般用水期 (10月~3月) 和 鱼类产卵育肥期 (4月~9月)
# 不同的生境保护目标对应不同的 MAR 百分比

targets = {
    'Poor (极差/生存底线)': {'general': 0.10, 'spawning': 0.10},
    'Fair (一般/基本维持)': {'general': 0.10, 'spawning': 0.30},
    'Good (良好/适宜生境)': {'general': 0.20, 'spawning': 0.40},
    'Excellent (优秀/最佳生境)': {'general': 0.30, 'spawning': 0.50}
}

eco_flows = {}

for target_name, percentages in targets.items():
    flow_req = np.zeros(12)
    for i in range(12):
        if 3 <= i <= 8: # 4月到9月 (索引3到8) 为产卵期
            flow_req[i] = MAR * percentages['spawning']
        else:
            flow_req[i] = MAR * percentages['general']
    eco_flows[target_name] = flow_req

# 绘图对比
plt.figure(figsize=(12, 7))

# 绘制自然流量柱状图
plt.bar(months, monthly_flow, color='lightblue', alpha=0.6, label='Natural Monthly Flow (Historical Avg)')
plt.axhline(y=MAR, color='k', linestyle='--', linewidth=2, label=f'Mean Annual Runoff (MAR = {MAR:.1f} $m^3/s$)')

# 绘制不同保护目标的生态基流红线
colors = ['red', 'orange', 'green', 'blue']
line_styles = ['-', '--', '-.', ':']

for (name, flow_req), color, ls in zip(eco_flows.items(), colors, line_styles):
    # 用阶梯图(step)展示按月份划分的标准
    plt.step(months, flow_req, color=color, linestyle=ls, linewidth=3, where='mid', label=f'Instream Flow: {name}')

# 标注关键时期
plt.axvspan(-0.5, 2.5, color='gray', alpha=0.1) # 1-3月
plt.axvspan(2.5, 8.5, color='green', alpha=0.1, label='Fish Spawning & Rearing Season (Apr-Sep)') # 4-9月
plt.axvspan(8.5, 11.5, color='gray', alpha=0.1) # 10-12月

plt.xlabel('Month', fontsize=12)
plt.ylabel('Flow Rate ($m^3/s$)', fontsize=12)
plt.title('Tennant Method for Instream Ecological Flow Requirements', fontsize=14)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "tennant_method_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
for i, month in enumerate(months):
    history.append({
        'Month': month,
        'Natural Flow (m³/s)': round(monthly_flow[i], 1),
        'Min Survival Baseflow (Poor)': round(eco_flows['Poor (极差/生存底线)'][i], 1),
        'Good Habitat Baseflow (Good)': round(eco_flows['Good (良好/适宜生境)'][i], 1),
        'Ideal Habitat Baseflow (Excellent)': round(eco_flows['Excellent (优秀/最佳生境)'][i], 1)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "tennant_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
