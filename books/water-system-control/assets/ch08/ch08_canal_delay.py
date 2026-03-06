import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

dt = 1.0
t = np.arange(0, 500, dt)
N = len(t)

delay_time = 40.0
delay_steps = int(delay_time / dt)

y = np.zeros(N)
y_ref = np.zeros(N)
u = np.zeros(N)

y_ref[50:] = 5.0

Kc = 0.8
tau_I = 20.0
integral = 0.0

for k in range(1, N):
    error = y_ref[k] - y[k-1]
    P = Kc * error
    integral += (Kc * dt / tau_I) * error
    u[k] = P + integral
    u[k] = np.clip(u[k], 0, 100)
    
    effective_u = u[k - delay_steps] if k >= delay_steps else 0.0
    
    tau_canal = 60.0
    y[k] = y[k-1] + dt * (0.15 * effective_u - y[k-1]) / tau_canal

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(t, y_ref, 'k--', label='Target Level (Setpoint)')
ax1.plot(t, y, 'b-', linewidth=2, label='Downstream Level (PV)')
ax1.set_ylabel('Water Level [m]', fontweight='bold')
ax1.legend(loc='lower right')
ax1.grid(True, alpha=0.4)

ax1.annotate('Severe Oscillations (Dead Time)', xy=(150, 4.0), xytext=(200, 2.0),
            arrowprops=dict(facecolor='red', shrink=0.05, width=1.5, headwidth=6), color='red')

ax2.plot(t, u, 'r-', linewidth=2, label='Upstream Gate Command (u)')
ax2.set_xlabel('Time [s]', fontweight='bold')
ax2.set_ylabel('Gate Opening [%]', fontweight='bold')
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.4)

plt.suptitle('Figure 8.1: PI Control Failure in Long Canal with Transport Delay', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch08/canal_delay_sim.png', dpi=300)

