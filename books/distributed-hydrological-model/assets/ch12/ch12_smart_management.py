import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch12"
os.makedirs(output_dir, exist_ok=True)

# 流域智能管理与水库调度优化 (Smart Basin Management & Reservoir Operation)
# 场景：利用数字孪生水文模型预测未来降雨，指导梯级水库进行“防洪与发电”的多目标调度。

# 1. 模拟参数设定
t_end = 120 # 模拟 120 小时 (5天)
dt = 1.0
time = np.arange(0, t_end, dt)
N = len(time)

# 气象预报：未来 5 天将有一场双峰暴雨
rain = np.zeros(N)
rain[20:40] = 10.0 # 第一波雨
rain[70:90] = 20.0 # 第二波大暴雨

# 2. 水文模型 (极简) 生成入库洪水 Q_in
Q_in = np.zeros(N)
S_catchment = 0.0
for i in range(1, N):
    S_catchment += rain[i] * dt * 0.8 # 80% 产流
    outflow = (S_catchment / 5.0) * dt # 快汇流
    S_catchment -= outflow
    Q_in[i] = outflow * 55.0 # 面积放大到真实流量 m3/s (缩小比例以适应库容)

Q_in += 50.0 # 基流

# 3. 水库物理模型与规则
# 水库容量参数 (假设面积为常数，简化 V = A * h，这里直接用 V 表示水位)
V_max = 50000.0 # 防洪极限库容
V_target = 30000.0 # 发电/供水最优库容
V_min = 10000.0 # 死库容
V_init = 35000.0 # 初始库容 (汛前水位偏高)

# 发电效益函数 (非线性: 流量与水头(库容)的乘积)
def calc_power(Q_out, V):
    # 如果低于死水位，无法发电
    if V < V_min: return 0.0
    # 如果水头太低，发电效率差
    head_factor = (V - V_min) / (V_max - V_min)
    return Q_out * head_factor * 0.5 # MW

# 4. 传统静态调度策略 (Static Rule Curve)
# 规则：保持 V 在 V_target 附近。如果有雨进来了，水位升高了再放水。由于保守，最大只敢放 400
V_static = np.zeros(N)
Q_out_static = np.zeros(N)
Power_static = np.zeros(N)
V_static[0] = V_init

for i in range(1, N):
    # 计算可用水量
    V_avail = V_static[i-1] + Q_in[i] * dt * 3600 / 1000.0 # 把流量转为体积单位(千立方米)
    
    # 静态规则：试图放水回到 target
    if V_avail > V_target:
        # 放水，传统规则由于看不到下游情况，最高只敢泄 400 m3/s
        discharge_needed = (V_avail - V_target) * 1000.0 / (dt * 3600)
        Q_out_static[i] = min(discharge_needed, 400.0)
    else:
        # 保水发电
        Q_out_static[i] = 50.0 # 最小生态基流
        
    # 水库平衡更新
    V_static[i] = V_avail - Q_out_static[i] * dt * 3600 / 1000.0
    Power_static[i] = calc_power(Q_out_static[i], V_static[i])

# 5. 数字孪生智慧调度策略 (Smart Predictive Control)
# 规则：模型已经“看到了”未来 5 天的极值暴雨。提前在第 0~20 小时把水库腾空(预泄)，迎接洪峰。
V_smart = np.zeros(N)
Q_out_smart = np.zeros(N)
Power_smart = np.zeros(N)
V_smart[0] = V_init

for i in range(1, N):
    V_avail = V_smart[i-1] + Q_in[i] * dt * 3600 / 1000.0
    
    # 智能预泄逻辑 (极其激进地腾空库容)
    if i < 20: 
        # 看到暴雨要来，全开闸门以最大安全流量 600 预泄，直到逼近死水位
        if V_avail > V_min + 5000:
            Q_out_smart[i] = 600.0
        else:
            Q_out_smart[i] = 50.0
    elif 20 <= i < 40: 
        # 第一波洪峰来临，利用腾空的巨大库容吃掉它，只保持最小生态下泄 50，绝不给下游添乱
        Q_out_smart[i] = 50.0 
    elif 40 <= i < 60: 
        # 两波雨之间的间隙，趁下游河道空闲，再次全开闸门狂排
        Q_out_smart[i] = 600.0
    else: 
        # 面对主洪峰，全力憋水，直到逼近极限再泄洪
        if V_avail > V_max * 0.95:
            Q_out_smart[i] = 600.0 # 逼近防洪极限，必须开闸
        else:
            # 洪峰期，利用库容吃掉，保持较小的下泄量保护城市
            Q_out_smart[i] = 100.0 
            
    # 水库平衡更新
    V_smart[i] = V_avail - Q_out_smart[i] * dt * 3600 / 1000.0
    Power_smart[i] = calc_power(Q_out_smart[i], V_smart[i])

