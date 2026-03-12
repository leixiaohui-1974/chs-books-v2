"""
第6章仿真：风电场站一次调频与次同步振荡（SSO）扫频分析
模拟风电场站对电网频率阶跃的响应，以及
次同步频率范围内的阻尼特性扫频评估。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ========== Part 1: 一次调频阶跃响应 ==========
# 风电场参数
P_farm_rated = 100e6     # 100MW风电场
n_turbines = 50          # 50台2MW机组
droop = 0.05             # 下垂系数 5%
P_initial = 0.8 * P_farm_rated  # 初始出力80%
P_reserve = P_farm_rated - P_initial  # 备用容量20%

# 调频模型参数
H_virtual = 6.0         # 虚拟惯量常数 (s)
T_pitch = 2.0           # 变桨响应时间常数 (s)
f_nom = 50.0             # 额定频率 (Hz)

# 频率阶跃事件
dt = 0.01
T_total = 60.0
time = np.arange(0, T_total, dt)
N = len(time)

# 电网频率跌落 (模拟大机组跳闸)
delta_f = np.zeros(N)
for i in range(N):
    t = time[i]
    if t < 5.0:
        delta_f[i] = 0
    elif t < 5.5:
        delta_f[i] = -0.5 * (t - 5.0) / 0.5  # 0.5s内跌落0.5Hz
    elif t < 30.0:
        # 系统调频后逐渐恢复
        delta_f[i] = -0.5 * np.exp(-(t - 5.5) / 15.0)
    else:
        delta_f[i] = -0.5 * np.exp(-24.5 / 15.0)

f_grid = f_nom + delta_f

# 风电场调频响应
delta_P = np.zeros(N)
P_output = np.zeros(N)

for i in range(1, N):
    # 下垂控制: delta_P_ref = -(1/droop) * (delta_f / f_nom) * P_farm_rated
    delta_P_ref = -(1.0 / droop) * (delta_f[i] / f_nom) * P_farm_rated
    delta_P_ref = np.clip(delta_P_ref, 0, P_reserve)  # 限制在备用容量内

    # 一阶惯性环节模拟变桨延迟
    delta_P[i] = delta_P[i-1] + (delta_P_ref - delta_P[i-1]) / T_pitch * dt

    P_output[i] = P_initial + delta_P[i]

# ========== Part 2: 次同步振荡(SSO)扫频 ==========
# 扫频范围：5-45 Hz（次同步频率）
f_sso = np.linspace(5, 45, 200)
omega_sso = 2 * np.pi * f_sso

# 风电场等效阻抗模型（简化Norton等效）
# 考虑变流器控制、PLL和机械振荡模式

# 机械扭振频率
f_torsional = [16.5, 25.3, 32.8]  # Hz (典型三阶扭振模式)
damping_ratios = [0.02, 0.015, 0.01]  # 阻尼比

# 电气阻抗（变流器控制贡献）
R_conv = 0.1  # 等效电阻 (p.u.)
L_conv = 0.15  # 等效电抗 (p.u.)

# 总阻抗 = 电气阻抗 + 机械振荡模式耦合
Z_total = np.zeros(len(f_sso), dtype=complex)

for i, f in enumerate(f_sso):
    s = 1j * 2 * np.pi * f

    # 基础电气阻抗
    Z_elec = R_conv + L_conv * s / (2 * np.pi * f_nom)

    # 机械模式耦合（每个扭振模式贡献一个谐振）
    Z_mech = 0
    for f_t, zeta in zip(f_torsional, damping_ratios):
        omega_t = 2 * np.pi * f_t
        omega = 2 * np.pi * f
        # 二阶振荡环节
        Z_mech += 0.05 * omega_t**2 / (omega_t**2 - omega**2 + 2j * zeta * omega_t * omega)

    Z_total[i] = Z_elec + Z_mech

# 阻尼指标：实部为正=正阻尼（稳定），实部为负=负阻尼（不稳定）
R_effective = np.real(Z_total)
X_effective = np.imag(Z_total)

# ---------- 绘图 ----------
fig = plt.figure(figsize=(16, 14))

# 子图1：频率事件与调频响应
ax1 = fig.add_subplot(3, 2, 1)
ax1.plot(time, f_grid, '#FF7043', linewidth=2)
ax1.axhline(f_nom, color='k', linestyle='--', alpha=0.3)
ax1.axhline(f_nom - 0.2, color='r', linestyle='--', alpha=0.3, label='0.2Hz死区')
ax1.set_ylabel('电网频率 (Hz)')
ax1.set_title('电网频率跌落事件')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2 = fig.add_subplot(3, 2, 2)
ax2.plot(time, P_output / 1e6, '#1565C0', linewidth=2, label='风电场出力')
ax2.axhline(P_initial / 1e6, color='k', linestyle='--', alpha=0.3, label='初始出力')
ax2.axhline(P_farm_rated / 1e6, color='r', linestyle='--', alpha=0.3, label='额定容量')
ax2.set_ylabel('有功功率 (MW)')
ax2.set_title('风电场一次调频响应')
ax2.legend()
ax2.grid(True, alpha=0.3)

ax3 = fig.add_subplot(3, 2, 3)
ax3.plot(time, delta_P / 1e6, '#4CAF50', linewidth=2)
ax3.set_ylabel('增发功率 (MW)')
ax3.set_xlabel('时间 (s)')
ax3.set_title('调频增发功率')
ax3.grid(True, alpha=0.3)

# 子图4：SSO扫频 - 阻抗幅值
ax4 = fig.add_subplot(3, 2, 4)
ax4.semilogy(f_sso, np.abs(Z_total), '#1565C0', linewidth=2)
for f_t in f_torsional:
    ax4.axvline(f_t, color='r', linestyle='--', alpha=0.5)
ax4.set_xlabel('频率 (Hz)')
ax4.set_ylabel('|Z| (p.u.)')
ax4.set_title('风电场次同步阻抗幅频特性')
ax4.grid(True, alpha=0.3)
ax4.annotate('扭振模式1\n16.5Hz', xy=(16.5, np.abs(Z_total[np.argmin(np.abs(f_sso-16.5))])),
            xytext=(20, 2), arrowprops=dict(arrowstyle='->', color='red'))

# 子图5：SSO扫频 - 等效电阻（阻尼指标）
ax5 = fig.add_subplot(3, 2, 5)
ax5.plot(f_sso, R_effective, '#FF7043', linewidth=2)
ax5.axhline(0, color='k', linewidth=1)
ax5.fill_between(f_sso, R_effective, 0, where=R_effective < 0,
                  alpha=0.3, color='red', label='负阻尼区(不稳定)')
ax5.fill_between(f_sso, R_effective, 0, where=R_effective >= 0,
                  alpha=0.3, color='green', label='正阻尼区(稳定)')
ax5.set_xlabel('频率 (Hz)')
ax5.set_ylabel('等效电阻 Re[Z] (p.u.)')
ax5.set_title('次同步频段等效电阻（阻尼指标）')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 子图6：SSO扫频 - 奈奎斯特图
ax6 = fig.add_subplot(3, 2, 6)
ax6.plot(R_effective, X_effective, '#7B1FA2', linewidth=2)
ax6.plot(R_effective[0], X_effective[0], 'go', markersize=8, label=f'起点({f_sso[0]:.0f}Hz)')
ax6.plot(R_effective[-1], X_effective[-1], 'rs', markersize=8, label=f'终点({f_sso[-1]:.0f}Hz)')
ax6.axvline(0, color='k', linewidth=0.5)
ax6.axhline(0, color='k', linewidth=0.5)
ax6.set_xlabel('Re[Z] (p.u.)')
ax6.set_ylabel('Im[Z] (p.u.)')
ax6.set_title('次同步阻抗奈奎斯特图')
ax6.legend()
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "freq_response_sso.png"), dpi=200)
plt.close()

# ---------- 输出KPI ----------
print("=" * 60)
print("第6章仿真结果：风电场站调频与SSO扫频")
print("=" * 60)

print(f"\n=== 一次调频测试 ===")
print(f"风电场容量: {P_farm_rated/1e6:.0f} MW ({n_turbines}台)")
print(f"初始出力: {P_initial/1e6:.0f} MW ({P_initial/P_farm_rated*100:.0f}%)")
print(f"下垂系数: {droop*100:.0f}%")
print(f"频率跌落: {np.min(delta_f):.2f} Hz")

# 调频KPI
delta_P_max = np.max(delta_P)
t_resp_idx = np.where(delta_P >= 0.1 * delta_P_max)[0]
t_response = time[t_resp_idx[0]] - 5.0 if len(t_resp_idx) > 0 else float('inf')

t_peak_idx = np.argmax(delta_P)
t_peak = time[t_peak_idx] - 5.0

print(f"最大增发功率: {delta_P_max/1e6:.2f} MW ({delta_P_max/P_farm_rated*100:.1f}%)")
print(f"响应时间(10%): {t_response:.2f} s")
print(f"达到峰值时间: {t_peak:.2f} s")

# 调频速率
delta_P_rate = np.max(np.diff(delta_P) / dt) / 1e6
print(f"最大功率变化率: {delta_P_rate:.2f} MW/s")

print(f"\n=== 次同步振荡扫频 ===")
print(f"扫频范围: {f_sso[0]:.0f}-{f_sso[-1]:.0f} Hz")
print(f"扭振模式频率: {f_torsional} Hz")
print(f"扭振模式阻尼比: {damping_ratios}")

# 负阻尼频段
neg_damp_regions = []
in_neg = False
for i in range(len(f_sso)):
    if R_effective[i] < 0 and not in_neg:
        start = f_sso[i]
        in_neg = True
    elif (R_effective[i] >= 0 or i == len(f_sso)-1) and in_neg:
        end = f_sso[i-1]
        neg_damp_regions.append((start, end))
        in_neg = False

print(f"\n负阻尼频段 (SSO风险区):")
for start, end in neg_damp_regions:
    min_R = np.min(R_effective[(f_sso >= start) & (f_sso <= end)])
    print(f"  {start:.1f} - {end:.1f} Hz, 最小等效电阻: {min_R:.4f} p.u.")

# 阻尼最差的模式
worst_idx = np.argmin(R_effective)
print(f"\n阻尼最差频率: {f_sso[worst_idx]:.1f} Hz")
print(f"最差等效电阻: {R_effective[worst_idx]:.4f} p.u.")
print(f"对应阻抗幅值: {np.abs(Z_total[worst_idx]):.4f} p.u.")
