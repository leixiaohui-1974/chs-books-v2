"""
第3章仿真：电力系统潮流计算
演示：3节点系统牛顿-拉夫逊法潮流求解
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
# 3节点电力系统潮流计算 (Newton-Raphson法)
# 节点1: 平衡节点 (Slack), V1=1.05∠0°
# 节点2: PV节点, P2=0.5 pu, V2=1.02 pu
# 节点3: PQ节点, P3=-1.0 pu, Q3=-0.5 pu (负荷)
#
# 线路阻抗 (标幺值):
# 线路1-2: z12 = 0.02 + j0.06
# 线路1-3: z13 = 0.01 + j0.04
# 线路2-3: z23 = 0.03 + j0.08
# ============================================================

print("=" * 60)
print("3节点电力系统 Newton-Raphson 潮流计算")
print("=" * 60)

# 节点导纳矩阵
z12 = 0.02 + 0.06j
z13 = 0.01 + 0.04j
z23 = 0.03 + 0.08j

y12 = 1.0 / z12
y13 = 1.0 / z13
y23 = 1.0 / z23

# Y矩阵 (3x3)
Y = np.zeros((3, 3), dtype=complex)
Y[0, 0] = y12 + y13
Y[0, 1] = -y12
Y[0, 2] = -y13
Y[1, 0] = -y12
Y[1, 1] = y12 + y23
Y[1, 2] = -y23
Y[2, 0] = -y13
Y[2, 1] = -y23
Y[2, 2] = y13 + y23

print("\n节点导纳矩阵 Y (标幺值):")
for i in range(3):
    row = "  ".join([f"{Y[i,j].real:8.3f}+j{Y[i,j].imag:8.3f}" for j in range(3)])
    print(f"  [{row}]")

# 已知量
P_spec = {1: 0.5, 2: -1.0}   # 节点2(idx=1), 节点3(idx=2)的有功
Q_spec = {2: -0.5}            # 节点3(idx=2)的无功
V_spec = {0: 1.05, 1: 1.02}   # 节点1,2的电压幅值

# 初始值
V = np.array([1.05, 1.02, 1.0])  # 电压幅值
theta = np.array([0.0, 0.0, 0.0])  # 电压相角(rad)

# NR迭代
max_iter = 20
tol = 1e-6
convergence_history = []

print(f"\n开始Newton-Raphson迭代 (容差={tol}):")
print("-" * 50)

for iteration in range(max_iter):
    # 计算功率注入
    P_calc = np.zeros(3)
    Q_calc = np.zeros(3)

    for i in range(3):
        for j in range(3):
            P_calc[i] += V[i] * V[j] * (
                Y[i,j].real * np.cos(theta[i] - theta[j]) +
                Y[i,j].imag * np.sin(theta[i] - theta[j])
            )
            Q_calc[i] += V[i] * V[j] * (
                Y[i,j].real * np.sin(theta[i] - theta[j]) -
                Y[i,j].imag * np.cos(theta[i] - theta[j])
            )

    # 功率偏差
    # PV节点(idx=1): ΔP2
    # PQ节点(idx=2): ΔP3, ΔQ3
    dP2 = P_spec[1] - P_calc[1]
    dP3 = P_spec[2] - P_calc[2]
    dQ3 = Q_spec[2] - Q_calc[2]

    mismatch = np.array([dP2, dP3, dQ3])
    max_mismatch = np.max(np.abs(mismatch))
    convergence_history.append(max_mismatch)

    print(f"  迭代 {iteration+1}: |ΔP2|={abs(dP2):.6e}, |ΔP3|={abs(dP3):.6e}, |ΔQ3|={abs(dQ3):.6e}, max={max_mismatch:.6e}")

    if max_mismatch < tol:
        print(f"\n收敛! 共 {iteration+1} 次迭代")
        break

    # Jacobian矩阵 (3x3: [dP/dθ, dP/dV; dQ/dθ, dQ/dV])
    # 变量: θ2, θ3, V3
    J = np.zeros((3, 3))

    # ∂P2/∂θ2
    for j in range(3):
        if j != 1:
            J[0, 0] += V[1] * V[j] * (-Y[1,j].real * np.sin(theta[1]-theta[j]) + Y[1,j].imag * np.cos(theta[1]-theta[j]))
    # ∂P2/∂θ3
    J[0, 1] = V[1] * V[2] * (Y[1,2].real * np.sin(theta[1]-theta[2]) - Y[1,2].imag * np.cos(theta[1]-theta[2]))
    # ∂P2/∂V3
    J[0, 2] = V[1] * (Y[1,2].real * np.cos(theta[1]-theta[2]) + Y[1,2].imag * np.sin(theta[1]-theta[2]))

    # ∂P3/∂θ2
    J[1, 0] = V[2] * V[1] * (Y[2,1].real * np.sin(theta[2]-theta[1]) - Y[2,1].imag * np.cos(theta[2]-theta[1]))
    # ∂P3/∂θ3
    for j in range(3):
        if j != 2:
            J[1, 1] += V[2] * V[j] * (-Y[2,j].real * np.sin(theta[2]-theta[j]) + Y[2,j].imag * np.cos(theta[2]-theta[j]))
    # ∂P3/∂V3
    for j in range(3):
        if j != 2:
            J[1, 2] += V[j] * (Y[2,j].real * np.cos(theta[2]-theta[j]) + Y[2,j].imag * np.sin(theta[2]-theta[j]))
    J[1, 2] += 2 * V[2] * Y[2,2].real

    # ∂Q3/∂θ2
    J[2, 0] = V[2] * V[1] * (Y[2,1].real * np.cos(theta[2]-theta[1]) + Y[2,1].imag * np.sin(theta[2]-theta[1]))
    # ∂Q3/∂θ3
    for j in range(3):
        if j != 2:
            J[2, 1] += V[2] * V[j] * (Y[2,j].real * np.cos(theta[2]-theta[j]) + Y[2,j].imag * np.sin(theta[2]-theta[j]))
    # ∂Q3/∂V3
    for j in range(3):
        if j != 2:
            J[2, 2] += V[j] * (Y[2,j].real * np.sin(theta[2]-theta[j]) - Y[2,j].imag * np.cos(theta[2]-theta[j]))
    J[2, 2] += -2 * V[2] * Y[2,2].imag

    # 求解修正量
    dx = np.linalg.solve(J, mismatch)

    theta[1] += dx[0]
    theta[2] += dx[1]
    V[2] += dx[2]

# 最终结果
print("\n" + "=" * 60)
print("潮流计算结果")
print("=" * 60)

# 计算线路潮流
S = np.zeros(3, dtype=complex)
for i in range(3):
    for j in range(3):
        Vi = V[i] * np.exp(1j * theta[i])
        Vj = V[j] * np.exp(1j * theta[j])
        S[i] += Vi * np.conj(Y[i,j] * (Vi - Vj)) if i != j else 0

# 修正平衡节点功率
P_calc_final = np.zeros(3)
Q_calc_final = np.zeros(3)
for i in range(3):
    for j in range(3):
        P_calc_final[i] += V[i] * V[j] * (
            Y[i,j].real * np.cos(theta[i] - theta[j]) +
            Y[i,j].imag * np.sin(theta[i] - theta[j])
        )
        Q_calc_final[i] += V[i] * V[j] * (
            Y[i,j].real * np.sin(theta[i] - theta[j]) -
            Y[i,j].imag * np.cos(theta[i] - theta[j])
        )

node_names = ['节点1(Slack)', '节点2(PV)', '节点3(PQ)']
for i in range(3):
    print(f"  {node_names[i]}: V={V[i]:.4f} pu, θ={np.degrees(theta[i]):.4f}°, P={P_calc_final[i]:.4f} pu, Q={Q_calc_final[i]:.4f} pu")

# 线路功率
print("\n线路功率流:")
lines = [(0, 1, z12), (0, 2, z13), (1, 2, z23)]
line_results = []
for i, j, z in lines:
    Vi = V[i] * np.exp(1j * theta[i])
    Vj = V[j] * np.exp(1j * theta[j])
    Iij = (Vi - Vj) / z
    Sij = Vi * np.conj(Iij)
    Sji = Vj * np.conj(-Iij)
    Ploss = Sij.real + Sji.real
    print(f"  线路{i+1}-{j+1}: S_{i+1}{j+1}={Sij.real:.4f}+j{Sij.imag:.4f} pu, 损耗={Ploss:.6f} pu")
    line_results.append({
        'from': i+1, 'to': j+1,
        'P_ij': round(Sij.real, 4), 'Q_ij': round(Sij.imag, 4),
        'P_loss': round(Ploss, 6)
    })

total_loss = sum(r['P_loss'] for r in line_results)
print(f"\n  系统总有功损耗: {total_loss:.6f} pu")

# ============================================================
# 绘图
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# (1) NR收敛曲线
axes[0].semilogy(range(1, len(convergence_history)+1), convergence_history, 'b-o', linewidth=2, markersize=6)
axes[0].axhline(tol, color='red', linestyle='--', label=f'容差={tol}')
axes[0].set_xlabel('迭代次数', fontsize=12)
axes[0].set_ylabel('最大功率偏差 (pu)', fontsize=12)
axes[0].set_title('Newton-Raphson 收敛过程', fontsize=13)
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

# (2) 节点电压分布
bar_colors = ['#3498db', '#27ae60', '#e74c3c']
bars = axes[1].bar(node_names, V, color=bar_colors, alpha=0.8, edgecolor='black')
axes[1].axhline(1.0, color='gray', linestyle='--', alpha=0.5, label='标称电压')
axes[1].axhline(0.95, color='red', linestyle=':', alpha=0.5, label='下限0.95pu')
axes[1].axhline(1.05, color='red', linestyle=':', alpha=0.5, label='上限1.05pu')
for bar, v in zip(bars, V):
    axes[1].text(bar.get_x() + bar.get_width()/2., v + 0.005, f'{v:.4f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
axes[1].set_ylabel('电压幅值 (pu)', fontsize=12)
axes[1].set_title('节点电压分布', fontsize=13)
axes[1].legend(fontsize=9)
axes[1].set_ylim([0.9, 1.1])
axes[1].grid(True, alpha=0.3, axis='y')

# (3) 功率平衡饼图
P_gen = P_calc_final[0] + P_calc_final[1]  # 发电总功率
P_load = abs(P_calc_final[2])  # 负荷
P_loss_total = total_loss

labels_pie = [f'负荷消耗\n{P_load:.3f} pu', f'网络损耗\n{P_loss_total:.4f} pu']
sizes = [P_load, P_loss_total]
pie_colors = ['#e74c3c', '#f39c12']
axes[2].pie(sizes, labels=labels_pie, colors=pie_colors, autopct='%1.1f%%',
           startangle=90, textprops={'fontsize': 10})
axes[2].set_title(f'系统有功平衡 (发电={P_gen:.4f} pu)', fontsize=13)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "ch03_power_flow.png"), dpi=200, bbox_inches='tight')
print(f"\n图片已保存: ch03_power_flow.png")

# 保存KPI
kpi = {
    "system": "3节点电力系统",
    "iterations": len(convergence_history),
    "final_mismatch": f"{convergence_history[-1]:.2e}",
    "nodes": [
        {"name": node_names[i], "V_pu": round(V[i], 4), "theta_deg": round(np.degrees(theta[i]), 4),
         "P_pu": round(P_calc_final[i], 4), "Q_pu": round(Q_calc_final[i], 4)}
        for i in range(3)
    ],
    "lines": line_results,
    "total_loss_pu": round(total_loss, 6)
}
with open(os.path.join(output_dir, "ch03_kpi.json"), "w", encoding="utf-8") as f:
    json.dump(kpi, f, ensure_ascii=False, indent=2)
print("KPI数据已保存: ch03_kpi.json")
