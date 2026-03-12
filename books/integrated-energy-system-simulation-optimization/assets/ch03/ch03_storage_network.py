"""
Ch03: Energy Storage & District Heating Network Dynamics
Simulate battery SOC dynamics + heating network thermal delay/loss.
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

# ============ Part 1: Battery Storage State-Space Model ============
# State: SOC; Input: P_charge/P_discharge; Parameters: capacity, efficiency
E_cap = 2000  # kWh
eta_ch = 0.95   # charging efficiency
eta_dis = 0.95  # discharging efficiency
P_max = 500     # kW max charge/discharge
dt = 1.0        # hour

T = 24
time_h = np.arange(T)

# TOU price
price = np.where((time_h >= 8) & (time_h <= 20), 0.8, 0.4)  # CNY/kWh

# Optimal strategy: charge at night (low price), discharge at peak
P_batt = np.zeros(T)
for i in range(T):
    if price[i] <= 0.4:
        P_batt[i] = P_max   # charge
    elif price[i] >= 0.8 and i >= 10:
        P_batt[i] = -P_max  # discharge

# Simulate SOC
soc = np.zeros(T + 1)
soc[0] = 0.5  # initial 50%
for i in range(T):
    if P_batt[i] > 0:  # charging
        delta_soc = P_batt[i] * eta_ch * dt / E_cap
    else:  # discharging
        delta_soc = P_batt[i] / eta_dis * dt / E_cap
    soc[i + 1] = np.clip(soc[i] + delta_soc, 0.1, 0.9)
    # Clip power if SOC hits limits
    if soc[i + 1] == 0.9 and P_batt[i] > 0:
        P_batt[i] = (0.9 - soc[i]) * E_cap / (eta_ch * dt)
        soc[i + 1] = 0.9
    elif soc[i + 1] == 0.1 and P_batt[i] < 0:
        P_batt[i] = (0.1 - soc[i]) * E_cap * eta_dis / dt
        soc[i + 1] = 0.1

# Cost comparison
cost_no_storage = np.zeros(T)
cost_with_storage = np.zeros(T)
base_load = np.array([400, 350, 300, 280, 300, 400, 600, 750, 850, 900,
                       900, 850, 800, 850, 900, 900, 850, 800, 750, 700,
                       600, 550, 500, 450])  # kW

for i in range(T):
    cost_no_storage[i] = base_load[i] * price[i]
    net_load = base_load[i] + P_batt[i]  # positive = more from grid
    cost_with_storage[i] = max(net_load, 0) * price[i]

# ============ Part 2: District Heating Network Thermal Dynamics ============
# Pipe: L=2000m, D=0.5m, insulation loss coefficient
pipe_length = 2000  # m
pipe_diameter = 0.5  # m
flow_velocity = 1.5  # m/s
transport_delay = pipe_length / flow_velocity  # seconds
rho = 1000  # kg/m^3
cp = 4186   # J/(kg·K)
mass_flow = rho * np.pi * (pipe_diameter/2)**2 * flow_velocity  # kg/s

# Heat loss coefficient (W/(m·K))
U_loss = 0.5  # W per meter per K temperature difference
T_ground = 5  # ground temperature in winter

# Supply temperature step response
dt_s = 10  # seconds
t_sim = np.arange(0, 3600, dt_s)  # 1 hour simulation
N_sim = len(t_sim)

T_supply_in = np.where(t_sim >= 300, 90, 75)  # step from 75 to 90 deg at t=300s
T_supply_out = np.zeros(N_sim)
T_supply_out[0] = 75

# Simple plug-flow model with thermal loss
delay_steps = int(transport_delay / dt_s)
for i in range(1, N_sim):
    if i >= delay_steps:
        T_in_delayed = T_supply_in[i - delay_steps]
    else:
        T_in_delayed = T_supply_in[0]
    # Temperature drop due to pipe heat loss
    T_drop = U_loss * pipe_length * (T_in_delayed - T_ground) / (mass_flow * cp)
    T_supply_out[i] = T_in_delayed - T_drop

# ============ KPI ============
total_no_storage = np.sum(cost_no_storage)
total_with_storage = np.sum(cost_with_storage)
saving = (1 - total_with_storage / total_no_storage) * 100
peak_no = np.max(base_load)
peak_with = np.max(base_load + P_batt)
T_drop_final = 90 - T_supply_out[-1]

print("=" * 60)
print("Part 1: Battery Storage Economic Performance")
print("-" * 60)
print(f"  Daily cost without storage: {total_no_storage:.0f} CNY")
print(f"  Daily cost with storage:    {total_with_storage:.0f} CNY")
print(f"  Cost saving:                {saving:.1f}%")
print(f"  Peak demand (no storage):   {peak_no:.0f} kW")
print(f"  Peak demand (with storage): {peak_with:.0f} kW")
print()
print("Part 2: Heating Network Dynamics")
print("-" * 60)
print(f"  Pipe length:          {pipe_length} m")
print(f"  Transport delay:      {transport_delay:.0f} s ({transport_delay/60:.1f} min)")
print(f"  Temperature drop:     {T_drop_final:.2f} deg C")
print(f"  Mass flow rate:       {mass_flow:.1f} kg/s")
print("=" * 60)

with open(os.path.join(output_dir, "storage_network_table.md"), "w", encoding="utf-8") as f:
    f.write("| Metric | No Storage | With Storage |\n")
    f.write("|:-------|:-----------|:-------------|\n")
    f.write(f"| Daily Cost (CNY) | {total_no_storage:.0f} | {total_with_storage:.0f} |\n")
    f.write(f"| Cost Saving (%) | - | {saving:.1f} |\n")
    f.write(f"| Peak Demand (kW) | {peak_no:.0f} | {peak_with:.0f} |\n")
    f.write(f"| Pipe Transport Delay (s) | - | {transport_delay:.0f} |\n")
    f.write(f"| Pipe Temp Drop (C) | - | {T_drop_final:.2f} |\n")

# ============ Plot ============
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Battery SOC
ax = axes[0, 0]
ax.plot(time_h, soc[:T] * 100, 'b-o', lw=2, ms=4)
ax.fill_between(time_h, 10, 90, alpha=0.1, color='green', label='Safe SOC Range')
ax.set_xlabel('Time (h)')
ax.set_ylabel('SOC (%)')
ax.set_title('Battery SOC Trajectory (Peak Shaving)', fontweight='bold')
ax.grid(True, ls='--', alpha=0.4)
ax.legend()

# Power schedule
ax = axes[0, 1]
colors = ['green' if p > 0 else 'red' for p in P_batt]
ax.bar(time_h, P_batt, color=colors, alpha=0.7, width=0.8)
ax.axhline(0, color='black', lw=0.5)
ax2 = ax.twinx()
ax2.step(time_h, price, 'k--', lw=1.5, where='mid', label='TOU Price')
ax2.set_ylabel('Price (CNY/kWh)')
ax.set_xlabel('Time (h)')
ax.set_ylabel('Battery Power (kW)')
ax.set_title('Charge/Discharge Schedule vs TOU Price', fontweight='bold')
ax.grid(True, ls='--', alpha=0.4)

# Cost comparison
ax = axes[1, 0]
ax.bar(time_h - 0.2, cost_no_storage, width=0.4, label='No Storage', color='red', alpha=0.7)
ax.bar(time_h + 0.2, cost_with_storage, width=0.4, label='With Storage', color='blue', alpha=0.7)
ax.set_xlabel('Time (h)')
ax.set_ylabel('Hourly Cost (CNY)')
ax.set_title(f'Cost Comparison (Saving {saving:.1f}%)', fontweight='bold')
ax.legend()
ax.grid(True, ls='--', alpha=0.4)

# Heating network temperature response
ax = axes[1, 1]
ax.plot(t_sim / 60, T_supply_in, 'r--', lw=1.5, label='Supply Inlet')
ax.plot(t_sim / 60, T_supply_out, 'b-', lw=2, label='Supply Outlet (2km away)')
ax.axvline(x=300/60 + transport_delay/60, color='gray', ls=':', label=f'Delay={transport_delay:.0f}s')
ax.set_xlabel('Time (min)')
ax.set_ylabel('Temperature (C)')
ax.set_title('Heating Network: Thermal Transport Delay', fontweight='bold')
ax.legend()
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "storage_network_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: storage_network_sim.png")
