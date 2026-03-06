import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import fsolve, root

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch13"
os.makedirs(output_dir, exist_ok=True)

# 泵站-管道-明渠-倒虹吸 综合耦合水力计算 (Comprehensive System)
# 这是一个全要素耦合稳态模型，包含水泵做功、管道摩擦、明渠非均匀流和倒虹吸损失

# 系统参数
Z_source = 20.0       # 取水库水位 m
Z_dest = 120.0        # 终点水库水位 m
Q_target = 5.0        # 目标流量 m^3/s

# 1. 提水泵站与压力管道
D_pipe1 = 1.2         # 压水管径 m
L_pipe1 = 1000.0      # 压水管长 m
f_pipe1 = 0.02        # 压水管阻力系数
# 水泵特性曲线: H_pump = H_shutoff - k * Q^2
H_shutoff = 130.0     # 水泵关死扬程 m
k_pump = 0.5          # 水泵内阻系数

# 2. 高位出水池 (过渡节点 1)
# 假定出水池水位必须满足下游渠道的需要

# 3. 引水明渠 (矩形)
b_ch = 4.0            # 渠道底宽 m
n_ch = 0.015          # 渠道糙率
S0_ch = 0.001         # 渠道底坡
L_ch = 3000.0         # 渠道长度 m
Z_ch_start = 110.0    # 渠道起点底高程 m
Z_ch_end = Z_ch_start - L_ch * S0_ch # 107.0m

# 4. 倒虹吸管与前池 (过渡节点 2)
D_pipe2 = 1.0         # 倒虹吸管径 m
L_pipe2 = 800.0       # 倒虹吸管长 m
f_pipe2 = 0.018       # 倒虹吸阻力系数
K_minor_2 = 1.5       # 倒虹吸局部损失系数和

# --- 耦合求解逻辑 ---
# 这是一个极其复杂的两端定水位的系统，流量是由系统自然平衡决定的！
# 我们需要写一个函数，输入猜测流量 Q，看最终推导出的起点水库水位是否等于 Z_source

def evaluate_system(Q):
    if Q <= 0: return -999.0
    
    # a. 倒虹吸管计算 (从下游 Z_dest 往上推)
    A_p2 = np.pi * D_pipe2**2 / 4
    V_p2 = Q / A_p2
    hf_p2 = f_pipe2 * (L_pipe2 / D_pipe2) * (V_p2**2 / (2*9.81))
    hm_p2 = K_minor_2 * (V_p2**2 / (2*9.81))
    Z_forebay = Z_dest + hf_p2 + hm_p2
    
    # b. 明渠计算 (从前池 Z_forebay 往上推)
    # 计算明渠正常水深
    def manning_eq(h):
        A = b_ch * h
        P = b_ch + 2*h
        R = A/P
        return (1/n_ch)*A*(R**(2/3))*np.sqrt(S0_ch) - Q
    hn = fsolve(manning_eq, 1.0)[0]
    
    h_end = Z_forebay - Z_ch_end
    # 使用简化的一阶步长法逆推渠道起点水深
    h_curr = h_end
    # 为了简化演示，这里用单步近似或均值计算，因为 L=3000 不算长
    A1 = b_ch * h_curr; R1 = A1/(b_ch+2*h_curr); V1 = Q/A1
    Sf1 = (n_ch**2 * V1**2) / (R1**(4/3))
    
    # 假设上游水深为 hn 附近，用牛顿法解能量方程
    def energy_eq_ch(h_up):
        A2 = b_ch * h_up; R2 = A2/(b_ch+2*h_up); V2 = Q/A2
        Sf2 = (n_ch**2 * V2**2) / (R2**(4/3))
        Sf_avg = (Sf1 + Sf2)/2.0
        E1 = h_curr + V1**2/(2*9.81)
        E2 = h_up + V2**2/(2*9.81)
        # E2 - E1 = (S0 - Sf_avg) * dx (这里从上游往下游算，dx是正的 L_ch)
        # 但我们是从下游反推上游，所以：
        return E2 - (E1 + (S0_ch - Sf_avg)*L_ch)
        
    h_start = fsolve(energy_eq_ch, hn)[0]
    Z_pool_up = Z_ch_start + h_start
    
    # c. 水泵与压力管道计算 (从高位水池往水源推)
    A_p1 = np.pi * D_pipe1**2 / 4
    V_p1 = Q / A_p1
    hf_p1 = f_pipe1 * (L_pipe1 / D_pipe1) * (V_p1**2 / (2*9.81))
    
    # 泵需要提供的净扬程 H_req
    H_req = Z_pool_up - Z_source + hf_p1
    
    # d. 泵实际能提供的扬程
    H_act = H_shutoff - k_pump * Q**2
    
    # 残差
    return H_req - H_act

# 寻找系统自然平衡流量
Q_balance = fsolve(evaluate_system, 5.0)[0]

