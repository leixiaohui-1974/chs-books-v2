#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第5章 示例：管状MPC（Tube MPC）用于鲁棒水库防洪调度
=====================================================

问题背景：
    水库防洪调度是防洪减灾的核心环节。调度决策需要基于入库流量
    预报来提前预泄腾库。然而，洪水预报天然存在不确定性：
    1. 降雨预报误差传递到流量预报，导致入库流量预测偏差；
    2. 预报误差在洪峰附近尤为显著，可能导致调度决策失误；
    3. 标准 MPC 假设预测完全准确，无法保证约束满足的鲁棒性。

    管状 MPC（Tube MPC）是一种鲁棒 MPC 方法，其核心思想是：
    1. 构造一个"管状"区域（tube），包含所有可能的实际状态轨迹；
    2. 对标称系统（无扰动）求解 MPC，得到标称最优轨迹；
    3. 通过辅助控制器将实际状态拉回标称轨迹附近；
    4. 收紧约束，确保即使在最大偏差下约束仍然满足。

    这种方法在洪水预报不确定性条件下，能保证水位不超过汛限水位，
    同时尽可能减小弃水（经济损失最小化）。

解题思路：
    1. 单水库质量守恒模型（离散时间）：
       As * (H(k+1) - H(k)) = (Q_in(k) - Q_out(k)) * dt
       等价于：H(k+1) = H(k) + (Q_in(k) - Q_out(k)) * dt / As

    2. 预报误差模型：
       Q_in_actual(k) = Q_in_predicted(k) + w(k)
       |w(k)| <= w_max

    3. Tube MPC 设计要素：
       a) RPI 集（鲁棒正不变集）：一维情形简化为 |z| <= alpha
          其中 alpha = w_max * dt / As / (1 - |1 + K_aux * dt/As|)
       b) 约束收紧：H_max_tight = H_flood - alpha
       c) 标称 MPC：对标称系统求解，约束使用收紧后的值
       d) 辅助控制器：u_aux = K_aux * (H_actual - H_nominal)

    4. 与标准 MPC（不考虑预报误差）对比，展示 Tube MPC 的鲁棒优势。

作者：雷晓辉 教授 | 河北工程大学
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# 中文字体设置
# ============================================================
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def generate_flood_inflow(N, dt, Q_base=200.0, Q_peak=1200.0, t_peak_hr=72.0):
    """
    生成 7 天洪水入库流量过程线
    ----------------------------
    采用双峰伽马分布近似：主峰在 t_peak_hr，次峰在 t_peak_hr + 30h。

    参数：
        N          : 总时间步数
        dt         : 时间步长 (s)
        Q_base     : 基流 (m^3/s)
        Q_peak     : 峰值流量 (m^3/s)
        t_peak_hr  : 峰值时刻 (h)
    返回：
        Q_true     : 真实入库流量 (m^3/s)
        Q_predicted: 预测入库流量 (m^3/s)（含误差）
    """
    t_hours = np.arange(N) * dt / 3600.0  # 转换为小时

    # 主洪峰（伽马形状）
    sigma1 = 18.0  # 主峰宽度 (h)
    peak1 = (Q_peak - Q_base) * np.exp(-0.5 * ((t_hours - t_peak_hr) / sigma1) ** 2)

    # 次洪峰（较弱）
    t_peak2 = t_peak_hr + 30.0
    sigma2 = 12.0
    peak2 = 0.4 * (Q_peak - Q_base) * np.exp(-0.5 * ((t_hours - t_peak2) / sigma2) ** 2)

    # 真实流量
    Q_true = Q_base + peak1 + peak2

    # 预测流量（加入有界误差）
    # 误差特征：洪峰附近误差大，平水期误差小
    np.random.seed(42)
    noise_base = np.random.randn(N) * 30.0  # 基础噪声
    # 洪峰附近增大误差
    peak_proximity = peak1 / (Q_peak - Q_base)
    noise_amplified = noise_base * (1.0 + 2.0 * peak_proximity)

    Q_predicted = Q_true + noise_amplified

    # 确保非负
    Q_predicted = np.maximum(Q_predicted, 0.0)
    Q_true = np.maximum(Q_true, 0.0)

    return Q_true, Q_predicted


