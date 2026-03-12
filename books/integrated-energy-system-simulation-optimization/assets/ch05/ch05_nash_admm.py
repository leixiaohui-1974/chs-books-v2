"""
Ch05: Multi-Agent Game Theory & Distributed Optimization
Two IES prosumers trade energy via Nash bargaining + ADMM.
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

T = 24
time_h = np.arange(T)

# ============ Two Prosumers ============
# Prosumer A: has solar PV (2 MW peak) + battery (1 MWh)
# Prosumer B: has CHP (1 MW gas) + heat demand
# Grid buy price (TOU), grid sell price = 0.3 * buy price

price_buy = np.where((time_h >= 8) & (time_h <= 20), 0.85, 0.40)  # CNY/kWh
price_sell = price_buy * 0.3  # feed-in tariff

# PV generation profile (MW)
pv_gen = np.array([0, 0, 0, 0, 0, 0.1, 0.5, 1.0, 1.5, 1.8,
                   2.0, 2.0, 1.8, 1.5, 1.2, 0.8, 0.4, 0.1, 0, 0,
                   0, 0, 0, 0])

# Prosumer A demand (MW)
demand_A = np.array([0.3, 0.25, 0.2, 0.2, 0.25, 0.4, 0.8, 1.2, 1.0, 0.9,
                     0.8, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.0, 0.8,
                     0.6, 0.5, 0.4, 0.3])

# Prosumer B demand (MW)
demand_B = np.array([0.5, 0.4, 0.4, 0.3, 0.4, 0.6, 1.0, 1.5, 1.3, 1.1,
                     1.0, 0.9, 0.9, 1.0, 1.2, 1.3, 1.4, 1.5, 1.2, 1.0,
                     0.8, 0.7, 0.6, 0.5])

# Prosumer A surplus/deficit (positive = surplus)
surplus_A = pv_gen - demand_A

# ============ Scenario 1: No P2P Trading (Grid Only) ============
cost_A_no_trade = np.zeros(T)
cost_B_no_trade = np.zeros(T)

for i in range(T):
    if surplus_A[i] > 0:
        cost_A_no_trade[i] = -surplus_A[i] * 1000 * price_sell[i]  # revenue
    else:
        cost_A_no_trade[i] = -surplus_A[i] * 1000 * price_buy[i]  # cost (surplus is negative)
    cost_B_no_trade[i] = demand_B[i] * 1000 * price_buy[i]

# ============ Scenario 2: Nash Bargaining P2P Trading ============
# P2P price = geometric mean of buy and sell prices (Nash bargaining solution)
price_p2p = np.sqrt(price_buy * price_sell)  # Nash bargaining price

cost_A_trade = np.zeros(T)
cost_B_trade = np.zeros(T)
p2p_flow = np.zeros(T)  # A -> B

for i in range(T):
    if surplus_A[i] > 0:
        # A has surplus, B needs energy
        tradeable = min(surplus_A[i], demand_B[i])
        p2p_flow[i] = tradeable

        # A: sell tradeable at p2p price, rest at grid sell price
        remaining_surplus = surplus_A[i] - tradeable
        cost_A_trade[i] = -(tradeable * 1000 * price_p2p[i] +
                            remaining_surplus * 1000 * price_sell[i])

        # B: buy tradeable at p2p price, rest from grid
        remaining_demand = demand_B[i] - tradeable
        cost_B_trade[i] = (tradeable * 1000 * price_p2p[i] +
                           remaining_demand * 1000 * price_buy[i])
    else:
        # A has deficit, both buy from grid
        cost_A_trade[i] = -surplus_A[i] * 1000 * price_buy[i]
        cost_B_trade[i] = demand_B[i] * 1000 * price_buy[i]

# ============ ADMM Convergence Simulation ============
# Simple ADMM for consensus optimization between A and B
# Minimize total cost subject to power balance
rho_admm = 0.5  # penalty parameter
max_iter = 50

# Track convergence at a representative hour (hour 10, peak PV)
h = 10
primal_residual = np.zeros(max_iter)
dual_residual = np.zeros(max_iter)

# Variables: x_A (A's trade), x_B (B's trade), z (consensus)
x_A = 0.0
x_B = 0.0
z = 0.0
lambda_A = 0.0
lambda_B = 0.0

for k in range(max_iter):
    # x-update (each prosumer optimizes locally)
    # A minimizes: cost_A(x_A) + lambda_A*(x_A - z) + rho/2*(x_A - z)^2
    x_A_new = (surplus_A[h] * price_p2p[h] - lambda_A + rho_admm * z) / (price_p2p[h] + rho_admm)
    x_A_new = np.clip(x_A_new, 0, surplus_A[h])

    x_B_new = (demand_B[h] * price_p2p[h] + lambda_B + rho_admm * z) / (price_p2p[h] + rho_admm)
    x_B_new = np.clip(x_B_new, 0, demand_B[h])

    # z-update (consensus)
    z_new = (x_A_new + x_B_new) / 2

    # Dual update
    lambda_A += rho_admm * (x_A_new - z_new)
    lambda_B += rho_admm * (x_B_new - z_new)

    # Residuals
    primal_residual[k] = np.sqrt((x_A_new - z_new)**2 + (x_B_new - z_new)**2)
    dual_residual[k] = rho_admm * np.abs(z_new - z)

    x_A, x_B, z = x_A_new, x_B_new, z_new

# ============ KPI ============
total_A_no = np.sum(cost_A_no_trade)
total_A_trade = np.sum(cost_A_trade)
total_B_no = np.sum(cost_B_no_trade)
total_B_trade = np.sum(cost_B_trade)
total_p2p = np.sum(p2p_flow)

admm_converge_iter = np.argmax(primal_residual < 1e-3) if np.any(primal_residual < 1e-3) else max_iter

print("=" * 65)
print(f"{'Metric':<35}{'No Trading':>14}{'P2P Trading':>14}")
print("-" * 65)
print(f"{'Prosumer A Daily Cost (CNY)':<35}{total_A_no:>14.0f}{total_A_trade:>14.0f}")
print(f"{'Prosumer B Daily Cost (CNY)':<35}{total_B_no:>14.0f}{total_B_trade:>14.0f}")
print(f"{'System Total Cost (CNY)':<35}{total_A_no+total_B_no:>14.0f}{total_A_trade+total_B_trade:>14.0f}")
print(f"{'P2P Energy Traded (MWh)':<35}{'-':>14}{total_p2p:>14.1f}")
print(f"{'ADMM Convergence (iterations)':<35}{'-':>14}{admm_converge_iter:>14d}")
print(f"{'A Saving (%)':<35}{'-':>14}{(1-total_A_trade/total_A_no)*100:>14.1f}")
print(f"{'B Saving (%)':<35}{'-':>14}{(1-total_B_trade/total_B_no)*100:>14.1f}")
print("=" * 65)

with open(os.path.join(output_dir, "nash_admm_table.md"), "w", encoding="utf-8") as f:
    f.write("| Metric | No Trading | P2P (Nash) |\n")
    f.write("|:-------|:-----------|:-----------|\n")
    f.write(f"| Prosumer A Cost (CNY) | {total_A_no:.0f} | {total_A_trade:.0f} |\n")
    f.write(f"| Prosumer B Cost (CNY) | {total_B_no:.0f} | {total_B_trade:.0f} |\n")
    f.write(f"| System Total (CNY) | {total_A_no+total_B_no:.0f} | {total_A_trade+total_B_trade:.0f} |\n")
    f.write(f"| P2P Traded (MWh) | - | {total_p2p:.1f} |\n")
    f.write(f"| ADMM Iterations | - | {admm_converge_iter} |\n")

# ============ Plot ============
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel 1: PV surplus and demand
ax = axes[0, 0]
ax.fill_between(time_h, 0, pv_gen, alpha=0.3, color='gold', label='PV Generation')
ax.plot(time_h, demand_A, 'b-o', ms=3, lw=2, label='Prosumer A Demand')
ax.plot(time_h, demand_B, 'r-s', ms=3, lw=2, label='Prosumer B Demand')
ax.set_xlabel('Time (h)')
ax.set_ylabel('Power (MW)')
ax.set_title('Prosumer Profiles & PV Generation', fontweight='bold')
ax.legend(fontsize=8)
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: P2P trade flow
ax = axes[0, 1]
ax.bar(time_h, p2p_flow * 1000, color='green', alpha=0.7, label='P2P Trade A→B')
ax2 = ax.twinx()
ax2.plot(time_h, price_buy, 'k-', lw=1.5, label='Grid Buy')
ax2.plot(time_h, price_p2p, 'r--', lw=1.5, label='P2P Price')
ax2.plot(time_h, price_sell, 'b:', lw=1.5, label='Grid Sell')
ax2.set_ylabel('Price (CNY/kWh)')
ax2.legend(fontsize=7, loc='upper right')
ax.set_xlabel('Time (h)')
ax.set_ylabel('P2P Trade (kW)')
ax.set_title('Peer-to-Peer Energy Trading', fontweight='bold')
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Cost comparison bar chart
ax = axes[1, 0]
x = np.arange(2)
width = 0.35
bars1 = ax.bar(x - width/2, [total_A_no, total_B_no], width, label='No Trading', color='red', alpha=0.7)
bars2 = ax.bar(x + width/2, [total_A_trade, total_B_trade], width, label='P2P Trading', color='blue', alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(['Prosumer A', 'Prosumer B'])
ax.set_ylabel('Daily Cost (CNY)')
ax.set_title('Cost Comparison: Grid-Only vs P2P', fontweight='bold')
ax.legend()
ax.grid(True, ls='--', alpha=0.4, axis='y')

# Panel 4: ADMM convergence
ax = axes[1, 1]
iters = np.arange(max_iter)
ax.semilogy(iters, primal_residual, 'b-', lw=2, label='Primal Residual')
ax.semilogy(iters, np.maximum(dual_residual, 1e-10), 'r--', lw=2, label='Dual Residual')
ax.axhline(1e-3, color='green', ls=':', label='Tolerance')
ax.set_xlabel('ADMM Iteration')
ax.set_ylabel('Residual')
ax.set_title('ADMM Convergence (Hour 10)', fontweight='bold')
ax.legend()
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "nash_admm_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: nash_admm_sim.png")