# --- 提取平衡状态下的系统全剖面数据 ---
# 重新计算平衡点各参数
Q = Q_balance
A_p2 = np.pi * D_pipe2**2 / 4; V_p2 = Q / A_p2
hf_p2 = f_pipe2 * (L_pipe2 / D_pipe2) * (V_p2**2 / (2*9.81))
hm_p2 = K_minor_2 * (V_p2**2 / (2*9.81))
Z_forebay = Z_dest + hf_p2 + hm_p2

A1 = b_ch * (Z_forebay - Z_ch_end); R1 = A1/(b_ch+2*(Z_forebay - Z_ch_end)); V1 = Q/A1
Sf1 = (n_ch**2 * V1**2) / (R1**(4/3))
def energy_eq_ch_final(h_up):
    A2 = b_ch * h_up; R2 = A2/(b_ch+2*h_up); V2 = Q/A2
    Sf2 = (n_ch**2 * V2**2) / (R2**(4/3))
    Sf_avg = (Sf1 + Sf2)/2.0
    E1 = (Z_forebay - Z_ch_end) + V1**2/(2*9.81)
    E2 = h_up + V2**2/(2*9.81)
    return E2 - (E1 + (S0_ch - Sf_avg)*L_ch)
h_start = fsolve(energy_eq_ch_final, 1.0)[0]
Z_pool_up = Z_ch_start + h_start

A_p1 = np.pi * D_pipe1**2 / 4; V_p1 = Q / A_p1
hf_p1 = f_pipe1 * (L_pipe1 / D_pipe1) * (V_p1**2 / (2*9.81))
H_pump = H_shutoff - k_pump * Q**2

# 生成全景剖面图绘图数据
# 空间横坐标
x_coords = [0, 0, L_pipe1, L_pipe1, L_pipe1+L_ch, L_pipe1+L_ch, L_pipe1+L_ch+L_pipe2]

# 结构底高程
z_struct = [Z_source, Z_source, Z_ch_start, Z_ch_start, Z_ch_end, Z_ch_end-5, Z_dest-5]

# 水面/能量线 (HGL)
z_hgl = [Z_source, Z_source + H_pump, Z_pool_up, Z_pool_up, Z_forebay, Z_forebay, Z_dest]

plt.figure(figsize=(14, 7))

# 绘制结构与地形
plt.plot(x_coords, z_struct, 'k-', linewidth=4, label='Engineering Structure (Pipes & Channel Bottom)')

# 绘制水力坡度线
plt.plot(x_coords, z_hgl, 'b-', linewidth=3, label='Hydraulic Grade Line (Water Surface / Pressure Head)')

# 标注水泵
plt.annotate(f'Pump Station\n+ {H_pump:.1f}m Head', xy=(0, Z_source + H_pump/2), xytext=(200, Z_source + 20),
             arrowprops=dict(facecolor='red', shrink=0.05))

# 标注流量
plt.text(1500, Z_pool_up + 5, f'System Balanced Discharge: {Q_balance:.2f} m³/s', fontsize=14, color='darkblue', fontweight='bold')

plt.xlabel('Distance from Source $x$ (m)', fontsize=12)
plt.ylabel('Elevation $Z$ (m)', fontsize=12)
plt.title('Comprehensive System Hydraulic Profile (Pump -> Pipe -> Channel -> Siphon)', fontsize=15)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

plt.savefig(os.path.join(output_dir, "comprehensive_profile.png"), dpi=300, bbox_inches='tight')

# 生成各节点特征表格
history = [
    {'Node': '01_Source Reservoir', 'Elevation Z (m)': Z_source, 'Head/Loss (m)': 0.0, 'Flow Q (m³/s)': round(Q_balance, 2)},
    {'Node': '02_Pump Outlet', 'Elevation Z (m)': round(Z_source + H_pump, 2), 'Head/Loss (m)': f'+{round(H_pump, 2)} (Added)', 'Flow Q (m³/s)': round(Q_balance, 2)},
    {'Node': '03_High Pool (Pipe 1 End)', 'Elevation Z (m)': round(Z_pool_up, 2), 'Head/Loss (m)': f'-{round(hf_p1, 2)} (Friction)', 'Flow Q (m³/s)': round(Q_balance, 2)},
    {'Node': '04_Forebay (Channel End)', 'Elevation Z (m)': round(Z_forebay, 2), 'Head/Loss (m)': f'-{round(Z_pool_up - Z_forebay, 2)} (Channel)', 'Flow Q (m³/s)': round(Q_balance, 2)},
    {'Node': '05_Dest Reservoir (Pipe 2 End)', 'Elevation Z (m)': Z_dest, 'Head/Loss (m)': f'-{round(hf_p2+hm_p2, 2)} (Siphon)', 'Flow Q (m³/s)': round(Q_balance, 2)}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "system_balance_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
