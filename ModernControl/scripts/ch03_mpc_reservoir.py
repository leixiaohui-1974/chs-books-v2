#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
第3章 模型预测控制（MPC）—— 水库防洪调度仿真
==============================================

问题背景：
    单一水库在汛期面临复杂的调度决策：既要通过预泄腾出防洪库容以拦蓄
    即将到来的洪峰，又要避免水位过低影响供水和发电效益。传统 PI 控制器
    基于当前误差进行反馈调节，无法利用未来入流预报信息。

    模型预测控制（MPC）能够显式纳入未来 Np 步的入流预报，在满足水位
    上下限（防洪限制水位、死水位）和下泄流量约束的前提下，通过滚动优化
    求解最优泄流序列，实现前瞻性调度。

    本例模拟一座中型水库在168小时（7天）内遭遇一次洪峰过程的调度场景：
    - 水库面积:    A_s = 5×10⁶ m²
    - 防洪限制水位: H_flood = 150 m
    - 死水位:       H_dead = 130 m
    - 目标水位:     H_target = 145 m
    - 最大下泄流量: Q_max = 2000 m$^3$/s
    - 时间步长:     dt = 3600 s（1小时）

    入流过程：基流 300 m$^3$/s + 洪峰 800·exp(-0.5·((t-72)/12)²)，
    洪峰于第72小时（第3天）到达，峰值流量约1100 m$^3$/s。

解题思路：
    1. 建立水库水量平衡离散模型:
       H(k+1) = H(k) + dt/A_s · (Q_in(k) - Q_out(k))

    2. MPC 控制器设计:
       - 预测时域 Np = 12 步，控制时域 Nc = 6 步
       - 目标函数: min Σ[w_h·(H(k)-H_target)² + w_u·ΔQ_out(k)²]
         其中 w_h 为水位跟踪权重，w_u 为控制量变化率权重
       - 约束: H_dead ≤ H(k) ≤ H_flood, 0 ≤ Q_out(k) ≤ Q_max
       - 采用 scipy.optimize.minimize（SLSQP）求解二次规划

    3. PI 控制器作为基准对比:
       Q_out(k) = Q_in(k) + Kp·(H(k)-H_target) + Ki·Σ(H-H_target)·dt
       Kp = -0.5, Ki = -0.001

    4. 生成三子图对比两种控制策略的调度效果

代码结构：
    - generate_inflow()     : 生成168小时入流过程（含洪峰）
    - mpc_controller()      : MPC滚动优化控制器
    - pi_controller()       : PI反馈控制器
    - simulate()            : 水库调度仿真主循环
    - plot_results()        : 绘制三子图对比
    - evaluate_performance(): 性能评估与统计
    - main()                : 主流程
