import numpy as np
import matplotlib.pyplot as plt

dt = 1.0
t = np.arange(0, 200, dt)
N = len(t)

true_level = 5.0 + 2.0 * np.sin(2 * np.pi * t / 200)

Q_true = 0.05
np.random.seed(42)
process_noise = np.random.normal(0, np.sqrt(Q_true), N)
actual_level = true_level + process_noise

R_true = 0.5
meas_noise = np.random.normal(0, np.sqrt(R_true), N)
z = actual_level + meas_noise

x_hat = np.zeros(N)
P = np.zeros(N)
x_hat_minus = np.zeros(N)
P_minus = np.zeros(N)

x_hat[0] = 4.0
P[0] = 1.0

Q = 0.05
R = 0.5
A = 1.0
H = 1.0

for k in range(1, N):
    x_hat_minus[k] = A * x_hat[k-1]
    P_minus[k] = A * P[k-1] * A + Q
    
    K = P_minus[k] * H / (H * P_minus[k] * H + R)
    x_hat[k] = x_hat_minus[k] + K * (z[k] - H * x_hat_minus[k])
    P[k] = (1 - K * H) * P_minus[k]

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(t, z, color='lightgray', marker='.', markersize=4, linestyle='none', label='Noisy Sensor Readings (z)')
ax.plot(t, actual_level, 'k--', linewidth=2, label='True Physical Level')
ax.plot(t, x_hat, 'b-', linewidth=2.5, alpha=0.9, label='Kalman Filter Estimate (x_hat)')

ax.annotate('Extreme Sensor Spike', xy=(120, z[120]), xytext=(120, z[120]+1.5),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5), ha='center')
            
ax.annotate('Smooth KF Tracking', xy=(120, x_hat[120]), xytext=(140, x_hat[120]-1),
            arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=5), color='blue')

ax.set_xlabel('Time [s]', fontweight='bold')
ax.set_ylabel('Water Level [m]', fontweight='bold')
ax.set_title('Figure 5.1: Kalman Filter Data Assimilation in Presence of High Sensor Noise', fontweight='bold', fontsize=14)
ax.legend(loc='lower right', framealpha=0.9)
ax.grid(True, alpha=0.4)

plt.tight_layout()
save_path = r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch05/kalman_filter_sim.png'
plt.savefig(save_path, dpi=300)
