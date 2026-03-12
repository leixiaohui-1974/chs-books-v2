# -*- coding: utf-8 -*-
"""
教材：《数字孪生流域》
章节：第3章 水文-水动力耦合模型（3.1 基本概念与理论框架）
功能：实现“降雨 -> 产汇流 -> 河道水动力演进”的耦合仿真，打印KPI结果表并绘图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.signal import fftconvolve
from scipy.special import gamma
from scipy.interpolate import interp1d
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

# ===================== 1) 关键参数定义（可按教学场景调整） =====================
# 时间参数
SIM_HOURS = 72.0          # 总模拟时长（小时）
DT_HOURS = 0.25           # 时间步长（小时）

# 流域产流参数
BASIN_AREA_KM2 = 520.0    # 流域面积（km^2）
SM_MAX = 120.0            # 土壤含水最大容量（mm）
SM_INIT = 70.0            # 初始土壤含水（mm）
KSAT = 8.0                # 饱和入渗能力基准（mm/h）
F_MIN = 1.0               # 最小入渗能力（mm/h）
ET_RATE = 0.08            # 蒸散发强度（mm/h）
K_PERC = 0.02             # 下渗系数（1/h）

# Nash汇流参数
NASH_N = 3                # 级联水库个数
NASH_K_H = 2.0            # 衰减时间常数（h）
UH_MAX_H = 24.0           # 单位线截断时长（h）

# 耦合分配参数
Q_BASE = 25.0             # 河道基流（m^3/s）
BASEFLOW_FACTOR = 0.35    # 地下径流折减系数
LATERAL_SHARE = 0.40      # 侧向汇入比例（其余作为上游边界入流）

# 河道水动力参数（线性化圣维南思想：对流-扩散-衰减）
RIVER_LENGTH_M = 50_000.0 # 河道长度（m）
NX = 80                   # 空间离散节点数
WAVE_C = 1.2              # 洪波波速（m/s）
DIFFUSIVITY = 180.0       # 水动力扩散系数（m^2/s）
ALPHA = 1.0 / (20.0 * 3600.0)  # 衰减系数（1/s）
TAU_UP = 900.0            # 上游边界松弛时间（s）

# 水位换算参数（矩形断面+曼宁公式）
WIDTH_M = 60.0            # 河宽（m）
MANNING_N = 0.035         # 曼宁糙率
BED_SLOPE = 4e-4          # 河床比降
DATUM_Z = 100.0           # 水位基准高程（m）

# KPI评估（构造伪观测）
OBS_LAG_H = 0.75          # 伪观测时滞（h）
OBS_SCALE_BIAS = -0.03    # 伪观测比例偏差
OBS_NOISE_STD = 3.0       # 伪观测噪声标准差（m^3/s）

# 绘图中文设置（若系统无中文字体，可删去本段）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ===================== 2) 时间序列与降雨过程 =====================
n_steps = int(SIM_HOURS / DT_HOURS) + 1
t_h = np.arange(n_steps) * DT_HOURS
t_s = t_h * 3600.0

# 用三个高斯雨团构造教学降雨过程（mm/h）
rain = (
    20.0 * np.exp(-0.5 * ((t_h - 12.0) / 2.0) ** 2)
    + 35.0 * np.exp(-0.5 * ((t_h - 24.0) / 3.0) ** 2)
    + 15.0 * np.exp(-0.5 * ((t_h - 40.0) / 4.0) ** 2)
)
rain[rain < 0.05] = 0.0

# ===================== 3) 水文模块：土壤蓄水 + 产流 =====================
S = np.zeros(n_steps)             # 土壤含水量（mm）
S[0] = SM_INIT
excess = np.zeros(n_steps)        # 地表超渗产流（mm/h）
baseflow_mm = np.zeros(n_steps)   # 基流生成（mm/h）

for i in range(n_steps - 1):
    # 入渗能力随土壤湿润程度下降
    infil_capacity = max(KSAT * (1.0 - S[i] / SM_MAX), F_MIN)
    infil = min(rain[i], infil_capacity)

    # 超渗产流
    excess[i] = max(rain[i] - infil, 0.0)

    # 土壤水量平衡
    percolation = K_PERC * S[i]
    dS = (infil - percolation - ET_RATE) * DT_HOURS
    S[i + 1] = np.clip(S[i] + dS, 0.0, SM_MAX)
    baseflow_mm[i] = max(percolation, 0.0)

excess[-1] = excess[-2]
baseflow_mm[-1] = baseflow_mm[-2]

# ===================== 4) 汇流模块：Nash单位线卷积 =====================
tau = np.arange(0.0, UH_MAX_H + DT_HOURS, DT_HOURS)
uh = (tau ** (NASH_N - 1) * np.exp(-tau / NASH_K_H)) / ((NASH_K_H ** NASH_N) * gamma(NASH_N))
uh[0] = 0.0
uh = uh / (np.sum(uh) * DT_HOURS)  # 保证单位线积分为1

quick_mm = fftconvolve(excess, uh, mode="full")[:n_steps] * DT_HOURS

# 转换为流量（m^3/s）
area_m2 = BASIN_AREA_KM2 * 1e6
quick_q = quick_mm / 1000.0 * area_m2 / 3600.0
base_q = BASEFLOW_FACTOR * baseflow_mm / 1000.0 * area_m2 / 3600.0
q_generated = quick_q + base_q

# 耦合方式：部分作为上游边界，部分作为沿程侧向入流
q_inlet = Q_BASE + (1.0 - LATERAL_SHARE) * q_generated
q_lateral_line = LATERAL_SHARE * q_generated / RIVER_LENGTH_M  # m^3/s/m

# ===================== 5) 水动力模块：1D对流-扩散-衰减方程 =====================
qin_fun = interp1d(t_s, q_inlet, kind="linear", bounds_error=False, fill_value=(q_inlet[0], q_inlet[-1]))
ql_fun = interp1d(t_s, q_lateral_line, kind="linear", bounds_error=False, fill_value=(q_lateral_line[0], q_lateral_line[-1]))

dx = RIVER_LENGTH_M / (NX - 1)

def rhs(t, q):
    """河道离散节点流量的时间导数。"""
    dq = np.zeros_like(q)
    qin = float(qin_fun(t))
    ql = float(ql_fun(t))

    # 上游边界：松弛到耦合入流
    dq[0] = (qin - q[0]) / TAU_UP

    # 内部节点：上风对流 + 中心扩散 + 源汇项
    for j in range(1, NX - 1):
        advec = -WAVE_C * (q[j] - q[j - 1]) / dx
        diff = DIFFUSIVITY * (q[j + 1] - 2.0 * q[j] + q[j - 1]) / dx**2
        dq[j] = advec + diff + ql - ALPHA * q[j]

    # 下游边界：零梯度近似
    advec_d = -WAVE_C * (q[-1] - q[-2]) / dx
    diff_d = DIFFUSIVITY * (q[-2] - q[-1]) / dx**2
    dq[-1] = advec_d + diff_d + ql - ALPHA * q[-1]
    return dq

q0 = np.full(NX, Q_BASE)
sol = solve_ivp(rhs, (t_s[0], t_s[-1]), q0, t_eval=t_s, method="BDF", rtol=1e-6, atol=1e-6)
if not sol.success:
    raise RuntimeError("水动力求解失败，请检查参数配置。")

Q_xt = sol.y
Q_mid = Q_xt[NX // 2]
Q_out = Q_xt[-1]

# ===================== 6) 流量-水位换算（曼宁公式反解） =====================
def discharge_to_depth(q):
    """由流量反求水深（矩形断面）。"""
    q = max(float(q), 1e-6)

    def fn(y):
        A = WIDTH_M * y
        P = WIDTH_M + 2.0 * y
        R = A / P
        q_calc = (1.0 / MANNING_N) * A * (R ** (2.0 / 3.0)) * np.sqrt(BED_SLOPE)
        return q_calc - q

    return brentq(fn, 1e-3, 20.0)

depth_out = np.array([discharge_to_depth(v) for v in Q_out])
wl_out = DATUM_Z + depth_out

# ===================== 7) 构造伪观测并计算KPI =====================
np.random.seed(2026)
shift_steps = int(OBS_LAG_H / DT_HOURS)
Q_obs = np.roll(Q_out, shift_steps) * (1.0 + OBS_SCALE_BIAS) + np.random.normal(0.0, OBS_NOISE_STD, n_steps)
Q_obs = np.clip(Q_obs, 0.0, None)

def nse(sim, obs):
    den = np.sum((obs - np.mean(obs)) ** 2)
    if den <= 1e-12:
        return np.nan
    return 1.0 - np.sum((sim - obs) ** 2) / den

rmse = np.sqrt(np.mean((Q_out - Q_obs) ** 2))
peak_sim = float(np.max(Q_out))
peak_obs = float(np.max(Q_obs))
tp_sim = float(t_h[np.argmax(Q_out)])
tp_obs = float(t_h[np.argmax(Q_obs)])
peak_err = (peak_sim - peak_obs) / max(peak_obs, 1e-6) * 100.0
peak_lag = tp_sim - tp_obs

vol_sim = float(np.trapz(Q_out, t_s))
vol_obs = float(np.trapz(Q_obs, t_s))
vol_bias = (vol_sim - vol_obs) / max(vol_obs, 1e-6) * 100.0

rain_total_mm = float(np.sum(rain) * DT_HOURS)
runoff_depth_mm = vol_sim / area_m2 * 1000.0
runoff_coef = runoff_depth_mm / max(rain_total_mm, 1e-6)

kpi_rows = [
    ("总降雨量 (mm)", f"{rain_total_mm:.2f}"),
    ("模拟径流深 (mm)", f"{runoff_depth_mm:.2f}"),
    ("径流系数 (-)", f"{runoff_coef:.3f}"),
    ("模拟洪峰 (m3/s)", f"{peak_sim:.2f}"),
    ("伪观测洪峰 (m3/s)", f"{peak_obs:.2f}"),
    ("洪峰相对误差 (%)", f"{peak_err:.2f}"),
    ("洪峰时差 (h)", f"{peak_lag:.2f}"),
    ("RMSE (m3/s)", f"{rmse:.2f}"),
    ("NSE (-)", f"{nse(Q_out, Q_obs):.3f}"),
    ("总量偏差 (%)", f"{vol_bias:.2f}"),
    ("最高水位 (m)", f"{np.max(wl_out):.2f}"),
]

def print_kpi_table(rows):
    c1 = max(len(r[0]) for r in rows + [("指标", "")]) + 2
    c2 = max(len(r[1]) for r in rows + [("", "数值")]) + 2
    line = "+" + "-" * c1 + "+" + "-" * c2 + "+"
    print("\nKPI结果表")
    print(line)
    print(f"|{'指标'.ljust(c1)}|{'数值'.ljust(c2)}|")
    print(line)
    for k, v in rows:
        print(f"|{k.ljust(c1)}|{v.ljust(c2)}|")
    print(line)

print_kpi_table(kpi_rows)

# ===================== 8) 绘图展示 =====================
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# 图1：降雨
axes[0].bar(t_h, rain, width=DT_HOURS, color="#4C78A8", edgecolor="white")
axes[0].invert_yaxis()
axes[0].set_ylabel("降雨 (mm/h)")
axes[0].set_title("水文-水动力耦合仿真结果")

# 图2：流量与水位
axes[1].plot(t_h, q_inlet, lw=1.6, label="上游入流(耦合)")
axes[1].plot(t_h, Q_mid, lw=1.6, label="中段流量")
axes[1].plot(t_h, Q_out, lw=2.0, label="下游出流(模拟)")
axes[1].plot(t_h, Q_obs, "--", lw=1.4, label="下游出流(伪观测)")
axes[1].set_ylabel("流量 (m3/s)")
ax2 = axes[1].twinx()
ax2.plot(t_h, wl_out, color="#54A24B", lw=1.4, alpha=0.85, label="下游水位")
ax2.set_ylabel("水位 (m)")

h1, l1 = axes[1].get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
axes[1].legend(h1 + h2, l1 + l2, loc="upper right", ncol=2, fontsize=9)

# 图3：河道流量时空分布
im = axes[2].imshow(
    Q_xt,
    aspect="auto",
    origin="lower",
    extent=[t_h[0], t_h[-1], 0, RIVER_LENGTH_M / 1000.0],
    cmap="viridis",
)
cb = fig.colorbar(im, ax=axes[2], pad=0.01)
cb.set_label("流量 (m3/s)")
axes[2].set_ylabel("河道里程 (km)")
axes[2].set_xlabel("时间 (h)")
axes[2].set_title("河道流量时空演化")

plt.tight_layout()
plt.savefig('ch03_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch03_simulation_result.png")
# plt.show()  # 禁用弹窗
