"""
Ch04: MBD Topology — Digital Twin Entity Graph & Water Balance Verification
Build a small water network (3 basins, 2 reaches, 1 reservoir, 1 pump station),
verify mass conservation through topological ordering, and visualize the network.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from collections import defaultdict, deque
import os

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))

# ============ MBD Entity Definitions ============
class Entity:
    """Base MBD entity with id, type, and attributes."""
    def __init__(self, eid, etype, name, **attrs):
        self.eid = eid
        self.etype = etype
        self.name = name
        self.attrs = attrs

    def __repr__(self):
        return f"{self.etype}({self.eid}: {self.name})"


class WaterNetwork:
    """Directed graph representing water flow topology."""
    def __init__(self):
        self.entities = {}
        self.edges = []  # (from_id, to_id)
        self.adj = defaultdict(list)
        self.in_degree = defaultdict(int)

    def add_entity(self, entity):
        self.entities[entity.eid] = entity
        if entity.eid not in self.in_degree:
            self.in_degree[entity.eid] = 0

    def add_flow(self, from_id, to_id):
        self.edges.append((from_id, to_id))
        self.adj[from_id].append(to_id)
        self.in_degree[to_id] += 1

    def topo_sort(self):
        """Kahn's algorithm for topological ordering."""
        queue = deque()
        for eid in self.entities:
            if self.in_degree[eid] == 0:
                queue.append(eid)
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for nxt in self.adj[node]:
                self.in_degree[nxt] -= 1
                if self.in_degree[nxt] == 0:
                    queue.append(nxt)
        if len(order) != len(self.entities):
            raise ValueError("Cycle detected in water network topology!")
        return order


# ============ Build Network ============
net = WaterNetwork()

# Basins (rainfall source nodes)
net.add_entity(Entity("B1", "Basin", "North Hill", area_km2=45, CN=72))
net.add_entity(Entity("B2", "Basin", "East Valley", area_km2=30, CN=85))
net.add_entity(Entity("B3", "Basin", "South Plain", area_km2=60, CN=90))

# Reaches (river channels)
net.add_entity(Entity("R1", "Reach", "Main River Upper", length_km=12, slope=0.002))
net.add_entity(Entity("R2", "Reach", "Main River Lower", length_km=8, slope=0.001))

# Reservoir
net.add_entity(Entity("RV1", "Reservoir", "Central Dam", capacity_Mm3=50, current_Mm3=30))

# Pump Station
net.add_entity(Entity("P1", "PumpStation", "City Pump", max_flow_m3s=15))

# Outlet
net.add_entity(Entity("OUT", "Outlet", "Sea Discharge"))

# Flow topology: B1->R1, B2->R1, R1->RV1, B3->R2, RV1->R2, R2->P1, P1->OUT
net.add_flow("B1", "R1")
net.add_flow("B2", "R1")
net.add_flow("R1", "RV1")
net.add_flow("B3", "R2")
net.add_flow("RV1", "R2")
net.add_flow("R2", "P1")
net.add_flow("P1", "OUT")

# ============ Topological Sort ============
topo_order = net.topo_sort()
print("Topological Order (computation sequence):")
for i, eid in enumerate(topo_order):
    e = net.entities[eid]
    print(f"  Step {i+1}: {e}")

# ============ Water Balance Simulation ============
N = 48  # 48 hours
dt = 1.0  # hour

# Rainfall (mm/h) — storm event at t=12-24
time_h = np.arange(N) * dt
rain = np.zeros(N)
for i in range(N):
    t = time_h[i]
    if 12 <= t <= 24:
        rain[i] = 8.0 * np.sin(np.pi * (t - 12) / 12)

# Simple runoff coefficient per basin
basins = {
    "B1": {"area": 45e6, "rc": 0.35},  # forested
    "B2": {"area": 30e6, "rc": 0.60},  # suburban
    "B3": {"area": 60e6, "rc": 0.75},  # urban
}

