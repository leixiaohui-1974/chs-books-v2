# -*- coding: utf-8 -*-
"""
《流域数字孪生与智能决策》第5章：可视化与交互式推演
功能：构建简化流域数字孪生仿真模型，进行情景对比、KPI评估，并提供交互式参数推演。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d


# =========================
# 1) 关键参数（统一管理）
# =========================
PARAMS = {
    "days": 120,            # 仿真总天数
    "dt": 1.0,              # 时间步长（天）
    "capacity": 1200.0,     # 水库总库容（百万m3，示意）
    "dead_storage": 180.0,  # 死库容
    "flood_limit": 900.0,   # 防洪限制水位对应库容
    "init_storage": 620.0,  # 初始库容
    "max_release": 65.0,    # 最大下泄能力
    "eco_flow": 20.0,       # 生态最小下泄
    "decay_k": 0.035,       # 污染物衰减系数
    "c0": 1.25,             # 初始污染物浓度（mg/L，示意）
    "seed": 42              # 随机种子（保证可复现）
}


def generate_inputs(days, dt, seed, rain_scale=1.0, pollution_scale=1.0):
    """生成外部驱动：降雨、入流、需水、来水浓度"""
    rng = np.random.default_rng(seed)
    t = np.arange(0, days + dt, dt)

    # 构造具有季节项+周周期+随机扰动的降雨序列
    rain = (
        22
        + 12 * np.sin(2 * np.pi * t / 28)
        + 7 * np.sin(2 * np.pi * t / 7)
        + rng.normal(0, 3, size=t.size)
    )
    rain = np.clip(rain, 0, None) * rain_scale

    # 线性化“降雨-产流”关系（简化示意）
    qin = 18 + 0.75 * rain

    # 下游需水过程
    demand = 28 + 4 * np.sin(2 * np.pi * (t - 5) / 30)

    # 入库污染物浓度过程
    cin = np.clip(
        (1.4 + 0.25 * np.sin(2 * np.pi * t / 20) + rng.normal(0, 0.06, size=t.size))
        * pollution_scale,
        0.3,
        None,
    )
    return t, rain, qin, demand, cin


def operation_rule(storage, demand, p):
    """调度规则：兼顾供水、生态、防洪"""
    release = max(p["eco_flow"], demand)

    # 超过防洪限制后，按超限量增加泄流
    if storage > p["flood_limit"]:
        extra = 0.55 * (storage - p["flood_limit"])
        release = max(release, p["eco_flow"] + extra)

    # 库容过低时，适当保水
    if storage < p["dead_storage"] + 20:
        release = max(p["eco_flow"], 0.75 * release)

    return float(np.clip(release, p["eco_flow"], p["max_release"]))


def simulate(p, rain_scale=1.0, gate_scale=1.0, pollution_scale=1.0):
    """执行一次完整仿真"""
    local = p.copy()
    local["max_release"] = p["max_release"] * gate_scale

    t, rain, qin, demand, cin = generate_inputs(
        local["days"], local["dt"], local["seed"], rain_scale, pollution_scale
    )

    qin_i = interp1d(t, qin, kind="linear", fill_value="extrapolate")
    demand_i = interp1d(t, demand, kind="linear", fill_value="extrapolate")

    # 库容微分方程 dS/dt = Qin - Qout
    def dS_dt(tt, s):
        q_in = float(qin_i(tt))
        dem = float(demand_i(tt))
        q_out = operation_rule(float(s[0]), dem, local)
        return [q_in - q_out]

    sol = solve_ivp(
        dS_dt,
        (t[0], t[-1]),
        [local["init_storage"]],
        t_eval=t,
        max_step=local["dt"],
    )

    storage = np.clip(sol.y[0], local["dead_storage"], local["capacity"])
    release = np.array([operation_rule(storage[i], demand[i], local) for i in range(t.size)])

    # 污染物质量守恒：M(t+dt)=M+入-出-衰减
    conc = np.zeros_like(t)
    conc[0] = local["c0"]
    for i in range(1, t.size):
        dt = local["dt"]
        v_prev = max(storage[i - 1], 1e-6)
        mass_prev = conc[i - 1] * v_prev
        mass_in = qin[i - 1] * cin[i - 1] * dt
        mass_out = release[i - 1] * conc[i - 1] * dt
        decay = local["decay_k"] * mass_prev * dt
        mass_new = max(mass_prev + mass_in - mass_out - decay, 0.0)
        conc[i] = mass_new / max(storage[i], 1e-6)

    # KPI
    flood_safe = np.mean(storage <= local["flood_limit"]) * 100
    supply = np.mean(release >= demand) * 100
    eco = np.mean(release >= local["eco_flow"]) * 100
    avg_conc = float(np.mean(conc))
    water_quality_score = max(0.0, 100 - 20 * avg_conc)
    score = 0.35 * flood_safe + 0.35 * supply + 0.20 * eco + 0.10 * water_quality_score

    kpi = {
        "flood_safe_rate": flood_safe,
        "supply_rate": supply,
        "eco_rate": eco,
        "avg_conc": avg_conc,
        "score": score,
    }

    return {
        "t": t,
        "rain": rain,
        "qin": qin,
        "demand": demand,
        "release": release,
        "cin": cin,
        "storage": storage,
        "conc": conc,
        "kpi": kpi,
    }


def print_kpi_table(results):
    """打印KPI结果表格"""
    print("\n=== KPI结果表（第5章 可视化与交互式推演） ===")
    header = "{:<10}{:>12}{:>12}{:>12}{:>12}{:>12}".format(
        "情景", "防洪安全率%", "供水保证率%", "生态达标率%", "平均浓度", "综合得分"
    )
    print(header)
    print("-" * 70)
    for name, sim in results:
        k = sim["kpi"]
        print(
            "{:<10}{:>12.1f}{:>12.1f}{:>12.1f}{:>12.3f}{:>12.1f}".format(
                name, k["flood_safe_rate"], k["supply_rate"], k["eco_rate"], k["avg_conc"], k["score"]
            )
        )


def make_comparison_figure(results, params):
    """生成情景对比图"""
    fig, (ax1, ax2) = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(1, 2, figsize=(12, 4.8))
    for name, sim in results:
        ax1.plot(sim["t"], sim["storage"], linewidth=2, label=name)
    ax1.axhline(params["flood_limit"], color="r", linestyle="--", label="防洪限制")
    ax1.set_title("情景库容过程对比")
    ax1.set_xlabel("时间（天）")
    ax1.set_ylabel("库容")
    ax1.grid(alpha=0.3)
    ax1.legend()

    names = [r[0] for r in results]
    scores = [r[1]["kpi"]["score"] for r in results]
    ax2.bar(names, scores, color=["#4C78A8", "#F58518", "#54A24B"])
    ax2.set_title("综合KPI得分对比")
    ax2.set_ylabel("得分")
    ax2.set_ylim(0, 105)
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("流域数字孪生情景评估", fontsize=13)
    fig.tight_layout()


def format_kpi_text(k):
    return (
        f"防洪安全率：{k['flood_safe_rate']:.1f}%\n"
        f"供水保证率：{k['supply_rate']:.1f}%\n"
        f"生态达标率：{k['eco_rate']:.1f}%\n"
        f"平均浓度：{k['avg_conc']:.3f}\n"
        f"综合得分：{k['score']:.1f}"
    )


def make_interactive_figure(params):
    """生成交互式推演图：滑块调整参数后实时更新"""
    sim0 = simulate(params, rain_scale=1.0, gate_scale=1.0, pollution_scale=1.0)

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    plt.subplots_adjust(left=0.08, right=0.74, bottom=0.20, hspace=0.28)

    ax_s, ax_q, ax_c = axes

    line_s, = ax_s.plot(sim0["t"], sim0["storage"], lw=2, color="#1f77b4", label="库容")
    ax_s.axhline(params["flood_limit"], color="r", ls="--", label="防洪限制")
    ax_s.set_ylabel("库容")
    ax_s.set_title("交互式推演：库容过程")
    ax_s.grid(alpha=0.3)
    ax_s.legend()

    line_qin, = ax_q.plot(sim0["t"], sim0["qin"], lw=1.8, color="#2ca02c", label="入流")
    line_rel, = ax_q.plot(sim0["t"], sim0["release"], lw=2, color="#ff7f0e", label="下泄")
    line_dem, = ax_q.plot(sim0["t"], sim0["demand"], lw=1.8, color="#9467bd", label="需水")
    ax_q.set_ylabel("流量")
    ax_q.set_title("交互式推演：入流-下泄-需水")
    ax_q.grid(alpha=0.3)
    ax_q.legend()

    line_cin, = ax_c.plot(sim0["t"], sim0["cin"], lw=1.5, color="#8c564b", label="来水浓度")
    line_conc, = ax_c.plot(sim0["t"], sim0["conc"], lw=2, color="#d62728", label="库内浓度")
    ax_c.set_ylabel("浓度")
    ax_c.set_xlabel("时间（天）")
    ax_c.set_title("交互式推演：水质过程")
    ax_c.grid(alpha=0.3)
    ax_c.legend()

    kpi_box = fig.text(
        0.77, 0.62, format_kpi_text(sim0["kpi"]),
        fontsize=10,
        bbox=dict(boxstyle="round", facecolor="#f5f5f5", edgecolor="#999999")
    )

    # 滑块区域
    ax_rain = plt.axes([0.10, 0.12, 0.56, 0.03])
    ax_gate = plt.axes([0.10, 0.08, 0.56, 0.03])
    ax_poll = plt.axes([0.10, 0.04, 0.56, 0.03])

    s_rain = Slider(ax_rain, "降雨倍率", 0.6, 1.8, valinit=1.0, valstep=0.05)
    s_gate = Slider(ax_gate, "闸门能力倍率", 0.8, 1.6, valinit=1.0, valstep=0.05)
    s_poll = Slider(ax_poll, "污染输入倍率", 0.5, 1.6, valinit=1.0, valstep=0.05)

    ax_reset = plt.axes([0.67, 0.04, 0.06, 0.11])
    b_reset = Button(ax_reset, "重置")

    def update(_):
        sim = simulate(
            params,
            rain_scale=s_rain.val,
            gate_scale=s_gate.val,
            pollution_scale=s_poll.val
        )
        line_s.set_ydata(sim["storage"])
        line_qin.set_ydata(sim["qin"])
        line_rel.set_ydata(sim["release"])
        line_dem.set_ydata(sim["demand"])
        line_cin.set_ydata(sim["cin"])
        line_conc.set_ydata(sim["conc"])

        ax_s.set_ylim(0, max(params["capacity"] * 1.05, np.max(sim["storage"]) * 1.1))
        ax_q.set_ylim(0, 1.2 * max(np.max(sim["qin"]), np.max(sim["release"]), np.max(sim["demand"])))
        ax_c.set_ylim(0, 1.2 * max(np.max(sim["cin"]), np.max(sim["conc"]), 0.1))
        kpi_box.set_text(format_kpi_text(sim["kpi"]))
        fig.canvas.draw_idle()

    def reset(_):
        s_rain.reset()
        s_gate.reset()
        s_poll.reset()

    s_rain.on_changed(update)
    s_gate.on_changed(update)
    s_poll.on_changed(update)
    b_reset.on_clicked(reset)


if __name__ == "__main__":
    # 三个典型情景：基准、强降雨、智慧调度
    scenarios = [
        ("基准情景", 1.00, 1.00, 1.00),
        ("强降雨情景", 1.35, 1.00, 1.15),
        ("智慧调度", 1.35, 1.25, 0.75),
    ]

    results = []
    for name, rain_scale, gate_scale, poll_scale in scenarios:
        results.append((name, simulate(PARAMS, rain_scale, gate_scale, poll_scale)))

    # 1) 打印KPI表格
    print_kpi_table(results)

    # 2) 生成Matplotlib图（对比图 + 交互式推演图）
    make_comparison_figure(results, PARAMS)
    make_interactive_figure(PARAMS)

    plt.savefig('ch05_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch05_simulation_result.png")
# plt.show()  # 禁用弹窗