# 6. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# 图 A: 水库入流与两种调度的出流对比 (Hydrographs)
ax1.plot(time, Q_in, 'k--', linewidth=2, label='Inflow Hydrograph (From Predictor)')
ax1.plot(time, Q_out_static, 'r-', linewidth=2, label='Static Rule Outflow (Reactive)')
ax1.plot(time, Q_out_smart, 'b-', linewidth=3, label='Smart Control Outflow (Proactive)')
ax1.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax1.set_title('Reservoir Routing: Inflow vs Regulated Outflow', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 图 B: 水库容积/水位轨迹 (Storage Trajectories)
ax2.plot(time, V_static, 'r-', linewidth=2, label='Storage (Static)')
ax2.plot(time, V_smart, 'b-', linewidth=3, label='Storage (Smart Predictive)')
ax2.axhline(V_max, color='k', linestyle=':', linewidth=2, label='Flood Limit (Danger)')
ax2.axhline(V_target, color='g', linestyle='--', linewidth=2, label='Optimal Target')

# 标注漫坝危险
danger_idx = np.where(V_static > V_max)[0]
if len(danger_idx) > 0:
    ax2.plot(time[danger_idx], V_static[danger_idx], 'rx', markersize=8)
    ax2.annotate('OVERTOPPING DANGER!\nStatic rule failed to pre-release.', 
                 xy=(time[danger_idx[0]], V_max), xytext=(time[danger_idx[0]]-30, V_max+5000),
                 arrowprops=dict(facecolor='red', shrink=0.05))

ax2.set_ylabel('Reservoir Storage ($10^3 m^3$)', fontsize=12)
ax2.set_title('Reservoir Storage Dynamics (Flood Control)', fontsize=14)
ax2.legend(loc='lower left', ncol=2)
ax2.grid(True, linestyle='--', alpha=0.6)

# 图 C: 发电效益轨迹 (Hydropower Generation)
ax3.fill_between(time, 0, Power_static, color='red', alpha=0.3, label='Static Power Gen')
ax3.fill_between(time, 0, Power_smart, color='blue', alpha=0.3, label='Smart Power Gen')
ax3.plot(time, Power_static, 'r-', linewidth=2)
ax3.plot(time, Power_smart, 'b-', linewidth=2)
ax3.set_xlabel('Time (hours)', fontsize=12)
ax3.set_ylabel('Hydropower Output (MW)', fontsize=12)
ax3.set_title('Hydropower Generation (Economic Benefit)', fontsize=14)
ax3.legend(loc='upper right')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "smart_reservoir_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 统计指标
max_v_static = np.max(V_static)
max_v_smart = np.max(V_smart)
total_power_static = np.sum(Power_static) * dt
total_power_smart = np.sum(Power_smart) * dt
max_qout_static = np.max(Q_out_static)
max_qout_smart = np.max(Q_out_smart)

history = [
    {'Metric': 'Max Reservoir Storage ($10^3 m^3$)', 'Static Rule': round(max_v_static, 0), 'Smart Control': round(max_v_smart, 0), 'Evaluation': 'Smart saved dam from overtopping'},
    {'Metric': 'Peak Downstream Discharge ($m^3/s$)', 'Static Rule': round(max_qout_static, 1), 'Smart Control': round(max_qout_smart, 1), 'Evaluation': 'Smart utilized full safe capacity'},
    {'Metric': 'Total Energy Generated (MWh)', 'Static Rule': round(total_power_static, 1), 'Smart Control': round(total_power_smart, 1), 'Evaluation': 'Smart sacrificed power for safety'},
    {'Metric': 'Pre-release Volume', 'Static Rule': '0 (Reactive)', 'Smart Control': 'Massive (Proactive)', 'Evaluation': 'AI leveraged weather forecasts'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "reservoir_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch12: Smart Basin Management", "Diagram showing a dam with an AI brain. It receives weather forecasts from a satellite, predicts flood volume, and proactively opens gates to pre-release water before the storm hits.")

print("Files generated successfully.")
