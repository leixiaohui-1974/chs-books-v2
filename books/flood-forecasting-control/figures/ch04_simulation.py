# -*- coding: utf-8 -*-
# 教材：《洪水预报与防洪调度》
# 章节：4.1 基本概念与理论框架
# 功能：演示“降雨-产流预报 + 水库防洪调度”一体化仿真，并输出KPI与图形结果

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
from scipy.special import gamma

# ==============================
# 1) 关键参数（可直接修改）
# ==============================
dt_hour = 1.0                      # 时间步长（小时）
dt_sec = dt_hour * 3600.0          # 时间步长（秒）
T = 72                             # 仿真时长（小时）
t = np.arange(T) * dt_hour         # 时间序列

# 流域参数
catchment_area_km2 = 850.0         # 流域面积（km2）
runoff_coef = 0.62                 # 综合径流系数
uh_n = 3.0                         # Nash单位线参数 n
uh_k = 2.8                         # Nash单位线参数 k（小时）
baseflow = 120.0                   # 基流（m3/s）

# 水库与调度参数
S0 = 1.65e8                        # 初始库容（m3）
S_dead = 0.90e8                    # 死库容（m3）
S_flood_limit = 2.10e8             # 防洪限制库容（m3）
S_max = 2.55e8                     # 最大允许库容（m3）

Q_release_min = 180.0              # 最小下泄流量（m3/s）
Q_release_max = 2600.0             # 最大下泄流量（m3/s）
Q_safe_downstream = 1500.0         # 下游安全流量（m3/s）

# 水位-库容简化关系：H = H0 + alpha * (S - S_dead)
H0 = 92.0                          # 死库容对应水位（m）
alpha = 1.25e-7                    # 线性系数（m/m3）
H_flood_limit = H0 + alpha * (S_flood_limit - S_dead)

# ==============================
# 2) 构造设计暴雨过程（mm/h）
# ==============================
rain = (
    38.0 * np.exp(-0.5 * ((t - 26.0) / 6.0) ** 2)
    + 6.0 * np.exp(-0.5 * ((t - 16.0) / 3.0) ** 2)
)
rain = np.clip(rain, 0.0, None)

# ==============================
# 3) 降雨-产流（概念预报）
# ==============================
# 有效降雨（mm/h）
rain_eff = runoff_coef * rain

# Nash离散单位线
tau = np.arange(T) * dt_hour
u = (1.0 / (uh_k * gamma(uh_n))) * (tau / uh_k) ** (uh_n - 1.0) * np.exp(-tau / uh_k)
u[0] = 0.0
u = u / np.sum(u)                  # 归一化，保证体积守恒

# 卷积得到入库流量：1 mm * 1 km2 = 1000 m3
rain_to_q = catchment_area_km2 * 1000.0 / dt_sec
Q_direct = np.convolve(rain_eff, u, mode="full")[:T] * rain_to_q
Q_in = Q_direct + baseflow

# ==============================
# 4) 水库调度仿真函数
# ==============================
def simulate_reservoir(gain_k: float):
    """
    gain_k: 超限调节系数[(m3/s)/m3]
    返回: Q_out, S, H
    """
    S = np.zeros(T)
    H = np.zeros(T)
    Q_out = np.zeros(T)
    S[0] = S0

    for i in range(T):
        # 当前水位
        H[i] = H0 + alpha * (S[i] - S_dead)

        # 规则调度：未超限最小泄量，超限后按比例增泄
        exceed = max(0.0, S[i] - S_flood_limit)
        q_rule = Q_release_min + gain_k * exceed
        q_rule = np.clip(q_rule, Q_release_min, Q_release_max)

        # 库容逼近上限时，进行应急加泄（仍受最大泄量约束）
        if i < T - 1:
            q_need = (S[i] + Q_in[i] * dt_sec - S_max) / dt_sec
            if q_need > q_rule:
                q_rule = min(q_need, Q_release_max)

        Q_out[i] = q_rule

        # 连续方程更新库容
        if i < T - 1:
            S[i + 1] = S[i] + (Q_in[i] - Q_out[i]) * dt_sec
            S[i + 1] = np.clip(S[i + 1], S_dead, S_max)

    return Q_out, S, H

