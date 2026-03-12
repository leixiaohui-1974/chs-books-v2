"""
书名：《人工智能与水利水电工程》
章节：第6章 Agent与MCP协议（6.1 基本概念与理论框架）
功能：构建“感知-推理-行动-协议-护栏”仿真，比较 Reactive、MCP、MCP+Guardrail 三种策略的KPI。
"""

import numpy as np
from scipy.special import expit
from scipy.optimize import minimize_scalar
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# ========================= 关键参数（教学可调） =========================
RANDOM_SEED = 20260307
N_STEPS = 72                 # 单次仿真时间步
N_EVAL_EPISODES = 120        # 评估轮数
N_TUNE_EPISODES = 36         # Guardrail参数寻优轮数

BASE_INFLOW = 320.0          # 基准入流
INFLOW_SIGMA = 42.0          # 入流波动
DEMAND_BASE = 290.0          # 基准下游需水
DEMAND_SIGMA = 28.0          # 需水波动

INIT_LEVEL = 92.0            # 初始库水位
LEVEL_TARGET = 95.0          # 目标水位
LEVEL_MIN = 88.0             # 安全下限
LEVEL_MAX = 102.0            # 安全上限
STORAGE_FACTOR = 35.0        # 库容-流量换算系数

MIN_RELEASE = 150.0          # 最小下泄
MAX_RELEASE = 520.0          # 最大下泄
MAX_RAMP = 55.0              # 相邻时刻最大变幅（护栏约束）

FLOOD_ALERT_INFLOW = 360.0   # 洪水警戒入流
FLOOD_SCALE = 24.0           # 风险映射尺度
LEVEL_SCALE = 3.0            # 水位映射尺度
RISK_RELEASE_GAIN = 120.0    # 风险项对理想下泄的增益
LEVEL_FEEDBACK_GAIN = 16.0   # 水位反馈增益

REACTIVE_GAIN = 14.0         # 反应式控制增益
OPT_RISK_GAIN = 128.0        # MCP优化器风险增益
OPT_LEVEL_GAIN = 18.0        # MCP优化器水位增益

OBS_LEVEL_STD = 0.85         # 观测噪声
PROCESS_LEVEL_STD = 0.20     # 过程噪声
FORECAST_NOISE_STD = 20.0    # 预测工具噪声
FALLBACK_NOISE_STD = 35.0    # 失败回退噪声

BASE_AGENT_LAT_MS = 22.0     # Agent本体时延
FORECAST_LAT_MS = 26.0       # 预测工具时延
OPT_LAT_MS = 35.0            # 优化工具时延

MCP_SUCCESS_PROB_FORECAST = 0.93  # MCP预测调用成功率
MCP_SUCCESS_PROB_OPT = 0.90       # MCP优化调用成功率

LATENCY_REF_MS = 130.0       # 效用中的时延归一化参考
SAVE_FIG = True
SHOW_FIG = True
FIG_NAME = "ch06_agent_mcp_simulation.png"

STRATEGIES = ["Reactive", "MCP", "MCP+Guardrail"]


def generate_series(rng, n_steps):
    """生成入流与需水序列。"""
    inflow = np.zeros(n_steps)
    inflow[0] = BASE_INFLOW + rng.normal(0, INFLOW_SIGMA)
    for t in range(1, n_steps):
        seasonal = 20.0 * np.sin(2 * np.pi * t / 24)
        shock = rng.normal(0, INFLOW_SIGMA)
        inflow[t] = 0.76 * inflow[t - 1] + 0.24 * (BASE_INFLOW + seasonal) + 0.25 * shock

    demand = (
        DEMAND_BASE
        + 18.0 * np.sin(2 * np.pi * (np.arange(n_steps) + 6) / 24)
        + rng.normal(0, DEMAND_SIGMA, n_steps)
    )
    return np.clip(inflow, 120, 620), np.clip(demand, 120, 500)


def ideal_release(level, inflow, demand):
    """理想策略：作为误差评估参考，不参与实际控制。"""
    risk = expit((inflow - FLOOD_ALERT_INFLOW) / FLOOD_SCALE + (level - LEVEL_TARGET) / LEVEL_SCALE)
    rel = demand + RISK_RELEASE_GAIN * risk + LEVEL_FEEDBACK_GAIN * (level - LEVEL_TARGET)
    return float(np.clip(rel, MIN_RELEASE, MAX_RELEASE))


def mean_ci95(values):
    """均值与95%置信区间。"""
    arr = np.asarray(values, dtype=float)
    if len(arr) <= 1:
        return float(np.mean(arr)), 0.0
    return float(np.mean(arr)), float(1.96 * stats.sem(arr))


def safe_mean_ci95(values):
    """空样本安全处理。"""
    if len(values) == 0:
        return np.nan, np.nan
    return mean_ci95(values)


