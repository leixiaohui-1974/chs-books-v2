"""
《洪水预报与防洪调度》 第8章配套仿真脚本
功能：构建“洪水预报-防洪调度”一体化模型，对比规则调度与预报MPC调度，
输出KPI结果表格，并绘制入出库流量、水位、库容过程线。
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# -----------------------------
# 关键参数（可按工程资料修改）
# -----------------------------
DT = 3600.0                # 计算步长，s（1小时）
N_STEPS = 72               # 仿真时长，步（72小时）
HORIZON = 12               # 预见期长度，步（12小时）

# 水位-库容参数（简化为抛物线关系）
H_DEAD = 80.0              # 死水位，m
H_FLOOD_LIMIT = 95.0       # 防洪限制水位，m
H_SAFE = 98.0              # 安全控制水位，m
H_MAX = 101.0              # 极限水位（含非常溢洪），m
STORAGE_K = 5.2e6          # V = k*(H-H_dead)^2 中的k，m3/m2

V_DEAD = 0.0
V_TARGET = STORAGE_K * (H_FLOOD_LIMIT - H_DEAD) ** 2
V_MAX = STORAGE_K * (H_MAX - H_DEAD) ** 2

# 下泄与机组（闸门）约束
Q_MIN = 100.0              # 最小下泄，m3/s
Q_MAX = 2500.0             # 常规最大下泄，m3/s
Q_DS_LIMIT = 1800.0        # 下游安全流量阈值，m3/s
DQ_MAX = 300.0             # 每小时最大变幅，m3/s/h

# MPC目标函数权重
W_LEVEL = 4.0              # 水位超限惩罚
W_DS = 1.2                 # 下游超限惩罚
W_SMOOTH = 0.05            # 动作平滑惩罚
W_RAMP = 0.30              # 变幅越限惩罚
W_TERMINAL = 6.0           # 末端库容偏差惩罚


def storage_from_level(h):
    """由水位计算库容"""
    return STORAGE_K * np.maximum(h - H_DEAD, 0.0) ** 2


def level_from_storage(v):
    """由库容反算水位"""
    return H_DEAD + np.sqrt(np.maximum(v, 0.0) / STORAGE_K)


def make_inflow_series(n):
    """构造双峰入库洪水过程（可替换为实测数据）"""
    t = np.arange(n)
    base = 320.0
    peak1 = 3200.0 * np.exp(-0.5 * ((t - 22.0) / 5.5) ** 2)
    peak2 = 2100.0 * np.exp(-0.5 * ((t - 44.0) / 7.5) ** 2)
    return base + peak1 + peak2


def build_forecasts(q_true, horizon, seed=2026):
    """构造滚动预报序列：含先验偏差与随预见期衰减的随机误差"""
    rng = np.random.default_rng(seed)
    n = len(q_true)
    forecasts = []
    for t in range(n):
        lead = np.arange(horizon)
        idx = np.clip(t + lead, 0, n - 1)

        # 近预见期误差小、远预见期误差略大
        bias = 0.10 * np.exp(-lead / 8.0)
        noise = rng.normal(0.0, 70.0, size=horizon) * np.exp(-lead / 10.0)

        qf = np.maximum(0.0, q_true[idx] * (1.0 + bias) + noise)
        forecasts.append(qf)
    return forecasts


def rule_control(h, q_in, q_prev):
    """传统规则调度：按水位分段+出库变幅约束"""
    if h <= H_FLOOD_LIMIT:
        q_tar = max(Q_MIN, 0.45 * q_in)
    elif h <= H_SAFE:
        q_tar = max(Q_MIN, 0.65 * q_in)
    else:
        q_tar = max(Q_DS_LIMIT, 0.90 * q_in)

    q_tar = np.clip(q_tar, q_prev - DQ_MAX, q_prev + DQ_MAX)
    return float(np.clip(q_tar, Q_MIN, Q_MAX))


def mpc_control(v0, q_prev, q_forecast):
    """MPC调度：每步滚动优化未来HORIZON步泄量序列"""
    m = len(q_forecast)

    def objective(u):
        v = v0
        j = 0.0
        for i in range(m):
            q = u[i]
            dq = q - (q_prev if i == 0 else u[i - 1])

            # 连续方程离散化：V(k+1)=V(k)+(Qin-Qout)*dt
            v = v + (q_forecast[i] - q) * DT
            h = level_from_storage(v)

            # 多目标惩罚
            j += W_LEVEL * max(0.0, h - H_SAFE) ** 2
            j += W_DS * max(0.0, q - Q_DS_LIMIT) ** 2 / 1e5
            j += W_SMOOTH * (dq ** 2) / 1e5
            j += W_RAMP * max(0.0, abs(dq) - DQ_MAX) ** 2 / 1e5

        # 末端库容回归目标
        j += W_TERMINAL * ((v - V_TARGET) ** 2) / 1e12
        return j

    u0 = np.full(m, np.clip(q_prev, Q_MIN, Q_MAX))
    bounds = [(Q_MIN, Q_MAX)] * m
    res = minimize(
        objective, u0, method="SLSQP", bounds=bounds,
        options={"maxiter": 80, "ftol": 1e-6, "disp": False}
    )

    # 若优化失败则采用保守回退策略
    if res.success:
        q_cmd = float(res.x[0])
    else:
        q_cmd = float(np.clip(q_prev + 0.5 * (q_forecast[0] - q_prev), Q_MIN, Q_MAX))

    # 再次施加变幅约束
    q_cmd = np.clip(q_cmd, q_prev - DQ_MAX, q_prev + DQ_MAX)
    q_cmd = np.clip(q_cmd, Q_MIN, Q_MAX)
    return float(q_cmd)


def run_simulation(strategy, q_in, forecasts):
    """执行全时段仿真"""
    n = len(q_in)
    q_out = np.zeros(n)
    v = np.zeros(n + 1)
    h = np.zeros(n + 1)

    v[0] = V_TARGET
    h[0] = level_from_storage(v[0])
    q_prev = 300.0

    for t in range(n):
        if strategy == "rule":
            q_cmd = rule_control(h[t], q_in[t], q_prev)
        else:
            q_cmd = mpc_control(v[t], q_prev, forecasts[t])

        q_real = q_cmd
        v_next = v[t] + (q_in[t] - q_real) * DT

        # 防止库容低于死库容
        if v_next < V_DEAD:
            q_real = max(0.0, q_in[t] + (v[t] - V_DEAD) / DT)
            v_next = V_DEAD

        # 超过极限库容时触发非常溢洪（自动加大出库）
        if v_next > V_MAX:
            spill = (v_next - V_MAX) / DT
            q_real += spill
            v_next = V_MAX

        q_out[t] = q_real
        v[t + 1] = v_next
        h[t + 1] = level_from_storage(v_next)
        q_prev = q_real

    return q_out, v, h


def calc_kpi(name, q_in, q_out, h, v):
    """计算调度评价指标"""
    peak_in = np.max(q_in)
    peak_out = np.max(q_out)
    return {
        "方案": name,
        "入库峰值(m3/s)": peak_in,
        "出库峰值(m3/s)": peak_out,
        "削峰率(%)": (peak_in - peak_out) / peak_in * 100.0,
        "最高水位(m)": np.max(h),
        "超安全水位时长(h)": np.sum(h > H_SAFE) * DT / 3600.0,
        "下游超限时长(h)": np.sum(q_out > Q_DS_LIMIT) * DT / 3600.0,
        "总下泄量(亿m3)": np.sum(q_out) * DT / 1e8,
        "末时库容偏差(百万m3)": (v[-1] - V_TARGET) / 1e6,
    }


def print_kpi_table(rows):
    """打印KPI结果表格"""
    headers = [
        "方案", "入库峰值(m3/s)", "出库峰值(m3/s)", "削峰率(%)", "最高水位(m)",
        "超安全水位时长(h)", "下游超限时长(h)", "总下泄量(亿m3)", "末时库容偏差(百万m3)"
    ]
    widths = [14, 16, 16, 10, 12, 18, 16, 14, 22]

    def fmt(x):
        return x if isinstance(x, str) else f"{x:.2f}"

    print("\n=== KPI结果表（第8章：洪水预报与防洪调度）===")
    print("".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("-" * sum(widths))
    for r in rows:
        print("".join(fmt(r[h]).ljust(w) for h, w in zip(headers, widths)))


def plot_results(t, q_in, q_rule, q_mpc, h_rule, h_mpc, v_rule, v_mpc):
    """绘制仿真结果图"""
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    t_state = np.arange(len(h_rule))

    fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

    # 图1：入出库流量
    ax[0].plot(t, q_in, "k-", lw=2.0, label="入库流量")
    ax[0].plot(t, q_rule, "--", lw=1.8, label="规则调度出库")
    ax[0].plot(t, q_mpc, "-", lw=1.8, label="预报MPC出库")
    ax[0].axhline(Q_DS_LIMIT, color="r", ls=":", lw=1.5, label="下游安全流量")
    ax[0].set_ylabel("流量 (m3/s)")
    ax[0].legend(loc="upper right")
    ax[0].grid(alpha=0.3)

    # 图2：水位过程
    ax[1].plot(t_state, h_rule, "--", lw=1.8, label="规则调度水位")
    ax[1].plot(t_state, h_mpc, "-", lw=1.8, label="预报MPC水位")
    ax[1].axhline(H_FLOOD_LIMIT, color="orange", ls=":", lw=1.5, label="防洪限制水位")
    ax[1].axhline(H_SAFE, color="r", ls=":", lw=1.5, label="安全控制水位")
    ax[1].set_ylabel("水位 (m)")
    ax[1].legend(loc="upper right")
    ax[1].grid(alpha=0.3)

    # 图3：库容过程
    ax[2].plot(t_state, v_rule / 1e8, "--", lw=1.8, label="规则调度库容")
    ax[2].plot(t_state, v_mpc / 1e8, "-", lw=1.8, label="预报MPC库容")
    ax[2].axhline(V_TARGET / 1e8, color="g", ls=":", lw=1.5, label="目标库容")
    ax[2].set_xlabel("时间步 (h)")
    ax[2].set_ylabel("库容 (亿m3)")
    ax[2].legend(loc="upper right")
    ax[2].grid(alpha=0.3)

    fig.suptitle("第8章仿真：洪水预报驱动的防洪调度对比")
    plt.tight_layout()
    plt.savefig('ch08_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch08_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    # 1) 生成入库洪水与滚动预报
    q_in = make_inflow_series(N_STEPS)
    forecasts = build_forecasts(q_in, HORIZON, seed=2026)

    # 2) 两种调度策略仿真
    q_rule, v_rule, h_rule = run_simulation("rule", q_in, forecasts)
    q_mpc, v_mpc, h_mpc = run_simulation("mpc", q_in, forecasts)

    # 3) KPI统计与表格打印
    kpi_rule = calc_kpi("规则调度", q_in, q_rule, h_rule, v_rule)
    kpi_mpc = calc_kpi("预报MPC调度", q_in, q_mpc, h_mpc, v_mpc)
    print_kpi_table([kpi_rule, kpi_mpc])

    # 4) 绘图
    t = np.arange(N_STEPS)
    plot_results(t, q_in, q_rule, q_mpc, h_rule, h_mpc, v_rule, v_mpc)
