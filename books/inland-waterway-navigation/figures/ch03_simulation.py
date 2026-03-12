# -*- coding: utf-8 -*-
"""
教材：《内河航道与通航水力学》
章节：第3章 船舶阻力与航速（3.1 基本概念与理论框架）
功能：基于阻力分解与功率平衡，仿真内河船舶在不同航速/水深条件下的阻力和可达航速，
并输出KPI结果表与可视化图形。
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# =============== 1) 关键参数定义（可直接改） ===============
rho = 1000.0           # 水密度(kg/m^3)
nu = 1.00e-6           # 运动黏度(m^2/s)
g = 9.81               # 重力加速度(m/s^2)

L = 52.0               # 船长(m)
B = 9.2                # 船宽(m)
T = 1.6                # 吃水(m)
Cb = 0.82              # 方形系数
S = 560.0              # 湿表面积(m^2)，课程中可替换为实测值

form_factor = 0.18     # 形状系数k（粘压阻附加）
Cr0 = 0.0012           # 基础剩余阻力系数
Cr_fr4 = 0.0060        # Fr^4项系数，用于描述兴波阻力增长
eta_total = 0.62       # 总推进效率（轴到有效功）

depth_design = 4.0     # 设计水深(m)
depth_cases = [3.0, 4.0, 6.0]  # 对比水深(m)

P_available_kw = 550.0 # 可用轴功率(kW)
v_design = 5.5         # 设计航速(m/s)

# =============== 2) 理论函数 ===============
def friction_coefficient(v):
    """ITTC-1957摩擦阻力系数"""
    Re = v * L / nu
    return 0.075 / (np.log10(Re) - 2.0) ** 2

def residual_coefficient(v):
    """剩余阻力系数：与弗劳德数相关"""
    Fr = v / np.sqrt(g * L)
    return Cr0 + Cr_fr4 * Fr**4

def shallow_water_factor(h):
    """浅水修正系数：体现水深受限时阻力放大"""
    ratio = T / h
    if ratio >= 0.95:
        raise ValueError("水深过小，T/h接近1，模型不再适用。")
    return 1.0 + 1.8 * ratio**2 / (1.0 - ratio)

def total_resistance(v, h):
    """总阻力(N)"""
    cf = friction_coefficient(v)
    cr = residual_coefficient(v)
    c_total = cf * (1.0 + form_factor) + cr
    return 0.5 * rho * S * v**2 * c_total * shallow_water_factor(h)

def shaft_power_required(v, h):
    """所需轴功率(W)"""
    return total_resistance(v, h) * v / eta_total

def solve_achievable_speed(power_kw, h, v_min=0.3, v_max=9.0):
    """由可用轴功率反解可达航速"""
    power_w = power_kw * 1000.0
    f = lambda x: shaft_power_required(x, h) - power_w

    if f(v_min) > 0:
        return np.nan
    if f(v_max) < 0:
        return v_max
    return brentq(f, v_min, v_max)

# =============== 3) 计算KPI ===============
v_ach = solve_achievable_speed(P_available_kw, depth_design)
R_design = total_resistance(v_design, depth_design)
P_design_kw = shaft_power_required(v_design, depth_design) / 1000.0
Fr_ach = v_ach / np.sqrt(g * L)

# 经济性示意指标：单位有效功耗(仅示意，教学中可换为油耗模型)
R_ach = total_resistance(v_ach, depth_design)
Pe_ach_kw = (R_ach * v_ach) / 1000.0
transport_eff = Pe_ach_kw / (v_ach * 3.6)  # kW/(km/h)

kpi_rows = [
    ("设计航速", f"{v_design:.2f} m/s ({v_design*3.6:.2f} km/h)", "输入参数"),
    ("设计航速总阻力", f"{R_design/1000:.2f} kN", "R(v_design, h_design)"),
    ("设计航速所需轴功率", f"{P_design_kw:.2f} kW", "P=R·V/eta"),
    ("可达最大航速", f"{v_ach:.2f} m/s ({v_ach*3.6:.2f} km/h)", "由可用功率反解"),
    ("可达航速弗劳德数", f"{Fr_ach:.3f}", "Fr=V/sqrt(gL)"),
    ("单位速度有效功耗", f"{transport_eff:.2f} kW/(km/h)", "教学示意KPI"),
]

print("\nKPI结果表（第3章 船舶阻力与航速）")
print("-" * 86)
print(f"{'指标':<20} | {'数值':<32} | {'说明'}")
print("-" * 86)
for name, value, note in kpi_rows:
    print(f"{name:<20} | {value:<32} | {note}")
print("-" * 86)

# =============== 4) 绘图 ===============
v = np.linspace(0.5, 8.0, 180)

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

# 图1：不同水深下的阻力-航速曲线
for h in depth_cases:
    R_curve = total_resistance(v, h) / 1000.0
    axes[0].plot(v, R_curve, label=f"h={h:.1f} m")
axes[0].scatter([v_design], [R_design / 1000.0], c="red", zorder=3, label="设计工况")
axes[0].set_xlabel("航速 V (m/s)")
axes[0].set_ylabel("总阻力 R (kN)")
axes[0].set_title("阻力-航速关系（不同水深）")
axes[0].grid(alpha=0.3)
axes[0].legend()

# 图2：设计水深下的功率平衡
P_curve_kw = shaft_power_required(v, depth_design) / 1000.0
axes[1].plot(v, P_curve_kw, label="所需轴功率")
axes[1].axhline(P_available_kw, color="r", linestyle="--", label="可用轴功率")
axes[1].scatter([v_ach], [P_available_kw], c="red", zorder=3, label="可达最大航速")
axes[1].set_xlabel("航速 V (m/s)")
axes[1].set_ylabel("轴功率 P (kW)")
axes[1].set_title("功率平衡与可达航速")
axes[1].grid(alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig('ch03_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch03_simulation_result.png")
# plt.show()  # 禁用弹窗
