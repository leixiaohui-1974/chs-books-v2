"""
第2章配套仿真：抗积分饱和PID在防洪排涝泵站中的应用

物理场景：城市防洪排涝泵站
- 目标水位：5.0m（安全水位）
- 暴雨导致水位上升，排涝泵需要加大排水量
- 控制器输出u(%)控制排涝泵功率（0~100%）
- 反作用控制：水位越高 → 排水越大 → error = pv - setpoint
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 尝试加载中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class IndustrialPID:
    """工业级PID控制器（含抗积分饱和）"""
    def __init__(self, Kc, tau_I, tau_D, dt, out_min=0.0, out_max=100.0, anti_windup=True):
        self.Kc = Kc
        self.tau_I = tau_I
        self.tau_D = tau_D
        self.dt = dt
        self.out_min = out_min
        self.out_max = out_max
        self.anti_windup = anti_windup
        self.integral = 0.0
        self.prev_error = 0.0

    def compute(self, setpoint, pv):
        # 反作用控制：水位高于目标时error>0，增大排水
        error = pv - setpoint
        P = self.Kc * error
        potential_I = self.integral + self.Kc * (self.dt / self.tau_I) * error
        D = self.Kc * self.tau_D * (error - self.prev_error) / self.dt

        u_unclamped = P + potential_I + D

        # 限幅与抗饱和逻辑
        if u_unclamped > self.out_max:
            u = self.out_max
            if self.anti_windup and error > 0:
                # 已饱和且误差仍促使增大输出 → 冻结积分
                pass
            else:
                self.integral = potential_I
        elif u_unclamped < self.out_min:
            u = self.out_min
            if self.anti_windup and error < 0:
                # 已饱和且误差仍促使减小输出 → 冻结积分
                pass
            else:
                self.integral = potential_I
        else:
            u = u_unclamped
            self.integral = potential_I

        self.prev_error = error
        return u


# 仿真参数
dt = 0.5       # 步长0.5s，更合理的离散化
t = np.arange(0, 500, dt)
n = len(t)

# 水箱参数
A_tank = 4.0    # 水箱截面积 m^2（集水池）
K_pump = 0.002  # 排涝泵流量系数：u=100%时排水0.2 m^3/s
Q_base = 0.04   # 基础入流 m^3/s（渗流+少量雨水）


def run_sim(anti_windup):
    pid = IndustrialPID(
        Kc=12.0, tau_I=10.0, tau_D=1.0, dt=dt,
        out_min=0.0, out_max=100.0, anti_windup=anti_windup
    )
    pv = np.zeros(n)
    u = np.zeros(n)
    integral_term = np.zeros(n)

    pv[0] = 5.0  # 初始水位=目标值
    u[0] = pid.compute(5.0, pv[0])  # 初始控制输出

    for i in range(1, n):
        # 暴雨扰动：t=20~100s期间入流猛增至10倍
        if 20 <= t[i] <= 100:
            Q_in = Q_base * 10.0  # 暴雨入流 0.4 m^3/s（远超泵最大排水0.2）
        else:
            Q_in = Q_base         # 正常入流 0.04 m^3/s

        Q_out = K_pump * u[i-1]   # 排涝泵排水

        # 水箱水量平衡：dh/dt = (Q_in - Q_out) / A
        pv[i] = pv[i-1] + (Q_in - Q_out) / A_tank * dt

        # 物理约束：水位不能为负
        pv[i] = max(pv[i], 0.0)

        u[i] = pid.compute(5.0, pv[i])
        integral_term[i] = pid.integral

    return pv, u, integral_term


# 运行两组仿真
pv_no_aw, u_no_aw, i_no_aw = run_sim(anti_windup=False)
pv_aw, u_aw, i_aw = run_sim(anti_windup=True)

# 绘图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# 子图1：水位响应
ax1.plot(t, pv_no_aw, 'r--', linewidth=1.5, label='Standard PID (no anti-windup)')
ax1.plot(t, pv_aw, 'b-', linewidth=2, label='Anti-Windup PID')
ax1.axhline(5.0, color='k', linestyle=':', linewidth=1, label='Setpoint (5.0 m)')
ax1.axvspan(20, 100, alpha=0.1, color='gray', label='Storm period')
ax1.set_ylabel('Water Level [m]', fontweight='bold')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.set_title('Integrator Windup vs Anti-Windup in Flood Drainage Control',
              fontsize=13, fontweight='bold')

# 子图2：阀门/泵输出
ax2.plot(t, u_no_aw, 'r--', linewidth=1.5, label='Pump Output (Standard)')
ax2.plot(t, u_aw, 'b-', linewidth=2, label='Pump Output (Anti-Windup)')
ax2.axhline(100.0, color='gray', linestyle=':', linewidth=1, label='Physical Max (100%)')
ax2.axhline(0.0, color='gray', linestyle=':', linewidth=1)
ax2.set_ylabel('Pump Command [%]', fontweight='bold')
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)

# 子图3：积分项累积
ax3.plot(t, i_no_aw, 'r--', linewidth=1.5, label='Integral Term (Standard)')
ax3.plot(t, i_aw, 'b-', linewidth=2, label='Integral Term (Anti-Windup)')
ax3.set_xlabel('Time [s]', fontweight='bold')
ax3.set_ylabel('Integral Accumulation', fontweight='bold')
ax3.legend(loc='upper right', fontsize=9)
ax3.grid(True, alpha=0.3)

plt.tight_layout()

save_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'pid_windup_sim.png'
)
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"Figure saved to: {save_path}")

# 打印关键数据点
print("\nKey simulation data points:")
for ti in [20, 50, 80, 100, 120, 150, 200, 280, 350, 450]:
    idx = int(ti / dt)
    if idx < n:
        print(f"  t={ti:3d}s: Standard PID: level={pv_no_aw[idx]:.2f}m, u={u_no_aw[idx]:.1f}% | "
              f"Anti-Windup: level={pv_aw[idx]:.2f}m, u={u_aw[idx]:.1f}%")
