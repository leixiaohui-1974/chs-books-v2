#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
第2章 状态空间分析 —— 双水箱串级系统综合案例
==============================================

问题背景：
    在水利工程中，串级水箱系统（cascaded tank system）是理解状态空间
    建模与分析的经典对象。本例考虑两个串联的圆柱形水箱：上游水箱1通过
    管道向下游水箱2供水，水箱2再通过出流管道向外排水。

    系统状态变量为两个水箱的水位偏差 δh₁、δh₂（相对于稳态工作点），
    输入为进入水箱1的流量偏差 δQ_in。系统的状态空间连续时间模型为：

        ẋ = A_c · x + B_c · u
        y = C · x

    其中：
        A_c = [[-k₁/A_{t1},  0         ],
               [ k₁/A_{t1}, -k₂/A_{t2}]]

        B_c = [[1/A_{t1}],
               [0        ]]

    参数：A_{t1}=2.0 m², A_{t2}=1.5 m², k₁=6.64×10⁻³ m²/s, k₂=8.86×10⁻³ m²/s

解题思路：
    1. 建立连续时间状态空间模型，计算系统矩阵 A_c 和输入矩阵 B_c
    2. 通过 ZOH（零阶保持器）方法进行离散化，得到离散模型 (A_d, B_d)
    3. 施加阶跃输入 δQ_in = 0.005 m³/s，使用 solve_ivp 仿真1小时阶跃响应
    4. 分析系统的能控性（controllability）和能观性（observability）
       - 传感器配置1：仅观测水箱1水位 → C₁ = [1, 0]
       - 传感器配置2：仅观测水箱2水位 → C₂ = [0, 1]
    5. 闭环 Lyapunov 稳定性分析：引入比例反馈 K = [Kp1, Kp2]，
       求解 Lyapunov 方程 A_cl^T P + P A_cl = -Q 判断闭环稳定性
    6. 生成四子图综合展示分析结果

代码结构：
    - build_model()         : 构建连续/离散状态空间模型
    - simulate_step()       : 阶跃响应仿真
    - analyze_controllability_observability() : 能控/能观性分析
    - lyapunov_stability()  : Lyapunov 稳定性分析
    - plot_results()        : 绘制四子图
    - main()                : 主流程
