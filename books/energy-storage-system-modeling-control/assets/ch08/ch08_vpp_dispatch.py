"""
Ch08: Virtual Power Plant (VPP) — Distributed Storage Aggregation
Simulate 10 distributed battery units under coordinated vs uncoordinated dispatch.
Compare peak-shaving effectiveness and individual SOC balance.
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
n_units = 10        # Distributed storage units
T = 24              # hours
dt = 0.25           # 15-minute intervals
N = int(T / dt)     # 96 steps
time_h = np.arange(N) * dt

# Each unit: 2 MWh capacity, 500 kW max power (commercial-scale)
E_cap = np.array([2000.0] * n_units)  # kWh
P_max = np.array([500.0] * n_units)   # kW charge/discharge limit
soc_init = np.random.uniform(0.4, 0.7, n_units)  # Random initial SOC

# Grid load profile (MW) — typical commercial/industrial
load_base = np.zeros(N)
for i in range(N):
    h = time_h[i]
    load_base[i] = 3.0 + 2.0 * np.sin(np.pi * (h - 6) / 12)  # Peak at noon
    if 9 <= h <= 11 or 14 <= h <= 16:
        load_base[i] += 1.5  # Office peak hours
    if 18 <= h <= 20:
        load_base[i] += 2.0  # Evening peak
load_base += np.random.normal(0, 0.1, N)
load_base = np.maximum(load_base, 1.0)  # MW

# TOU electricity price (CNY/kWh)
price = np.zeros(N)
for i in range(N):
    h = time_h[i]
    if 8 <= h <= 12 or 17 <= h <= 21:
        price[i] = 1.2   # Peak
    elif 0 <= h <= 7 or 22 <= h <= 24:
        price[i] = 0.3   # Valley
    else:
        price[i] = 0.7   # Shoulder

# ============ Scenario A: Uncoordinated (each unit acts independently) ============
soc_A = np.zeros((N + 1, n_units))
soc_A[0] = soc_init.copy()
P_A = np.zeros((N, n_units))
grid_load_A = load_base.copy()

for i in range(N):
    for u in range(n_units):
        # Simple rule: charge when cheap, discharge when expensive
        if price[i] <= 0.3 and soc_A[i, u] < 0.9:
            P_A[i, u] = -P_max[u]  # charge (negative = absorb)
        elif price[i] >= 1.2 and soc_A[i, u] > 0.2:
            P_A[i, u] = P_max[u]   # discharge (positive = inject)
        else:
            P_A[i, u] = 0

        # SOC update
        soc_A[i+1, u] = soc_A[i, u] - P_A[i, u] * dt / E_cap[u]
        soc_A[i+1, u] = np.clip(soc_A[i+1, u], 0.1, 0.95)

    grid_load_A[i] = load_base[i] - np.sum(P_A[i]) / 1000  # MW

# ============ Scenario B: VPP Coordinated Dispatch ============
soc_B = np.zeros((N + 1, n_units))
soc_B[0] = soc_init.copy()
P_B = np.zeros((N, n_units))
grid_load_B = load_base.copy()

# VPP target: flatten load to average, proportionally distribute among units
load_avg = np.mean(load_base)

for i in range(N):
    # Desired aggregate power (MW): positive = discharge to grid
    P_target_mw = load_base[i] - load_avg
    P_target_kw = P_target_mw * 1000  # convert to kW total

    # Distribute proportionally based on available capacity
    available = np.zeros(n_units)
    for u in range(n_units):
        if P_target_kw > 0:  # Need discharge
            available[u] = min(P_max[u], (soc_B[i, u] - 0.15) * E_cap[u] / dt)
        else:  # Need charge
            available[u] = min(P_max[u], (0.90 - soc_B[i, u]) * E_cap[u] / dt)
        available[u] = max(available[u], 0)

    total_available = np.sum(available)
    if total_available > 0:
        for u in range(n_units):
            share = available[u] / total_available
            P_cmd = P_target_kw * share
            P_cmd = np.clip(P_cmd, -P_max[u], P_max[u])
            P_B[i, u] = P_cmd
    else:
        P_B[i] = 0

    # SOC update
    for u in range(n_units):
        soc_B[i+1, u] = soc_B[i, u] - P_B[i, u] * dt / E_cap[u]
        soc_B[i+1, u] = np.clip(soc_B[i+1, u], 0.1, 0.95)

    grid_load_B[i] = load_base[i] - np.sum(P_B[i]) / 1000

# ============ KPI ============
peak_orig = np.max(load_base)
peak_A = np.max(grid_load_A)
peak_B = np.max(grid_load_B)
valley_orig = np.min(load_base)
valley_A = np.min(grid_load_A)
valley_B = np.min(grid_load_B)
pv_ratio_orig = (peak_orig - valley_orig) / peak_orig * 100
pv_ratio_A = (peak_A - valley_A) / peak_A * 100
pv_ratio_B = (peak_B - valley_B) / peak_B * 100

# Cost calculation
cost_orig = np.sum(load_base * 1000 * price * dt)  # kWh * price
cost_A = np.sum(grid_load_A * 1000 * price * dt)
cost_B = np.sum(grid_load_B * 1000 * price * dt)

# SOC dispersion (std at end)
soc_std_A = np.std(soc_A[-1])
soc_std_B = np.std(soc_B[-1])

print("=" * 70)
print(f"{'Metric':<30}{'No Storage':>13}{'Uncoord.':>13}{'VPP Coord.':>13}")
print("-" * 70)
print(f"{'Peak Load (MW)':<30}{peak_orig:>13.2f}{peak_A:>13.2f}{peak_B:>13.2f}")
print(f"{'Valley Load (MW)':<30}{valley_orig:>13.2f}{valley_A:>13.2f}{valley_B:>13.2f}")
print(f"{'Peak-Valley Ratio (%)':<30}{pv_ratio_orig:>13.1f}{pv_ratio_A:>13.1f}{pv_ratio_B:>13.1f}")
print(f"{'Daily Cost (CNY)':<30}{cost_orig:>13.0f}{cost_A:>13.0f}{cost_B:>13.0f}")
print(f"{'SOC Std at End':<30}{'-':>13}{soc_std_A:>13.3f}{soc_std_B:>13.3f}")
print(f"{'Peak Reduction (%)':<30}{'-':>13}"
      f"{(1-peak_A/peak_orig)*100:>13.1f}{(1-peak_B/peak_orig)*100:>13.1f}")
print("=" * 70)

with open(os.path.join(output_dir, "vpp_table.md"), "w", encoding="utf-8") as f:
    f.write("| Metric | No Storage | Uncoordinated | VPP Coordinated |\n")
    f.write("|:-------|:-----------|:--------------|:----------------|\n")
    f.write(f"| Peak Load (MW) | {peak_orig:.2f} | {peak_A:.2f} | {peak_B:.2f} |\n")
    f.write(f"| Valley Load (MW) | {valley_orig:.2f} | {valley_A:.2f} | {valley_B:.2f} |\n")
    f.write(f"| Peak-Valley Ratio (%) | {pv_ratio_orig:.1f} | {pv_ratio_A:.1f} | {pv_ratio_B:.1f} |\n")
    f.write(f"| Daily Cost (CNY) | {cost_orig:.0f} | {cost_A:.0f} | {cost_B:.0f} |\n")
    f.write(f"| SOC Dispersion (Std) | - | {soc_std_A:.3f} | {soc_std_B:.3f} |\n")
    f.write(f"| Peak Reduction (%) | - | {(1-peak_A/peak_orig)*100:.1f} | {(1-peak_B/peak_orig)*100:.1f} |\n")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Panel 1: Load profiles
ax = axes[0]
ax.plot(time_h, load_base, 'k--', lw=1.5, label='Original Load')
ax.plot(time_h, grid_load_A, 'r-', lw=2, label=f'Uncoordinated (peak={peak_A:.1f} MW)')
ax.plot(time_h, grid_load_B, 'b-', lw=2, label=f'VPP Coordinated (peak={peak_B:.1f} MW)')
ax.axhline(load_avg, color='green', ls=':', lw=1, label=f'Target Average ({load_avg:.1f} MW)')
ax.fill_between(time_h, load_base, grid_load_B,
                where=grid_load_B < load_base, alpha=0.15, color='blue', label='Peak Shaving')
ax.set_ylabel('Grid Load (MW)', fontsize=11)
ax.set_title('Grid Load: Original vs Uncoordinated vs VPP Coordinated',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, ncol=2)
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: SOC trajectories
ax = axes[1]
for u in range(n_units):
    ax.plot(time_h, soc_B[:-1, u] * 100, alpha=0.6, lw=1.5)
ax.set_ylabel('SOC (%)', fontsize=11)
ax.set_title('VPP Coordinated: Individual Unit SOC Trajectories (10 units)',
             fontsize=13, fontweight='bold')
ax.axhline(15, color='red', ls='--', lw=1, alpha=0.5, label='SOC Lower Limit')
ax.axhline(90, color='red', ls='--', lw=1, alpha=0.5, label='SOC Upper Limit')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Aggregate power and price
ax = axes[2]
P_agg_A = np.sum(P_A, axis=1) / 1000  # MW
P_agg_B = np.sum(P_B, axis=1) / 1000
ax.plot(time_h, P_agg_A, 'r-', lw=2, label='Uncoordinated Aggregate')
ax.plot(time_h, P_agg_B, 'b-', lw=2, label='VPP Coordinated Aggregate')
ax.set_ylabel('Aggregate Storage Power (MW)', fontsize=11)
ax.set_xlabel('Time (h)', fontsize=11)
ax2 = ax.twinx()
ax2.fill_between(time_h, 0, price, alpha=0.15, color='orange', label='TOU Price')
ax2.set_ylabel('Electricity Price (CNY/kWh)', fontsize=11, color='orange')
ax.set_title('Aggregate Storage Dispatch vs Electricity Price',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax2.legend(fontsize=9, loc='upper right')
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "vpp_dispatch_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: vpp_dispatch_sim.png")