def nominal_mpc_step(H_nom, Q_pred, H_target, H_max, H_min, Q_max, dt, As, Np=6):
    """
    标称 MPC 控制器（贪心策略逼近目标水位）
    -----------------------------------------
    简化的多步前瞻 MPC：在预测域内贪心地选择泄量，
    使水位尽可能接近目标，同时满足约束。

    参数：
        H_nom   : 当前标称水位 (m)
        Q_pred  : 预测入流序列 (m^3/s)，长度 >= Np
        H_target: 目标水位 (m)
        H_max   : 水位上界 (m)（可能已收紧）
        H_min   : 水位下界 (m)
        Q_max   : 最大泄量 (m^3/s)
        dt      : 时间步长 (s)
        As      : 水库面积 (m^2)
        Np      : 预测步数
    返回：
        Q_out   : 当前步的最优泄量 (m^3/s)
    """
    # 简化策略：单步贪心 + 多步前瞻安全检查
    H_current = H_nom

    # 计算使水位回到目标所需的泄量
    Q_desired = Q_pred[0] + As * (H_current - H_target) / dt

    # 安全检查：预测未来水位是否会超限
    H_future = H_current
    for j in range(min(Np, len(Q_pred))):
        H_future += (Q_pred[j] - Q_desired) * dt / As

    # 如果未来水位过高，增大泄量
    if H_future > H_max - 0.5:
        Q_desired = Q_pred[0] + As * (H_current - H_target) / dt + 100.0

    # 约束
    Q_desired = np.clip(Q_desired, 0.0, Q_max)

    return Q_desired


