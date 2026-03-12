"""
Ch07: Battery Thermal Safety — Lumped-Parameter Thermal Model
Simulate thermal runaway propagation in a 4-cell module:
Cell-1 develops internal short circuit, heat propagates to neighbors.
Compare: (A) No cooling, (B) Active liquid cooling.
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
np.random.seed(42)

# ============ Thermal Parameters (4-cell module) ============
n_cells = 4
m_cell = 0.045       # kg per cell (18650)
cp = 1000.0           # J/(kg·K) specific heat
R_cc = 8.0            # K/W thermal resistance between adjacent cells
R_amb = 50.0          # K/W thermal resistance to ambient (natural convection)
R_cool = 2.0          # K/W thermal resistance with liquid cooling (highly effective)
T_amb = 25.0          # Ambient temperature (°C)
T_runaway = 150.0     # Thermal runaway trigger temperature (°C)

# Normal heat generation: I^2 * R_internal
I_normal = 5.0        # A normal discharge
R_int = 0.05          # Ohm internal resistance
Q_normal = I_normal**2 * R_int  # 1.25 W per cell

# Internal short circuit: massive heat generation
Q_short = 80.0        # W (internal short in cell 0)

# ============ Simulation ============
dt = 0.1   # seconds
T_total = 300.0  # 5 minutes
N = int(T_total / dt)
time_s = np.arange(N) * dt

# Scenario A: No cooling
T_no_cool = np.ones((N, n_cells)) * T_amb
# Scenario B: Active liquid cooling
T_cooled = np.ones((N, n_cells)) * T_amb

runaway_flags_A = [False] * n_cells
runaway_flags_B = [False] * n_cells
runaway_times_A = [None] * n_cells
runaway_times_B = [None] * n_cells

# Cell 0 develops ISC at t=10s
t_isc = 10.0

for scenario in ['A', 'B']:
    T = T_no_cool if scenario == 'A' else T_cooled
    flags = runaway_flags_A if scenario == 'A' else runaway_flags_B
    times = runaway_times_A if scenario == 'A' else runaway_times_B
    R_to_amb = R_amb if scenario == 'A' else R_cool

    for i in range(1, N):
        t = time_s[i]
        for c in range(n_cells):
            # Heat generation
            if c == 0 and t >= t_isc:
                if flags[c]:
                    Q_gen = 200.0  # full runaway exothermic
                else:
                    Q_gen = Q_short  # ISC
            else:
                Q_gen = Q_normal

            # If this cell has entered runaway, massive heat
            if flags[c] and c != 0:
                Q_gen = 200.0

            # Heat transfer to ambient
            Q_amb = (T[i-1, c] - T_amb) / R_to_amb

            # Heat transfer to neighbors
            Q_neighbor = 0
            if c > 0:
                Q_neighbor += (T[i-1, c] - T[i-1, c-1]) / R_cc
            if c < n_cells - 1:
                Q_neighbor += (T[i-1, c] - T[i-1, c+1]) / R_cc

            # Temperature update: m*cp*dT/dt = Q_gen - Q_amb - Q_neighbor
            dT = (Q_gen - Q_amb - Q_neighbor) / (m_cell * cp) * dt
            T[i, c] = T[i-1, c] + dT

            # Check runaway trigger
            if T[i, c] >= T_runaway and not flags[c]:
                flags[c] = True
                times[c] = time_s[i]

# ============ KPI ============
cells_runaway_A = sum(1 for f in runaway_flags_A if f)
cells_runaway_B = sum(1 for f in runaway_flags_B if f)
T_peak_A = np.max(T_no_cool)
T_peak_B = np.max(T_cooled)
t_first_prop_A = runaway_times_A[1] if runaway_times_A[1] else float('inf')
t_first_prop_B = runaway_times_B[1] if runaway_times_B[1] else float('inf')

print("=" * 65)
print(f"{'Metric':<35}{'No Cooling':>13}{'Liquid Cool':>13}")
print("-" * 65)
print(f"{'Peak Temperature (°C)':<35}{T_peak_A:>13.1f}{T_peak_B:>13.1f}")
print(f"{'Cells in Runaway (of 4)':<35}{cells_runaway_A:>13d}{cells_runaway_B:>13d}")
print(f"{'Cell-0 Runaway Time (s)':<35}"
      f"{runaway_times_A[0]:>13.1f}{runaway_times_B[0]:>13.1f}")
t_prop_A_str = f"{t_first_prop_A:.1f}" if t_first_prop_A < float('inf') else "Never"
t_prop_B_str = f"{t_first_prop_B:.1f}" if t_first_prop_B < float('inf') else "Never"
print(f"{'First Propagation Time (s)':<35}{t_prop_A_str:>13}{t_prop_B_str:>13}")
print(f"{'Propagation Prevented?':<35}{'NO':>13}{'YES' if cells_runaway_B <= 1 else 'NO':>13}")
print("=" * 65)

with open(os.path.join(output_dir, "thermal_table.md"), "w", encoding="utf-8") as f:
    f.write("| Metric | No Cooling | Liquid Cooling |\n")
    f.write("|:-------|:-----------|:---------------|\n")
    f.write(f"| Peak Temperature (C) | {T_peak_A:.1f} | {T_peak_B:.1f} |\n")
    f.write(f"| Cells in Runaway (of 4) | {cells_runaway_A} | {cells_runaway_B} |\n")
    f.write(f"| Cell-0 Runaway Time (s) | {runaway_times_A[0]:.1f} | {runaway_times_B[0]:.1f} |\n")
    f.write(f"| First Propagation (s) | {t_prop_A_str} | {t_prop_B_str} |\n")
    f.write(f"| Propagation Prevented | NO | {'YES' if cells_runaway_B <= 1 else 'NO'} |\n")

# ============ Plot ============
fig, axes = plt.subplots(2, 1, figsize=(14, 10))
colors = ['red', 'orange', 'blue', 'green']
labels = ['Cell-0 (ISC)', 'Cell-1', 'Cell-2', 'Cell-3']

# Panel 1: No cooling
ax = axes[0]
for c in range(n_cells):
    ax.plot(time_s, T_no_cool[:, c], color=colors[c], lw=2, label=labels[c])
ax.axhline(T_runaway, color='black', ls='--', lw=1.5, label=f'Runaway Threshold ({T_runaway}°C)')
ax.fill_between(time_s, T_runaway, np.max(T_no_cool) * 1.05,
                alpha=0.1, color='red', label='Runaway Zone')
ax.set_ylabel('Temperature (°C)', fontsize=11)
ax.set_title('Scenario A: No Active Cooling — Thermal Runaway Propagation',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, ncol=3)
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: With liquid cooling
ax = axes[1]
for c in range(n_cells):
    ax.plot(time_s, T_cooled[:, c], color=colors[c], lw=2, label=labels[c])
ax.axhline(T_runaway, color='black', ls='--', lw=1.5, label=f'Runaway Threshold ({T_runaway}°C)')
ax.fill_between(time_s, T_runaway, max(T_runaway * 1.5, np.max(T_cooled) * 1.05),
                alpha=0.1, color='red')
ax.set_ylabel('Temperature (°C)', fontsize=11)
ax.set_xlabel('Time (s)', fontsize=11)
ax.set_title('Scenario B: Active Liquid Cooling — Propagation Contained',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, ncol=3)
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "thermal_runaway_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: thermal_runaway_sim.png")
