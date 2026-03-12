"""
第4章仿真：硬件在环（HIL）与纯数字仿真（SIL）的延迟对比
模拟风电变桨控制器在SIL和HIL环境下的性能差异，
重点分析I/O延迟和采样步长对控制品质的影响。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ---------- 风电机组变桨系统模型 ----------
# 简化桨距角动力学: J_pitch * d^2(beta)/dt^2 + D_pitch * d(beta)/dt = T_act - T_aero
# 传递函数: G(s) = 1 / (J*s^2 + D*s)
# 使用PI控制器: C(s) = Kp + Ki/s

J_pitch = 50.0      # 变桨惯量 (kg*m^2)
D_pitch = 20.0      # 阻尼系数 (N*m*s/rad)
Kp = 500.0           # PI比例增益
Ki = 100.0           # PI积分增益

# 仿真参数
dt_sil = 0.001       # SIL步长 1ms (理想)
dt_hil = 0.001       # HIL步长 1ms (实际)
T_total = 10.0
time_sil = np.arange(0, T_total, dt_sil)
N_sil = len(time_sil)

# 参考桨距角信号
beta_ref = np.zeros(N_sil)
beta_ref[time_sil >= 1.0] = 5.0     # 1s时阶跃到5度
beta_ref[time_sil >= 4.0] = 10.0    # 4s时阶跃到10度
beta_ref[time_sil >= 7.0] = 3.0     # 7s时阶跃回3度

# 气动扰动力矩
np.random.seed(42)
T_aero_disturbance = 50 * np.sin(2 * np.pi * 0.5 * time_sil) + 20 * np.random.randn(N_sil)

def simulate_pitch_control(dt, delay_samples, noise_std, label):
    """模拟变桨控制闭环"""
    N = int(T_total / dt)
    time = np.arange(0, T_total, dt)

    beta = np.zeros(N)
    dbeta = np.zeros(N)
    u_cmd = np.zeros(N)
    integral_err = 0.0

    # 延迟缓冲
    u_delayed = np.zeros(N)

    for k in range(1, N):
        # 参考信号
        ref = 0.0
        if time[k] >= 1.0: ref = 5.0
        if time[k] >= 4.0: ref = 10.0
        if time[k] >= 7.0: ref = 3.0

        # 传感器噪声
        beta_meas = beta[k-1] + np.random.normal(0, noise_std)

        # PI控制器
        err = ref - beta_meas
        integral_err += err * dt
        u_cmd[k] = Kp * err + Ki * integral_err

        # 执行器饱和
        u_cmd[k] = np.clip(u_cmd[k], -5000, 5000)

        # 延迟模拟
        if k >= delay_samples:
            u_delayed[k] = u_cmd[k - delay_samples]
        else:
            u_delayed[k] = 0

        # 气动扰动
        t_idx = min(int(time[k] / dt_sil), N_sil - 1)
        T_aero = T_aero_disturbance[t_idx]

        # 变桨动力学
        T_net = u_delayed[k] - T_aero
        ddbeta = (T_net - D_pitch * dbeta[k-1]) / J_pitch
        dbeta[k] = dbeta[k-1] + ddbeta * dt
        beta[k] = beta[k-1] + dbeta[k] * dt

    return time, beta, u_cmd

# ---------- 三种场景 ----------
# SIL: 无延迟，低噪声
t_sil, beta_sil, u_sil = simulate_pitch_control(dt_sil, delay_samples=0, noise_std=0.01, label='SIL')

# HIL (1ms延迟，即1个采样周期)
t_hil1, beta_hil1, u_hil1 = simulate_pitch_control(dt_hil, delay_samples=1, noise_std=0.05, label='HIL-1ms')

# HIL (5ms延迟，即5个采样周期)
t_hil5, beta_hil5, u_hil5 = simulate_pitch_control(dt_hil, delay_samples=5, noise_std=0.05, label='HIL-5ms')

# ---------- 绘图 ----------
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# 桨距角响应
ax1 = axes[0]
ax1.plot(t_sil, beta_sil, '#1565C0', linewidth=1.5, label='SIL (无延迟)')
ax1.plot(t_hil1, beta_hil1, '#4CAF50', linewidth=1.5, label='HIL (1ms延迟)')
ax1.plot(t_hil5, beta_hil5, '#FF7043', linewidth=1.5, label='HIL (5ms延迟)')
# 参考信号
beta_ref_plot = np.zeros_like(t_sil)
beta_ref_plot[t_sil >= 1.0] = 5.0
beta_ref_plot[t_sil >= 4.0] = 10.0
beta_ref_plot[t_sil >= 7.0] = 3.0
ax1.plot(t_sil, beta_ref_plot, 'k--', linewidth=2, label='参考值')
ax1.set_ylabel('桨距角 (deg)')
ax1.set_title('风电变桨控制 —— SIL与HIL响应对比')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 控制量
ax2 = axes[1]
ax2.plot(t_sil, u_sil, '#1565C0', linewidth=0.8, alpha=0.7, label='SIL')
ax2.plot(t_hil1, u_hil1, '#4CAF50', linewidth=0.8, alpha=0.7, label='HIL-1ms')
ax2.plot(t_hil5, u_hil5, '#FF7043', linewidth=0.8, alpha=0.7, label='HIL-5ms')
ax2.set_ylabel('控制力矩 (N*m)')
ax2.set_title('执行器力矩指令')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 跟踪误差
err_sil = beta_ref_plot - beta_sil
err_hil1 = beta_ref_plot - beta_hil1
err_hil5 = beta_ref_plot - beta_hil5

ax3 = axes[2]
ax3.plot(t_sil, err_sil, '#1565C0', linewidth=1, alpha=0.8, label='SIL')
ax3.plot(t_hil1, err_hil1, '#4CAF50', linewidth=1, alpha=0.8, label='HIL-1ms')
ax3.plot(t_hil5, err_hil5, '#FF7043', linewidth=1, alpha=0.8, label='HIL-5ms')
ax3.axhline(0, color='k', linewidth=0.5)
ax3.set_ylabel('跟踪误差 (deg)')
ax3.set_xlabel('时间 (s)')
ax3.set_title('桨距角跟踪误差')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "hil_vs_sil_pitch.png"), dpi=200)
plt.close()

# ---------- 计算KPI ----------
def compute_kpi(time, beta, beta_ref_arr, label):
    """计算各阶跃响应的KPI"""
    # 稳态区间分析
    segments = [
        ('阶跃1(0->5deg)', 1.0, 3.5, 5.0),
        ('阶跃2(5->10deg)', 4.0, 6.5, 10.0),
        ('阶跃3(10->3deg)', 7.0, 9.5, 3.0),
    ]

    results = {}
    for name, t_start, t_end, ref_val in segments:
        mask = (time >= t_start) & (time <= t_end)
        mask_ss = (time >= t_end - 0.5) & (time <= t_end)

        beta_seg = beta[mask]
        beta_ss = beta[mask_ss]

        # 稳态误差
        ss_err = abs(np.mean(beta_ss) - ref_val)
        # 超调量
        if ref_val > beta[int(t_start/dt_sil)]:  # 正阶跃
            overshoot = max(0, (np.max(beta_seg) - ref_val) / ref_val * 100)
        else:
            overshoot = max(0, (ref_val - np.min(beta_seg)) / ref_val * 100) if ref_val != 0 else 0

        # RMSE
        ref_seg = np.full_like(beta_seg, ref_val)
        rmse = np.sqrt(np.mean((beta_seg - ref_seg)**2))

        # 调节时间 (进入2%范围)
        t_seg = time[mask]
        settled = np.abs(beta_seg - ref_val) < 0.02 * abs(ref_val) if ref_val != 0 else np.abs(beta_seg - ref_val) < 0.1
        if np.any(settled):
            # 找到最后一次离开2%带后不再离开的时刻
            for i in range(len(settled)-1, -1, -1):
                if not settled[i]:
                    t_settle = t_seg[min(i+1, len(t_seg)-1)] - t_start
                    break
            else:
                t_settle = 0.0
        else:
            t_settle = t_end - t_start

        results[name] = {
            'ss_err': ss_err,
            'overshoot': overshoot,
            'rmse': rmse,
            't_settle': t_settle,
        }

    return results

kpi_sil = compute_kpi(t_sil, beta_sil, beta_ref_plot, 'SIL')
kpi_hil1 = compute_kpi(t_hil1, beta_hil1, beta_ref_plot, 'HIL-1ms')
kpi_hil5 = compute_kpi(t_hil5, beta_hil5, beta_ref_plot, 'HIL-5ms')

print("=" * 60)
print("第4章仿真结果：SIL vs HIL 变桨控制对比")
print("=" * 60)

print(f"\n系统参数: J={J_pitch} kg*m^2, D={D_pitch} N*m*s/rad")
print(f"控制器: Kp={Kp}, Ki={Ki}")
print(f"步长: {dt_sil*1000:.0f} ms")

for seg_name in ['阶跃1(0->5deg)', '阶跃2(5->10deg)', '阶跃3(10->3deg)']:
    print(f"\n--- {seg_name} ---")
    print(f"{'指标':<15} {'SIL':>10} {'HIL-1ms':>10} {'HIL-5ms':>10}")
    print(f"{'稳态误差(deg)':<15} {kpi_sil[seg_name]['ss_err']:>10.3f} {kpi_hil1[seg_name]['ss_err']:>10.3f} {kpi_hil5[seg_name]['ss_err']:>10.3f}")
    print(f"{'超调量(%)':<15} {kpi_sil[seg_name]['overshoot']:>10.2f} {kpi_hil1[seg_name]['overshoot']:>10.2f} {kpi_hil5[seg_name]['overshoot']:>10.2f}")
    print(f"{'RMSE(deg)':<15} {kpi_sil[seg_name]['rmse']:>10.3f} {kpi_hil1[seg_name]['rmse']:>10.3f} {kpi_hil5[seg_name]['rmse']:>10.3f}")
    print(f"{'调节时间(s)':<15} {kpi_sil[seg_name]['t_settle']:>10.3f} {kpi_hil1[seg_name]['t_settle']:>10.3f} {kpi_hil5[seg_name]['t_settle']:>10.3f}")

# 全局RMSE
rmse_total_sil = np.sqrt(np.mean((beta_sil - beta_ref_plot)**2))
rmse_total_hil1 = np.sqrt(np.mean((beta_hil1 - beta_ref_plot)**2))
rmse_total_hil5 = np.sqrt(np.mean((beta_hil5 - beta_ref_plot)**2))

print(f"\n全局RMSE: SIL={rmse_total_sil:.3f}, HIL-1ms={rmse_total_hil1:.3f}, HIL-5ms={rmse_total_hil5:.3f}")
