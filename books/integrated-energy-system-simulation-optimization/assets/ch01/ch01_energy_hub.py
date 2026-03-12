"""
Ch01: What is IES? — Energy Hub Concept Demonstration
Show how an Energy Hub couples electricity, heat, and gas through
conversion devices (CHP, heat pump, gas boiler), and why coupling
improves overall efficiency vs isolated operation.
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

# ============ 24h Load Profiles ============
T = 24
dt = 1.0  # hourly
N = int(T / dt)
time_h = np.arange(N)

# Electricity demand (MW)
P_elec = np.array([2.0, 1.8, 1.5, 1.5, 1.8, 2.5, 3.5, 4.5, 5.0, 5.5,
                   5.5, 5.0, 4.5, 5.0, 5.5, 5.5, 5.0, 5.5, 6.0, 5.5,
                   4.5, 3.5, 3.0, 2.5])
# Heat demand (MW thermal)
Q_heat = np.array([3.0, 3.0, 2.5, 2.5, 2.5, 3.0, 4.0, 5.0, 4.5, 3.5,
                   3.0, 2.5, 2.5, 2.5, 3.0, 3.5, 4.0, 5.0, 5.5, 5.0,
                   4.5, 4.0, 3.5, 3.0])

# ============ Device Parameters ============
# CHP: gas -> electricity + heat
eta_chp_e = 0.35   # electrical efficiency
eta_chp_h = 0.45   # thermal efficiency (waste heat recovery)
eta_chp_total = eta_chp_e + eta_chp_h  # 80%

# Gas boiler: gas -> heat
eta_boiler = 0.90

# Heat pump: electricity -> heat (COP=3.5)
cop_hp = 3.5

# Grid electricity price (CNY/kWh)
price_elec = np.where((time_h >= 8) & (time_h <= 20), 0.8, 0.4)
# Gas price (CNY/kWh_gas)
price_gas = 0.35  # CNY per kWh gas equivalent

# ============ Scenario A: Isolated Operation (no coupling) ============
# Electricity from grid only, heat from gas boiler only
gas_isolated = np.zeros(N)
cost_isolated = np.zeros(N)
primary_energy_isolated = np.zeros(N)

for i in range(N):
    # All electricity from grid
    elec_cost = P_elec[i] * 1000 * price_elec[i]  # kWh * price
    # All heat from gas boiler
    gas_for_heat = Q_heat[i] / eta_boiler  # MW_gas
    heat_cost = gas_for_heat * 1000 * price_gas

    cost_isolated[i] = elec_cost + heat_cost
    gas_isolated[i] = gas_for_heat
    primary_energy_isolated[i] = P_elec[i] + gas_for_heat  # total primary energy

# ============ Scenario B: Energy Hub (CHP + Heat Pump + Boiler) ============
gas_hub = np.zeros(N)
cost_hub = np.zeros(N)
primary_energy_hub = np.zeros(N)
chp_elec = np.zeros(N)
chp_heat = np.zeros(N)
hp_heat = np.zeros(N)
boiler_heat = np.zeros(N)
grid_elec = np.zeros(N)

for i in range(N):
    # Strategy: CHP covers base heat, heat pump covers peak, boiler as backup
    # CHP sizing: max 3 MW gas input
    chp_gas_max = 3.0  # MW gas

    # Determine CHP operation based on heat demand
    heat_from_chp_needed = min(Q_heat[i], chp_gas_max * eta_chp_h)
    chp_gas = heat_from_chp_needed / eta_chp_h
    chp_elec[i] = chp_gas * eta_chp_e
    chp_heat[i] = heat_from_chp_needed

    # Remaining heat demand
    heat_remaining = Q_heat[i] - chp_heat[i]

    # Use heat pump for remaining (if electricity is cheap)
    if price_elec[i] <= 0.5 and heat_remaining > 0:
        hp_elec_needed = min(heat_remaining / cop_hp, 1.0)  # max 1 MW elec
        hp_heat[i] = hp_elec_needed * cop_hp
        heat_remaining -= hp_heat[i]

    # Boiler for any residual
    if heat_remaining > 0:
        boiler_heat[i] = heat_remaining
        boiler_gas = heat_remaining / eta_boiler
    else:
        boiler_gas = 0

    # Grid electricity = demand - CHP generation + heat pump consumption
    grid_elec[i] = P_elec[i] - chp_elec[i] + (hp_heat[i] / cop_hp if hp_heat[i] > 0 else 0)
    grid_elec[i] = max(grid_elec[i], 0)

    # Costs
    elec_cost = grid_elec[i] * 1000 * price_elec[i]
    gas_cost = (chp_gas + boiler_gas) * 1000 * price_gas
    cost_hub[i] = elec_cost + gas_cost
    gas_hub[i] = chp_gas + boiler_gas
    primary_energy_hub[i] = grid_elec[i] + chp_gas + boiler_gas

# ============ KPI ============
total_cost_iso = np.sum(cost_isolated)
total_cost_hub = np.sum(cost_hub)
total_pe_iso = np.sum(primary_energy_isolated)
total_pe_hub = np.sum(primary_energy_hub)
cost_saving = (1 - total_cost_hub / total_cost_iso) * 100
pe_saving = (1 - total_pe_hub / total_pe_iso) * 100

print("=" * 60)
print(f"{'Metric':<35}{'Isolated':>12}{'Energy Hub':>12}")
print("-" * 60)
print(f"{'Daily Cost (CNY)':<35}{total_cost_iso:>12.0f}{total_cost_hub:>12.0f}")
print(f"{'Primary Energy (MWh)':<35}{total_pe_iso:>12.1f}{total_pe_hub:>12.1f}")
print(f"{'Cost Saving (%)':<35}{'-':>12}{cost_saving:>12.1f}")
print(f"{'Primary Energy Saving (%)':<35}{'-':>12}{pe_saving:>12.1f}")
print(f"{'CHP Electricity Generated (MWh)':<35}{'-':>12}{np.sum(chp_elec):>12.1f}")
print(f"{'Grid Electricity Purchased (MWh)':<35}{np.sum(P_elec):>12.1f}{np.sum(grid_elec):>12.1f}")
print("=" * 60)

with open(os.path.join(output_dir, "hub_table.md"), "w", encoding="utf-8") as f:
    f.write("| Metric | Isolated | Energy Hub |\n")
    f.write("|:-------|:---------|:-----------|\n")
    f.write(f"| Daily Cost (CNY) | {total_cost_iso:.0f} | {total_cost_hub:.0f} |\n")
    f.write(f"| Primary Energy (MWh) | {total_pe_iso:.1f} | {total_pe_hub:.1f} |\n")
    f.write(f"| Cost Saving (%) | - | {cost_saving:.1f} |\n")
    f.write(f"| Primary Energy Saving (%) | - | {pe_saving:.1f} |\n")
    f.write(f"| CHP Elec Generated (MWh) | - | {np.sum(chp_elec):.1f} |\n")
    f.write(f"| Grid Elec Purchased (MWh) | {np.sum(P_elec):.1f} | {np.sum(grid_elec):.1f} |\n")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Panel 1: Load profiles
ax = axes[0]
ax.plot(time_h, P_elec, 'b-o', lw=2, ms=4, label='Electricity Demand (MW)')
ax.plot(time_h, Q_heat, 'r-s', lw=2, ms=4, label='Heat Demand (MW_th)')
ax.set_ylabel('Demand (MW)', fontsize=11)
ax.set_title('24h Energy Demand: Electricity and Heat',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: Energy Hub supply breakdown
ax = axes[1]
ax.bar(time_h, grid_elec, width=0.8, label='Grid Purchase', color='blue', alpha=0.7)
ax.bar(time_h, chp_elec, width=0.8, bottom=grid_elec, label='CHP Electricity',
       color='green', alpha=0.7)
ax.bar(time_h, -chp_heat, width=0.4, label='CHP Heat', color='orange', alpha=0.7)
ax.bar(time_h, -(chp_heat + hp_heat), width=0.4, label='Heat Pump', color='red', alpha=0.5)
ax.axhline(0, color='black', lw=0.5)
ax.set_ylabel('Power (MW)', fontsize=11)
ax.set_title('Energy Hub: Multi-Source Supply Breakdown',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, ncol=2)
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Cost comparison
ax = axes[2]
ax.bar(time_h - 0.2, cost_isolated / 1000, width=0.4, label=f'Isolated (Total={total_cost_iso:.0f})',
       color='red', alpha=0.7)
ax.bar(time_h + 0.2, cost_hub / 1000, width=0.4, label=f'Energy Hub (Total={total_cost_hub:.0f})',
       color='blue', alpha=0.7)
ax.set_ylabel('Hourly Cost (k CNY)', fontsize=11)
ax.set_xlabel('Time (h)', fontsize=11)
ax.set_title(f'Cost Comparison: Isolated vs Energy Hub (Saving {cost_saving:.1f}%)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "energy_hub_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: energy_hub_sim.png")
