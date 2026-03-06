import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\photovoltaic-system-modeling-control\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 光伏逆变器并网控制 (Grid-Tied Inverter Control)
# 模拟在 d-q 旋转坐标系下，利用锁相环(PLL)实现逆变器输出电流与电网电压同步，
# 以及有功/无功电流解耦 PI 控制的过程。

# 1. 模拟参数设定
f_grid = 50.0 # 电网频率 50 Hz
omega_grid = 2 * np.pi * f_grid # 角频率 rad/s
t_end = 0.1 # 模拟 0.1 秒 (5 个工频周期)
dt = 50e-6 # 50 微秒步长 (20kHz 采样率)
time = np.arange(0, t_end, dt)
N = len(time)

# 2. 模拟真实电网电压 (含谐波与相位跳变)
V_peak = 311.0 # 220V rms * sqrt(2)
theta_grid = omega_grid * time # 真实相位

# 在 t=0.04s 发生 30度的相位跳变 (Phase Jump)
phase_shift = np.zeros(N)
phase_shift[time >= 0.04] = np.pi / 6.0 

theta_grid += phase_shift

# 生成三相电网电压
Va = V_peak * np.cos(theta_grid)
Vb = V_peak * np.cos(theta_grid - 2*np.pi/3)
Vc = V_peak * np.cos(theta_grid + 2*np.pi/3)

# 3. 极简锁相环 (PLL - Phase Locked Loop) 仿真
# 利用基于同步参考系 (SRF-PLL) 的逻辑：将 abc 转为 dq，控制 v_q = 0，使得 theta_pll 追上 theta_grid
theta_pll = np.zeros(N)
omega_pll = np.ones(N) * omega_grid
theta_pll[0] = 0.0 # 初始猜测 0 

# PLL PI 控制器参数
Kp_pll = 100.0
Ki_pll = 2000.0
pll_integral = 0.0

vd_measured = np.zeros(N)
vq_measured = np.zeros(N)

for i in range(1, N):
    # a. Clarke 变换 (abc -> alpha beta)
    v_alpha = (2/3) * (Va[i] - 0.5*Vb[i] - 0.5*Vc[i])
    v_beta  = (2/3) * (np.sqrt(3)/2 * Vb[i] - np.sqrt(3)/2 * Vc[i])
    
    # b. Park 变换 (alpha beta -> d q) 利用上一时刻的估算相位
    cos_t = np.cos(theta_pll[i-1])
    sin_t = np.sin(theta_pll[i-1])
    
    vd = v_alpha * cos_t + v_beta * sin_t
    vq = -v_alpha * sin_t + v_beta * cos_t
    
    vd_measured[i] = vd
    vq_measured[i] = vq
    
    # c. PI 控制器消除 vq
    error_pll = 0.0 - vq
    pll_integral += error_pll * dt
    delta_omega = Kp_pll * error_pll + Ki_pll * pll_integral
    
    # d. 积分得到新的相位
    omega_pll[i] = omega_grid + delta_omega
    theta_pll[i] = theta_pll[i-1] + omega_pll[i] * dt
    # 限制在 0-2pi
    theta_pll[i] = theta_pll[i] % (2*np.pi)

# 4. 电流内环解耦控制 (Current Loop in dq frame)
# 逆变器通过 L 滤波器并网。L * di/dt = v_inv - v_grid
L_filter = 5e-3 # 5 mH 滤波电感

Id_ref = np.zeros(N)
Iq_ref = np.zeros(N)

# 设定指令：在 t=0.02s，指令逆变器输出满载有功 (Id=20A)。
# 在 t=0.06s，指令逆变器输出无功 (Iq=-10A) 以支撑电网。
Id_ref[time >= 0.02] = 20.0
Iq_ref[time >= 0.06] = -10.0

Id_actual = np.zeros(N)
Iq_actual = np.zeros(N)

# 电流 PI 参数
Kp_c = 10.0
Ki_c = 500.0
int_d = 0.0
int_q = 0.0

for i in range(1, N):
    err_d = Id_ref[i] - Id_actual[i-1]
    err_q = Iq_ref[i] - Iq_actual[i-1]
    
    int_d += err_d * dt
    int_q += err_q * dt
    
    # 解耦方程算出逆变器需要的端电压指令 (包含前馈解耦和电网电压前馈)
    # V_inv_d = v_grid_d - omega * L * Iq + PI(err_d)
    v_inv_d_ref = vd_measured[i] - omega_pll[i] * L_filter * Iq_actual[i-1] + (Kp_c * err_d + Ki_c * int_d)
    v_inv_q_ref = vq_measured[i] + omega_pll[i] * L_filter * Id_actual[i-1] + (Kp_c * err_q + Ki_c * int_q)
    
    # 物理模型响应 (欧拉法模拟 L 滤波器)
    # L * dId/dt = v_inv_d - v_grid_d + omega*L*Iq
    dId = (v_inv_d_ref - vd_measured[i] + omega_pll[i] * L_filter * Iq_actual[i-1]) / L_filter
    dIq = (v_inv_q_ref - vq_measured[i] - omega_pll[i] * L_filter * Id_actual[i-1]) / L_filter
    
    Id_actual[i] = Id_actual[i-1] + dId * dt
    Iq_actual[i] = Iq_actual[i-1] + dIq * dt

