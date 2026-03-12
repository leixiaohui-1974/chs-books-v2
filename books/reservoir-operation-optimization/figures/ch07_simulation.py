"""
教材：《水库调度优化与决策》
章节示例：单库供水-发电联合调度仿真（SLSQP）
功能：构建周尺度来水与需水序列，优化下泄过程，输出KPI表并绘制对比图。
"""
import numpy as np
from scipy.optimize import minimize, NonlinearConstraint
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# 绘图中文显示（若本机无该字体，matplotlib会自动回退）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def generate_series(T, seed):
    """生成示例来水与需水序列（单位：百万m3/周）"""
    rng = np.random.default_rng(seed)
    t = np.arange(T)

    inflow = 55 + 18 * np.sin(2 * np.pi * (t - 8) / T) + rng.normal(0, 4, T)
    inflow = np.clip(inflow, 20, 95)

    demand = 58 + 9 * np.sin(2 * np.pi * (t + 3) / T) + rng.normal(0, 2, T)
    demand = np.clip(demand, 35, 85)

    evaporation = np.full(T, 2.0)
    return inflow, demand, evaporation


def storage_path(release, inflow, evaporation, s0):
    """根据水量平衡计算库容轨迹"""
    T = len(release)
    s = np.empty(T + 1)
    s[0] = s0
    for i in range(T):
        s[i + 1] = s[i] + inflow[i] - release[i] - evaporation[i]
    return s


def head_from_storage(storage_avg, s_min, s_max, h_min, h_max):
    """用线性关系近似库容-水头关系"""
    ratio = (storage_avg - s_min) / (s_max - s_min)
    ratio = np.clip(ratio, 0.0, 1.0)
    return h_min + (h_max - h_min) * ratio


def objective(release, inflow, demand, evaporation, p):
    """优化目标：缺水最小 + 调度平滑 + 期末库容约束 + 发电收益"""
    s = storage_path(release, inflow, evaporation, p["S0"])
    shortage = np.maximum(0.0, demand - release)
    smooth = np.diff(release)
    terminal = s[-1] - p["S_TARGET"]

    s_avg = 0.5 * (s[:-1] + s[1:])
    head = head_from_storage(s_avg, p["S_MIN"], p["S_MAX"], p["H_MIN"], p["H_MAX"])
    energy = p["K_ENERGY"] * np.sum(release * head)

    value = (
        p["W_DEF"] * np.sum(shortage ** 2)
        + p["W_SMOOTH"] * np.sum(smooth ** 2)
        + p["W_TERMINAL"] * terminal ** 2
        - p["W_ENERGY"] * energy
    )
    return value


def simulate_baseline(inflow, demand, evaporation, p):
    """基准策略：按需水+库容偏差修正的经验规则调度"""
    T = len(inflow)
    release = np.zeros(T)
    spill = np.zeros(T)
    s = np.empty(T + 1)
    s[0] = p["S0"]

    for i in range(T):
        # 规则曲线：目标放水 = 需水 + 库容偏差修正
        guide = demand[i] + p["K_RULE"] * (s[i] - p["S_TARGET"])
        guide = np.clip(guide, p["R_MIN"], p["R_MAX"])

        # 保证不跌破死库容
        max_release_feasible = s[i] + inflow[i] - evaporation[i] - p["S_MIN"]
        guide = min(guide, p["R_MAX"], max_release_feasible)
        guide = max(0.0, guide)

        s_next = s[i] + inflow[i] - guide - evaporation[i]

        # 超过兴利库容记为弃水
        if s_next > p["S_MAX"]:
            spill[i] = s_next - p["S_MAX"]
            s_next = p["S_MAX"]

        release[i] = guide
        s[i + 1] = s_next

    return release, s, spill


def calc_kpi(release, storage, demand, spill, p):
    """计算KPI指标"""
    supply = np.minimum(release, demand)
    shortage = demand - supply
    reliability = np.mean(shortage <= 1e-6) * 100

    s_avg = 0.5 * (storage[:-1] + storage[1:])
    head = head_from_storage(s_avg, p["S_MIN"], p["S_MAX"], p["H_MIN"], p["H_MAX"])
    energy = p["K_ENERGY"] * np.sum(release * head)

    return {
        "总需水量(百万m3)": float(np.sum(demand)),
        "总供水量(百万m3)": float(np.sum(supply)),
        "总缺水量(百万m3)": float(np.sum(shortage)),
        "供水可靠率(%)": float(reliability),
        "总弃水量(百万m3)": float(np.sum(spill)),
        "期末库容(百万m3)": float(storage[-1]),
        "发电指标(相对值)": float(energy),
    }


def print_kpi_table(base_kpi, opt_kpi):
    """打印KPI对比表"""
    headers = ["指标", "基准调度", "优化调度"]
    keys = list(base_kpi.keys())
    rows = []
    for k in keys:
        rows.append([k, f"{base_kpi[k]:.2f}", f"{opt_kpi[k]:.2f}"])

    widths = [len(h) for h in headers]
    for row in rows:
        for j, cell in enumerate(row):
            widths[j] = max(widths[j], len(cell))

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    head_line = "| " + " | ".join(headers[j].ljust(widths[j]) for j in range(3)) + " |"

    print("\nKPI结果表")
    print(sep)
    print(head_line)
    print(sep)
    for row in rows:
        line = "| " + " | ".join(row[j].ljust(widths[j]) for j in range(3)) + " |"
        print(line)
    print(sep)