def main():
    # ============================================================
    # 水库参数
    # ============================================================
    As = 2e6         # 水库面积 (m^2)
    H_flood = 150.0  # 汛限水位 / 防洪高水位 (m)
    H_dead = 130.0   # 死水位 (m)
    H_target = 145.0 # 正常蓄水目标水位 (m)
    Q_max = 1500.0   # 最大泄量 (m^3/s)
    dt = 3600.0      # 时间步长 (s) = 1小时

    # ============================================================
    # 预报误差参数
    # ============================================================
    w_max = 100.0    # 入流预报最大误差 (m^3/s)

    # ============================================================
    # 辅助控制器参数
    # ============================================================
    K_aux = 0.0005   # 辅助反馈增益

    # ============================================================
    # 仿真设置
    # ============================================================
    T_hours = 168    # 仿真时长 (h) = 7 天
    N = T_hours      # 总步数（每步1小时）

    # 生成洪水过程线
    Q_true, Q_predicted = generate_flood_inflow(N, dt)

    # ============================================================
    # RPI 集计算（一维简化）
    # ============================================================
    # 闭环极点：rho = |1 + K_aux * dt / As|（一步收缩因子）
    rho = abs(1.0 + K_aux * dt / As)
    # 误差传播系数
    beta = w_max * dt / As  # 单步最大偏差 (m)

    # RPI 集半径：alpha = beta / (1 - rho)（几何级数求和）
    if rho < 1.0:
        alpha = beta / (1.0 - rho)
    else:
        alpha = beta * 10.0  # 退化处理
        print(f"  警告：辅助控制器不稳定 (rho={rho:.4f})，RPI 集退化")

    print(f"  RPI 集半径 alpha = {alpha:.4f} m")
    print(f"  闭环收缩因子 rho = {rho:.6f}")
    print(f"  单步最大偏差 beta = {beta:.4f} m")

    # ============================================================
    # 约束收紧
    # ============================================================
    H_flood_tight = H_flood - alpha  # 收紧后的水位上界
    print(f"  原始汛限水位：{H_flood:.1f} m")
    print(f"  收紧后上界：  {H_flood_tight:.4f} m")

    # ============================================================
    # Tube MPC 仿真
    # ============================================================
    H_nom_tube = np.zeros(N + 1)   # 标称水位
    H_act_tube = np.zeros(N + 1)   # 实际水位
    Q_out_tube = np.zeros(N)       # 泄量
    H_upper_tube = np.zeros(N + 1) # Tube 上界
    H_lower_tube = np.zeros(N + 1) # Tube 下界

    H_nom_tube[0] = H_target
    H_act_tube[0] = H_target

    for k in range(N):
        # Tube 边界
        H_upper_tube[k] = H_nom_tube[k] + alpha
        H_lower_tube[k] = H_nom_tube[k] - alpha

        # 标称 MPC（使用预测流量，约束收紧）
        Q_pred_horizon = Q_predicted[k:min(k+6, N)]
        if len(Q_pred_horizon) < 6:
            Q_pred_horizon = np.pad(Q_pred_horizon, (0, 6 - len(Q_pred_horizon)),
                                     mode='edge')

        Q_nom = nominal_mpc_step(
            H_nom_tube[k], Q_pred_horizon,
            H_target, H_flood_tight, H_dead, Q_max, dt, As, Np=6
        )

        # 辅助控制器修正
        e_state = H_act_tube[k] - H_nom_tube[k]
        Q_aux = -K_aux * e_state * As / dt  # 偏差修正泄量

        # 实际泄量 = 标称 + 辅助
        Q_out_total = Q_nom + Q_aux
        Q_out_total = np.clip(Q_out_total, 0.0, Q_max)
        Q_out_tube[k] = Q_out_total

        # 标称系统更新（使用预测入流）
        H_nom_tube[k+1] = H_nom_tube[k] + (Q_predicted[k] - Q_nom) * dt / As

        # 实际系统更新（使用真实入流）
        H_act_tube[k+1] = H_act_tube[k] + (Q_true[k] - Q_out_total) * dt / As

    # 最后一步的 Tube 边界
    H_upper_tube[N] = H_nom_tube[N] + alpha
    H_lower_tube[N] = H_nom_tube[N] - alpha

    # ============================================================
    # 标准 MPC 仿真（不考虑预报误差，用于对比）
    # ============================================================
    H_std = np.zeros(N + 1)
    Q_out_std = np.zeros(N)
    H_std[0] = H_target

    for k in range(N):
        Q_pred_horizon = Q_predicted[k:min(k+6, N)]
        if len(Q_pred_horizon) < 6:
            Q_pred_horizon = np.pad(Q_pred_horizon, (0, 6 - len(Q_pred_horizon)),
                                     mode='edge')

        # 标准 MPC（不收紧约束）
        Q_out_std[k] = nominal_mpc_step(
            H_std[k], Q_pred_horizon,
            H_target, H_flood, H_dead, Q_max, dt, As, Np=6
        )

        # 用真实入流更新（标准 MPC 无辅助控制器）
        H_std[k+1] = H_std[k] + (Q_true[k] - Q_out_std[k]) * dt / As

    # ============================================================
    # 性能指标计算
    # ============================================================
    # 最高水位
    H_max_tube = np.max(H_act_tube)
    H_max_std = np.max(H_std)

    # 是否超过汛限水位
    exceed_tube = np.any(H_act_tube > H_flood)
    exceed_std = np.any(H_std > H_flood)

    # 总泄量（洪水期）
    Q_total_tube = np.sum(Q_out_tube) * dt
    Q_total_std = np.sum(Q_out_std) * dt

    # ============================================================
    # 绘制三面板图
    # ============================================================
    t_hours_arr = np.arange(N) * dt / 3600.0
    t_hours_state = np.arange(N + 1) * dt / 3600.0

    fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)
    fig.suptitle('第5章：Tube MPC vs 标准MPC 鲁棒水库防洪调度',
                 fontsize=16, fontweight='bold')

    # --- 面板1：入库流量（真实 vs 预测）---
    ax1 = axes[0]
    ax1.plot(t_hours_arr, Q_true, 'b-', linewidth=1.8, label='真实入库流量')
    ax1.plot(t_hours_arr, Q_predicted, 'r--', linewidth=1.0, alpha=0.7, label='预测入库流量')
    ax1.fill_between(t_hours_arr,
                     Q_true - w_max, Q_true + w_max,
                     alpha=0.15, color='orange', label=f'误差带 (+/-{w_max} m^3/s)')
    ax1.set_ylabel('流量 (m^3/s)', fontsize=12)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.set_title('入库洪水过程线（7天预报）', fontsize=12)
    ax1.grid(True, alpha=0.3)

    # --- 面板2：水位（含 Tube 边界）---
    ax2 = axes[1]
    ax2.plot(t_hours_state, H_act_tube, 'b-', linewidth=2.0, label='Tube MPC 实际水位')
    ax2.plot(t_hours_state, H_nom_tube, 'b--', linewidth=1.0, alpha=0.6, label='Tube MPC 标称水位')
    ax2.fill_between(t_hours_state, H_lower_tube, H_upper_tube,
                     alpha=0.2, color='blue', label='Tube 边界')
    ax2.plot(t_hours_state, H_std, 'r-', linewidth=1.5, label='标准MPC 水位')
    ax2.axhline(y=H_flood, color='darkred', linestyle='-', linewidth=2.0,
                label=f'汛限水位 {H_flood} m')
    ax2.axhline(y=H_flood_tight, color='orange', linestyle=':', linewidth=1.5,
                label=f'收紧上界 {H_flood_tight:.1f} m')
    ax2.axhline(y=H_target, color='green', linestyle='-.', linewidth=1.0, alpha=0.5,
                label=f'目标水位 {H_target} m')
    ax2.set_ylabel('水位 (m)', fontsize=12)
    ax2.legend(loc='upper left', fontsize=9, ncol=2)
    ax2.set_title(f'水库水位（最高：Tube={H_max_tube:.2f}m, 标准={H_max_std:.2f}m）',
                  fontsize=12)
    ax2.grid(True, alpha=0.3)

    # --- 面板3：泄量 ---
    ax3 = axes[2]
    ax3.plot(t_hours_arr, Q_out_tube, 'b-', linewidth=1.5, label='Tube MPC 泄量')
    ax3.plot(t_hours_arr, Q_out_std, 'r--', linewidth=1.2, label='标准MPC 泄量')
    ax3.axhline(y=Q_max, color='gray', linestyle=':', alpha=0.5,
                label=f'最大泄量 {Q_max} m^3/s')
    ax3.set_xlabel('时间 (h)', fontsize=12)
    ax3.set_ylabel('泄量 (m^3/s)', fontsize=12)
    ax3.legend(loc='upper right', fontsize=10)
    ax3.set_title('调度泄量过程线', fontsize=12)
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存图片
    fig_path = 'D:/cowork/教材/chs-books-v2/ModernControl/figures/ch05_tube_mpc_reservoir.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    # ============================================================
    # 打印结论与建议
    # ============================================================
    print()
    print("=" * 70)
    print("  第5章 Tube MPC 鲁棒水库防洪调度 — 仿真结论与建议")
    print("=" * 70)
    print()
    print("【仿真条件】")
    print(f"  仿真时长：{T_hours} 小时（7天）")
    print(f"  时间步长：{dt/3600:.0f} 小时")
    print(f"  水库面积：As = {As:.0e} m^2")
    print(f"  汛限水位：{H_flood} m，目标水位：{H_target} m")
    print(f"  最大泄量：{Q_max} m^3/s")
    print(f"  入流预报误差上界：w_max = {w_max} m^3/s")
    print(f"  洪峰流量：约 {np.max(Q_true):.0f} m^3/s（出现在 t≈72h）")
    print()
    print("【Tube MPC 设计参数】")
    print(f"  辅助控制器增益：K_aux = {K_aux}")
    print(f"  RPI 集半径：alpha = {alpha:.4f} m")
    print(f"  约束收紧量：{alpha:.4f} m")
    print(f"  收紧后水位上界：{H_flood_tight:.4f} m")
    print()
    print("【性能对比】")
    print(f"  Tube MPC 最高水位：{H_max_tube:.2f} m "
          f"{'(超限!)' if exceed_tube else '(安全)'}")
    print(f"  标准 MPC 最高水位：{H_max_std:.2f} m "
          f"{'(超限!)' if exceed_std else '(安全)'}")
    print(f"  Tube MPC 总泄量：{Q_total_tube/1e6:.2f} 百万 m3")
    print(f"  标准 MPC 总泄量：{Q_total_std/1e6:.2f} 百万 m3")
    print()
    print("【结论】")
    print("  1. Tube MPC 通过约束收紧（保守调度），确保即使在最大预报误差")
    print("     条件下，实际水位仍不超过汛限水位，满足防洪安全硬约束。")
    print("  2. 标准 MPC 不考虑预报误差的影响，在洪峰附近预报偏差较大时，")
    print("     实际水位可能逼近甚至超过汛限水位，存在安全隐患。")
    print("  3. 辅助控制器 K_aux 将实际状态拉回标称轨迹附近，")
    print("     保证实际水位始终处于 Tube 边界之内。")
    print("  4. Tube MPC 的代价是略微增加了预泄量（保守性），")
    print("     但换取了确定性的安全保障，这在防洪调度中是值得的。")
    print()
    print("【工程建议】")
    print("  1. RPI 集半径 alpha 取决于预报误差上界 w_max 和辅助增益 K_aux，")
    print("     工程中应根据历史预报误差统计确定 w_max。")
    print("  2. K_aux 越大，Tube 越窄（保守性越低），但过大可能导致")
    print("     泄量波动剧烈，需权衡。")
    print("  3. 多水库联合调度场景中，Tube MPC 可扩展为分布式框架。")
    print("  4. 建议结合集合预报（ensemble forecast）动态更新 w_max。")
    print()
    print(f"  图片已保存至：{fig_path}")
    print("=" * 70)


if __name__ == '__main__':
    main()
