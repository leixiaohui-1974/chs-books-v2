import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import root

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch11"
os.makedirs(output_dir, exist_ok=True)

# 简单环状管网平差计算 (Hardy Cross 方法 / 牛顿-拉夫逊法)

# 节点高程和需求 (N1, N2, N3)
# N1 是水库 (恒定水头 H1 = 100m)
# N2 是需水节点 (Q_demand_2 = 0.5 m3/s), 高程 Z2 = 50m
# N3 是需水节点 (Q_demand_3 = 0.3 m3/s), 高程 Z3 = 40m

# 管段参数 (L_i, D_i, C_hw: Hazen-Williams系数)
# P12: 连接 N1 到 N2, L=1000m, D=0.4m, C=120
# P23: 连接 N2 到 N3, L=800m, D=0.3m, C=120
# P13: 连接 N1 到 N3, L=1200m, D=0.35m, C=120

def hazen_williams_loss(Q, L, D, C=120):
    # hf = 10.67 * L * Q^1.852 / (C^1.852 * D^4.87)
    # 采用带有符号的 Q 以表示方向
    abs_Q = np.abs(Q)
    # 防止 Q=0 导致导数奇异
    if abs_Q < 1e-6:
        abs_Q = 1e-6
    hf = 10.67 * L * (abs_Q**1.852) / ((C**1.852) * (D**4.87))
    return np.sign(Q) * hf

# 目标函数：寻找节点 H2 和 H3 使得节点流量连续
def network_equations(H):
    H2, H3 = H
    H1 = 100.0
    
    # 根据水头差反算流量 (从公式 hf = R * Q^1.852 得到 Q = (hf/R)^(1/1.852))
    def calc_Q(H_from, H_to, L, D, C=120):
        hf = H_from - H_to
        R = 10.67 * L / ((C**1.852) * (D**4.87))
        abs_hf = np.abs(hf)
        if abs_hf < 1e-6:
            return 0.0
        Q_mag = (abs_hf / R)**(1/1.852)
        return np.sign(hf) * Q_mag

    Q12 = calc_Q(H1, H2, 1000.0, 0.4)
    Q23 = calc_Q(H2, H3, 800.0, 0.3)
    Q13 = calc_Q(H1, H3, 1200.0, 0.35)
    
    # 节点连续性方程: sum(Q_in) - sum(Q_out) - Q_demand = 0
    eq1 = Q12 - Q23 - 0.5 # N2
    eq2 = Q13 + Q23 - 0.3 # N3
    
    return [eq1, eq2]

# 求解稳态水头
res = root(network_equations, [90.0, 80.0])
H2_steady, H3_steady = res.x

# 计算稳态下的流量分布
def final_Q(H_from, H_to, L, D, C=120):
    hf = H_from - H_to
    R = 10.67 * L / ((C**1.852) * (D**4.87))
    Q_mag = (np.abs(hf) / R)**(1/1.852)
    return np.sign(hf) * Q_mag

Q12_s = final_Q(100.0, H2_steady, 1000.0, 0.4)
Q23_s = final_Q(H2_steady, H3_steady, 800.0, 0.3)
Q13_s = final_Q(100.0, H3_steady, 1200.0, 0.35)

# 生成一张展示随着节点 N2 需求量增加，管网水头和流量重分配的表格
Q2_demands = np.linspace(0.1, 1.5, 8)
history = []

for q2_d in Q2_demands:
    def temp_equations(H):
        H2, H3 = H
        H1 = 100.0
        Q12 = calc_Q(H1, H2, 1000.0, 0.4)
        Q23 = calc_Q(H2, H3, 800.0, 0.3)
        Q13 = calc_Q(H1, H3, 1200.0, 0.35)
        return [Q12 - Q23 - q2_d, Q13 + Q23 - 0.3]
    
    # 局部定义的 calc_Q
    def calc_Q(H_from, H_to, L, D, C=120):
        hf = H_from - H_to
        R = 10.67 * L / ((C**1.852) * (D**4.87))
        if np.abs(hf) < 1e-6: return 0.0
        return np.sign(hf) * (np.abs(hf) / R)**(1/1.852)
        
    temp_res = root(temp_equations, [90.0, 80.0])
    h2_val, h3_val = temp_res.x
    
    q12_val = calc_Q(100.0, h2_val, 1000.0, 0.4)
    q23_val = calc_Q(h2_val, h3_val, 800.0, 0.3)
    q13_val = calc_Q(100.0, h3_val, 1200.0, 0.35)
    
    history.append({
        'N2 Demand (m³/s)': round(q2_d, 2),
        'Head H2 (m)': round(h2_val, 2),
        'Head H3 (m)': round(h3_val, 2),
        'Flow Q12 (m³/s)': round(q12_val, 3),
        'Flow Q23 (m³/s)': round(q23_val, 3),
        'Flow Q13 (m³/s)': round(q13_val, 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "network_balancing_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 绘制需求变化与水头跌落曲线
demands = [row['N2 Demand (m³/s)'] for row in history]
h2_heads = [row['Head H2 (m)'] for row in history]
h3_heads = [row['Head H3 (m)'] for row in history]

plt.figure(figsize=(9, 6))
plt.plot(demands, h2_heads, 'bo-', linewidth=2, label='Node 2 Head (H2)')
plt.plot(demands, h3_heads, 'rs--', linewidth=2, label='Node 3 Head (H3)')
plt.axhline(y=100, color='k', linestyle=':', label='Reservoir Node 1 (H1=100m)')

plt.xlabel('Demand at Node 2 ($m^3/s$)', fontsize=12)
plt.ylabel('Pressure Head $H$ (m)', fontsize=12)
plt.title('Network Pressure Head Drop due to Demand Increase', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "network_head_drop.png"), dpi=300, bbox_inches='tight')

# 绘制流量重分配曲线
q12_flows = [row['Flow Q12 (m³/s)'] for row in history]
q23_flows = [row['Flow Q23 (m³/s)'] for row in history]
q13_flows = [row['Flow Q13 (m³/s)'] for row in history]

plt.figure(figsize=(9, 6))
plt.plot(demands, q12_flows, 'b-', linewidth=2.5, label='Main Pipe P12 (N1->N2)')
plt.plot(demands, q13_flows, 'g-', linewidth=2.5, label='Secondary Pipe P13 (N1->N3)')
plt.plot(demands, q23_flows, 'r--', linewidth=2, label='Cross Pipe P23 (N2->N3)')
plt.axhline(y=0, color='k', linewidth=1)

plt.xlabel('Demand at Node 2 ($m^3/s$)', fontsize=12)
plt.ylabel('Pipe Flow Rate $Q$ ($m^3/s$)', fontsize=12)
plt.title('Flow Redistribution in Looped Network', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, "network_flow_redistribution.png"), dpi=300, bbox_inches='tight')

print("Files generated successfully.")