def plot_results(weeks, inflow, demand, release_base, release_opt, s_base, s_opt, shortage_base, shortage_opt, p):
    """绘制调度对比图"""
    fig, ax = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    ax[0].bar(weeks, inflow, color="#8ecae6", alpha=0.8, label="来水")
    ax[0].plot(weeks, demand, color="#023047", linewidth=2, label="需水")
    ax[0].plot(weeks, release_base, color="#fb8500", linestyle="--", linewidth=1.8, label="基准放水")
    ax[0].plot(weeks, release_opt, color="#2a9d8f", linewidth=2, label="优化放水")
    ax[0].set_ylabel("流量/水量(百万m3/周)")
    ax[0].set_title("来水-需水-放水过程")
    ax[0].legend()

    ax[1].plot(np.arange(0, len(s_base)), s_base, color="#fb8500", linestyle="--", linewidth=1.8, label="基准库容")
    ax[1].plot(np.arange(0, len(s_opt)), s_opt, color="#2a9d8f", linewidth=2, label="优化库容")
    ax[1].axhline(p["S_MIN"], color="gray", linestyle=":", label="死库容")
    ax[1].axhline(p["S_MAX"], color="gray", linestyle="-.", label="兴利库容")
    ax[1].axhline(p["S_TARGET"], color="#6d597a", linestyle="--", label="目标库容")
    ax[1].set_ylabel("库容(百万m3)")
    ax[1].set_title("库容轨迹对比")
    ax[1].legend(ncol=2)

    ax[2].plot(weeks, np.cumsum(shortage_base), color="#fb8500", linestyle="--", linewidth=2, label="基准累计缺水")
    ax[2].plot(weeks, np.cumsum(shortage_opt), color="#2a9d8f", linewidth=2, label="优化累计缺水")
    ax[2].set_xlabel("周次")
    ax[2].set_ylabel("累计缺水(百万m3)")
    ax[2].set_title("累计缺水过程")
    ax[2].legend()

    plt.tight_layout()
    plt.savefig('ch07_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch07_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    # ---------------- 关键参数定义 ----------------
    T = 52
    RANDOM_SEED = 42

    params = {
        "S0": 600.0,         # 初始库容
        "S_MIN": 250.0,      # 死库容
        "S_MAX": 900.0,      # 兴利库容上限
        "S_TARGET": 560.0,   # 期末目标库容
        "R_MIN": 15.0,       # 最小下泄
        "R_MAX": 110.0,      # 最大下泄
        "H_MIN": 28.0,       # 最小有效水头
        "H_MAX": 60.0,       # 最大有效水头
        "K_ENERGY": 1.0,     # 发电指标折算系数
        "W_DEF": 6.0,        # 缺水惩罚权重
        "W_SMOOTH": 0.25,    # 平滑惩罚权重
        "W_TERMINAL": 1.8,   # 期末库容权重
        "W_ENERGY": 0.03,    # 发电收益权重
        "K_RULE": 0.08,      # 基准策略修正系数
    }

    inflow, demand, evaporation = generate_series(T, RANDOM_SEED)
    weeks = np.arange(1, T + 1)

    # ---------------- 基准调度 ----------------
    release_base, s_base, spill_base = simulate_baseline(inflow, demand, evaporation, params)

    # ---------------- 优化调度 ----------------
    x0 = np.clip(demand, params["R_MIN"], params["R_MAX"])
    bounds = [(params["R_MIN"], params["R_MAX"])] * T

    # 约束：每周末库容必须在[S_MIN, S_MAX]内
    c_storage = NonlinearConstraint(
        lambda r: storage_path(r, inflow, evaporation, params["S0"])[1:],
        params["S_MIN"],
        params["S_MAX"],
    )

    res = minimize(
        objective,
        x0,
        args=(inflow, demand, evaporation, params),
        method="SLSQP",
        bounds=bounds,
        constraints=[c_storage],
        options={"maxiter": 500, "ftol": 1e-8, "disp": False},
    )

    if res.success:
        release_opt = res.x
        print(f"优化求解成功：{res.message}")
    else:
        release_opt = x0
        print(f"优化未收敛，回退到初值策略：{res.message}")

    s_opt = storage_path(release_opt, inflow, evaporation, params["S0"])
    spill_opt = np.zeros(T)  # 约束保证不超过兴利库容，理论上无弃水

    # ---------------- KPI计算与打印 ----------------
    kpi_base = calc_kpi(release_base, s_base, demand, spill_base, params)
    kpi_opt = calc_kpi(release_opt, s_opt, demand, spill_opt, params)
    print_kpi_table(kpi_base, kpi_opt)

    # ---------------- 绘图 ----------------
    shortage_base = np.maximum(0.0, demand - np.minimum(release_base, demand))
    shortage_opt = np.maximum(0.0, demand - np.minimum(release_opt, demand))

    plot_results(
        weeks, inflow, demand,
        release_base, release_opt,
        s_base, s_opt,
        shortage_base, shortage_opt,
        params
    )


if __name__ == "__main__":
    main()
