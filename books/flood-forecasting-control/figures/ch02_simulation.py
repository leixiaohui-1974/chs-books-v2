# -*- coding: utf-8 -*-
"""
教材：《洪水预报与防洪调度》
章节：第2章 水文预报模型（2.1 基本概念与理论框架）
功能：构建“降雨-蒸散-产汇流”概念性水文预报模型，进行参数率定，输出KPI并绘图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# =========================
# 关键参数（可按教学需要调整）
# =========================
N_STEP = 180                 # 仿真时段长度（小时）
DT_HOUR = 1.0                # 时间步长（小时）
BASIN_AREA_KM2 = 1850.0      # 流域面积（km^2）
RANDOM_SEED = 42             # 随机种子（保证可复现）
OBS_NOISE_STD = 12.0         # 观测流量噪声标准差（m3/s）

# 参数初值与约束： [产流系数, 基流退水系数, 最大土壤蓄水量, 蒸散修正系数]
X0 = np.array([0.35, 0.06, 110.0, 0.80])
BOUNDS = [
    (0.05, 0.85),   # 产流系数 C_runoff
    (0.01, 0.20),   # 基流退水系数 K_base
    (60.0, 260.0),  # 最大土壤蓄水 S_max
    (0.30, 1.30),   # 蒸散修正 ET_coef
]


def depth_to_flow(q_mm, area_km2, dt_hour):
    """将径流深(mm/时段)换算为流量(m3/s)。"""
    area_m2 = area_km2 * 1e6
    volume_m3 = q_mm / 1000.0 * area_m2
    return volume_m3 / (dt_hour * 3600.0)


def generate_forcing(n_step, seed=42):
    """生成降雨与潜在蒸散序列（教学演示用）。"""
    rng = np.random.default_rng(seed)
    t = np.arange(n_step)

    # 基础随机降雨 + 几次暴雨脉冲
    rain = rng.gamma(shape=0.7, scale=2.2, size=n_step)
    storms = [(30, 16, 5), (72, 22, 7), (116, 30, 9), (150, 18, 6)]
    for center, amp, width in storms:
        rain += amp * np.exp(-0.5 * ((t - center) / width) ** 2)
    rain = np.clip(rain, 0.0, None)

    # 潜在蒸散：日周期 + 轻微扰动
    pet = 0.22 + 0.10 * np.sin(2 * np.pi * t / 24.0) + 0.04 * rng.random(n_step)
    pet = np.clip(pet, 0.05, None)
    return rain, pet


def conceptual_model(params, rain_mm, pet_mm, area_km2, dt_hour, s0=45.0):
    """
    概念模型（输入-状态-输出）：
    输入：降雨、潜在蒸散
    状态：土壤含水量 S
    输出：流量 Q
    """
    c_runoff, k_base, s_max, et_coef = params
    s = s0

    q_mm = np.zeros_like(rain_mm)
    s_series = np.zeros_like(rain_mm)

    for i, (p, e) in enumerate(zip(rain_mm, pet_mm)):
        # 1) 入渗：受土壤剩余容量约束
        infil_potential = (1.0 - c_runoff) * p
        infil_capacity = max(s_max - s, 0.0)
        infil = min(infil_potential, infil_capacity)

        # 2) 快速径流：固定比例地表产流 + 饱和超渗部分
        excess = max(infil_potential - infil, 0.0)
        quick = c_runoff * p + excess

        # 3) 更新土壤蓄水
        s += infil

        # 4) 实际蒸散
        et = min(s, et_coef * e)
        s -= et

        # 5) 基流退水（线性水库思想）
        base = k_base * s
        s -= base

        q_mm[i] = quick + base
        s_series[i] = s

    q_m3s = depth_to_flow(q_mm, area_km2, dt_hour)
    return q_m3s, s_series


def objective(x, rain, pet, q_obs):
    """率定目标函数：最小化RMSE。"""
    q_sim, _ = conceptual_model(x, rain, pet, BASIN_AREA_KM2, DT_HOUR)
    rmse = np.sqrt(np.mean((q_sim - q_obs) ** 2))
    return rmse


def calc_metrics(q_obs, q_sim):
    """计算常用KPI。"""
    eps = 1e-12
    nse = 1.0 - np.sum((q_obs - q_sim) ** 2) / (np.sum((q_obs - np.mean(q_obs)) ** 2) + eps)
    rmse = np.sqrt(np.mean((q_obs - q_sim) ** 2))
    mae = np.mean(np.abs(q_obs - q_sim))
    bias_pct = 100.0 * np.sum(q_sim - q_obs) / (np.sum(q_obs) + eps)
    peak_err_pct = 100.0 * (np.max(q_sim) - np.max(q_obs)) / (np.max(q_obs) + eps)
    corr = np.corrcoef(q_obs, q_sim)[0, 1]
    r2 = corr ** 2
    return {
        "NSE": nse,
        "RMSE(m3/s)": rmse,
        "MAE(m3/s)": mae,
        "BIAS(%)": bias_pct,
        "PEAK_ERR(%)": peak_err_pct,
        "R2": r2,
    }


def print_table(title, rows):
    """打印简单ASCII表格。"""
    w1, w2 = 20, 16
    line = "+" + "-" * w1 + "+" + "-" * w2 + "+"
    print("\n" + title)
    print(line)
    print(f"|{'指标/参数':^{w1}}|{'数值':^{w2}}|")
    print(line)
    for k, v in rows:
        print(f"|{k:^{w1}}|{v:^{w2}}|")
    print(line)


def main():
    # 字体设置（避免中文乱码，按系统可用字体自动回退）
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    # 1) 生成输入序列
    rain, pet = generate_forcing(N_STEP, seed=RANDOM_SEED)

    # 2) 构造“观测流量”（教学中可替换为实测数据）
    true_params = np.array([0.40, 0.045, 135.0, 0.88])
    q_true, _ = conceptual_model(true_params, rain, pet, BASIN_AREA_KM2, DT_HOUR)

    rng = np.random.default_rng(RANDOM_SEED + 10)
    q_obs = np.clip(q_true + rng.normal(0.0, OBS_NOISE_STD, size=N_STEP), 0.0, None)

    # 3) 参数率定（SciPy优化）
    result = minimize(
        objective,
        x0=X0,
        args=(rain, pet, q_obs),
        method="L-BFGS-B",
        bounds=BOUNDS,
    )
    best_params = result.x
    q_sim, s_sim = conceptual_model(best_params, rain, pet, BASIN_AREA_KM2, DT_HOUR)

    # 4) KPI计算并打印
    metrics = calc_metrics(q_obs, q_sim)
    param_rows = [
        ("C_runoff", f"{best_params[0]:.4f}"),
        ("K_base", f"{best_params[1]:.4f}"),
        ("S_max(mm)", f"{best_params[2]:.2f}"),
        ("ET_coef", f"{best_params[3]:.4f}"),
        ("优化是否成功", str(result.success)),
    ]
    kpi_rows = [(k, f"{v:.4f}") for k, v in metrics.items()]

    print_table("参数率定结果表", param_rows)
    print_table("KPI结果表（率定期）", kpi_rows)

    # 5) 绘图
    t = np.arange(N_STEP)
    fig, axes = plt.subplots(
        3, 1, figsize=(12, 9), sharex=True, gridspec_kw={"height_ratios": [1.2, 2.0, 1.2]}
    )

    axes[0].bar(t, rain, color="#4C78A8", width=1.0, label="降雨(mm/h)")
    axes[0].plot(t, pet, color="#F58518", linewidth=1.5, label="潜在蒸散(mm/h)")
    axes[0].set_ylabel("气象输入")
    axes[0].legend(loc="upper right")
    axes[0].grid(alpha=0.25)

    axes[1].plot(t, q_obs, color="#E45756", linewidth=1.8, label="观测流量")
    axes[1].plot(t, q_sim, color="#54A24B", linewidth=1.8, label="模拟流量")
    axes[1].set_ylabel("流量(m3/s)")
    axes[1].set_title("洪水预报概念模型：观测与模拟对比")
    axes[1].legend(loc="upper right")
    axes[1].grid(alpha=0.25)

    axes[2].plot(t, s_sim, color="#B279A2", linewidth=1.8, label="土壤含水状态S")
    axes[2].set_ylabel("S(mm)")
    axes[2].set_xlabel("时间步（小时）")
    axes[2].legend(loc="upper right")
    axes[2].grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig('ch02_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch02_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
