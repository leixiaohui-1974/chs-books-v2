"""
Ch06: IES Simulation Platform — Four-Season Energy Flow Test
Object-oriented IES component library + seasonal dispatch comparison.
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

# ============ IES Component Classes ============
class CHP:
    def __init__(self, P_max_gas=3.0, eta_e=0.35, eta_h=0.45):
        self.P_max_gas = P_max_gas  # MW gas input
        self.eta_e = eta_e
        self.eta_h = eta_h

    def operate(self, gas_input):
        gas = min(gas_input, self.P_max_gas)
        return gas * self.eta_e, gas * self.eta_h, gas  # elec, heat, gas_used

class HeatPump:
    def __init__(self, P_max_elec=1.0, cop=3.5):
        self.P_max_elec = P_max_elec
        self.cop = cop

    def operate(self, elec_input):
        elec = min(elec_input, self.P_max_elec)
        return elec * self.cop, elec  # heat, elec_used

class ElecChiller:
    def __init__(self, P_max_elec=1.0, cop=5.0):
        self.P_max_elec = P_max_elec
        self.cop = cop

    def operate(self, elec_input):
        elec = min(elec_input, self.P_max_elec)
        return elec * self.cop, elec  # cooling, elec_used

class GasBoiler:
    def __init__(self, P_max_gas=2.0, eta=0.90):
        self.P_max_gas = P_max_gas
        self.eta = eta

    def operate(self, gas_input):
        gas = min(gas_input, self.P_max_gas)
        return gas * self.eta, gas  # heat, gas_used

class Battery:
    def __init__(self, E_cap=2000, P_max=500, eta=0.95):
        self.E_cap = E_cap  # kWh
        self.P_max = P_max  # kW
        self.eta = eta
        self.soc = 0.5

    def charge(self, power_kw, dt=1.0):
        p = min(power_kw, self.P_max)
        delta = p * self.eta * dt / self.E_cap
        self.soc = min(self.soc + delta, 0.9)
        return p

    def discharge(self, power_kw, dt=1.0):
        p = min(power_kw, self.P_max)
        delta = p / self.eta * dt / self.E_cap
        if self.soc - delta < 0.1:
            p = (self.soc - 0.1) * self.E_cap * self.eta / dt
            delta = (self.soc - 0.1)
        self.soc -= delta
        return p

# ============ Seasonal Load Profiles (24h, MW) ============
T = 24
time_h = np.arange(T)

seasons = {
    'Winter': {
        'elec': np.array([2.0, 1.8, 1.5, 1.5, 1.8, 2.5, 3.5, 4.5, 5.0, 5.0,
                          4.8, 4.5, 4.2, 4.5, 5.0, 5.2, 5.0, 5.5, 5.5, 5.0,
                          4.0, 3.5, 3.0, 2.5]),
        'heat': np.array([5.0, 5.0, 4.5, 4.5, 4.5, 5.0, 6.0, 7.0, 6.5, 5.5,
                          5.0, 4.5, 4.5, 4.5, 5.0, 5.5, 6.0, 7.0, 7.5, 7.0,
                          6.5, 6.0, 5.5, 5.0]),
        'cool': np.zeros(T),
    },
    'Summer': {
        'elec': np.array([2.5, 2.2, 2.0, 2.0, 2.2, 3.0, 4.0, 5.0, 5.5, 6.0,
                          6.5, 6.5, 6.0, 6.0, 6.5, 7.0, 7.0, 6.5, 6.0, 5.5,
                          4.5, 3.5, 3.0, 2.5]),
        'heat': np.array([1.0, 1.0, 0.8, 0.8, 0.8, 1.0, 1.5, 2.0, 1.5, 1.2,
                          1.0, 0.8, 0.8, 0.8, 1.0, 1.2, 1.5, 2.0, 2.0, 1.5,
                          1.2, 1.0, 1.0, 1.0]),
        'cool': np.array([0, 0, 0, 0, 0, 0.5, 1.5, 3.0, 4.0, 5.0,
                          5.5, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5,
                          1.0, 0.5, 0, 0]),
    },
    'Spring': {
        'elec': np.array([1.8, 1.5, 1.3, 1.3, 1.5, 2.0, 3.0, 4.0, 4.5, 4.5,
                          4.3, 4.0, 3.8, 4.0, 4.5, 4.5, 4.3, 4.5, 4.5, 4.0,
                          3.5, 3.0, 2.5, 2.0]),
        'heat': np.array([3.0, 3.0, 2.5, 2.5, 2.5, 3.0, 3.5, 4.0, 3.5, 3.0,
                          2.5, 2.0, 2.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0, 3.5,
                          3.0, 3.0, 3.0, 3.0]),
        'cool': np.array([0, 0, 0, 0, 0, 0, 0.3, 0.8, 1.2, 1.5,
                          1.5, 1.2, 1.0, 0.8, 0.5, 0.3, 0, 0, 0, 0,
                          0, 0, 0, 0]),
    },
    'Autumn': {
        'elec': np.array([1.8, 1.5, 1.3, 1.3, 1.5, 2.0, 3.0, 4.0, 4.5, 4.8,
                          4.5, 4.2, 4.0, 4.2, 4.5, 4.8, 4.5, 4.8, 4.5, 4.0,
                          3.5, 3.0, 2.5, 2.0]),
        'heat': np.array([3.5, 3.5, 3.0, 3.0, 3.0, 3.5, 4.5, 5.0, 4.5, 4.0,
                          3.5, 3.0, 3.0, 3.0, 3.5, 4.0, 4.5, 5.5, 5.5, 5.0,
                          4.5, 4.0, 3.5, 3.5]),
        'cool': np.zeros(T),
    }
}

# Gas price
price_gas = 0.35  # CNY/kWh_gas
price_elec = np.where((time_h >= 8) & (time_h <= 20), 0.8, 0.4)

# ============ Run Seasonal Dispatch ============
results = {}

for season_name, loads in seasons.items():
    chp = CHP()
    hp = HeatPump()
    chiller = ElecChiller()
    boiler = GasBoiler()
    batt = Battery()

    total_cost = 0
    total_gas = 0
    total_grid = 0
    elec_from_grid = np.zeros(T)

    for i in range(T):
        E_dem = loads['elec'][i]  # MW
        H_dem = loads['heat'][i]
        C_dem = loads['cool'][i]

        # Strategy: CHP for base heat+electricity, HP for extra heat,
        # chiller for cooling, boiler as backup, grid for remaining electricity

        # CHP: cover heat demand first
        chp_gas_need = min(H_dem / chp.eta_h, chp.P_max_gas)
        chp_e, chp_h, chp_gas = chp.operate(chp_gas_need)
        h_remaining = H_dem - chp_h

        # Heat pump for remaining heat (off-peak hours)
        hp_heat = 0
        hp_elec = 0
        if h_remaining > 0 and price_elec[i] <= 0.5:
            hp_heat, hp_elec = hp.operate(h_remaining / hp.cop)
            h_remaining -= hp_heat

        # Boiler for residual heat
        boiler_heat = 0
        boiler_gas = 0
        if h_remaining > 0:
            boiler_heat, boiler_gas = boiler.operate(h_remaining / boiler.eta)

        # Electric chiller for cooling
        chiller_cool = 0
        chiller_elec = 0
        if C_dem > 0:
            chiller_cool, chiller_elec = chiller.operate(C_dem / chiller.cop)

        # Net electricity demand
        e_net = E_dem - chp_e + hp_elec + chiller_elec
        e_from_grid = max(e_net, 0)
        elec_from_grid[i] = e_from_grid

        # Cost
        gas_cost = (chp_gas + boiler_gas) * 1000 * price_gas
        elec_cost = e_from_grid * 1000 * price_elec[i]
        total_cost += gas_cost + elec_cost
        total_gas += chp_gas + boiler_gas
        total_grid += e_from_grid

    results[season_name] = {
        'total_cost': total_cost,
        'total_gas': total_gas,
        'total_grid': total_grid,
        'elec_from_grid': elec_from_grid,
        'elec_demand': loads['elec'],
        'heat_demand': loads['heat'],
        'cool_demand': loads['cool'],
    }

# ============ KPI ============
print("=" * 70)
print(f"{'Season':<12}{'Total Cost':>12}{'Gas Used':>12}{'Grid Elec':>12}"
      f"{'Heat Load':>12}{'Cool Load':>12}")
print(f"{'':12}{'(CNY)':>12}{'(MWh)':>12}{'(MWh)':>12}"
      f"{'(MWh)':>12}{'(MWh)':>12}")
print("-" * 70)
for s in ['Winter', 'Spring', 'Summer', 'Autumn']:
    r = results[s]
    print(f"{s:<12}{r['total_cost']:>12.0f}{r['total_gas']:>12.1f}"
          f"{r['total_grid']:>12.1f}"
          f"{np.sum(seasons[s]['heat']):>12.1f}"
          f"{np.sum(seasons[s]['cool']):>12.1f}")
print("=" * 70)

with open(os.path.join(output_dir, "seasonal_table.md"), "w", encoding="utf-8") as f:
    f.write("| Season | Total Cost (CNY) | Gas (MWh) | Grid Elec (MWh) | Heat Load (MWh) | Cool Load (MWh) |\n")
    f.write("|:-------|:-----------------|:----------|:----------------|:----------------|:----------------|\n")
    for s in ['Winter', 'Spring', 'Summer', 'Autumn']:
        r = results[s]
        f.write(f"| {s} | {r['total_cost']:.0f} | {r['total_gas']:.1f} | "
                f"{r['total_grid']:.1f} | {np.sum(seasons[s]['heat']):.1f} | "
                f"{np.sum(seasons[s]['cool']):.1f} |\n")

# ============ Plot ============
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
season_list = ['Winter', 'Spring', 'Summer', 'Autumn']
colors = {'elec': 'blue', 'heat': 'red', 'cool': 'cyan'}

for idx, (s, ax) in enumerate(zip(season_list, axes.flat)):
    ax.fill_between(time_h, 0, seasons[s]['elec'], alpha=0.3, color='blue', label='Elec Demand')
    ax.fill_between(time_h, 0, seasons[s]['heat'], alpha=0.3, color='red', label='Heat Demand')
    if np.any(seasons[s]['cool'] > 0):
        ax.fill_between(time_h, 0, seasons[s]['cool'], alpha=0.3, color='cyan', label='Cool Demand')
    ax.plot(time_h, results[s]['elec_from_grid'], 'b--', lw=2, label='Grid Purchase')
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('Power (MW)')
    r = results[s]
    ax.set_title(f'{s}: Cost={r["total_cost"]:.0f} CNY', fontweight='bold')
    ax.legend(fontsize=7)
    ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "ies_platform_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: ies_platform_sim.png")
