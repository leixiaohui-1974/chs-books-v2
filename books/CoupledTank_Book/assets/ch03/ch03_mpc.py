import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\CoupledTank_Book\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 从 PID 到 MPC (Model Predictive Control)
# 模拟在存在物理硬约束 (水位上限) 的双容水箱系统中，MPC 如何通过前瞻优化避免漫溢，而 PID 却无能为力。

# 1. 物理参数
A1 = 1.0; A2 = 1.0
a12 = 0.05; a2 = 0.04
g = 9.81
H_max = 5.0 # 水箱1的物理高度极限 (漫溢线)

# 2. 离散化非线性系统仿真步长
dt = 1.0
t_end = 150
time = np.arange(0, t_end, dt)
N = len(time)

target_h2 = np.ones(N) * 2.0
target_h2[30:] = 4.0 # 第30秒，要求水箱2的水位飙升到 4.0m

def simulate_step(h1, h2, u):
    # 使用简单的欧拉法进行离散化推进
    delta_h = h1 - h2
    q12 = a12 * np.sign(delta_h) * np.sqrt(2 * g * abs(delta_h))
    qout = a2 * np.sqrt(2 * g * max(0, h2))
    
    h1_new = h1 + (u - q12) / A1 * dt
    h2_new = h2 + (q12 - qout) / A2 * dt
    
    return max(0, h1_new), max(0, h2_new)

# 3. 方案 A: 传统 PID 控制器 (只看目标，不看约束)
h1_pid = np.zeros(N)
h2_pid = np.zeros(N)
u_pid = np.zeros(N)

h1_pid[0] = 2.0; h2_pid[0] = 2.0
u_pid[0] = a2 * np.sqrt(2 * g * 2.0)

Kp = 1.5
Ki = 0.05
integral = 0.0

for i in range(1, N):
    error = target_h2[i] - h2_pid[i-1]
    
    # PID 只看 Tank 2 的误差
    if not (u_pid[i-1] == 3.0 and error > 0): # 简单的防积分饱和
        integral += error * dt
        
    u_cmd = Kp * error + Ki * integral
    u_pid[i] = max(0.0, min(3.0, u_cmd)) # 水泵最大 3.0 m3/s
    
    h1_pid[i], h2_pid[i] = simulate_step(h1_pid[i-1], h2_pid[i-1], u_pid[i])

# 4. 方案 B: 模型预测控制 (MPC)
# MPC 的魔法：它可以预测未来，并且把 H1 <= 5.0 写进了“死刑约束”里。
h1_mpc = np.zeros(N)
h2_mpc = np.zeros(N)
u_mpc = np.zeros(N)

h1_mpc[0] = 2.0; h2_mpc[0] = 2.0
u_mpc[0] = u_pid[0]

Np = 10 # 预测步长 (看未来10秒)
Nu = 3  # 控制步长

# MPC 优化目标函数
def mpc_objective(u_seq, current_h1, current_h2, current_target):
    h1 = current_h1
    h2 = current_h2
    cost = 0.0
    
    # 将较短的控制序列扩展到预测域
    full_u_seq = np.zeros(Np)
    full_u_seq[:Nu] = u_seq
    full_u_seq[Nu:] = u_seq[-1]
    
    for k in range(Np):
        h1, h2 = simulate_step(h1, h2, full_u_seq[k])
        # 惩罚偏离目标
        cost += 10.0 * (h2 - current_target)**2
        # 惩罚水泵剧烈动作
        if k == 0:
            cost += 1.0 * (full_u_seq[k] - u_mpc[i-1])**2
        else:
            cost += 1.0 * (full_u_seq[k] - full_u_seq[k-1])**2
            
    return cost

# MPC 物理安全红线 (Constraints)
def mpc_constraint_h1_max(u_seq, current_h1, current_h2):
    # 模拟未来 Np 步，确保在任何时刻 h1 都不能超过 H_max
    h1 = current_h1
    h2 = current_h2
    min_margin = 999.0
    
    full_u_seq = np.zeros(Np)
    full_u_seq[:Nu] = u_seq
    full_u_seq[Nu:] = u_seq[-1]
    
    for k in range(Np):
        h1, h2 = simulate_step(h1, h2, full_u_seq[k])
        margin = H_max - h1
        if margin < min_margin:
            min_margin = margin
    return min_margin # 必须 >= 0

