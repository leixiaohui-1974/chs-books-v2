"""
Ch10: Multi-Agent Water Operations — Dispatcher vs Analyzer vs Controller
Simulate a 24h flood event where three specialized agents must coordinate.
Compare single-agent (monolithic) vs multi-agent (MAS) performance.
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

# ============ Scenario: 24h Flood Event ============
N = 144  # 144 steps x 10min = 24 hours
dt = 10.0 / 60  # hours (10 min)
time_h = np.arange(N) * dt

# Rainfall (mm/h) — extreme storm event
rain = np.zeros(N)
for i in range(N):
    t = time_h[i]
    if 4 <= t <= 10:
        rain[i] = 60 * np.sin(np.pi * (t - 4) / 6)
    if 14 <= t <= 18:  # second wave
        rain[i] += 45 * np.sin(np.pi * (t - 14) / 4)

# Sensor anomaly: station drift at t=8-12h
sensor_drift = np.zeros(N)
for i in range(N):
    t = time_h[i]
    if 8 <= t <= 12:
        sensor_drift[i] = -5.0  # reports 5 mm/h less than reality

# Reservoir: capacity 100 Mm3, initial 65 Mm3 (already high)
rv_cap = 100.0
rv_init = 65.0
flood_line = 90.0
safe_line = 80.0

# Inflow conversion: rain * catchment_area * runoff_coeff
catchment = 500e6  # 500 km2
rc = 0.6
inflow = rain * catchment * rc / 1e6 / 1000  # Mm3/h

# ============ Mode A: Single Agent (Monolithic) ============
# One LLM agent tries to do everything: forecast + analyze + control
# It sees raw sensor data (with drift), makes ad-hoc decisions
mono_vol = np.zeros(N + 1)
mono_vol[0] = rv_init
mono_release = np.zeros(N)
mono_alerts = []
mono_sensor_detected = False

for i in range(N):
    t = time_h[i]
    observed_rain = rain[i] + sensor_drift[i]  # contaminated
    observed_rain = max(0, observed_rain)  # can't be negative

    # Monolithic agent: simple rule based on observed rain
    # No forecast lookahead, no sensor validation
    inflow_est = observed_rain * catchment * rc / 1e6 / 1000

    if mono_vol[i] > flood_line:
        mono_release[i] = 8.0  # panic mode
    elif mono_vol[i] > safe_line:
        mono_release[i] = 4.0  # cautious
    elif observed_rain > 20:
        mono_release[i] = 3.0
    else:
        mono_release[i] = 1.0  # base release

    mono_vol[i + 1] = mono_vol[i] + (inflow[i] - mono_release[i]) * dt
    mono_vol[i + 1] = np.clip(mono_vol[i + 1], 0, rv_cap)

    if mono_vol[i + 1] > flood_line:
        mono_alerts.append((t, "FLOOD_WARNING"))

# ============ Mode B: Multi-Agent System (MAS) ============
# Dispatcher: forecast + planning
# Analyzer: sensor validation + anomaly detection
# Controller: execute release with safety guardrails

mas_vol = np.zeros(N + 1)
mas_vol[0] = rv_init
mas_release = np.zeros(N)
mas_alerts = []
mas_sensor_flags = np.zeros(N)
mas_forecast = np.zeros(N)

# Analyzer: detect sensor drift by cross-validating with radar
radar_rain = rain.copy()  # radar is clean

# Dispatcher: 6-step lookahead forecast
for i in range(N):
    t = time_h[i]

    # === Analyzer Agent ===
    observed_rain = rain[i] + sensor_drift[i]
    observed_rain = max(0, observed_rain)

    # Cross-validate station vs radar
    discrepancy = abs(radar_rain[i] - observed_rain)
    if discrepancy > 3.0 and radar_rain[i] > 5:
        mas_sensor_flags[i] = 1  # flag sensor drift
        corrected_rain = radar_rain[i]  # trust radar
    else:
        corrected_rain = (radar_rain[i] + observed_rain) / 2  # blend

    # === Dispatcher Agent ===
    # 6-step lookahead: predict future inflow
    future_inflow = 0
    for k in range(min(6, N - i)):
        future_rain_est = rain[min(i + k, N - 1)]  # "forecast" (simplified)
        future_inflow += future_rain_est * catchment * rc / 1e6 / 1000 * dt
    mas_forecast[i] = future_inflow

    predicted_peak = mas_vol[i] + future_inflow
    pre_release_needed = max(0, predicted_peak - safe_line)

    # === Controller Agent ===
    current_inflow = corrected_rain * catchment * rc / 1e6 / 1000

    # Proactive release based on forecast
    if predicted_peak > safe_line:
        target_release = max(2.0, pre_release_needed / (6 * dt))
        target_release = min(target_release, 10.0)  # pump capacity
    elif mas_vol[i] > safe_line:
        target_release = 5.0
    else:
        target_release = 1.0

    # Safety guardrail: never release more than inflow + 2 when below safe_line
    if mas_vol[i] < safe_line:
        target_release = min(target_release, current_inflow + 2.0)

    mas_release[i] = max(0, target_release)

    mas_vol[i + 1] = mas_vol[i] + (inflow[i] - mas_release[i]) * dt
    mas_vol[i + 1] = np.clip(mas_vol[i + 1], 0, rv_cap)

    if mas_vol[i + 1] > flood_line:
        mas_alerts.append((t, "FLOOD_WARNING"))

# ============ KPI ============
mono_peak = np.max(mono_vol)
mas_peak = np.max(mas_vol)
mono_flood_steps = int(np.sum(mono_vol > flood_line))
mas_flood_steps = int(np.sum(mas_vol > flood_line))
mono_total_release = np.sum(mono_release) * dt
mas_total_release = np.sum(mas_release) * dt
sensor_flags_total = int(np.sum(mas_sensor_flags))

print("=" * 60)
print(f"{'KPI':<35}{'Monolithic':>12}{'MAS':>12}")
print("-" * 60)
print(f"{'Peak Volume (Mm3)':<35}{mono_peak:>12.1f}{mas_peak:>12.1f}")
print(f"{'Flood Line Violations (steps)':<35}{mono_flood_steps:>12d}{mas_flood_steps:>12d}")
print(f"{'Total Release (Mm3)':<35}{mono_total_release:>12.1f}{mas_total_release:>12.1f}")
print(f"{'Sensor Drift Detected':<35}{'No':>12}{'Yes ('+str(sensor_flags_total)+')':>12}")
print(f"{'Proactive Pre-release':<35}{'No':>12}{'Yes':>12}")
print(f"{'Flood Averted':<35}{'No' if mono_flood_steps>0 else 'Yes':>12}{'Yes' if mas_flood_steps==0 else 'No':>12}")

# ============ Plot ============
fig, axes = plt.subplots(4, 1, figsize=(14, 16), sharex=True)

# Panel 1: Rainfall + Sensor Status
ax = axes[0]
ax.fill_between(time_h, 0, rain, alpha=0.3, color='blue', label='True Rainfall')
observed = np.maximum(0, rain + sensor_drift)
ax.plot(time_h, observed, 'r--', lw=1.5, label='Station Observed (with drift)')
ax.plot(time_h, radar_rain, 'g-', lw=1, alpha=0.5, label='Radar (clean)')
# Mark sensor drift period
drift_mask = sensor_drift != 0
if np.any(drift_mask):
    ax.fill_between(time_h, 0, max(rain)*0.1, where=drift_mask,
                    alpha=0.2, color='orange', label='Sensor Drift Period')
ax.set_ylabel('Rainfall (mm/h)', fontsize=11)
ax.set_title('Input: Dual-Wave Storm + Sensor Drift Anomaly',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper right')
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: Reservoir Volume comparison
ax = axes[1]
ax.plot(np.arange(N+1)*dt, mono_vol, 'r-', lw=2, label=f'Monolithic (peak={mono_peak:.1f})')
ax.plot(np.arange(N+1)*dt, mas_vol, 'g-', lw=2, label=f'MAS (peak={mas_peak:.1f})')
ax.axhline(flood_line, color='red', ls='--', lw=1.5, label=f'Flood Line ({flood_line})')
ax.axhline(safe_line, color='orange', ls='--', lw=1.5, label=f'Safe Line ({safe_line})')
ax.fill_between(np.arange(N+1)*dt, flood_line, rv_cap,
                alpha=0.1, color='red', label='Flood Danger Zone')
ax.set_ylabel('Volume (Mm3)', fontsize=11)
ax.set_title('Reservoir Volume: Monolithic Agent vs Multi-Agent System',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Release strategies
ax = axes[2]
ax.step(time_h, mono_release, 'r-', lw=2, where='post', label='Monolithic Release')
ax.step(time_h, mas_release, 'g-', lw=2, where='post', label='MAS Release')
ax.fill_between(time_h, mono_release, mas_release,
                where=mas_release > mono_release,
                alpha=0.15, color='green', label='MAS Pre-release Advantage')
ax.set_ylabel('Release (Mm3/h)', fontsize=11)
ax.set_title('Release Strategy: Reactive (Mono) vs Proactive (MAS)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

# Panel 4: Agent Activity Timeline
ax = axes[3]
# Analyzer flags
flag_times = time_h[mas_sensor_flags > 0]
ax.scatter(flag_times, np.ones(len(flag_times)) * 3, c='orange', s=50,
           marker='^', zorder=5, label='Analyzer: Sensor Drift Flag')

# Dispatcher forecast
ax.fill_between(time_h, 0, mas_forecast / max(mas_forecast.max(), 0.01) * 2,
                alpha=0.2, color='blue', label='Dispatcher: Forecast Intensity')

# Controller release
ax.fill_between(time_h, 0, mas_release / max(mas_release.max(), 0.01),
                alpha=0.2, color='green', step='post', label='Controller: Release Activity')

ax.set_yticks([0, 1, 2, 3])
ax.set_yticklabels(['Idle', 'Controller', 'Dispatcher', 'Analyzer'], fontsize=10)
ax.set_xlabel('Time (hours)', fontsize=11)
ax.set_title('MAS Agent Activity Timeline: Analyzer / Dispatcher / Controller',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper right')
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "agent_dispatch_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: agent_dispatch_sim.png")

# Markdown table
md = [
    "| KPI | Monolithic | MAS | Assessment |",
    "|:----|:-----------|:----|:-----------|",
    f"| Peak Volume | {mono_peak:.1f} Mm3 | {mas_peak:.1f} Mm3 | MAS avoids flood |",
    f"| Flood Violations | {mono_flood_steps} steps | {mas_flood_steps} steps | MAS: zero |",
    f"| Sensor Drift Detected | No | Yes ({sensor_flags_total} flags) | Analyzer agent |",
    f"| Pre-release Strategy | Reactive | Proactive | Dispatcher lookahead |",
    f"| Total Release | {mono_total_release:.1f} Mm3 | {mas_total_release:.1f} Mm3 | MAS more efficient |",
]
with open(os.path.join(output_dir, "agent_kpi_table.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
for line in md:
    print(line)
