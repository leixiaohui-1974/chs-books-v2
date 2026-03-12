# -*- coding: utf-8 -*-
"""
教材：《内河航道与通航水力学》
章节：第2章 通航水位保障与流量调配（2.1 基本概念与理论框架）
功能：构建“来水-调配-水位”联动仿真，优化补偿流量并输出KPI与图形
"""

import numpy as np
from scipy.optimize import minimize, Bounds, LinearConstraint
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# =========================
# 1) 关键参数（可直接改动）
# =========================
np.random.seed(2026)                  # 固定随机种子，便于教学复现实验
T_hours = 96                          # 总仿真时长（小时）
dt_hours = 1.0                        # 时间步长（小时）
dt = dt_hours * 3600                  # 时间步长（秒）
N = int(T_hours / dt_hours)           # 步数
t = np.arange(N)                      # 时间索引（h）

# 断面水位-流量关系参数：H = H0 + k*Q^m
H0 = 1.85                             # 基准水位（m）
k_h = 0.013                           # 系数
m_h = 0.63                            # 指数

# 通航控制目标
H_nav_min = 2.80                      # 最低通航水位（m）
H_nav_target = 2.95                   # 期望通航水位（m）

# 调蓄工程（库群等效）参数
S_min = 20e6                          # 最小库容（m^3）
S_max = 95e6                          # 最大库容（m^3）
S0 = 62e6                             # 初始库容（m^3）
S_end_min = 40e6                      # 末时段最低保留库容（m^3）

Q_rel_min = 20.0                      # 最小补偿流量（m^3/s）
Q_rel_max = 420.0                     # 最大补偿流量（m^3/s）

# 目标函数权重（教学可调）
w_short = 2.0e4                       # 水位不足惩罚（保障优先）
w_target = 2.8e3                      # 低于目标水位惩罚
w_smooth = 3.0                        # 调度平滑惩罚
w_release = 0.08                      # 节水偏好惩罚
w_storage = 1.0e-14                   # 库容软约束惩罚

save_fig = True
fig_name = "chapter2_navigation_dispatch.png"

# =========================
# 2) 构造来水/天然流量过程
# =========================
# 天然流量：周期波动 + 随机扰动（代表潮汐、支流来水、局地影响）
Q_nat = (
    120
    + 38 * np.sin(2 * np.pi * t / 24 - 0.8)
    + 20 * np.sin(2 * np.pi * t / 12 + 0.4)
    + np.random.normal(0, 8, N)
)
Q_nat = np.clip(Q_nat, 45, None)

# 入库流量：两次洪峰 + 扰动（代表上游过程不均匀）
Q_in = (
    170
    + 90 * np.exp(-((t - 28) / 8.5) ** 2)
    + 65 * np.exp(-((t - 70) / 11.0) ** 2)
    + np.random.normal(0, 7, N)
)
Q_in = np.clip(Q_in, 70, None)

# =========================
# 3) 模型函数
# =========================
def stage_from_flow(q_total: np.ndarray) -> np.ndarray:
    """由总流量计算控制断面水位。"""
    q_safe = np.clip(q_total, 1e-6, None)
    return H0 + k_h * np.power(q_safe, m_h)

def simulate(q_rel: np.ndarray):
    """给定补偿流量序列，返回库容、总流量、水位和缺额。"""
    # 离散水量平衡：S(k+1)=S(k)+(Q_in-Q_rel)*dt
    S = S0 + np.r_[0.0, np.cumsum((Q_in - q_rel) * dt)]
    Q_total = Q_nat + q_rel
    H = stage_from_flow(Q_total)
    H_short = np.maximum(0.0, H_nav_min - H)
    return S, Q_total, H, H_short

def objective(q_rel: np.ndarray) -> float:
    """综合目标：保水位、稳调度、兼顾节水与安全库容。"""
    S, _, H, H_short = simulate(q_rel)

    # 1) 最低通航水位不足惩罚
    loss_short = w_short * np.sum(H_short ** 2)

    # 2) 低于目标水位惩罚（非硬约束）
    loss_target = w_target * np.sum(np.maximum(0.0, H_nav_target - H) ** 2)

    # 3) 调度爬坡惩罚（避免闸坝频繁大幅调整）
    dq = np.diff(q_rel, prepend=q_rel[0])
    loss_smooth = w_smooth * np.sum(dq ** 2)

    # 4) 节水惩罚（抑制不必要的大流量补偿）
    loss_release = w_release * np.sum(q_rel)

    # 5) 库容软惩罚（尽量远离极限边界）
    S_mid = 0.5 * (S_min + S_max)
    loss_storage = w_storage * np.sum((S[1:] - S_mid) ** 2)

    return loss_short + loss_target + loss_smooth + loss_release + loss_storage

# =========================
# 4) 线性约束（库容上下限+末时段库容）
# =========================
# S(k)=S0 + dt*sum_{i<=k}(Q_in(i)-Q_rel(i))
# 可整理为 A*x 在区间内的线性不等式
L = np.tril(np.ones((N, N)))           # 下三角累加矩阵
cum_in = np.cumsum(Q_in)

