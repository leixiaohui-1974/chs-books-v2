"""
第1章仿真：传递函数与方框图化简
演示：RLC电路的传递函数推导、梅森增益公式验证、方框图化简对比
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import control as ct
import os
import json

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# 案例：RLC串联电路的传递函数
# 微分方程: L*di/dt + R*i + (1/C)*∫i dt = u(t)
# 以电容电压为输出: G(s) = 1/(LCs^2 + RCs + 1)
# 参数: R=2Ω, L=1H, C=0.5F
# ============================================================
R, L, C_val = 2.0, 1.0, 0.5
wn = 1.0 / np.sqrt(L * C_val)  # 自然频率
zeta = R / (2.0 * np.sqrt(L / C_val))  # 阻尼比

print("=" * 60)
print("RLC串联电路传递函数分析")
print("=" * 60)
print(f"参数: R={R} Ω, L={L} H, C={C_val} F")
print(f"自然频率 ωn = 1/√(LC) = {wn:.4f} rad/s")
print(f"阻尼比 ζ = R/(2√(L/C)) = {zeta:.4f}")

# 构建传递函数 G(s) = 1/(LCs^2 + RCs + 1) = wn^2/(s^2 + 2*zeta*wn*s + wn^2)
num = [wn**2]
den = [1, 2*zeta*wn, wn**2]
G_rlc = ct.tf(num, den)
print(f"\n传递函数 G(s) = {wn**2:.2f} / (s^2 + {2*zeta*wn:.2f}s + {wn**2:.2f})")

# 极点
poles = np.roots(den)
print(f"闭环极点: {poles}")

# 阶跃响应
time = np.linspace(0, 12, 500)
t, y = ct.step_response(G_rlc, time)

# 性能指标
y_ss = y[-1]
overshoot = (np.max(y) - y_ss) / y_ss * 100 if y_ss > 0 else 0
peak_time = t[np.argmax(y)]
# 调节时间 (2%带)
settle_idx = np.where(np.abs(y - y_ss) > 0.02 * y_ss)[0]
settling_time = t[settle_idx[-1]] if len(settle_idx) > 0 else 0

print(f"\n阶跃响应性能指标:")
print(f"  稳态值: {y_ss:.4f}")
print(f"  超调量: {overshoot:.2f}%")
print(f"  峰值时间: {peak_time:.4f} s")
print(f"  调节时间(2%): {settling_time:.4f} s")

# ============================================================
# 梅森增益公式验证
# 信号流图: R(s) -[G1]-> X1 -[G2]-> X2 -[G3]-> Y(s)
# 反馈回路: X2 -[-H1]-> X1 (局部反馈)
#           Y  -[-H2]-> R  (总反馈)
# Mason: T = Σ(Pk*Δk)/Δ
# ============================================================
print("\n" + "=" * 60)
print("梅森增益公式验证")
print("=" * 60)

G1_val, G2_val, G3_val = 2.0, 3.0, 4.0
H1_val, H2_val = 0.5, 0.1

# 方框图代数法
# 内环: G_inner = G2/(1+G2*H1)
G_inner = G2_val / (1 + G2_val * H1_val)
# 前向通路: G_forward = G1 * G_inner * G3
G_forward = G1_val * G_inner * G3_val
# 总闭环: T = G_forward / (1 + G_forward * H2)
T_block = G_forward / (1 + G_forward * H2_val)

print(f"方框图代数法:")
print(f"  内环等效: G2/(1+G2*H1) = {G_inner:.4f}")
print(f"  前向通道: G1*G_inner*G3 = {G_forward:.4f}")
print(f"  闭环增益: T = {T_block:.4f}")

# 梅森增益公式法
# 前向通路 P1 = G1*G2*G3
P1 = G1_val * G2_val * G3_val
# 回路增益: L1 = -G2*H1, L2 = -G1*G2*G3*H2
L1 = -G2_val * H1_val
L2 = -G1_val * G2_val * G3_val * H2_val
# 不接触回路对: L1和L2接触(共享G2节点)，无不接触回路对
Delta = 1 - (L1 + L2) + 0  # 无不接触回路对
# P1的余因子: 与P1接触的回路全部去掉 → Δ1=1
Delta_1 = 1
T_mason = P1 * Delta_1 / Delta

print(f"\n梅森增益公式法:")
print(f"  前向通路增益 P1 = G1*G2*G3 = {P1:.4f}")
print(f"  回路增益: L1 = -G2*H1 = {L1:.4f}")
print(f"  回路增益: L2 = -G1*G2*G3*H2 = {L2:.4f}")
print(f"  特征式 Δ = 1-(L1+L2) = {Delta:.4f}")
print(f"  余因子 Δ1 = {Delta_1}")
print(f"  Mason增益 T = P1*Δ1/Δ = {T_mason:.4f}")
print(f"\n验证: 方框图法 = {T_block:.4f}, Mason公式 = {T_mason:.4f}, 误差 = {abs(T_block-T_mason):.2e}")

# ============================================================
# 不同阻尼比对比
# ============================================================
zeta_values = [0.2, 0.5, 0.707, 1.0, 2.0]
zeta_labels = ['ζ=0.2 (欠阻尼)', 'ζ=0.5 (欠阻尼)', 'ζ=0.707 (最佳阻尼)', 'ζ=1.0 (临界阻尼)', 'ζ=2.0 (过阻尼)']
colors = ['#e74c3c', '#e67e22', '#27ae60', '#2980b9', '#8e44ad']

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左图：不同阻尼比的阶跃响应
for z, label, color in zip(zeta_values, zeta_labels, colors):
    num_z = [wn**2]
    den_z = [1, 2*z*wn, wn**2]
    G_z = ct.tf(num_z, den_z)
    t_z, y_z = ct.step_response(G_z, time)
    axes[0].plot(t_z, y_z, linewidth=2, label=label, color=color)

axes[0].axhline(1.0, color='gray', linestyle='--', alpha=0.5, label='稳态值')
axes[0].set_xlabel('时间 (s)', fontsize=12)
axes[0].set_ylabel('输出 y(t)', fontsize=12)
axes[0].set_title('二阶系统阶跃响应 (ωn=1.414 rad/s)', fontsize=13)
axes[0].legend(fontsize=9, loc='lower right')
axes[0].grid(True, alpha=0.3)
axes[0].set_xlim([0, 12])
axes[0].set_ylim([-0.1, 1.8])

# 右图：RLC电路极点分布
ax2 = axes[1]
theta = np.linspace(0, 2*np.pi, 200)
ax2.plot(wn*np.cos(theta), wn*np.sin(theta), 'k--', alpha=0.3, label=f'|s|=ωn={wn:.2f}')

for z, label, color in zip(zeta_values, zeta_labels, colors):
    den_z = [1, 2*z*wn, wn**2]
    p = np.roots(den_z)
    ax2.plot(p.real, p.imag, 'x', markersize=10, markeredgewidth=2, color=color, label=label)

ax2.axhline(0, color='gray', alpha=0.3)
ax2.axvline(0, color='gray', alpha=0.3)
ax2.set_xlabel('实部 Re(s)', fontsize=12)
ax2.set_ylabel('虚部 Im(s)', fontsize=12)
ax2.set_title('s平面极点分布', fontsize=13)
ax2.legend(fontsize=8, loc='upper left')
ax2.grid(True, alpha=0.3)
ax2.set_aspect('equal')
ax2.set_xlim([-4, 1])
ax2.set_ylim([-2, 2])

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "ch01_transfer_function.png"), dpi=200, bbox_inches='tight')
print(f"\n图片已保存: ch01_transfer_function.png")

# 保存KPI表
kpi = {
    "rlc_params": {"R": R, "L": L, "C": C_val, "wn": round(wn, 4), "zeta": round(zeta, 4)},
    "step_response": {
        "steady_state": round(float(y_ss), 4),
        "overshoot_pct": round(float(overshoot), 2),
        "peak_time_s": round(float(peak_time), 4),
        "settling_time_2pct_s": round(float(settling_time), 4)
    },
    "mason_verification": {
        "block_diagram_gain": round(T_block, 4),
        "mason_formula_gain": round(T_mason, 4),
        "error": f"{abs(T_block-T_mason):.2e}"
    },
    "poles": [str(p) for p in poles]
}
with open(os.path.join(output_dir, "ch01_kpi.json"), "w", encoding="utf-8") as f:
    json.dump(kpi, f, ensure_ascii=False, indent=2)
print("KPI数据已保存: ch01_kpi.json")
