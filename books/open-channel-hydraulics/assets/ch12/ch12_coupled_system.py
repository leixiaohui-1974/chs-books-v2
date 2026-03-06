import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import fsolve

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch12"
os.makedirs(output_dir, exist_ok=True)

# 渠道-管道耦合系统 (Channel-Pipe Coupled System)
# 模拟明渠通过前池(过渡段)转入有压管道，最终排入下游水库的稳态耦合水力计算

# 参数设置
Q_target = 8.0   # 目标流量 m^3/s

# 1. 上游明渠参数 (梯形渠道)
b_ch = 3.0       # 底宽 m
m_ch = 1.0       # 边坡
n_ch = 0.015     # 糙率
S0_ch = 0.0005   # 底坡
Z_ch_start = 50.0 # 渠道起点高程 m
L_ch = 2000.0    # 渠道长度 m
Z_ch_end = Z_ch_start - L_ch * S0_ch # 渠道末端(前池底)高程 49.0m

# 2. 前池参数 (Forebay)
# 假设前池足够大，流速近似为0
# 进口处发生跌水，水位降落
loss_coeff_entrance = 0.5 # 管道进口损失系数

# 3. 下游有压管道参数 (圆形)
D_pipe = 1.5     # 管径 m
L_pipe = 1500.0  # 管长 m
f_pipe = 0.018   # 达西阻力系数
Z_pipe_end = 35.0 # 管道末端高程
loss_coeff_exit = 1.0 # 出口损失系数

# 4. 下游水库水位
Z_res = 40.0     # 下游水库恒定水位 m

# --- 计算过程 ---

# 步骤 1: 计算管道的水头损失 (从下游水库逆推至前池)
A_pipe = np.pi * (D_pipe**2) / 4.0
V_pipe = Q_target / A_pipe
head_velocity = V_pipe**2 / (2 * 9.81)

# hf = f * (L/D) * (V^2 / 2g)
hf_pipe = f_pipe * (L_pipe / D_pipe) * head_velocity
hm_pipe = (loss_coeff_entrance + loss_coeff_exit) * head_velocity
total_pipe_loss = hf_pipe + hm_pipe

# 前池必须维持的绝对水位 Z_forebay
Z_forebay = Z_res + total_pipe_loss
# 前池水深
h_forebay = Z_forebay - Z_ch_end

# 步骤 2: 计算明渠的正常水深和临界水深
def manning_eq(h):
    A = (b_ch + m_ch * h) * h
    P = b_ch + 2 * h * np.sqrt(1 + m_ch**2)
    R = A / P
    return (1/n_ch) * A * (R**(2/3)) * np.sqrt(S0_ch) - Q_target

h_normal = fsolve(manning_eq, 1.0)[0]

def critical_eq(h):
    A = (b_ch + m_ch * h) * h
    T = b_ch + 2 * m_ch * h
    return (Q_target**2 * T) / (9.81 * A**3) - 1.0

h_critical = fsolve(critical_eq, 1.0)[0]

# 步骤 3: 渠道水面曲线计算 (如果 h_forebay > h_normal，则是M1壅水曲线；否则是M2降水曲线)
# 使用直接步长法或标准步长法，这里为了演示，简化计算M区水面线
# 逆推法
x_points = [L_ch]
h_points = [h_forebay]
Z_points = [Z_forebay]

dx = -50.0
x_curr = L_ch
h_curr = h_forebay

