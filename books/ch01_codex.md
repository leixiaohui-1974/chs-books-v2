```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASM1好氧子模型仿真（有机物降解 + 硝化）
依赖: numpy, scipy, matplotlib
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


def monod(s, k):
    return s / (k + s + 1e-12)


def asm1_aerobic_rhs(t, x, p):
    # 状态: [S_S, S_NH, S_NO, X_BH, X_BA]
    x_raw = x.copy()
    S_S, S_NH, S_NO, X_BH, X_BA = np.maximum(x_raw, 0.0)

    # 过程速率（Monod动力学）
    rho_H = p["mu_H"] * monod(S_S, p["K_S"]) * monod(p["S_O"], p["K_OH"]) * X_BH
    rho_A = p["mu_A"] * monod(S_NH, p["K_NH"]) * monod(p["S_O"], p["K_OA"]) * X_BA
    rho_bH = p["b_H"] * X_BH
    rho_bA = p["b_A"] * X_BA
    rho = np.array([rho_H, rho_A, rho_bH, rho_bA], dtype=float)

    # ASM1简化计量矩阵 N (5x4)
    # 列顺序: [异养生长, 自养生长(硝化), 异养衰减, 自养衰减]
    N = np.array([
        [-1.0 / p["Y_H"],                  0.0,           0.0,          0.0],  # dS_S
        [-p["i_XB"], -(1.0 / p["Y_A"] + p["i_XB"]), +p["i_XB"], +p["i_XB"]],  # dS_NH
        [0.0,                   +1.0 / p["Y_A"],           0.0,          0.0],  # dS_NO
        [+1.0,                               0.0,          -1.0,          0.0],  # dX_BH
        [0.0,                               +1.0,           0.0,         -1.0],  # dX_BA
    ], dtype=float)

    dxdt = N @ rho

    # 防止积分误差导致状态出现负值后继续向负方向发散
    eps = 1e-10
    for i in range(len(dxdt)):
        if x_raw[i] <= eps and dxdt[i] < 0:
            dxdt[i] = 0.0

    return dxdt


def simulate(params, x0, t_end_h=48.0, n_points=241):
    t_eval_h = np.linspace(0.0, t_end_h, n_points)
    t_eval_d = t_eval_h / 24.0
    t_span_d = (0.0, t_end_h / 24.0)

    sol = solve_ivp(
        fun=lambda t, y: asm1_aerobic_rhs(t, y, params),
        t_span=t_span_d,
        y0=x0,
        t_eval=t_eval_d,
        method="BDF",
        rtol=1e-6,
        atol=1e-8,
    )
    if not sol.success:
        raise RuntimeError(f"积分失败: {sol.message}")
    return t_eval_h, sol.y


def print_kpi(x0, xT):
    S_S0, S_NH0, S_NO0, X_BH0, X_BA0 = x0
    S_Sf, S_NHf, S_NOf, X_BHf, X_BAf = xT

    ss_removal = (S_S0 - S_Sf) / max(S_S0, 1e-12) * 100.0
    nh_removal = (S_NH0 - S_NHf) / max(S_NH0, 1e-12) * 100.0
    no_gen = S_NOf - S_NO0
    nitrif_conv = no_gen / max(S_NH0, 1e-12) * 100.0
    bh_growth = (X_BHf - X_BH0) / max(X_BH0, 1e-12) * 100.0
    ba_growth = (X_BAf - X_BA0) / max(X_BA0, 1e-12) * 100.0

    rows = [
        ("有机底物去除率", ss_removal, "%"),
        ("氨氮去除率", nh_removal, "%"),
        ("硝酸盐生成量", no_gen, "mgN/L"),
        ("表观硝化转化率", nitrif_conv, "%"),
        ("异养菌生物量增幅", bh_growth, "%"),
        ("自养菌生物量增幅", ba_growth, "%"),
        ("终点S_S", S_Sf, "mgCOD/L"),
        ("终点S_NH", S_NHf, "mgN/L"),
        ("终点S_NO", S_NOf, "mgN/L"),
    ]

    print("\nASM1好氧仿真 KPI")
    print(f"{'指标':<18}{'数值':>12}   单位")
    print("-" * 38)
    for name, value, unit in rows:
        print(f"{name:<18}{value:>12.3f}   {unit}")


def plot_substrate(t_h, S_S):
    plt.figure(figsize=(8, 4.6))
    plt.plot(t_h, S_S, color="#1f77b4", lw=2.2, label="S_S")
    plt.xlabel("Time (h)")
    plt.ylabel("S_S (mgCOD/L)")
    plt.title("ASM1 Aerobic Dynamics: Substrate Degradation")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # 参数（可按教材案例调整）
    params = {
        "mu_H": 6.0,    # d^-1, 异养菌最大比增长速率
        "K_S": 20.0,    # mgCOD/L, 异养底物半饱和常数
        "K_OH": 0.2,    # mgO2/L, 异养氧半饱和常数
        "b_H": 0.62,    # d^-1, 异养菌衰减系数
        "Y_H": 0.67,    # mgCODX/mgCODS, 异养产率

        "mu_A": 0.8,    # d^-1, 自养菌最大比增长速率
        "K_NH": 1.0,    # mgN/L, 氨氮半饱和常数
        "K_OA": 0.4,    # mgO2/L, 自养氧半饱和常数
        "b_A": 0.17,    # d^-1, 自养菌衰减系数
        "Y_A": 0.24,    # mgCODX/mgN, 自养产率

        "i_XB": 0.086,  # mgN/mgCODX, 生物量含氮系数
        "S_O": 2.0,     # mgO2/L, 好氧条件下近似恒定DO
    }

    # 初始状态: [S_S, S_NH, S_NO, X_BH, X_BA]
    x0 = np.array([200.0, 35.0, 1.0, 120.0, 20.0], dtype=float)

    t_h, X = simulate(params, x0, t_end_h=48.0, n_points=241)
    print_kpi(x0, X[:, -1])
    plot_substrate(t_h, X[0, :])
```

代码解读（约500字）：
这段脚本把第1章 ASM1 的核心思想落在一个可教学演示的好氧子模型上，状态向量取 `S_S、S_NH、S_NO、X_BH、X_BA`，分别对应易降解有机底物、氨氮、硝态氮、异养菌和自养菌。动力学速率由 Monod 形式构造：`rho_H` 表示异养菌好氧生长，受 `S_S` 与溶解氧双重限制；`rho_A` 表示自养菌硝化生长，受 `S_NH` 与溶解氧限制；`rho_bH`、`rho_bA` 为两类菌衰减。状态方程采用 ASM 常见写法 `dx/dt = N·rho`，其中 `N` 是化学计量矩阵，明确每个反应对每个状态的“消耗/生成”关系，结构清晰且便于扩展到完整 13 状态。数值求解使用 `solve_ivp(BDF)`，这是处理活性污泥刚性方程较稳妥的选择。脚本最后输出 KPI 表格（有机底物去除率、氨氮去除率、硝酸盐生成量、表观硝化转化率、生物量增幅），并绘制一张 `S_S` 随时间变化图，直观看到有机物被快速降解、硝化逐步推进。读者可优先修改三类参数：一是运行条件（`S_O`、仿真时长 `t_end_h`）；二是初始工况 `x0`；三是动力学参数（`mu_H、mu_A、K_S、K_NH、Y_H、Y_A` 等）。若要贴近工程系统，可进一步加入进出水流量项、氧传质方程和缺氧反硝化过程。  

说明：当前会话策略禁止我在终端执行 Python 做实机校验，但脚本按标准 `numpy/scipy/matplotlib` 接口编写。