"""
Ch02: Multi-Energy Conversion Device Modeling
Compare CHP, gas boiler, heat pump, and absorption chiller
performance curves under varying load conditions.
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

# ============ Load Range ============
load_frac = np.linspace(0.1, 1.0, 50)  # 10% to 100% load

# ============ CHP (Gas Turbine + Waste Heat Recovery) ============
# At full load: eta_e = 0.35, eta_h = 0.45, total = 0.80
# Part-load efficiency drops (quadratic fit from manufacturer data)
eta_chp_e_full = 0.35
eta_chp_h_full = 0.45
# Electrical efficiency degrades at part load
eta_chp_e = eta_chp_e_full * (0.5 + 0.5 * load_frac)  # linear degradation
# Thermal efficiency relatively stable
eta_chp_h = eta_chp_h_full * (0.85 + 0.15 * load_frac)
eta_chp_total = eta_chp_e + eta_chp_h

# ============ Gas Boiler ============
# High efficiency across load range, slight dip at very low loads
eta_boiler = 0.92 * (0.9 + 0.1 * load_frac)

# ============ Electric Heat Pump ============
# COP varies with outdoor temperature; here simulate COP vs load fraction
# At design conditions: COP = 3.5, degrades at part load due to cycling
cop_hp = 3.5 * (0.7 + 0.3 * load_frac)

# ============ Absorption Chiller (Single-effect LiBr) ============
# Driven by waste heat from CHP. COP ~ 0.7 at full load
cop_abs = 0.70 * (0.6 + 0.4 * load_frac)

# ============ Electric Chiller (Vapor Compression) ============
# COP ~ 5.0 at full load
cop_elec_chiller = 5.0 * (0.75 + 0.25 * load_frac)

# ============ KPI Table at Key Operating Points ============
key_points = [0.25, 0.50, 0.75, 1.00]
print("=" * 75)
print(f"{'Load%':<8}{'CHP_e':>8}{'CHP_h':>8}{'CHP_tot':>8}{'Boiler':>8}"
      f"{'HP_COP':>8}{'Abs_COP':>8}{'EC_COP':>8}")
print("-" * 75)
for lf in key_points:
    idx = np.argmin(np.abs(load_frac - lf))
    print(f"{lf*100:>5.0f}%  "
          f"{eta_chp_e[idx]:>8.3f}{eta_chp_h[idx]:>8.3f}{eta_chp_total[idx]:>8.3f}"
          f"{eta_boiler[idx]:>8.3f}{cop_hp[idx]:>8.2f}{cop_abs[idx]:>8.3f}"
          f"{cop_elec_chiller[idx]:>8.2f}")
print("=" * 75)

# Save table
with open(os.path.join(output_dir, "device_table.md"), "w", encoding="utf-8") as f:
    f.write("| Load (%) | CHP Elec Eff | CHP Heat Eff | CHP Total Eff | Boiler Eff | HP COP | Abs Chiller COP | Elec Chiller COP |\n")
    f.write("|:---------|:-------------|:-------------|:--------------|:-----------|:-------|:----------------|:-----------------|\n")
    for lf in key_points:
        idx = np.argmin(np.abs(load_frac - lf))
        f.write(f"| {lf*100:.0f} | {eta_chp_e[idx]:.3f} | {eta_chp_h[idx]:.3f} | "
                f"{eta_chp_total[idx]:.3f} | {eta_boiler[idx]:.3f} | {cop_hp[idx]:.2f} | "
                f"{cop_abs[idx]:.3f} | {cop_elec_chiller[idx]:.2f} |\n")

# ============ Plot ============
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# CHP efficiency curves
ax = axes[0, 0]
ax.plot(load_frac * 100, eta_chp_e * 100, 'b-', lw=2, label='Electrical Eff')
ax.plot(load_frac * 100, eta_chp_h * 100, 'r-', lw=2, label='Thermal Eff')
ax.plot(load_frac * 100, eta_chp_total * 100, 'k--', lw=2, label='Total Eff')
ax.set_xlabel('Load (%)')
ax.set_ylabel('Efficiency (%)')
ax.set_title('CHP Part-Load Efficiency', fontweight='bold')
ax.legend()
ax.grid(True, ls='--', alpha=0.4)
ax.set_ylim(0, 100)

# Gas boiler
ax = axes[0, 1]
ax.plot(load_frac * 100, eta_boiler * 100, 'orange', lw=2)
ax.set_xlabel('Load (%)')
ax.set_ylabel('Efficiency (%)')
ax.set_title('Gas Boiler Part-Load Efficiency', fontweight='bold')
ax.grid(True, ls='--', alpha=0.4)
ax.set_ylim(70, 100)

# Heat pump COP
ax = axes[1, 0]
ax.plot(load_frac * 100, cop_hp, 'green', lw=2)
ax.set_xlabel('Load (%)')
ax.set_ylabel('COP')
ax.set_title('Heat Pump COP vs Load', fontweight='bold')
ax.grid(True, ls='--', alpha=0.4)

# Chillers comparison
ax = axes[1, 1]
ax.plot(load_frac * 100, cop_abs, 'purple', lw=2, label='Absorption (LiBr)')
ax.plot(load_frac * 100, cop_elec_chiller, 'cyan', lw=2, label='Electric (Vapor Comp.)')
ax.set_xlabel('Load (%)')
ax.set_ylabel('COP')
ax.set_title('Chiller COP Comparison', fontweight='bold')
ax.legend()
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "device_models_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: device_models_sim.png")
