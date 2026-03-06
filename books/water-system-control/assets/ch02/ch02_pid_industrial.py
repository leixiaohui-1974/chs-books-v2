import numpy as np
import matplotlib.pyplot as plt
import os

class IndustrialPID:
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
        error = setpoint - pv
        P = self.Kc * error
        
        # Potential integral
        potential_I = self.integral + self.Kc * (self.dt / self.tau_I) * error
        D = self.Kc * self.tau_D * (error - self.prev_error) / self.dt
        
        u_unclamped = P + potential_I + D
        
        if u_unclamped > self.out_max:
            u = self.out_max
            if not self.anti_windup or error < 0:
                self.integral = potential_I 
            elif self.anti_windup and error > 0:
                pass 
        elif u_unclamped < self.out_min:
            u = self.out_min
            if not self.anti_windup or error > 0:
                self.integral = potential_I
            elif self.anti_windup and error < 0:
                pass 
        else:
            u = u_unclamped
            self.integral = potential_I
            
        self.prev_error = error
        return u

dt = 1.0
t = np.arange(0, 300, dt)
n = len(t)

def run_sim(anti_windup):
    pid = IndustrialPID(Kc=10.0, tau_I=20.0, tau_D=0.0, dt=dt, out_min=0.0, out_max=100.0, anti_windup=anti_windup)
    pv = np.zeros(n)
    u = np.zeros(n)
    integral_term = np.zeros(n)
    
    pv[0] = 5.0
    u[0] = 50.0
    
    for i in range(1, n):
        dist = 2.0 if 20 <= t[i] <= 100 else 0.5
        outflow = 0.05 * u[i-1]
        pv[i] = pv[i-1] + (dist - outflow) * dt
        
        u[i] = pid.compute(5.0, pv[i])
        integral_term[i] = pid.integral
        
    return pv, u, integral_term

pv_no_aw, u_no_aw, i_no_aw = run_sim(False)
pv_aw, u_aw, i_aw = run_sim(True)

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

ax1.plot(t, pv_no_aw, 'r--', label='Level (Standard PID)')
ax1.plot(t, pv_aw, 'b-', linewidth=2, label='Level (Anti-Windup PID)')
ax1.axhline(5.0, color='k', linestyle=':', label='Setpoint (5.0m)')
ax1.set_ylabel('Water Level [m]', fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.5)

ax2.plot(t, u_no_aw, 'r--', label='Valve Output % (Standard)')
ax2.plot(t, u_aw, 'b-', linewidth=2, label='Valve Output % (Anti-Windup)')
ax2.axhline(100.0, color='k', linestyle=':', label='Physical Max (100%)')
ax2.set_ylabel('Valve Cmd [%]', fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.5)

ax3.plot(t, i_no_aw, 'r--', label='Integral Term (Standard)')
ax3.plot(t, i_aw, 'b-', linewidth=2, label='Integral Term (Anti-Windup)')
ax3.set_xlabel('Time [s]', fontweight='bold')
ax3.set_ylabel('Integral Accumulation', fontweight='bold')
ax3.legend(loc='upper right')
ax3.grid(True, alpha=0.5)

plt.suptitle('Figure 2.1: Integrator Windup vs Anti-Windup in Flood Control', fontsize=14, fontweight='bold')
plt.tight_layout()

save_path = r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch02/pid_windup_sim.png'
plt.savefig(save_path, dpi=300)