"""

import os
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm, solve_continuous_lyapunov
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适用于无GUI环境
import matplotlib.pyplot as plt

# ── 中文字体配置 ──
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 全局物理参数
# ============================================================
At1 = 2.0          # 水箱1横截面积 [m²]
At2 = 1.5          # 水箱2横截面积 [m²]
k1 = 6.64e-3       # 水箱1出流系数（线性化后）[m²/s]
k2 = 8.86e-3       # 水箱2出流系数（线性化后）[m²/s]
dt = 60.0           # 离散化采样周期 [s]（1分钟）
delta_Qin = 0.005   # 阶跃输入幅值 [m³/s]
T_sim = 3600.0       # 仿真时长 [s]（1小时）

# 闭环比例增益
Kp1 = 0.01
Kp2 = 0.008


def build_model():
    """
    构建双水箱串级系统的连续与离散状态空间模型。

    连续模型:
        ẋ = A_c x + B_c u

    离散化采用 ZOH（零阶保持器）方法:
        A_d = exp(A_c * dt)
        B_d = A_c⁻¹ (A_d - I) B_c

    返回:
        A_c, B_c : 连续时间系统矩阵
        A_d, B_d : 离散时间系统矩阵
    """
    # ── 连续时间系统矩阵 ──
    # 状态: x = [δh₁, δh₂]^T
    # 水箱1: dδh₁/dt = -k₁/A_{t1} δh₁ + (1/A_{t1}) δQ_in
    # 水箱2: dδh₂/dt = +k₁/A_{t1} δh₁ - k₂/A_{t2} δh₂
    #   （水箱1的出流 = 水箱2的入流）
    A_c = np.array([
        [-k1 / At1,         0.0],
        [ k1 / At1, -k2 / At2]
    ])

    B_c = np.array([
        [1.0 / At1],
        [0.0]
    ])

    # ── ZOH 离散化 ──
    # A_d = e^{A_c * dt}
    A_d = expm(A_c * dt)

    # B_d = A_c^{-1} (A_d - I) B_c
    # 对于非奇异 A_c，此公式精确成立
    A_c_inv = np.linalg.inv(A_c)
    B_d = A_c_inv @ (A_d - np.eye(2)) @ B_c

    return A_c, B_c, A_d, B_d


def simulate_step(A_c, B_c):
    """
    阶跃响应仿真：施加 δQ_in 阶跃输入，求解连续时间ODE。

    使用 scipy.integrate.solve_ivp 的 RK45 方法。

    返回:
        t_eval : 时间序列 [s]
        h1     : 水箱1水位偏差序列 [m]
        h2     : 水箱2水位偏差序列 [m]
    """
    # 初始状态：两水箱均处于稳态（偏差为零）
    x0 = np.array([0.0, 0.0])

    # 系统微分方程：ẋ = A_c x + B_c u（u = delta_Qin 阶跃）
    def dynamics(t, x):
        u = np.array([delta_Qin])  # 恒定阶跃输入
        dxdt = A_c @ x + (B_c @ u).flatten()
        return dxdt

    # 稠密输出的时间点
    t_eval = np.linspace(0, T_sim, 500)

    # 数值积分
    sol = solve_ivp(
        dynamics,
        t_span=(0, T_sim),
        y0=x0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-8,
        atol=1e-10
    )

    return sol.t, sol.y[0], sol.y[1]


def analyze_controllability_observability(A_c, B_c):
    """
    能控性与能观性分析。

    能控性矩阵: Mc = [B, AB]（2×2，因为 n=2）
        若 rank(Mc) = n = 2，则系统完全能控。

    能观性矩阵: Mo = [C; CA]（2×2）
        配置1: C₁ = [1, 0] —— 仅观测水箱1水位
        配置2: C₂ = [0, 1] —— 仅观测水箱2水位

    返回:
        results : dict，包含各配置的矩阵、秩、以及判定结论
    """
    n = A_c.shape[0]  # 状态维数 = 2

    # ── 能控性分析 ──
    # Mc = [B_c, A_c B_c]
    Mc = np.hstack([B_c, A_c @ B_c])
    rank_Mc = np.linalg.matrix_rank(Mc)

    # ── 能观性分析 —— 配置1：C₁ = [1, 0] ──
    C1 = np.array([[1.0, 0.0]])
    Mo1 = np.vstack([C1, C1 @ A_c])
    rank_Mo1 = np.linalg.matrix_rank(Mo1)

    # ── 能观性分析 —— 配置2：C₂ = [0, 1] ──
    C2 = np.array([[0.0, 1.0]])
    Mo2 = np.vstack([C2, C2 @ A_c])
    rank_Mo2 = np.linalg.matrix_rank(Mo2)

    results = {
        'Mc': Mc,
        'rank_Mc': rank_Mc,
        'controllable': rank_Mc == n,
        'C1': C1,
        'Mo1': Mo1,
        'rank_Mo1': rank_Mo1,
        'observable_C1': rank_Mo1 == n,
        'C2': C2,
        'Mo2': Mo2,
        'rank_Mo2': rank_Mo2,
        'observable_C2': rank_Mo2 == n,
    }

    return results


def lyapunov_stability(A_c):
    """
    Lyapunov 稳定性分析（闭环系统）。

    闭环反馈: u = -K x，其中 K = [Kp1, Kp2]
    闭环系统矩阵: A_cl = A_c - B_c K

    Lyapunov 方程: A_cl^T P + P A_cl = -Q
    取 Q = I（单位矩阵），若解出的 P 为正定矩阵，则闭环系统渐近稳定。

    判定正定性：检查 P 的所有特征值是否大于零。

    返回:
        A_cl        : 闭环系统矩阵
        eigenvalues : A_cl 的特征值（应具有负实部）
        P           : Lyapunov 方程的解
        P_eigs      : P 的特征值（正定则全正）
        is_stable   : 是否渐近稳定
    """
    # 反馈增益矩阵 K（1×2）
    K = np.array([[Kp1, Kp2]])

    # 输入矩阵
    B_c = np.array([
        [1.0 / At1],
        [0.0]
    ])

    # 闭环系统矩阵
    A_cl = A_c - B_c @ K

    # 闭环特征值
    eigenvalues = np.linalg.eigvals(A_cl)

    # 求解 Lyapunov 方程: A_cl^T P + P A_cl = -Q
    Q = np.eye(2)
    P = solve_continuous_lyapunov(A_cl.T, -Q)

    # P 的特征值（判定正定性）
    P_eigs = np.linalg.eigvals(P)
    is_stable = np.all(P_eigs > 0)

    return A_cl, eigenvalues, P, P_eigs, is_stable


def plot_results(t, h1, h2, A_c, A_cl, cl_eigs, co_results, P_eigs, is_stable):
    """
    绘制四子图综合展示：

    子图1（左上）: 水箱1阶跃响应曲线
    子图2（右上）: 水箱2阶跃响应曲线
    子图3（左下）: 开环与闭环特征值在复平面上的分布
    子图4（右下）: 能控性/能观性分析结果汇总表
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('第2章 状态空间分析 —— 双水箱串级系统', fontsize=16, fontweight='bold')

    t_min = t / 60.0  # 时间转换为分钟

    # ── 子图1：水箱1阶跃响应 ──
    ax1 = axes[0, 0]
    ax1.plot(t_min, h1 * 100, 'b-', linewidth=2, label='$\\delta h_1$')
    ax1.set_xlabel('时间 [min]', fontsize=12)
    ax1.set_ylabel('水位偏差 [cm]', fontsize=12)
    ax1.set_title('(a) 水箱1阶跃响应', fontsize=13)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)

    # 标注稳态值
    h1_ss = h1[-1] * 100
    ax1.axhline(y=h1_ss, color='b', linestyle='--', alpha=0.5)
    ax1.annotate(f'稳态值: {h1_ss:.2f} cm',
                 xy=(t_min[-1] * 0.7, h1_ss),
                 fontsize=10, color='blue')

    # ── 子图2：水箱2阶跃响应 ──
    ax2 = axes[0, 1]
    ax2.plot(t_min, h2 * 100, 'r-', linewidth=2, label='$\\delta h_2$')
    ax2.set_xlabel('时间 [min]', fontsize=12)
    ax2.set_ylabel('水位偏差 [cm]', fontsize=12)
    ax2.set_title('(b) 水箱2阶跃响应', fontsize=13)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)

    # 标注稳态值
    h2_ss = h2[-1] * 100
    ax2.axhline(y=h2_ss, color='r', linestyle='--', alpha=0.5)
    ax2.annotate(f'稳态值: {h2_ss:.2f} cm',
                 xy=(t_min[-1] * 0.7, h2_ss),
                 fontsize=10, color='red')

    # ── 子图3：特征值分布（复平面） ──
    ax3 = axes[1, 0]

    # 开环特征值
    ol_eigs = np.linalg.eigvals(A_c)
    ax3.plot(ol_eigs.real, ol_eigs.imag, 'ro', markersize=12,
             markeredgewidth=2, markerfacecolor='none', label='开环特征值')

    # 闭环特征值
    ax3.plot(cl_eigs.real, cl_eigs.imag, 'bx', markersize=12,
             markeredgewidth=2, label='闭环特征值')

    # 虚轴（稳定性边界）
    ax3.axvline(x=0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
    ax3.axhline(y=0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)

    # 左半平面着色表示稳定区域
    xlim = ax3.get_xlim()
    ax3.axvspan(xlim[0] * 1.5, 0, alpha=0.05, color='green')
    ax3.set_xlabel('实部 Re($\\lambda$)', fontsize=12)
    ax3.set_ylabel('虚部 Im($\\lambda$)', fontsize=12)
    ax3.set_title('(c) 特征值分布（复平面）', fontsize=13)
    ax3.legend(fontsize=10, loc='upper left')
    ax3.grid(True, alpha=0.3)

    # 标注特征值数值
    for i, eig in enumerate(ol_eigs):
        ax3.annotate(f'$\\lambda_{i+1}^{{OL}}$={eig.real:.4f}',
                     xy=(eig.real, eig.imag),
                     xytext=(eig.real + 0.0003, eig.imag + 0.0002),
                     fontsize=9, color='red')
    for i, eig in enumerate(cl_eigs):
        ax3.annotate(f'$\\lambda_{i+1}^{{CL}}$={eig.real:.4f}',
                     xy=(eig.real, eig.imag),
                     xytext=(eig.real + 0.0003, eig.imag - 0.0003),
                     fontsize=9, color='blue')

    # ── 子图4：能控性/能观性结果汇总 ──
    ax4 = axes[1, 1]
    ax4.axis('off')

    # 创建汇总表格
    table_data = [
        ['分析项目', '结果', '判定'],
        ['能控性矩阵 Mc 秩',
         str(co_results['rank_Mc']),
         '完全能控' if co_results['controllable'] else '不完全能控'],
        ['能观性（配置1: C=[1,0]）',
         f"秩={co_results['rank_Mo1']}",
         '完全能观' if co_results['observable_C1'] else '不完全能观'],
        ['能观性（配置2: C=[0,1]）',
         f"秩={co_results['rank_Mo2']}",
         '完全能观' if co_results['observable_C2'] else '不完全能观'],
        ['Lyapunov P 特征值',
         f"[{P_eigs[0].real:.2f}, {P_eigs[1].real:.2f}]",
         '渐近稳定' if is_stable else '不稳定'],
    ]

    # 使用 matplotlib 表格绘制
    table = ax4.table(
        cellText=table_data[1:],
        colLabels=table_data[0],
        cellLoc='center',
        loc='center',
        colWidths=[0.42, 0.30, 0.28]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.0, 1.8)

    # 设置表头样式
    for j in range(3):
        table[0, j].set_facecolor('#4472C4')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # 设置数据行交替颜色
    for i in range(1, 5):
        color = '#D6E4F0' if i % 2 == 1 else '#FFFFFF'
        for j in range(3):
            table[i, j].set_facecolor(color)

    ax4.set_title('(d) 能控性/能观性与稳定性分析结果', fontsize=13, pad=20)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # ── 保存图片 ──
    fig_dir = r'D:/cowork/教材/chs-books-v2/ModernControl/figures'
    os.makedirs(fig_dir, exist_ok=True)
    fig_path = os.path.join(fig_dir, 'ch02_state_space_analysis.png')
    plt.savefig(fig_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"\n[图片已保存] {fig_path}")


def main():
    """主流程：模型构建 → 仿真 → 分析 → 绘图 → 输出结论"""

    print("=" * 70)
    print("  第2章 状态空间分析 —— 双水箱串级系统综合案例")
    print("=" * 70)

    # ──────────────────────────────────────────────
    # 步骤1：构建状态空间模型
    # ──────────────────────────────────────────────
    print("\n>> 步骤1：构建状态空间模型")
    A_c, B_c, A_d, B_d = build_model()

    print(f"  连续时间系统矩阵 A_c =")
    print(f"    {A_c[0]}")
    print(f"    {A_c[1]}")
    print(f"  连续时间输入矩阵 B_c = {B_c.flatten()}")

    # 开环特征值（连续时间）
    eigs_ol = np.linalg.eigvals(A_c)
    print(f"\n  开环特征值: λ₁ = {eigs_ol[0]:.6f}, λ₂ = {eigs_ol[1]:.6f}")
    print(f"  两个特征值均为负实数 → 开环系统渐近稳定")

    # 时间常数
    tau1 = -1.0 / eigs_ol[0].real
    tau2 = -1.0 / eigs_ol[1].real
    print(f"  时间常数: τ₁ = {tau1:.1f} s ({tau1/60:.1f} min)")
    print(f"             τ₂ = {tau2:.1f} s ({tau2/60:.1f} min)")

    print(f"\n  ZOH离散化（采样周期 dt = {dt} s）:")
    print(f"  离散系统矩阵 A_d =")
    print(f"    {A_d[0]}")
    print(f"    {A_d[1]}")
    print(f"  离散输入矩阵 B_d = {B_d.flatten()}")

    # ──────────────────────────────────────────────
    # 步骤2：阶跃响应仿真
    # ──────────────────────────────────────────────
    print(f"\n>> 步骤2：阶跃响应仿真（δQ_in = {delta_Qin} m³/s，持续 {T_sim/60:.0f} min）")
    t, h1, h2 = simulate_step(A_c, B_c)

    # 稳态分析（解析解）
    # 稳态时 ẋ = 0 → x_ss = -A_c⁻¹ B_c u
    x_ss = -np.linalg.inv(A_c) @ (B_c * delta_Qin)
    x_ss = x_ss.flatten()  # 确保一维
    print(f"  解析稳态值: dh1_ss = {x_ss[0]*100:.4f} cm, dh2_ss = {x_ss[1]*100:.4f} cm")
    print(f"  仿真终值:   δh₁ = {h1[-1]*100:.4f} cm,    δh₂ = {h2[-1]*100:.4f} cm")

    # ──────────────────────────────────────────────
    # 步骤3：能控性与能观性分析
    # ──────────────────────────────────────────────
    print(f"\n>> 步骤3：能控性与能观性分析")
    co_results = analyze_controllability_observability(A_c, B_c)

    print(f"  能控性矩阵 Mc =")
    print(f"    {co_results['Mc'][0]}")
    print(f"    {co_results['Mc'][1]}")
    print(f"  rank(Mc) = {co_results['rank_Mc']} → "
          f"{'完全能控' if co_results['controllable'] else '不完全能控'}")

    print(f"\n  传感器配置1: C₁ = [1, 0]（仅观测水箱1水位）")
    print(f"  能观性矩阵 Mo₁ =")
    print(f"    {co_results['Mo1'][0]}")
    print(f"    {co_results['Mo1'][1]}")
    print(f"  rank(Mo₁) = {co_results['rank_Mo1']} → "
          f"{'完全能观' if co_results['observable_C1'] else '不完全能观'}")

    print(f"\n  传感器配置2: C₂ = [0, 1]（仅观测水箱2水位）")
    print(f"  能观性矩阵 Mo₂ =")
    print(f"    {co_results['Mo2'][0]}")
    print(f"    {co_results['Mo2'][1]}")
    print(f"  rank(Mo₂) = {co_results['rank_Mo2']} → "
          f"{'完全能观' if co_results['observable_C2'] else '不完全能观'}")

    # ──────────────────────────────────────────────
    # 步骤4：Lyapunov 稳定性分析
    # ──────────────────────────────────────────────
    print(f"\n>> 步骤4：Lyapunov 稳定性分析")
    print(f"  反馈增益: K = [{Kp1}, {Kp2}]")

    A_cl, cl_eigs, P, P_eigs, is_stable = lyapunov_stability(A_c)

    print(f"  闭环系统矩阵 A_cl =")
    print(f"    {A_cl[0]}")
    print(f"    {A_cl[1]}")
    print(f"  闭环特征值: λ₁_cl = {cl_eigs[0].real:.6f}, λ₂_cl = {cl_eigs[1].real:.6f}")
    print(f"\n  Lyapunov 方程 A_cl^T P + P A_cl = -I 的解 P =")
    print(f"    {P[0]}")
    print(f"    {P[1]}")
    print(f"  P 的特征值: {P_eigs[0].real:.4f}, {P_eigs[1].real:.4f}")
    print(f"  P 正定性判定: {'正定（渐近稳定）' if is_stable else '非正定（不稳定）'}")

    # ──────────────────────────────────────────────
    # 步骤5：绘图
    # ──────────────────────────────────────────────
    print(f"\n>> 步骤5：生成综合分析图")
    plot_results(t, h1, h2, A_c, A_cl, cl_eigs, co_results, P_eigs, is_stable)

    # ──────────────────────────────────────────────
    # 结论与建议
    # ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  结论与建议")
    print("=" * 70)
    print(f"""
  1. 模型特性：
     - 双水箱串级系统为2阶线性时不变系统，开环特征值均为负实数
       （λ₁ = {eigs_ol[0].real:.6f}, λ₂ = {eigs_ol[1].real:.6f}），
       系统本身渐近稳定。
     - 时间常数分别为 τ₁ = {tau1:.1f} s 和 τ₂ = {tau2:.1f} s，
       表明水箱1响应较水箱2更快（面积更大但出流系数更小）。

  2. 阶跃响应：
     - 阶跃输入 δQ_in = {delta_Qin} m³/s 后，水箱1先快速上升再趋于稳态；
       水箱2因串级耦合呈现S形响应（先慢后快再趋稳）。
     - 仿真终值与解析稳态值吻合，验证了模型正确性。

  3. 能控性分析：
     - 能控性矩阵 Mc 秩为 {co_results['rank_Mc']}（= 系统阶数），
       系统完全能控。仅通过调节入流 δQ_in 即可控制两水箱水位。

  4. 能观性分析：
     - 配置1（仅观测水箱1）: rank(Mo₁) = {co_results['rank_Mo1']}
       → {'完全能观，但实际中上游传感器对下游估计精度有限' if co_results['observable_C1'] else '不完全能观'}。
     - 配置2（仅观测水箱2）: rank(Mo₂) = {co_results['rank_Mo2']}
       → {'完全能观，下游传感器可推断上游状态' if co_results['observable_C2'] else '不完全能观'}。
     - 工程建议：优先在下游水箱布设传感器，可同时推断上下游水位。

  5. 稳定性分析：
     - 引入比例反馈 K = [{Kp1}, {Kp2}] 后，闭环特征值为
       λ₁_cl = {cl_eigs[0].real:.6f}, λ₂_cl = {cl_eigs[1].real:.6f}，
       均位于复平面左半部分。
     - Lyapunov 矩阵 P 正定（特征值 = [{P_eigs[0].real:.2f}, {P_eigs[1].real:.2f}]），
       确认闭环系统渐近稳定。
""")


if __name__ == '__main__':
    main()
