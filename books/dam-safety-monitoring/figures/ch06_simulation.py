"""
书名：《大坝安全监测与预警》
章节：第6章 案例：混凝土坝/土石坝（6.1 基本概念与理论框架）
功能：构建“监测数据 -> 机理回归建模 -> 阈值预警 -> KPI评估 -> 图形展示”的完整仿真流程
"""

import numpy as np
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（可直接调参）
# =========================
N_DAYS = 365 * 2                  # 仿真天数
TRAIN_RATIO = 0.70                # 训练集比例
RANDOM_SEED = 2026                # 随机种子，保证可复现
CONCRETE_NOISE_STD = 0.60         # 混凝土坝观测噪声标准差
EARTH_NOISE_STD = 0.80            # 土石坝观测噪声标准差
N_ANOMALY = 12                    # 每类坝注入异常点个数
WARNING_K1 = 2.0                  # 一级预警阈值系数（k*sigma）
WARNING_K2 = 3.0                  # 二级预警阈值系数（k*sigma）

# 混凝土坝“真实”参数（用于生成仿真真值）
TRUE_CONCRETE = np.array([2.0, 0.070, 0.050, 1.20, -0.80, 0.030])
# 土石坝“真实”参数（用于生成仿真真值）
TRUE_EARTH = np.array([1.0, 0.050, 0.080, 0.180, 6.00, 0.015])

rng = np.random.default_rng(RANDOM_SEED)

# 中文显示设置（若本机无中文字体，可删除这两行）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 2) 数据生成与机理模型
# =========================
def generate_drivers(n_days: int, rng_obj):
    """生成外部驱动因子：库水位、气温、降雨。"""
    t = np.arange(n_days, dtype=float)

    # 库水位：年周期 + 随机扰动
    h = 100 + 10 * np.sin(2 * np.pi * t / 365 - 0.6) + rng_obj.normal(0, 1.2, n_days)
    # 气温：年周期 + 随机扰动
    temp = 15 + 12 * np.sin(2 * np.pi * t / 365 - np.pi / 2) + rng_obj.normal(0, 1.0, n_days)
    # 降雨：Gamma随机 + 季节性调制
    rain = rng_obj.gamma(1.5, 5.0, n_days) * (0.3 + 0.7 * (np.sin(2 * np.pi * t / 365) + 1) / 2)

    return t, h, temp, rain


def concrete_model(p, t, h, temp):
    """
    混凝土坝响应模型（示例）：
    位移/效应 = 水位项 + 温度项 + 周期项 + 时效项
    """
    a0, a1, a2, a3, a4, a5 = p
    return (
        a0
        + a1 * h
        + a2 * temp
        + a3 * np.sin(2 * np.pi * t / 365)
        + a4 * np.cos(2 * np.pi * t / 365)
        + a5 * np.log1p(t)
    )


def earth_model(p, t, h, temp, rain):
    """
    土石坝响应模型（示例）：
    位移/渗流效应 = 水位项 + 降雨项 + 固结时变项 + 衰减项 + 温度项
    """
    b0, b1, b2, b3, b4, b5 = p
    return b0 + b1 * h + b2 * rain + b3 * np.sqrt(t + 1) + b4 * np.exp(-t / 500) + b5 * temp


def inject_observation_noise_and_anomaly(y_true, noise_std, n_anomaly, rng_obj):
    """叠加观测噪声并注入异常点，返回观测值与真实异常标签。"""
    y_obs = y_true + rng_obj.normal(0, noise_std, len(y_true))
    labels = np.zeros(len(y_true), dtype=int)

    anomaly_idx = rng_obj.choice(len(y_true), size=n_anomaly, replace=False)
    spike = rng_obj.normal(0, 4 * noise_std, n_anomaly) + rng_obj.choice([-1, 1], n_anomaly) * (5 * noise_std)
    y_obs[anomaly_idx] += spike
    labels[anomaly_idx] = 1
    return y_obs, labels


