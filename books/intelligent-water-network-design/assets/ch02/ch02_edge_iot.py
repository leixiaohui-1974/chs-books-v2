import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\intelligent-water-network-design\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 边缘计算与物联网 (Edge Computing & IoT)
# 模拟水网物联网设备（传感器）产生的高频原始数据，
# 对比“云端直接处理(Cloud-Only)”与“边缘计算预处理(Edge-Cloud)”的带宽消耗与延迟差异。

# 1. 模拟物理世界：水管管网水压 (Water Pressure in Pipe)
# 采样率 100 Hz (每秒 100 个点)，模拟 60 秒
fs = 100
t_end = 60.0
time = np.arange(0, t_end, 1/fs)
N = len(time)

# 正常水压基线 (例如 0.4 MPa)
pressure_base = 0.4 * np.ones(N)

# 制造日常用水导致的缓慢波动
slow_wave = 0.05 * np.sin(2 * np.pi * time / 20.0)

# 制造传感器的高频白噪声 (精度抖动)
np.random.seed(42)
noise = np.random.normal(0, 0.01, N)

# 制造“水锤效应”异常冲击 (Water Hammer Anomaly)
# 在 30秒 处由于某个大阀门突然关闭，产生高频振荡
water_hammer = np.zeros(N)
anomaly_start = 30.0
for i, t in enumerate(time):
    if t >= anomaly_start and t < anomaly_start + 5.0:
        # 衰减的指数高频振荡
        water_hammer[i] = 0.15 * np.exp(-(t - anomaly_start)*2.0) * np.sin(2 * np.pi * 5.0 * (t - anomaly_start))

# 真实的原始信号 (Raw Signal)
raw_pressure = pressure_base + slow_wave + noise + water_hammer

# 2. 方案 A: 纯云端架构 (Cloud-Only Architecture)
# 边缘设备是“傻子”，只负责采集。把所有 100Hz 的原始数据打包通过 4G/5G 传给云端。
# 云端负责过滤噪声、识别水锤异常。
# 带宽消耗：100 float/sec
data_tx_cloud = np.ones(N) * 1.0 # 相对单位，每个点发1次

# 3. 方案 B: 边缘计算架构 (Edge Computing Architecture)
# 边缘盒子(Edge Node)内嵌了智能算法 (比如移动平均、小波变换或轻量级 AI)。
# 逻辑：
# 1. 如果数据平稳，边缘盒子就在本地做平均，每 5 秒钟只向云端发送一个“健康心跳包”和平均值。
# 2. 如果边缘盒子检测到异常高频振荡 (导数或方差超标)，立刻触发“报警模式”，
#    将异常前后几秒的高频原始数据全量透传给云端供专家分析。

# 边缘端异常检测算法 (简单方差检测滑动窗口)
window_size = 50 # 0.5s 窗口
rolling_var = pd.Series(raw_pressure).rolling(window=window_size).var().fillna(0).values

threshold = 0.0005 # 超过这个方差认为有异常 (比如水锤)
is_anomaly = rolling_var > threshold

# 膨胀异常窗口，确保把异常前后的数据都发上去
anomaly_expanded = np.zeros(N, dtype=bool)
for i in range(N):
    if is_anomaly[i]:
        # 向前向后扩展 1 秒 (100个点)
        start_idx = max(0, i - 100)
        end_idx = min(N, i + 100)
        anomaly_expanded[start_idx:end_idx] = True

data_tx_edge = np.zeros(N)
edge_processed_signal = np.zeros(N)
edge_processed_signal[:] = np.nan # 不发送的地方是空值

last_send_time = -5.0
for i, t in enumerate(time):
    if anomaly_expanded[i]:
        # 异常期间：全量透传 (100Hz)
        data_tx_edge[i] = 1.0
        edge_processed_signal[i] = raw_pressure[i]
    else:
        # 平稳期间：每 2 秒发送一个平均值包 (降频到 0.5Hz)
        if t - last_send_time >= 2.0:
            data_tx_edge[i] = 1.0
            # 计算过去两秒的平均值
            start_idx = max(0, int((t - 2.0)*fs))
            edge_processed_signal[i] = np.mean(raw_pressure[start_idx:i])
            last_send_time = t