"""

import os
import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt

# ── 中文字体配置 ──
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 全局物理参数
# ============================================================
As = 5e6          # 水库面积 [m²]
H_flood = 150.0   # 防洪限制水位 [m]
H_dead = 130.0     # 死水位 [m]
H_target = 145.0   # 目标水位 [m]
Q_max = 2000.0     # 最大下泄流量 [m$^3$/s]
dt = 3600.0        # 时间步长 [s]（1小时）
T_total = 168      # 总仿真时长 [h]（7天）
H0 = 145.0         # 初始水位 [m]

# MPC 参数
Np = 12            # 预测时域 [步]
Nc = 6             # 控制时域 [步]
w_h = 100.0        # 水位跟踪权重
w_u = 0.01         # 控制量变化率权重（惩罚急剧变化）

# PI 参数 (纯反馈，无入流前馈)
Kp_pi = -200.0      # 比例增益 [m3/s / m]（水位偏高1m → 增加泄流200 m3/s）
Ki_pi = -0.02        # 积分增益 [m3/s / (m·s)]


def generate_inflow(N):
    """
    生成入流过程线。

    模型: Q_in(t) = Q_base + Q_peak · exp(-0.5 · ((t - t_peak) / σ)²)

    参数:
        N : int, 时间步数

    返回:
        Q_in : ndarray, shape (N,), 每个时间步的入流量 [m$^3$/s]
    """
    Q_base = 300.0    # 基流 [m$^3$/s]
    Q_peak = 800.0    # 洪峰增量 [m$^3$/s]
    t_peak = 72.0     # 洪峰到达时刻 [h]
    sigma = 12.0      # 洪峰持续宽度参数 [h]

    t = np.arange(N, dtype=float)  # 时间序列 [h]

    # 高斯型洪峰叠加在基流上
    Q_in = Q_base + Q_peak * np.exp(-0.5 * ((t - t_peak) / sigma) ** 2)

    return Q_in


def reservoir_dynamics(H_current, Q_in, Q_out):
    """
    水库水量平衡方程（离散时间）。

    H(k+1) = H(k) + dt / A_s · (Q_in(k) - Q_out(k))

    参数:
        H_current : float, 当前水位 [m]
        Q_in      : float, 当前入流量 [m$^3$/s]
        Q_out     : float, 当前下泄流量 [m$^3$/s]

    返回:
        H_next : float, 下一时刻水位 [m]
    """
    H_next = H_current + dt / As * (Q_in - Q_out)
    return H_next


def mpc_controller(H_current, Q_in_forecast, Q_out_prev):
    """
    MPC 滚动优化控制器。

    在每个时间步，基于当前水位 H_current 和未来 Np 步入流预报，
    求解如下约束优化问题：

        min  Σ_{j=0}^{Np-1} [ w_h · (H_pred(j) - H_target)²
                             + w_u · (ΔQ_out(j))² ]
        s.t. H_dead ≤ H_pred(j) ≤ H_flood,  j = 0,...,Np-1
             0 ≤ Q_out(j) ≤ Q_max,           j = 0,...,Nc-1
             Q_out(j) = Q_out(Nc-1),          j = Nc,...,Np-1  （控制时域外保持）

    其中 ΔQ_out(j) = Q_out(j) - Q_out(j-1)

    参数:
        H_current      : float, 当前水位 [m]
        Q_in_forecast  : ndarray, shape (Np,), 入流预报 [m$^3$/s]
        Q_out_prev     : float, 上一步的下泄流量 [m$^3$/s]（用于计算ΔQ）

    返回:
        Q_out_optimal : float, 本步最优下泄流量 [m$^3$/s]
    """
    # ── 确保入流预报长度至少为 Np ──
    if len(Q_in_forecast) < Np:
        # 不足部分用最后一个值填充
        Q_in_forecast = np.pad(
            Q_in_forecast,
            (0, Np - len(Q_in_forecast)),
            mode='edge'
        )

    def objective(u_vec):
        """
        目标函数：水位跟踪误差 + 控制量变化率惩罚。

        u_vec : 控制时域内的下泄流量序列，shape (Nc,)
        """
        cost = 0.0
        H_pred = H_current  # 从当前水位开始预测

        for j in range(Np):
            # 控制时域内用优化变量，控制时域外保持最后一个值
            if j < Nc:
                Q_out_j = u_vec[j]
            else:
                Q_out_j = u_vec[Nc - 1]

            # 水位预测
            H_pred = H_pred + dt / As * (Q_in_forecast[j] - Q_out_j)

            # 水位跟踪代价
            cost += w_h * (H_pred - H_target) ** 2

            # 控制量变化率代价
            if j == 0:
                delta_u = Q_out_j - Q_out_prev
            elif j < Nc:
                delta_u = Q_out_j - u_vec[j - 1]
            else:
                delta_u = 0.0
            cost += w_u * delta_u ** 2

        return cost

    def constraint_water_level(u_vec):
        """
        不等式约束函数（返回值 >= 0 时满足约束）。

        同时处理上限和下限：
          H_dead ≤ H_pred(j) ≤ H_flood
        等价于:
          H_pred(j) - H_dead ≥ 0    (下限)
          H_flood - H_pred(j) ≥ 0    (上限)
        """
        constraints = []
        H_pred = H_current

        for j in range(Np):
            if j < Nc:
                Q_out_j = u_vec[j]
            else:
                Q_out_j = u_vec[Nc - 1]

            H_pred = H_pred + dt / As * (Q_in_forecast[j] - Q_out_j)

            # 下限约束: H_pred - H_dead ≥ 0
            constraints.append(H_pred - H_dead)
            # 上限约束: H_flood - H_pred ≥ 0
            constraints.append(H_flood - H_pred)

        return np.array(constraints)

    # ── 初始猜测：泄流量等于预报入流量的均值 ──
    u0 = np.full(Nc, np.mean(Q_in_forecast[:Nc]))

    # ── 控制量边界约束 ──
    bounds = [(0.0, Q_max)] * Nc

    # ── 水位约束 ──
    cons = {'type': 'ineq', 'fun': constraint_water_level}

    # ── 求解优化问题 ──
    result = minimize(
        objective,
        u0,
        method='SLSQP',
        bounds=bounds,
        constraints=cons,
        options={'maxiter': 200, 'ftol': 1e-8}
    )

    # 仅取第一步的最优控制量（滚动时域策略）
    Q_out_optimal = np.clip(result.x[0], 0.0, Q_max)

    return Q_out_optimal


def pi_controller(H_current, Q_in_current, integral_error):
    """
    PI 控制器（纯反馈，不含入流前馈）。

    控制律: Q_out = Q_base + Kp · e(k) + Ki · Sum_e·dt
    其中误差 e(k) = H(k) - H_target
    Q_base 为基准泄流量（设为额定入流 300 m3/s）。

    PI控制器仅基于当前水位误差进行反馈调节，不利用入流信息，
    这是传统水库调度中常见的简单反馈策略。

    参数:
        H_current       : float, 当前水位 [m]
        Q_in_current    : float, 当前入流量 [m$^3$/s]（PI不使用）
        integral_error  : float, 误差积分 [m·s]

    返回:
        Q_out      : float, 下泄流量 [m$^3$/s]
        new_integral : float, 更新后的误差积分
    """
    Q_base = 300.0  # 基准泄流 = 设计基流 [m3/s]
    error = H_current - H_target  # 水位偏差

    # 更新积分项
    new_integral = integral_error + error * dt

    # PI 控制律（纯反馈）
    # 水位偏高时 error > 0，Kp_pi < 0 → -Kp_pi*error > 0 → 增大泄流
    Q_out = Q_base - Kp_pi * error - Ki_pi * new_integral

    # 限幅：泄流量不能为负，也不能超过最大值
    Q_out = np.clip(Q_out, 0.0, Q_max)

    return Q_out, new_integral


def simulate():
    """
    水库调度仿真主循环，分别运行 MPC 和 PI 两种控制策略。

    返回:
        time_hours : ndarray, 时间序列 [h]
        Q_in       : ndarray, 入流过程 [m$^3$/s]
        H_mpc      : ndarray, MPC 水位过程 [m]
        Q_out_mpc  : ndarray, MPC 下泄流量 [m$^3$/s]
        H_pi       : ndarray, PI 水位过程 [m]
        Q_out_pi   : ndarray, PI 下泄流量 [m$^3$/s]
    """
    # ── 生成入流过程 ──
    Q_in = generate_inflow(T_total)
    time_hours = np.arange(T_total, dtype=float)

    # ── 存储数组初始化 ──
    H_mpc = np.zeros(T_total + 1)
    Q_out_mpc = np.zeros(T_total)
    H_pi = np.zeros(T_total + 1)
    Q_out_pi = np.zeros(T_total)

    H_mpc[0] = H0
    H_pi[0] = H0

    # PI 积分项初始化
    integral_error = 0.0
    # MPC 上一步泄流量初始化
    Q_out_prev_mpc = Q_in[0]  # 初始泄流 = 入流（维持水位不变）

    print(f"\n  仿真进行中（共 {T_total} 步）...")

    for k in range(T_total):
        # ── MPC 控制 ──
        # 提取未来 Np 步入流预报（假设完美预报）
        forecast_end = min(k + Np, T_total)
        Q_in_forecast = Q_in[k:forecast_end]

        Q_out_mpc[k] = mpc_controller(H_mpc[k], Q_in_forecast, Q_out_prev_mpc)
        H_mpc[k + 1] = reservoir_dynamics(H_mpc[k], Q_in[k], Q_out_mpc[k])
        Q_out_prev_mpc = Q_out_mpc[k]

        # ── PI 控制 ──
        Q_out_pi[k], integral_error = pi_controller(
            H_pi[k], Q_in[k], integral_error
        )
        H_pi[k + 1] = reservoir_dynamics(H_pi[k], Q_in[k], Q_out_pi[k])

        # 进度提示（每24小时报告一次）
        if (k + 1) % 24 == 0:
            print(f"    第 {k+1:3d} 小时 (第{(k+1)//24}天): "
                  f"H_mpc={H_mpc[k+1]:.2f}m, H_pi={H_pi[k+1]:.2f}m")

    return time_hours, Q_in, H_mpc, Q_out_mpc, H_pi, Q_out_pi


def evaluate_performance(H_mpc, Q_out_mpc, H_pi, Q_out_pi, Q_in):
    """
    性能评估：比较 MPC 与 PI 的调度效果。

    指标：
    1. 水位偏差 RMSE（相对于目标水位）
    2. 最大水位（是否逼近/超过防洪限制水位）
    3. 最小水位（是否逼近/低于死水位）
    4. 最大泄流量（越小对下游越安全）
    5. 泄流平稳性（泄流量变化率的标准差）
    """
    # 去掉初始值，只分析仿真过程
    H_mpc_proc = H_mpc[1:]
    H_pi_proc = H_pi[1:]

    # RMSE
    rmse_mpc = np.sqrt(np.mean((H_mpc_proc - H_target) ** 2))
    rmse_pi = np.sqrt(np.mean((H_pi_proc - H_target) ** 2))

    # 最大/最小水位
    H_max_mpc = np.max(H_mpc_proc)
    H_max_pi = np.max(H_pi_proc)
    H_min_mpc = np.min(H_mpc_proc)
    H_min_pi = np.min(H_pi_proc)

    # 最大泄流
    Q_max_mpc = np.max(Q_out_mpc)
    Q_max_pi = np.max(Q_out_pi)

    # 泄流平稳性（变化率标准差）
    dQ_mpc = np.diff(Q_out_mpc)
    dQ_pi = np.diff(Q_out_pi)
    smooth_mpc = np.std(dQ_mpc)
    smooth_pi = np.std(dQ_pi)

    # 洪峰削减率
    Q_in_peak = np.max(Q_in)
    peak_red_mpc = (1.0 - Q_max_mpc / Q_in_peak) * 100
    peak_red_pi = (1.0 - Q_max_pi / Q_in_peak) * 100

    metrics = {
        'rmse': (rmse_mpc, rmse_pi),
        'H_max': (H_max_mpc, H_max_pi),
        'H_min': (H_min_mpc, H_min_pi),
        'Q_max': (Q_max_mpc, Q_max_pi),
        'smoothness': (smooth_mpc, smooth_pi),
        'peak_reduction': (peak_red_mpc, peak_red_pi),
        'Q_in_peak': Q_in_peak,
    }

    return metrics


def plot_results(time_hours, Q_in, H_mpc, Q_out_mpc, H_pi, Q_out_pi):
    """
    绘制三子图：
        (a) 入流过程线
        (b) 水位过程线（MPC vs PI，含防洪/死水位限）
        (c) 下泄流量过程线（MPC vs PI）
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    fig.suptitle('第3章 模型预测控制（MPC）—— 水库防洪调度仿真',
                 fontsize=16, fontweight='bold')

    # ── 子图(a)：入流过程线 ──
    ax1 = axes[0]
    ax1.fill_between(time_hours, 0, Q_in, alpha=0.3, color='steelblue')
    ax1.plot(time_hours, Q_in, 'b-', linewidth=2, label='入库流量 $Q_{in}$')

    # 标注洪峰
    peak_idx = np.argmax(Q_in)
    ax1.annotate(f'洪峰: {Q_in[peak_idx]:.0f} m$^3$/s\n(第{peak_idx}小时)',
                 xy=(time_hours[peak_idx], Q_in[peak_idx]),
                 xytext=(time_hours[peak_idx] + 15, Q_in[peak_idx] - 50),
                 arrowprops=dict(arrowstyle='->', color='darkblue'),
                 fontsize=11, color='darkblue')

    ax1.set_ylabel('流量 [m$^3$/s]', fontsize=12)
    ax1.set_title('(a) 入库流量过程线', fontsize=13)
    ax1.legend(fontsize=11, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)

    # ── 子图(b)：水位过程线 ──
    ax2 = axes[1]
    time_h_ext = np.arange(T_total + 1, dtype=float)  # 水位多一个点（包含末时刻）

    ax2.plot(time_h_ext, H_mpc, 'r-', linewidth=2.0, label='MPC 水位')
    ax2.plot(time_h_ext, H_pi, 'g--', linewidth=2.0, label='PI 水位')
    ax2.axhline(y=H_flood, color='darkred', linestyle='-.', linewidth=1.5,
                label=f'防洪限制水位 ({H_flood} m)')
    ax2.axhline(y=H_dead, color='orange', linestyle='-.', linewidth=1.5,
                label=f'死水位 ({H_dead} m)')
    ax2.axhline(y=H_target, color='gray', linestyle=':', linewidth=1.2,
                label=f'目标水位 ({H_target} m)')

    # 安全区间着色
    ax2.axhspan(H_dead, H_flood, alpha=0.05, color='green')

    ax2.set_ylabel('水位 [m]', fontsize=12)
    ax2.set_title('(b) 水库水位过程线', fontsize=13)
    ax2.legend(fontsize=10, loc='upper right', ncol=2)
    ax2.grid(True, alpha=0.3)

    # 动态Y轴范围
    all_H = np.concatenate([H_mpc, H_pi])
    y_margin = 2.0
    ax2.set_ylim(min(np.min(all_H), H_dead) - y_margin,
                 max(np.max(all_H), H_flood) + y_margin)

    # ── 子图(c)：下泄流量过程线 ──
    ax3 = axes[2]
    ax3.plot(time_hours, Q_out_mpc, 'r-', linewidth=2.0, label='MPC 下泄流量')
    ax3.plot(time_hours, Q_out_pi, 'g--', linewidth=2.0, label='PI 下泄流量')
    ax3.plot(time_hours, Q_in, 'b:', linewidth=1.0, alpha=0.5, label='入库流量（参考）')

    # 标注最大泄流
    peak_mpc_idx = np.argmax(Q_out_mpc)
    peak_pi_idx = np.argmax(Q_out_pi)
    ax3.annotate(f'MPC峰值: {Q_out_mpc[peak_mpc_idx]:.0f}',
                 xy=(time_hours[peak_mpc_idx], Q_out_mpc[peak_mpc_idx]),
                 xytext=(time_hours[peak_mpc_idx] + 10,
                         Q_out_mpc[peak_mpc_idx] + 60),
                 arrowprops=dict(arrowstyle='->', color='red'),
                 fontsize=10, color='red')

    ax3.set_xlabel('时间 [h]', fontsize=12)
    ax3.set_ylabel('流量 [m$^3$/s]', fontsize=12)
    ax3.set_title('(c) 下泄流量过程线', fontsize=13)
    ax3.legend(fontsize=10, loc='upper right')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(bottom=0)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # ── 保存图片 ──
    fig_dir = r'D:/cowork/教材/chs-books-v2/ModernControl/figures'
    os.makedirs(fig_dir, exist_ok=True)
    fig_path = os.path.join(fig_dir, 'ch03_mpc_reservoir.png')
    plt.savefig(fig_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"\n[图片已保存] {fig_path}")


