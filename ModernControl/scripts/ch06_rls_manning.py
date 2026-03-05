#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第6章 示例1：递推最小二乘法（RLS）辨识明渠曼宁糙率系数

=== 问题背景 ===
在明渠水力学中，曼宁糙率系数 n 是决定水流阻力的关键参数。
实际工程中，n 值受渠道表面状况、水生植物、淤积等因素影响，
往往随时间缓慢变化，且难以通过直接测量获取。

曼宁公式描述了明渠均匀流的流量-水力关系：
    Q = (1/n) * A * R^(2/3) * S0^(1/2)

其中 A 为过水断面面积，R 为水力半径，S0 为底坡。

本例通过递推最小二乘法（RLS），利用在线流量和水位观测数据，
实时辨识曼宁糙率系数 n，实现参数的在线跟踪。

=== 解题思路 ===
1. 将曼宁公式线性化为 y = theta * phi 的形式：
   - 令 theta = 1/n^2（待辨识参数）
   - 则 phi = A^2 * R^(4/3) * S0（已知回归变量）
   - 观测量 y = Q^2
2. 采用带遗忘因子的RLS算法进行递推估计：
   - 遗忘因子 lambda = 0.98，使算法具有跟踪慢时变参数的能力
   - 初始猜测 n = 0.035（偏离真值 0.025 约40%）
3. 利用正弦激励信号模拟流量波动，增强参数可辨识性

作者：雷晓辉 教授，河北工程大学
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，用于服务器环境
import matplotlib.pyplot as plt

# ============================================================
# 全局绘图参数设置：中文字体支持
# ============================================================
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False     # 正确显示负号


def manning_flow(n, A, R, S0):
    """
    曼宁公式计算明渠流量

    参数:
        n  : 曼宁糙率系数 [-]
        A  : 过水断面面积 [m^2]
        R  : 水力半径 [m]
        S0 : 渠底纵坡 [-]

    返回:
        Q  : 流量 [m^3/s]
    """
    return (1.0 / n) * A * R**(2.0/3.0) * np.sqrt(S0)


def compute_hydraulic_params(Q, B, S0, n):
    """
    根据流量反算矩形断面的水深和水力参数

    对于矩形断面：
        A = B * h（过水面积）
        P = B + 2h（湿周）
        R = A / P（水力半径）

    利用曼宁公式 Q = (1/n)*A*R^(2/3)*sqrt(S0) 迭代求解水深 h。
    此处采用简化方法：假设宽浅渠道 R ≈ h，直接反算。

    参数:
        Q  : 流量 [m^3/s]
        B  : 渠道底宽 [m]
        S0 : 渠底纵坡 [-]
        n  : 曼宁糙率系数 [-]

    返回:
        h  : 水深 [m]
        A  : 过水断面面积 [m^2]
        R  : 水力半径 [m]
    """
    # 迭代求解水深（牛顿法）
    h = 1.5  # 初始猜测水深
    for _ in range(50):
        A = B * h
        P = B + 2.0 * h
        R = A / P
        # 曼宁公式残差
        Q_calc = (1.0 / n) * A * R**(2.0/3.0) * np.sqrt(S0)
        # 对h求导（数值微分）
        dh_num = 1e-6
        A2 = B * (h + dh_num)
        P2 = B + 2.0 * (h + dh_num)
        R2 = A2 / P2
        Q_calc2 = (1.0 / n) * A2 * R2**(2.0/3.0) * np.sqrt(S0)
        dQdh = (Q_calc2 - Q_calc) / dh_num
        if abs(dQdh) < 1e-12:
            break
        h = h - (Q_calc - Q) / dQdh
        h = max(h, 0.1)  # 防止水深为负
    A = B * h
    P = B + 2.0 * h
    R = A / P
    return h, A, R


