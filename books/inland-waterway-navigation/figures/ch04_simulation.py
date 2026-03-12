# -*- coding: utf-8 -*-
"""
教材：《内河航道与通航水力学》
章节：航道渐变流与通航安全耦合仿真
功能：基于 Manning 公式与渐变流方程计算沿程水深，进一步评估船舶富余水深（UKC）、
输出 KPI 结果表，并绘制水力与通航安全图。
章节关键词：渐变流、Manning 糙率、弗劳德数、富余水深、通航能力
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（可按教学场景调整）
# =========================
g = 9.81                  # 重力加速度 (m/s^2)
L = 50_000.0              # 航段长度 (m)
b = 80.0                  # 航道等效底宽 (m)
S0 = 1.2e-4               # 河床坡降 (-)
n = 0.028                 # Manning 糙率
Q = 900.0                 # 设计流量 (m^3/s)
y_upstream = 7.0          # 上游控制断面水深 (m)

ship_draft = 3.2          # 船舶吃水 (m)
squat_coeff = 0.15        # 下沉量系数（经验）
ukc_required = 0.8        # 最小富余水深要求 (m)

nx = 400                  # 沿程离散点数

# =========================
# 2) 水力学基础函数
# =========================
def area(y):
    """矩形断面过水面积 A"""
    return b * y

def wetted_perimeter(y):
    """矩形断面湿周 P"""
    return b + 2.0 * y

def hydraulic_radius(y):
    """水力半径 R = A/P"""
    return area(y) / wetted_perimeter(y)

def velocity(y):
    """断面平均流速 V = Q/A"""
    return Q / area(y)

def friction_slope(y):
    """摩阻坡降 Sf（Manning）"""
    A = area(y)
    R = hydraulic_radius(y)
    return (n * Q / (A * R ** (2.0 / 3.0))) ** 2

def froude_number(y):
    """弗劳德数 Fr = V/sqrt(g*y)（矩形断面）"""
    V = velocity(y)
    return V / np.sqrt(g * y)

# =========================
# 3) 求正常水深 yn（用于对比）
# =========================
def manning_residual(y):
    A = area(y)
    R = hydraulic_radius(y)
    q_calc = (1.0 / n) * A * R ** (2.0 / 3.0) * np.sqrt(S0)
    return q_calc - Q

yn = brentq(manning_residual, 0.2, 30.0)

# =========================
# 4) 渐变流微分方程 dy/dx = (S0 - Sf)/(1 - Fr^2)
# =========================
def gvf_ode(x, y):
    yv = max(float(y[0]), 0.05)  # 防止数值迭代出现非物理负水深
    sf = friction_slope(yv)
    fr = froude_number(yv)

    den = 1.0 - fr ** 2
    # 避免分母过小导致数值发散
    if abs(den) < 1e-4:
        den = 1e-4 if den >= 0 else -1e-4

    dydx = (S0 - sf) / den
    return [dydx]

x_eval = np.linspace(0.0, L, nx)
sol = solve_ivp(
    gvf_ode, (0.0, L), [y_upstream],
    t_eval=x_eval, method="RK45",
    rtol=1e-6, atol=1e-8
)

if not sol.success:
    raise RuntimeError(f"数值积分失败：{sol.message}")

x = sol.t
y = np.maximum(sol.y[0], 0.05)

# 河床与水面线高程（以 x=0 断面河床高程为 0）
z_bed = -S0 * x
z_ws = z_bed + y

# =========================
# 5) 通航指标（UKC）计算
# =========================
V = velocity(y)
Fr = froude_number(y)
Sf = friction_slope(y)

# 船舶下沉量（简化经验模型）
squat = squat_coeff * V ** 2 / (2.0 * g)

# 富余水深 UKC = 实际水深 - 吃水 - 下沉量
ukc = y - ship_draft - squat
safe_mask = ukc >= ukc_required
safe_ratio = 100.0 * np.mean(safe_mask)

i_min_y = int(np.argmin(y))
i_min_ukc = int(np.argmin(ukc))

# =========================
# 6) KPI 结果表打印
# =========================
kpi_rows = [
    ("正常水深 yn (m)", yn),
    ("最小水深 y_min (m)", y[i_min_y]),
    ("最小水深位置 x (km)", x[i_min_y] / 1000.0),
    ("最大流速 V_max (m/s)", np.max(V)),
    ("最大弗劳德数 Fr_max (-)", np.max(Fr)),
    ("平均摩阻坡降 Sf_mean (-)", np.mean(Sf)),
    ("最小富余水深 UKC_min (m)", ukc[i_min_ukc]),
    ("UKC 满足率 (%)", safe_ratio),
]

def print_kpi_table(rows):
    name_w = max(len(r[0]) for r in rows) + 2
    val_w = 14
    print("\n=== KPI 结果表 ===")
    print(f"{'指标'.ljust(name_w)}{'数值'.rjust(val_w)}")
    print("-" * (name_w + val_w))
    for name, value in rows:
        print(f"{name.ljust(name_w)}{value:>{val_w}.4f}")

print_kpi_table(kpi_rows)

# =========================
# 7) 绘图
# =========================
fig, axes = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(3, 1, figsize=(10, 10), constrained_layout=True)

# 图1：水深沿程分布
axes[0].plot(x / 1000.0, y, lw=2, label="水深 y(x)")
axes[0].axhline(yn, color="tab:orange", ls="--", label=f"正常水深 yn={yn:.2f} m")
axes[0].set_xlabel("里程 x (km)")
axes[0].set_ylabel("水深 (m)")
axes[0].set_title("渐变流水深分布")
axes[0].grid(alpha=0.3)
axes[0].legend()

# 图2：河床线与水面线
axes[1].plot(x / 1000.0, z_bed, lw=2, label="河床线 z_bed")
axes[1].plot(x / 1000.0, z_ws, lw=2, label="水面线 z_ws")
axes[1].set_xlabel("里程 x (km)")
axes[1].set_ylabel("高程 (m)")
axes[1].set_title("沿程河床-水面线")
axes[1].grid(alpha=0.3)
axes[1].legend()

# 图3：富余水深安全校核
axes[2].plot(x / 1000.0, ukc, lw=2, label="UKC")
axes[2].axhline(ukc_required, color="tab:red", ls="--", label=f"要求值={ukc_required:.2f} m")
axes[2].fill_between(
    x / 1000.0, ukc, ukc_required,
    where=(ukc < ukc_required), alpha=0.25, color="red", label="不满足区段"
)
axes[2].set_xlabel("里程 x (km)")
axes[2].set_ylabel("富余水深 (m)")
axes[2].set_title("通航安全校核（考虑下沉量）")
axes[2].grid(alpha=0.3)
axes[2].legend()

plt.savefig('ch04_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch04_simulation_result.png")
# plt.show()  # 禁用弹窗
