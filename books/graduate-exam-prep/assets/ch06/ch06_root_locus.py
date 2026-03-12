"""
第6章仿真：考研高频真题解析
演示：根轨迹综合设计 + 潮流短路联合计算 + Python验证
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
# 题目1：根轨迹综合设计
# 开环传递函数: G(s) = K(s+2) / [s(s+1)(s+4)]
# 要求: (1) 绘制根轨迹 (2) 确定使系统临界稳定的K
#       (3) 当K=10时计算闭环极点和超调量
# ============================================================
print("=" * 60)
print("题目1: 根轨迹综合设计")
print("G(s) = K(s+2) / [s(s+1)(s+4)]")
print("=" * 60)

# 开环零极点
open_zeros = [-2]
open_poles = [0, -1, -4]
print(f"开环零点: {open_zeros}")
print(f"开环极点: {open_poles}")

# 渐近线
n_p = len(open_poles)
n_z = len(open_zeros)
n_asymp = n_p - n_z
sigma_a = (sum(open_poles) - sum(open_zeros)) / n_asymp
angles_a = [(2*k+1)*180/n_asymp for k in range(n_asymp)]
print(f"\n渐近线:")
print(f"  交点 σa = (Σpi - Σzi)/(n-m) = ({sum(open_poles)}-({sum(open_zeros)}))/{n_asymp} = {sigma_a:.2f}")
print(f"  角度: {angles_a}°")

# 分离点 (求 1+KG(s)H(s)=0 → K = -s(s+1)(s+4)/(s+2), dK/ds=0)
# 数值求解
from numpy.polynomial import polynomial as P
s_test = np.linspace(-4, 0, 10000)
K_test = -s_test * (s_test+1) * (s_test+4) / (s_test+2)
# dK/ds ≈ 0的点
dK = np.diff(K_test)
sign_changes = np.where(np.diff(np.sign(dK)))[0]
breakaway_points = []
for idx in sign_changes:
    s_bp = s_test[idx+1]
    K_bp = K_test[idx+1]
    if K_bp > 0:
        breakaway_points.append((s_bp, K_bp))
        print(f"  分离点: s={s_bp:.4f}, K={K_bp:.4f}")

# 与虚轴交点 (Routh判据)
# 特征方程: s^3 + 5s^2 + (4+K)s + 2K = 0
# Routh:
#   s^3: 1     4+K
#   s^2: 5     2K
#   s^1: (5(4+K)-2K)/5 = (20+3K)/5
#   s^0: 2K
# 临界: 20+3K=0 → K=-20/3 (无意义) 或系统始终稳定对K>0
# 实际检查: s^1行 > 0 需 K > -20/3, 对所有K>0成立
# 所以该系统对所有K>0都是稳定的(有零点改善了稳定性)
print(f"\nRouth判据分析:")
print(f"  特征方程: s^3 + 5s^2 + (4+K)s + 2K = 0")
print(f"  s^1行: (20+3K)/5 > 0 当 K > -20/3")
print(f"  结论: 系统对所有 K > 0 均稳定 (根轨迹不穿越虚轴)")

# K=10时的闭环分析
K_design = 10.0
s = ct.tf('s')
G_open = K_design * (s + 2) / (s * (s + 1) * (s + 4))
G_closed = ct.feedback(G_open, 1)

char_poly = [1, 5, 14, 20]  # s^3+5s^2+(4+10)s+2*10
cl_roots = np.roots(char_poly)
print(f"\nK={K_design}时闭环极点: {cl_roots}")

# 阶跃响应
time = np.linspace(0, 8, 500)
t_step, y_step = ct.step_response(G_closed, time)
y_ss = y_step[-1]
overshoot = (np.max(y_step) - y_ss) / y_ss * 100
peak_time = t_step[np.argmax(y_step)]
settle_idx = np.where(np.abs(y_step - y_ss) > 0.02 * y_ss)[0]
settling_time = t_step[settle_idx[-1]] if len(settle_idx) > 0 else 0

print(f"\nK={K_design}时阶跃响应:")
print(f"  稳态值: {y_ss:.4f}")
print(f"  超调量: {overshoot:.2f}%")
print(f"  峰值时间: {peak_time:.4f} s")
print(f"  调节时间(2%): {settling_time:.4f} s")

# 稳态误差 (I型系统对阶跃输入)
Kv_rl = ct.dcgain(G_open * s) if False else K_design * 2 / (1 * 4)  # lim s→0 sG(s)
ess_step = 0  # I型系统对阶跃无差
ess_ramp = 1.0 / Kv_rl  # 对斜坡
print(f"  位置误差常数 Kp = ∞ (I型系统)")
print(f"  速度误差常数 Kv = {Kv_rl:.4f}")
print(f"  阶跃稳态误差: {ess_step}")
print(f"  斜坡稳态误差: {ess_ramp:.4f}")

# ============================================================
# 题目2: 简化潮流+短路联合计算
# 2节点系统: 发电机→变压器→线路→无穷大母线
# 先求正常运行潮流,再在线路末端发生三相短路
# ============================================================
print("\n" + "=" * 60)
print("题目2: 潮流-短路联合计算")
print("=" * 60)

# 潮流部分
V1 = 1.05  # 发电机端电压 pu
V2 = 1.0   # 无穷大母线电压 pu
X_line = 0.2  # 线路电抗 pu
delta = np.arcsin(0.5 * X_line / (V1 * V2))  # P=V1V2sin(δ)/X → δ=arcsin(PX/V1V2)
P_transfer = 0.5  # 传输有功 pu
delta_actual = np.arcsin(P_transfer * X_line / (V1 * V2))

print(f"  正常运行:")
print(f"    V1={V1} pu, V2={V2} pu, X={X_line} pu")
print(f"    传输功率 P={P_transfer} pu")
print(f"    功角 δ={np.degrees(delta_actual):.4f}°")

Q_transfer = (V1 * V2 * np.cos(delta_actual) - V2**2) / X_line
print(f"    无功功率 Q={Q_transfer:.4f} pu")

# 短路部分
X_total = 0.2 + 0.1  # 加上变压器电抗
I_sc = V1 / X_total
print(f"\n  三相短路 (线路末端):")
print(f"    总电抗 Xt={X_total} pu")
print(f"    短路电流 Isc={I_sc:.4f} pu")
print(f"    短路容量 Ssc={V2*I_sc:.4f} pu = {V2*I_sc*100:.1f} MVA (基准100MVA)")

# ============================================================
# 绘图
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# (1) 根轨迹图
ax1 = axes[0, 0]
# 手动绘制根轨迹
K_range = np.linspace(0.01, 100, 5000)
all_roots = []
for K in K_range:
    coeffs = [1, 5, 4+K, 2*K]
    roots = np.roots(coeffs)
    all_roots.append(roots)
all_roots = np.array(all_roots)

for i in range(3):
    ax1.plot(all_roots[:, i].real, all_roots[:, i].imag, '.', markersize=1, color='blue', alpha=0.5)

# 标记开环零极点
ax1.plot([p.real for p in [0, -1, -4]], [0, 0, 0], 'bx', markersize=12, markeredgewidth=3, label='开环极点')
ax1.plot([-2], [0], 'bo', markersize=10, markeredgewidth=2, fillstyle='none', label='开环零点')

# 标记K=10闭环极点
for r in cl_roots:
    ax1.plot(r.real, r.imag, 'r*', markersize=15, label=f'K=10: {r:.2f}' if r.imag >= 0 else '')

ax1.axhline(0, color='gray', alpha=0.3)
ax1.axvline(0, color='gray', alpha=0.3)
ax1.set_xlabel('实部 Re(s)', fontsize=12)
ax1.set_ylabel('虚部 Im(s)', fontsize=12)
ax1.set_title('根轨迹图: G(s)=K(s+2)/[s(s+1)(s+4)]', fontsize=12)
ax1.legend(fontsize=8, loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.set_xlim([-6, 2])
ax1.set_ylim([-5, 5])

# (2) K=10阶跃响应
axes[0, 1].plot(t_step, y_step, 'b-', linewidth=2)
axes[0, 1].axhline(y_ss, color='gray', linestyle='--', alpha=0.5, label=f'稳态值={y_ss:.3f}')
axes[0, 1].axhline(y_ss*1.02, color='red', linestyle=':', alpha=0.3)
axes[0, 1].axhline(y_ss*0.98, color='red', linestyle=':', alpha=0.3)
axes[0, 1].plot(peak_time, np.max(y_step), 'rv', markersize=10, label=f'峰值={np.max(y_step):.3f}')
axes[0, 1].set_xlabel('时间 (s)', fontsize=12)
axes[0, 1].set_ylabel('输出 y(t)', fontsize=12)
axes[0, 1].set_title(f'K=10 闭环阶跃响应 (超调{overshoot:.1f}%)', fontsize=12)
axes[0, 1].legend(fontsize=10)
axes[0, 1].grid(True, alpha=0.3)

# (3) K对超调量和调节时间的影响
K_sweep = np.linspace(1, 60, 100)
overshoots = []
settle_times = []
for K in K_sweep:
    s_var = ct.tf('s')
    G_tmp = K * (s_var + 2) / (s_var * (s_var + 1) * (s_var + 4))
    G_cl_tmp = ct.feedback(G_tmp, 1)
    try:
        t_tmp, y_tmp = ct.step_response(G_cl_tmp, time)
        y_ss_tmp = y_tmp[-1]
        os_tmp = (np.max(y_tmp) - y_ss_tmp) / y_ss_tmp * 100 if y_ss_tmp > 0 else 0
        si = np.where(np.abs(y_tmp - y_ss_tmp) > 0.02 * y_ss_tmp)[0]
        ts_tmp = t_tmp[si[-1]] if len(si) > 0 else 0
    except:
        os_tmp = 0
        ts_tmp = 0
    overshoots.append(os_tmp)
    settle_times.append(ts_tmp)

ax3 = axes[1, 0]
ax3_twin = ax3.twinx()
line1, = ax3.plot(K_sweep, overshoots, 'b-', linewidth=2, label='超调量(%)')
line2, = ax3_twin.plot(K_sweep, settle_times, 'r--', linewidth=2, label='调节时间(s)')
ax3.axvline(K_design, color='green', linestyle=':', alpha=0.7, label=f'K={K_design}')
ax3.set_xlabel('增益 K', fontsize=12)
ax3.set_ylabel('超调量 (%)', fontsize=12, color='blue')
ax3_twin.set_ylabel('调节时间 (s)', fontsize=12, color='red')
ax3.set_title('K对系统性能的影响', fontsize=13)
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax3.legend(lines, labels, fontsize=10)
ax3.grid(True, alpha=0.3)

# (4) 功角-功率曲线
delta_range = np.linspace(0, np.pi, 200)
P_delta = V1 * V2 * np.sin(delta_range) / X_line
axes[1, 1].plot(np.degrees(delta_range), P_delta, 'b-', linewidth=2, label='P-δ曲线')
axes[1, 1].axhline(P_transfer, color='red', linestyle='--', label=f'传输功率={P_transfer} pu')
axes[1, 1].plot(np.degrees(delta_actual), P_transfer, 'ro', markersize=10, label=f'运行点 δ={np.degrees(delta_actual):.1f}°')
axes[1, 1].set_xlabel('功角 δ (°)', fontsize=12)
axes[1, 1].set_ylabel('有功功率 P (pu)', fontsize=12)
axes[1, 1].set_title('功角-功率特性曲线', fontsize=13)
axes[1, 1].legend(fontsize=10)
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].set_xlim([0, 180])

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "ch06_exam_problems.png"), dpi=200, bbox_inches='tight')
print(f"\n图片已保存: ch06_exam_problems.png")

# 保存KPI
kpi = {
    "root_locus": {
        "open_zeros": open_zeros,
        "open_poles": open_poles,
        "asymptote_center": sigma_a,
        "asymptote_angles": angles_a,
        "all_K_stable": True,
        "K_design": K_design,
        "closed_loop_poles": [str(r) for r in cl_roots],
        "overshoot_pct": round(float(overshoot), 2),
        "settling_time_s": round(float(settling_time), 4),
        "Kv": round(Kv_rl, 4),
        "ess_ramp": round(ess_ramp, 4)
    },
    "power_flow_short_circuit": {
        "V1_pu": V1, "V2_pu": V2,
        "delta_deg": round(np.degrees(delta_actual), 4),
        "P_transfer_pu": P_transfer,
        "Q_transfer_pu": round(Q_transfer, 4),
        "I_sc_pu": round(I_sc, 4),
        "S_sc_MVA": round(V2*I_sc*100, 1)
    }
}
with open(os.path.join(output_dir, "ch06_kpi.json"), "w", encoding="utf-8") as f:
    json.dump(kpi, f, ensure_ascii=False, indent=2)
print("KPI数据已保存: ch06_kpi.json")
