import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Coupled Tanks Parameters
A1, A2 = 2.0, 2.0
C_d = 0.6
a1, a2 = 0.05, 0.05
g = 9.81

def coupled_dynamics(state, t, Q_in1, Q_in2):
    h1, h2 = state
    # Prevent negative heads causing math domain errors
    h1 = max(h1, 0.0)
    h2 = max(h2, 0.0)
    
    # Flow from Tank 1 to Tank 2 depends on head difference
    delta_h = h1 - h2
    Q_12 = np.sign(delta_h) * C_d * a1 * np.sqrt(2 * g * abs(delta_h))
    
    # Outflow from Tank 2
    Q_out2 = C_d * a2 * np.sqrt(2 * g * h2)
    
    dh1_dt = (Q_in1 - Q_12) / A1
    dh2_dt = (Q_in2 + Q_12 - Q_out2) / A2
    
    return [dh1_dt, dh2_dt]

t = np.linspace(0, 300, 1000)

# Scenario: Step input to Tank 1 only, observing the coupled response in Tank 2
Q_in1 = 0.2
Q_in2 = 0.0
initial_state = [0.0, 0.0]

states = odeint(coupled_dynamics, initial_state, t, args=(Q_in1, Q_in2))
h1 = states[:, 0]
h2 = states[:, 1]

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(t, h1, 'b-', linewidth=2.5, label='Tank 1 Level (h1)')
ax.plot(t, h2, 'r--', linewidth=2.5, label='Tank 2 Level (h2)')

# Annotate strong coupling effect
ax.annotate('Water flows into T1,\nbut T2 also rises due to coupling', xy=(50, 0.5), xytext=(80, 0.2),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))

ax.set_xlabel('Time [s]', fontweight='bold')
ax.set_ylabel('Water Level [m]', fontweight='bold')
ax.set_title('Figure 4.1: Nonlinear Dynamic Response of Coupled Interacting Tanks', fontweight='bold', fontsize=14)
ax.legend(loc='upper left')
ax.grid(True, alpha=0.5)

save_path = r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch04/coupled_tanks_sim.png'
plt.savefig(save_path, dpi=300, bbox_inches='tight')
