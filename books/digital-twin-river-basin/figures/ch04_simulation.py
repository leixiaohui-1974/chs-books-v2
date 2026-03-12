# -*- coding: utf-8 -*-
"""
《数字孪生流域》 第4章：模型自动校准与同化
小节：4.1 基本概念与理论框架
功能：在简化降雨-径流状态空间模型中，演示参数自动校准（Optimization）与数据同化（EnKF）。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 关键参数（可按教学需要修改）
# =========================
SEED = 42                 # 随机种子，保证可复现
N_STEPS = 180             # 总时长（时间步）
CAL_END = 90              # 校准期结束位置，后半段作为验证期
MISS_RATE = 0.12          # 观测缺测比例

OBS_STD = 2.0             # 观测噪声标准差
TRUE_PROCESS_STD = 0.6    # 真值系统过程噪声

TRUE_A = 0.86             # 真值参数a（流量记忆项）
TRUE_B = 1.75             # 真值参数b（降雨响应系数）
TRUE_Q0 = 8.0             # 真值初始流量

INIT_A = 0.60             # 初始猜测参数a
INIT_B = 1.10             # 初始猜测参数b
Q0_GUESS = 6.0            # 模型初始状态猜测

ENSEMBLE_SIZE = 80        # EnKF集合成员数
ENKF_PROCESS_STD = 0.8    # EnKF预报阶段过程噪声

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def generate_rainfall(n, rng_obj):
    """生成带有暴雨脉冲和枯水期特征的合成降雨序列"""
    rain = rng_obj.gamma(shape=1.6, scale=3.8, size=n)
    dry_mask = rng_obj.random(n) < 0.35
    rain[dry_mask] *= 0.2

    x = np.arange(n)
    for c in [28, 67, 115, 150]:
        rain += 10.0 * np.exp(-0.5 * ((x - c) / 2.8) ** 2)
    return rain


def simulate_discharge(params, rain, q0, process_std=0.0, rng_obj=None):
    """
    状态方程（简化线性形式）：
    Q_t = a * Q_(t-1) + b * P_t + w_t
    """
    a, b = params
    q = np.zeros_like(rain)
    q[0] = max(q0, 0.0)

    for t in range(1, len(rain)):
        noise = 0.0 if process_std <= 0 else rng_obj.normal(0.0, process_std)
        q[t] = a * q[t - 1] + b * rain[t] + noise
        q[t] = max(q[t], 0.0)
    return q


def objective(theta, rain, obs, q0):
    """自动校准目标函数：最小化均方误差（仅使用非缺测观测）"""
    a, b = theta
    if not (0.1 <= a <= 0.99 and 0.1 <= b <= 5.0):
        return 1e9

    sim = simulate_discharge((a, b), rain, q0)
    mask = ~np.isnan(obs)
    if mask.sum() < 10:
        return 1e9

    mse = np.mean((sim[mask] - obs[mask]) ** 2)
    return mse


def run_enkf(rain, obs, params, q0, ensemble_size, process_std, obs_std, rng_obj):
    """
    集合卡尔曼滤波（EnKF）同化：
    - 预报：每个集合成员按状态方程前推
    - 分析：若有观测，则按Kalman增益更新集合
    """
    a, b = params
    n = len(rain)

    # 初始化集合
    ens = np.full(ensemble_size, q0) + rng_obj.normal(0, 1.0, ensemble_size)
    ens = np.clip(ens, 0, None)

    q_analysis = np.zeros(n)
    q_forecast = np.zeros(n)
    k_hist = np.zeros(n)

    q_analysis[0] = ens.mean()
    q_forecast[0] = ens.mean()

    for t in range(1, n):
        # 1) 预报步
        ens = a * ens + b * rain[t] + rng_obj.normal(0, process_std, ensemble_size)
        ens = np.clip(ens, 0, None)
        q_forecast[t] = ens.mean()

        # 2) 分析步（有观测才更新）
        if not np.isnan(obs[t]):
            pf = np.var(ens, ddof=1) + 1e-6
            r = obs_std ** 2
            k = pf / (pf + r)  # Kalman增益

            # 扰动观测形式的EnKF
            y_pert = obs[t] + rng_obj.normal(0, obs_std, ensemble_size)
            ens = ens + k * (y_pert - ens)
            ens = np.clip(ens, 0, None)
            k_hist[t] = k
        else:
            k_hist[t] = 0.0

        q_analysis[t] = ens.mean()

    return q_analysis, q_forecast, k_hist


def calc_metrics(sim, truth):
    """计算KPI：RMSE、MAE、NSE、Bias、Corr"""
    rmse = np.sqrt(np.mean((sim - truth) ** 2))
    mae = np.mean(np.abs(sim - truth))
    denom = np.sum((truth - truth.mean()) ** 2)
    nse = 1 - np.sum((sim - truth) ** 2) / denom if denom > 0 else np.nan
    bias = np.mean(sim - truth)
    corr = np.corrcoef(sim, truth)[0, 1] if len(sim) > 1 else np.nan
    return rmse, mae, nse, bias, corr


def print_kpi_table(rows):
    """打印KPI结果表格"""
    headers = ["方案", "RMSE", "MAE", "NSE", "Bias", "Corr"]
    print("\n=== KPI结果表（验证期）===")
    print("-" * 79)
    print(f"{headers[0]:<18s}{headers[1]:>12s}{headers[2]:>10s}{headers[3]:>10s}{headers[4]:>10s}{headers[5]:>10s}")
    print("-" * 79)
    for r in rows:
        name, rmse, mae, nse, bias, corr = r
        print(f"{name:<18s}{rmse:>12.3f}{mae:>10.3f}{nse:>10.3f}{bias:>10.3f}{corr:>10.3f}")
    print("-" * 79)


def main():
    rng = np.random.default_rng(SEED)

    # 1) 构造“真值系统”和“观测”
    rain = generate_rainfall(N_STEPS, rng)
    q_true = simulate_discharge((TRUE_A, TRUE_B), rain, TRUE_Q0, process_std=TRUE_PROCESS_STD, rng_obj=rng)
    q_obs = np.clip(q_true + rng.normal(0, OBS_STD, N_STEPS), 0, None)

    # 引入缺测，贴近真实监测场景
    q_obs_nan = q_obs.copy()
    missing_idx = rng.choice(np.arange(N_STEPS), size=int(MISS_RATE * N_STEPS), replace=False)
    q_obs_nan[missing_idx] = np.nan

    # 2) 自动校准（仅使用校准期）
    result = minimize(
        objective,
        x0=np.array([INIT_A, INIT_B]),
        args=(rain[:CAL_END], q_obs_nan[:CAL_END], Q0_GUESS),
        method="L-BFGS-B",
        bounds=[(0.1, 0.99), (0.1, 5.0)],
        options={"maxiter": 300}
    )
    cal_a, cal_b = result.x

    # 3) 三种方案模拟：初始开环 / 校准开环 / 校准+同化
    q_init = simulate_discharge((INIT_A, INIT_B), rain, Q0_GUESS)
    q_cal = simulate_discharge((cal_a, cal_b), rain, Q0_GUESS)
    q_assim, q_forecast, k_hist = run_enkf(
        rain, q_obs_nan, (cal_a, cal_b), Q0_GUESS,
        ENSEMBLE_SIZE, ENKF_PROCESS_STD, OBS_STD, rng
    )

    # 4) KPI评估（验证期）
    idx = slice(CAL_END, None)
    rows = [
        ("初始参数开环",) + calc_metrics(q_init[idx], q_true[idx]),
        ("自动校准开环",) + calc_metrics(q_cal[idx], q_true[idx]),
        ("校准+EnKF同化",) + calc_metrics(q_assim[idx], q_true[idx]),
    ]

    # 5) 打印结果
    print("=== 参数信息 ===")
    print(f"真实参数: a={TRUE_A:.3f}, b={TRUE_B:.3f}")
    print(f"初始参数: a={INIT_A:.3f}, b={INIT_B:.3f}")
    print(f"校准参数: a={cal_a:.3f}, b={cal_b:.3f}")
    print(f"优化收敛: {result.success}, message={result.message}")
    print_kpi_table(rows)

    # 6) 绘图
    t = np.arange(N_STEPS)
    fig, axes = plt.subplots(
        3, 1, figsize=(12, 10), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0, 1.1]}
    )

    # 图1：流量过程线
    ax = axes[0]
    ax.plot(t, q_true, color="black", lw=2.0, label="真值流量")
    valid = ~np.isnan(q_obs_nan)
    ax.scatter(t[valid], q_obs_nan[valid], s=14, color="gray", alpha=0.55, label="观测流量")
    ax.plot(t, q_init, "--", color="#d62728", lw=1.6, label="初始参数开环")
    ax.plot(t, q_cal, "-", color="#1f77b4", lw=1.8, label="自动校准开环")
    ax.plot(t, q_assim, "-", color="#2ca02c", lw=2.0, label="校准+EnKF同化")
    ax.axvline(CAL_END, color="k", ls=":", lw=1.0)
    ax.text(CAL_END + 2, ax.get_ylim()[1] * 0.92, "验证期", fontsize=10)
    ax.set_ylabel("流量 Q")
    ax.set_title("第4章 4.1 模型自动校准与同化（简化示例）")
    ax.legend(loc="upper right", ncol=2, fontsize=9)
    ax.grid(alpha=0.2)

    # 图2：降雨过程
    ax = axes[1]
    ax.bar(t, rain, color="#4c78a8", width=0.9)
    ax.axvline(CAL_END, color="k", ls=":", lw=1.0)
    ax.set_ylabel("降雨 P")
    ax.grid(alpha=0.2)

    # 图3：误差对比
    ax = axes[2]
    ax.plot(t, q_cal - q_true, color="#1f77b4", lw=1.5, label="开环误差(校准)")
    ax.plot(t, q_assim - q_true, color="#2ca02c", lw=1.6, label="同化误差")
    ax.axhline(0.0, color="k", lw=1.0)
    ax.axvline(CAL_END, color="k", ls=":", lw=1.0)
    ax.set_ylabel("模拟误差")
    ax.set_xlabel("时间步")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
