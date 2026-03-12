"""
Ch01: Microgrid Frequency Stability — Why Energy Storage Is Essential
Simulate grid frequency response when renewable output drops suddenly,
comparing: (A) No storage, (B) With battery storage providing inertia support.
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

# ============ System Parameters ============
dt = 0.01          # seconds
T_total = 60.0     # seconds simulation
N = int(T_total / dt)
time = np.arange(N) * dt

f_nom = 50.0       # Hz nominal frequency
H_grid = 5.0       # Grid inertia constant (seconds) — conventional generators
H_storage = 2.0    # Virtual inertia from storage (seconds)
D_load = 1.5       # Load damping coefficient (pu)
P_base = 100.0     # MW base power

# Renewable drop event: at t=5s, wind output drops 20 MW (0.2 pu)
P_disturb = np.zeros(N)
for i in range(N):
    if time[i] >= 5.0:
        P_disturb[i] = -0.20  # 20% sudden power deficit

# ============ Scenario A: No Storage (grid inertia only) ============
f_no_storage = np.zeros(N)
f_no_storage[0] = f_nom
df = 0.0

for i in range(1, N):
    # Swing equation: 2H * df/dt = P_mech - P_elec - D*Δf
    # Governor response (slow): P_gov with 3s time constant
    t = time[i]
    if t >= 5.0:
        tau_gov = 3.0
        P_gov = 0.20 * (1 - np.exp(-(t - 5.0) / tau_gov))  # governor ramp
    else:
        P_gov = 0.0

    P_net = P_disturb[i] + P_gov
    delta_f = f_no_storage[i-1] - f_nom
    ddf = (P_net - D_load * delta_f / f_nom) / (2 * H_grid)
    df += ddf * dt
    f_no_storage[i] = f_nom + df * f_nom

# ============ Scenario B: With Battery Storage (virtual inertia + droop) ============
f_with_storage = np.zeros(N)
f_with_storage[0] = f_nom
df2 = 0.0

# Battery state
soc = 0.80  # initial SOC
E_cap = 50.0  # MWh capacity
P_batt = np.zeros(N)
soc_trace = np.zeros(N)
soc_trace[0] = soc
K_droop = 5.0  # droop gain: MW per Hz deviation

for i in range(1, N):
    t = time[i]
    if t >= 5.0:
        tau_gov = 3.0
        P_gov = 0.20 * (1 - np.exp(-(t - 5.0) / tau_gov))
    else:
        P_gov = 0.0

    # Battery droop response (fast, <100ms)
    delta_f = f_with_storage[i-1] - f_nom
    P_batt_cmd = -K_droop * delta_f / f_nom  # positive = discharge
    P_batt_cmd = np.clip(P_batt_cmd, -0.25, 0.25)  # ±25 MW limit

    # SOC constraint
    if soc <= 0.10 and P_batt_cmd > 0:
        P_batt_cmd = 0
    if soc >= 0.95 and P_batt_cmd < 0:
        P_batt_cmd = 0

    P_batt[i] = P_batt_cmd
    soc -= P_batt_cmd * P_base * dt / (E_cap * 3600)
    soc = np.clip(soc, 0.0, 1.0)
    soc_trace[i] = soc

    H_total = H_grid + H_storage
    P_net = P_disturb[i] + P_gov + P_batt_cmd
    ddf2 = (P_net - D_load * delta_f / f_nom) / (2 * H_total)
    df2 += ddf2 * dt
    f_with_storage[i] = f_nom + df2 * f_nom

# ============ KPI ============
f_nadir_no = np.min(f_no_storage)
f_nadir_with = np.min(f_with_storage)
rocof_no = np.min(np.diff(f_no_storage) / dt)  # worst rate of change
rocof_with = np.min(np.diff(f_with_storage) / dt)
# Find recovery time: first time freq returns to 49.95 AFTER reaching nadir
nadir_idx_no = np.argmin(f_no_storage)
nadir_idx_with = np.argmin(f_with_storage)
t_recovery_no = 0
t_recovery_with = 0
for i in range(nadir_idx_no, N):
    if f_no_storage[i] >= 49.95:
        t_recovery_no = time[i] - 5.0
        break
if t_recovery_no == 0:
    t_recovery_no = -1  # never recovered
for i in range(nadir_idx_with, N):
    if f_with_storage[i] >= 49.95:
        t_recovery_with = time[i] - 5.0
        break
if t_recovery_with == 0:
    t_recovery_with = -1

peak_batt_mw = np.max(P_batt) * P_base
soc_consumed = soc_trace[0] - np.min(soc_trace)

print("=" * 65)
print(f"{'Metric':<30}{'No Storage':>15}{'With Storage':>15}")
print("-" * 65)
print(f"{'Frequency Nadir (Hz)':<30}{f_nadir_no:>15.3f}{f_nadir_with:>15.3f}")
print(f"{'RoCoF (Hz/s)':<30}{rocof_no:>15.3f}{rocof_with:>15.3f}")
t_rec_no_str = f"{t_recovery_no:.1f}" if t_recovery_no > 0 else "Never"
t_rec_with_str = f"{t_recovery_with:.1f}" if t_recovery_with > 0 else "Never"
print(f"{'Recovery to 49.95Hz (s)':<30}{t_rec_no_str:>15}{t_rec_with_str:>15}")
print(f"{'Peak Battery Output (MW)':<30}{'-':>15}{peak_batt_mw:>15.1f}")
print(f"{'SOC Consumed (%)':<30}{'-':>15}{soc_consumed*100:>15.1f}")
print("=" * 65)

# Save KPI table
with open(os.path.join(output_dir, "freq_table.md"), "w", encoding="utf-8") as f:
    f.write("| Metric | No Storage | With Storage |\n")
    f.write("|:-------|:-----------|:-------------|\n")
    f.write(f"| Frequency Nadir (Hz) | {f_nadir_no:.3f} | {f_nadir_with:.3f} |\n")
    f.write(f"| RoCoF (Hz/s) | {rocof_no:.3f} | {rocof_with:.3f} |\n")
    f.write(f"| Recovery to 49.95Hz (s) | {t_rec_no_str} | {t_rec_with_str} |\n")
    f.write(f"| Peak Battery Output (MW) | - | {peak_batt_mw:.1f} |\n")
    f.write(f"| SOC Consumed (%) | - | {soc_consumed*100:.1f} |\n")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Panel 1: Disturbance
ax = axes[0]
ax.fill_between(time, 0, P_disturb * P_base, alpha=0.3, color='red',
                label='Renewable Power Drop (MW)')
ax.set_ylabel('Power Deficit (MW)', fontsize=11)
ax.set_title('Sudden Renewable Output Drop: 20 MW Wind Power Loss at t=5s',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)
ax.set_ylim([-25, 5])

# Panel 2: Frequency response
ax = axes[1]
ax.plot(time, f_no_storage, 'r-', lw=2, label=f'No Storage (nadir={f_nadir_no:.3f} Hz)')
ax.plot(time, f_with_storage, 'b-', lw=2, label=f'With Storage (nadir={f_nadir_with:.3f} Hz)')
ax.axhline(49.5, color='red', ls='--', lw=1, alpha=0.7, label='UFLS Threshold (49.5 Hz)')
ax.axhline(49.95, color='green', ls=':', lw=1, alpha=0.7, label='Recovery Target (49.95 Hz)')
ax.fill_between(time, 49.0, 49.5, alpha=0.08, color='red')
ax.set_ylabel('Frequency (Hz)', fontsize=11)
ax.set_title('Grid Frequency Response: With vs Without Battery Storage',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)
ax.set_ylim([49.0, 50.2])

# Panel 3: Battery response + SOC
ax = axes[2]
ax.plot(time, P_batt * P_base, 'b-', lw=2, label='Battery Output (MW)')
ax.set_ylabel('Battery Power (MW)', fontsize=11, color='blue')
ax.set_xlabel('Time (s)', fontsize=11)
ax2 = ax.twinx()
ax2.plot(time, soc_trace * 100, 'g--', lw=1.5, label='SOC (%)')
ax2.set_ylabel('SOC (%)', fontsize=11, color='green')
ax2.set_ylim([70, 85])
ax.set_title('Battery Storage Response: Fast Droop + SOC Trajectory',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax2.legend(fontsize=9, loc='upper right')
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "freq_stability_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: freq_stability_sim.png")
