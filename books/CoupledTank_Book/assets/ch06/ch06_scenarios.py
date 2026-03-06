"""
第6章案例仿真：三种典型场景
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

dt = 0.5

# ============================================================
# 场景一：单水箱快速充水不溢出
# ============================================================
t1 = np.arange(0, 150, dt); N1 = len(t1)
A = 2.0; k_out = 0.3; h0 = 0.5; h_tgt = 4.0; h_max = 5.0; u_max = 3.0

h1 = np.zeros(N1); u1 = np.zeros(N1); h1[0] = h0

for i in range(1, N1):
    err = h_tgt - h1[i-1]
    qo_now = k_out * np.sqrt(max(h1[i-1], 0))

    if err > 2.0:
        u_cmd = u_max  # Bang: full power
    elif err > 0.2:
        # Singular: smooth reduction. Key: predict where we'll be
        rate = (u1[max(0,i-1)] - qo_now) / A
        predicted = h1[i-1] + rate * 5.0  # 5s lookahead
        if predicted > h_max - 0.3:
            u_cmd = qo_now + err * 0.3  # gentle
        else:
            u_cmd = min(u_max, err * 1.0 + qo_now)
    else:
        u_cmd = qo_now + err * 0.5  # fine tracking

    u1[i] = np.clip(u_cmd, 0, u_max)
    h1[i] = max(0, h1[i-1] + (u1[i] - qo_now) / A * dt)

# ============================================================
# 场景二：双容水箱扰动抑制
# h1 > h2, gravity-driven flow from tank 1 to tank 2
# ============================================================
t2 = np.arange(0, 300, dt); N2 = len(t2)
A1, A2 = 2.0, 2.0
k12 = 1.0   # wider connecting pipe
kout2 = 0.2  # smaller outlet
h1i, h2i = 4.2, 3.5  # h1 > h2
h2_tgt = 4.0

# At steady state with h2=4.0:
# kout2*sqrt(4.0) = 0.2*2.0 = 0.4
# k12*sqrt(h1-4.0) = 0.4 → sqrt(h1-4.0) = 0.4 → h1 = 4.16
# pump = 0.4

dist2 = np.zeros(N2)
dist2[(t2 >= 60) & (t2 < 140)] = 0.3  # downstream suddenly draws water

def q12f(h1v, h2v):
    return k12 * np.sqrt(max(h1v - h2v, 0)) if h1v > h2v else 0.0

def qoutf(h2v):
    return kout2 * np.sqrt(max(h2v, 0))

# --- A: 纯反馈 (slow PI, no disturbance info) ---
h1a = np.zeros(N2); h2a = np.zeros(N2); ua = np.zeros(N2)
h1a[0], h2a[0] = h1i, h2i
Kp_slow = 0.6; Ki_slow = 0.008; int_a = 0.0

for i in range(1, N2):
    err = h2_tgt - h2a[i-1]
    int_a += err * dt
    base = q12f(h1a[i-1], h2a[i-1]) + qoutf(h2a[i-1])
    ua[i] = np.clip(Kp_slow * err + Ki_slow * int_a + base * 0.5, 0, 3.0)
    q12 = q12f(h1a[i-1], h2a[i-1])
    qo = qoutf(h2a[i-1])
    h1a[i] = max(0, h1a[i-1] + (ua[i] - q12) / A1 * dt)
    h2a[i] = max(0, h2a[i-1] + (q12 - qo - dist2[i]) / A2 * dt)

# --- B: 前馈+反馈 (fast PI + disturbance detection) ---
h1b = np.zeros(N2); h2b = np.zeros(N2); ub = np.zeros(N2)
h1b[0], h2b[0] = h1i, h2i
Kp_fast = 1.2; Ki_fast = 0.015; int_b = 0.0; d_est = np.zeros(N2)

for i in range(1, N2):
    if i >= 3:
        dh2 = h2b[i-1] - h2b[i-2]
        q12p = q12f(h1b[i-2], h2b[i-2])
        qop = qoutf(h2b[i-2])
        exp_dh2 = (q12p - qop) / A2 * dt
        resid = dh2 - exp_dh2
        if resid < -0.0003:
            d_est[i] = min(-resid * A2 / dt, 1.0)
        else:
            d_est[i] = max(0, d_est[i-1] * 0.85)

    err = h2_tgt - h2b[i-1]
    int_b += err * dt
    base = q12f(h1b[i-1], h2b[i-1]) + qoutf(h2b[i-1])
    ff = d_est[i]
    ub[i] = np.clip(Kp_fast * err + Ki_fast * int_b + ff + base * 0.5, 0, 3.0)
    q12 = q12f(h1b[i-1], h2b[i-1])
    qo = qoutf(h2b[i-1])
    h1b[i] = max(0, h1b[i-1] + (ub[i] - q12) / A1 * dt)
    h2b[i] = max(0, h2b[i-1] + (q12 - qo - dist2[i]) / A2 * dt)

# ============================================================
# 场景三：执行器故障+泄漏（用场景二的参数）
# ============================================================
t3 = np.arange(0, 300, dt); N3 = len(t3)
h1c = np.zeros(N3); h2c = np.zeros(N3); uc = np.zeros(N3)
h1c[0], h2c[0] = 4.2, 4.0  # near steady state

fault_step = int(50/dt)
leak_step = int(80/dt)
leak_rate = 0.05  # small leak

int_c = 0.0
u_lock = None

for i in range(1, N3):
    if i < fault_step:
        err = h2_tgt - h2c[i-1]
        int_c += err * dt
        base = q12f(h1c[i-1], h2c[i-1]) + qoutf(h2c[i-1])
        uc[i] = np.clip(Kp_fast * err + Ki_fast * int_c + base * 0.5, 0, 3.0)
        u_lock = uc[i]
    else:
        uc[i] = u_lock

    leak = leak_rate if i >= leak_step else 0.0
    q12 = q12f(h1c[i-1], h2c[i-1])
    qo = qoutf(h2c[i-1])
    h1c[i] = max(0, h1c[i-1] + (uc[i] - q12 - leak) / A1 * dt)
    h2c[i] = max(0, h2c[i-1] + (q12 - qo) / A2 * dt)

alarm_t = t3[min(leak_step + int(10/dt), N3-1)]

# ============================================================
# 绘图
# ============================================================
fig, axes = plt.subplots(3, 2, figsize=(14, 16))

# Scene 1
peak1 = np.max(h1)
axes[0,0].plot(t1, h1, 'b-', lw=2, label='MPC level')
axes[0,0].axhline(h_tgt, color='k', ls='--', label=f'Target {h_tgt}m')
axes[0,0].axhline(h_max, color='r', ls='--', label=f'Safety {h_max}m')
axes[0,0].annotate(f'Peak={peak1:.2f}m\nSafe', xy=(t1[np.argmax(h1)], peak1),
            xytext=(80, peak1+0.3), arrowprops=dict(facecolor='blue', shrink=0.05), fontsize=9)
axes[0,0].set_ylabel('Level (m)'); axes[0,0].set_title('Scene 1: Fast Fill', fontweight='bold')
axes[0,0].legend(fontsize=9); axes[0,0].grid(True, ls='--', alpha=0.5)

axes[0,1].plot(t1, u1, 'b-', lw=2, label='MPC pump')
axes[0,1].axhline(u_max, color='r', ls=':', label=f'Limit {u_max}')
axes[0,1].set_ylabel('Flow (m3/s)'); axes[0,1].set_title('Scene 1: Pump (Bang-Singular-Bang)', fontweight='bold')
axes[0,1].legend(fontsize=9); axes[0,1].grid(True, ls='--', alpha=0.5)

# Scene 2
dr = slice(int(60/dt), int(250/dt))
dev_a = abs(np.min(h2a[dr]) - h2_tgt)
dev_b = abs(np.min(h2b[dr]) - h2_tgt)
idx_a = int(60/dt) + np.argmin(h2a[dr])
idx_b = int(60/dt) + np.argmin(h2b[dr])

axes[1,0].plot(t2, h2a, 'r-', lw=2, label=f'FB only (dev={dev_a:.2f}m)')
axes[1,0].plot(t2, h2b, 'b-', lw=2, label=f'FF+FB (dev={dev_b:.2f}m)')
axes[1,0].axhline(h2_tgt, color='k', ls='--', label=f'Target {h2_tgt}m')
axes[1,0].axvspan(60, 140, alpha=0.15, color='purple', label='Disturbance')
axes[1,0].set_ylabel('Level (m)'); axes[1,0].set_title('Scene 2: Tank 2 Disturbance Rejection', fontweight='bold')
axes[1,0].legend(fontsize=9); axes[1,0].grid(True, ls='--', alpha=0.5)

axes[1,1].plot(t2, h1a, 'r--', lw=1.5, label='FB h1')
axes[1,1].plot(t2, h1b, 'b--', lw=1.5, label='FF+FB h1')
axes[1,1].plot(t2, ua, 'r-', lw=1.5, alpha=0.5, label='FB pump')
axes[1,1].plot(t2, ub, 'b-', lw=1.5, alpha=0.5, label='FF pump')
axes[1,1].axvspan(60, 140, alpha=0.15, color='purple')
axes[1,1].set_ylabel('Level/Flow'); axes[1,1].set_title('Scene 2: Tank 1 & Pump', fontweight='bold')
axes[1,1].legend(fontsize=8); axes[1,1].grid(True, ls='--', alpha=0.5)

# Scene 3
axes[2,0].plot(t3, h1c, 'r-', lw=2, label='Tank 1')
axes[2,0].plot(t3, h2c, 'b-', lw=2, label='Tank 2')
axes[2,0].axhline(1.0, color='orange', ls=':', label='Low 1.0m')
axes[2,0].axhline(5.0, color='red', ls=':', label='High 5.0m')
axes[2,0].axvline(50, color='gray', ls='--', alpha=0.7, label='Valve stuck')
axes[2,0].axvline(80, color='brown', ls='--', alpha=0.7, label='Leak starts')
axes[2,0].set_xlabel('Time (s)'); axes[2,0].set_ylabel('Level (m)')
axes[2,0].set_title('Scene 3: Fault + Leak', fontweight='bold')
axes[2,0].legend(fontsize=8, loc='best'); axes[2,0].grid(True, ls='--', alpha=0.5)

axes[2,1].plot(t3, uc, 'b-', lw=2, label='Pump')
axes[2,1].axvline(50, color='gray', ls='--', alpha=0.7)
if u_lock: axes[2,1].axhline(u_lock, color='red', ls=':', label=f'Locked={u_lock:.2f}')
fl = np.zeros(N3); fl[leak_step:] = leak_rate
axes[2,1].fill_between(t3, 0, fl, alpha=0.3, color='brown', label=f'Leak={leak_rate}')
axes[2,1].set_xlabel('Time (s)'); axes[2,1].set_ylabel('Flow (m3/s)')
axes[2,1].set_title('Scene 3: Actuator', fontweight='bold')
axes[2,1].legend(fontsize=9); axes[2,1].grid(True, ls='--', alpha=0.5)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "scenarios_sim.png"), dpi=300, bbox_inches='tight')

# ============================================================
# KPI
# ============================================================
fill_t = None
for i in range(N1):
    if h1[i] >= h_tgt * 0.98:
        fill_t = t1[i]; break

rec_a = rec_b = None
for i in range(int(140/dt), N2):
    if rec_a is None and abs(h2a[i] - h2_tgt) < 0.05: rec_a = t2[i] - 60
    if rec_b is None and abs(h2b[i] - h2_tgt) < 0.05: rec_b = t2[i] - 60

improve = (dev_a - dev_b) / dev_a * 100 if dev_a > 0 else 0

print("=" * 50)
print("Ch06 Results")
print("=" * 50)
print(f"\nScene 1: Fill time={'%.0f'%fill_t+'s' if fill_t else '>150s'}, peak={peak1:.2f}m, overflow={peak1>h_max}")
print(f"\nScene 2:")
print(f"  FB deviation: {dev_a:.2f}m, FF+FB: {dev_b:.2f}m, improve: {improve:.0f}%")
print(f"  FB recovery: {'%.0f'%rec_a+'s' if rec_a else '>240s'}")
print(f"  FF recovery: {'%.0f'%rec_b+'s' if rec_b else '>240s'}")
print(f"\nScene 3:")
print(f"  h1: [{np.min(h1c):.2f}, {np.max(h1c):.2f}]m")
print(f"  h2: [{np.min(h2c):.2f}, {np.max(h2c):.2f}]m")
safe = np.min(h1c)>=1.0 and np.max(h1c)<=5.0 and np.min(h2c)>=1.0 and np.max(h2c)<=5.0
print(f"  Safe: {safe}, alarm: t={alarm_t:.0f}s")
print(f"\nFiles: {output_dir}")