while x_curr > 0:
    A1 = (b_ch + m_ch * h_curr) * h_curr
    P1 = b_ch + 2 * h_curr * np.sqrt(1 + m_ch**2)
    R1 = A1 / P1
    V1 = Q_target / A1
    E1 = h_curr + V1**2 / (2 * 9.81)
    Sf1 = (n_ch**2 * V1**2) / (R1**(4/3))
    
    h_next = h_curr - 0.05 if h_forebay > h_normal else h_curr + 0.05 # 猜测方向
    
    for _ in range(20):
        A2 = (b_ch + m_ch * h_next) * h_next
        P2 = b_ch + 2 * h_next * np.sqrt(1 + m_ch**2)
        R2 = A2 / P2
        V2 = Q_target / A2
        E2 = h_next + V2**2 / (2 * 9.81)
        Sf2 = (n_ch**2 * V2**2) / (R2**(4/3))
        
        Sf_avg = (Sf1 + Sf2) / 2.0
        # 逆推公式 (dx 是负的)
        target_E2 = E1 - S0_ch * dx + Sf_avg * dx
        error = E2 - target_E2
        
        if abs(error) < 1e-4: break
        h_next = h_next - error * 0.5
        
    x_curr += dx
    h_curr = h_next
    x_points.append(x_curr)
    h_points.append(h_curr)
    Z_points.append(Z_ch_start - x_curr * S0_ch + h_curr)

# 反转数组使之从上游到下游
x_points = x_points[::-1]
Z_points = Z_points[::-1]
Z_bottom_ch = [Z_ch_start - x * S0_ch for x in x_points]

# 提取关键点制作表格
history = []
Q_sweep = [4.0, 6.0, 8.0, 10.0, 12.0]
for q in Q_sweep:
    V_p = q / A_pipe
    hf = f_pipe * (L_pipe / D_pipe) * (V_p**2 / (2 * 9.81))
    hm = (loss_coeff_entrance + loss_coeff_exit) * (V_p**2 / (2 * 9.81))
    z_fb = Z_res + hf + hm
    
    def m_eq_temp(h_val):
        A_val = (b_ch + m_ch * h_val) * h_val
        P_val = b_ch + 2 * h_val * np.sqrt(1 + m_ch**2)
        R_val = A_val / P_val
        return (1/n_ch) * A_val * (R_val**(2/3)) * np.sqrt(S0_ch) - q
    hn_temp = fsolve(m_eq_temp, 1.0)[0]
    
    status = "Submerged (M1)" if z_fb - Z_ch_end > hn_temp else "Free Fall (M2)"
    
    history.append({
        'System Q (m³/s)': q,
        'Pipe Head Loss (m)': round(hf + hm, 2),
        'Forebay Water Elev Z (m)': round(z_fb, 2),
        'Channel Normal Depth (m)': round(hn_temp, 2),
        'Coupling Status': status
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "coupling_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 绘制耦合系统全景剖面图
plt.figure(figsize=(12, 6))

# 明渠部分
plt.plot(x_points, Z_points, 'b-', linewidth=2, label='Open Channel Water Surface')
plt.plot(x_points, Z_bottom_ch, 'k-', linewidth=3, label='Channel Bottom')

# 前池部分 (垂直虚线表示过渡)
plt.axvline(x=L_ch, color='gray', linestyle='--')

# 管道部分 (只画一条表示HGL/EGL的直线)
x_pipe = [L_ch, L_ch + L_pipe]
Z_pipe_hgl = [Z_forebay - head_velocity - loss_coeff_entrance*head_velocity, Z_res]
plt.plot(x_pipe, Z_pipe_hgl, 'c-.', linewidth=2, label='Pipe Hydraulic Grade Line (HGL)')
plt.plot([L_ch, L_ch+L_pipe], [Z_ch_end-D_pipe, Z_pipe_end], 'k-', linewidth=4, label='Underground Pipe')

# 下游水库
plt.fill_between([L_ch+L_pipe, L_ch+L_pipe+200], [Z_pipe_end, Z_pipe_end], [Z_res, Z_res], color='blue', alpha=0.3, label='Downstream Reservoir')

plt.xlabel('System Distance $x$ (m)', fontsize=12)
plt.ylabel('Elevation $Z$ (m)', fontsize=12)
plt.title(f'Channel-Pipe Coupled System Profile (Q = {Q_target} m³/s)', fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

# 添加标注
plt.annotate('Forebay\n(Coupling Node)', xy=(L_ch, Z_forebay), xytext=(L_ch-400, Z_forebay+5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

plt.savefig(os.path.join(output_dir, "coupled_system_profile.png"), dpi=300, bbox_inches='tight')

print("Files generated successfully.")
