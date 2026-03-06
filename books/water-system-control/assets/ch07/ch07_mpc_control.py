import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# Simulate a constrained tank level control using MPC
dt = 1.0
t = np.arange(0, 50, dt)
N = len(t)

# Tank model: h[k+1] = h[k] + (Qin[k] - Qout[k]) * dt / A
A = 2.0
# To make it a linear prediction model for simple MPC, assume Qout is a constant disturbance demand
Q_demand = 0.5

# MPC Parameters
Hp = 10  # Prediction Horizon
Hc = 3   # Control Horizon
Q_weight = 10.0  # Penalty on level error
R_weight = 0.1   # Penalty on control effort

# Hard Constraints
u_min, u_max = 0.0, 1.0 # Pump capacity limits
h_min, h_max = 2.0, 8.0 # Tank physical limits

def mpc_cost(u_seq, h_current, SP):
    cost = 0.0
    h_pred = h_current
    for i in range(Hp):
        # Use control sequence up to Hc, then hold constant
        u_idx = min(i, Hc - 1)
        u_k = u_seq[u_idx]
        
        # Predict next state
        h_pred = h_pred + (u_k - Q_demand) * dt / A
        
        # Add to cost
        cost += Q_weight * (h_pred - SP)**2
        cost += R_weight * (u_k**2) # penalize pump energy
        
        # Soft penalty for hard constraints to guide optimizer
        if h_pred > h_max: cost += 1e5 * (h_pred - h_max)**2
        if h_pred < h_min: cost += 1e5 * (h_min - h_pred)**2
    return cost

h = np.zeros(N)
u = np.zeros(N)
h[0] = 3.0 # Initial level
SP = 5.0   # Target level

# Initial guess for optimizer
u_guess = np.ones(Hc) * 0.5
bounds = [(u_min, u_max) for _ in range(Hc)]

for k in range(N-1):
    # Dynamic Disturbance (e.g. sudden water draw from city)
    current_demand = Q_demand
    if 20 <= k <= 30:
        current_demand = 1.2 # Massive leak or draw
        
    # Solve MPC Optimization
    res = minimize(mpc_cost, u_guess, args=(h[k], SP), bounds=bounds, method='SLSQP')
    u_opt = res.x[0] # Apply only the first control move (Receding Horizon)
    
    # Store and apply to plant
    u[k] = u_opt
    h[k+1] = h[k] + (u[k] - current_demand) * dt / A
    
    # Shift guess for next step
    u_guess = np.roll(res.x, -1)
    u_guess[-1] = u_guess[-2]

# Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(t, h, 'b-', linewidth=2.5, label='Water Level (t)$')
ax1.axhline(SP, color='k', linestyle='--', label='Setpoint (5.0m)')
ax1.axhline(h_min, color='r', linestyle=':', label='Hard Min Constraint (2.0m)')
ax1.axhline(h_max, color='r', linestyle=':', label='Hard Max Constraint (8.0m)')
ax1.fill_between(t[20:31], 0, 10, color='gray', alpha=0.2, label='Massive Disturbance Zone')
ax1.set_ylabel('Water Level [m]', fontweight='bold')
ax1.set_ylim(1, 9)
ax1.legend(loc='lower right')
ax1.grid(True, alpha=0.4)

ax2.plot(t[:-1], u[:-1], 'g-', linewidth=2.5, label='Optimal Pump Cmd (t)$')
ax2.axhline(u_max, color='r', linestyle=':', label='Pump Saturation Limit (1.0 ^3/s$)')
ax2.axhline(u_min, color='r', linestyle=':', label='Pump Off Limit (0.0 ^3/s$)')
ax2.fill_between(t[20:31], -0.2, 1.2, color='gray', alpha=0.2)
ax2.set_xlabel('Time [s]', fontweight='bold')
ax2.set_ylabel('Pump Command', fontweight='bold')
ax2.set_ylim(-0.1, 1.2)
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.4)

plt.suptitle('Figure 7.1: Model Predictive Control (MPC) with Hard Constraints', fontsize=14, fontweight='bold')
plt.tight_layout()
save_path = r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch07/mpc_sim.png'
plt.savefig(save_path, dpi=300)
