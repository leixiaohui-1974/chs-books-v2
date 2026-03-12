# -*- coding: utf-8 -*-
"""
教材：《洪水预报与防洪调度》
章节：第6章 洪水风险图与预警系统（6.1 基本概念与理论框架）
功能：基于“致灾因子-暴露度-脆弱性”框架构建洪水风险图，并评估分级预警KPI。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy import ndimage
from scipy.stats import genextreme, gamma

# =========================
# 1) 关键参数（可按教学需要调整）
# =========================
SEED = 42
N_EVENTS = 300                  # 蒙特卡洛洪水场次数
NX, NY = 140, 100               # 网格列数、行数
CELL_SIZE_M = 200               # 网格边长（米）
CELL_AREA_KM2 = (CELL_SIZE_M ** 2) / 1e6

# 洪峰流量GEV分布参数（用于随机生成洪水事件）
GEV_C = -0.12
GEV_LOC = 1800.0
GEV_SCALE = 420.0

# 水位-流量关系参数：H = H0 + A * Q^B
H0 = 24.0
RATING_A = 0.018
RATING_B = 0.62

# 河道外水位衰减（每1个网格距离衰减的水位，单位m）
DIST_ATTENUATION = 0.012

# 预报误差（对洪峰流量叠加高斯误差）
FORECAST_Q_STD = 220.0

# 预警阈值（单位：m）
LEVEL_YELLOW = 30.0
LEVEL_ORANGE = 31.0
LEVEL_RED = 32.0
LEVEL_DANGER = 31.0             # 判定“危险洪水事件”的真实阈值

# 风险计算参数
DEPTH_NORM = 2.5                # 将水深归一化到[0,1]时的特征深度
ASSET_VALUE_PER_KM2 = 1800.0    # 单位面积资产价值（万元/km2）

# 图形输出控制
SHOW_FIGURE = True
SAVE_FIGURE = False
FIG_NAME = "chapter6_flood_risk_warning.png"


def rating_curve(q):
    """水位-流量关系曲线。"""
    q = np.maximum(q, 1.0)
    return H0 + RATING_A * np.power(q, RATING_B)


def build_terrain(rng):
    """构造教学用地形DEM（高程场）。"""
    x = np.linspace(0, 1, NX)
    y = np.linspace(0, 1, NY)
    X, Y = np.meshgrid(x, y)

    # 大尺度地形趋势 + 起伏项
    base = 28.5 + 4.0 * (1 - Y) + 1.2 * np.sin(3 * np.pi * X) * np.cos(2 * np.pi * Y)
    noise = rng.normal(0, 0.8, size=(NY, NX))
    dem = ndimage.gaussian_filter(base + noise, sigma=2.2)
    return X, Y, dem


def build_river_distance():
    """构造弯曲河道并计算每个网格到河道的欧式距离。"""
    cols = np.arange(NX)
    river_row = (NY * (0.52 + 0.18 * np.sin(2 * np.pi * cols / NX))).astype(int)
    river_row = np.clip(river_row, 0, NY - 1)

    river_mask = np.zeros((NY, NX), dtype=bool)
    river_mask[river_row, cols] = True

    # 距离变换：计算每个格点到最近河道格点的距离（单位：网格）
    dist_to_river = ndimage.distance_transform_edt(~river_mask)
    return river_mask, dist_to_river


def calc_metrics(obs, pred):
    """二分类预警KPI：POD, FAR, CSI。"""
    hits = np.sum(obs & pred)
    misses = np.sum(obs & (~pred))
    false_alarms = np.sum((~obs) & pred)

    pod = hits / (hits + misses + 1e-12)
    far = false_alarms / (hits + false_alarms + 1e-12)
    csi = hits / (hits + misses + false_alarms + 1e-12)
    return pod, far, csi, hits, misses, false_alarms


def print_kpi_table(kpi):
    """打印KPI结果表格。"""
    print("\n=== KPI结果表（第6章：洪水风险图与预警系统）===")
    print(f"{'指标':<24} | {'数值':>14}")
    print("-" * 43)
    for k, v in kpi.items():
        if isinstance(v, float):
            print(f"{k:<24} | {v:>14.3f}")
        else:
            print(f"{k:<24} | {str(v):>14}")


def main():
    rng = np.random.default_rng(SEED)

    # 2) 构建地形、河道、暴露度与脆弱性
    X, Y, dem = build_terrain(rng)
    river_mask, dist_to_river = build_river_distance()

    # 暴露度：假设城镇中心在(0.62, 0.42)附近
    exposure = 0.35 + 0.65 * np.exp(-((X - 0.62) ** 2 + (Y - 0.42) ** 2) / 0.035)

    # 脆弱性：地势越低，脆弱性越高
    dem_norm = (dem - dem.min()) / (dem.max() - dem.min() + 1e-12)
    vulnerability = np.clip(0.25 + 0.75 * (1 - dem_norm), 0, 1)

    # 3) 随机生成洪峰事件（真实）与预报洪峰（带误差）
    q_true = genextreme.rvs(c=GEV_C, loc=GEV_LOC, scale=GEV_SCALE, size=N_EVENTS, random_state=rng)
    q_true = np.clip(q_true, 200.0, None)

    q_forecast = q_true + rng.normal(0, FORECAST_Q_STD, size=N_EVENTS)
    q_forecast = np.clip(q_forecast, 50.0, None)

    wl_true = rating_curve(q_true)
    wl_forecast = rating_curve(q_forecast)

    # 4) 洪水淹没深度与风险图计算
    effective_wl = wl_true[:, None, None] - DIST_ATTENUATION * dist_to_river[None, :, :]
    depth_all = np.maximum(0.0, effective_wl - dem[None, :, :])

    hazard = np.clip(depth_all / DEPTH_NORM, 0, 1)
    risk_all = hazard * exposure[None, :, :] * vulnerability[None, :, :]
    mean_risk_map = risk_all.mean(axis=0)

    flooded_area = (depth_all > 0.05).sum(axis=(1, 2)) * CELL_AREA_KM2
    loss_wanyuan = risk_all.sum(axis=(1, 2)) * ASSET_VALUE_PER_KM2 * CELL_AREA_KM2

    # 5) 预警分级（按预报水位）
    warning_level = np.full(N_EVENTS, "蓝色", dtype=object)
    warning_level[wl_forecast >= LEVEL_YELLOW] = "黄色"
    warning_level[wl_forecast >= LEVEL_ORANGE] = "橙色"
    warning_level[wl_forecast >= LEVEL_RED] = "红色"

    danger_obs = wl_true >= LEVEL_DANGER
    warning_pred = wl_forecast >= LEVEL_ORANGE  # 将橙色及以上视为“触发警报”

    pod, far, csi, hits, misses, false_alarms = calc_metrics(danger_obs, warning_pred)
    rmse = np.sqrt(np.mean((wl_forecast - wl_true) ** 2))

    # 6) 打印KPI表格
    kpi = {
        "总模拟场次": N_EVENTS,
        "危险洪水场次": int(np.sum(danger_obs)),
        "水位预报RMSE(m)": rmse,
        "命中率POD": pod,
        "空报率FAR": far,
        "临界成功指数CSI": csi,
        "平均淹没面积(km2)": float(np.mean(flooded_area)),
        "95%分位淹没面积(km2)": float(np.percentile(flooded_area, 95)),
        "平均风险指数": float(np.mean(mean_risk_map)),
        "平均预期损失(万元)": float(np.mean(loss_wanyuan)),
        "命中数Hits": int(hits),
        "漏报数Misses": int(misses),
        "空报数FalseAlarms": int(false_alarms),
    }
    print_kpi_table(kpi)

    print("\n预警等级统计：")
    for c in ["蓝色", "黄色", "橙色", "红色"]:
        print(f"{c}: {np.sum(warning_level == c)} 场")

    # 7) 选取95%分位洪峰对应事件展示淹没图
    rep_idx = np.argsort(q_true)[int(0.95 * N_EVENTS) - 1]
    rep_depth = depth_all[rep_idx]
    rep_peak = q_true[rep_idx]

    # 构造代表性过程线（用于展示阈值预警逻辑）
    t = np.linspace(0, 72, 320)  # 小时
    g = gamma.pdf(t, a=5.0, scale=6.0)
    g = g / (g.max() + 1e-12)
    q_hydro = 300 + rep_peak * g
    wl_hydro = rating_curve(q_hydro)

    # 8) 绘图
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "sans-serif"]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # 图1：地形与河道
    im0 = axes[0, 0].imshow(dem, cmap="terrain")
    axes[0, 0].contour(river_mask.astype(float), levels=[0.5], colors="deepskyblue", linewidths=1.2)
    axes[0, 0].set_title("地形DEM与河道")
    axes[0, 0].set_xlabel("X网格")
    axes[0, 0].set_ylabel("Y网格")
    fig.colorbar(im0, ax=axes[0, 0], shrink=0.85, label="高程(m)")

    # 图2：代表事件淹没深度图
    im1 = axes[0, 1].imshow(rep_depth, cmap="Blues")
    axes[0, 1].set_title("95%分位洪峰事件淹没深度")
    axes[0, 1].set_xlabel("X网格")
    axes[0, 1].set_ylabel("Y网格")
    fig.colorbar(im1, ax=axes[0, 1], shrink=0.85, label="水深(m)")

    # 图3：平均风险图
    im2 = axes[1, 0].imshow(mean_risk_map, cmap="YlOrRd", vmin=0, vmax=1)
    axes[1, 0].set_title("平均洪水风险图（Hazard×Exposure×Vulnerability）")
    axes[1, 0].set_xlabel("X网格")
    axes[1, 0].set_ylabel("Y网格")
    fig.colorbar(im2, ax=axes[1, 0], shrink=0.85, label="风险指数(0-1)")

    # 图4：代表性水位过程与预警阈值
    axes[1, 1].plot(t, wl_hydro, color="navy", lw=2, label="代表事件水位过程")
    axes[1, 1].axhline(LEVEL_YELLOW, color="gold", ls="--", lw=1.5, label="黄色阈值")
    axes[1, 1].axhline(LEVEL_ORANGE, color="darkorange", ls="--", lw=1.5, label="橙色阈值")
    axes[1, 1].axhline(LEVEL_RED, color="red", ls="--", lw=1.5, label="红色阈值")
    axes[1, 1].set_title("预警阈值示意（代表洪水过程）")
    axes[1, 1].set_xlabel("时间(h)")
    axes[1, 1].set_ylabel("水位(m)")
    axes[1, 1].grid(alpha=0.25)
    axes[1, 1].legend(fontsize=9)

    plt.tight_layout()

    if SAVE_FIGURE:
        plt.savefig(FIG_NAME, dpi=200, bbox_inches="tight")
        print(f"\n图件已保存：{FIG_NAME}")

    if SHOW_FIGURE:
        # plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