# Compute inflow from each basin (m3/h)
basin_flow = {}
for bid, props in basins.items():
    # Q = rain(mm/h) * area(m2) * rc / 1000
    basin_flow[bid] = rain * props["area"] * props["rc"] / 1000.0

# Route water through network in topological order
node_inflow = defaultdict(lambda: np.zeros(N))
node_outflow = defaultdict(lambda: np.zeros(N))

# Assign basin runoff
for bid in ["B1", "B2", "B3"]:
    node_outflow[bid] = basin_flow[bid]

# Reservoir state
rv_volume = np.zeros(N + 1)
rv_volume[0] = 30e6  # 30 Mm3 initial
rv_capacity = 50e6
rv_release = np.zeros(N)

# Process in topological order
for eid in topo_order:
    e = net.entities[eid]

    if e.etype == "Basin":
        # Already computed
        pass
    elif e.etype == "Reach":
        # Sum all upstream inflows, apply simple lag (2h delay for R1, 1h for R2)
        total_in = np.zeros(N)
        for (fr, to) in net.edges:
            if to == eid:
                total_in += node_outflow[fr]
        lag = 2 if eid == "R1" else 1
        delayed = np.zeros(N)
        delayed[lag:] = total_in[:-lag] if lag > 0 else total_in
        node_inflow[eid] = total_in
        node_outflow[eid] = delayed * 0.95  # 5% transmission loss
    elif e.etype == "Reservoir":
        total_in = np.zeros(N)
        for (fr, to) in net.edges:
            if to == eid:
                total_in += node_outflow[fr]
        node_inflow[eid] = total_in
        for t in range(N):
            rv_volume[t + 1] = rv_volume[t] + total_in[t] * dt
            # Release rule: if volume > 40Mm3, release excess; always release min 5 m3/s
            base_release = 5.0 * 3600  # m3/h
            if rv_volume[t + 1] > 40e6:
                flood_release = (rv_volume[t + 1] - 40e6) * 0.3
                rv_release[t] = base_release + flood_release
            else:
                rv_release[t] = base_release
            rv_volume[t + 1] = max(0, rv_volume[t + 1] - rv_release[t] * dt)
        node_outflow[eid] = rv_release
    elif e.etype == "PumpStation":
        total_in = np.zeros(N)
        for (fr, to) in net.edges:
            if to == eid:
                total_in += node_outflow[fr]
        node_inflow[eid] = total_in
        # Pump capacity: max 15 m3/s = 54000 m3/h
        pump_cap = 15.0 * 3600
        node_outflow[eid] = np.minimum(total_in, pump_cap)
    elif e.etype == "Outlet":
        total_in = np.zeros(N)
        for (fr, to) in net.edges:
            if to == eid:
                total_in += node_outflow[fr]
        node_inflow[eid] = total_in

# ============ Mass Balance Check ============
total_rain_vol = sum(np.sum(basin_flow[b]) * dt for b in basins)
total_outlet_vol = np.sum(node_inflow["OUT"]) * dt
rv_storage_change = rv_volume[-1] - rv_volume[0]
# Transmission losses in reaches
loss_R1 = np.sum(node_inflow["R1"] - node_outflow["R1"] / 0.95 * 0.05) * dt  # approximate
total_loss = total_rain_vol - total_outlet_vol - rv_storage_change