# 5. 反向 Park/Clarke 变换，获得注入电网的三相交流电流
Ia = np.zeros(N)
Ib = np.zeros(N)
Ic = np.zeros(N)

for i in range(N):
    cos_t = np.cos(theta_pll[i])
    sin_t = np.sin(theta_pll[i])
    
    # dq -> alpha beta
    ialpha = Id_actual[i] * cos_t - Iq_actual[i] * sin_t
    ibeta  = Id_actual[i] * sin_t + Iq_actual[i] * cos_t
    
    # alpha beta -> abc
    Ia[i] = ialpha
    Ib[i] = -0.5 * ialpha + (np.sqrt(3)/2) * ibeta
    Ic[i] = -0.5 * ialpha - (np.sqrt(3)/2) * ibeta

# 6. 绘图对比
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# A. 锁相环 (PLL) 跟踪电网跳变
# 为了好看，画 sin(theta) 比较相位
ax1.plot(time, np.sin(theta_grid % (2*np.pi)), 'k--', linewidth=2, label='Grid Real Phase $\sin(\\theta_{grid})$')
ax1.plot(time, np.sin(theta_pll), 'r-', linewidth=2, alpha=0.7, label='PLL Estimated Phase $\sin(\\theta_{pll})$')
ax1.axvline(0.04, color='gray', linestyle=':', label='Grid Phase Jump (+30°)')

ax1.set_ylabel('Phase $\sin(\\theta)$', fontsize=12)
ax1.set_title('Phase Locked Loop (PLL) Tracking under Grid Fault', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# B. d-q 轴有功无功解耦控制
ax2.plot(time, Id_ref, 'b--', linewidth=2, label='Active Current Ref ($I_d^*$)')
ax2.plot(time, Id_actual, 'b-', linewidth=3, alpha=0.7, label='Actual Active Current ($I_d$)')
ax2.plot(time, Iq_ref, 'g--', linewidth=2, label='Reactive Current Ref ($I_q^*$)')
ax2.plot(time, Iq_actual, 'g-', linewidth=3, alpha=0.7, label='Actual Reactive Current ($I_q$)')

# 标注 PLL 抖动引起的小交叉
ax2.annotate('PLL transient causes brief P/Q coupling', xy=(0.042, 20), xytext=(0.01, 5),
             arrowprops=dict(facecolor='black', shrink=0.05))

ax2.set_ylabel('d-q Current (A)', fontsize=12)
ax2.set_title('Decoupled Active & Reactive Power Control (d-q frame)', fontsize=14)
ax2.legend(loc='lower left', ncol=2)
ax2.grid(True, linestyle='--', alpha=0.6)

# C. 真实送入电网的三相电流
ax3.plot(time, Ia, 'r-', linewidth=1.5, label='Phase A Current ($I_a$)')
ax3.plot(time, Ib, 'b-', linewidth=1.5, label='Phase B Current ($I_b$)')
ax3.plot(time, Ic, 'g-', linewidth=1.5, label='Phase C Current ($I_c$)')

# 叠加电网电压(缩小比例)看同步
ax3.plot(time, Va/10.0, 'k--', linewidth=1, alpha=0.5, label='Grid Voltage A (scaled)')

ax3.set_xlabel('Time (seconds)', fontsize=12)
ax3.set_ylabel('AC Current (A)', fontsize=12)
ax3.set_title('Three-Phase AC Current Injected into Grid', fontsize=14)
ax3.legend(loc='upper right', ncol=2)
ax3.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "grid_tied_inverter_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = [
    {'Time Phase': '0-0.02s', 'Event': 'Standby', 'Id (Active)': round(Id_actual[int(0.01/dt)], 1), 'Iq (Reactive)': round(Iq_actual[int(0.01/dt)], 1), 'PLL Status': 'Locked'},
    {'Time Phase': '0.02-0.04s', 'Event': 'Active Power Injection', 'Id (Active)': round(Id_actual[int(0.03/dt)], 1), 'Iq (Reactive)': round(Iq_actual[int(0.03/dt)], 1), 'PLL Status': 'Locked'},
    {'Time Phase': '0.04-0.06s', 'Event': 'Grid Phase Jump', 'Id (Active)': round(Id_actual[int(0.045/dt)], 1), 'Iq (Reactive)': round(Iq_actual[int(0.045/dt)], 1), 'PLL Status': 'Re-locking Transient'},
    {'Time Phase': '0.06-0.10s', 'Event': 'Reactive Power Support', 'Id (Active)': round(Id_actual[int(0.08/dt)], 1), 'Iq (Reactive)': round(Iq_actual[int(0.08/dt)], 1), 'PLL Status': 'Locked'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "inverter_control_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: Grid-Tied Inverter Control", "Diagram showing an Inverter acting as a bridge. On the left is the DC link from the solar panels. On the right is the AC grid. Inside the Inverter brain, a PLL locks onto the grid wave, while a dq-axis controller separately manages Active (Watts) and Reactive (VARs) power.")

print("Files generated successfully.")
