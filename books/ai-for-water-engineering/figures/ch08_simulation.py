# -*- coding: utf-8 -*-
"""
书名：《人工智能与水利水电工程》
章节：第8章 时序预测：洪水/水质/负荷预报
功能：基于 numpy/scipy/matplotlib 实现洪水/水质/负荷三任务时序仿真，
      输出KPI结果表，开展参数敏感性分析，并绘制预测结果图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.stats import norm

# =========================
# 关键参数（可直接调参）
# =========================
RANDOM_SEED = 2026
N_STEPS = 1200             # 总时间步（示例按小时）
TRAIN_RATIO = 0.70         # 训练集比例
VAL_RATIO = 0.15           # 验证集比例（本脚本用于划分，不单独调参）
FORECAST_H = 72            # 起报后多步预测长度
PI_LEVEL = 0.90            # 预测区间置信水平

# ESN（回声状态网络）参数
N_RES = 180                # 水库神经元数量
SPECTRAL_RADIUS = 0.92     # 谱半径（核心稳定性参数）
LEAK_RATE = 0.35           # 泄露率（记忆速度）
INPUT_SCALE = 0.45         # 输入缩放
RIDGE_ALPHA = 1e-2         # 岭回归正则
WASHOUT = 40               # 前期洗出步数

# 参数敏感性分析：洪水任务上扫描谱半径
SENSITIVITY_R = [0.70, 0.85, 0.92, 1.05, 1.20]


def nse(y_true, y_pred):
    """Nash-Sutcliffe效率系数"""
    den = np.sum((y_true - np.mean(y_true)) ** 2) + 1e-12
    num = np.sum((y_true - y_pred) ** 2)
    return 1.0 - num / den


def build_synthetic_data(n, seed=RANDOM_SEED):
    """生成洪水/水质/负荷三类仿真序列与外生驱动"""
    rng = np.random.default_rng(seed)
    t = np.arange(n)

    # 外生变量：降雨、气温、日周期、周末、工业指数
    rain_base = 5.0 + 3.0 * np.sin(2 * np.pi * t / 96)
    rain = np.clip(rain_base + rng.gamma(shape=1.3, scale=1.6, size=n), 0, None)

    storm_idx = rng.choice(np.arange(24, n - 24), size=22, replace=False)
    for p in storm_idx:
        w = int(rng.integers(4, 12))
        amp = rng.uniform(8, 25)
        pulse = amp * np.exp(-np.linspace(0, 2.5, w))
        rain[p:p + w] += pulse[: max(0, min(w, n - p))]

    temp = 20 + 9 * np.sin(2 * np.pi * t / (24 * 30) - 0.8) + rng.normal(0, 1.2, n)
    hour = t % 24
    is_weekend = (((t // 24) % 7) >= 5).astype(float)
    industrial = 1.0 + 0.12 * np.sin(2 * np.pi * t / (24 * 14) + 0.6) + rng.normal(0, 0.03, n)

    # 由降雨卷积得到径流过程，再映射为流量
    runoff = np.convolve(rain, np.array([0.08, 0.23, 0.37, 0.20, 0.12]), mode="same")
    flow = np.clip(18 + 0.95 * runoff + rng.normal(0, 1.0, n), 0.2, None)

    pollutant_load = 3.0 + 0.6 * np.sin(2 * np.pi * t / 168 + 1.2) + rng.normal(0, 0.22, n)

    flood = np.zeros(n)
    quality = np.zeros(n)
    load = np.zeros(n)

    # 初值
    flood[:3] = [12.0, 12.5, 11.8]
    quality[:3] = [4.8, 4.7, 4.9]
    load[:3] = [103.0, 99.0, 97.5]

    # 状态递推：体现各任务的动力学差异
    for i in range(3, n):
        daily = np.sin(2 * np.pi * hour[i] / 24 - 0.5) + 0.25 * np.sin(2 * np.pi * hour[i] / 12)
        cooling = max(temp[i] - 27.0, 0.0)

        flood[i] = (
            3.5 + 0.78 * flood[i - 1] - 0.11 * flood[i - 2] + 0.03 * flood[i - 3]
            + 0.11 * rain[i] + 0.06 * rain[i - 1] + rng.normal(0, 0.38)
        )
        quality[i] = (
            0.9 + 0.84 * quality[i - 1] - 0.09 * quality[i - 2] + 0.02 * quality[i - 3]
            + 0.04 * temp[i] - 0.035 * flow[i] + 0.21 * pollutant_load[i] + rng.normal(0, 0.16)
        )
        load[i] = (
            28 + 0.72 * load[i - 1] - 0.08 * load[i - 2] + 0.03 * load[i - 3]
            + 11 * daily - 4.2 * is_weekend[i] + 1.8 * cooling + 14 * (industrial[i] - 1.0)
            + rng.normal(0, 2.4)
        )

    flood = np.clip(flood, 0, None)
    quality = np.clip(quality, 0.05, None)
    load = np.clip(load, 1.0, None)

    exog_common = np.column_stack([
        rain,
        temp,
        np.sin(2 * np.pi * hour / 24),
        np.cos(2 * np.pi * hour / 24),
        is_weekend,
        industrial,
    ])

    return {
        "t": t,
        "rain": rain,
        "temp": temp,
        "flow": flow,
        "pollutant_load": pollutant_load,
        "exog_common": exog_common,
        "flood": flood,
        "quality": quality,
        "load": load,
    }


def init_reservoir(input_dim, n_res, spectral_radius, input_scale, seed):
    """初始化ESN权重，并按谱半径缩放递归矩阵"""
    rng = np.random.default_rng(seed)
    W_in = rng.uniform(-input_scale, input_scale, size=(n_res, input_dim + 1))
    W = rng.uniform(-1.0, 1.0, size=(n_res, n_res))

    # 稀疏化（约8%保留）
    mask = rng.uniform(0.0, 1.0, size=(n_res, n_res))
    W[mask > 0.08] = 0.0

    eigvals = np.linalg.eigvals(W)
    sr = np.max(np.abs(eigvals)) + 1e-12
    W *= spectral_radius / sr
    return W_in, W


def ridge_fit(X, y, alpha):
    """岭回归闭式解（不惩罚截距项）"""
    I = np.eye(X.shape[1])
    I[0, 0] = 0.0
    w = np.linalg.solve(X.T @ X + alpha * I, X.T @ y)
    return w


def kpi_metrics(y_true, y_pred, lower, upper):
    """确定性 + 概率区间KPI"""
    err = y_true - y_pred
    mae = np.mean(np.abs(err))
    rmse = np.sqrt(np.mean(err ** 2))
    mape = np.mean(np.abs(err) / (np.abs(y_true) + 1e-8)) * 100.0
    nse_val = nse(y_true, y_pred)
    picp = np.mean((y_true >= lower) & (y_true <= upper)) * 100.0
    mpiw = np.mean(upper - lower)
    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE(%)": mape,
        "R2": nse_val,
        "NSE": nse_val,
        "PICP(%)": picp,
        "MPIW": mpiw,
    }


def esn_train_predict(y, exog, params, seed_offset=0):
    """单任务ESN训练 + 测试集递推预测"""
    n = len(y)
    train_end = int(n * TRAIN_RATIO)
    val_end = int(n * (TRAIN_RATIO + VAL_RATIO))

    input_dim = exog.shape[1] + 1  # +1表示前一时刻目标值反馈
    W_in, W = init_reservoir(
        input_dim=input_dim,
        n_res=params["n_res"],
        spectral_radius=params["spectral_radius"],
        input_scale=params["input_scale"],
        seed=RANDOM_SEED + seed_offset,
    )

    x = np.zeros(params["n_res"])
    states, targets = [], []

    # 训练阶段：教师强制（使用真实 y[t-1]）
    for t in range(1, train_end):
        u = np.concatenate([exog[t], [y[t - 1]]])
        x = (1.0 - params["leak_rate"]) * x + params["leak_rate"] * np.tanh(W_in @ np.r_[1.0, u] + W @ x)
        if t >= params["washout"]:
            states.append(np.r_[1.0, x])   # 加截距
            targets.append(y[t])

    Xtr = np.asarray(states)
    ytr = np.asarray(targets)
    w_out = ridge_fit(Xtr, ytr, params["ridge_alpha"])

    # 残差标准差近似不确定性，构造预测区间
    y_fit = Xtr @ w_out
    sigma = np.std(ytr - y_fit, ddof=1) + 1e-8
    z = norm.ppf((1 + PI_LEVEL) / 2)

    y_pred = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    y_pred[:train_end] = y[:train_end]

    # 测试阶段：递推预测（使用上一时刻预测值反馈）
    for t in range(train_end, n):
        prev_y = y[t - 1] if t == train_end else y_pred[t - 1]
        u = np.concatenate([exog[t], [prev_y]])
        x = (1.0 - params["leak_rate"]) * x + params["leak_rate"] * np.tanh(W_in @ np.r_[1.0, u] + W @ x)
        y_pred[t] = np.r_[1.0, x] @ w_out
        lower[t] = y_pred[t] - z * sigma
        upper[t] = y_pred[t] + z * sigma

    idx_test = np.arange(train_end, n)
    y_true_test = y[idx_test]
    y_pred_test = y_pred[idx_test]
    lower_test = lower[idx_test]
    upper_test = upper[idx_test]

    kpis = kpi_metrics(y_true_test, y_pred_test, lower_test, upper_test)

    # 从起报点截取多步预测曲线
    h_end = min(train_end + FORECAST_H, n)
    horizon = {
        "idx": np.arange(train_end, h_end),
        "true": y[train_end:h_end],
        "pred": y_pred[train_end:h_end],
    }

    return {
        "train_end": train_end,
        "val_end": val_end,
        "idx_test": idx_test,
        "y_true": y_true_test,
        "y_pred": y_pred_test,
        "lower": lower_test,
        "upper": upper_test,
        "kpi": kpis,
        "horizon": horizon,
    }


def print_kpi_table(results):
    """打印KPI结果表格"""
    line = "=" * 108
    print("\n" + line)
    print("KPI结果表（《人工智能与水利水电工程》第8章：时序预测仿真）")
    print(line)
    print(f"{'任务':<8}{'MAE':>10}{'RMSE':>10}{'MAPE(%)':>12}{'R2':>10}{'NSE':>10}{'PICP(%)':>12}{'MPIW':>10}")
    print("-" * 108)
    for name in ["洪水", "水质", "负荷"]:
        k = results[name]["kpi"]
        print(f"{name:<8}{k['MAE']:>10.3f}{k['RMSE']:>10.3f}{k['MAPE(%)']:>12.2f}{k['R2']:>10.3f}{k['NSE']:>10.3f}{k['PICP(%)']:>12.2f}{k['MPIW']:>10.3f}")
    print(line)


def sensitivity_analysis(data, base_params):
    """洪水任务参数敏感性：谱半径 -> NSE, RMSE"""
    out = []
    y = data["flood"]
    exog_flood = np.column_stack([data["exog_common"], data["flow"]])
    for r in SENSITIVITY_R:
        p = dict(base_params)
        p["spectral_radius"] = r
        res = esn_train_predict(y, exog_flood, p, seed_offset=77)
        out.append((r, res["kpi"]["NSE"], res["kpi"]["RMSE"]))
    return out


def plot_results(results, sensitivity):
    """绘制三任务预测曲线和敏感性曲线"""
    fig, axes = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(2, 2, figsize=(15, 10))
    colors = {"洪水": "#1f77b4", "水质": "#2ca02c", "负荷": "#d62728"}

    for i, name in enumerate(["洪水", "水质", "负荷"]):
        ax = axes[i // 2, i % 2]
        r = results[name]
        x = r["idx_test"]
        ax.plot(x, r["y_true"], color="black", lw=1.4, label="真实值")
        ax.plot(x, r["y_pred"], color=colors[name], lw=1.6, label="预测值")
        ax.fill_between(x, r["lower"], r["upper"], color=colors[name], alpha=0.18, label=f"{int(PI_LEVEL*100)}%区间")
        ax.axvline(r["train_end"], color="gray", ls="--", lw=1.0, label="训练/测试分界")
        ax.set_title(f"{name}测试集预测")
        ax.set_xlabel("时间步")
        ax.set_ylabel(name)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=9)

    # 第4幅图：谱半径敏感性
    ax4 = axes[1, 1]
    r_vals = [x[0] for x in sensitivity]
    nse_vals = [x[1] for x in sensitivity]
    rmse_vals = [x[2] for x in sensitivity]

    ax4.plot(r_vals, nse_vals, marker="o", lw=1.8, color="#1f77b4", label="NSE")
    ax4.set_xlabel("spectral_radius")
    ax4.set_ylabel("NSE", color="#1f77b4")
    ax4.tick_params(axis="y", labelcolor="#1f77b4")
    ax4.grid(alpha=0.25)

    ax4r = ax4.twinx()
    ax4r.plot(r_vals, rmse_vals, marker="s", lw=1.6, color="#d62728", label="RMSE")
    ax4r.set_ylabel("RMSE", color="#d62728")
    ax4r.tick_params(axis="y", labelcolor="#d62728")
    ax4.set_title("洪水任务参数敏感性（谱半径）")

    plt.tight_layout()
    plt.savefig('ch08_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch08_simulation_result.png")
# plt.show()  # 禁用弹窗


def main():
    data = build_synthetic_data(N_STEPS)

    params = {
        "n_res": N_RES,
        "spectral_radius": SPECTRAL_RADIUS,
        "leak_rate": LEAK_RATE,
        "input_scale": INPUT_SCALE,
        "ridge_alpha": RIDGE_ALPHA,
        "washout": WASHOUT,
    }

    # 三任务输入构造
    exog_flood = np.column_stack([data["exog_common"], data["flow"]])
    exog_quality = np.column_stack([data["exog_common"], data["flow"], data["pollutant_load"]])
    exog_load = np.column_stack([data["exog_common"]])

    results = {
        "洪水": esn_train_predict(data["flood"], exog_flood, params, seed_offset=11),
        "水质": esn_train_predict(data["quality"], exog_quality, params, seed_offset=22),
        "负荷": esn_train_predict(data["load"], exog_load, params, seed_offset=33),
    }

    # 打印KPI结果表
    print_kpi_table(results)

    # 参数敏感性分析并打印
    sensitivity = sensitivity_analysis(data, params)
    print("\n参数敏感性（洪水任务，变化 spectral_radius）")
    print(f"{'spectral_radius':<18}{'NSE':>10}{'RMSE':>10}")
    for r, nse_val, rmse in sensitivity:
        print(f"{r:<18.2f}{nse_val:>10.3f}{rmse:>10.3f}")

    # 画图
    plot_results(results, sensitivity)


if __name__ == "__main__":
    main()
