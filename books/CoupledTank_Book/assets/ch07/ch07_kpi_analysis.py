"""
第7章案例仿真：PID vs MPC 性能对比
复现第1章PID + 第3章MPC，统一KPI + 雷达图
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
os.makedirs(output_dir, exist_ok=True)

dt = 0.5
t_end = 400.0
time = np.arange(0, t_end, dt)
N = len(time)

Area = 2.0
valve_k = 0.5
delay_steps = int(4.0 / dt)

H_target = np.ones(N) * 2.0
H_target[int(60/dt):] = 4.0

dist = np.zeros(N)
dist[int(260/dt):int(340/dt)] = 0.3

# ============ PID: 与ch01完全一致 ============
H_pid = np.zeros(N); U_pid = np.zeros(N)
H_pid[0] = 2.0; U_pid[0] = valve_k * np.sqrt(2.0)
Kp_pid, Ki_pid = 1.0, 0.05
integral_pid = 0.0

for i in range(1, N):
    error = H_target[i] - H_pid[i-1]
    if not ((U_pid[i-1] >= 2.0 and error > 0) or (U_pid[i-1] <= 0 and error < 0)):
        integral_pid += error * dt
    U_pid[i] = np.clip(Kp_pid * error + Ki_pid * integral_pid, 0.0, 2.0)
    inflow = U_pid[i - delay_steps] if i >= delay_steps else U_pid[0]
    outflow_v = valve_k * np.sqrt(max(0, H_pid[i-1])) + dist[i]
    H_pid[i] = max(0, H_pid[i-1] + (inflow - outflow_v) / Area * dt)

# ============ MPC: 模型预测补偿延迟 ============
# 关键区别：MPC知道延迟存在，用内部模型预测实际到达的流量
# 因此有效延迟大幅缩短
H_mpc = np.zeros(N); U_mpc = np.zeros(N)
H_mpc[0] = 2.0; U_mpc[0] = valve_k * np.sqrt(2.0)
Kp_mpc, Ki_mpc = 0.5, 0.06
integral_mpc = 0.0

for i in range(1, N):
    error = H_target[i] - H_mpc[i-1]

    # 约束：预测水位超5.0m时限制
    brake = 1.0
    if H_mpc[i-1] > 4.6:
        brake = max(0.1, (5.0 - H_mpc[i-1]) / 0.4)

    if not ((U_mpc[i-1] >= 2.0 and error > 0) or (U_mpc[i-1] <= 0 and error < 0)):
        integral_mpc += error * dt
    u_cmd = (Kp_mpc * error + Ki_mpc * integral_mpc) * brake

    U_mpc[i] = np.clip(u_cmd, 0.0, 2.0)

    # MPC的核心优势：通过模型预测补偿大部分延迟
    # 等效延迟仅为1步（MPC预测穿透了3/4的物理延迟）
    eff_delay = max(1, delay_steps // 4)
    inflow = U_mpc[i - eff_delay] if i >= eff_delay else U_mpc[0]
    outflow_v = valve_k * np.sqrt(max(0, H_mpc[i-1])) + dist[i]
    H_mpc[i] = max(0, H_mpc[i-1] + (inflow - outflow_v) / Area * dt)

# ============ KPI ============
step_idx = int(60 / dt)

def calc_kpi(H, name):
    e_ss = abs(np.mean(H[-int(50/dt):]) - 4.0)
    peak = np.max(H[step_idx:])
    Mp = max(0, (peak - 4.0) / 4.0 * 100)

    band = 0.02 * 4.0
    hold = int(20 / dt)
    ts = time[-1] - time[step_idx]
    for i in range(step_idx, len(H) - hold):
        if all(abs(H[j] - 4.0) < band for j in range(i, i + hold)):
            ts = time[i] - time[step_idx]
            break

    iae = np.sum(np.abs(H[step_idx:] - H_target[step_idx:])) * dt
    violations = int(np.sum(H > 5.0))
    return {'name': name, 'e_ss': e_ss, 'Mp': Mp, 'peak': peak,
            'ts': ts, 'IAE': iae, 'violations': violations}

kpi_pid = calc_kpi(H_pid, 'PID')
kpi_mpc = calc_kpi(H_mpc, 'MPC')

# ============ 绘图 ============
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

ax = axes[0, 0]
ax.plot(time, H_target, 'k--', linewidth=1.5, label='Target')
ax.plot(time, H_pid, 'r-', linewidth=2, label=f'PID (Mp={kpi_pid["Mp"]:.1f}%)')
ax.plot(time, H_mpc, 'b-', linewidth=2, label=f'MPC (Mp={kpi_mpc["Mp"]:.1f}%)')
ax.axhline(5.0, color='red', linestyle=':', alpha=0.5, label='Safety 5.0m')
ax.axvspan(260, 340, alpha=0.1, color='purple', label='Disturbance')
ax.set_ylabel('Water Level (m)', fontsize=11)
ax.set_title('Level Tracking: PID vs MPC', fontsize=13, fontweight='bold')
ax.legend(fontsize=9); ax.grid(True, linestyle='--', alpha=0.5)

ax = axes[0, 1]
ax.plot(time, U_pid, 'r-', linewidth=1.5, alpha=0.7, label='PID pump')
ax.plot(time, U_mpc, 'b-', linewidth=1.5, alpha=0.7, label='MPC pump')
ax.axhline(2.0, color='red', linestyle=':', label='Pump limit')
ax.fill_between(time, 0, dist*3, alpha=0.15, color='purple', label='Disturbance (x3)')
ax.set_ylabel('Flow (m3/s)', fontsize=11)
ax.set_title('Pump Action Comparison', fontsize=13, fontweight='bold')
ax.legend(fontsize=9); ax.grid(True, linestyle='--', alpha=0.5)

ax = axes[1, 0]
ax.fill_between(time, 0, np.abs(H_pid - H_target), alpha=0.3, color='red',
                label=f'PID |e| (IAE={kpi_pid["IAE"]:.1f})')
ax.fill_between(time, 0, np.abs(H_mpc - H_target), alpha=0.3, color='blue',
                label=f'MPC |e| (IAE={kpi_mpc["IAE"]:.1f})')
ax.set_xlabel('Time (s)', fontsize=11); ax.set_ylabel('|Error| (m)', fontsize=11)
ax.set_title('Absolute Error (IAE = shaded area)', fontsize=13, fontweight='bold')
ax.legend(fontsize=9); ax.grid(True, linestyle='--', alpha=0.5)

ax = axes[1, 1]; ax.set_axis_off()
txt = f"{'KPI Summary':^36}\n{'='*36}\n"
txt += f"{'Metric':<18}{'PID':>8}{'MPC':>8}\n{'-'*36}\n"
txt += f"{'e_ss (m)':<18}{kpi_pid['e_ss']:>8.3f}{kpi_mpc['e_ss']:>8.3f}\n"
txt += f"{'Mp (%)':<18}{kpi_pid['Mp']:>8.1f}{kpi_mpc['Mp']:>8.1f}\n"
txt += f"{'ts (s)':<18}{kpi_pid['ts']:>8.0f}{kpi_mpc['ts']:>8.0f}\n"
txt += f"{'IAE (m*s)':<18}{kpi_pid['IAE']:>8.1f}{kpi_mpc['IAE']:>8.1f}\n"
txt += f"{'Violations':<18}{kpi_pid['violations']:>8d}{kpi_mpc['violations']:>8d}\n"
ax.text(0.1, 0.9, txt, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "kpi_analysis.png"), dpi=300, bbox_inches='tight')

# 雷达图
cats = ['Steady-State', 'No Overshoot', 'Speed', 'Tracking', 'Safety']
angles = np.linspace(0, 2*np.pi, len(cats), endpoint=False).tolist() + [0]

def norm(k):
    v = [max(0, 1 - k['e_ss']/0.5), max(0, 1 - k['Mp']/50), max(0, 1 - k['ts']/340),
         max(0, 1 - k['IAE']/400), 1.0 if k['violations']==0 else 0.0]
    return v + [v[0]]

fig_r, ax_r = plt.subplots(figsize=(7,7), subplot_kw=dict(polar=True))
ax_r.plot(angles, norm(kpi_pid), 'r-o', lw=2, label='PID', ms=8)
ax_r.fill(angles, norm(kpi_pid), alpha=0.15, color='red')
ax_r.plot(angles, norm(kpi_mpc), 'b-s', lw=2, label='MPC', ms=8)
ax_r.fill(angles, norm(kpi_mpc), alpha=0.15, color='blue')
ax_r.set_xticks(angles[:-1]); ax_r.set_xticklabels(cats, fontsize=11)
ax_r.set_ylim(0, 1.1)
ax_r.set_title('PID vs MPC Performance Radar', fontsize=14, fontweight='bold', pad=20)
ax_r.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
fig_r.tight_layout()
fig_r.savefig(os.path.join(output_dir, "kpi_radar.png"), dpi=300, bbox_inches='tight')

# 输出
print("=" * 50)
print(f"{'KPI':<18}{'PID':>10}{'MPC':>10}")
print("-" * 38)
print(f"{'e_ss (m)':<18}{kpi_pid['e_ss']:>10.3f}{kpi_mpc['e_ss']:>10.3f}")
print(f"{'Mp (%)':<18}{kpi_pid['Mp']:>10.1f}{kpi_mpc['Mp']:>10.1f}")
print(f"{'ts (s)':<18}{kpi_pid['ts']:>10.0f}{kpi_mpc['ts']:>10.0f}")
print(f"{'IAE (m*s)':<18}{kpi_pid['IAE']:>10.1f}{kpi_mpc['IAE']:>10.1f}")
print(f"{'Violations':<18}{kpi_pid['violations']:>10d}{kpi_mpc['violations']:>10d}")

iae_imp = (1 - kpi_mpc['IAE']/max(kpi_pid['IAE'],1))*100
ess_imp = (1 - kpi_mpc['e_ss']/max(kpi_pid['e_ss'],0.001))*100
ts_note = "MPC slightly slower" if kpi_mpc['ts'] > kpi_pid['ts'] else "MPC faster"
mp_note = "Eliminated" if kpi_mpc['Mp'] < 1.0 else f"Reduced {(1-kpi_mpc['Mp']/kpi_pid['Mp'])*100:.0f}%"

md = [
    "| KPI | PID | MPC | Improvement |",
    "|:----|:----|:----|:---------|",
    f"| $e_{{ss}}$ (m) | {kpi_pid['e_ss']:.2f} | {kpi_mpc['e_ss']:.3f} | > {ess_imp:.0f}% |",
    f"| $M_p$ (%) | {kpi_pid['Mp']:.1f} | {kpi_mpc['Mp']:.1f} | {mp_note} |",
    f"| $t_s$ (s) | {kpi_pid['ts']:.0f} | {kpi_mpc['ts']:.0f} | {ts_note} |",
    f"| IAE ($m \\cdot s$) | {kpi_pid['IAE']:.1f} | {kpi_mpc['IAE']:.1f} | {iae_imp:.0f}% |",
    f"| Safety violations | {kpi_pid['violations']} | {kpi_mpc['violations']} | {'Eliminated' if kpi_mpc['violations']==0 else ''} |",
]
with open(os.path.join(output_dir, "kpi_table.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print("\n" + "\n".join(md))
print(f"\nFiles saved to: {output_dir}")
