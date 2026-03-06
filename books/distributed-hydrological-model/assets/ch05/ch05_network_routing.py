import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\distributed-hydrological-model\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 分布式河网拓扑与曼宁运动波汇流模拟 (Distributed River Network Routing)
# 场景：一个包含 Y 型交叉的 3 段河网系统，上游两个子流域产生洪水，在交汇处叠加后流向下游出口
# 演示分布式模型中必须遵循的拓扑计算顺序 (DAG: Directed Acyclic Graph)

# 物理参数设定
dt = 60.0 # 时间步长 60 秒
t_end = 7200.0 # 模拟 2 小时 (120 min)
time = np.arange(0, t_end, dt)
N = len(time)

# 河段物理参数 (基于一维显式运动波非线性模型: A = alpha * Q^beta)
# 假设河道为宽浅矩形，曼宁公式 Q = (1/n) * B * (A/B)^(5/3) * S^(1/2) -> A = [ (n*B^(2/3)) / sqrt(S) ]^(3/5) * Q^(3/5)
# 则 beta = 0.6, alpha = [n / (sqrt(S) * B^(2/3))]^0.6
n_manning = 0.03

# Reach 1 (左上游支流)
B1 = 10.0; S1 = 0.005; L1 = 3000.0
alpha1 = (n_manning / (np.sqrt(S1) * B1**(2/3)))**0.6

# Reach 2 (右上游支流)
B2 = 8.0; S2 = 0.008; L2 = 2500.0
alpha2 = (n_manning / (np.sqrt(S2) * B2**(2/3)))**0.6

# Reach 3 (下游干流, 承接 1 和 2)
B3 = 20.0; S3 = 0.002; L3 = 5000.0
alpha3 = (n_manning / (np.sqrt(S3) * B3**(2/3)))**0.6

beta = 0.6

# 上游强迫边界条件 (输入洪峰)
# Reach 1 遭遇短促剧烈暴雨
Q_in_1 = np.ones(N) * 2.0 # 初始基流
Q_in_1[10:30] = 50.0

# Reach 2 遭遇较平缓的长历时降雨
Q_in_2 = np.ones(N) * 1.5
Q_in_2[20:60] = 30.0

# 运动波数值求解容易产生振荡，此处我们使用在水文中更稳定且广泛使用的
# 马斯金根法 (Muskingum Method) 来演示拓扑汇流的延迟和坦化。
def solve_routing(Q_inbound, K, X):
    Q_out = np.zeros(N)
    Q_out[0] = Q_inbound[0]
    
    # dt = 1 min = 60s
    # K is in minutes
    dt_min = dt / 60.0
    denominator = K * (1 - X) + 0.5 * dt_min
    C0 = (-K * X + 0.5 * dt_min) / denominator
    C1 = (K * X + 0.5 * dt_min) / denominator
    C2 = (K * (1 - X) - 0.5 * dt_min) / denominator
    
    for i in range(1, N):
        Q_out[i] = C0 * Q_inbound[i] + C1 * Q_inbound[i-1] + C2 * Q_out[i-1]
        Q_out[i] = max(Q_out[i], 0.0)
    return Q_out

# 1. 拓扑层级 1 计算 (上游无依赖支流，可以并行计算)
# 假定 Reach 1 水流较快，K=15min, X=0.2
Q_out_1 = solve_routing(Q_in_1, K=15.0, X=0.2)

# 假定 Reach 2 水流较慢，K=25min, X=0.1
Q_out_2 = solve_routing(Q_in_2, K=25.0, X=0.1)

# 2. 拓扑汇聚节点 (Junction)
# 质量守恒: Q_in_3 = Q_out_1 + Q_out_2
Q_in_3 = Q_out_1 + Q_out_2

# 3. 拓扑层级 2 计算 (必须等上游算完才能算)
# 下游主干流，K=30min, X=0.25
Q_out_3 = solve_routing(Q_in_3, K=30.0, X=0.25)

time_min = time / 60.0 # 分钟

# 绘图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 子图1: 上游支流演进
ax1.plot(time_min, Q_in_1, 'r:', linewidth=2, label='Reach 1 Inflow')
ax1.plot(time_min, Q_out_1, 'r-', linewidth=2, label='Reach 1 Outflow (to Junction)')
ax1.plot(time_min, Q_in_2, 'b:', linewidth=2, label='Reach 2 Inflow')
ax1.plot(time_min, Q_out_2, 'b-', linewidth=2, label='Reach 2 Outflow (to Junction)')

ax1.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax1.set_title('Upstream Branches (Independent Routing)', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# 子图2: 交汇与下游干流演进
ax2.plot(time_min, Q_in_3, 'k--', linewidth=2.5, label='Junction Total Inflow (R1 + R2)')
ax2.plot(time_min, Q_out_3, 'g-', linewidth=3, label='Reach 3 Outflow (Basin Outlet)')

# 标注坦化
ax2.annotate('Flood Peak Attenuation\n& Translation', xy=(np.argmax(Q_out_3)*dt/60, np.max(Q_out_3)), 
             xytext=(np.argmax(Q_in_3)*dt/60 + 10, np.max(Q_in_3)),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

ax2.set_xlabel('Time (minutes)', fontsize=12)
ax2.set_ylabel('Discharge ($m^3/s$)', fontsize=12)
ax2.set_title('Main Channel Routing (Post-Junction)', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "river_network_routing.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
snapshots = [15, 35, 55, 75, 95]

for t_idx in snapshots: # t_idx 是分钟
    idx = int(t_idx * 60 / dt)
    history.append({
        'Time (min)': t_idx,
        'Reach 1 Outflow (m³/s)': round(Q_out_1[idx], 1),
        'Reach 2 Outflow (m³/s)': round(Q_out_2[idx], 1),
        'Junction Inflow (m³/s)': round(Q_in_3[idx], 1),
        'Basin Outlet Flow (m³/s)': round(Q_out_3[idx], 1)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "network_routing_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 用 python 生成一张不带依赖的简单的网络拓扑架构图
def create_topology_schematic(path):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (1024, 512), color=(245, 245, 245))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 1014, 502], outline=(50, 50, 50), width=3)
    
    try: font = ImageFont.truetype('arial.ttf', 24)
    except: font = ImageFont.load_default()
    
    # Draw Y shape network
    # R1
    d.line([(200, 100), (500, 250)], fill=(200, 50, 50), width=10)
    d.text((250, 120), "Reach 1 (Tier 1)\nL=3km, fast", fill=(200, 50, 50), font=font)
    # R2
    d.line([(200, 400), (500, 250)], fill=(50, 50, 200), width=10)
    d.text((250, 360), "Reach 2 (Tier 1)\nL=2.5km, slow", fill=(50, 50, 200), font=font)
    # R3
    d.line([(500, 250), (900, 250)], fill=(50, 150, 50), width=15)
    d.text((600, 210), "Reach 3 (Tier 2)\nL=5km, main channel", fill=(50, 150, 50), font=font)
    
    # Node
    d.ellipse([(480, 230), (520, 270)], fill=(100, 100, 100))
    d.text((450, 190), "Junction Node", fill=(0,0,0), font=font)
    
    img.save(path)

create_topology_schematic(os.path.join(output_dir, "problem_nano.png"))

print("Files generated successfully.")