# 计算累积数据传输量 (Cumulative Data Transmission)
cum_tx_cloud = np.cumsum(data_tx_cloud)
cum_tx_edge = np.cumsum(data_tx_edge)

# 4. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 原始高频数据 (传感器源头)
ax1.plot(time, raw_pressure, 'gray', linewidth=1, alpha=0.8, label='Raw IoT Sensor Signal (100Hz)')
ax1.set_ylabel('Water Pressure (MPa)', fontsize=12)
ax1.set_title('Level 0: Raw High-Frequency IoT Data (Contains Noise & Anomalies)', fontsize=14)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注水锤
ax1.annotate('Water Hammer\n(Valve closed)', xy=(30.5, 0.5), xytext=(20, 0.55),
             arrowprops=dict(facecolor='red', shrink=0.05))

# B. 边缘计算过滤后的上传数据 (云端看到的样子)
ax2.plot(time, raw_pressure, 'gray', linewidth=1, alpha=0.2, label='(Raw Background)')
# 正常状态的稀疏散点
normal_idx = (data_tx_edge > 0) & (~anomaly_expanded)
ax2.plot(time[normal_idx], edge_processed_signal[normal_idx], 'go', markersize=6, label='Edge Normal Heartbeat (0.5Hz Avg)')

# 异常状态的全量透传实线
anomaly_idx = (data_tx_edge > 0) & anomaly_expanded
ax2.plot(time[anomaly_idx], edge_processed_signal[anomaly_idx], 'r-', linewidth=2, label='Edge Alarm Passthrough (100Hz Raw)')

ax2.set_ylabel('Water Pressure (MPa)', fontsize=12)
ax2.set_title('Level 1: Data Received by Cloud (After Edge AI Filtering)', fontsize=14)
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 通信带宽消耗对比
ax3.plot(time, cum_tx_cloud, 'k-', linewidth=3, label='Cumulative Packets (Cloud-Only)')
ax3.plot(time, cum_tx_edge, 'b-', linewidth=3, label='Cumulative Packets (Edge-Cloud)')
ax3.fill_between(time, cum_tx_edge, cum_tx_cloud, color='gray', alpha=0.2, label='Saved Bandwidth (90%+)')

ax3.set_xlabel('Time (seconds)', fontsize=12)
ax3.set_ylabel('Transmitted Data Packets', fontsize=12)
ax3.set_title('Communication Cost & Network Congestion Analysis', fontsize=14)
ax3.legend(loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edge_computing_sim.png"), dpi=300, bbox_inches='tight')

# 5. 生成对比表格
# 计算指标
total_packets_cloud = cum_tx_cloud[-1]
total_packets_edge = cum_tx_edge[-1]
compression_ratio = (total_packets_cloud - total_packets_edge) / total_packets_cloud * 100

history = [
    {'Architecture': 'Cloud-Only (Dumb Sensor)', 'Data Packets Sent': f"{int(total_packets_cloud):,}", 'Cloud Compute Load': 'Extremely High (Processes all noise)', 'Anomaly Detection Delay': 'High (Network Latency)'},
    {'Architecture': 'Edge-Cloud (Smart Box)', 'Data Packets Sent': f"{int(total_packets_edge):,}", 'Cloud Compute Load': 'Low (Only processes anomalies)', 'Anomaly Detection Delay': 'Millisecond (Local Trigger)'},
    {'Architecture': 'Impact / ROI', 'Data Packets Sent': f"Bandwidth Saved {compression_ratio:.1f}%", 'Cloud Compute Load': 'Server Cost Slashed', 'Anomaly Detection Delay': 'Instant Valve Shutoff'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "edge_iot_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch02: Edge Computing & IoT", "Diagram showing a water pipe with a sensor. The sensor data hits an Edge AI Box on a pole. The box drops 95% of boring data in the trash, and only sends the crucial 5% (like a pipe burst spike) up to the Cloud via 5G.")

print("Files generated successfully.")
