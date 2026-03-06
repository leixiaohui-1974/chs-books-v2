import numpy as np
import matplotlib.pyplot as plt

# Simulate a nonlinear pump system using Sliding Mode Control (SMC)
dt = 0.1
t = np.arange(0, 50, dt)
N = len(t)

# Nonlinear System: Valve flow has unpredictable friction/hysteresis
# dy/dt = f(y) + g(y)u + d(t)
def f(y): return -0.5 * np.sqrt(abs(y))
def g(y): return 1.0

y_smc = np.zeros(N)
y_pid = np.zeros(N)
u_smc = np.zeros(N)
u_pid = np.zeros(N)

y_smc[0] = 0.0
y_pid[0] = 0.0

y_ref = 5.0 # Target level

# SMC Parameters
lambda_smc = 1.0
eta = 2.0  # Robustness margin against disturbance
Phi = 0.5  # Boundary layer to reduce chattering

# PID Parameters (Tuned for nominal conditions)
Kp = 2.0
Ki = 0.5
integral = 0.0

for k in range(1, N):
    # Massive Unknown Disturbance (e.g., sudden massive leak or pump voltage drop)
    d_t = 3.0 * np.sin(2 * np.pi * t[k] / 10) + (2.0 if 20 < t[k] < 30 else 0)
    
    # --- SMC Control Law ---
    e_smc = y_smc[k-1] - y_ref
    # Sliding surface s = e
    s = e_smc 
    
    # Equivalent control (cancels known dynamics)
    u_eq = (-f(y_smc[k-1])) / g(y_smc[k-1])
    
    # Robust control (handles uncertainties)
    # Using saturation function sat(s/Phi) instead of sign(s) to eliminate chattering
    u_sw = -eta * np.clip(s / Phi, -1.0, 1.0) 
    
    u_smc[k] = u_eq + u_sw
    u_smc[k] = np.clip(u_smc[k], -10, 10) # Physical limit
    
    # --- PID Control Law ---
    e_pid = y_ref - y_pid[k-1]
    integral += e_pid * dt
    u_pid[k] = Kp * e_pid + Ki * integral
    u_pid[k] = np.clip(u_pid[k], -10, 10)
    
    # --- Plant Dynamics ---
    y_smc[k] = y_smc[k-1] + (f(y_smc[k-1]) + g(y_smc[k-1])*u_smc[k] + d_t) * dt
    y_pid[k] = y_pid[k-1] + (f(y_pid[k-1]) + g(y_pid[k-1])*u_pid[k] + d_t) * dt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(t, np.full_like(t, y_ref), 'k--', label='Target Level (5.0m)')
ax1.plot(t, y_pid, 'r-', linewidth=1.5, alpha=0.7, label='PID Response (Vulnerable to Disturbance)')
ax1.plot(t, y_smc, 'b-', linewidth=2.5, label='SMC Response (Robust)')
ax1.set_ylabel('Water Level [m]', fontweight='bold')
ax1.legend(loc='lower right')
ax1.grid(True, alpha=0.4)

# Highlight disturbance zone
ax1.fill_between(t[200:300], 0, 10, color='gray', alpha=0.2)
ax1.annotate('Unknown Severe Disturbance', xy=(25, 8), ha='center')

ax2.plot(t, u_pid, 'r-', linewidth=1.5, alpha=0.7, label='PID Command')
ax2.plot(t, u_smc, 'b-', linewidth=2.5, label='SMC Command')
ax2.set_xlabel('Time [s]', fontweight='bold')
ax2.set_ylabel('Control Action u(t)', fontweight='bold')
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.4)

plt.suptitle('Figure 9.1: Sliding Mode Control (SMC) vs PID under Severe Nonlinear Disturbances', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch09/smc_sim.png', dpi=300)