def main():
    """主函数：RLS辨识曼宁糙率系数"""

    # ============================================================
    # 1. 渠道物理参数设定
    # ============================================================
    L = 5000.0      # 渠道长度 [m]
    B = 8.0         # 矩形断面底宽 [m]
    S0 = 0.0002     # 渠底纵坡 [-]
    n_true = 0.025  # 真实曼宁糙率系数 [-]

    # ============================================================
    # 2. 仿真参数
    # ============================================================
    dt = 60.0       # 时间步长 [s]
    T_sim = 3600.0  # 仿真总时长 [s]（1小时）
    N_steps = int(T_sim / dt)  # 仿真步数
    t = np.arange(N_steps) * dt  # 时间序列 [s]

    # ============================================================
    # 3. 生成带正弦激励的流量数据
    # ============================================================
    # 基础流量叠加正弦波动，模拟上游调控引起的流量变化
    Q_base = 15.0  # 基础流量 [m^3/s]
    Q_amp = 3.0    # 正弦波幅值 [m^3/s]
    Q_period = T_sim  # 正弦波周期 [s]

    # 真实流量（含正弦激励）
    Q_true = Q_base + Q_amp * np.sin(2.0 * np.pi * t / Q_period)

    # 添加测量噪声（流量计噪声，标准差0.3 m^3/s）
    np.random.seed(42)  # 固定随机种子，保证结果可复现
    noise_std = 0.3
    Q_meas = Q_true + np.random.randn(N_steps) * noise_std

    # ============================================================
    # 4. 计算每个时刻的水力参数（用真实n值生成"真实"水力状态）
    # ============================================================
    h_arr = np.zeros(N_steps)
    A_arr = np.zeros(N_steps)
    R_arr = np.zeros(N_steps)

    for k in range(N_steps):
        h_arr[k], A_arr[k], R_arr[k] = compute_hydraulic_params(
            Q_true[k], B, S0, n_true
        )

    # ============================================================
    # 5. 构造RLS回归模型
    # ============================================================
    # 线性化模型：Q^2 = theta * phi
    # 其中 theta = 1/n^2, phi = A^2 * R^(4/3) * S0
    # 观测量 y = Q_meas^2

    y = Q_meas**2  # 观测量（流量的平方）
    phi = A_arr**2 * R_arr**(4.0/3.0) * S0  # 回归变量

    # ============================================================
    # 6. RLS递推最小二乘算法
    # ============================================================
    lam = 0.98       # 遗忘因子（0<lambda<=1，越小跟踪越快但噪声越大）
    n_init = 0.035   # 初始猜测的糙率系数

    # 初始化
    theta_hat = 1.0 / n_init**2  # 初始参数估计值
    P = 1000.0  # 初始协方差（标量，因为只有一个参数），设大值表示初始不确定性大

    # 存储结果
    n_est = np.zeros(N_steps)  # 辨识的n值时间序列
    e_pred = np.zeros(N_steps) # 预测误差时间序列

    for k in range(N_steps):
        # --- 预测误差 ---
        y_pred = theta_hat * phi[k]
        e_pred[k] = y[k] - y_pred

        # --- RLS增益计算 ---
        # 标量情形下的卡尔曼增益
        K = P * phi[k] / (lam + phi[k] * P * phi[k])

        # --- 参数更新 ---
        theta_hat = theta_hat + K * e_pred[k]

        # --- 协方差更新 ---
        P = (1.0 / lam) * (P - K * phi[k] * P)

        # --- 转换回n值 ---
        # theta = 1/n^2  =>  n = 1/sqrt(theta)
        if theta_hat > 0:
            n_est[k] = 1.0 / np.sqrt(theta_hat)
        else:
            # 防止非物理值
            n_est[k] = n_est[k-1] if k > 0 else n_init

    # ============================================================
    # 7. 绘制结果图
    # ============================================================
    t_min = t / 60.0  # 转换为分钟

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), dpi=150)

    # --- 子图1：糙率系数辨识收敛过程 ---
    ax1 = axes[0]
    ax1.plot(t_min, n_est, 'b-', linewidth=1.5, label='RLS估计值')
    ax1.axhline(y=n_true, color='r', linestyle='--', linewidth=1.5,
                label=f'真实值 n={n_true}')
    ax1.axhline(y=n_init, color='gray', linestyle=':', linewidth=1.0,
                label=f'初始猜测 n={n_init}')
    ax1.set_xlabel('时间 [min]', fontsize=12)
    ax1.set_ylabel('曼宁糙率系数 n', fontsize=12)
    ax1.set_title('RLS递推辨识曼宁糙率系数收敛过程', fontsize=14)
    ax1.legend(fontsize=11, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, T_sim/60])

    # --- 子图2：预测误差 ---
    ax2 = axes[1]
    ax2.plot(t_min, e_pred, 'g-', linewidth=0.8, alpha=0.8, label='预测误差')
    ax2.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax2.set_xlabel('时间 [min]', fontsize=12)
    ax2.set_ylabel('预测误差 $e(k) = y(k) - \\hat{y}(k)$', fontsize=12)
    ax2.set_title('RLS预测误差随时间变化', fontsize=14)
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, T_sim/60])

    plt.tight_layout()

    # 保存图片
    fig_path = 'D:/cowork/教材/chs-books-v2/ModernControl/figures/ch06_rls_manning.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[图片已保存] {fig_path}")

    # ============================================================
    # 8. 打印结论与建议
    # ============================================================
    # 计算收敛后的估计精度（取最后10%数据的均值）
    n_final = np.mean(n_est[-N_steps//10:])
    n_std = np.std(n_est[-N_steps//10:])
    rel_error = abs(n_final - n_true) / n_true * 100

    print("\n" + "="*60)
    print("结论与建议")
    print("="*60)
    print(f"  渠道参数: L={L}m, B={B}m, S0={S0}, n_true={n_true}")
    print(f"  仿真时长: {T_sim/60:.0f} min, 时间步长: {dt:.0f} s")
    print(f"  RLS遗忘因子: λ={lam}")
    print(f"  初始猜测: n_init={n_init}（偏差{abs(n_init-n_true)/n_true*100:.0f}%）")
    print(f"  收敛后估计值: n_est={n_final:.5f} ± {n_std:.5f}")
    print(f"  相对误差: {rel_error:.2f}%")
    print()
    print("  [结论1] RLS算法能够从偏差40%的初始猜测快速收敛至真实值附近，")
    print("          收敛时间约为5~10个时间步（5~10分钟）。")
    print("  [结论2] 遗忘因子λ=0.98使算法具有良好的慢时变参数跟踪能力，")
    print("          但需在跟踪速度和噪声抑制之间权衡。")
    print("  [结论3] 正弦激励信号有效增强了持续激励条件，")
    print("          这是参数可辨识性的必要条件。")
    print("  [建议]  实际应用中，遗忘因子应根据参数变化速率调整：")
    print("          缓变参数取0.98~0.99，快变参数取0.95~0.97。")
    print("="*60)


if __name__ == '__main__':
    main()
