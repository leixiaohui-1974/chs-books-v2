# -*- coding: utf-8 -*-
# 书名：《大坝安全监测与智能预警》
# 章节：第1章 1.1 基本概念与理论框架（大坝变形监测）
# 功能：构建“环境驱动-变形响应-残差预警”的仿真流程，输出KPI并绘图

import numpy as np
from scipy import linalg
from scipy.stats import norm
from scipy.signal import savgol_filter
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# ---------- 关键参数（可按工程实际调整） ----------
SEED = 2026                  # 随机种子，保证复现实验
N_DAYS = 730                 # 监测天数（2年）
TRAIN_RATIO = 0.7            # 建模期比例
NOISE_STD = 0.35             # 观测噪声标准差（mm）
ALPHA_CONF = 0.9973          # 控制限置信度，对应约3sigma
H0 = 100.0                   # 基准库水位（m）

# 真实机理参数（用于生成“地真值”）
A0_TRUE = 2.0                # 常数项（mm）
AH_TRUE = 0.12               # 水压系数（mm/m）
AT_TRUE = 0.07               # 温度系数（mm/℃）
AC_TRUE = 1.10               # 时效（蠕变）系数（mm）
CREEP_SCALE = 25.0           # 蠕变时间尺度


def rmse(y, yhat):
    return np.sqrt(np.mean((y - yhat) ** 2))


def mae(y, yhat):
    return np.mean(np.abs(y - yhat))


def r2_score(y, yhat):
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1 - ss_res / ss_tot


