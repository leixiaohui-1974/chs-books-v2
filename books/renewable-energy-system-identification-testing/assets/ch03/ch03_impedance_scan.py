"""
第3章仿真：并网逆变器阻抗扫频与奈奎斯特稳定性分析
模拟弱电网条件下逆变器输出阻抗的频率扫描，
并用奈奎斯特判据评估系统稳定裕度。
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

# ---------- 系统参数 ----------
# 逆变器参数 (典型3kW单相并网)
L_inv = 3.0e-3      # 逆变器侧电感 (H)
R_inv = 0.1          # 逆变器侧电阻 (Ohm)
C_f = 10e-6          # 滤波电容 (F)
L_g_weak = 5.0e-3    # 弱电网等效电感 (H) — SCR约2
L_g_strong = 0.5e-3  # 强电网等效电感 (H) — SCR约20
R_g = 0.05           # 电网侧电阻 (Ohm)

# PLL参数
Kp_pll = 1.8
Ki_pll = 50.0

# 电流环PI控制器
Kp_i = 10.0
Ki_i = 500.0

# 频率扫描范围
f_scan = np.logspace(0, 4, 500)  # 1 Hz to 10 kHz
omega = 2 * np.pi * f_scan
s = 1j * omega

# ---------- 逆变器输出阻抗模型 ----------
# 简化为：Z_inv(s) = (Kp_i + Ki_i/s) * (L_inv*s + R_inv) / (1 + (Kp_i + Ki_i/s))
# 考虑PLL影响的修正阻抗

Z_pi = Kp_i + Ki_i / s  # 电流环PI
Z_L = L_inv * s + R_inv  # 逆变器电感阻抗

# 开环传递函数
G_ol = Z_pi / Z_L
# 闭环后的等效输出阻抗
Z_inv = Z_L * (1 + G_ol) / G_ol

# PLL对阻抗的影响（在低频段引入负电阻效应）
H_pll = (Kp_pll * s + Ki_pll) / (s**2 + Kp_pll * s + Ki_pll)
# PLL耦合项（简化模型）
Z_inv_with_pll = Z_inv * (1 - 0.3 * H_pll)

# ---------- 电网阻抗 ----------
Z_grid_weak = L_g_weak * s + R_g
Z_grid_strong = L_g_strong * s + R_g

# ---------- 奈奎斯特比 L(s) = Z_grid/Z_inv ----------
L_weak = Z_grid_weak / Z_inv_with_pll
L_strong = Z_grid_strong / Z_inv_with_pll

# ---------- 伯德图 ----------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 阻抗幅频
ax1 = axes[0, 0]
ax1.loglog(f_scan, np.abs(Z_inv_with_pll), '#1565C0', linewidth=2, label='逆变器阻抗 |Z_inv|')
ax1.loglog(f_scan, np.abs(Z_grid_weak), '#FF7043', linewidth=2, label='电网阻抗(弱) |Z_grid|')
ax1.loglog(f_scan, np.abs(Z_grid_strong), '#4CAF50', linewidth=2, linestyle='--', label='电网阻抗(强) |Z_grid|')
ax1.set_xlabel('频率 (Hz)')
ax1.set_ylabel('阻抗幅值 (Ohm)')
ax1.set_title('阻抗幅频特性')
ax1.legend()
ax1.grid(True, which='both', alpha=0.3)

# 阻抗相频
ax2 = axes[0, 1]
ax2.semilogx(f_scan, np.angle(Z_inv_with_pll, deg=True), '#1565C0', linewidth=2, label='逆变器相角')
ax2.semilogx(f_scan, np.angle(Z_grid_weak, deg=True), '#FF7043', linewidth=2, label='弱电网相角')
ax2.semilogx(f_scan, np.angle(Z_grid_strong, deg=True), '#4CAF50', linewidth=2, linestyle='--', label='强电网相角')
ax2.set_xlabel('频率 (Hz)')
ax2.set_ylabel('相角 (度)')
ax2.set_title('阻抗相频特性')
ax2.legend()
ax2.grid(True, which='both', alpha=0.3)
ax2.set_ylim([-180, 180])

# 奈奎斯特图（弱电网）
ax3 = axes[1, 0]
ax3.plot(np.real(L_weak), np.imag(L_weak), '#FF7043', linewidth=2, label='弱电网')
ax3.plot(-1, 0, 'rx', markersize=12, markeredgewidth=3, label='临界点(-1,0)')
circle = plt.Circle((0, 0), 1, fill=False, color='gray', linestyle='--', alpha=0.5)
ax3.add_patch(circle)
ax3.set_xlabel('实部')
ax3.set_ylabel('虚部')
ax3.set_title('奈奎斯特图 — 弱电网(SCR=2)')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_xlim([-3, 2])
ax3.set_ylim([-2, 2])
ax3.set_aspect('equal')

# 奈奎斯特图（强电网）
ax4 = axes[1, 1]
ax4.plot(np.real(L_strong), np.imag(L_strong), '#4CAF50', linewidth=2, label='强电网')
ax4.plot(-1, 0, 'rx', markersize=12, markeredgewidth=3, label='临界点(-1,0)')
circle2 = plt.Circle((0, 0), 1, fill=False, color='gray', linestyle='--', alpha=0.5)
ax4.add_patch(circle2)
ax4.set_xlabel('实部')
ax4.set_ylabel('虚部')
ax4.set_title('奈奎斯特图 — 强电网(SCR=20)')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.set_xlim([-1, 1])
ax4.set_ylim([-1, 1])
ax4.set_aspect('equal')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "impedance_nyquist.png"), dpi=200)
plt.close()

# ---------- 计算稳定裕度 ----------
# 幅值交叉频率（|L(jw)|=1的点）
def find_gain_crossover(L_ratio, freqs):
    mag = np.abs(L_ratio)
    crossings = []
    for i in range(len(mag)-1):
        if (mag[i] - 1) * (mag[i+1] - 1) < 0:
            # 线性插值
            f_cross = freqs[i] + (freqs[i+1] - freqs[i]) * (1 - mag[i]) / (mag[i+1] - mag[i])
            phase_cross = np.angle(L_ratio[i], deg=True)
            crossings.append((f_cross, phase_cross))
    return crossings

# 相位裕度
crossings_weak = find_gain_crossover(L_weak, f_scan)
crossings_strong = find_gain_crossover(L_strong, f_scan)

# 到(-1,0)的最小距离
dist_weak = np.min(np.abs(L_weak - (-1 + 0j)))
dist_strong = np.min(np.abs(L_strong - (-1 + 0j)))

print("=" * 60)
print("第3章仿真结果：逆变器阻抗扫频与奈奎斯特分析")
print("=" * 60)

print(f"\n逆变器参数:")
print(f"  L_inv = {L_inv*1e3:.1f} mH, R_inv = {R_inv} Ohm")
print(f"  C_f = {C_f*1e6:.0f} uF")
print(f"  电流环: Kp={Kp_i}, Ki={Ki_i}")
print(f"  PLL: Kp={Kp_pll}, Ki={Ki_pll}")

print(f"\n弱电网 (L_g={L_g_weak*1e3:.1f}mH, SCR~2):")
if crossings_weak:
    for fc, pc in crossings_weak:
        pm = 180 + pc
        print(f"  增益交叉频率 = {fc:.1f} Hz, 相位裕度 = {pm:.1f} deg")
print(f"  奈奎斯特最小距离 = {dist_weak:.3f}")
print(f"  稳定性: {'不稳定(裕度不足)' if dist_weak < 0.3 else '条件稳定'}")

print(f"\n强电网 (L_g={L_g_strong*1e3:.1f}mH, SCR~20):")
if crossings_strong:
    for fc, pc in crossings_strong:
        pm = 180 + pc
        print(f"  增益交叉频率 = {fc:.1f} Hz, 相位裕度 = {pm:.1f} deg")
print(f"  奈奎斯特最小距离 = {dist_strong:.3f}")
print(f"  稳定性: {'稳定' if dist_strong > 0.5 else '条件稳定'}")

print(f"\n频率扫描范围: {f_scan[0]:.0f} Hz ~ {f_scan[-1]:.0f} Hz")
print(f"扫描点数: {len(f_scan)}")