print(f"\n{'='*50}")
print(f"Water Balance Check (48h simulation)")
print(f"{'-'*50}")
print(f"Total basin runoff:  {total_rain_vol/1e6:>10.2f} Mm3")
print(f"Total outlet volume: {total_outlet_vol/1e6:>10.2f} Mm3")
print(f"Reservoir dV:        {rv_storage_change/1e6:>10.2f} Mm3")
print(f"Residual (losses):   {total_loss/1e6:>10.2f} Mm3")
print(f"Mass balance error:  {abs(total_loss)/max(total_rain_vol,1)*100:>10.2f} %")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# Panel 1: Rainfall + Basin Runoff
ax = axes[0]
ax.bar(time_h, rain, width=0.8, color='steelblue', alpha=0.5, label='Rainfall (mm/h)')
ax.set_ylabel('Rainfall (mm/h)', fontsize=11, color='steelblue')
ax.set_ylim(0, max(rain) * 1.5)
ax2 = ax.twinx()
for bid, color, label in [("B1", "green", "B1-North Hill (CN=72)"),
                            ("B2", "orange", "B2-East Valley (CN=85)"),
                            ("B3", "red", "B3-South Plain (CN=90)")]:
    ax2.plot(time_h, basin_flow[bid] / 3600, color=color, lw=2, label=label)
ax2.set_ylabel('Basin Runoff (m3/s)', fontsize=11)
ax2.legend(fontsize=9, loc='upper right')
ax.set_title('MBD Topology: Rainfall Input & Basin Runoff by Land Use Type',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.4)

# Panel 2: Reservoir Volume + Release
ax = axes[1]
ax.fill_between(np.arange(N+1) * dt, rv_volume / 1e6, alpha=0.3, color='blue',
                label='Reservoir Volume')
ax.plot(np.arange(N+1) * dt, rv_volume / 1e6, 'b-', lw=2)
ax.axhline(40, color='orange', ls='--', lw=1.5, label='Flood Control Level (40 Mm3)')
ax.axhline(50, color='red', ls=':', lw=1.5, label='Max Capacity (50 Mm3)')
ax.set_ylabel('Volume (Mm3)', fontsize=11, color='blue')
ax3 = ax.twinx()
ax3.step(time_h, rv_release / 3600, 'r-', lw=1.5, where='post', label='Release (m3/s)')
ax3.set_ylabel('Release (m3/s)', fontsize=11, color='red')
ax3.legend(fontsize=9, loc='upper right')
ax.legend(fontsize=9, loc='upper left')
ax.set_title('Reservoir Water Balance: Storage & Flood Release',
             fontsize=13, fontweight='bold')
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Flow at Key Nodes
ax = axes[2]
ax.plot(time_h, node_outflow["R1"] / 3600, 'g-', lw=2, label='R1 Upper River Outflow')
ax.plot(time_h, node_outflow["R2"] / 3600, 'b-', lw=2, label='R2 Lower River Outflow')
ax.plot(time_h, node_outflow["P1"] / 3600, 'r--', lw=2, label='P1 Pump Station Discharge')
ax.axhline(15, color='red', ls=':', lw=1, label='Pump Capacity (15 m3/s)')
ax.fill_between(time_h, node_outflow["P1"] / 3600, node_outflow["R2"] / 3600,
                where=node_outflow["R2"] > node_outflow["P1"],
                alpha=0.2, color='red', label='Pump Overflow Risk')
ax.set_xlabel('Time (hours)', fontsize=11)
ax.set_ylabel('Flow (m3/s)', fontsize=11)
ax.set_title('Flow Propagation Through Topological Network',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "mbd_topology_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: mbd_topology_sim.png")

# Markdown KPI table
md = [
    "| Node | Type | Peak Inflow (m3/s) | Peak Outflow (m3/s) | Assessment |",
    "|:-----|:-----|:-------------------|:--------------------|:-----------|",
]
for eid in topo_order:
    e = net.entities[eid]
    pi = np.max(node_inflow[eid]) / 3600 if np.any(node_inflow[eid]) else 0
    po = np.max(node_outflow[eid]) / 3600
    note = ""
    if e.etype == "Reservoir":
        note = f"Peak Vol={np.max(rv_volume)/1e6:.1f} Mm3"
    elif e.etype == "PumpStation" and po >= 15 * 0.99:
        note = "Near Capacity!"
    md.append(f"| {e.name} | {e.etype} | {pi:.1f} | {po:.1f} | {note} |")

with open(os.path.join(output_dir, "mbd_kpi_table.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
for line in md:
    print(line)