A_storage = -dt * L
lb_storage = S_min - S0 - dt * cum_in
ub_storage = S_max - S0 - dt * cum_in
con_storage = LinearConstraint(A_storage, lb_storage, ub_storage)

A_end = -dt * np.ones((1, N))
lb_end = np.array([S_end_min - S0 - dt * np.sum(Q_in)])
ub_end = np.array([np.inf])
con_end = LinearConstraint(A_end, lb_end, ub_end)

# 流量边界
bounds = Bounds(np.full(N, Q_rel_min), np.full(N, Q_rel_max))

# 初值：按“满足最低水位”反推所需总流量
Q_need = np.power(np.maximum((H_nav_min - H0) / k_h, 1e-6), 1.0 / m_h)
x0 = np.clip(Q_need - Q_nat, Q_rel_min, Q_rel_max)

# =========================
# 5) 优化求解
# =========================
res = minimize(
    objective,
    x0=x0,
    method="SLSQP",
    bounds=bounds,
    constraints=[con_storage, con_end],
    options={"maxiter": 500, "ftol": 1e-7, "disp": False},
)

if not res.success:
    print(f"[警告] 优化未完全收敛：{res.message}")

Q_rel_opt = np.clip(res.x, Q_rel_min, Q_rel_max)
S, Q_total, H, H_short = simulate(Q_rel_opt)

# =========================
# 6) KPI表格输出
# =========================
guarantee_rate = 100.0 * np.mean(H >= H_nav_min)
min_stage = np.min(H)
avg_stage = np.mean(H)
avg_rel = np.mean(Q_rel_opt)
max_rel = np.max(Q_rel_opt)
shortage_integral = np.sum(H_short * dt_hours)     # m·h
end_storage = S[-1] / 1e6                           # million m^3
ramp_std = np.std(np.diff(Q_rel_opt))

kpi_rows = [
    ("通航水位保证率", f"{guarantee_rate:6.2f} %"),
    ("最小通航水位", f"{min_stage:6.3f} m"),
    ("平均通航水位", f"{avg_stage:6.3f} m"),
    ("平均补偿流量", f"{avg_rel:6.2f} m^3/s"),
    ("最大补偿流量", f"{max_rel:6.2f} m^3/s"),
    ("水位缺额积分", f"{shortage_integral:6.3f} m·h"),
    ("末时段库容", f"{end_storage:6.2f} million m^3"),
    ("流量爬坡标准差", f"{ramp_std:6.2f} m^3/s"),
]

print("\n" + "=" * 60)
print("KPI结果表：第2章 通航水位保障与流量调配")
print("=" * 60)
for name, value in kpi_rows:
    print(f"{name:<18} | {value:>22}")
print("=" * 60)

# =========================
# 7) 绘图
# =========================
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# 图1：流量过程
axes[0].plot(t, Q_nat, label="天然流量 Q_nat", lw=1.8)
axes[0].plot(t, Q_in, label="入库流量 Q_in", lw=1.8)
axes[0].plot(t, Q_rel_opt, label="优化补偿流量 Q_rel", lw=2.2)
axes[0].plot(t, Q_total, "--", label="控制断面总流量 Q_total", lw=1.8)
axes[0].set_ylabel("流量 (m^3/s)")
axes[0].set_title("通航水位保障与流量调配仿真")
axes[0].grid(alpha=0.25)
axes[0].legend(ncol=2, fontsize=9)

# 图2：通航水位保障
axes[1].plot(t, H, color="tab:blue", lw=2.2, label="控制断面水位")
axes[1].axhline(H_nav_min, color="tab:red", ls="--", lw=1.8, label="最低通航水位")
axes[1].axhline(H_nav_target, color="tab:green", ls="-.", lw=1.6, label="目标通航水位")
axes[1].fill_between(t, H, H_nav_min, where=(H < H_nav_min), color="tab:red", alpha=0.22, label="水位缺额区")
axes[1].set_ylabel("水位 (m)")
axes[1].grid(alpha=0.25)
axes[1].legend(fontsize=9)

# 图3：库容过程
axes[2].plot(t, S[1:] / 1e6, color="tab:purple", lw=2.0, label="库容")
axes[2].axhline(S_min / 1e6, color="tab:red", ls="--", lw=1.5, label="库容下限")
axes[2].axhline(S_max / 1e6, color="tab:orange", ls="--", lw=1.5, label="库容上限")
axes[2].set_ylabel("库容 (million m^3)")
axes[2].set_xlabel("时间 (hour)")
axes[2].grid(alpha=0.25)
axes[2].legend(fontsize=9)

plt.tight_layout()
if save_fig:
    plt.savefig(fig_name, dpi=150)
    print(f"图像已保存：{fig_name}")
# plt.show()  # 禁用弹窗