# =========================
# 3) 模型拟合、预警、KPI
# =========================
def fit_concrete_params(t, h, temp, y, train_end):
    """用最小二乘拟合混凝土坝模型参数。"""
    def residuals(p):
        return concrete_model(p, t[:train_end], h[:train_end], temp[:train_end]) - y[:train_end]

    p0 = np.array([0.0, 0.05, 0.02, 1.0, 1.0, 0.01])
    return least_squares(residuals, p0).x


def fit_earth_params(t, h, temp, rain, y, train_end):
    """用最小二乘拟合土石坝模型参数。"""
    def residuals(p):
        return earth_model(p, t[:train_end], h[:train_end], temp[:train_end], rain[:train_end]) - y[:train_end]

    p0 = np.array([0.0, 0.04, 0.03, 0.2, 5.0, 0.01])
    return least_squares(residuals, p0).x


def warning_levels(residual, train_end, k1=2.0, k2=3.0):
    """
    按训练期残差标准差建立预警阈值：
    |残差| > k1*sigma -> 一级预警
    |残差| > k2*sigma -> 二级预警
    """
    sigma = np.std(residual[:train_end], ddof=1)
    th1, th2 = k1 * sigma, k2 * sigma

    level = np.zeros_like(residual, dtype=int)
    abs_r = np.abs(residual)
    level[abs_r > th1] = 1
    level[abs_r > th2] = 2
    return level, th1, th2


def calc_kpi(y, yhat, true_anomaly, alarm2):
    """计算拟合与预警性能指标。"""
    err = y - yhat
    rmse = np.sqrt(np.mean(err ** 2))
    mae = np.mean(np.abs(err))
    r2 = 1 - np.sum(err ** 2) / np.sum((y - np.mean(y)) ** 2)

    tp = np.sum((alarm2 == 1) & (true_anomaly == 1))
    fp = np.sum((alarm2 == 1) & (true_anomaly == 0))
    fn = np.sum((alarm2 == 0) & (true_anomaly == 1))
    tn = np.sum((alarm2 == 0) & (true_anomaly == 0))

    precision = tp / (tp + fp + 1e-12)
    recall = tp / (tp + fn + 1e-12)
    false_alarm_rate = fp / (fp + tn + 1e-12)

    return {
        "RMSE": rmse,
        "MAE": mae,
        "R2": r2,
        "Precision": precision,
        "Recall": recall,
        "FalseAlarm": false_alarm_rate,
    }


def print_kpi_table(kpi_map):
    """打印KPI结果表格。"""
    print("\n================ KPI结果表 ================")
    print(f"{'坝型':<10}{'RMSE':>10}{'MAE':>10}{'R2':>10}{'Precision':>12}{'Recall':>10}{'FalseAlarm':>12}")
    print("-" * 74)
    for dam_name, k in kpi_map.items():
        print(
            f"{dam_name:<10}"
            f"{k['RMSE']:>10.3f}"
            f"{k['MAE']:>10.3f}"
            f"{k['R2']:>10.3f}"
            f"{k['Precision']:>12.3f}"
            f"{k['Recall']:>10.3f}"
            f"{k['FalseAlarm']:>12.3f}"
        )
    print("=" * 74)


def normalize(x):
    """用于多驱动同图展示的标准化。"""
    return (x - np.mean(x)) / (np.std(x) + 1e-12)