def main():
    """主流程：参数打印 → 仿真 → 评估 → 绘图 → 输出结论"""

    print("=" * 70)
    print("  第3章 模型预测控制（MPC）—— 水库防洪调度仿真")
    print("=" * 70)

    # ──────────────────────────────────────────────
    # 参数总览
    # ──────────────────────────────────────────────
    print("\n>> 水库参数:")
    print(f"  水库面积 A_s = {As:.0e} m²")
    print(f"  防洪限制水位 = {H_flood} m")
    print(f"  死水位 = {H_dead} m")
    print(f"  目标水位 = {H_target} m")
    print(f"  最大下泄流量 = {Q_max} m3/s")
    print(f"  初始水位 = {H0} m")
    print(f"  时间步长 = {dt} s（{dt/3600:.0f} 小时）")
    print(f"  仿真时长 = {T_total} h（{T_total/24:.0f} 天）")

    print(f"\n>> MPC 参数:")
    print(f"  预测时域 Np = {Np}")
    print(f"  控制时域 Nc = {Nc}")
    print(f"  水位跟踪权重 w_h = {w_h}")
    print(f"  控制变化率权重 w_u = {w_u}")

    print(f"\n>> PI 参数:")
    print(f"  比例增益 Kp = {Kp_pi}")
    print(f"  积分增益 Ki = {Ki_pi}")

    # ──────────────────────────────────────────────
    # 入流过程
    # ──────────────────────────────────────────────
    Q_in = generate_inflow(T_total)
    print(f"\n>> 入流过程:")
    print(f"  基流 = 300 m3/s")
    print(f"  洪峰流量 = {np.max(Q_in):.1f} m3/s（第{np.argmax(Q_in)}小时）")
    print(f"  洪峰持续时间 ≈ 48小时（显著高于基流的时段）")

    # ──────────────────────────────────────────────
    # 仿真
    # ──────────────────────────────────────────────
    print("\n>> 运行调度仿真...")
    time_hours, Q_in, H_mpc, Q_out_mpc, H_pi, Q_out_pi = simulate()

    # ──────────────────────────────────────────────
    # 性能评估
    # ──────────────────────────────────────────────
    print("\n>> 性能评估:")
    metrics = evaluate_performance(H_mpc, Q_out_mpc, H_pi, Q_out_pi, Q_in)

    rmse_mpc, rmse_pi = metrics['rmse']
    H_max_mpc, H_max_pi = metrics['H_max']
    H_min_mpc, H_min_pi = metrics['H_min']
    Q_max_mpc, Q_max_pi = metrics['Q_max']
    smooth_mpc, smooth_pi = metrics['smoothness']
    peak_red_mpc, peak_red_pi = metrics['peak_reduction']

    print(f"\n  {'指标':<24s} {'MPC':>12s} {'PI':>12s} {'优势':>8s}")
    print(f"  {'-'*60}")
    print(f"  {'水位RMSE [m]':<24s} {rmse_mpc:>12.4f} {rmse_pi:>12.4f} "
          f"{'MPC' if rmse_mpc < rmse_pi else 'PI':>8s}")
    print(f"  {'最高水位 [m]':<24s} {H_max_mpc:>12.2f} {H_max_pi:>12.2f} "
          f"{'MPC' if H_max_mpc < H_max_pi else 'PI':>8s}")
    print(f"  {'最低水位 [m]':<24s} {H_min_mpc:>12.2f} {H_min_pi:>12.2f} "
          f"{'MPC' if H_min_mpc > H_min_pi else 'PI':>8s}")
    print(f"  {'最大泄流 [m3/s]':<24s} {Q_max_mpc:>12.1f} {Q_max_pi:>12.1f} "
          f"{'MPC' if Q_max_mpc < Q_max_pi else 'PI':>8s}")
    print(f"  {'泄流平稳性 σ(ΔQ)':<24s} {smooth_mpc:>12.2f} {smooth_pi:>12.2f} "
          f"{'MPC' if smooth_mpc < smooth_pi else 'PI':>8s}")
    print(f"  {'洪峰削减率 [%]':<24s} {peak_red_mpc:>12.1f} {peak_red_pi:>12.1f} "
          f"{'MPC' if peak_red_mpc > peak_red_pi else 'PI':>8s}")

    # ──────────────────────────────────────────────
    # 绘图
    # ──────────────────────────────────────────────
    print("\n>> 生成对比图...")
    plot_results(time_hours, Q_in, H_mpc, Q_out_mpc, H_pi, Q_out_pi)

    # ──────────────────────────────────────────────
    # 结论与建议
    # ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  结论与建议")
    print("=" * 70)
    print(f"""
  1. 水位控制精度：
     - MPC 的水位 RMSE = {rmse_mpc:.4f} m，PI 的水位 RMSE = {rmse_pi:.4f} m。
     - MPC 利用未来 {Np} 小时的入流预报信息，能够提前预泄腾库，
       在洪峰到来前主动降低水位，为蓄洪留出更多库容。

  2. 防洪安全性：
     - MPC 最高水位 = {H_max_mpc:.2f} m，PI 最高水位 = {H_max_pi:.2f} m。
     - MPC 通过前瞻性调度，有效降低了洪峰期间的水位峰值，
       距防洪限制水位 ({H_flood} m) 保持了更大的安全裕度。

  3. 下游防洪效果：
     - MPC 最大泄流 = {Q_max_mpc:.1f} m3/s，PI 最大泄流 = {Q_max_pi:.1f} m3/s。
     - MPC 洪峰削减率 = {peak_red_mpc:.1f}%，PI 洪峰削减率 = {peak_red_pi:.1f}%。
     - MPC 能够将泄流过程"削峰填谷"，减小对下游河道的冲击。

  4. 调度平稳性：
     - MPC 泄流变化率标准差 σ(ΔQ) = {smooth_mpc:.2f}，
       PI 泄流变化率标准差 σ(ΔQ) = {smooth_pi:.2f}。
     - 较小的变化率意味着闸门调节更平稳，有利于机械设备保护
       和下游河道的流态稳定。

  5. 工程应用建议：
     - MPC 的优势依赖于准确的入流预报。在实际工程中，需配合
       水文预报模型（如新安江模型、LSTM降雨-径流模型）提供
       未来 12-24 小时的入流预测。
     - 预报不确定性可通过鲁棒 MPC 或随机 MPC 来处理。
     - PI 控制作为备用方案（当预报系统故障时）仍具有工程价值。
""")


if __name__ == '__main__':
    main()
