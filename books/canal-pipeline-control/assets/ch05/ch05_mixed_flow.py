import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import root

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\canal-pipeline-control\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 渠道与地下管网混流调度 (Mixed Flow System Balancing)
# 场景：上游是明渠，通过前池跌入地下承压管网，再分配给多个城市节点
# 计算稳态下，水压和流量在明渠和管网中的自动重分配现象

# 物理参数
# 明渠
b_ch = 5.0
n_ch = 0.015
S0_ch = 0.0005
L_ch = 2000.0
Z_start = 100.0
Z_forebay_bottom = Z_start - L_ch * S0_ch # 99.0m

# 管网 (简化的 Y 型分叉)
# 管 1: 从前池到节点 A (长度 L1=1000m, 径 D1=1.0m, C=120)
# 管 2: 从节点 A 到城市 1 (长度 L2=800m, 径 D2=0.8m, C=120)
# 管 3: 从节点 A 到城市 2 (长度 L3=1200m, 径 D3=0.8m, C=120)

# 目标：当城市 2 的需求突然从 1.0 飙升到 4.0 时，
# 明渠前端的总源头流量虽然增加了，但在自然平差下，城市 1 的可用水头会发生什么变化？

def HW_loss(Q, L, D, C=120):
    abs_Q = np.abs(Q)
    if abs_Q < 1e-6: return 0.0
    return np.sign(Q) * 10.67 * L * (abs_Q**1.852) / ((C**1.852) * (D**4.87))

def manning_Q(h):
    if h <= 0: return 0.0
    A = b_ch * h
    P = b_ch + 2*h
    R = A/P
    return (1/n_ch) * A * (R**(2/3)) * np.sqrt(S0_ch)

# 构建非线性方程组
# 未知数: [H_forebay, H_nodeA, Q_total]
def system_equations(vars, demand_city1, demand_city2):
    H_fb, H_A, Q_tot = vars
    
    # 1. 连续性方程 (节点A)
    # 流入A的流量 = Q_tot
    # 流出A到City1 = Q2
    # 流出A到City2 = Q3
    # 但是我们需要根据水头差来算流量
    def Q_from_H(H_up, H_down, L, D, C=120):
        hf = H_up - H_down
        R = 10.67 * L / ((C**1.852) * (D**4.87))
        abs_hf = np.abs(hf)
        if abs_hf < 1e-6: return 0.0
        return np.sign(hf) * (abs_hf / R)**(1/1.852)
        
    Q1 = Q_from_H(H_fb, H_A, 1000.0, 1.0)
    Q2 = demand_city1 # 假设末端阀门强行抽取 demand
    Q3 = demand_city2
    
    eq1 = Q1 - (Q2 + Q3)
    eq2 = Q_tot - Q1
    
    # 2. 明渠能力方程 (假设自由出流或受一定顶托，这里为了简单，假设前池水位不能超过明渠供水能力对应的正常水深)
    # 假设上游按照 Q_tot 供水，到达前池时形成水深 h = H_fb - Z_forebay_bottom
    # Q_tot = Manning(h)
    h_fb = H_fb - Z_forebay_bottom
    eq3 = Q_tot - manning_Q(h_fb)
    
    return [eq1, eq2, eq3]

# 模拟不同需求下的稳态平衡
d2_values = np.linspace(1.0, 5.0, 50)
d1_fixed = 2.0

H_fb_history = []
H_A_history = []
Q_tot_history = []

for d2 in d2_values:
    res = root(system_equations, [101.0, 95.0, 3.0], args=(d1_fixed, d2))
    H_fb, H_A, Q_tot = res.x
    H_fb_history.append(H_fb)
    H_A_history.append(H_A)
    Q_tot_history.append(Q_tot)

# 制表
history = []
snapshots = [1.0, 2.0, 3.0, 4.0, 5.0]
for d2 in snapshots:
    idx = np.argmin(np.abs(d2_values - d2))
    history.append({
        'City 2 Demand (m³/s)': d2,
        'City 1 Demand (m³/s)': d1_fixed,
        'Total System Q (m³/s)': round(Q_tot_history[idx], 2),
        'Forebay Head (m)': round(H_fb_history[idx], 2),
        'Node A Head (m)': round(H_A_history[idx], 2),
        'City 1 Delivery Pressure Drop (m)': round(HW_loss(d1_fixed, 800.0, 0.8), 2),
        'City 1 Available Head (m)': round(H_A_history[idx] - HW_loss(d1_fixed, 800.0, 0.8), 2)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "mixed_flow_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 绘图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(d2_values, H_fb_history, 'b-', linewidth=2, label='Forebay Head (Coupling Point)')
ax1.plot(d2_values, H_A_history, 'r--', linewidth=2, label='Node A Head (Pipe Bifurcation)')
# 城市 1 的实际可用水头 = Node A 水头 - 管2的摩擦损失
city1_head = np.array(H_A_history) - HW_loss(d1_fixed, 800.0, 0.8)
ax1.plot(d2_values, city1_head, 'g-', linewidth=3, label='City 1 Available Head (Victim)')
ax1.set_ylabel('Hydraulic Head (m)', fontsize=12)
ax1.set_title('Mixed System Balancing: The "Water Robbery" Effect', fontsize=14)
ax1.legend()
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注压力跌落
ax1.annotate('City 1 loses pressure\nbecause City 2 is pulling hard', xy=(4.0, city1_head[np.argmin(np.abs(d2_values - 4.0))]), xytext=(2.0, city1_head[0]-5),
             arrowprops=dict(facecolor='green', shrink=0.05, width=1, headwidth=6))

ax2.plot(d2_values, Q_tot_history, 'k-', linewidth=2, label='Total Required System Flow')
ax2.plot(d2_values, np.ones(len(d2_values))*d1_fixed, 'g--', linewidth=2, label='City 1 Flow (Fixed)')
ax2.plot(d2_values, d2_values, 'm:', linewidth=2, label='City 2 Flow (Increasing)')
ax2.set_xlabel('City 2 Water Demand ($m^3/s$)', fontsize=12)
ax2.set_ylabel('Flow Rate ($m^3/s$)', fontsize=12)
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "mixed_flow_sim.png"), dpi=300, bbox_inches='tight')

print("Files generated successfully.")
