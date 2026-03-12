# -*- coding: utf-8 -*-
# 《水库调度优化与决策》 第4章：梯级水库联合优化
# 功能：构建三库串联联合调度仿真，综合发电收益、供水保障、防洪约束与期末库容目标进行优化

import numpy as np
from scipy.optimize import minimize, Bounds
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# -------------------------
# 0) 绘图中文显示设置
# -------------------------
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# -------------------------
# 1) 关键参数定义（可按工程对象调整）
# -------------------------
T = 12  # 调度时段（月）
N = 3   # 梯级水库数量（串联）
res_names = ["上游库", "中游库", "下游库"]

sec_per_period = 30 * 24 * 3600  # 每月秒数（简化取30天）
hours_per_period = 30 * 24        # 每月小时数

# 天然来水（m3/s）：行=水库，列=月份
qin_natural = np.array([
    [220, 240, 260, 340, 420, 520, 610, 580, 460, 360, 280, 240],
    [120, 130, 145, 180, 240, 300, 350, 330, 260, 200, 160, 130],
    [80,  85,  90, 120, 160, 210, 250, 235, 185, 140, 110,  90]
], dtype=float)

# 上游下泄向下游传输系数（损失/滞后简化）
route_coef = np.array([0.95, 0.96], dtype=float)

# 库容约束（百万m3）
storage_min = np.array([300, 220, 180], dtype=float)
storage_max = np.array([1200, 900, 700], dtype=float)

# 初始与期末目标库容（百万m3）
storage_init = np.array([700, 520, 420], dtype=float)
storage_target_end = np.array([720, 540, 430], dtype=float)

# 汛限库容（百万m3），汛期为6-9月（索引5-8）
flood_limit = np.array([1000, 760, 600], dtype=float)
flood_month_idx = np.array([5, 6, 7, 8], dtype=int)

# 下泄流量边界（m3/s）
release_min = np.array([80, 70, 90], dtype=float)
release_max = np.array([700, 620, 650], dtype=float)

# 下游需水过程（m3/s），以最下游控制断面为代表
demand_downstream = np.array([260, 250, 245, 260, 285, 320, 350, 340, 310, 290, 275, 265], dtype=float)

# 水电参数
rho = 1000.0
g = 9.81
eta = np.array([0.90, 0.91, 0.92], dtype=float)
head_base = np.array([55, 42, 30], dtype=float)        # 基础水头(m)
head_k = np.array([0.020, 0.018, 0.015], dtype=float)  # 水头-库容系数 m/(百万m3)
q_turb_max = np.array([520, 500, 540], dtype=float)    # 过机流量上限(m3/s)

# 电价（元/MWh）
price = np.array([320, 315, 310, 305, 300, 298, 296, 300, 308, 315, 325, 330], dtype=float)

# 惩罚系数（可调）
penalty_deficit = 4.0e5     # 供水缺额惩罚
penalty_flood = 2.0e5       # 汛限超限惩罚
penalty_terminal = 8.0e5    # 期末库容偏差惩罚
penalty_smooth = 5.0e3      # 下泄平滑惩罚
penalty_storage = 3.0e6     # 库容越界惩罚（硬约束软化）

# -------------------------
# 2) 模型函数
# -------------------------
def reshape_release(x):
    """决策向量 -> N*T下泄矩阵"""
    return x.reshape(N, T)

def cascade_inflow(release):
    """各库入流=天然来水+上游下泄传输"""
    qin = qin_natural.copy()
    qin[1, :] += route_coef[0] * release[0, :]
    qin[2, :] += route_coef[1] * release[1, :]
    return qin

def simulate(release):
    """给定下泄过程，递推库容、出力、发电量"""
    qin = cascade_inflow(release)
    storage = np.zeros((N, T + 1), dtype=float)
    storage[:, 0] = storage_init

    for t in range(T):
        delta = (qin[:, t] - release[:, t]) * sec_per_period / 1e6
        storage[:, t + 1] = storage[:, t] + delta

    head = head_base[:, None] + head_k[:, None] * storage[:, :-1]
    q_turb = np.minimum(release, q_turb_max[:, None])
    power_mw = rho * g * eta[:, None] * q_turb * head / 1e6
    energy_mwh = power_mw * hours_per_period

    return {
        "qin": qin,
        "storage": storage,
        "head": head,
        "q_turb": q_turb,
        "power_mw": power_mw,
        "energy_mwh": energy_mwh
    }

def objective(x):
    """目标函数：最小化( -发电收益 + 各类惩罚 )"""
    release = reshape_release(x)
    out = simulate(release)

    # 1) 发电收益（越大越好 -> 取负号）
    month_energy = out["energy_mwh"].sum(axis=0)
    revenue = np.sum(month_energy * price)

    # 2) 下游供水缺额惩罚
    deficit = np.maximum(demand_downstream - release[2, :], 0.0)
    loss_deficit = penalty_deficit * np.sum(deficit ** 2)

    # 3) 汛期限蓄超限惩罚
    flood_excess = np.maximum(out["storage"][:, flood_month_idx + 1] - flood_limit[:, None], 0.0)
    loss_flood = penalty_flood * np.sum(flood_excess ** 2)

    # 4) 期末库容偏差惩罚
    terminal_dev = out["storage"][:, -1] - storage_target_end
    loss_terminal = penalty_terminal * np.sum(terminal_dev ** 2)

    # 5) 下泄平滑惩罚
    diff_r = np.diff(release, axis=1)
    loss_smooth = penalty_smooth * np.sum(diff_r ** 2)

    # 6) 库容边界惩罚
    storage_mid = out["storage"][:, 1:]
    below = np.maximum(storage_min[:, None] - storage_mid, 0.0)
    above = np.maximum(storage_mid - storage_max[:, None], 0.0)
    loss_storage = penalty_storage * np.sum(below ** 2 + above ** 2)

    return -revenue + loss_deficit + loss_flood + loss_terminal + loss_smooth + loss_storage

