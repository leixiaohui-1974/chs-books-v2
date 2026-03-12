"""
Ch04: PCS Bidirectional Control — CC/CV Charging Strategy Simulation
Simulate a Buck converter charging a lithium battery with CC (Constant Current)
followed by CV (Constant Voltage) phases, demonstrating the transition logic.
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

# ============ Battery + Converter Parameters ============
V_bus = 400.0       # DC bus voltage (V)
V_cutoff = 4.2      # Cell cutoff voltage (V)
N_series = 96       # Series cells (for ~400V pack)
V_pack_max = V_cutoff * N_series  # 403.2 V
V_pack_nom = 3.7 * N_series       # 355.2 V

# Battery model: 1st-order Thevenin
Q_cap = 50.0        # Ah capacity
R0 = 0.008 * N_series  # Pack ohmic resistance (0.768 Ohm total)
R1 = 0.005 * N_series  # Polarization resistance (0.48 Ohm)
C1 = 3000.0            # Polarization capacitance (F)

# CC/CV parameters
I_cc = 0.5 * Q_cap   # 0.5C charging current = 25A
I_cv_cutoff = 0.05 * Q_cap  # CV termination at C/20 = 2.5A

# OCV-SOC curve (simplified polynomial)
def ocv(soc):
    """Pack OCV as function of SOC (0-1)"""
    # Per-cell OCV: ~3.0V at 0%, ~4.2V at 100%
    v_cell = 3.0 + 1.0 * soc + 0.2 * soc**2 - 0.05 * soc**3
    v_cell = np.clip(v_cell, 3.0, 4.2)
    return v_cell * N_series

# ============ Simulation ============
dt = 1.0  # 1 second steps
T_total = 7200  # 2 hours max
N = int(T_total / dt)
time_s = np.arange(N) * dt
time_min = time_s / 60.0

soc = 0.10  # Start at 10% SOC
U1 = 0.0    # Polarization voltage

soc_trace = np.zeros(N)
V_trace = np.zeros(N)
I_trace = np.zeros(N)
P_trace = np.zeros(N)
duty_trace = np.zeros(N)
mode_trace = np.zeros(N)  # 0=CC, 1=CV, 2=done

mode = 0  # Start in CC mode
t_switch = None
t_done = None

for i in range(N):
    V_ocv = ocv(soc)

    if mode == 0:  # CC phase
        I_charge = I_cc
        V_terminal = V_ocv + I_charge * R0 + U1
        if V_terminal >= V_pack_max:
            mode = 1
            t_switch = time_min[i]
    elif mode == 1:  # CV phase
        V_terminal = V_pack_max
        I_charge = (V_pack_max - V_ocv - U1) / R0
        I_charge = max(I_charge, 0)
        if I_charge <= I_cv_cutoff:
            mode = 2
            t_done = time_min[i]
    else:  # Done
        I_charge = 0
        V_terminal = V_ocv

    # Update polarization voltage
    dU1 = (-U1 / (R1 * C1) + I_charge / C1) * dt
    U1 += dU1

    # Update SOC
    soc += I_charge * dt / (Q_cap * 3600)
    soc = np.clip(soc, 0, 1.0)

    # Duty cycle: D = V_terminal / V_bus (Buck converter)
    duty = V_terminal / V_bus if V_bus > 0 else 0
    duty = np.clip(duty, 0, 1.0)

    soc_trace[i] = soc
    V_trace[i] = V_terminal
    I_trace[i] = I_charge
    P_trace[i] = V_terminal * I_charge / 1000  # kW
    duty_trace[i] = duty
    mode_trace[i] = mode

    if mode == 2 and i > 0:
        # Fill remaining with final values
        soc_trace[i:] = soc
        V_trace[i:] = V_ocv
        I_trace[i:] = 0
        P_trace[i:] = 0
        duty_trace[i:] = V_ocv / V_bus
        mode_trace[i:] = 2
        break

# ============ KPI ============
soc_final = soc_trace[min(i, N-1)]
energy_in = np.sum(P_trace[:i] * dt) / 3600  # kWh
if t_switch is None:
    t_switch = time_min[min(i, N-1)]
if t_done is None:
    t_done = time_min[min(i, N-1)]

cc_duration = t_switch
cv_duration = t_done - t_switch if t_done > t_switch else 0
peak_power = np.max(P_trace)

print("=" * 60)
print(f"{'Metric':<35}{'Value':>20}")
print("-" * 60)
print(f"{'CC Phase Duration (min)':<35}{cc_duration:>20.1f}")
print(f"{'CV Phase Duration (min)':<35}{cv_duration:>20.1f}")
print(f"{'Total Charge Time (min)':<35}{t_done:>20.1f}")
print(f"{'Final SOC (%)':<35}{soc_final*100:>20.1f}")
print(f"{'Energy Input (kWh)':<35}{energy_in:>20.1f}")
print(f"{'Peak Charging Power (kW)':<35}{peak_power:>20.1f}")
print(f"{'CC→CV Transition Voltage (V)':<35}{V_pack_max:>20.1f}")
print("=" * 60)

with open(os.path.join(output_dir, "ccv_table.md"), "w", encoding="utf-8") as f:
    f.write("| Metric | Value |\n")
    f.write("|:-------|:------|\n")
    f.write(f"| CC Phase Duration (min) | {cc_duration:.1f} |\n")
    f.write(f"| CV Phase Duration (min) | {cv_duration:.1f} |\n")
    f.write(f"| Total Charge Time (min) | {t_done:.1f} |\n")
    f.write(f"| Final SOC (%) | {soc_final*100:.1f} |\n")
    f.write(f"| Energy Input (kWh) | {energy_in:.1f} |\n")
    f.write(f"| Peak Charging Power (kW) | {peak_power:.1f} |\n")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Trim to actual charging duration + margin
t_end = min(t_done + 10, T_total / 60)
mask = time_min <= t_end

# Panel 1: Voltage and Current
ax = axes[0]
ax.plot(time_min[mask], V_trace[mask], 'r-', lw=2, label='Pack Voltage (V)')
ax.set_ylabel('Voltage (V)', fontsize=11, color='red')
ax.axhline(V_pack_max, color='red', ls='--', lw=1, alpha=0.5,
           label=f'Cutoff Voltage ({V_pack_max:.1f} V)')
if t_switch:
    ax.axvline(t_switch, color='orange', ls=':', lw=2, label=f'CC→CV Switch ({t_switch:.1f} min)')
ax2 = ax.twinx()
ax2.plot(time_min[mask], I_trace[mask], 'b-', lw=2, label='Charge Current (A)')
ax2.set_ylabel('Current (A)', fontsize=11, color='blue')
ax.set_title('CC/CV Charging Profile: Voltage and Current',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='center left')
ax2.legend(fontsize=9, loc='center right')
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: SOC and Power
ax = axes[1]
ax.plot(time_min[mask], soc_trace[mask] * 100, 'g-', lw=2, label='SOC (%)')
ax.set_ylabel('SOC (%)', fontsize=11, color='green')
ax2 = ax.twinx()
ax2.plot(time_min[mask], P_trace[mask], 'm-', lw=2, label='Charging Power (kW)')
ax2.set_ylabel('Power (kW)', fontsize=11, color='purple')
ax.set_title('State of Charge and Charging Power',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='center left')
ax2.legend(fontsize=9, loc='center right')
ax.grid(True, ls='--', alpha=0.4)
# Mark CC and CV regions
if t_switch:
    ax.axvspan(0, t_switch, alpha=0.08, color='blue', label='CC Phase')
    ax.axvspan(t_switch, t_done if t_done else t_end, alpha=0.08, color='orange')
    ax.text(t_switch / 2, 95, 'CC Phase', ha='center', fontsize=10, color='blue')
    if t_done:
        ax.text((t_switch + t_done) / 2, 95, 'CV Phase', ha='center', fontsize=10, color='orange')

# Panel 3: Buck converter duty cycle
ax = axes[2]
ax.plot(time_min[mask], duty_trace[mask] * 100, 'k-', lw=2, label='Duty Cycle D (%)')
ax.set_ylabel('Duty Cycle (%)', fontsize=11)
ax.set_xlabel('Time (min)', fontsize=11)
ax.set_title('Buck Converter Duty Cycle: D = V_pack / V_bus',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "ccv_charging_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: ccv_charging_sim.png")