def run_episode(strategy, seed, guardrail_lambda=1.0, record=False):
    """运行单轮仿真。"""
    rng = np.random.default_rng(seed)
    inflow, demand = generate_series(rng, N_STEPS)

    level = INIT_LEVEL
    prev_release = DEMAND_BASE

    rmse_terms, violation_flags, satisfaction, latencies = [], [], [], []
    call_count, success_count = 0, 0

    rel_hist, level_hist, ideal_hist = [], [level], []

    for t in range(N_STEPS):
        i_t = float(inflow[t])
        d_t = float(demand[t])
        ideal = ideal_release(level, i_t, d_t)
        ideal_hist.append(ideal)

        level_obs = level + rng.normal(0, OBS_LEVEL_STD)
        latency = BASE_AGENT_LAT_MS + rng.normal(0, 1.2)

        if strategy == "Reactive":
            release = d_t + REACTIVE_GAIN * (level_obs - LEVEL_TARGET)
        else:
            # MCP协议下：调用预测工具 + 优化工具
            call_count += 2

            latency += max(1.0, rng.lognormal(np.log(FORECAST_LAT_MS), 0.22))
            if rng.random() < MCP_SUCCESS_PROB_FORECAST:
                success_count += 1
                base_pred = inflow[t - 1] if t > 0 else i_t
                pred_inflow = 0.74 * i_t + 0.26 * base_pred + rng.normal(0, FORECAST_NOISE_STD)
            else:
                pred_inflow = i_t + rng.normal(0, FALLBACK_NOISE_STD)

            latency += max(1.0, rng.lognormal(np.log(OPT_LAT_MS), 0.25))
            if rng.random() < MCP_SUCCESS_PROB_OPT:
                success_count += 1
                pred_risk = expit(
                    (pred_inflow - FLOOD_ALERT_INFLOW) / FLOOD_SCALE
                    + (level_obs - LEVEL_TARGET) / LEVEL_SCALE
                )
                release = d_t + OPT_RISK_GAIN * pred_risk + OPT_LEVEL_GAIN * (level_obs - LEVEL_TARGET)
            else:
                release = d_t + REACTIVE_GAIN * (level_obs - LEVEL_TARGET)

            # Guardrail：协议层安全边界，防止动作越界与跳变
            if strategy == "MCP+Guardrail":
                release = np.clip(release, MIN_RELEASE, MAX_RELEASE)
                projected = level + (i_t - release) / STORAGE_FACTOR

                if projected > LEVEL_MAX:
                    required = i_t - STORAGE_FACTOR * (LEVEL_MAX - level)
                    release = (1 - guardrail_lambda) * release + guardrail_lambda * required
                elif projected < LEVEL_MIN:
                    required = i_t - STORAGE_FACTOR * (LEVEL_MIN - level)
                    release = (1 - guardrail_lambda) * release + guardrail_lambda * required

                release = np.clip(release, prev_release - MAX_RAMP, prev_release + MAX_RAMP)

        release = float(np.clip(release, MIN_RELEASE, MAX_RELEASE))
        next_level = level + (i_t - release) / STORAGE_FACTOR + rng.normal(0, PROCESS_LEVEL_STD)

        violation = float((next_level < LEVEL_MIN) or (next_level > LEVEL_MAX))
        sat = float(np.clip(1.0 - abs(release - d_t) / (d_t + 1e-6), 0.0, 1.0))

        rmse_terms.append((release - ideal) ** 2)
        violation_flags.append(violation)
        satisfaction.append(sat)
        latencies.append(max(1.0, latency))

        rel_hist.append(release)
        level_hist.append(next_level)

        level = next_level
        prev_release = release

    rmse = float(np.sqrt(np.mean(rmse_terms)))
    vio = float(np.mean(violation_flags))
    sat = float(np.mean(satisfaction))
    lat = float(np.mean(latencies))
    mcp_success = (success_count / call_count) if call_count > 0 else np.nan

    # 综合效用：质量、风险、成本折中
    utility = (
        0.40 * (1.0 - vio)
        + 0.35 * sat
        + 0.20 * (1.0 - rmse / MAX_RELEASE)
        - 0.05 * (lat / LATENCY_REF_MS)
    )

    metrics = {
        "rmse": rmse,
        "violation": vio,
        "satisfaction": sat,
        "mcp_success": mcp_success,
        "latency": lat,
        "utility": utility,
    }

    traj = None
    if record:
        traj = {
            "inflow": inflow,
            "demand": demand,
            "release": np.array(rel_hist),
            "level": np.array(level_hist),
            "ideal_release": np.array(ideal_hist),
        }

    return metrics, traj


# ========================= 1) 先用scipy寻优Guardrail强度 =========================
val_seeds = np.arange(7000, 7000 + N_TUNE_EPISODES)

def tune_objective(lmbd):
    vals = []
    for s in val_seeds:
        m, _ = run_episode("MCP+Guardrail", int(s), guardrail_lambda=float(lmbd), record=False)
        vals.append(m["utility"])
    return -float(np.mean(vals))

res = minimize_scalar(
    tune_objective,
    bounds=(0.0, 1.5),
    method="bounded",
    options={"maxiter": 40},
)
best_lambda = float(res.x)

# ========================= 2) 正式评估三种策略 =========================
eval_seeds = np.arange(9000, 9000 + N_EVAL_EPISODES)
summary, per_episode_points, rep_trajs = {}, {}, {}