# ==============================
# 5) 用SciPy优化调度参数
# ==============================
def objective(gain_k: float):
    Q_out_tmp, S_tmp, _ = simulate_reservoir(gain_k)
    peak_out = np.max(Q_out_tmp)
    exceed_safe = np.maximum(Q_out_tmp - Q_safe_downstream, 0.0)
    exceed_storage = np.maximum(S_tmp - S_flood_limit, 0.0)

    # 目标：兼顾削峰与超限风险
    J = (
        1.0 * peak_out
        + 0.004 * np.sum(exceed_safe ** 2)
        + 1.2e-8 * np.sum(exceed_storage ** 2)
    )
    return J

opt = minimize_scalar(objective, bounds=(1e-6, 8e-5), method="bounded")
best_k = opt.x

Q_out, S, H = simulate_reservoir(best_k)

# ==============================
# 6) KPI计算并打印表格
# ==============================
peak_in = np.max(Q_in)
peak_out = np.max(Q_out)
peak_clip_rate = (peak_in - peak_out) / peak_in * 100.0
max_H = np.max(H)
max_S = np.max(S)
exceed_hours = int(np.sum(S > S_flood_limit))
final_S = S[-1]
water_balance_err = (S0 + np.sum(Q_in - Q_out) * dt_sec) - final_S

kpis = [
    ("入库洪峰流量", f"{peak_in:,.1f} m3/s"),
    ("出库洪峰流量", f"{peak_out:,.1f} m3/s"),
    ("洪峰削减率", f"{peak_clip_rate:.2f} %"),
    ("最高水位", f"{max_H:.2f} m"),
    ("最高库容", f"{max_S:,.0f} m3"),
    ("超防洪限制时长", f"{exceed_hours} h"),
    ("末时段库容", f"{final_S:,.0f} m3"),
    ("水量平衡误差", f"{water_balance_err:.3f} m3"),
    ("最优调节系数k", f"{best_k:.7f} (m3/s)/m3"),
]

print("\n=== KPI结果表（教材4.1） ===")
print("+------------------+--------------------------+")
print("| 指标             | 数值                     |")
print("+------------------+--------------------------+")
for name, val in kpis:
    print(f"| {name:<16} | {val:<24} |")
print("+------------------+--------------------------+")

# ==============================
# 7) 绘图
# ==============================
fig, axes = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(3, 1, figsize=(10, 11), sharex=True)

# 图1：暴雨过程
axes[0].bar(t, rain, width=0.9, color="#4C78A8", alpha=0.85, label="设计暴雨")
axes[0].set_ylabel("雨强 (mm/h)")
axes[0].set_title("降雨-洪水预报与防洪调度一体化仿真（4.1）")
axes[0].grid(True, alpha=0.25)
axes[0].legend(loc="upper right")

# 图2：入库/出库流量
axes[1].plot(t, Q_in, color="#F58518", lw=2.2, label="入库流量 Q_in")
axes[1].plot(t, Q_out, color="#54A24B", lw=2.2, label="出库流量 Q_out")
axes[1].axhline(Q_safe_downstream, color="red", ls="--", lw=1.3, label="下游安全流量")
axes[1].set_ylabel("流量 (m3/s)")
axes[1].grid(True, alpha=0.25)
axes[1].legend(loc="upper right")

# 图3：水位过程
axes[2].plot(t, H, color="#B279A2", lw=2.2, label="库水位 H")
axes[2].axhline(H_flood_limit, color="black", ls="--", lw=1.3, label="防洪限制水位")
axes[2].set_xlabel("时间 (h)")
axes[2].set_ylabel("水位 (m)")
axes[2].grid(True, alpha=0.25)
axes[2].legend(loc="upper right")

plt.tight_layout()
plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗
