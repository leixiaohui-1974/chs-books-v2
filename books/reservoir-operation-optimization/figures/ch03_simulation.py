# -*- coding: utf-8 -*-
# ============================================================
# 教材《水库调度优化与决策》
# 第3章：多目标优化（NSGA-II）
# 功能：构建“供水缺水率-发电波动”双目标水库调度仿真与决策示例
# 依赖：numpy / scipy / matplotlib
# ============================================================

import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# ------------------------ 关键参数定义 ------------------------
SEED = 20260307                 # 随机种子，保证复现实验
N_YEARS = 3                     # 仿真年数
MONTHS_PER_YEAR = 12
N_MONTHS = N_YEARS * MONTHS_PER_YEAR

POP_SIZE = 80                   # 种群规模
N_GENERATIONS = 100             # 迭代代数
CROSSOVER_RATE = 0.9            # 交叉概率
MUTATION_RATE = 0.12            # 单基因变异概率

GENE_LOW = 0.60                 # 调度系数下界
GENE_HIGH = 1.40                # 调度系数上界

# 水库与水电参数（示例）
S_MIN = 180.0                   # 死库容（百万m3）
S_MAX = 620.0                   # 正常蓄水上限（百万m3）
S_INIT = 430.0                  # 初始库容（百万m3）
R_MIN = 20.0                    # 最小下泄（百万m3/月）
R_MAX = 130.0                   # 最大下泄（百万m3/月）
H_MIN = 22.0                    # 最小有效水头（m）
H_MAX = 55.0                    # 最大有效水头（m）
ETA = 0.87                      # 综合效率

# 月需水与基准入流（百万m3/月）
DEMAND_12 = np.array([70, 68, 72, 75, 82, 90, 96, 92, 86, 80, 76, 72], dtype=float)
INFLOW_BASE_12 = np.array([55, 52, 60, 78, 95, 130, 170, 160, 120, 92, 74, 60], dtype=float)

rng = np.random.default_rng(SEED)


def build_inflow_series():
    """用截断正态扰动构造季节性入流序列（体现 scipy 的应用）"""
    seasonal = np.tile(INFLOW_BASE_12, N_YEARS)
    # 扰动因子约束在[0.65, 1.45]
    a, b = (0.65 - 1.0) / 0.2, (1.45 - 1.0) / 0.2
    factor = stats.truncnorm.rvs(a, b, loc=1.0, scale=0.2, size=N_MONTHS, random_state=rng)
    return seasonal * factor


def simulate_reservoir(policy_12, inflow_series):
    """
    policy_12: 12个月调度系数，实际出库目标=系数*需水
    返回：目标函数值 + KPI + 过程序列
    """
    demand = np.tile(DEMAND_12, N_YEARS)

    storage = np.zeros(N_MONTHS + 1)
    release = np.zeros(N_MONTHS)
    spill = np.zeros(N_MONTHS)
    deficit = np.zeros(N_MONTHS)
    energy = np.zeros(N_MONTHS)  # 月发电量（GWh）

    storage[0] = S_INIT

    for t in range(N_MONTHS):
        m = t % 12

        # 1) 根据规则曲线给出目标出库
        target_release = policy_12[m] * demand[t]

        # 2) 可供出库水量：不低于死库容
        max_release_from_storage = max(0.0, storage[t] + inflow_series[t] - S_MIN)
        feasible_max_release = min(R_MAX, max_release_from_storage)

        # 3) 受最小下泄与可行上限共同约束
        r_t = np.clip(target_release, R_MIN, feasible_max_release)
        release[t] = r_t

        # 4) 缺水按“需水-实际供水”计算
        deficit[t] = max(0.0, demand[t] - r_t)

        # 5) 更新库容并计算弃水
        next_storage = storage[t] + inflow_series[t] - r_t
        if next_storage > S_MAX:
            spill[t] = next_storage - S_MAX
            next_storage = S_MAX
        if next_storage < S_MIN:
            # 理论上前面已约束，这里做数值保护
            next_storage = S_MIN
        storage[t + 1] = next_storage

        # 6) 估算月发电量：E=ρgVhη（单位换算到GWh）
        head = H_MIN + (storage[t] - S_MIN) / (S_MAX - S_MIN) * (H_MAX - H_MIN)
        energy[t] = 0.002725 * ETA * head * r_t

    # ------------------------ 目标函数 ------------------------
    deficit_ratio = deficit.sum() / demand.sum()                     # 目标1：缺水率最小
    power_cv = np.std(energy) / (np.mean(energy) + 1e-9)            # 目标2：发电波动最小

    # 期末库容偏差惩罚（约束处理）
    terminal_penalty = abs(storage[-1] - S_INIT) / (S_MAX - S_MIN)

    obj1 = deficit_ratio + 0.25 * terminal_penalty
    obj2 = power_cv + 0.25 * terminal_penalty

    kpi = {
        "deficit_ratio": deficit_ratio,
        "power_cv": power_cv,
        "annual_energy_gwh": energy.sum() / N_YEARS,
        "spill_ratio": spill.sum() / (inflow_series.sum() + 1e-9),
        "terminal_storage_dev": abs(storage[-1] - S_INIT),
    }

    traces = {
        "storage": storage,
        "release": release,
        "inflow": inflow_series,
        "energy": energy,
    }

    return np.array([obj1, obj2]), kpi, traces


