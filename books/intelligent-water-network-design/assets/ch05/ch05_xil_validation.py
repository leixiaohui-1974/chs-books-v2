"""
Ch05: MiL vs SiL Precision Validation
Compare float64 (MiL/Python) vs 16-bit fixed-point (SiL/PLC) MPC performance.
Real PLCs often use 16-bit integers scaled by 0.1, causing quantization errors.
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

# ============ System Parameters ============
N = 48              # 48 half-hour steps = 24 hours
dt = 0.5            # hours per step
V_max = 50.0        # max volume (x 10000 m3)
V_safe = 48.0       # ODD boundary
U_max = 15.0        # max pump (x 10000 m3/h)
V_init = 20.0       # initial volume

# Inflow pattern (x 10000 m3/h)
time_h = np.arange(N) * dt
Q_in = np.zeros(N)
for i in range(N):
    t = time_h[i]
    Q_in[i] = 2.0
    if 8 <= t <= 14:
        Q_in[i] += 4.0 * np.sin(np.pi * (t - 8) / 6)
    if 18 <= t <= 23:
        Q_in[i] += 8.0 * np.sin(np.pi * (t - 18) / 5)

# Electricity price
price = np.ones(N) * 0.6
for i in range(N):
    t = time_h[i]
    if 10 <= t <= 15 or 18 <= t <= 21:
        price[i] = 1.2
    elif t <= 6 or t >= 22:
        price[i] = 0.3


def fixed16(x, scale=10.0):
    """Simulate 16-bit fixed-point: multiply by scale, round to int16, divide back.
    Scale=10 means resolution = 0.1 units (i.e., 1000 m3 resolution)."""
    clamped = np.clip(x * scale, -32768, 32767)
    return np.int16(np.round(clamped)).astype(np.float64) / scale


def run_mpc(mode='float64'):
    """Run MPC with specified precision mode."""
    V = np.zeros(N + 1)
    U = np.zeros(N)
    V[0] = V_init
    v_state = V_init

    for t in range(N):
        q = Q_in[t]
        if mode == 'fixed16':
            q = fixed16(q)
            v_state = fixed16(v_state)

        best_u = 0.0
        best_cost = 1e12

        # Search over 40 pump candidates
        for ui in range(41):
            u_cand = U_max * ui / 40.0
            if mode == 'fixed16':
                u_cand = fixed16(u_cand)

            cost = 0.0
            v_pred = v_state

            # 6-step lookahead
            for k in range(min(6, N - t)):
                tk = t + k
                q_k = Q_in[tk]
                p_k = price[tk]
                if mode == 'fixed16':
                    q_k = fixed16(q_k)
                    p_k = fixed16(p_k)

                u_k = u_cand if k == 0 else max(0.0, min(U_max,
                    (v_pred - 15.0) * 0.8))
                if mode == 'fixed16':
                    u_k = fixed16(u_k)

                v_pred = v_pred + (q_k - u_k) * dt
                if mode == 'fixed16':
                    v_pred = fixed16(v_pred)
                v_pred = max(0.0, min(V_max, v_pred))

                cost += p_k * u_k * dt
                if v_pred > V_safe:
                    cost += 500.0 * (v_pred - V_safe) ** 2
                if mode == 'fixed16':
                    cost = fixed16(cost, scale=1.0)  # coarser cost resolution

            if cost < best_cost:
                best_cost = cost
                best_u = u_cand

        U[t] = best_u
        v_next = v_state + (q - best_u) * dt
        if mode == 'fixed16':
            v_next = fixed16(v_next)
        v_state = max(0.0, min(V_max, v_next))
        V[t + 1] = v_state

    return V, U


# ============ Run Both Modes ============
V_f64, U_f64 = run_mpc('float64')
V_fix, U_fix = run_mpc('fixed16')

time_v = np.arange(N + 1) * dt
time_u = np.arange(N) * dt

# ============ KPI ============
trunc_err = np.abs(V_f64 - V_fix)
max_err = np.max(trunc_err)
rmse_base = np.sqrt(np.mean((V_f64[1:] - V_init) ** 2))
rmse_fix = np.sqrt(np.mean((V_fix[1:] - V_init) ** 2))
rmse_deg = abs(rmse_fix - rmse_base) / max(rmse_base, 0.01) * 100
odd_f64 = int(np.sum(V_f64 > V_safe))
odd_fix = int(np.sum(V_fix > V_safe))
cost_f64 = np.sum(price * U_f64 * dt)
cost_fix = np.sum(price * U_fix * dt)

print("=" * 58)
print(f"{'KPI':<30}{'MiL(f64)':>13}{'SiL(int16)':>13}")
print("-" * 58)
print(f"{'Peak Volume (x10k m3)':<30}{np.max(V_f64):>13.2f}{np.max(V_fix):>13.2f}")
print(f"{'Max Quant Error (x10k m3)':<30}{'-':>13}{max_err:>13.2f}")
print(f"{'RMSE Degradation (%)':<30}{'-':>13}{rmse_deg:>13.1f}")
print(f"{'ODD Violations (>48)':<30}{odd_f64:>13d}{odd_fix:>13d}")
print(f"{'Energy Cost (CNY)':<30}{cost_f64:>13.0f}{cost_fix:>13.0f}")
odd_pass = odd_fix == 0 and rmse_deg < 5
print(f"{'ODD Compliance':<30}{'PASS':>13}{'PASS' if odd_pass else 'FAIL':>13}")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

ax = axes[0]
ax.plot(time_v, V_f64, 'b-o', lw=2, ms=3, label=f'MiL (float64) peak={np.max(V_f64):.2f}')
ax.plot(time_v, V_fix, 'r--s', lw=2, ms=3, label=f'SiL (int16) peak={np.max(V_fix):.2f}')
ax.axhline(V_safe, color='orange', ls='--', lw=1.5, label=f'ODD Boundary ({V_safe})')
ax.axhline(V_max, color='red', ls=':', lw=1.5, label=f'Overflow ({V_max})')
ax.fill_between(time_v, V_safe, V_max, alpha=0.08, color='red', label='ODD Violation Zone')
ax.set_ylabel('Volume (x10000 m3)', fontsize=11)
ax.set_title('MiL vs SiL: Tank Volume & ODD Compliance', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.5)

ax = axes[1]
colors = ['green' if e < 0.15 else 'orange' if e < 0.5 else 'red' for e in trunc_err]
ax.bar(time_v, trunc_err, width=dt*0.8, color=colors, alpha=0.8)
ax.axhline(0.5, color='red', ls='--', lw=1, label='Threshold (0.5 = 5000 m3)')
ax.set_ylabel('Quantization Error (x10000 m3)', fontsize=11)
ax.set_title(f'Fixed-Point Quantization Error (max={max_err:.2f}, resolution=0.1)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.5)

ax = axes[2]
ax.step(time_u, U_f64, 'b-', lw=2, where='post', label='MiL Pump (f64)')
ax.step(time_u, U_fix, 'r--', lw=2, where='post', label='SiL Pump (int16)')
ax2 = ax.twinx()
ax2.fill_between(time_u, 0, price, alpha=0.15, color='orange', step='post')
ax2.set_ylabel('Price (CNY/kWh)', fontsize=11, color='orange')
ax.set_xlabel('Time (hours)', fontsize=11)
ax.set_ylabel('Pump Flow (x10000 m3/h)', fontsize=11)
ax.set_title('Control Action: Float64 vs Fixed-Point', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.5)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "xil_validation_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: xil_validation_sim.png")

# Markdown KPI table
md = [
    "| KPI | MiL (float64) | SiL (int16) | Assessment |",
    "|:----|:--------------|:------------|:-----------|",
    f"| Peak Volume | {np.max(V_f64):.2f} | {np.max(V_fix):.2f} | {'Both Safe' if np.max(V_fix)<V_max else 'SiL OVERFLOW'} |",
    f"| Max Quantization Error | - | {max_err:.2f} (x10k m3) | {'OK' if max_err<0.5 else 'Review Needed'} |",
    f"| RMSE Degradation | - | {rmse_deg:.1f}% | {'<5% PASS' if rmse_deg<5 else '>5% FAIL'} |",
    f"| ODD Violations | {odd_f64} | {odd_fix} | {'Compliant' if odd_fix==0 else 'Non-compliant'} |",
    f"| Energy Cost (CNY) | {cost_f64:.0f} | {cost_fix:.0f} | Delta={abs(cost_f64-cost_fix):.0f} |",
]
with open(os.path.join(output_dir, "xil_kpi_table.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
for line in md:
    print(line)
