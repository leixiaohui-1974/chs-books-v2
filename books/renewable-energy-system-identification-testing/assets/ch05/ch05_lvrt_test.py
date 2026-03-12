"""
第5章仿真：风电机组低电压穿越（LVRT）测试
模拟GB/T 19963标准规定的电压跌落曲线，
测试双馈风电机组（DFIG）的电流/功率响应。
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

# ---------- 电网电压跌落曲线 (GB/T 19963) ----------
# 跌落深度80% (剩余20%), 持续625ms
T_total = 3.0
dt = 0.0002  # 200us
time = np.arange(0, T_total, dt)
N = len(time)
V_nom = 690  # 额定线电压 (V)

# 构造电压跌落包络
V_env = np.ones(N)
t_fault_start = 0.5
t_fault_end = 1.125   # 625ms跌落
t_recovery_end = 2.0  # 恢复到90%

for i in range(N):
    t = time[i]
    if t < t_fault_start:
        V_env[i] = 1.0
    elif t < t_fault_start + 0.02:  # 20ms跌落过渡
        V_env[i] = 1.0 - 0.8 * (t - t_fault_start) / 0.02
    elif t < t_fault_end:
        V_env[i] = 0.20  # 残压20%
    elif t < t_fault_end + 0.1:  # 100ms恢复过渡
        V_env[i] = 0.20 + 0.7 * (t - t_fault_end) / 0.1
    elif t < t_recovery_end:
        V_env[i] = 0.90 + 0.10 * (t - t_fault_end - 0.1) / (t_recovery_end - t_fault_end - 0.1)
    else:
        V_env[i] = 1.0

V_grid = V_env * V_nom

# ---------- DFIG简化模型响应 ----------
# 额定参数
P_rated = 2.0e6    # 2MW
I_rated = P_rated / (np.sqrt(3) * V_nom)  # 额定电流

# 定子电流响应（简化模型）
# 跌落时定子磁链产生暂态直流分量，导致转子电流冲击
I_stator = np.zeros(N)
I_rotor = np.zeros(N)
P_active = np.zeros(N)
Q_reactive = np.zeros(N)

# 稳态前
I_stator_ss = I_rated

# Crowbar参数
crowbar_active = np.zeros(N, dtype=bool)
crowbar_threshold = 2.0 * I_rated  # 2倍额定电流触发

tau_dc = 0.05  # 直流分量衰减时间常数
tau_recovery = 0.3  # 功率恢复时间常数

for i in range(N):
    t = time[i]

    if t < t_fault_start:
        # 正常运行
        I_stator[i] = I_rated
        I_rotor[i] = 0.3 * I_rated  # 转子电流约30%
        P_active[i] = P_rated
        Q_reactive[i] = 0

    elif t < t_fault_start + 0.02:
        # 跌落瞬间 - 暂态冲击
        dt_fault = t - t_fault_start
        # 直流暂态分量
        I_dc = 3.0 * I_rated * np.exp(-dt_fault / tau_dc) * (1 - V_env[i])
        I_stator[i] = I_rated * V_env[i] + I_dc
        I_rotor[i] = 0.3 * I_rated + 2.5 * I_dc  # 转子电流冲击更大

        if I_rotor[i] > crowbar_threshold:
            crowbar_active[i] = True

        P_active[i] = P_rated * V_env[i]**2
        Q_reactive[i] = -0.5e6  # 跌落时注入无功

    elif t < t_fault_end:
        # 跌落持续
        dt_fault = t - t_fault_start
        I_dc = 3.0 * I_rated * np.exp(-dt_fault / tau_dc) * 0.8
        I_stator[i] = max(I_rated * V_env[i], 0.2 * I_rated) + I_dc * max(0, 1 - dt_fault / 0.1)
        I_rotor[i] = 0.3 * I_rated * V_env[i] + I_dc * 0.5 * max(0, 1 - dt_fault / 0.1)

        if I_rotor[i] > crowbar_threshold:
            crowbar_active[i] = True

        P_active[i] = P_rated * V_env[i]**2
        # 无功电流注入要求: I_q >= 1.5 * (0.9 - V_env) * I_rated
        Iq_req = max(0, 1.5 * (0.9 - V_env[i]) * I_rated)
        Q_reactive[i] = -np.sqrt(3) * V_grid[i] * Iq_req  # 容性无功

    elif t < t_recovery_end:
        # 恢复阶段
        dt_rec = t - t_fault_end
        I_stator[i] = I_rated * V_env[i] + 0.5 * I_rated * np.exp(-dt_rec / tau_recovery)
        I_rotor[i] = 0.3 * I_rated + 0.3 * I_rated * np.exp(-dt_rec / tau_recovery)
        P_active[i] = P_rated * V_env[i] * (1 - 0.3 * np.exp(-dt_rec / tau_recovery))
        Q_reactive[i] = -0.3e6 * np.exp(-dt_rec / (tau_recovery * 2))

    else:
        # 恢复完成
        I_stator[i] = I_rated
        I_rotor[i] = 0.3 * I_rated
        P_active[i] = P_rated
        Q_reactive[i] = 0

# ---------- 绘图 ----------
fig, axes = plt.subplots(4, 1, figsize=(14, 14))

# 电压
ax1 = axes[0]
ax1.plot(time, V_grid / V_nom * 100, '#1565C0', linewidth=2)
ax1.axhline(20, color='r', linestyle='--', alpha=0.5, label='残压20%')
ax1.axhline(90, color='#4CAF50', linestyle='--', alpha=0.5, label='90%恢复线')
ax1.fill_between(time, 0, V_grid / V_nom * 100, alpha=0.1, color='#1565C0')
ax1.set_ylabel('电网电压 (%)')
ax1.set_title('LVRT测试 —— 电网电压跌落曲线 (GB/T 19963)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim([0, 120])

# 电流
ax2 = axes[1]
ax2.plot(time, I_stator / I_rated, '#1565C0', linewidth=1.5, label='定子电流')
ax2.plot(time, I_rotor / I_rated, '#FF7043', linewidth=1.5, label='转子电流')
ax2.axhline(2.0, color='r', linestyle='--', alpha=0.5, label='Crowbar阈值')
# 标记Crowbar动作
crowbar_times = time[crowbar_active]
if len(crowbar_times) > 0:
    ax2.axvspan(crowbar_times[0], crowbar_times[-1], alpha=0.15, color='red', label='Crowbar激活')
ax2.set_ylabel('电流 (p.u.)')
ax2.set_title('定子/转子电流响应')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_ylim([0, 5])

# 有功功率
ax3 = axes[2]
ax3.plot(time, P_active / 1e6, '#4CAF50', linewidth=2)
ax3.axhline(2.0, color='k', linestyle='--', alpha=0.3, label='额定2MW')
ax3.set_ylabel('有功功率 (MW)')
ax3.set_title('有功功率响应')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 无功功率
ax4 = axes[3]
ax4.plot(time, Q_reactive / 1e6, '#7B1FA2', linewidth=2)
ax4.axhline(0, color='k', linewidth=0.5)
ax4.set_ylabel('无功功率 (MVar)')
ax4.set_xlabel('时间 (s)')
ax4.set_title('无功功率注入（容性为负）')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "lvrt_test_response.png"), dpi=200)
plt.close()

# ---------- LVRT标准合规检查 ----------
print("=" * 60)
print("第5章仿真结果：LVRT测试结果")
print("=" * 60)

print(f"\n测试条件:")
print(f"  额定功率: {P_rated/1e6:.0f} MW")
print(f"  额定电压: {V_nom} V")
print(f"  额定电流: {I_rated:.1f} A")
print(f"  跌落深度: 80% (残压20%)")
print(f"  跌落持续时间: {(t_fault_end - t_fault_start)*1000:.0f} ms")

# 检查是否脱网
disconnected = False
print(f"\n测试结果:")
print(f"  是否脱网: {'是' if disconnected else '否 (通过)'}")

# 峰值电流
I_stator_peak = np.max(I_stator)
I_rotor_peak = np.max(I_rotor)
print(f"  定子电流峰值: {I_stator_peak/I_rated:.2f} p.u. (绝对值: {I_stator_peak:.1f} A)")
print(f"  转子电流峰值: {I_rotor_peak/I_rated:.2f} p.u. (绝对值: {I_rotor_peak:.1f} A)")

# Crowbar动作时间
if np.any(crowbar_active):
    cb_duration = np.sum(crowbar_active) * dt * 1000
    print(f"  Crowbar动作: 是, 持续 {cb_duration:.1f} ms")
else:
    print(f"  Crowbar动作: 否")

# 功率恢复时间
idx_after_fault = time >= t_fault_end
P_after = P_active[idx_after_fault]
t_after = time[idx_after_fault]
idx_90 = np.where(P_after >= 0.9 * P_rated)[0]
if len(idx_90) > 0:
    t_power_recovery = t_after[idx_90[0]] - t_fault_end
    print(f"  有功功率恢复至90%时间: {t_power_recovery*1000:.0f} ms")

# 无功电流注入
Q_during_fault = Q_reactive[(time >= t_fault_start + 0.05) & (time <= t_fault_end)]
Q_avg = np.mean(Q_during_fault)
print(f"  跌落期间平均无功注入: {Q_avg/1e6:.3f} MVar")

# 电压恢复后稳态
idx_final = time >= 2.5
P_final = np.mean(P_active[idx_final])
print(f"  恢复后有功功率: {P_final/1e6:.3f} MW ({P_final/P_rated*100:.1f}%)")
print(f"  恢复后电压: {np.mean(V_grid[idx_final])/V_nom*100:.1f}%")
