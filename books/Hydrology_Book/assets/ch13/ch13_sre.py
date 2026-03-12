import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Hydrology_Book\assets\ch13"
os.makedirs(output_dir, exist_ok=True)

# 平台可靠性工程 (SRE) 与混沌测试 (Chaos Engineering)
# 场景：模拟在连续 30 天的高频水文预报中，单机架构与云原生高可用(HA)架构在面对硬件故障时的 SLI (可用性指标) 对比。

# 1. 模拟环境：30天，每分钟一次服务健康打点 (共 43200 分钟)
days = 30
minutes_per_day = 24 * 60
total_minutes = days * minutes_per_day
time = np.arange(total_minutes)

# 生成每日的水文 API 请求量 (白天高峰，夜间低谷，遭遇暴雨时请求激增)
base_load = 50 + 40 * np.sin(np.pi * (time % minutes_per_day) / (minutes_per_day / 2) - np.pi/2)
# 模拟第 15 天发生大暴雨，API 请求暴涨 5 倍
storm_surge = np.zeros(total_minutes)
storm_start = 14 * minutes_per_day
storm_end = 16 * minutes_per_day
storm_surge[storm_start:storm_end] = 300 * np.exp(-((time[storm_start:storm_end] - (storm_start + minutes_per_day)) / 600)**2)
request_load = base_load + storm_surge + np.random.normal(0, 5, total_minutes)
request_load = np.maximum(10, request_load)

# 2. 混沌工程：注入随机与特定故障
# a. 内存泄漏导致的 OOM (Out of Memory) 崩溃 (每 7 天发生一次)
# b. 暴雨期算力过载导致的雪崩
# c. 机房市电中断 (第 25 天)
faults = np.zeros(total_minutes)
# OOM
faults[7*minutes_per_day : 7*minutes_per_day + 45] = 1 # 宕机 45 分钟恢复
faults[21*minutes_per_day : 21*minutes_per_day + 60] = 1
# 暴雨期单机算力雪崩
faults[15*minutes_per_day : 15*minutes_per_day + 180] = 1 # 宕机 3 小时
# 市电中断
faults[25*minutes_per_day : 25*minutes_per_day + 120] = 1 # 宕机 2 小时

# 3. 架构 A：传统单体架构 (Monolith) - 只要发生故障，系统直接返回 502 Bad Gateway
status_monolith = np.ones(total_minutes) # 1 为正常，0 为宕机
status_monolith[faults == 1] = 0

# 4. 架构 B：云原生高可用架构 (K8s 多活集群 + 自动扩缩容 HPA)
status_ha = np.ones(total_minutes)
# HA 架构在 OOM 时：Pod 崩溃，K8s 在 1 分钟内拉起新 Pod
status_ha[7*minutes_per_day : 7*minutes_per_day + 1] = 0
status_ha[21*minutes_per_day : 21*minutes_per_day + 1] = 0
# HA 架构在暴雨时：自动触发 HPA 扩容，短暂卡顿 2 分钟，随后平稳承载
status_ha[15*minutes_per_day : 15*minutes_per_day + 2] = 0
# HA 架构在市电中断时：主数据中心瘫痪，全局 DNS 流量切换至备用数据中心，耗时 5 分钟
status_ha[25*minutes_per_day : 25*minutes_per_day + 5] = 0

# 5. 计算 SRE 核心指标 (SLI: Service Level Indicator)
def calc_sli(status_array):
    uptime = np.sum(status_array == 1)
    downtime = np.sum(status_array == 0)
    availability = (uptime / total_minutes) * 100
    return downtime, availability

down_mono, avail_mono = calc_sli(status_monolith)
down_ha, avail_ha = calc_sli(status_ha)

# 6. 绘图展示
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# A. API 负载监控
ax1.plot(time / minutes_per_day, request_load, 'k-', linewidth=1, alpha=0.7)
ax1.set_ylabel('API Requests / min', fontsize=12)
ax1.set_title('System Load: Daily Fluctuations & Extreme Storm Surge', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.5)

# B. 传统单机架构的可用性图谱
ax2.fill_between(time / minutes_per_day, 0, 1, where=(status_monolith==1), color='green', alpha=0.5, label='System UP')
ax2.fill_between(time / minutes_per_day, 0, 1, where=(status_monolith==0), color='red', alpha=0.8, label='System DOWN (502 Error)')
ax2.set_ylabel('Monolith Status', fontsize=12)
ax2.set_title(f'Traditional IT Architecture (Availability: {avail_mono:.3f}%)', fontsize=14)
ax2.set_yticks([])
ax2.legend(loc='upper right')

# 标注暴雨期系统崩溃
ax2.annotate('Crash during Storm!\n(Worst possible time)', xy=(15.1, 0.5), xytext=(12, 0.7),
             arrowprops=dict(facecolor='black', shrink=0.05))

# C. SRE 云原生高可用架构的可用性图谱
ax3.fill_between(time / minutes_per_day, 0, 1, where=(status_ha==1), color='green', alpha=0.5, label='System UP')
ax3.fill_between(time / minutes_per_day, 0, 1, where=(status_ha==0), color='red', alpha=0.8, label='Micro-Outages (Recovered)')
ax3.set_xlabel('Time (Days)', fontsize=12)
ax3.set_ylabel('Cloud Native Status', fontsize=12)
ax3.set_title(f'SRE Cloud Native Architecture (Availability: {avail_ha:.3f}% - "Three Nines")', fontsize=14)
ax3.set_yticks([])
ax3.legend(loc='upper right')

# 标注自愈能力
ax3.annotate('HPA Auto-scaling\nDNS Failover', xy=(15.0, 0.5), xytext=(17, 0.7),
             arrowprops=dict(facecolor='blue', shrink=0.05))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "sre_reliability_sim.png"), dpi=300, bbox_inches='tight')

# 7. 生成运维报表 (Markdown Table)
history = [
    {'Metric': 'Target SLO (Service Level Obj.)', 'Monolith': '> 99.0%', 'Cloud Native (SRE)': '> 99.9% (Three Nines)'},
    {'Metric': 'Total Downtime in 30 Days', 'Monolith': f"{down_mono} minutes ({down_mono/60:.1f} hrs)", 'Cloud Native (SRE)': f"{down_ha} minutes"},
    {'Metric': 'Actual Availability (SLI)', 'Monolith': f"{avail_mono:.3f}% (Failed)", 'Cloud Native (SRE)': f"{avail_ha:.3f}% (Passed)"},
    {'Metric': 'Storm Event Survivability', 'Monolith': 'Catastrophic Failure', 'Cloud Native (SRE)': 'Seamless Auto-scaled'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "sre_metrics_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 8. 占位图生成
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch13: HydroDesktop SRE & Chaos", "Diagram of a Server Room on fire (Chaos Engineering). A traditional server melts down, causing a total blackout. But a Cloud Native SRE system instantly shifts its traffic to a backup data center, surviving the fire with only 5 minutes of downtime.")

print("Files generated successfully.")