# -------------------------
# 3) 优化求解
# -------------------------
lb = np.repeat(release_min, T)
ub = np.repeat(release_max, T)
bounds = Bounds(lb, ub)

# 初值
release0 = np.zeros((N, T), dtype=float)
release0[0, :] = np.clip(0.55 * qin_natural[0, :], release_min[0], release_max[0])
release0[1, :] = np.clip(0.50 * (qin_natural[1, :] + route_coef[0] * release0[0, :]), release_min[1], release_max[1])
release0[2, :] = np.clip(np.maximum(demand_downstream, 0.48 * (qin_natural[2, :] + route_coef[1] * release0[1, :])),
                         release_min[2], release_max[2])

res = minimize(
    objective,
    release0.ravel(),
    method="SLSQP",
    bounds=bounds,
    options={"maxiter": 600, "ftol": 1e-6, "disp": False}
)

release_opt = reshape_release(res.x)
out_opt = simulate(release_opt)

# -------------------------
# 4) KPI统计与表格打印
# -------------------------
energy_gwh_each = out_opt["energy_mwh"].sum(axis=1) / 1000.0
energy_gwh_total = energy_gwh_each.sum()
revenue_total = np.sum(out_opt["energy_mwh"].sum(axis=0) * price)
revenue_10k = revenue_total / 1e4

deficit = np.maximum(demand_downstream - release_opt[2, :], 0.0)
deficit_vol_million_m3 = np.sum(deficit * sec_per_period / 1e6)

flood_excess = np.maximum(out_opt["storage"][:, flood_month_idx + 1] - flood_limit[:, None], 0.0)
terminal_dev = out_opt["storage"][:, -1] - storage_target_end

storage_mid = out_opt["storage"][:, 1:]
storage_violate = (np.maximum(storage_min[:, None] - storage_mid, 0.0) +
                   np.maximum(storage_mid - storage_max[:, None], 0.0)).sum()

def print_table(title, headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    line = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
    print("\n" + title)
    print(line)
    print("| " + " | ".join(f"{headers[i]:<{widths[i]}}" for i in range(len(headers))) + " |")
    print(line)
    for row in rows:
        print("| " + " | ".join(f"{str(row[i]):<{widths[i]}}" for i in range(len(row))) + " |")
    print(line)

kpi_rows = [
    ["优化收敛", str(res.success)],
    ["目标函数值(元)", f"{res.fun:,.2f}"],
    ["总发电量(GWh)", f"{energy_gwh_total:,.2f}"],
    ["总发电收益(万元)", f"{revenue_10k:,.2f}"],
    ["下游供水缺额总量(百万m3)", f"{deficit_vol_million_m3:,.2f}"],
    ["汛期限蓄超限累计(百万m3)", f"{flood_excess.sum():,.2f}"],
    ["期末库容偏差L2(百万m3)", f"{np.linalg.norm(terminal_dev):,.2f}"],
    ["库容越界累计(百万m3)", f"{storage_violate:,.2f}"]
]
print_table("KPI结果总表", ["指标", "数值"], kpi_rows)

res_rows = []
for i in range(N):
    res_rows.append([
        res_names[i],
        f"{energy_gwh_each[i]:,.2f}",
        f"{out_opt['storage'][i, :].min():,.2f}",
        f"{out_opt['storage'][i, :].max():,.2f}",
        f"{out_opt['storage'][i, -1]:,.2f}"
    ])
print_table("分库运行指标",
            ["水库", "发电量(GWh)", "最小库容(百万m3)", "最大库容(百万m3)", "期末库容(百万m3)"],
            res_rows)

# -------------------------
# 5) 绘图
# -------------------------
months = np.arange(1, T + 1)
plt.figure(figsize=(12, 9))

ax1 = plt.subplot(3, 1, 1)
for i in range(N):
    ax1.plot(np.arange(0, T + 1), out_opt["storage"][i, :], marker="o", label=f"{res_names[i]}库容")
    ax1.hlines(flood_limit[i], 0, T, linestyles="--", linewidth=1, alpha=0.8)
ax1.set_title("梯级水库库容过程线")
ax1.set_xlabel("时段(月)")
ax1.set_ylabel("库容(百万m3)")
ax1.grid(alpha=0.3)
ax1.legend(ncol=2, fontsize=9)

ax2 = plt.subplot(3, 1, 2)
for i in range(N):
    ax2.plot(months, release_opt[i, :], marker="s", label=f"{res_names[i]}下泄")
ax2.plot(months, demand_downstream, "k--", linewidth=2, label="下游需水")
ax2.set_title("下泄调度与下游需水对比")
ax2.set_xlabel("月份")
ax2.set_ylabel("流量(m3/s)")
ax2.grid(alpha=0.3)
ax2.legend(ncol=2, fontsize=9)

ax3 = plt.subplot(3, 1, 3)
for i in range(N):
    ax3.bar(months + (i - 1) * 0.25, out_opt["energy_mwh"][i, :] / 1000.0, width=0.25, label=res_names[i])
ax3.set_title("各库月发电量")
ax3.set_xlabel("月份")
ax3.set_ylabel("发电量(GWh)")
ax3.grid(axis="y", alpha=0.3)
ax3.legend()

plt.tight_layout()
# plt.savefig('ch04_simulation_result.png', dpi=220)
# plt.show()  # 禁用弹窗
