"""
Ch08: MCP Schema Guardrail — LLM Hallucination vs Schema-Constrained Output
Simulate how strict MCP schema validation prevents LLM from generating
physically impossible water control commands.
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

# ============ Physical Constraints (MCP Schema) ============
SCHEMA = {
    "gate_opening": {"min": 0.0, "max": 1.0, "unit": "fraction", "type": "float"},
    "pump_speed": {"min": 0, "max": 1500, "unit": "rpm", "type": "int"},
    "release_flow": {"min": 0.0, "max": 500.0, "unit": "m3/s", "type": "float"},
    "target_level": {"min": 145.0, "max": 175.0, "unit": "m", "type": "float"},
}

# ============ Simulate LLM Outputs ============
N_queries = 100  # 100 user queries to the hydro-LLM

# Mode A: No schema (raw LLM output — may hallucinate)
# LLM sometimes outputs correct values, sometimes wildly wrong
raw_outputs = []
for i in range(N_queries):
    out = {}
    # Gate: mostly correct, 15% chance of hallucination
    if np.random.random() < 0.15:
        out["gate_opening"] = np.random.choice([1.5, -0.2, 2.0, 999])  # impossible
    else:
        out["gate_opening"] = round(np.random.uniform(0.0, 1.0), 2)

    # Pump: 20% chance of hallucination (negative, too high, or string-like)
    if np.random.random() < 0.20:
        out["pump_speed"] = np.random.choice([-500, 3000, 99999, 0])
    else:
        out["pump_speed"] = int(np.random.uniform(0, 1500))

    # Release: 10% chance of absurd values
    if np.random.random() < 0.10:
        out["release_flow"] = np.random.choice([5000, -100, 1e6])
    else:
        out["release_flow"] = round(np.random.uniform(0, 500), 1)

    # Level: 12% chance of impossible target
    if np.random.random() < 0.12:
        out["target_level"] = np.random.choice([200, 100, 0, 999])
    else:
        out["target_level"] = round(np.random.uniform(145, 175), 1)

    raw_outputs.append(out)

# Mode B: Schema-validated (MCP enforced)
def validate_and_clamp(output, schema):
    """MCP schema validation: reject or clamp invalid values."""
    validated = {}
    violations = []
    for key, spec in schema.items():
        val = output.get(key, None)
        if val is None:
            violations.append((key, "MISSING", None))
            validated[key] = (spec["min"] + spec["max"]) / 2  # safe default
        elif val < spec["min"] or val > spec["max"]:
            violations.append((key, "OUT_OF_RANGE", val))
            validated[key] = np.clip(val, spec["min"], spec["max"])
        else:
            validated[key] = val
    return validated, violations

validated_outputs = []
all_violations = []
for out in raw_outputs:
    v_out, viols = validate_and_clamp(out, SCHEMA)
    validated_outputs.append(v_out)
    all_violations.append(viols)

# ============ Analyze Results ============
fields = ["gate_opening", "pump_speed", "release_flow", "target_level"]
field_labels = ["Gate Opening", "Pump Speed (rpm)", "Release (m3/s)", "Target Level (m)"]

raw_valid = {f: 0 for f in fields}
raw_dangerous = {f: 0 for f in fields}
schema_safe = {f: 0 for f in fields}

for i in range(N_queries):
    for f in fields:
        v = raw_outputs[i][f]
        s = SCHEMA[f]
        if s["min"] <= v <= s["max"]:
            raw_valid[f] += 1
        else:
            raw_dangerous[f] += 1
        # Schema output always valid
        schema_safe[f] += 1

total_raw_violations = sum(raw_dangerous[f] for f in fields)
total_queries_with_violation = sum(1 for viols in all_violations if len(viols) > 0)

print("=" * 65)
print(f"{'Field':<20}{'Raw Valid':>12}{'Raw Dangerous':>15}{'Schema Safe':>13}")
print("-" * 65)
for f, label in zip(fields, field_labels):
    print(f"{label:<20}{raw_valid[f]:>12d}{raw_dangerous[f]:>15d}{schema_safe[f]:>13d}")
print("-" * 65)
print(f"{'TOTAL':<20}{sum(raw_valid.values()):>12d}{total_raw_violations:>15d}{N_queries*4:>13d}")
print(f"\nQueries with >= 1 violation: {total_queries_with_violation}/{N_queries} ({total_queries_with_violation}%)")
print(f"Without MCP: {total_raw_violations} dangerous commands would reach physical actuators!")
print(f"With MCP: 0 dangerous commands pass through (100% interception)")

# ============ Simulate Physical Consequence ============
# What happens if unchecked commands reach a reservoir?
reservoir_level = np.zeros(N_queries + 1)
reservoir_level[0] = 160.0  # initial level (m)
reservoir_level_safe = np.zeros(N_queries + 1)
reservoir_level_safe[0] = 160.0

flood_line = 175.0
dead_line = 145.0

for i in range(N_queries):
    # Raw mode: use LLM output directly
    release = raw_outputs[i]["release_flow"]
    inflow = np.random.uniform(50, 200)  # random inflow
    area = 1e6  # reservoir area m2
    dh = (inflow - release) * 3600 / area  # level change per hour
    reservoir_level[i + 1] = reservoir_level[i] + dh
    # No safety clamp in raw mode

    # Schema mode: use validated output
    release_safe = validated_outputs[i]["release_flow"]
    dh_safe = (inflow - release_safe) * 3600 / area
    reservoir_level_safe[i + 1] = np.clip(
        reservoir_level_safe[i] + dh_safe, dead_line, flood_line + 5)

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# Panel 1: Raw vs Schema command comparison (4 subfields)
ax = axes[0]
x = np.arange(len(fields))
w = 0.25
bars1 = ax.bar(x - w, [raw_valid[f] for f in fields], w, color='green', alpha=0.7,
               label='Raw: Valid Commands')
bars2 = ax.bar(x, [raw_dangerous[f] for f in fields], w, color='red', alpha=0.7,
               label='Raw: Dangerous Commands')
bars3 = ax.bar(x + w, [schema_safe[f] for f in fields], w, color='blue', alpha=0.7,
               label='Schema: All Safe')
ax.set_xticks(x)
ax.set_xticklabels(field_labels, fontsize=10)
ax.set_ylabel('Command Count (out of 100)', fontsize=11)
ax.set_title('MCP Schema Guardrail: LLM Hallucination Interception Rate',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4, axis='y')

# Panel 2: Time series of gate_opening commands
ax = axes[1]
raw_gate = [raw_outputs[i]["gate_opening"] for i in range(N_queries)]
safe_gate = [validated_outputs[i]["gate_opening"] for i in range(N_queries)]
ax.scatter(range(N_queries), raw_gate, c='red', s=15, alpha=0.6, label='Raw LLM Output')
ax.plot(range(N_queries), safe_gate, 'g-', lw=1.5, alpha=0.8, label='Schema-Validated')
ax.axhline(0, color='black', ls='--', lw=1)
ax.axhline(1, color='black', ls='--', lw=1)
ax.fill_between(range(N_queries), 1, max(raw_gate) * 1.1, alpha=0.1, color='red',
                label='Physically Impossible Zone')
ax.fill_between(range(N_queries), min(raw_gate) * 1.1, 0, alpha=0.1, color='red')
ax.set_ylabel('Gate Opening (0-1)', fontsize=11)
ax.set_title('Gate Opening Commands: Raw LLM vs Schema-Constrained',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Reservoir level consequence
ax = axes[2]
hours = np.arange(N_queries + 1)
ax.plot(hours, reservoir_level, 'r-', lw=2, label='No Schema (Raw LLM)')
ax.plot(hours, reservoir_level_safe, 'g-', lw=2, label='MCP Schema Protected')
ax.axhline(flood_line, color='red', ls='--', lw=1.5, label=f'Flood Line ({flood_line}m)')
ax.axhline(dead_line, color='brown', ls='--', lw=1.5, label=f'Dead Level ({dead_line}m)')
ax.fill_between(hours, flood_line, max(max(reservoir_level), flood_line + 5),
                alpha=0.15, color='red', label='Overflow Disaster Zone')
ax.set_xlabel('Time Step (hours)', fontsize=11)
ax.set_ylabel('Reservoir Level (m)', fontsize=11)
ax.set_title('Physical Consequence: Reservoir Level Under Raw vs Schema-Protected Control',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, ls='--', alpha=0.4)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "mcp_guardrail_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: mcp_guardrail_sim.png")

# Markdown table
md = [
    "| Metric | Without MCP | With MCP | Assessment |",
    "|:-------|:------------|:---------|:-----------|",
    f"| Dangerous Commands | {total_raw_violations} | 0 | 100% interception |",
    f"| Queries with Violations | {total_queries_with_violation}% | 0% | Schema eliminates risk |",
    f"| Gate Hallucinations | {raw_dangerous['gate_opening']} | 0 | Clamped to [0,1] |",
    f"| Pump Hallucinations | {raw_dangerous['pump_speed']} | 0 | Clamped to [0,1500] |",
    f"| Release Hallucinations | {raw_dangerous['release_flow']} | 0 | Clamped to [0,500] |",
    f"| Level Hallucinations | {raw_dangerous['target_level']} | 0 | Clamped to [145,175] |",
]
with open(os.path.join(output_dir, "mcp_kpi_table.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
for line in md:
    print(line)
