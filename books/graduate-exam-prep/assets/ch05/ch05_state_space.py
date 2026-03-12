"""
第5章仿真：状态空间分析
演示：直流电机状态空间建模、可控可观判定、极点配置与观测器设计
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy import linalg as la
from scipy.integrate import solve_ivp
import os
import json

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# 直流电机状态空间模型
# 状态变量: x1=电枢电流ia, x2=角速度ω
# 参数: R=1Ω, L=0.5H, Kt=0.01 N·m/A, Ke=0.01 V·s/rad
#       J=0.01 kg·m², b=0.1 N·m·s/rad
#
# 状态方程:
#   dx1/dt = -(R/L)*x1 - (Ke/L)*x2 + (1/L)*u
#   dx2/dt = (Kt/J)*x1 - (b/J)*x2
# ============================================================

R_a = 1.0    # 电枢电阻 Ω
L_a = 0.5    # 电枢电感 H
Kt = 0.01    # 转矩常数 N·m/A
Ke = 0.01    # 反电动势常数 V·s/rad
J = 0.01     # 转动惯量 kg·m²
b = 0.1      # 粘性摩擦系数 N·m·s/rad

# 状态矩阵
A = np.array([
    [-R_a/L_a, -Ke/L_a],
    [Kt/J, -b/J]
])
B = np.array([[1/L_a], [0]])
C = np.array([[0, 1]])  # 输出为角速度
D = np.array([[0]])

print("=" * 60)
print("直流电机状态空间模型")
print("=" * 60)
print(f"\nA = {A}")
print(f"B = {B.flatten()}")
print(f"C = {C.flatten()}")
print(f"D = {D.flatten()}")

# 特征值 (开环极点)
eigenvalues = np.linalg.eigvals(A)
print(f"\n开环极点: {eigenvalues}")
for i, ev in enumerate(eigenvalues):
    print(f"  λ{i+1} = {ev:.4f} (实部{'<' if ev.real < 0 else '>'}0, {'稳定' if ev.real < 0 else '不稳定'})")

# ============================================================
# 可控性分析
# ============================================================
print("\n" + "=" * 60)
print("可控性分析")
print("=" * 60)

Mc = np.hstack([B, A @ B])  # 可控性矩阵 [B, AB]
rank_Mc = np.linalg.matrix_rank(Mc)
det_Mc = np.linalg.det(Mc)

print(f"可控性矩阵 Mc = [B, AB]:")
print(f"  {Mc}")
print(f"  rank(Mc) = {rank_Mc}, det(Mc) = {det_Mc:.6f}")
print(f"  系统{'完全可控' if rank_Mc == 2 else '不完全可控'}")

# ============================================================
# 可观测性分析
# ============================================================
print("\n" + "=" * 60)
print("可观测性分析")
print("=" * 60)

Mo = np.vstack([C, C @ A])  # 可观测性矩阵 [C; CA]
rank_Mo = np.linalg.matrix_rank(Mo)
det_Mo = np.linalg.det(Mo)

print(f"可观测性矩阵 Mo = [C; CA]:")
print(f"  {Mo}")
print(f"  rank(Mo) = {rank_Mo}, det(Mo) = {det_Mo:.6f}")
print(f"  系统{'完全可观测' if rank_Mo == 2 else '不完全可观测'}")

# ============================================================
# 极点配置 (状态反馈)
# 目标极点: p1=-5, p2=-10 (比开环快5倍以上)
# ============================================================
print("\n" + "=" * 60)
print("极点配置设计")
print("=" * 60)

desired_poles = np.array([-5.0, -10.0])
print(f"期望极点: {desired_poles}")

# 用Ackermann公式
# K = [0, 1]*Mc^(-1) * φ(A)
# φ(A) = A^2 + 15A + 50I (from desired char. poly: s^2+15s+50)
phi_A = A @ A + 15 * A + 50 * np.eye(2)
Mc_inv = np.linalg.inv(Mc)
K = np.array([[0, 1]]) @ Mc_inv @ phi_A
K = K.flatten()

print(f"状态反馈增益 K = {K}")
A_cl = A - B @ K.reshape(1, -1)
cl_poles = np.linalg.eigvals(A_cl)
print(f"闭环极点验证: {cl_poles}")
print(f"极点配置误差: {np.sort(cl_poles) - np.sort(desired_poles)}")

# ============================================================
# 全维状态观测器设计
# 观测器极点: p1=-25, p2=-50 (比闭环极点快5倍)
# ============================================================
print("\n" + "=" * 60)
print("全维状态观测器设计")
print("=" * 60)

obs_poles = np.array([-25.0, -50.0])
print(f"观测器极点: {obs_poles}")

# 对偶系统极点配置: L^T = acker(A^T, C^T, obs_poles)
# φ_obs(A^T) = (A^T)^2 + 75*A^T + 1250*I
AT = A.T
CT = C.T
Mo_dual = np.hstack([CT, AT @ CT])
phi_AT = AT @ AT + 75 * AT + 1250 * np.eye(2)
L_T = np.array([[0, 1]]) @ np.linalg.inv(Mo_dual) @ phi_AT
L = L_T.T.flatten()

print(f"观测器增益 L = {L}")
A_obs = A - L.reshape(-1, 1) @ C
obs_eigs = np.linalg.eigvals(A_obs)
print(f"观测器极点验证: {obs_eigs}")

# ============================================================
# 仿真: 开环 vs 极点配置闭环 vs 带观测器闭环
# ============================================================
print("\n" + "=" * 60)
print("动态仿真")
print("=" * 60)

def open_loop(t, x):
    u = 12.0  # 12V阶跃输入
    return (A @ x + B.flatten() * u)

def closed_loop_full_state(t, x):
    r = 12.0  # 参考输入
    u = r - K @ x
    return (A @ x + B.flatten() * u)

def closed_loop_observer(t, z):
    # z = [x1, x2, x_hat1, x_hat2]
    x = z[:2]
    x_hat = z[2:]
    r = 12.0
    y = C @ x  # 实际输出
    y_hat = C @ x_hat  # 估计输出
    u = r - K @ x_hat  # 用估计状态反馈
    dx = A @ x + B.flatten() * u
    dx_hat = A @ x_hat + B.flatten() * u + L * (y - y_hat).flatten()
    return np.concatenate([dx, dx_hat])

t_span = (0, 3)
t_eval = np.linspace(0, 3, 500)
x0 = np.array([0.0, 0.0])

sol_open = solve_ivp(open_loop, t_span, x0, t_eval=t_eval, method='RK45')
sol_cl = solve_ivp(closed_loop_full_state, t_span, x0, t_eval=t_eval, method='RK45')
z0 = np.array([0.0, 0.0, 0.0, 0.0])  # 观测器初始估计也为0
sol_obs = solve_ivp(closed_loop_observer, t_span, z0, t_eval=t_eval, method='RK45')

# 计算性能指标
for name, sol, idx in [("开环", sol_open, 1), ("闭环(全状态)", sol_cl, 1), ("闭环(观测器)", sol_obs, 1)]:
    y = sol.y[idx]
    y_ss = y[-1]
    peak = np.max(y)
    overshoot = (peak - y_ss) / y_ss * 100 if y_ss > 0 else 0
    settle_idx = np.where(np.abs(y - y_ss) > 0.02 * abs(y_ss))[0]
    ts = sol.t[settle_idx[-1]] if len(settle_idx) > 0 else 0
    print(f"  {name}: 稳态值={y_ss:.4f}, 超调量={overshoot:.2f}%, 调节时间={ts:.4f}s")

# ============================================================
# 绘图
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# (1) 角速度响应对比
axes[0, 0].plot(sol_open.t, sol_open.y[1], 'b--', linewidth=2, label='开环')
axes[0, 0].plot(sol_cl.t, sol_cl.y[1], 'r-', linewidth=2, label='闭环(全状态反馈)')
axes[0, 0].plot(sol_obs.t, sol_obs.y[1], 'g-.', linewidth=2, label='闭环(观测器反馈)')
axes[0, 0].set_xlabel('时间 (s)', fontsize=12)
axes[0, 0].set_ylabel('角速度 ω (rad/s)', fontsize=12)
axes[0, 0].set_title('直流电机角速度阶跃响应', fontsize=13)
axes[0, 0].legend(fontsize=10)
axes[0, 0].grid(True, alpha=0.3)

# (2) 观测器估计误差
obs_err1 = sol_obs.y[0] - sol_obs.y[2]  # ia误差
obs_err2 = sol_obs.y[1] - sol_obs.y[3]  # ω误差
axes[0, 1].plot(sol_obs.t, obs_err1, 'r-', linewidth=2, label='ia估计误差')
axes[0, 1].plot(sol_obs.t, obs_err2, 'b-', linewidth=2, label='ω估计误差')
axes[0, 1].set_xlabel('时间 (s)', fontsize=12)
axes[0, 1].set_ylabel('估计误差', fontsize=12)
axes[0, 1].set_title('状态观测器估计误差收敛', fontsize=13)
axes[0, 1].legend(fontsize=10)
axes[0, 1].grid(True, alpha=0.3)

# (3) 极点分布
ax3 = axes[1, 0]
ax3.plot(eigenvalues.real, eigenvalues.imag, 'bx', markersize=12, markeredgewidth=3, label=f'开环极点')
ax3.plot(cl_poles.real, cl_poles.imag, 'ro', markersize=10, markeredgewidth=2, label=f'闭环极点(配置)')
ax3.plot(obs_eigs.real, obs_eigs.imag, 'gs', markersize=10, markeredgewidth=2, label=f'观测器极点')
ax3.axhline(0, color='gray', alpha=0.3)
ax3.axvline(0, color='gray', alpha=0.3)
ax3.set_xlabel('实部 Re(s)', fontsize=12)
ax3.set_ylabel('虚部 Im(s)', fontsize=12)
ax3.set_title('s平面极点分布', fontsize=13)
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)
ax3.set_xlim([-55, 5])

# (4) 电枢电流
axes[1, 1].plot(sol_open.t, sol_open.y[0], 'b--', linewidth=2, label='开环')
axes[1, 1].plot(sol_cl.t, sol_cl.y[0], 'r-', linewidth=2, label='闭环(全状态)')
axes[1, 1].plot(sol_obs.t, sol_obs.y[0], 'g-.', linewidth=2, label='闭环(观测器)')
axes[1, 1].set_xlabel('时间 (s)', fontsize=12)
axes[1, 1].set_ylabel('电枢电流 ia (A)', fontsize=12)
axes[1, 1].set_title('电枢电流响应', fontsize=13)
axes[1, 1].legend(fontsize=10)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "ch05_state_space.png"), dpi=200, bbox_inches='tight')
print(f"\n图片已保存: ch05_state_space.png")

# 保存KPI
kpi = {
    "dc_motor_params": {"R": R_a, "L": L_a, "Kt": Kt, "Ke": Ke, "J": J, "b": b},
    "A_matrix": A.tolist(),
    "B_matrix": B.flatten().tolist(),
    "open_loop_poles": [str(e) for e in eigenvalues],
    "controllability": {"rank": int(rank_Mc), "det": round(det_Mc, 6), "is_controllable": bool(rank_Mc == 2)},
    "observability": {"rank": int(rank_Mo), "det": round(det_Mo, 6), "is_observable": bool(rank_Mo == 2)},
    "pole_placement": {
        "desired_poles": desired_poles.tolist(),
        "K_gain": K.tolist(),
        "achieved_poles": [round(p.real, 4) for p in cl_poles]
    },
    "observer": {
        "desired_poles": obs_poles.tolist(),
        "L_gain": L.tolist(),
        "achieved_poles": [round(p.real, 4) for p in obs_eigs]
    }
}
with open(os.path.join(output_dir, "ch05_kpi.json"), "w", encoding="utf-8") as f:
    json.dump(kpi, f, ensure_ascii=False, indent=2)
print("KPI数据已保存: ch05_kpi.json")
