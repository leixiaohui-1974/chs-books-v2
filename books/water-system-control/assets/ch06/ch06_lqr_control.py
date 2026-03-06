import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import solve_continuous_are
from scipy.integrate import odeint

# System parameters for two coupled tanks
A1, A2 = 2.0, 2.0
C_d = 0.6
a1, a2 = 0.05, 0.05
g = 9.81

# Operating point for linearization (Steady state)
h1_0, h2_0 = 5.0, 3.0
Q12_0 = C_d * a1 * np.sqrt(2 * g * (h1_0 - h2_0))
Q_out2_0 = C_d * a2 * np.sqrt(2 * g * h2_0)
Q_in1_0 = Q12_0
Q_in2_0 = Q_out2_0 - Q12_0

# Jacobians to form State Space A and B matrices
# A = [ df1/dh1, df1/dh2 ; df2/dh1, df2/dh2 ]
# B = [ 1/A1, 0 ; 0, 1/A2 ]
R1 = (2 * np.sqrt(h1_0 - h2_0)) / (C_d * a1 * np.sqrt(2 * g))
R2 = (2 * np.sqrt(h2_0)) / (C_d * a2 * np.sqrt(2 * g))

A_sys = np.array([
    [-1/(A1*R1),  1/(A1*R1)],
    [ 1/(A2*R1), -1/(A2*R1) - 1/(A2*R2)]
])

B_sys = np.array([
    [1/A1, 0],
    [0, 1/A2]
])

# LQR Design
# We want to strongly penalize h2 deviation (index 1), and use control energy carefully
Q_lqr = np.array([
    [10.0, 0.0],
    [0.0, 100.0]
])

R_lqr = np.array([
    [1.0, 0.0],
    [0.0, 1.0]
])

# Solve Riccati equation
P = solve_continuous_are(A_sys, B_sys, Q_lqr, R_lqr)

# Calculate optimal feedback gain K
K = np.linalg.inv(R_lqr) @ B_sys.T @ P

def lqr_coupled_dynamics(state, t):
    # State is deviation from operating point: x = [delta_h1, delta_h2]
    x = np.array(state)
    
    # Control law: u = -Kx
    u = -K @ x
    
    # Linearized dynamics: x_dot = (A - BK)x
    dxdt = (A_sys - B_sys @ K) @ x
    return dxdt

t = np.linspace(0, 50, 500)
# Initial disturbance: Tank 2 is 1.0m above setpoint
initial_state = [0.0, 1.0] 

states = odeint(lqr_coupled_dynamics, initial_state, t)

h1_dev = states[:, 0]
h2_dev = states[:, 1]
u_dev = -(K @ states.T).T

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]}, sharex=True)

ax1.plot(t, h2_dev, 'r-', linewidth=2.5, label='Tank 2 Level Deviation ($\Delta h_2$)')
ax1.plot(t, h1_dev, 'b--', linewidth=2, alpha=0.8, label='Tank 1 Level Deviation ($\Delta h_1$)')
ax1.axhline(0, color='k', linestyle=':', label='Target State (0 Deviation)')
ax1.set_ylabel('Water Level Deviation [m]', fontweight='bold')
ax1.set_title('Figure 6.1: LQR State Feedback Stabilization of Coupled Tanks', fontweight='bold', fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.4)

ax2.plot(t, u_dev[:, 0], 'b-', linewidth=2, label='Control Cmd 1 ($\Delta Q_{in1}$)')
ax2.plot(t, u_dev[:, 1], 'r-', linewidth=2, label='Control Cmd 2 ($\Delta Q_{in2}$)')
ax2.set_xlabel('Time [s]', fontweight='bold')
ax2.set_ylabel('Valve Cmd Dev [^3/s$]', fontweight='bold')
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.4)

plt.tight_layout()
save_path = r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch06/lqr_sim.png'
plt.savefig(save_path, dpi=300)
