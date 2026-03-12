"""
Ch09: Skill Workflow — Forecast Review Skill vs Ad-hoc LLM
Compare deterministic Skill-based forecast review pipeline
with unstructured LLM ad-hoc analysis on the same set of anomalous forecasts.
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

# ============ Generate Forecast Scenarios ============
N_cases = 50  # 50 forecast events to review

# Ground truth labels
# 0 = normal, 1 = model overestimate, 2 = sensor drift, 3 = true extreme event
labels = np.random.choice([0, 1, 2, 3], size=N_cases, p=[0.50, 0.20, 0.15, 0.15])

# Forecast data for each case
cases = []
for i in range(N_cases):
    case = {
        "id": i + 1,
        "label": labels[i],
        "radar_peak_mm": np.random.uniform(20, 80),
        "nwp_peak_mm": 0,
        "station_peak_mm": 0,
        "model_peak_flow": 0,
        "observed_flow": 0,
    }

    if labels[i] == 0:  # Normal: all sources agree
        base = case["radar_peak_mm"]
        case["nwp_peak_mm"] = base * np.random.uniform(0.85, 1.15)
        case["station_peak_mm"] = base * np.random.uniform(0.90, 1.10)
        case["model_peak_flow"] = base * 2.5 * np.random.uniform(0.9, 1.1)
        case["observed_flow"] = case["model_peak_flow"] * np.random.uniform(0.85, 1.15)
    elif labels[i] == 1:  # Model overestimate: model >> observed
        base = case["radar_peak_mm"]
        case["nwp_peak_mm"] = base * np.random.uniform(0.85, 1.15)
        case["station_peak_mm"] = base * np.random.uniform(0.90, 1.10)
        case["model_peak_flow"] = base * 2.5 * np.random.uniform(1.8, 3.0)  # inflated
        case["observed_flow"] = base * 2.5 * np.random.uniform(0.7, 1.0)
    elif labels[i] == 2:  # Sensor drift: station disagrees with radar/NWP
        base = case["radar_peak_mm"]
        case["nwp_peak_mm"] = base * np.random.uniform(0.85, 1.15)
        case["station_peak_mm"] = base * np.random.uniform(0.3, 0.5)  # drifted low
        case["model_peak_flow"] = base * 2.5 * np.random.uniform(0.9, 1.1)
        case["observed_flow"] = case["model_peak_flow"] * np.random.uniform(0.85, 1.15)
    else:  # True extreme: all high, consistent
        case["radar_peak_mm"] = np.random.uniform(80, 150)
        base = case["radar_peak_mm"]
        case["nwp_peak_mm"] = base * np.random.uniform(0.90, 1.10)
        case["station_peak_mm"] = base * np.random.uniform(0.85, 1.15)
        case["model_peak_flow"] = base * 2.5 * np.random.uniform(0.95, 1.05)
        case["observed_flow"] = case["model_peak_flow"] * np.random.uniform(0.90, 1.10)

    cases.append(case)


# ============ Skill-based Review (Deterministic SOP) ============
def skill_review(case):
    """
    Deterministic Skill: 3-source cross-validation + model bias check.
    Returns: (diagnosis, confidence)
    """
    radar = case["radar_peak_mm"]
    nwp = case["nwp_peak_mm"]
    station = case["station_peak_mm"]
    model_q = case["model_peak_flow"]
    obs_q = case["observed_flow"]

    # Step 1: Cross-validate rainfall sources
    rain_sources = [radar, nwp, station]
    rain_mean = np.mean(rain_sources)
    rain_cv = np.std(rain_sources) / max(rain_mean, 0.01)

    # Step 2: Check station drift
    station_ratio = station / max(radar, 0.01)

    # Step 3: Check model bias
    model_ratio = model_q / max(obs_q, 0.01)

    # Decision tree (deterministic SOP)
    if station_ratio < 0.6:
        return 2, 0.90  # Sensor drift
    elif model_ratio > 1.5:
        return 1, 0.85  # Model overestimate
    elif radar > 70 and rain_cv < 0.15:
        return 3, 0.88  # True extreme
    else:
        return 0, 0.92  # Normal


# ============ Ad-hoc LLM Review (Probabilistic) ============
def adhoc_llm_review(case):
    """
    Simulated ad-hoc LLM: sometimes correct, sometimes misclassifies.
    No systematic SOP, relies on pattern matching with noise.
    """
    true_label = case["label"]

    # LLM has ~70% base accuracy but degrades on edge cases
    if true_label == 0:  # Normal: LLM usually gets right
        if np.random.random() < 0.80:
            return 0, np.random.uniform(0.6, 0.9)
        else:
            return np.random.choice([1, 3]), np.random.uniform(0.4, 0.7)
    elif true_label == 1:  # Model overestimate: LLM often misses
        if np.random.random() < 0.55:
            return 1, np.random.uniform(0.5, 0.8)
        else:
            return np.random.choice([0, 3]), np.random.uniform(0.3, 0.6)
    elif true_label == 2:  # Sensor drift: LLM rarely detects
        if np.random.random() < 0.40:
            return 2, np.random.uniform(0.4, 0.7)
        else:
            return np.random.choice([0, 1]), np.random.uniform(0.3, 0.5)
    else:  # True extreme: LLM sometimes panics
        if np.random.random() < 0.65:
            return 3, np.random.uniform(0.5, 0.8)
        else:
            return np.random.choice([0, 1]), np.random.uniform(0.3, 0.6)


# ============ Run Both Modes ============
skill_results = []
llm_results = []
for case in cases:
    s_diag, s_conf = skill_review(case)
    l_diag, l_conf = adhoc_llm_review(case)
    skill_results.append({"diag": s_diag, "conf": s_conf, "correct": s_diag == case["label"]})
    llm_results.append({"diag": l_diag, "conf": l_conf, "correct": l_diag == case["label"]})

# ============ KPI ============
categories = ["Normal", "Model Overestimate", "Sensor Drift", "True Extreme"]
skill_acc = sum(r["correct"] for r in skill_results) / N_cases * 100
llm_acc = sum(r["correct"] for r in llm_results) / N_cases * 100

# Per-category accuracy
skill_cat_acc = {}
llm_cat_acc = {}
for cat_id, cat_name in enumerate(categories):
    mask = labels == cat_id
    n = np.sum(mask)
    if n > 0:
        skill_cat_acc[cat_name] = sum(
            skill_results[i]["correct"] for i in range(N_cases) if labels[i] == cat_id
        ) / n * 100
        llm_cat_acc[cat_name] = sum(
            llm_results[i]["correct"] for i in range(N_cases) if labels[i] == cat_id
        ) / n * 100

# False alarm: diagnosed as extreme (3) but actually normal (0)
skill_false_alarm = sum(
    1 for i in range(N_cases)
    if skill_results[i]["diag"] == 3 and labels[i] == 0
)
llm_false_alarm = sum(
    1 for i in range(N_cases)
    if llm_results[i]["diag"] == 3 and labels[i] == 0
)

# Missed extreme: actually extreme (3) but diagnosed as normal (0)
skill_missed = sum(
    1 for i in range(N_cases)
    if skill_results[i]["diag"] == 0 and labels[i] == 3
)
llm_missed = sum(
    1 for i in range(N_cases)
    if llm_results[i]["diag"] == 0 and labels[i] == 3
)

print("=" * 60)
print(f"{'Metric':<30}{'Skill SOP':>14}{'Ad-hoc LLM':>14}")
print("-" * 60)
print(f"{'Overall Accuracy':<30}{skill_acc:>13.1f}%{llm_acc:>13.1f}%")
for cat in categories:
    print(f"  {cat:<28}{skill_cat_acc.get(cat,0):>13.1f}%{llm_cat_acc.get(cat,0):>13.1f}%")
print(f"{'False Alarms (extreme)':<30}{skill_false_alarm:>14d}{llm_false_alarm:>14d}")
print(f"{'Missed Extremes':<30}{skill_missed:>14d}{llm_missed:>14d}")
print(f"{'Avg Confidence':<30}{np.mean([r['conf'] for r in skill_results]):>13.2f}{np.mean([r['conf'] for r in llm_results]):>13.2f}")

# ============ Plot ============
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# Panel 1: Per-category accuracy comparison
ax = axes[0]
x = np.arange(len(categories))
w = 0.3
ax.bar(x - w/2, [skill_cat_acc.get(c, 0) for c in categories], w,
       color='green', alpha=0.7, label='Skill SOP (Deterministic)')
ax.bar(x + w/2, [llm_cat_acc.get(c, 0) for c in categories], w,
       color='red', alpha=0.7, label='Ad-hoc LLM (Probabilistic)')
ax.axhline(80, color='orange', ls='--', lw=1, label='Minimum Acceptable (80%)')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('Accuracy (%)', fontsize=11)
ax.set_ylim(0, 110)
ax.set_title('Forecast Review Accuracy by Anomaly Category',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, ls='--', alpha=0.4, axis='y')

# Panel 2: Confidence vs Correctness scatter
ax = axes[1]
for i in range(N_cases):
    color_s = 'green' if skill_results[i]["correct"] else 'red'
    color_l = 'blue' if llm_results[i]["correct"] else 'orange'
    ax.scatter(i, skill_results[i]["conf"], c=color_s, s=20, alpha=0.6,
              marker='o')
    ax.scatter(i, llm_results[i]["conf"], c=color_l, s=20, alpha=0.6,
              marker='x')
# Legend
ax.scatter([], [], c='green', marker='o', label='Skill Correct')
ax.scatter([], [], c='red', marker='o', label='Skill Wrong')
ax.scatter([], [], c='blue', marker='x', label='LLM Correct')
ax.scatter([], [], c='orange', marker='x', label='LLM Wrong')
ax.set_ylabel('Confidence Score', fontsize=11)
ax.set_xlabel('Case Index', fontsize=11)
ax.set_title('Confidence vs Correctness: Skill (circles) vs LLM (crosses)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, ncol=4, loc='lower right')
ax.grid(True, ls='--', alpha=0.4)

# Panel 3: Confusion summary — false alarms and missed extremes
ax = axes[2]
metrics = ['False Alarms\n(cry wolf)', 'Missed Extremes\n(deadly silence)',
           'Overall\nAccuracy (%)']
skill_vals = [skill_false_alarm, skill_missed, skill_acc]
llm_vals = [llm_false_alarm, llm_missed, llm_acc]
x = np.arange(len(metrics))
ax.bar(x - w/2, skill_vals, w, color='green', alpha=0.7, label='Skill SOP')
ax.bar(x + w/2, llm_vals, w, color='red', alpha=0.7, label='Ad-hoc LLM')
# Add value labels
for j in range(len(metrics)):
    ax.text(x[j] - w/2, skill_vals[j] + 0.5, f'{skill_vals[j]:.0f}',
            ha='center', fontsize=10, fontweight='bold', color='green')
    ax.text(x[j] + w/2, llm_vals[j] + 0.5, f'{llm_vals[j]:.0f}',
            ha='center', fontsize=10, fontweight='bold', color='red')
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=11)
ax.set_title('Critical Safety Metrics: False Alarms vs Missed Extremes',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, ls='--', alpha=0.4, axis='y')

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "skill_workflow_sim.png"), dpi=300, bbox_inches='tight')
print(f"\nFigure saved: skill_workflow_sim.png")

# Markdown table
md = [
    "| Metric | Skill SOP | Ad-hoc LLM | Assessment |",
    "|:-------|:----------|:-----------|:-----------|",
    f"| Overall Accuracy | {skill_acc:.0f}% | {llm_acc:.0f}% | Skill +{skill_acc-llm_acc:.0f}pp |",
    f"| Sensor Drift Detection | {skill_cat_acc.get('Sensor Drift',0):.0f}% | {llm_cat_acc.get('Sensor Drift',0):.0f}% | Skill dominant |",
    f"| False Alarms | {skill_false_alarm} | {llm_false_alarm} | Lower is better |",
    f"| Missed Extremes | {skill_missed} | {llm_missed} | 0 = perfect |",
]
with open(os.path.join(output_dir, "skill_kpi_table.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
for line in md:
    print(line)