def precision_recall_f1(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1, tp, fp, fn


def mean_detection_delay(warn_flag, events):
    """计算每个异常事件从起点到首次被预警的延迟（天）"""
    delays = []
    for start, end in events:
        idx = np.where(warn_flag[start:end + 1])[0]
        if idx.size > 0:
            delays.append(int(idx[0]))
        else:
            delays.append(np.nan)
    return float(np.nanmean(delays)) if np.any(~np.isnan(delays)) else np.nan


def print_kpi_table(rows):
    print("\n" + "=" * 52)
    print(f"{'KPI指标':<32}{'数值':>18}")
    print("-" * 52)
    for name, value in rows:
        text = "NaN" if (isinstance(value, float) and np.isnan(value)) else f"{value:.4f}"
        print(f"{name:<32}{text:>18}")
    print("=" * 52)


def main():
    # ---------- 1) 数据仿真：环境因子 + 变形机理 ----------
    np.random.seed(SEED)
    day = np.arange(N_DAYS)

    # 水位：季节周期 + 随机波动
    water_level = H0 + 8 * np.sin(2 * np.pi * day / 365 + 0.6) + np.random.normal(0, 0.8, N_DAYS)

    # 温度：年周期 + 随机扰动
    temp = 16 + 11 * np.sin(2 * np.pi * (day - 35) / 365) + np.random.normal(0, 1.2, N_DAYS)

    # 时效项：对数增长，近似反映蠕变/徐变
    creep = np.log1p(day / CREEP_SCALE)

    # 理论变形（无噪声）
    deformation_true = (
        A0_TRUE
        + AH_TRUE * (water_level - H0)
        + AT_TRUE * temp
        + AC_TRUE * creep
    )

    # 监测观测值（含噪声）
    deformation_obs = deformation_true + np.random.normal(0, NOISE_STD, N_DAYS)

    # ---------- 2) 注入异常：模拟结构行为突变 ----------
    # 两段事件：渐变漂移 + 短时突增
    events = [(560, 578), (650, 656)]
    truth_anomaly = np.zeros(N_DAYS, dtype=int)

    # 事件1：逐步上浮（如局部刚度变化）
    s1, e1 = events[0]
    deformation_obs[s1:e1 + 1] += np.linspace(0.2, 1.8, e1 - s1 + 1)
    truth_anomaly[s1:e1 + 1] = 1

    # 事件2：突发跃迁（如异常工况）
    s2, e2 = events[1]
    deformation_obs[s2:e2 + 1] += 1.6
    truth_anomaly[s2:e2 + 1] = 1

    # ---------- 3) 理论框架建模：H-T-C（水位-温度-时效） ----------
    X = np.column_stack([
        np.ones(N_DAYS),          # 常数项
        (water_level - H0),       # 水压项
        temp,                     # 温度项
        creep                     # 时效项
    ])

    split = int(N_DAYS * TRAIN_RATIO)
    X_train, y_train = X[:split], deformation_obs[:split]
    X_test, y_test = X[split:], deformation_obs[split:]

    # 使用 SciPy 最小二乘拟合参数
    beta_hat, *_ = linalg.lstsq(X_train, y_train)

    y_hat = X @ beta_hat
    residual = deformation_obs - y_hat

    # ---------- 4) 预警判据：残差控制图 ----------
    res_train = residual[:split]
    mu_r = np.mean(res_train)
    sigma_r = np.std(res_train, ddof=1)
    z = norm.ppf((1 + ALPHA_CONF) / 2)
    threshold = z * sigma_r

    warn_flag = (np.abs(residual - mu_r) > threshold).astype(int)

    # ---------- 5) KPI评估 ----------
    rmse_train = rmse(y_train, y_hat[:split])
    rmse_test = rmse(y_test, y_hat[split:])
    mae_test = mae(y_test, y_hat[split:])
    r2_test = r2_score(y_test, y_hat[split:])

    precision, recall, f1, tp, fp, fn = precision_recall_f1(truth_anomaly[split:], warn_flag[split:])
    neg = np.sum(truth_anomaly[split:] == 0)
    false_alarm_rate = fp / neg if neg > 0 else 0.0
    avg_delay = mean_detection_delay(warn_flag, events)

    kpi_rows = [
        ("Train RMSE (mm)", rmse_train),
        ("Test RMSE (mm)", rmse_test),
        ("Test MAE (mm)", mae_test),
        ("Test R2", r2_test),
        ("Precision", precision),
        ("Recall", recall),
        ("F1-score", f1),
        ("False Alarm Rate", false_alarm_rate),
        ("Avg Detection Delay (day)", avg_delay),
    ]
    print_kpi_table(kpi_rows)

    print("\n拟合参数（估计值 vs 真实值）")
    param_names = ["A0", "AH", "AT", "AC"]
    param_true = [A0_TRUE, AH_TRUE, AT_TRUE, AC_TRUE]
    for n, b, t in zip(param_names, beta_hat, param_true):
        print(f"{n:<3} 估计={b:8.4f} | 真实={t:8.4f}")

    # ---------- 6) 可视化 ----------
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # 图1：观测与模型拟合
    axes[0].plot(day, deformation_obs, label="监测变形", lw=1.2, color="#1f77b4")
    axes[0].plot(day, y_hat, label="模型拟合", lw=1.8, color="#ff7f0e")
    warn_idx = np.where(warn_flag == 1)[0]
    axes[0].scatter(warn_idx, deformation_obs[warn_idx], s=18, c="red", label="预警点")
    truth_idx = np.where(truth_anomaly == 1)[0]
    axes[0].scatter(truth_idx, deformation_obs[truth_idx], s=28, facecolors="none", edgecolors="gold", label="真实异常")
    axes[0].axvline(split, color="gray", ls="--", lw=1.0, label="训练/测试分界")
    axes[0].set_ylabel("位移 (mm)")
    axes[0].set_title("大坝变形监测仿真：观测、拟合与预警")
    axes[0].legend(loc="best", ncol=3)
    axes[0].grid(alpha=0.25)

    # 图2：残差控制图
    res_smooth = savgol_filter(residual, 31, 3)
    axes[1].plot(day, residual, lw=1.0, color="#2ca02c", label="残差")
    axes[1].plot(day, res_smooth, lw=2.0, color="#9467bd", label="残差平滑")
    axes[1].axhline(mu_r + threshold, color="r", ls="--", lw=1.2, label="上控制限")
    axes[1].axhline(mu_r - threshold, color="r", ls="--", lw=1.2, label="下控制限")
    axes[1].axhline(mu_r, color="k", ls=":", lw=1.0, label="残差均值")
    axes[1].set_ylabel("残差 (mm)")
    axes[1].set_title("残差控制图（理论阈值预警）")
    axes[1].legend(loc="best", ncol=4)
    axes[1].grid(alpha=0.25)

    # 图3：理论分量拆解
    hydro_part = beta_hat[1] * (water_level - H0)
    thermal_part = beta_hat[2] * temp
    creep_part = beta_hat[3] * creep
    axes[2].plot(day, hydro_part, lw=1.5, label="水压分量")
    axes[2].plot(day, thermal_part, lw=1.5, label="温度分量")
    axes[2].plot(day, creep_part, lw=1.5, label="时效分量")
    axes[2].set_xlabel("监测日")
    axes[2].set_ylabel("分量贡献 (mm)")
    axes[2].set_title("变形理论框架：驱动分量贡献")
    axes[2].legend(loc="best")
    axes[2].grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig('ch01_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch01_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