for strategy in STRATEGIES:
    metrics_list = []
    points = {"latency": [], "violation": []}

    for idx, s in enumerate(eval_seeds):
        m, tr = run_episode(strategy, int(s), guardrail_lambda=best_lambda, record=(idx == 0))
        metrics_list.append(m)
        points["latency"].append(m["latency"])
        points["violation"].append(m["violation"])
        if tr is not None:
            rep_trajs[strategy] = tr

    mcp_vals = [m["mcp_success"] for m in metrics_list if not np.isnan(m["mcp_success"])]
    summary[strategy] = {
        "rmse": mean_ci95([m["rmse"] for m in metrics_list]),
        "violation": mean_ci95([m["violation"] for m in metrics_list]),
        "satisfaction": mean_ci95([m["satisfaction"] for m in metrics_list]),
        "mcp_success": safe_mean_ci95(mcp_vals),
        "latency": mean_ci95([m["latency"] for m in metrics_list]),
        "utility": mean_ci95([m["utility"] for m in metrics_list]),
    }
    per_episode_points[strategy] = points

# ========================= 3) 打印KPI结果表格 =========================
print("\nAgent-MCP仿真 KPI 结果（均值±95%CI）")
header = f"{'策略':<14} | {'RMSE':>12} | {'违规率':>12} | {'满足率':>12} | {'MCP成功率':>14} | {'时延ms':>12} | {'效用':>10}"
print("-" * len(header))
print(header)
print("-" * len(header))

def fmt(v):
    return f"{v[0]:.3f}±{v[1]:.3f}"

for strategy in STRATEGIES:
    row = summary[strategy]
    mcp_txt = "-" if strategy == "Reactive" else fmt(row["mcp_success"])
    print(
        f"{strategy:<14} | {fmt(row['rmse']):>12} | {fmt(row['violation']):>12} | "
        f"{fmt(row['satisfaction']):>12} | {mcp_txt:>14} | {fmt(row['latency']):>12} | {fmt(row['utility']):>10}"
    )

print("-" * len(header))
print(f"Guardrail最优强度 lambda = {best_lambda:.3f} （由 scipy.optimize.minimize_scalar 求得）")

# ========================= 4) 生成matplotlib图 =========================
x = np.arange(N_STEPS)
fig, axes = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(2, 2, figsize=(13, 8))

# 图1：下泄决策对比
ax = axes[0, 0]
ax.plot(x, rep_trajs["Reactive"]["ideal_release"], "k--", lw=2, label="理想下泄")
for strategy, c in zip(STRATEGIES, ["tab:blue", "tab:orange", "tab:green"]):
    ax.plot(x, rep_trajs[strategy]["release"], color=c, alpha=0.9, label=strategy)
ax.set_title("单场景下泄决策对比")
ax.set_xlabel("时间步")
ax.set_ylabel("流量")
ax.grid(alpha=0.3)
ax.legend()

# 图2：库水位轨迹与安全边界
ax = axes[0, 1]
for strategy, c in zip(STRATEGIES, ["tab:blue", "tab:orange", "tab:green"]):
    ax.plot(np.arange(N_STEPS + 1), rep_trajs[strategy]["level"], color=c, label=strategy)
ax.axhline(LEVEL_MIN, color="red", ls="--", lw=1.5, label="安全下限")
ax.axhline(LEVEL_MAX, color="purple", ls="--", lw=1.5, label="安全上限")
ax.set_title("单场景库水位轨迹")
ax.set_xlabel("时间步")
ax.set_ylabel("水位")
ax.grid(alpha=0.3)
ax.legend()

# 图3：综合效用柱状图
ax = axes[1, 0]
util_means = [summary[s]["utility"][0] for s in STRATEGIES]
util_cis = [summary[s]["utility"][1] for s in STRATEGIES]
ax.bar(STRATEGIES, util_means, yerr=util_cis, capsize=4, color=["tab:blue", "tab:orange", "tab:green"])
ax.set_title("综合效用对比")
ax.set_ylabel("Utility")
ax.grid(axis="y", alpha=0.3)

# 图4：时延-违规率散点
ax = axes[1, 1]
for strategy, c in zip(STRATEGIES, ["tab:blue", "tab:orange", "tab:green"]):
    ax.scatter(
        per_episode_points[strategy]["latency"],
        per_episode_points[strategy]["violation"],
        s=18,
        alpha=0.55,
        color=c,
        label=strategy,
    )
ax.set_title("时延-安全违规率散点")
ax.set_xlabel("平均时延 (ms)")
ax.set_ylabel("违规率")
ax.grid(alpha=0.3)
ax.legend()

fig.suptitle("《人工智能与水利水电工程》6.1 Agent与MCP协议仿真", fontsize=13)
fig.tight_layout()

if SAVE_FIG:
    plt.savefig(FIG_NAME, dpi=160)
    print(f"图像已保存：{FIG_NAME}")

if SHOW_FIG:
    # plt.show()  # 禁用弹窗
else:
    plt.close(fig)