# =========================
# 4) 主流程
# =========================
if __name__ == "__main__":
    # 生成驱动因子
    t, h, temp, rain = generate_drivers(N_DAYS, rng)
    train_end = int(N_DAYS * TRAIN_RATIO)

    # 生成“真实响应”
    y_true_c = concrete_model(TRUE_CONCRETE, t, h, temp)
    y_true_e = earth_model(TRUE_EARTH, t, h, temp, rain)

    # 生成观测值并注入异常
    y_obs_c, label_c = inject_observation_noise_and_anomaly(y_true_c, CONCRETE_NOISE_STD, N_ANOMALY, rng)
    y_obs_e, label_e = inject_observation_noise_and_anomaly(y_true_e, EARTH_NOISE_STD, N_ANOMALY, rng)

    # 参数反演（拟合）
    p_hat_c = fit_concrete_params(t, h, temp, y_obs_c, train_end)
    p_hat_e = fit_earth_params(t, h, temp, rain, y_obs_e, train_end)

    # 全时段预测
    y_hat_c = concrete_model(p_hat_c, t, h, temp)
    y_hat_e = earth_model(p_hat_e, t, h, temp, rain)

    # 残差与预警
    res_c = y_obs_c - y_hat_c
    res_e = y_obs_e - y_hat_e
    lv_c, th1_c, th2_c = warning_levels(res_c, train_end, WARNING_K1, WARNING_K2)
    lv_e, th1_e, th2_e = warning_levels(res_e, train_end, WARNING_K1, WARNING_K2)

    # 二级预警作为“报警事件”用于KPI统计
    alarm2_c = (lv_c == 2).astype(int)
    alarm2_e = (lv_e == 2).astype(int)

    kpi_c = calc_kpi(y_obs_c, y_hat_c, label_c, alarm2_c)
    kpi_e = calc_kpi(y_obs_e, y_hat_e, label_e, alarm2_e)

    # 打印结果
    print("混凝土坝拟合参数:", np.round(p_hat_c, 4))
    print("土石坝拟合参数  :", np.round(p_hat_e, 4))
    print(f"混凝土坝阈值: 一级={th1_c:.3f}, 二级={th2_c:.3f}")
    print(f"土石坝阈值  : 一级={th1_e:.3f}, 二级={th2_e:.3f}")

    print_kpi_table({
        "混凝土坝": kpi_c,
        "土石坝": kpi_e
    })

    # 画图
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

    # 图1：驱动因子（标准化后同图）
    axes[0].plot(t, normalize(h), label="库水位(标准化)", linewidth=1.2)
    axes[0].plot(t, normalize(temp), label="气温(标准化)", linewidth=1.2)
    axes[0].plot(t, normalize(rain), label="降雨(标准化)", linewidth=1.2)
    axes[0].axvline(train_end, color="gray", linestyle="--", linewidth=1.0, label="训练/验证分界")
    axes[0].set_title("驱动因子时序")
    axes[0].legend(loc="upper right")
    axes[0].grid(alpha=0.25)

    # 图2：混凝土坝
    axes[1].plot(t, y_obs_c, label="观测值", color="#1f77b4", linewidth=1.0)
    axes[1].plot(t, y_hat_c, label="模型预测", color="#ff7f0e", linewidth=1.5)
    axes[1].scatter(t[lv_c == 1], y_obs_c[lv_c == 1], s=20, c="goldenrod", label="一级预警")
    axes[1].scatter(t[lv_c == 2], y_obs_c[lv_c == 2], s=28, c="red", label="二级预警")
    axes[1].axvline(train_end, color="gray", linestyle="--", linewidth=1.0)
    axes[1].set_title("混凝土坝：监测-预测-预警")
    axes[1].legend(loc="upper right")
    axes[1].grid(alpha=0.25)

    # 图3：土石坝
    axes[2].plot(t, y_obs_e, label="观测值", color="#2ca02c", linewidth=1.0)
    axes[2].plot(t, y_hat_e, label="模型预测", color="#d62728", linewidth=1.5)
    axes[2].scatter(t[lv_e == 1], y_obs_e[lv_e == 1], s=20, c="goldenrod", label="一级预警")
    axes[2].scatter(t[lv_e == 2], y_obs_e[lv_e == 2], s=28, c="red", label="二级预警")
    axes[2].axvline(train_end, color="gray", linestyle="--", linewidth=1.0)
    axes[2].set_title("土石坝：监测-预测-预警")
    axes[2].set_xlabel("时间（天）")
    axes[2].legend(loc="upper right")
    axes[2].grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig('ch06_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch06_simulation_result.png")
# plt.show()  # 禁用弹窗
