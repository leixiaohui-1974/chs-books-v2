"""
Ch07: API Architecture Load Test Simulation
Compare synchronous vs asynchronous API architectures under burst water event queries.
Simulate concurrent request handling, queue depth, and response latency.
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

# ============ Simulation Parameters ============
T = 300          # 300 seconds (5 minutes)
dt = 1.0         # 1-second resolution
N = int(T / dt)
time_s = np.arange(N) * dt

# Request arrival rate (requests/second)
# Normal: ~2 req/s, Burst (flood event at t=100-200): ~30 req/s
arrival_rate = np.ones(N) * 2.0
for i in range(N):
    t = time_s[i]
    if 100 <= t <= 200:
        arrival_rate[i] = 2.0 + 28.0 * np.sin(np.pi * (t - 100) / 100)

# Generate actual request counts per second (Poisson)
requests = np.random.poisson(arrival_rate)

# ============ Architecture A: Synchronous (blocking) ============
# Each request takes 2-5 seconds to process (hydro simulation)
# Max concurrent: 4 threads (typical sync server)
sync_max_threads = 4
sync_queue = 0
sync_latency = np.zeros(N)
sync_dropped = np.zeros(N)
sync_queue_depth = np.zeros(N)
sync_active = np.zeros(N)
sync_completed = np.zeros(N)

# Track when each thread becomes free
sync_thread_free = np.zeros(sync_max_threads)

for i in range(N):
    t = time_s[i]
    # Free up threads that finished
    available = int(np.sum(sync_thread_free <= t))

    # New requests arrive
    new_reqs = requests[i]
    sync_queue += new_reqs

    # Process as many as we have threads for
    processed = min(sync_queue, available)
    for j in range(processed):
        # Find a free thread
        for k in range(sync_max_threads):
            if sync_thread_free[k] <= t:
                proc_time = np.random.uniform(2.0, 5.0)
                sync_thread_free[k] = t + proc_time
                sync_latency[i] += proc_time
                break

    sync_queue -= processed
    sync_completed[i] = processed

    # Drop requests if queue > 50 (timeout)
    if sync_queue > 50:
        dropped = sync_queue - 50
        sync_dropped[i] = dropped
        sync_queue = 50

    sync_queue_depth[i] = sync_queue
    sync_active[i] = sync_max_threads - available + processed
    if processed > 0:
        sync_latency[i] = sync_latency[i] / processed + sync_queue * 0.5  # queue wait
    else:
        sync_latency[i] = sync_queue * 0.5 if sync_queue > 0 else 0

# ============ Architecture B: Async (job queue + workers) ============
# Requests immediately return job_id (50ms), actual processing in background
# 8 async workers, job queue unlimited, results polled
async_workers = 8
async_queue = 0
async_latency = np.zeros(N)  # Response latency (just acknowledgment)
async_job_latency = np.zeros(N)  # Actual job completion time
async_queue_depth = np.zeros(N)
async_completed = np.zeros(N)
async_dropped = np.zeros(N)  # Should be zero

async_worker_free = np.zeros(async_workers)

for i in range(N):
    t = time_s[i]
    available = int(np.sum(async_worker_free <= t))

    new_reqs = requests[i]
    async_queue += new_reqs

    # Immediate response: all requests get 50ms ACK
    async_latency[i] = 0.05 if new_reqs > 0 else 0

    # Background processing
    processed = min(async_queue, available)
    total_job_time = 0
    for j in range(processed):
        for k in range(async_workers):
            if async_worker_free[k] <= t:
                proc_time = np.random.uniform(2.0, 5.0)
                async_worker_free[k] = t + proc_time
                total_job_time += proc_time
                break

    async_queue -= processed
    async_completed[i] = processed
    async_queue_depth[i] = async_queue
    if processed > 0:
        async_job_latency[i] = total_job_time / processed
    else:
        async_job_latency[i] = 0

# ============ KPI ============
total_requests = int(np.sum(requests))
sync_total_dropped = int(np.sum(sync_dropped))
sync_total_completed = int(np.sum(sync_completed))
async_total_completed = int(np.sum(async_completed))
sync_avg_latency = np.mean(sync_latency[sync_latency > 0])
sync_p99_latency = np.percentile(sync_latency[sync_latency > 0], 99)
async_avg_ack = np.mean(async_latency[async_latency > 0])

print("=" * 60)
print(f"{'KPI':<35}{'Sync API':>12}{'Async API':>12}")
print("-" * 60)
print(f"{'Total Requests':<35}{total_requests:>12d}{total_requests:>12d}")
print(f"{'Completed':<35}{sync_total_completed:>12d}{async_total_completed:>12d}")
print(f"{'Dropped (timeout)':<35}{sync_total_dropped:>12d}{0:>12d}")
print(f"{'Avg Response Latency (s)':<35}{sync_avg_latency:>12.2f}{async_avg_ack:>12.3f}")
print(f"{'P99 Response Latency (s)':<35}{sync_p99_latency:>12.2f}{0.05:>12.3f}")
print(f"{'Max Queue Depth':<35}{int(np.max(sync_queue_depth)):>12d}{int(np.max(async_queue_depth)):>12d}")
print(f"{'Drop Rate':<35}{sync_total_dropped/max(total_requests,1)*100:>11.1f}%{0.0:>11.1f}%")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Panel 1: Request arrival rate + actual requests
ax = axes[0]
ax.fill_between(time_s, 0, arrival_rate, alpha=0.2, color='blue', label='Expected Rate')
ax.bar(time_s, requests, width=0.8, color='steelblue', alpha=0.6, label='Actual Requests')
ax.axvline(100, color='red', ls='--', lw=1, alpha=0.5)
ax.axvline(200, color='red', ls='--', lw=1, alpha=0.5)
ax.annotate('Flood Event Burst', xy=(150, max(requests)*0.9),
            fontsize=11, ha='center', color='red', fontweight='bold')
ax.set_ylabel('Requests / second', fontsize=11)
ax.set_title('API Request Storm: Normal vs Flood Event Burst Traffic',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: Response latency comparison
ax = axes[1]
ax.plot(time_s, sync_latency, 'r-', lw=1.5, alpha=0.7, label='Sync: User Wait Time')
ax.plot(time_s, async_latency, 'g-', lw=2, label='Async: ACK Latency (50ms)')
ax.axhline(5, color='orange', ls='--', lw=1, label='SLO: 5s Response')
ax.fill_between(time_s, 5, sync_latency, where=sync_latency > 5,
                alpha=0.2, color='red', label='SLO Violation Zone')
ax.set_ylabel('Response Latency (s)', fontsize=11)
ax.set_title('User-Perceived Latency: Sync Blocks vs Async Acknowledges',
             fontsize=13, fontweight='bold')
ax.set_ylim(0, min(max(sync_latency) * 1.1, 50))
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Queue depth + dropped requests
ax = axes[2]
ax.plot(time_s, sync_queue_depth, 'r-', lw=2, label='Sync Queue Depth')
ax.plot(time_s, async_queue_depth, 'g-', lw=2, label='Async Job Queue Depth')
ax.axhline(50, color='red', ls=':', lw=1, label='Sync Queue Limit (50)')
ax2 = ax.twinx()
ax2.bar(time_s, sync_dropped, width=0.8, color='darkred', alpha=0.5, label='Sync Dropped')
ax2.set_ylabel('Dropped Requests', fontsize=11, color='darkred')
ax2.legend(fontsize=9, loc='upper right')
ax.set_xlabel('Time (seconds)', fontsize=11)
ax.set_ylabel('Queue Depth', fontsize=11)
ax.set_title('Queue Saturation & Request Loss Under Flood-Event Traffic Spike',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "api_load_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: api_load_sim.png")

# Markdown table
md = [
    "| KPI | Sync API | Async API | Assessment |",
    "|:----|:---------|:----------|:-----------|",
    f"| Total Requests | {total_requests} | {total_requests} | Same load |",
    f"| Completed | {sync_total_completed} | {async_total_completed} | Async: {async_total_completed-sync_total_completed:+d} |",
    f"| Dropped | {sync_total_dropped} | 0 | Sync loses {sync_total_dropped/max(total_requests,1)*100:.0f}% |",
    f"| Avg Latency | {sync_avg_latency:.1f}s | {async_avg_ack*1000:.0f}ms | Async {sync_avg_latency/async_avg_ack:.0f}x faster |",
    f"| P99 Latency | {sync_p99_latency:.1f}s | 50ms | SLO Compliant |",
]
with open(os.path.join(output_dir, "api_kpi_table.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
for line in md:
    print(line)
