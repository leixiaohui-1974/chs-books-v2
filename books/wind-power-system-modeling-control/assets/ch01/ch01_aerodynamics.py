import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\wind-power-system-modeling-control\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 风机空气动力学与最大功率点跟踪 (MPPT)
# 模拟风力发电机在不同风速下的功率曲线 (Cp-Lambda) 以及变桨距控制 (Pitch Control)

# 1. 物理参数
rho = 1.225 # 空气密度 kg/m^3
R = 40.0 # 叶片半径 m
A = np.pi * R**2 # 扫风面积 m^2

# 2. Cp (风能利用系数) 模型计算函数
# 典型近似公式：Cp(lambda, beta) = c1 * (c2/lambda_i - c3*beta - c4) * exp(-c5/lambda_i) + c6*lambda
def calc_cp(lam, beta):
    c1 = 0.5176
    c2 = 116.0
    c3 = 0.4
    c4 = 5.0
    c5 = 21.0
    c6 = 0.0068
    
    # 避免除以零
    lam_i = 1.0 / (1.0 / (lam + 0.08 * beta) - 0.035 / (beta**3 + 1.0))
    
    cp = c1 * (c2 / lam_i - c3 * beta - c4) * np.exp(-c5 / lam_i) + c6 * lam
    return max(0.0, cp)

# 3. 绘制 Cp-Lambda 曲线
lambda_vals = np.linspace(0.1, 15, 100)
beta_vals = [0.0, 5.0, 10.0, 15.0, 20.0]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

for b in beta_vals:
    cp_vals = [calc_cp(l, b) for l in lambda_vals]
    ax1.plot(lambda_vals, cp_vals, linewidth=2, label=f'Pitch angle $\\beta$={b}°')

# 找到最佳叶尖速比 (Optimal TSR)
lam_opt = lambda_vals[np.argmax([calc_cp(l, 0) for l in lambda_vals])]
cp_max = calc_cp(lam_opt, 0)

ax1.plot(lam_opt, cp_max, 'r*', markersize=12, label=f'Max $C_p$={cp_max:.3f} at $\\lambda_{{opt}}$={lam_opt:.1f}')
ax1.set_xlabel('Tip Speed Ratio ($\\lambda$)', fontsize=12)
ax1.set_ylabel('Power Coefficient ($C_p$)', fontsize=12)
ax1.set_title('$C_p-\\lambda$ Characteristics for different pitch angles', fontsize=14)
ax1.legend()
ax1.grid(True, linestyle='--', alpha=0.6)

# 4. 模拟 MPPT 运行过程与功率限制
v_wind = np.linspace(3, 25, 100) # 风速 3m/s 到 25m/s
P_rated = 2.0 * 1e6 # 额定功率 2 MW

P_mech_mppt = np.zeros_like(v_wind) # 不限制的理论最大功率
P_mech_actual = np.zeros_like(v_wind) # 实际输出功率
omega_mppt = np.zeros_like(v_wind)
beta_ctrl = np.zeros_like(v_wind)

for i, v in enumerate(v_wind):
    # a. 假设完美追踪最佳叶尖速比 (MPPT)
    omega_opt = lam_opt * v / R
    omega_mppt[i] = omega_opt * 60 / (2 * np.pi) # 转换为 rpm
    
    # b. 计算机械功率 P = 0.5 * rho * A * v^3 * Cp_max
    p_avail = 0.5 * rho * A * v**3 * cp_max
    P_mech_mppt[i] = p_avail
    
    # c. 实施控制策略：达到额定功率后进行变桨 (Pitch Control) 限制功率
    if p_avail > P_rated:
        P_mech_actual[i] = P_rated
        # 寻找能够刚好输出额定功率的桨距角 beta (简化：保持转速在额定风速下的转速)
        # 实际风机此时保持恒定转速和恒定功率
        omega_rated = omega_mppt[np.where(P_mech_mppt > P_rated)[0][0]]
        lam_rated = omega_rated * (2 * np.pi / 60) * R / v
        
        # 牛顿法或简单扫描找 beta
        target_cp = P_rated / (0.5 * rho * A * v**3)
        b_test = 0.0
        while calc_cp(lam_rated, b_test) > target_cp and b_test < 30.0:
            b_test += 0.1
        beta_ctrl[i] = b_test
    else:
        P_mech_actual[i] = p_avail
        beta_ctrl[i] = 0.0 # 额定风速以下，桨距角为0，全力发电

# 图 B: 风机运行功率曲线
ax2_twin = ax2.twinx()
ax2.plot(v_wind, P_mech_mppt / 1e6, 'k--', linewidth=2, label='Theoretical Max Power')
ax2.plot(v_wind, P_mech_actual / 1e6, 'b-', linewidth=3, label='Actual Regulated Power')
ax2.axvline(x=v_wind[np.where(P_mech_actual >= P_rated)[0][0]], color='r', linestyle=':', label='Rated Wind Speed')

ax2_twin.plot(v_wind, beta_ctrl, 'g-.', linewidth=2, label='Pitch Angle $\\beta$')

ax2.set_xlabel('Wind Speed (m/s)', fontsize=12)
ax2.set_ylabel('Mechanical Power (MW)', fontsize=12, color='b')
ax2_twin.set_ylabel('Pitch Angle (°)', fontsize=12, color='g')
ax2.set_title('Wind Turbine Power Curve & Pitch Control', fontsize=14)

lines_1, labels_1 = ax2.get_legend_handles_labels()
lines_2, labels_2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "aerodynamics_mppt_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
# 选择几个典型风速点：切入风速附近、额定风速附近、切出风速附近
history = []
snapshots_v = [5.0, 8.0, 11.0, 15.0, 20.0]

for v_snap in snapshots_v:
    idx = np.argmin(np.abs(v_wind - v_snap))
    state = "MPPT" if P_mech_actual[idx] < P_rated else "Pitch Control"
    history.append({
        'Wind Speed (m/s)': round(v_snap, 1),
        'Rotor Speed (rpm)': round(omega_mppt[idx] if state == "MPPT" else omega_mppt[np.where(P_mech_actual >= P_rated)[0][0]], 1),
        'Pitch Angle β (°)': round(beta_ctrl[idx], 1),
        'Power Output (MW)': round(P_mech_actual[idx]/1e6, 3),
        'Operating Mode': state
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "aerodynamics_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch01: Wind Turbine Aerodynamics", "Diagram illustrating air flowing through a wind turbine rotor. It shows the tip speed ratio (lambda) relationship and how the blade pitch angle (beta) is turned mechanically to spill excess wind energy at high speeds.")

print("Files generated successfully.")
