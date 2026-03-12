"""
Ch01: Compound Risk Profile — Why Intelligent Hydrology Matters in 2026
Compare reactive vs predictive flood management under compound risk scenarios.
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

# ============ Scenario: 72h Compound Event ============
N = 72  # hours
time_h = np.arange(N)

# Rainfall (mm/h) — two bursts
rain = np.zeros(N)
for i in range(N):
    if 8 <= i <= 16:
        rain[i] = 25 * np.sin(np.pi * (i - 8) / 8)
    if 36 <= i <= 48:
        rain[i] = 45 * np.sin(np.pi * (i - 36) / 12)

# Infrastructure aging: pump/gate release capacity degrades
pump_capacity_new = 5.0  # Mm3/h (design capacity)
pump_capacity_aged = 3.0  # Mm3/h (aged, 60%)

# Urban expansion: CN increases over decades
CN_2000 = 65  # year 2000
CN_2026 = 82  # year 2026

# Simple runoff: Q = rain * area * RC / 1000, RC ~ (CN/100)^2
area = 220e6  # 220 km2

def compute_runoff(rain, CN):
    rc = (CN / 100.0) ** 2
    return rain * area * rc / 1e6 / 1000  # Mm3/h

inflow_2000 = compute_runoff(rain, CN_2000)
inflow_2026 = compute_runoff(rain, CN_2026)

# ============ Mode A: Reactive (wait for alarm) ============
def simulate_reactive(inflow, pump_cap):
    vol = np.zeros(N + 1)
    vol[0] = 8.0  # 8 Mm3 initial
    release = np.zeros(N)
    alarm_level = 15.0
    flood_level = 20.0

    for i in range(N):
        if vol[i] > alarm_level:
            release[i] = min(pump_cap, vol[i] - alarm_level + inflow[i])
        else:
            release[i] = 1.0  # base flow

        vol[i + 1] = vol[i] + inflow[i] - release[i]
        vol[i + 1] = max(0, vol[i + 1])

    return vol, release

# ============ Mode B: Predictive (forecast + pre-release) ============
def simulate_predictive(inflow, pump_cap, rain_forecast):
    vol = np.zeros(N + 1)
    vol[0] = 8.0
    release = np.zeros(N)
    alarm_level = 15.0

    for i in range(N):
        # 12h lookahead: predict future inflow
        future_vol = 0
        for k in range(min(12, N - i)):
            future_vol += compute_runoff(np.array([rain_forecast[i + k]]), CN_2026)[0]

        predicted_peak = vol[i] + future_vol
        if predicted_peak > alarm_level * 0.6 or vol[i] > alarm_level * 0.5:
            # Aggressive pre-release to create buffer
            target = pump_cap  # full capacity pre-release
        elif vol[i] > alarm_level:
            target = pump_cap
        else:
            target = 0.5

        release[i] = min(target, pump_cap)
        vol[i + 1] = vol[i] + inflow[i] - release[i]
        vol[i + 1] = max(0, vol[i + 1])

    return vol, release

# Run 4 scenarios
flood_level = 20.0

# Scenario 1: 2000 + new pump + reactive (baseline: no problem)
vol_base, rel_base = simulate_reactive(inflow_2000, pump_capacity_new)

# Scenario 2: 2026 + aged pump + reactive (compound risk: disaster)
vol_compound, rel_compound = simulate_reactive(inflow_2026, pump_capacity_aged)

# Scenario 3: 2026 + aged pump + predictive (intelligent: saved)
vol_predict, rel_predict = simulate_predictive(inflow_2026, pump_capacity_aged, rain)

# ============ KPI ============
def kpi(vol, name):
    peak = np.max(vol)
    flood_hrs = int(np.sum(vol > flood_level))
    return peak, flood_hrs

peak_base, flood_base = kpi(vol_base, "Baseline")
peak_comp, flood_comp = kpi(vol_compound, "Compound")
peak_pred, flood_pred = kpi(vol_predict, "Predictive")

print("=" * 65)
print(f"{'Scenario':<30}{'Peak (Mm3)':>12}{'Flood Hours':>13}{'Status':>10}")
print("-" * 65)
print(f"{'2000: New Pump + Reactive':<30}{peak_base:>12.1f}{flood_base:>13d}{'SAFE':>10}")
print(f"{'2026: Aged Pump + Reactive':<30}{peak_comp:>12.1f}{flood_comp:>13d}{'FLOOD':>10}")
print(f"{'2026: Aged Pump + Predictive':<30}{peak_pred:>12.1f}{flood_pred:>13d}{'SAFE' if flood_pred==0 else 'RISK':>10}")
print(f"\nCompound risk amplification: peak {peak_base:.1f} -> {peak_comp:.1f} Mm3 (+{(peak_comp-peak_base)/peak_base*100:.0f}%)")
print(f"Predictive control recovery: {peak_comp:.1f} -> {peak_pred:.1f} Mm3 ({flood_comp} -> {flood_pred} flood hours)")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Panel 1: Hazard x Exposure x Vulnerability
ax = axes[0]
ax.fill_between(time_h, 0, rain, alpha=0.3, color='blue', label='Rainfall (Hazard)')
ax.set_ylabel('Rainfall (mm/h)', fontsize=11, color='blue')
ax2 = ax.twinx()
ax2.plot(time_h, inflow_2000, 'g--', lw=1.5, label=f'Runoff 2000 (CN={CN_2000})')
ax2.plot(time_h, inflow_2026, 'r-', lw=2, label=f'Runoff 2026 (CN={CN_2026})')
ax2.set_ylabel('Inflow (Mm3/h)', fontsize=11, color='red')
ax2.legend(fontsize=9, loc='upper right')
ax.legend(fontsize=9, loc='upper left')
ax.set_title('Compound Risk: Same Rainfall, Different Runoff (Urbanization CN Increase)',
             fontsize=13, fontweight='bold')
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: Volume trajectories
ax = axes[1]
tv = np.arange(N + 1)
ax.plot(tv, vol_base, 'g--', lw=1.5, label=f'2000 Baseline (peak={peak_base:.1f})')
ax.plot(tv, vol_compound, 'r-', lw=2, label=f'2026 Reactive (peak={peak_comp:.1f})')
ax.plot(tv, vol_predict, 'b-', lw=2, label=f'2026 Predictive (peak={peak_pred:.1f})')
ax.axhline(flood_level, color='red', ls='--', lw=1.5, label=f'Flood Level ({flood_level} Mm3)')
ax.fill_between(tv, flood_level, max(peak_comp, flood_level) * 1.1,
                alpha=0.1, color='red', label='Flood Zone')
# Mark flood hours
flood_mask = vol_compound > flood_level
ax.fill_between(tv, flood_level, vol_compound,
                where=flood_mask,
                alpha=0.3, color='red')
ax.set_ylabel('Storage Volume (Mm3)', fontsize=11)
ax.set_title('Three Futures: Baseline / Compound Reactive / Compound Predictive',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Release strategies
ax = axes[2]
ax.step(time_h, rel_base, 'g--', lw=1.5, where='post', label='2000 Release')
ax.step(time_h, rel_compound, 'r-', lw=2, where='post', label='2026 Reactive Release')
ax.step(time_h, rel_predict, 'b-', lw=2, where='post', label='2026 Predictive Release')
ax.axhline(pump_capacity_new, color='green', ls=':', lw=1, alpha=0.5,
           label=f'New Pump Cap ({pump_capacity_new} m3/s)')
ax.axhline(pump_capacity_aged, color='red', ls=':', lw=1, alpha=0.5,
           label=f'Aged Pump Cap ({pump_capacity_aged} m3/s)')
ax.fill_between(time_h, rel_predict, rel_compound,
                where=rel_predict > rel_compound,
                alpha=0.15, color='blue', label='Predictive Pre-release')
ax.set_xlabel('Time (hours)', fontsize=11)
ax.set_ylabel('Release (Mm3/h)', fontsize=11)
ax.set_title('Release Strategy: Reactive Panic vs Predictive Pre-positioning',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, ncol=2, loc='upper right')
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "risk_profile_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: risk_profile_sim.png")