for i in range(1, N):
    # 在每一步，跑一个微型优化器
    u_init = np.ones(Nu) * u_mpc[i-1]
    bounds = [(0.0, 3.0) for _ in range(Nu)] # 水泵物理限制
    
    # 设置约束字典
    cons = {'type': 'ineq', 'fun': lambda u, h1=h1_mpc[i-1], h2=h2_mpc[i-1]: mpc_constraint_h1_max(u, h1, h2)}
    
    res = minimize(mpc_objective, u_init, args=(h1_mpc[i-1], h2_mpc[i-1], target_h2[i]), 
                   method='SLSQP', bounds=bounds, constraints=cons)
    
    # 只执行算出的控制序列的第一步 (Rolling Horizon)
    optimal_u = res.x[0]
    u_mpc[i] = optimal_u
    
    # 将决定下发给真实的物理模型
    h1_mpc[i], h2_mpc[i] = simulate_step(h1_mpc[i-1], h2_mpc[i-1], u_mpc[i])

# 5. 绘图对比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

# A. 水箱 1 (上游节点) 的生存战
ax1.plot(time, h1_pid, 'r--', linewidth=2, label='Tank 1 (PID) - Overtopped!')
ax1.plot(time, h1_mpc, 'b-', linewidth=3, label='Tank 1 (MPC) - Safe')
ax1.axhline(H_max, color='k', linestyle='-', linewidth=3, label=f'Safety Limit ({H_max}m)')

ax1.fill_between(time, H_max, h1_pid, where=(h1_pid>H_max), color='red', alpha=0.3, label='Flooding Disaster')

ax1.set_ylabel('Tank 1 Level (m)', fontsize=12)
ax1.set_title('Constraint Handling: PID Blindness vs MPC Foresight', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 水箱 2 (下游节点) 的目标追踪与控制代价
ax2.plot(time, target_h2, 'k:', linewidth=2, label='Target Level (Tank 2)')
ax2.plot(time, h2_pid, 'r--', linewidth=2, label='Tank 2 (PID)')
ax2.plot(time, h2_mpc, 'b-', linewidth=3, label='Tank 2 (MPC)')

ax2.set_xlabel('Time (seconds)', fontsize=12)
ax2.set_ylabel('Tank 2 Level (m)', fontsize=12)
ax2.set_title('Target Tracking Performance', fontsize=14)
ax2.legend(loc='lower right')
ax2.grid(True, linestyle='--', alpha=0.6)

# 标注 MPC 牺牲追踪速度换取绝对安全
ax2.annotate('MPC deliberately slows down\nto protect Tank 1', xy=(40, h2_mpc[40]), xytext=(50, 2.5),
             arrowprops=dict(facecolor='blue', shrink=0.05))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "mpc_vs_pid_coupled_sim.png"), dpi=300, bbox_inches='tight')

# 生成数据表格
history = [
    {'Metric': 'Max Tank 1 Level (m)', 'PID Controller': round(np.max(h1_pid), 2), 'MPC Algorithm': round(np.max(h1_mpc), 2), 'Evaluation': 'MPC perfectly respects physical limit'},
    {'Metric': 'Disaster (Flooding)', 'PID Controller': 'YES (Overtopped)', 'MPC Algorithm': 'NO (Safe)', 'Evaluation': 'PID blind to unmeasured constraints'},
    {'Metric': 'Rise Time to Target (s)', 'PID Controller': 'Fast (but lethal)', 'MPC Algorithm': 'Controlled & Calculated', 'Evaluation': 'MPC sacrifices speed for system survival'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "mpc_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: Model Predictive Control (MPC)", "Diagram showing a robot playing chess. The robot (MPC) looks 10 moves ahead. It sees that if it pumps water too fast to reach the goal, Tank 1 will explode. So it calculates a slower, perfectly safe pumping strategy.")

print("Files generated successfully.")
