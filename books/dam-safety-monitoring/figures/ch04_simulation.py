# -*- coding: utf-8 -*-
"""
教材：《大坝安全监测与预警》
章节：第4章 统计模型（HST/HTT）
功能：生成合成监测数据，对HST与HTT模型进行参数识别、KPI评估和可视化。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy import linalg, stats
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（可按工程场景修改）
# =========================
RANDOM_SEED = 42
N_DAYS = 6 * 365          # 仿真时长：6年（日尺度）
TRAIN_RATIO = 0.75        # 训练集占比
NOISE_STD = 0.20          # 监测噪声标准差（mm）

# “真实”位移机理参数（用于生成合成数据）
B0 = 0.15
B_H1, B_H2, B_H3 = 0.85, 0.30, -0.12       # 水压项（H）
B_SIN1, B_COS1 = 0.20, -0.08               # 一阶季节项（S）
B_TEMP1, B_TEMP2 = 0.35, 0.05              # 温度项（HTT中的T）
B_TIME1, B_TIME2 = 0.10, -0.06             # 时效项（HST中的T）


def simulate_data(n_days: int, noise_std: float, seed: int = 42):
    """生成模拟的库水位、温度和坝体位移数据。"""
    rng = np.random.default_rng(seed)
    t = np.arange(n_days, dtype=float)
    year = t / 365.0
    omega = 2.0 * np.pi / 365.0

    # 库水位：年周期 + 半年周期 + 缓慢趋势 + 随机扰动
    h = (
        100
        + 7.5 * np.sin(omega * (t - 25))
        + 1.8 * np.sin(2 * omega * t)
        + 0.004 * t
        + rng.normal(0, 0.35, n_days)
    )

    # 温度：季节主导 + 次谐波 + 随机扰动
    temp = (
        16
        + 12.0 * np.sin(omega * (t - 170))
        + 1.2 * np.sin(2 * omega * (t - 170))
        + rng.normal(0, 0.8, n_days)
    )

    # 标准化，避免高次项数值过大
    h_n = stats.zscore(h, ddof=1)
    temp_n = stats.zscore(temp, ddof=1)

    # 真实位移（mm）：综合H/S/T机理，加入观测噪声
    y = (
        B0
        + B_H1 * h_n
        + B_H2 * h_n ** 2
        + B_H3 * h_n ** 3
        + B_SIN1 * np.sin(omega * t)
        + B_COS1 * np.cos(omega * t)
        + B_TEMP1 * temp_n
        + B_TEMP2 * temp_n ** 2
        + B_TIME1 * year
        + B_TIME2 * np.log1p(year)
        + rng.normal(0, noise_std, n_days)
    )
    return t, h_n, temp_n, y


def build_hst_matrix(t, h_n):
    """构建设计矩阵：HST = 水压(H) + 季节(S) + 时效(T)。"""
    year = t / 365.0
    w = 2.0 * np.pi * t / 365.0
    X = np.column_stack([
        np.ones_like(t),
        h_n, h_n ** 2, h_n ** 3,      # H: 水压多项式
        np.sin(w), np.cos(w),         # S: 一阶谐波
        np.sin(2 * w), np.cos(2 * w), # S: 二阶谐波
        year, np.log1p(year)          # T: 线性时效 + 对数蠕变
    ])
    names = ["1", "H", "H^2", "H^3", "sin(w)", "cos(w)", "sin(2w)", "cos(2w)", "t", "ln(1+t)"]
    return X, names


def build_htt_matrix(t, h_n, temp_n):
    """构建设计矩阵：HTT = 水压(H) + 温度(T) + 时效(T)。"""
    year = t / 365.0
    X = np.column_stack([
        np.ones_like(t),
        h_n, h_n ** 2, h_n ** 3,      # H
        temp_n, temp_n ** 2,          # 温度项
        year, np.log1p(year),         # 时效项
        h_n * temp_n                  # 交互项（可解释热-水耦合）
    ])
    names = ["1", "H", "H^2", "H^3", "Temp", "Temp^2", "t", "ln(1+t)", "H*Temp"]
    return X, names


def fit_lstsq(X, y):
    """最小二乘估计。"""
    beta, _, _, _ = linalg.lstsq(X, y)
    y_hat = X @ beta
    return beta, y_hat


def calc_metrics(y_true, y_pred, k_params):
    """计算KPI：R2/RMSE/MAE/AIC/BIC/DW/Pearson。"""
    n = len(y_true)
    resid = y_true - y_pred
    rss = np.sum(resid ** 2)
    tss = np.sum((y_true - np.mean(y_true)) ** 2)

    r2 = 1.0 - rss / tss if tss > 1e-12 else np.nan
    rmse = np.sqrt(np.mean(resid ** 2))
    mae = np.mean(np.abs(resid))
    aic = n * np.log(rss / n) + 2 * k_params
    bic = n * np.log(rss / n) + k_params * np.log(n)
    dw = np.sum(np.diff(resid) ** 2) / np.sum(resid ** 2)
    pearson_r, _ = stats.pearsonr(y_true, y_pred)

    return {
        "R2": r2,
        "RMSE": rmse,
        "MAE": mae,
        "AIC": aic,
        "BIC": bic,
        "DW": dw,
        "PearsonR": pearson_r,
    }


def print_kpi_table(rows):
    """打印KPI结果表格。"""
    headers = ["模型", "R2(测试)", "RMSE(测试)", "MAE(测试)", "AIC(训练)", "BIC(训练)", "DW(测试)", "PearsonR(测试)"]
    line = "-" * 108
    print("\n" + line)
    print("{:^10s} {:>10s} {:>12s} {:>12s} {:>12s} {:>12s} {:>10s} {:>14s}".format(*headers))
    print(line)
    for r in rows:
        print("{:^10s} {:>10.4f} {:>12.4f} {:>12.4f} {:>12.2f} {:>12.2f} {:>10.4f} {:>14.4f}".format(
            r["model"], r["R2_test"], r["RMSE_test"], r["MAE_test"], r["AIC_train"], r["BIC_train"], r["DW_test"], r["PearsonR_test"]
        ))
    print(line)


def main():
    # 中文绘图字体设置（若本机无字体，matplotlib会自动降级）
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    # 2) 生成数据
    t, h_n, temp_n, y = simulate_data(N_DAYS, NOISE_STD, RANDOM_SEED)

    # 3) 训练/测试划分（按时间先后划分，符合监测预测场景）
    n_train = int(TRAIN_RATIO * N_DAYS)
    idx_train = np.arange(n_train)
    idx_test = np.arange(n_train, N_DAYS)

    t_train, t_test = t[idx_train], t[idx_test]
    y_train, y_test = y[idx_train], y[idx_test]
    h_train, h_test = h_n[idx_train], h_n[idx_test]
    temp_train, temp_test = temp_n[idx_train], temp_n[idx_test]

    # 4) 构建HST模型并拟合
    X_hst_train, hst_names = build_hst_matrix(t_train, h_train)
    X_hst_test, _ = build_hst_matrix(t_test, h_test)
    beta_hst, y_hst_train = fit_lstsq(X_hst_train, y_train)
    y_hst_test = X_hst_test @ beta_hst

    # 5) 构建HTT模型并拟合
    X_htt_train, htt_names = build_htt_matrix(t_train, h_train, temp_train)
    X_htt_test, _ = build_htt_matrix(t_test, h_test, temp_test)
    beta_htt, y_htt_train = fit_lstsq(X_htt_train, y_train)
    y_htt_test = X_htt_test @ beta_htt

    # 全时段拟合值（用于作图）
    X_hst_all, _ = build_hst_matrix(t, h_n)
    X_htt_all, _ = build_htt_matrix(t, h_n, temp_n)
    y_hst_all = X_hst_all @ beta_hst
    y_htt_all = X_htt_all @ beta_htt

    # 6) KPI计算
    m_hst_train = calc_metrics(y_train, y_hst_train, X_hst_train.shape[1])
    m_hst_test = calc_metrics(y_test, y_hst_test, X_hst_train.shape[1])
    m_htt_train = calc_metrics(y_train, y_htt_train, X_htt_train.shape[1])
    m_htt_test = calc_metrics(y_test, y_htt_test, X_htt_train.shape[1])

    rows = [
        {
            "model": "HST",
            "R2_test": m_hst_test["R2"],
            "RMSE_test": m_hst_test["RMSE"],
            "MAE_test": m_hst_test["MAE"],
            "AIC_train": m_hst_train["AIC"],
            "BIC_train": m_hst_train["BIC"],
            "DW_test": m_hst_test["DW"],
            "PearsonR_test": m_hst_test["PearsonR"],
        },
        {
            "model": "HTT",
            "R2_test": m_htt_test["R2"],
            "RMSE_test": m_htt_test["RMSE"],
            "MAE_test": m_htt_test["MAE"],
            "AIC_train": m_htt_train["AIC"],
            "BIC_train": m_htt_train["BIC"],
            "DW_test": m_htt_test["DW"],
            "PearsonR_test": m_htt_test["PearsonR"],
        },
    ]

    # 7) 打印参数和KPI
    print("\nHST参数估计：")
    for name, val in zip(hst_names, beta_hst):
        print(f"  {name:>8s} = {val: .4f}")

    print("\nHTT参数估计：")
    for name, val in zip(htt_names, beta_htt):
        print(f"  {name:>8s} = {val: .4f}")

    print_kpi_table(rows)

    # 8) 绘图
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    # 图1：全时段观测与拟合
    ax = axes[0, 0]
    ax.plot(t, y, color="black", lw=1.0, label="观测位移")
    ax.plot(t, y_hst_all, color="#1f77b4", lw=1.1, label="HST拟合")
    ax.plot(t, y_htt_all, color="#d62728", lw=1.1, label="HTT拟合")
    ax.axvline(n_train, color="gray", ls="--", lw=1, label="训练/测试分界")
    ax.set_title("坝体位移：观测与模型拟合")
    ax.set_xlabel("时间（日）")
    ax.set_ylabel("位移（mm）")
    ax.legend(loc="best")
    ax.grid(alpha=0.25)

    # 图2：测试集散点对比
    ax = axes[0, 1]
    ax.scatter(y_test, y_hst_test, s=12, alpha=0.55, label="HST", color="#1f77b4")
    ax.scatter(y_test, y_htt_test, s=12, alpha=0.55, label="HTT", color="#d62728")
    y_min = min(y_test.min(), y_hst_test.min(), y_htt_test.min())
    y_max = max(y_test.max(), y_hst_test.max(), y_htt_test.max())
    ax.plot([y_min, y_max], [y_min, y_max], "k--", lw=1, label="理想线 y=x")
    ax.set_title("测试集：预测值 vs 观测值")
    ax.set_xlabel("观测位移（mm）")
    ax.set_ylabel("预测位移（mm）")
    ax.legend(loc="best")
    ax.grid(alpha=0.25)

    # 图3：测试集残差时程
    ax = axes[1, 0]
    resid_hst_test = y_test - y_hst_test
    resid_htt_test = y_test - y_htt_test
    ax.plot(t_test, resid_hst_test, lw=1.0, label="HST残差", color="#1f77b4")
    ax.plot(t_test, resid_htt_test, lw=1.0, label="HTT残差", color="#d62728")
    ax.axhline(0.0, color="k", ls="--", lw=1)
    ax.set_title("测试集残差时程")
    ax.set_xlabel("时间（日）")
    ax.set_ylabel("残差（mm）")
    ax.legend(loc="best")
    ax.grid(alpha=0.25)

    # 图4：测试集残差分布（直方图）
    ax = axes[1, 1]
    ax.hist(resid_hst_test, bins=30, alpha=0.55, density=True, label="HST残差", color="#1f77b4")
    ax.hist(resid_htt_test, bins=30, alpha=0.55, density=True, label="HTT残差", color="#d62728")
    # 用正态曲线辅助观察残差分布
    mu_h, sd_h = stats.norm.fit(resid_hst_test)
    mu_t, sd_t = stats.norm.fit(resid_htt_test)
    x_line = np.linspace(min(resid_hst_test.min(), resid_htt_test.min()),
                         max(resid_hst_test.max(), resid_htt_test.max()), 300)
    ax.plot(x_line, stats.norm.pdf(x_line, mu_h, sd_h), color="#1f77b4", lw=1.2)
    ax.plot(x_line, stats.norm.pdf(x_line, mu_t, sd_t), color="#d62728", lw=1.2)
    ax.set_title("测试集残差分布")
    ax.set_xlabel("残差（mm）")
    ax.set_ylabel("概率密度")
    ax.legend(loc="best")
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
