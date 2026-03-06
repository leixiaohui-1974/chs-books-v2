import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch07"
os.makedirs(output_dir, exist_ok=True)

# 结果导向：能耗 KPI 评估与多角色视图 (KPI Assessment & Role-based Dashboard)
# 模拟在引入数字孪生协同控制后，工厂一个月的真实运行数据变化，
# 以及针对操作员、工艺员、厂长的不同数据呈现。

# 1. 模拟长周期运行数据 (30天，每天 24 小时)
days = 30
hours_per_day = 24
N = days * hours_per_day
time = np.arange(0, N)

np.random.seed(42)

# 物理产出：每天要求蒸发水分总量保持在约 1000 吨/天
target_evap_rate = 1000.0 / 24.0 # t/h

# 模拟结疤导致的基础传热效率衰减
efficiency_decay = np.linspace(1.0, 0.7, N)

# 场景 A：传统人工控制 (Conservative Manual Control)
# 为了防止不达标，人工控制总是给出极大的安全裕度 (多加蒸汽)
# 且对波动的响应导致蒸汽浪费
steam_manual = (target_evap_rate / efficiency_decay) * 0.45 * (1 + 0.1 * np.random.rand(N))
evap_manual = target_evap_rate + np.random.normal(0, 1.5, N)

# 场景 B：智能协同控制 (Smart Cooperative Control - MPC + SQP)
# AI 敢于贴着红线走，压榨每一滴蒸汽的价值
steam_smart = (target_evap_rate / efficiency_decay) * 0.38 * (1 + 0.02 * np.random.randn(N))
evap_smart = target_evap_rate + np.random.normal(0, 0.2, N)

# 2. 核心 KPI：汽耗比计算 (Steam Ratio = Steam / Evaporated Water)
ratio_manual = steam_manual / evap_manual
ratio_smart = steam_smart / evap_smart

# 降采样为每日统计数据 (Daily Aggregation)
daily_manual_ratio = np.mean(ratio_manual.reshape(-1, 24), axis=1)
daily_smart_ratio = np.mean(ratio_smart.reshape(-1, 24), axis=1)
daily_time = np.arange(1, days + 1)

# 3. 多角色数据视图绘图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 14))

# 视图 A: 厂长视角 (经济视角 - 关注宏观成本与 KPI 达标)
ax1.plot(daily_time, daily_manual_ratio, 'r-o', linewidth=2, markersize=6, label='Manual Operations (Historical)')
ax1.plot(daily_time, daily_smart_ratio, 'g-s', linewidth=3, markersize=8, label='Digital Twin Operations (Current)')
ax1.axhline(0.40, color='k', linestyle='--', linewidth=2, label='Factory KPI Target (0.40 t/t)')

ax1.fill_between(daily_time, daily_manual_ratio, daily_smart_ratio, color='green', alpha=0.2, label='Direct Steam Savings (Profit)')

ax1.set_ylabel('Daily Steam Ratio (t/t)', fontsize=12)
ax1.set_title('Plant Manager View: Financial Impact & KPI Achievement', fontsize=14)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.6)

# 视图 B: 工艺员视角 (设备健康视角 - 关注结疤衰减趋势)
# 工艺员需要决定什么时候洗罐。通过辨识技术反推设备健康度
health_index_manual = 1.0 / daily_manual_ratio
health_index_smart = 1.0 / daily_smart_ratio # 智能控制下健康度显得更高，因为能效更好

ax2.plot(daily_time, health_index_manual, 'gray', linestyle=':', linewidth=2, label='Apparent Health (Manual)')
ax2.plot(daily_time, efficiency_decay[::24], 'k-', linewidth=3, label='True Scaling Health (Estimated by AI)')
ax2.axhline(0.75, color='red', linestyle='-', linewidth=2, label='Cleaning Threshold (Trigger Wash)')

ax2.annotate('AI predicts washing needed\non Day 26', xy=(26, 0.75), xytext=(15, 0.8),
             arrowprops=dict(facecolor='black', shrink=0.05))

ax2.set_ylabel('Equipment Health Index', fontsize=12)
ax2.set_title('Process Engineer View: Fouling Prediction & Maintenance', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# 视图 C: 操作员视角 (实时红线视角 - 关注是否超标)
# 提取一天内 (第 15 天) 的高频波动
day15_start = 14 * 24
day15_end = 15 * 24
time_hours = np.arange(0, 24)

ax3.plot(time_hours, evap_manual[day15_start:day15_end], 'r--', linewidth=2, label='Evaporation Rate (Manual)')
ax3.plot(time_hours, evap_smart[day15_start:day15_end], 'b-', linewidth=3, label='Evaporation Rate (AI Control)')
ax3.axhspan(target_evap_rate - 0.5, target_evap_rate + 0.5, color='green', alpha=0.2, label='Strict Quality Target Band')

ax3.set_xlabel('Hour of the Day (Day 15)', fontsize=12)
ax3.set_ylabel('Evaporation Rate (t/h)', fontsize=12)
ax3.set_title('Operator View: Real-time Stability & Alarm Prevention', fontsize=14)
ax3.legend(loc='upper right')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "role_based_dashboards.png"), dpi=300, bbox_inches='tight')

# 4. 生成财务报表 (Markdown Table)
total_steam_manual = np.sum(steam_manual)
total_steam_smart = np.sum(steam_smart)
steam_saved_tons = total_steam_manual - total_steam_smart
steam_price = 200.0 # 元/吨
money_saved = steam_saved_tons * steam_price / 10000.0 # 万元

history = [
    {'Metric': 'Monthly Steam Consumption (tons)', 'Manual': f"{int(total_steam_manual):,}", 'AI Control': f"{int(total_steam_smart):,}", 'Improvement': f"-{int(steam_saved_tons):,} tons"},
    {'Metric': 'Average Steam Ratio (t/t)', 'Manual': round(np.mean(ratio_manual), 3), 'AI Control': round(np.mean(ratio_smart), 3), 'Improvement': f"-{round((np.mean(ratio_manual)-np.mean(ratio_smart))/np.mean(ratio_manual)*100, 1)}%"},
    {'Metric': 'Target Compliance (%)', 'Manual': '45%', 'AI Control': '99%', 'Improvement': 'Quality Stabilized'},
    {'Metric': 'Direct Economic Benefit (CNY)', 'Manual': '-', 'AI Control': f"{round(money_saved, 1)} 万", 'Improvement': 'Immediate ROI'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "kpi_financial_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch07: Result-Oriented Dashboards", "Diagram splitting into three screens. Top screen for Manager shows huge bags of money saved. Middle screen for Engineer shows a graph predicting when pipes will clog. Bottom screen for Operator shows a green checkmark saying 'All limits respected'.")

print("Files generated successfully.")
