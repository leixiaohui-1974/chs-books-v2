"""
第4章仿真：电力系统短路故障分析
演示：对称分量法求解三相短路和单相接地短路电流
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os
import json

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# 系统: 无限大电源 → 变压器 → 线路 → 短路点
# 基准: SB=100MVA, VB=110kV
#
# 正序阻抗: X1 = X_G1 + X_T1 + X_L1 = 0.05 + 0.10 + 0.15 = 0.30 pu
# 负序阻抗: X2 = 0.30 pu (近似等于正序)
# 零序阻抗: X0 = 0.05 + 0.10 + 0.45 = 0.60 pu (零序线路阻抗约为正序3倍)
# 电源电压: E = 1.0 pu
# ============================================================

print("=" * 60)
print("电力系统短路故障分析 (对称分量法)")
print("=" * 60)

SB = 100  # MVA
VB = 110  # kV
IB = SB / (np.sqrt(3) * VB)  # 基准电流 kA
print(f"\n基准值: SB={SB} MVA, VB={VB} kV, IB={IB:.4f} kA")

# 序阻抗
X1 = 0.30  # 正序
X2 = 0.30  # 负序
X0 = 0.60  # 零序
E = 1.0    # 电源电压 pu

print(f"\n序阻抗 (标幺值):")
print(f"  正序 X1 = {X1} pu")
print(f"  负序 X2 = {X2} pu")
print(f"  零序 X0 = {X0} pu")

# 算子
a = np.exp(1j * 2 * np.pi / 3)  # 120°旋转算子
a2 = a * a

print(f"\n旋转算子: a = {a:.4f}")
print(f"          a^2 = {a2:.4f}")

# ============================================================
# 1. 三相短路 (对称短路)
# ============================================================
print("\n" + "=" * 60)
print("1. 三相短路分析")
print("=" * 60)

I1_3ph = E / (1j * X1)  # 正序电流
I_3ph_pu = abs(I1_3ph)
I_3ph_kA = I_3ph_pu * IB

print(f"  正序电流 I1 = E/jX1 = {I1_3ph:.4f} pu")
print(f"  三相短路电流 |I_3ph| = {I_3ph_pu:.4f} pu = {I_3ph_kA:.4f} kA")

# 冲击电流 (考虑非周期分量)
Ksh = 1.8  # 冲击系数
I_impulse = np.sqrt(2) * Ksh * I_3ph_kA
print(f"  冲击电流 ish = √2 * Ksh * I = {I_impulse:.4f} kA (Ksh={Ksh})")

# ============================================================
# 2. 单相接地短路 (A相)
# ============================================================
print("\n" + "=" * 60)
print("2. 单相接地短路 (A相接地)")
print("=" * 60)

# 边界条件: Ia1 = Ia2 = Ia0 = E / j(X1+X2+X0)
I_seq_1ph = E / (1j * (X1 + X2 + X0))
I_1ph_A = 3 * I_seq_1ph  # Ia = 3*Ia0
I_1ph_pu = abs(I_1ph_A)
I_1ph_kA = I_1ph_pu * IB

print(f"  各序电流 I1=I2=I0 = E/j(X1+X2+X0) = {I_seq_1ph:.4f} pu")
print(f"  A相短路电流 Ia = 3*I0 = {abs(I_1ph_A):.4f} pu = {I_1ph_kA:.4f} kA")

# 各相电流 (用对称分量合成)
Ia = I_seq_1ph + I_seq_1ph + I_seq_1ph  # I0+I1+I2, 各序相等
Ib = I_seq_1ph + a2 * I_seq_1ph + a * I_seq_1ph
Ic = I_seq_1ph + a * I_seq_1ph + a2 * I_seq_1ph

print(f"\n  相电流:")
print(f"    Ia = {abs(Ia):.4f}∠{np.degrees(np.angle(Ia)):.1f}° pu")
print(f"    Ib = {abs(Ib):.4f}∠{np.degrees(np.angle(Ib)):.1f}° pu")
print(f"    Ic = {abs(Ic):.4f}∠{np.degrees(np.angle(Ic)):.1f}° pu")

# ============================================================
# 3. 两相短路 (B-C相)
# ============================================================
print("\n" + "=" * 60)
print("3. 两相短路 (B-C相短路)")
print("=" * 60)

# 边界条件: I1 = -I2 = E/j(X1+X2), I0 = 0
I1_2ph = E / (1j * (X1 + X2))
I2_2ph = -I1_2ph
I0_2ph = 0

Ia_2ph = I0_2ph + I1_2ph + I2_2ph
Ib_2ph = I0_2ph + a2 * I1_2ph + a * I2_2ph
Ic_2ph = I0_2ph + a * I1_2ph + a2 * I2_2ph

I_2ph_pu = abs(Ib_2ph)
I_2ph_kA = I_2ph_pu * IB

print(f"  序电流: I1={I1_2ph:.4f}, I2={I2_2ph:.4f}, I0={I0_2ph}")
print(f"  |Ib| = |Ic| = {I_2ph_pu:.4f} pu = {I_2ph_kA:.4f} kA")
print(f"  |Ia| = {abs(Ia_2ph):.6f} pu (理论为0)")

# ============================================================
# 4. 两相接地短路 (B-C相接地)
# ============================================================
print("\n" + "=" * 60)
print("4. 两相接地短路 (B-C相接地)")
print("=" * 60)

# I1 = E / j[X1 + X2*X0/(X2+X0)]
X_parallel = (X2 * X0) / (X2 + X0)
I1_2phg = E / (1j * (X1 + X_parallel))
# I2 = -I1 * jX0/(j(X2+X0))
I2_2phg = -I1_2phg * X0 / (X2 + X0)
I0_2phg = -I1_2phg * X2 / (X2 + X0)

Ia_2phg = I0_2phg + I1_2phg + I2_2phg
Ib_2phg = I0_2phg + a2 * I1_2phg + a * I2_2phg
Ic_2phg = I0_2phg + a * I1_2phg + a2 * I2_2phg

print(f"  X2//X0 = {X_parallel:.4f} pu")
print(f"  序电流: I1={abs(I1_2phg):.4f}pu, I2={abs(I2_2phg):.4f}pu, I0={abs(I0_2phg):.4f}pu")
print(f"  |Ia| = {abs(Ia_2phg):.6f} pu (理论为0)")
print(f"  |Ib| = {abs(Ib_2phg):.4f} pu = {abs(Ib_2phg)*IB:.4f} kA")
print(f"  |Ic| = {abs(Ic_2phg):.4f} pu = {abs(Ic_2phg)*IB:.4f} kA")

# ============================================================
# 5. 短路电流对比与暂态波形
# ============================================================
fault_types = ['三相短路', '单相接地', '两相短路', '两相接地']
fault_currents_pu = [I_3ph_pu, I_1ph_pu, I_2ph_pu, abs(Ib_2phg)]
fault_currents_kA = [I_3ph_kA, I_1ph_kA, I_2ph_kA, abs(Ib_2phg)*IB]

print("\n" + "=" * 60)
print("短路电流汇总")
print("=" * 60)
for ft, pu, ka in zip(fault_types, fault_currents_pu, fault_currents_kA):
    ratio = pu / I_3ph_pu
    print(f"  {ft}: {pu:.4f} pu = {ka:.4f} kA (与三相短路之比={ratio:.4f})")

# ============================================================
# 绘图
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# (1) 短路电流对比柱状图
bar_colors = ['#e74c3c', '#3498db', '#27ae60', '#f39c12']
bars = axes[0, 0].bar(fault_types, fault_currents_kA, color=bar_colors, alpha=0.8, edgecolor='black')
for bar, ka in zip(bars, fault_currents_kA):
    axes[0, 0].text(bar.get_x() + bar.get_width()/2., ka + 0.02, f'{ka:.3f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
axes[0, 0].set_ylabel('短路电流 (kA)', fontsize=12)
axes[0, 0].set_title('四种短路类型电流对比', fontsize=13)
axes[0, 0].grid(True, alpha=0.3, axis='y')

# (2) 三相短路暂态波形
t = np.linspace(0, 0.1, 2000)  # 0.1秒
f0 = 50  # Hz
omega = 2 * np.pi * f0
Im = np.sqrt(2) * I_3ph_kA
Ta = 0.05  # 非周期分量衰减时间常数

ia_t = Im * (np.sin(omega * t - np.pi/2) + np.sin(np.pi/2) * np.exp(-t/Ta))
ib_t = Im * (np.sin(omega * t - np.pi/2 - 2*np.pi/3) + np.sin(np.pi/2 + 2*np.pi/3) * np.exp(-t/Ta))
ic_t = Im * (np.sin(omega * t - np.pi/2 + 2*np.pi/3) + np.sin(np.pi/2 - 2*np.pi/3) * np.exp(-t/Ta))

axes[0, 1].plot(t*1000, ia_t, 'r-', linewidth=1.5, label='ia(t)')
axes[0, 1].plot(t*1000, ib_t, 'g-', linewidth=1.5, label='ib(t)')
axes[0, 1].plot(t*1000, ic_t, 'b-', linewidth=1.5, label='ic(t)')
axes[0, 1].axhline(0, color='gray', alpha=0.3)
axes[0, 1].set_xlabel('时间 (ms)', fontsize=12)
axes[0, 1].set_ylabel('电流 (kA)', fontsize=12)
axes[0, 1].set_title('三相短路暂态电流波形', fontsize=13)
axes[0, 1].legend(fontsize=10)
axes[0, 1].grid(True, alpha=0.3)

# (3) 序网图示意 (用电流相量图代替)
theta_range = np.linspace(0, 2*np.pi, 100)
# 三相短路相量
ax3 = axes[1, 0]
angles_3ph = [np.angle(I1_3ph), np.angle(I1_3ph) - 2*np.pi/3, np.angle(I1_3ph) + 2*np.pi/3]
mags_3ph = [I_3ph_pu, I_3ph_pu, I_3ph_pu]
phase_labels = ['Ia', 'Ib', 'Ic']
phase_colors = ['red', 'green', 'blue']
for ang, mag, lbl, clr in zip(angles_3ph, mags_3ph, phase_labels, phase_colors):
    ax3.arrow(0, 0, mag*np.cos(ang), mag*np.sin(ang), head_width=0.05, head_length=0.03,
              fc=clr, ec=clr, linewidth=2)
    ax3.text(mag*np.cos(ang)*1.15, mag*np.sin(ang)*1.15, lbl, fontsize=11, color=clr, fontweight='bold')
ax3.set_xlim([-4, 4])
ax3.set_ylim([-4, 4])
ax3.set_aspect('equal')
ax3.axhline(0, color='gray', alpha=0.3)
ax3.axvline(0, color='gray', alpha=0.3)
ax3.set_title('三相短路电流相量图', fontsize=13)
ax3.grid(True, alpha=0.3)

# (4) 单相接地电流相量
ax4 = axes[1, 1]
currents_1ph = [Ia, Ib, Ic]
for curr, lbl, clr in zip(currents_1ph, phase_labels, phase_colors):
    mag_c = abs(curr)
    ang_c = np.angle(curr)
    if mag_c > 0.001:
        ax4.arrow(0, 0, mag_c*np.cos(ang_c), mag_c*np.sin(ang_c), head_width=0.05, head_length=0.03,
                  fc=clr, ec=clr, linewidth=2)
        ax4.text(mag_c*np.cos(ang_c)*1.15, mag_c*np.sin(ang_c)*1.15,
                f'{lbl}={mag_c:.2f}pu', fontsize=10, color=clr, fontweight='bold')
ax4.set_xlim([-4, 4])
ax4.set_ylim([-4, 4])
ax4.set_aspect('equal')
ax4.axhline(0, color='gray', alpha=0.3)
ax4.axvline(0, color='gray', alpha=0.3)
ax4.set_title('单相接地短路电流相量图', fontsize=13)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "ch04_short_circuit.png"), dpi=200, bbox_inches='tight')
print(f"\n图片已保存: ch04_short_circuit.png")

# 保存KPI
kpi = {
    "base_values": {"SB_MVA": SB, "VB_kV": VB, "IB_kA": round(IB, 4)},
    "sequence_impedance": {"X1_pu": X1, "X2_pu": X2, "X0_pu": X0},
    "fault_summary": [
        {"type": ft, "current_pu": round(pu, 4), "current_kA": round(ka, 4), "ratio_to_3ph": round(pu/I_3ph_pu, 4)}
        for ft, pu, ka in zip(fault_types, fault_currents_pu, fault_currents_kA)
    ],
    "impulse_current_kA": round(I_impulse, 4)
}
with open(os.path.join(output_dir, "ch04_kpi.json"), "w", encoding="utf-8") as f:
    json.dump(kpi, f, ensure_ascii=False, indent=2)
print("KPI数据已保存: ch04_kpi.json")
