import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 氧化铝蒸发工序控制架构仿真 (Alumina Evaporation Control Architecture)
# 模拟系统面临大时滞 (Time Delay) 和进料波动时，
# 传统单回路 PID (Decentralized PID) 与 集中式模型预测控制 (MPC) 的表现差异。

# 1. 模拟参数设定
N = 100 # 模拟时间步 100 分钟
time = np.arange(0, N)

# 系统存在 5 分钟的纯时滞 (Dead time / Delay)
delay = 5 

# 进料浓度扰动 (Disturbance)
feed_conc = np.ones(N) * 140.0
feed_conc[20:60] = 130.0 # 突然变稀
feed_conc[60:] = 145.0   # 突然变浓

# 目标出料浓度
target_conc = 240.0

# 2. 简化的被控对象模型 (FOPTD - First Order Plus Time Delay)
# y(t) = (K * u(t-d) + Kd * d(t-d)) / (tau * s + 1)
# 用离散差分方程近似
def process_dynamics(y_prev, u_delayed, d_delayed):
    tau = 10.0 # 惯性时间常数
    # u 是蒸汽量 (基准 50t/h), d 是进料浓度
    # 蒸汽越多，出料越浓；进料越稀，出料越稀
    gain_u = 2.0 
    gain_d = 1.6
    
    # 平衡点附近线性化
    u_delta = u_delayed - 50.0
    d_delta = d_delayed - 140.0
    
    y_steady = 240.0 + gain_u * u_delta + gain_d * d_delta
    y_new = y_prev + (y_steady - y_prev) / tau
    return y_new

# 3. 场景 A: 传统单回路 PID 控制
y_pid = np.ones(N) * 240.0
u_pid = np.ones(N) * 50.0

# PID 参数 (由于大时滞，PI参数必须调得极其保守，否则会剧烈震荡)
Kp = 0.5
Ki = 0.05
integral_error = 0.0

for t in range(1, N):
    # 模拟物理过程 (使用历史数据模拟时滞)
    u_eff = u_pid[t-delay] if t >= delay else 50.0
    d_eff = feed_conc[t-delay] if t >= delay else 140.0
    y_pid[t] = process_dynamics(y_pid[t-1], u_eff, d_eff)
    
    # 计算误差
    error = target_conc - y_pid[t]
    integral_error += error
    
    # PID 控制律
    delta_u = Kp * error + Ki * integral_error
    u_pid[t] = 50.0 + delta_u
    # 阀门开度限制
    u_pid[t] = max(20.0, min(u_pid[t], 80.0))

# 4. 场景 B: 集中式模型预测控制 (Simplified MPC)
# 假定 MPC 拥有完美的前馈预知能力，并且能够提前预判时滞
y_mpc = np.ones(N) * 240.0
u_mpc = np.ones(N) * 50.0

for t in range(1, N):
    u_eff = u_mpc[t-delay] if t >= delay else 50.0
    d_eff = feed_conc[t-delay] if t >= delay else 140.0
    y_mpc[t] = process_dynamics(y_mpc[t-1], u_eff, d_eff)
    
    # 极其简化的 MPC 前馈+时滞补偿逻辑
    # 如果 MPC 能提前看到 d 将在未来发生变化，它会提前动作
    # 真实 MPC 会求解二次规划，这里直接用前馈解算加上未来目标预测
    future_d = feed_conc[min(t + delay, N-1)] # 看到未来的扰动
    
    # 求解需要的稳态控制量: 240 = 240 + gain_u * (u_req - 50) + gain_d * (future_d - 140)
    # => gain_u * (u_req - 50) = -gain_d * (future_d - 140)
    # => u_req = 50 - (gain_d / gain_u) * (future_d - 140)
    gain_u = 2.0; gain_d = 1.6
    u_req = 50.0 - (gain_d / gain_u) * (future_d - 140.0)
    
    # 加上一点反馈微调消除稳态误差
    error = target_conc - y_mpc[t]
    u_mpc[t] = u_req + 0.1 * error
    u_mpc[t] = max(20.0, min(u_mpc[t], 80.0))

# 5. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 进料扰动 (Disturbance)
ax1.plot(time, feed_conc, 'k--', linewidth=2, label='Feed Concentration Disturbance')
ax1.set_ylabel('Feed Conc. (g/L)', fontsize=12)
ax1.set_title('External Disturbance: Unstable Upstream Process', fontsize=14)
ax1.legend(loc='lower left')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. 出料浓度追踪对比 (Output Concentration)
ax2.plot(time, y_pid, 'r-', linewidth=2, label='Traditional PID (Reactive)')
ax2.plot(time, y_mpc, 'b-', linewidth=3, label='MPC with Feedforward (Proactive)')
ax2.axhline(target_conc, color='g', linestyle=':', linewidth=3, label='Target Setpoint')
ax2.axhspan(238, 242, color='green', alpha=0.1, label='Strict Quality Window')

ax2.set_ylabel('Output Conc. (g/L)', fontsize=12)
ax2.set_title('Control Performance: Quality Window Violation', fontsize=14)
ax2.legend(loc='lower left')
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 控制动作对比 (Control Action - Steam Valve)
ax3.plot(time, u_pid, 'r-', linewidth=2, label='PID Steam Action')
ax3.plot(time, u_mpc, 'b-', linewidth=2, label='MPC Steam Action')

ax3.annotate('MPC anticipates delay\nand acts beforehand', xy=(15, u_mpc[15]), xytext=(5, 65),
             arrowprops=dict(facecolor='blue', shrink=0.05))

ax3.set_xlabel('Time (Minutes)', fontsize=12)
ax3.set_ylabel('Steam Flow (t/h)', fontsize=12)
ax3.set_title('Control Effort: Reactive oscillation vs Proactive adjustment', fontsize=14)
ax3.legend(loc='upper right')
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "mpc_vs_pid_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 性能统计
mae_pid = np.mean(np.abs(y_pid - target_conc))
mae_mpc = np.mean(np.abs(y_mpc - target_conc))
tv_pid = np.sum(np.abs(np.diff(u_pid))) # 总变差，衡量阀门磨损
tv_mpc = np.sum(np.abs(np.diff(u_mpc)))

history = [
    {'Metric': 'Mean Absolute Error (g/L)', 'Traditional PID': round(mae_pid, 2), 'Intelligent MPC': round(mae_mpc, 2), 'Improvement': f"{(mae_pid - mae_mpc)/mae_pid*100:.1f}% tighter quality"},
    {'Metric': 'Max Deviation from Target', 'Traditional PID': round(np.max(np.abs(y_pid - target_conc)), 2), 'Intelligent MPC': round(np.max(np.abs(y_mpc - target_conc)), 2), 'Improvement': 'Avoided Off-spec Product'},
    {'Metric': 'Valve Total Variation (Wear)', 'Traditional PID': round(tv_pid, 1), 'Intelligent MPC': round(tv_mpc, 1), 'Improvement': 'Less valve hunting'},
    {'Metric': 'Response Type to Delay', 'Traditional PID': 'Reactive (Oscillates)', 'Intelligent MPC': 'Proactive (Anticipates)', 'Improvement': 'Broken the delay curse'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "control_strategy_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: MPC vs PID Architecture", "Diagram showing a brain (MPC algorithm) looking ahead through a mathematical model window to predict future states, sending early commands to a steam valve to perfectly counteract a wave of incoming disturbance.")

print("Files generated successfully.")
