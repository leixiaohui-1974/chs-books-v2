"""
书名：《水库调度优化与决策》
章节：第5章 实时调度（滚动MPC）
功能：构建含SOS2分段线性化的水库调度MILP仿真，输出KPI结果表并绘制调度过程图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix


def main():
    # =========================
    # 1) 关键参数定义
    # =========================
    T = 24                      # 调度时段数（例如24个6小时）
    dt_h = 6.0                  # 每时段小时数
    dt_v = dt_h * 3600.0 / 1e6  # 流量(m3/s)转体积(百万m3)的系数

    # 合成入库流量过程（可替换为实测/预报序列）
    t_idx = np.arange(T)
    inflow = (
        700
        + 650 * np.exp(-((t_idx - 7) / 2.8) ** 2)
        + 900 * np.exp(-((t_idx - 16) / 2.2) ** 2)
    )
    inflow = np.clip(inflow, 250, None)

    # 库容-水位分段点（SOS2）
    V_bp = np.array([180, 220, 260, 300, 340, 380, 420], dtype=float)      # 百万m3
    Z_up_bp = np.array([148.0, 151.0, 154.0, 157.0, 159.5, 161.5, 163.0])   # m

    # 总泄量-尾水位分段点（SOS2）
    Q_bp = np.array([100, 300, 600, 900, 1300, 1800], dtype=float)          # m3/s
    Z_tail_bp = np.array([120.0, 120.8, 121.9, 123.0, 124.2, 125.8], dtype=float)

    # 工程运行边界
    s0 = 300.0                 # 初始库容（百万m3）
    s_target = 310.0           # 末期目标库容（百万m3）
    s_flood = 360.0            # 防洪控制库容（百万m3）
    s_min, s_max = V_bp[0], V_bp[-1]

    q_min, q_max = 120.0, 1500.0     # 机组下泄约束
    spill_max = 1800.0               # 弃水上限
    q_eco = 220.0                    # 生态流量下限
    q0 = 350.0                       # 初始下泄
    ramp_up, ramp_dn = 400.0, 400.0  # 下泄爬坡约束

    # 目标函数权重（可做灵敏度分析）
    release_value = 1.0      # 下泄收益（线性近似）
    spill_penalty = 7.0      # 弃水惩罚
    flood_penalty = 40.0     # 超汛限惩罚
    eco_penalty = 80.0       # 生态缺额惩罚
    terminal_penalty = 8.0   # 末库容偏差惩罚

    # 发电计算参数（用于KPI评估，不直接入MILP目标）
    eta = 0.90
    head_loss = 2.0

    Jv = len(V_bp)
    Jq = len(Q_bp)

    # =========================
    # 2) 变量索引
    # =========================
    cur = 0
    idx_s = np.arange(cur, cur + T); cur += T
    idx_r = np.arange(cur, cur + T); cur += T
    idx_sp = np.arange(cur, cur + T); cur += T
    idx_z = np.arange(cur, cur + T); cur += T
    idx_e = np.arange(cur, cur + T); cur += T

    idx_dev_p = cur; cur += 1
    idx_dev_n = cur; cur += 1

    idx_lam_v = np.arange(cur, cur + T * Jv).reshape(T, Jv); cur += T * Jv
    idx_y_v = np.arange(cur, cur + T * (Jv - 1)).reshape(T, Jv - 1); cur += T * (Jv - 1)

    idx_lam_q = np.arange(cur, cur + T * Jq).reshape(T, Jq); cur += T * Jq
    idx_y_q = np.arange(cur, cur + T * (Jq - 1)).reshape(T, Jq - 1); cur += T * (Jq - 1)

    n_var = cur

    # =========================
    # 3) 目标函数
    # =========================
    c = np.zeros(n_var)
    c[idx_r] = -release_value
    c[idx_sp] = spill_penalty
    c[idx_z] = flood_penalty
    c[idx_e] = eco_penalty
    c[idx_dev_p] = terminal_penalty
    c[idx_dev_n] = terminal_penalty

    # 二进制变量：SOS2段选择变量
    integrality = np.zeros(n_var, dtype=int)
    integrality[idx_y_v.ravel()] = 1
    integrality[idx_y_q.ravel()] = 1

    # =========================
    # 4) 变量上下界
    # =========================
    lb = np.full(n_var, -np.inf)
    ub = np.full(n_var, np.inf)

    lb[idx_s], ub[idx_s] = s_min, s_max
    lb[idx_r], ub[idx_r] = q_min, q_max
    lb[idx_sp], ub[idx_sp] = 0.0, spill_max
    lb[idx_z], ub[idx_z] = 0.0, np.inf
    lb[idx_e], ub[idx_e] = 0.0, np.inf
    lb[idx_dev_p], ub[idx_dev_p] = 0.0, np.inf
    lb[idx_dev_n], ub[idx_dev_n] = 0.0, np.inf

    lb[idx_lam_v.ravel()], ub[idx_lam_v.ravel()] = 0.0, 1.0
    lb[idx_lam_q.ravel()], ub[idx_lam_q.ravel()] = 0.0, 1.0
    lb[idx_y_v.ravel()], ub[idx_y_v.ravel()] = 0.0, 1.0
    lb[idx_y_q.ravel()], ub[idx_y_q.ravel()] = 0.0, 1.0

    # =========================
    # 5) 线性约束构建
    # =========================
    rows = []

    def add_row(cols, vals, low, up):
        rows.append((np.asarray(cols, dtype=int), np.asarray(vals, dtype=float), float(low), float(up)))

    # 5.1 质量平衡
    for t in range(T):
        cols = [idx_s[t], idx_r[t], idx_sp[t]]
        vals = [1.0, dt_v, dt_v]
        rhs = dt_v * inflow[t]
        if t == 0:
            rhs += s0
        else:
            cols.append(idx_s[t - 1]); vals.append(-1.0)
        add_row(cols, vals, rhs, rhs)

    # 5.2 库容-SOS2关系
    for t in range(T):
        add_row(idx_lam_v[t], np.ones(Jv), 1.0, 1.0)
        add_row([idx_s[t], *idx_lam_v[t]], [1.0, *(-V_bp)], 0.0, 0.0)
        add_row(idx_y_v[t], np.ones(Jv - 1), 1.0, 1.0)

        # λ0 <= y0
        add_row([idx_lam_v[t, 0], idx_y_v[t, 0]], [1.0, -1.0], -np.inf, 0.0)
        # λj <= yj-1 + yj
        for j in range(1, Jv - 1):
            add_row([idx_lam_v[t, j], idx_y_v[t, j - 1], idx_y_v[t, j]], [1.0, -1.0, -1.0], -np.inf, 0.0)
        # λ_last <= y_last
        add_row([idx_lam_v[t, Jv - 1], idx_y_v[t, Jv - 2]], [1.0, -1.0], -np.inf, 0.0)

    # 5.3 总泄量-SOS2关系
    for t in range(T):
        add_row(idx_lam_q[t], np.ones(Jq), 1.0, 1.0)
        add_row([idx_r[t], idx_sp[t], *idx_lam_q[t]], [1.0, 1.0, *(-Q_bp)], 0.0, 0.0)
        add_row(idx_y_q[t], np.ones(Jq - 1), 1.0, 1.0)

        add_row([idx_lam_q[t, 0], idx_y_q[t, 0]], [1.0, -1.0], -np.inf, 0.0)
        for j in range(1, Jq - 1):
            add_row([idx_lam_q[t, j], idx_y_q[t, j - 1], idx_y_q[t, j]], [1.0, -1.0, -1.0], -np.inf, 0.0)
        add_row([idx_lam_q[t, Jq - 1], idx_y_q[t, Jq - 2]], [1.0, -1.0], -np.inf, 0.0)

    # 5.4 防洪软约束：S_t - z_t <= s_flood
    for t in range(T):
        add_row([idx_s[t], idx_z[t]], [1.0, -1.0], -np.inf, s_flood)

    # 5.5 生态约束：R_t + Spill_t + e_t >= q_eco
    for t in range(T):
        add_row([idx_r[t], idx_sp[t], idx_e[t]], [1.0, 1.0, 1.0], q_eco, np.inf)

    # 5.6 下泄爬坡约束
    add_row([idx_r[0]], [1.0], q0 - ramp_dn, q0 + ramp_up)
    for t in range(1, T):
        add_row([idx_r[t], idx_r[t - 1]], [1.0, -1.0], -np.inf, ramp_up)
        add_row([idx_r[t - 1], idx_r[t]], [1.0, -1.0], -np.inf, ramp_dn)

    # 5.7 末库容偏差绝对值线性化：S_T - d+ + d- = s_target
    add_row([idx_s[T - 1], idx_dev_p, idx_dev_n], [1.0, -1.0, 1.0], s_target, s_target)

    # 稀疏矩阵组装
    m = len(rows)
    A = lil_matrix((m, n_var), dtype=float)
    lc = np.zeros(m)
    uc = np.zeros(m)
    for i, (cols, vals, lo, up) in enumerate(rows):
        A[i, cols] = vals
        lc[i] = lo
        uc[i] = up

    constraints = [LinearConstraint(A.tocsr(), lc, uc)]
    bounds = Bounds(lb, ub)

    # =========================
    # 6) 求解MILP
    # =========================
    res = milp(
        c=c,
        integrality=integrality,
        bounds=bounds,
        constraints=constraints,
        options={"disp": False}
    )

    if (not res.success) or (res.x is None):
        raise RuntimeError(f"MILP未收敛，状态码={res.status}, 信息={res.message}")

    x = res.x
    s = x[idx_s]
    r = x[idx_r]
    sp = x[idx_sp]
    z = x[idx_z]
    eco = x[idx_e]
    lam_v = x[idx_lam_v]
    lam_q = x[idx_lam_q]

    # =========================
    # 7) KPI计算与打印
    # =========================
    z_up = lam_v @ Z_up_bp
    z_tail = lam_q @ Z_tail_bp
    head = np.maximum(z_up - z_tail - head_loss, 0.0)

    power_mw = 9.81 * eta * r * head / 1000.0
    energy_gwh = np.sum(power_mw * dt_h) / 1000.0

    kpi = [
        ("优化目标函数值", res.fun),
        ("总入库水量(百万m3)", np.sum(inflow) * dt_v),
        ("总机组下泄水量(百万m3)", np.sum(r) * dt_v),
        ("总弃水量(百万m3)", np.sum(sp) * dt_v),
        ("生态缺额水量(百万m3)", np.sum(eco) * dt_v),
        ("峰值库容(百万m3)", np.max(s)),
        ("超汛限持续时间(小时)", np.count_nonzero(s > s_flood) * dt_h),
        ("累计超汛限库容(百万m3)", np.sum(np.maximum(s - s_flood, 0.0))),
        ("平均净水头(m)", np.mean(head)),
        ("总发电量(GWh)", energy_gwh),
    ]

    print("\n=== KPI结果表 ===")
    print(f"{'指标':<28}{'数值':>16}")
    print("-" * 46)
    for name, value in kpi:
        print(f"{name:<28}{value:>16.3f}")

    print("\n=== 分时段结果(前10段) ===")
    print(f"{'时段':>4} {'入流':>10} {'下泄':>10} {'弃水':>10} {'库容':>10} {'水头':>10}")
    for i in range(min(10, T)):
        print(f"{i+1:>4d} {inflow[i]:>10.1f} {r[i]:>10.1f} {sp[i]:>10.1f} {s[i]:>10.1f} {head[i]:>10.2f}")

    # =========================
    # 8) 绘图
    # =========================
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    x_plot = np.arange(1, T + 1)
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

    # 图1：流量过程
    axes[0].plot(x_plot, inflow, "b-", lw=2, label="入库流量")
    axes[0].plot(x_plot, r, "g-", lw=2, label="机组下泄")
    axes[0].bar(x_plot, sp, color="orange", alpha=0.4, label="弃水流量")
    axes[0].set_ylabel("流量 (m3/s)")
    axes[0].set_title("水库调度流量过程")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    # 图2：库容过程
    axes[1].plot(x_plot, s, "k-", lw=2, label="库容")
    axes[1].axhline(s_flood, color="r", ls="--", lw=1.8, label="防洪控制库容")
    axes[1].axhline(s_target, color="purple", ls=":", lw=1.8, label="末期目标库容")
    axes[1].fill_between(x_plot, s_flood, s, where=(s > s_flood), color="red", alpha=0.25, label="超汛限区")
    axes[1].set_ylabel("库容 (百万m3)")
    axes[1].set_title("库容演化与防洪控制")
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    # 图3：净水头与出力
    ax3 = axes[2]
    ax3.plot(x_plot, head, "c-", lw=2, label="净水头")
    ax3.set_ylabel("净水头 (m)")
    ax3.set_xlabel("调度时段")
    ax3.grid(alpha=0.25)
    ax3.set_title("水头与出力过程")

    ax3b = ax3.twinx()
    ax3b.plot(x_plot, power_mw, "m-", lw=2, label="出力")
    ax3b.set_ylabel("出力 (MW)")

    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3b.get_legend_handles_labels()
    ax3b.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.tight_layout()
    plt.savefig('ch05_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch05_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