def dominates(a, b):
    """判断个体a是否支配个体b（最小化问题）"""
    return np.all(a <= b) and np.any(a < b)


def fast_non_dominated_sort(objs):
    n = len(objs)
    dominated_set = [[] for _ in range(n)]
    dominate_count = np.zeros(n, dtype=int)
    fronts = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominates(objs[p], objs[q]):
                dominated_set[p].append(q)
            elif dominates(objs[q], objs[p]):
                dominate_count[p] += 1
        if dominate_count[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in dominated_set[p]:
                dominate_count[q] -= 1
                if dominate_count[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    fronts.pop()
    rank = np.zeros(n, dtype=int)
    for i, front in enumerate(fronts):
        for idx in front:
            rank[idx] = i
    return fronts, rank


def crowding_distance(objs, front):
    """计算某一front中的拥挤距离"""
    if len(front) == 0:
        return {}
    if len(front) == 1:
        return {front[0]: np.inf}

    distance = np.zeros(len(front), dtype=float)
    front_objs = objs[front]
    n_obj = front_objs.shape[1]

    for m in range(n_obj):
        order = np.argsort(front_objs[:, m])
        distance[order[0]] = np.inf
        distance[order[-1]] = np.inf

        vmin = front_objs[order[0], m]
        vmax = front_objs[order[-1], m]
        if vmax - vmin < 1e-12:
            continue

        for i in range(1, len(front) - 1):
            distance[order[i]] += (front_objs[order[i + 1], m] - front_objs[order[i - 1], m]) / (vmax - vmin)

    return {front[i]: distance[i] for i in range(len(front))}


def tournament_selection(pop, rank, crowd_map, n_select):
    """锦标赛选择：先比较等级，再比较拥挤距离"""
    selected_idx = []
    n = len(pop)
    for _ in range(n_select):
        i, j = rng.integers(0, n, size=2)
        if rank[i] < rank[j]:
            winner = i
        elif rank[i] > rank[j]:
            winner = j
        else:
            winner = i if crowd_map.get(i, 0.0) > crowd_map.get(j, 0.0) else j
        selected_idx.append(winner)
    return pop[selected_idx]


def crossover(p1, p2):
    """算术交叉"""
    if rng.random() > CROSSOVER_RATE:
        return p1.copy(), p2.copy()
    alpha = rng.random(len(p1))
    c1 = alpha * p1 + (1 - alpha) * p2
    c2 = alpha * p2 + (1 - alpha) * p1
    return np.clip(c1, GENE_LOW, GENE_HIGH), np.clip(c2, GENE_LOW, GENE_HIGH)


def mutate(child):
    """高斯变异"""
    child = child.copy()
    mask = rng.random(len(child)) < MUTATION_RATE
    if np.any(mask):
        child[mask] += rng.normal(0, 0.08, size=np.sum(mask))
    return np.clip(child, GENE_LOW, GENE_HIGH)


def evaluate_population(pop, inflow_series):
    objs = np.zeros((len(pop), 2))
    for i, indiv in enumerate(pop):
        objs[i], _, _ = simulate_reservoir(indiv, inflow_series)
    return objs


def make_offspring(pop, rank, crowd_map):
    mating_pool = tournament_selection(pop, rank, crowd_map, len(pop))
    children = []
    for i in range(0, len(mating_pool), 2):
        p1 = mating_pool[i]
        p2 = mating_pool[(i + 1) % len(mating_pool)]
        c1, c2 = crossover(p1, p2)
        children.append(mutate(c1))
        children.append(mutate(c2))
    return np.array(children[: len(pop)])


def nsga2_optimize(inflow_series):
    pop = rng.uniform(GENE_LOW, GENE_HIGH, size=(POP_SIZE, 12))

    for _ in range(N_GENERATIONS):
        objs = evaluate_population(pop, inflow_series)
        fronts, rank = fast_non_dominated_sort(objs)

        crowd_map = {}
        for front in fronts:
            crowd_map.update(crowding_distance(objs, front))

        offspring = make_offspring(pop, rank, crowd_map)

        # 父代 + 子代，环境选择
        combined = np.vstack([pop, offspring])
        combined_objs = evaluate_population(combined, inflow_series)
        combined_fronts, _ = fast_non_dominated_sort(combined_objs)

        new_idx = []
        for front in combined_fronts:
            if len(new_idx) + len(front) <= POP_SIZE:
                new_idx.extend(front)
            else:
                dist = crowding_distance(combined_objs, front)
                order = sorted(front, key=lambda idx: dist[idx], reverse=True)
                need = POP_SIZE - len(new_idx)
                new_idx.extend(order[:need])
                break

        pop = combined[np.array(new_idx)]

    final_objs = evaluate_population(pop, inflow_series)
    final_fronts, _ = fast_non_dominated_sort(final_objs)
    pareto_idx = np.array(final_fronts[0])

    return pop, final_objs, pareto_idx


def print_kpi_table(records):
    print("\nKPI结果表（Pareto前沿样本）")
    print("-" * 84)
    print(f"{'方案':<8}{'缺水率':>10}{'发电波动':>12}{'年均发电(GWh)':>16}{'弃水率':>10}{'末库容偏差':>12}")
    print("-" * 84)
    for rec in records:
        print(
            f"{rec['name']:<8}"
            f"{rec['deficit_ratio']:>10.4f}"
            f"{rec['power_cv']:>12.4f}"
            f"{rec['annual_energy_gwh']:>16.2f}"
            f"{rec['spill_ratio']:>10.4f}"
            f"{rec['terminal_storage_dev']:>12.2f}"
        )
    print("-" * 84)


def main():
    inflow_series = build_inflow_series()
    pop, objs, pareto_idx = nsga2_optimize(inflow_series)

    pareto_pop = pop[pareto_idx]
    pareto_objs = objs[pareto_idx]

    # 从Pareto集中选折中解：两目标标准化后等权求和最小
    min_v = pareto_objs.min(axis=0)
    max_v = pareto_objs.max(axis=0)
    norm = (pareto_objs - min_v) / (max_v - min_v + 1e-12)
    compromise_local_idx = int(np.argmin(norm.sum(axis=1)))
    compromise_policy = pareto_pop[compromise_local_idx]

    _, compromise_kpi, compromise_trace = simulate_reservoir(compromise_policy, inflow_series)

    # 展示Pareto前沿中按缺水率排序的前5个 + 折中解
    order = np.argsort(pareto_objs[:, 0])
    show_n = min(5, len(order))
    records = []
    for i in range(show_n):
        idx = order[i]
        _, kpi_i, _ = simulate_reservoir(pareto_pop[idx], inflow_series)
        kpi_i["name"] = f"P{i+1}"
        records.append(kpi_i)

    compromise_rec = compromise_kpi.copy()
    compromise_rec["name"] = "折中解"
    records.append(compromise_rec)
    print_kpi_table(records)

    # ------------------------ 绘图 ------------------------
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))

    # 图1：Pareto前沿
    axes[0].scatter(objs[:, 0], objs[:, 1], s=18, alpha=0.35, label="最终种群")
    axes[0].scatter(pareto_objs[:, 0], pareto_objs[:, 1], s=35, c="tab:red", label="Pareto前沿")
    axes[0].scatter(
        pareto_objs[compromise_local_idx, 0],
        pareto_objs[compromise_local_idx, 1],
        s=90, c="gold", edgecolors="black", label="折中解", zorder=5
    )
    axes[0].set_xlabel("目标1：缺水率+惩罚")
    axes[0].set_ylabel("目标2：发电波动+惩罚")
    axes[0].set_title("NSGA-II Pareto前沿")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    # 图2：折中解过程线
    t = np.arange(1, N_MONTHS + 1)
    ax2 = axes[1]
    ax2.plot(t, compromise_trace["inflow"], label="入流", lw=1.6)
    ax2.plot(t, compromise_trace["release"], label="出库", lw=1.8)
    ax2.set_xlabel("时段（月）")
    ax2.set_ylabel("流量/水量（百万m3/月）")
    ax2.set_title("折中解下的入流-出库-库容过程")
    ax2.grid(alpha=0.25)

    ax2b = ax2.twinx()
    ax2b.plot(t, compromise_trace["storage"][1:], "g--", lw=1.5, label="库容")
    ax2b.set_ylabel("库容（百万m3）")

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.tight_layout()
    plt.savefig('ch03_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch03_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
