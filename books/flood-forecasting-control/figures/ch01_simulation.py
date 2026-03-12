#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《洪水预报与防洪调度》- 第1章《洪水成因与暴雨设计》1.1 基本概念与理论框架
功能：构建“设计暴雨 -> 产流 -> 汇流 -> 防洪调度”仿真链条，输出KPI表格并绘制过程图。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy.stats import gamma
from scipy.integrate import trapezoid
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt


# ======================
# 一、关键参数（可直接修改）
# ======================
DT_MIN = 10                      # 计算时步（分钟）
DURATION_HR = 24                 # 暴雨历时（小时）
RETURN_PERIOD_YR = 50            # 设计重现期（年）
PEAK_RATIO = 0.40                # 芝加哥雨型峰现系数（0~1）

# IDF强度经验参数：i = a / (t + b)^n，t: min, i: mm/h
IDF_A = 920.0
IDF_B = 18.0
IDF_N = 0.73

AREA_KM2 = 210.0                 # 流域面积（km2）
CN = 78.0                        # SCS-CN曲线数

NASH_N = 3.2                     # Nash模型级数参数
NASH_K_HR = 1.6                  # Nash模型储蓄系数（小时）

ROUTING_K_HR = 3.5               # 线性水库调蓄系数（小时）


def idf_intensity(t_min: np.ndarray, a: float, b: float, n: float) -> np.ndarray:
    """IDF强度公式，避免t=0奇异。"""
    t_eff = np.maximum(t_min, 1.0)
    return a / ((t_eff + b) ** n)


def build_design_storm(duration_hr: float, dt_min: float, peak_ratio: float):
    """构造简化芝加哥雨型，返回时间序列、雨强、雨量。"""
    dt_hr = dt_min / 60.0
    t = np.arange(0, duration_hr + dt_hr, dt_hr)
    tp = peak_ratio * duration_hr

    i_mm_hr = np.zeros_like(t)
    for k, tk in enumerate(t):
        if tk <= tp:
            td = (tp - tk) * 60.0 + dt_min / 2.0
        else:
            td = (tk - tp) * 60.0 + dt_min / 2.0
        i_mm_hr[k] = idf_intensity(np.array([td]), IDF_A, IDF_B, IDF_N)[0]

    rain_mm = i_mm_hr * dt_hr
    return t, i_mm_hr, rain_mm


def scs_cn_excess(rain_mm: np.ndarray, cn: float, dt_min: float):
    """SCS-CN损失法：总雨量 -> 有效降雨。"""
    dt_hr = dt_min / 60.0
    s_mm = 25400.0 / cn - 254.0
    ia_mm = 0.2 * s_mm

    cum_p = np.cumsum(rain_mm)
    cum_pe = np.where(
        cum_p > ia_mm,
        (cum_p - ia_mm) ** 2 / (cum_p - ia_mm + s_mm),
        0.0,
    )

    pe_mm = np.diff(np.r_[0.0, cum_pe])
    pe_i_mm_hr = pe_mm / dt_hr
    return pe_mm, pe_i_mm_hr, s_mm, ia_mm


def nash_transform(pe_i_mm_hr: np.ndarray, t_hr: np.ndarray, area_km2: float, n: float, k_hr: float, dt_min: float):
    """Nash瞬时单位线汇流：有效雨强 -> 入流过程线。"""
    dt_hr = dt_min / 60.0
    area_m2 = area_km2 * 1e6

    # 单位线（Gamma分布），并做积分归一化
    u = gamma.pdf(t_hr, a=n, scale=k_hr)
    u = u / np.sum(u * dt_hr)

    # 离散卷积：e(mm/h) * u(1/h) * dt = q_depth(mm/h)
    q_depth_mm_hr = np.convolve(pe_i_mm_hr, u, mode="full")[: len(t_hr)] * dt_hr

    # 径流深换算流量：Q = h * A / 3600
    q_in = q_depth_mm_hr / 1000.0 * area_m2 / 3600.0
    return u, q_in


def linear_reservoir_routing(q_in: np.ndarray, dt_min: float, k_hr: float):
    """线性水库调蓄，近似防洪调度演算。"""
    dt_sec = dt_min * 60.0
    k_sec = k_hr * 3600.0

    q_out = np.zeros_like(q_in)
    for i in range(1, len(q_in)):
        q_out[i] = q_out[i - 1] + dt_sec / k_sec * (q_in[i] - q_out[i - 1])
    return q_out


