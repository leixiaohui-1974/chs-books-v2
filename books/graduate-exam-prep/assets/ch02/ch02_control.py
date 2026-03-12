"""
第2章仿真：时域分析与频域分析
演示：二阶系统阶跃响应、Routh判据验证、Bode图与稳定裕度
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
# 考研经典题型: G(s) = K / [s(s+1)(s+5)]
# 求: 稳定K范围(Routh), 不同K的阶跃响应, Bode图与裕度
# ============================================================
print("=" * 60)
print("经典I型系统频域与时域综合分析")
print("G(s) = K / [s(s+1)(s+5)]")
print("=" * 60)

# Routh判据求稳定K范围
# 特征方程: s^3 + 6s^2 + 5s + K = 0
# Routh表:
#   s^3: 1    5
#   s^2: 6    K
#   s^1: (30-K)/6
#   s^0: K
# 稳定条件: K>0 且 30-K>0 → 0 < K < 30
K_critical = 30.0
print(f"\nRouth判据分析:")
print(f"  特征方程: s^3 + 6s^2 + 5s + K = 0")
print(f"  Routh表第一列: [1, 6, (30-K)/6, K]")
print(f"  稳定条件: 0 < K < {K_critical}")

# 分析多个K值
K_values = [5.0, 10.0, 20.0, 30.0, 50.0]
results = []

for K in K_values:
    s = ct.tf('s')
    G_open = K / (s * (s + 1) * (s + 5))
    G_closed = ct.feedback(G_open, 1)

    # 裕度
    gm, pm, wcg, wcp = ct.margin(G_open)
    gm_db = 20 * np.log10(gm) if gm and gm > 0 else float('inf')

    # 特征根
    char_poly = [1, 6, 5, K]
    roots = np.roots(char_poly)
    is_stable = all(r.real < 0 for r in roots)

    # 稳态误差(对斜坡输入, I型系统)
    Kv = K / 5.0  # 速度误差系数 = lim s→0 s*G(s) = K/5
    ess_ramp = 1.0 / Kv  # 斜坡稳态误差

    result = {
        'K': K,
        'phase_margin_deg': round(pm, 2) if pm else 0,
        'gain_margin_dB': round(gm_db, 2),
        'is_stable': is_stable,
        'Kv': round(Kv, 2),
        'ess_ramp': round(ess_ramp, 4),
        'poles': [f"{r:.3f}" for r in roots]
    }
    results.append(result)

    status = "稳定" if is_stable else "不稳定"
    print(f"\n  K={K:5.1f}: PM={pm:7.2f}°, GM={gm_db:7.2f}dB, {status}")
    print(f"          Kv={Kv:.2f}, 斜坡稳态误差={ess_ramp:.4f}")
    print(f"          极点: {[f'{r:.3f}' for r in roots]}")

# ============================================================
# 绘图
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# (1) 阶跃响应对比
time = np.linspace(0, 15, 1000)
colors = ['#27ae60', '#2980b9', '#e67e22', '#e74c3c', '#8e44ad']
labels_k = [f'K={K}' for K in K_values]

for i, K in enumerate(K_values):
    s = ct.tf('s')
    G_open = K / (s * (s + 1) * (s + 5))
    G_closed = ct.feedback(G_open, 1)
    try:
        t, y = ct.step_response(G_closed, time)
        # 截断发散响应
        y_clipped = np.clip(y, -5, 5)
        axes[0, 0].plot(t, y_clipped, linewidth=2, color=colors[i], label=labels_k[i])
    except Exception:
        pass

axes[0, 0].axhline(1.0, color='gray', linestyle='--', alpha=0.5)
axes[0, 0].set_xlabel('时间 (s)', fontsize=11)
axes[0, 0].set_ylabel('输出 y(t)', fontsize=11)
axes[0, 0].set_title('单位阶跃响应 (不同增益K)', fontsize=13)
axes[0, 0].legend(fontsize=9)
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].set_ylim([-3, 3])

# (2) Bode图 (K=10)
K_bode = 10.0
s = ct.tf('s')
G_bode = K_bode / (s * (s + 1) * (s + 5))
mag, phase, omega = ct.bode(G_bode, plot=False)
mag_db = 20 * np.log10(mag)

ax_mag = axes[0, 1]
ax_mag.semilogx(omega, mag_db, 'b-', linewidth=2)
ax_mag.axhline(0, color='red', linestyle='--', alpha=0.5)
gm_k10, pm_k10, wcg_k10, wcp_k10 = ct.margin(G_bode)
if wcp_k10:
    ax_mag.axvline(wcp_k10, color='green', linestyle=':', alpha=0.7, label=f'ωc={wcp_k10:.2f} rad/s')
ax_mag.set_xlabel('频率 (rad/s)', fontsize=11)
ax_mag.set_ylabel('幅值 (dB)', fontsize=11)
ax_mag.set_title(f'Bode幅频特性 (K={K_bode})', fontsize=13)
ax_mag.legend(fontsize=9)
ax_mag.grid(True, alpha=0.3, which='both')

# (3) Bode相频
ax_phase = axes[1, 0]
ax_phase.semilogx(omega, np.degrees(phase), 'b-', linewidth=2)
ax_phase.axhline(-180, color='red', linestyle='--', alpha=0.5, label='-180°线')
if wcp_k10:
    phase_at_wc = np.interp(wcp_k10, omega, np.degrees(phase))
    ax_phase.plot(wcp_k10, phase_at_wc, 'go', markersize=10, label=f'PM={pm_k10:.1f}°')
    ax_phase.annotate(f'PM={pm_k10:.1f}°', xy=(wcp_k10, phase_at_wc),
                      xytext=(wcp_k10*3, phase_at_wc+20), fontsize=10,
                      arrowprops=dict(arrowstyle='->', color='green'))
ax_phase.set_xlabel('频率 (rad/s)', fontsize=11)
ax_phase.set_ylabel('相位 (°)', fontsize=11)
ax_phase.set_title(f'Bode相频特性 (K={K_bode})', fontsize=13)
ax_phase.legend(fontsize=9)
ax_phase.grid(True, alpha=0.3, which='both')

# (4) K vs 相位裕度关系
K_sweep = np.linspace(1, 50, 200)
pm_sweep = []
for K in K_sweep:
    s = ct.tf('s')
    G_tmp = K / (s * (s + 1) * (s + 5))
    _, pm_tmp, _, _ = ct.margin(G_tmp)
    pm_sweep.append(pm_tmp if pm_tmp else -90)

axes[1, 1].plot(K_sweep, pm_sweep, 'b-', linewidth=2)
axes[1, 1].axhline(0, color='red', linestyle='--', label='PM=0° (临界)')
axes[1, 1].axhline(30, color='orange', linestyle=':', label='PM=30° (工程下限)')
axes[1, 1].axvline(30, color='red', linestyle=':', alpha=0.5, label='K_cr=30 (Routh)')
axes[1, 1].fill_between(K_sweep, 0, [max(0, p) for p in pm_sweep], alpha=0.1, color='green')
axes[1, 1].set_xlabel('增益 K', fontsize=11)
axes[1, 1].set_ylabel('相位裕度 (°)', fontsize=11)
axes[1, 1].set_title('增益K与相位裕度的关系', fontsize=13)
axes[1, 1].legend(fontsize=9)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "ch02_time_freq_analysis.png"), dpi=200, bbox_inches='tight')
print(f"\n图片已保存: ch02_time_freq_analysis.png")

# 保存KPI
kpi = {
    "system": "G(s) = K / [s(s+1)(s+5)]",
    "routh_critical_K": K_critical,
    "stable_range": "0 < K < 30",
    "results": results
}
with open(os.path.join(output_dir, "ch02_kpi.json"), "w", encoding="utf-8") as f:
    json.dump(kpi, f, ensure_ascii=False, indent=2)
print("KPI数据已保存: ch02_kpi.json")
