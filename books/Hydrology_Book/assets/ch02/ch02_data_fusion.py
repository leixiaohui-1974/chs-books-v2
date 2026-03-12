"""
Ch02: Multi-Source Data Fusion — Station vs Radar vs Satellite
Demonstrate why raw multi-source data is inconsistent and how
quality-controlled fusion produces reliable input for hydrological models.
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

# ============ Generate "True" Rainfall Field (60 min, 1-min resolution) ============
N = 360  # 6 hours, 1-min steps
time_min = np.arange(N)
time_h = time_min / 60.0

# True rainfall: storm with peak at t=2h
rain_true = np.zeros(N)
for i in range(N):
    t = time_h[i]
    if 1.0 <= t <= 4.0:
        rain_true[i] = 30 * np.sin(np.pi * (t - 1.0) / 3.0)
    rain_true[i] += np.random.normal(0, 0.5)  # micro-noise
rain_true = np.maximum(0, rain_true)

# ============ Three Data Sources (with realistic defects) ============

# Source A: Ground Station (high accuracy but sparse, 5-min aggregation)
station_interval = 5  # minutes
station_times = np.arange(0, N, station_interval)
station_rain = np.zeros(N)
for t in station_times:
    # Average over 5-min window
    window = rain_true[t:min(t + station_interval, N)]
    station_rain[t] = np.mean(window) if len(window) > 0 else 0
    # Add small calibration bias
    station_rain[t] *= np.random.uniform(0.95, 1.05)
# Inject sensor dropout: t=120-150 min (2.0-2.5h) — peak of storm!
for i in range(120, 150):
    if i in station_times:
        station_rain[i] = 0  # MISSING during peak!

# Quality flags for station
station_qflag = np.array(['GOOD'] * N, dtype=object)
for i in range(120, 150):
    station_qflag[i] = 'MISSING'

# Source B: Radar (spatial coverage, 10-min, systematic overestimate in heavy rain)
radar_interval = 10
radar_times = np.arange(0, N, radar_interval)
radar_rain = np.zeros(N)
for t in radar_times:
    window = rain_true[t:min(t + radar_interval, N)]
    base = np.mean(window) if len(window) > 0 else 0
    # Radar overestimates heavy rain by 15-25%
    if base > 15:
        radar_rain[t] = base * np.random.uniform(1.15, 1.25)
    else:
        radar_rain[t] = base * np.random.uniform(0.90, 1.10)

# Source C: Satellite (wide coverage, 30-min, significant underestimate + delay)
sat_interval = 30
sat_times = np.arange(0, N, sat_interval)
sat_rain = np.zeros(N)
for t in sat_times:
    # Satellite has 15-min processing delay
    t_delayed = max(0, t - 15)
    window = rain_true[t_delayed:min(t_delayed + sat_interval, N)]
    base = np.mean(window) if len(window) > 0 else 0
    # Systematic underestimate 20-30%
    sat_rain[t] = base * np.random.uniform(0.70, 0.80)

# ============ Fusion Algorithm ============
fused_rain = np.zeros(N)
fused_qflag = np.array(['FUSED'] * N, dtype=object)
fusion_weights = np.zeros((N, 3))  # station, radar, satellite

for i in range(N):
    sources = []
    weights = []

    # Station: high weight if GOOD, zero if MISSING
    s_val = station_rain[i] if i in station_times else np.nan
    if station_qflag[i] == 'GOOD' and not np.isnan(s_val) and s_val > 0:
        sources.append(s_val)
        weights.append(3.0)  # highest trust
    else:
        sources.append(0)
        weights.append(0)

    # Radar: medium weight, apply bias correction for heavy rain
    r_val = radar_rain[i] if i in radar_times else np.nan
    if not np.isnan(r_val) and r_val > 0:
        # Bias correction: reduce by 15% if > 15 mm/h
        if r_val > 15:
            r_val *= 0.85
        sources.append(r_val)
        weights.append(2.0)
    else:
        sources.append(0)
        weights.append(0)

    # Satellite: low weight
    sv_val = sat_rain[i] if i in sat_times else np.nan
    if not np.isnan(sv_val) and sv_val > 0:
        sources.append(sv_val)
        weights.append(1.0)
    else:
        sources.append(0)
        weights.append(0)

    total_w = sum(weights)
    if total_w > 0:
        fused_rain[i] = sum(s * w for s, w in zip(sources, weights)) / total_w
        fusion_weights[i] = [w / total_w for w in weights]
    else:
        fused_rain[i] = 0
        fused_qflag[i] = 'NO_DATA'

    # Flag fused quality
    if weights[0] == 0 and weights[1] > 0:
        fused_qflag[i] = 'RADAR_ONLY'
    elif total_w == 0:
        fused_qflag[i] = 'NO_DATA'

# ============ Error Metrics ============
# Compare each source and fusion against truth (at their respective times)
def rmse_at_times(estimate, truth, times):
    errors = []
    for t in times:
        if t < len(truth) and estimate[t] > 0:
            errors.append((estimate[t] - truth[t]) ** 2)
    return np.sqrt(np.mean(errors)) if errors else 0

# For fair comparison, evaluate all at 10-min intervals
eval_times = radar_times
station_at_eval = np.array([station_rain[t] if station_qflag[t] == 'GOOD' else np.nan
                            for t in eval_times])
radar_at_eval = np.array([radar_rain[t] for t in eval_times])
sat_at_eval = np.array([sat_rain[t] if t in sat_times else np.nan for t in eval_times])
fused_at_eval = np.array([fused_rain[t] for t in eval_times])
true_at_eval = np.array([np.mean(rain_true[t:min(t+10, N)]) for t in eval_times])

# RMSE (excluding NaN)
def rmse(est, truth):
    mask = ~np.isnan(est) & (est > 0)
    if np.sum(mask) == 0:
        return np.nan
    return np.sqrt(np.mean((est[mask] - truth[mask]) ** 2))

rmse_station = rmse(station_at_eval, true_at_eval)
rmse_radar = rmse(radar_at_eval, true_at_eval)
rmse_sat = rmse(sat_at_eval, true_at_eval)
rmse_fused = rmse(fused_at_eval, true_at_eval)

# Peak capture
peak_true = np.max(true_at_eval)
peak_station = np.nanmax(station_at_eval)
peak_radar = np.max(radar_at_eval)
peak_fused = np.max(fused_at_eval)

print("=" * 60)
print(f"{'Source':<20}{'RMSE (mm/h)':>15}{'Peak (mm/h)':>15}{'Coverage':>12}")
print("-" * 60)
print(f"{'Ground Truth':<20}{'-':>15}{peak_true:>15.1f}{'100%':>12}")
print(f"{'Station':<20}{rmse_station:>15.2f}{peak_station:>15.1f}{'83% (gap)':>12}")
print(f"{'Radar':<20}{rmse_radar:>15.2f}{peak_radar:>15.1f}{'100%':>12}")
print(f"{'Satellite':<20}{rmse_sat:>15.2f}{np.nanmax(sat_at_eval):>15.1f}{'100% (delay)':>12}")
print(f"{'Fused':<20}{rmse_fused:>15.2f}{peak_fused:>15.1f}{'100%':>12}")
print(f"\nFusion RMSE improvement vs best single source: "
      f"{(1 - rmse_fused/min(rmse_station, rmse_radar))*100:.0f}%")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Panel 1: Raw sources vs truth
ax = axes[0]
ax.fill_between(time_h, 0, rain_true, alpha=0.15, color='black', label='True Rainfall')
ax.scatter(time_h[station_times], station_rain[station_times], c='green', s=25,
           marker='o', zorder=5, label='Station (5-min, gaps)')
ax.scatter(time_h[radar_times], radar_rain[radar_times], c='blue', s=25,
           marker='s', zorder=5, label='Radar (10-min, overestimate)')
ax.scatter(time_h[sat_times], sat_rain[sat_times], c='orange', s=25,
           marker='^', zorder=5, label='Satellite (30-min, underestimate)')
# Mark missing period
ax.axvspan(2.0, 2.5, alpha=0.2, color='red', label='Station Dropout!')
ax.set_ylabel('Rainfall (mm/h)', fontsize=11)
ax.set_title('Raw Multi-Source Data: Inconsistent, Gappy, Biased',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, ncol=2, loc='upper right')
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: Fused result vs truth
ax = axes[1]
ax.fill_between(time_h, 0, rain_true, alpha=0.15, color='black', label='True Rainfall')
ax.plot(time_h, fused_rain, 'r-', lw=2, label=f'Quality-Controlled Fusion (RMSE={rmse_fused:.2f})')
# Color-code quality flags
for i in range(N):
    if fused_qflag[i] == 'RADAR_ONLY':
        ax.axvspan(time_h[i], time_h[min(i+1, N-1)], alpha=0.1, color='blue')
    elif fused_qflag[i] == 'NO_DATA':
        ax.axvspan(time_h[i], time_h[min(i+1, N-1)], alpha=0.3, color='red')
ax.set_ylabel('Rainfall (mm/h)', fontsize=11)
ax.set_title('After Fusion: Continuous, Bias-Corrected, Quality-Flagged',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Error comparison
ax = axes[2]
sources = ['Station', 'Radar', 'Satellite', 'Fused']
rmses = [rmse_station, rmse_radar, rmse_sat if not np.isnan(rmse_sat) else 0, rmse_fused]
colors = ['green', 'blue', 'orange', 'red']
bars = ax.bar(sources, rmses, color=colors, alpha=0.7, edgecolor='black')
for bar, val in zip(bars, rmses):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.2, f'{val:.2f}',
            ha='center', fontsize=11, fontweight='bold')
ax.set_ylabel('RMSE (mm/h)', fontsize=11)
ax.set_title('Error Comparison: Single Source vs Quality-Controlled Fusion',
             fontsize=13, fontweight='bold')
ax.grid(True, ls='--', alpha=0.4, axis='y')

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "data_fusion_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: data_fusion_sim.png")