def print_kpi_table(kpis):
    """打印KPI结果表格。"""
    print("\nKPI结果表（第1章 1.1 仿真）")
    print("=" * 62)
    print(f"{'指标':<22}{'数值':>20}{'单位':>14}")
    print("-" * 62)
    for name, value, unit in kpis:
        print(f"{name:<22}{value:>20}{unit:>14}")
    print("=" * 62)


def main():
    # 1) 设计暴雨
    t_hr, i_mm_hr, rain_mm = build_design_storm(DURATION_HR, DT_MIN, PEAK_RATIO)

    # 2) 产流（有效降雨）
    pe_mm, pe_i_mm_hr, s_mm, ia_mm = scs_cn_excess(rain_mm, CN, DT_MIN)

    # 3) 汇流（入流）
    u, q_in = nash_transform(pe_i_mm_hr, t_hr, AREA_KM2, NASH_N, NASH_K_HR, DT_MIN)

    # 4) 调蓄（出流）
    q_out = linear_reservoir_routing(q_in, DT_MIN, ROUTING_K_HR)

    # 5) KPI计算
    dt_sec = DT_MIN * 60.0
    total_rain = np.sum(rain_mm)
    total_pe = np.sum(pe_mm)
    runoff_coeff = total_pe / total_rain if total_rain > 0 else np.nan

    peak_in = np.max(q_in)
    peak_out = np.max(q_out)
    cut_rate = (peak_in - peak_out) / peak_in * 100.0 if peak_in > 0 else 0.0

    t_peak_in = t_hr[np.argmax(q_in)]
    t_peak_out = t_hr[np.argmax(q_out)]
    lag_hr = t_peak_out - t_peak_in

    v_in = trapezoid(q_in, dx=dt_sec)
    v_out = trapezoid(q_out, dx=dt_sec)
    delta_storage = v_in - v_out

    kpi_rows = [
        ("设计重现期", f"{RETURN_PERIOD_YR:.0f}", "年"),
        ("SCS潜在滞蓄量S", f"{s_mm:.2f}", "mm"),
        ("初损Ia", f"{ia_mm:.2f}", "mm"),
        ("总降雨量", f"{total_rain:.2f}", "mm"),
        ("有效降雨量", f"{total_pe:.2f}", "mm"),
        ("径流系数", f"{runoff_coeff:.3f}", "-"),
        ("入流洪峰", f"{peak_in:.2f}", "m3/s"),
        ("出流洪峰", f"{peak_out:.2f}", "m3/s"),
        ("削峰率", f"{cut_rate:.2f}", "%"),
        ("峰现滞后", f"{lag_hr:.2f}", "h"),
        ("过程总入流量", f"{v_in / 1e6:.3f}", "百万m3"),
        ("过程总出流量", f"{v_out / 1e6:.3f}", "百万m3"),
        ("期末库容增量", f"{delta_storage / 1e6:.3f}", "百万m3"),
    ]
    print_kpi_table(kpi_rows)

    # 6) 绘图
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

    axes[0].bar(t_hr, rain_mm, width=(DT_MIN / 60.0) * 0.9, color="#4F81BD", alpha=0.85, label="总降雨")
    axes[0].bar(t_hr, pe_mm, width=(DT_MIN / 60.0) * 0.6, color="#E67E22", alpha=0.9, label="有效降雨")
    axes[0].set_ylabel("雨量 (mm/Δt)")
    axes[0].set_title("设计暴雨与有效降雨过程")
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].plot(t_hr, u, color="#16A085", linewidth=2.0)
    axes[1].set_ylabel("u(t) (1/h)")
    axes[1].set_title("Nash瞬时单位线")
    axes[1].grid(alpha=0.25)

    axes[2].plot(t_hr, q_in, color="#C0392B", linewidth=2.2, label="入流过程")
    axes[2].plot(t_hr, q_out, color="#2E86C1", linewidth=2.2, label="出流过程（调蓄后）")
    axes[2].set_xlabel("时间 (h)")
    axes[2].set_ylabel("流量 (m3/s)")
    axes[2].set_title("洪水过程线与调蓄效果")
    axes[2].legend()
    axes[2].grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig('ch01_simulation_result.png', dpi=150)
    # plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
