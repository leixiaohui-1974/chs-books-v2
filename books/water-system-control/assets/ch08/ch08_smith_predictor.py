"""
第8章配套仿真：史密斯预估器在长距离明渠中的延时补偿

物理场景：灌溉干渠末端水位控制
- 渠道长度：800m，波速约2 m/s，纯滞后约400s
- 惯性时间常数：500s（渠池蓄水效应）
- 上游泵站→下游取水口的水位响应存在显著纯滞后
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# === 物理系统参数 ===
K_true = 1.0       # 稳态增益（归一化）
T_true = 500.0     # 惯性时间常数 s（渠池蓄水效应）
L_true = 400.0     # 物理纯滞后 s（渠道长800m，波速~2m/s）

# 内部预测模型参数（假设完美匹配）
K_model = K_true
T_model = T_true
L_model = L_true

dt = 5.0          # 仿真步长 5s
time = np.arange(0, 5000, dt)
N = len(time)

# 目标设定值：t=200s时设定值阶跃至2.0m
sp = np.zeros(N)
sp_start = int(200 / dt)
sp[sp_start:] = 2.0

# === 标准PI控制器（无补偿）===
y_pid = np.zeros(N)
u_pid = np.zeros(N)
integral_pid = 0.0

# 控制器参数（基于无延迟模型整定，偏激进以展示问题）
Kc = 2.0
Tau_I = 300.0

for k in range(1, N):
    err = sp[k] - y_pid[k-1]
    integral_pid += err * dt
    u_pid[k] = np.clip(Kc * (err + integral_pid / Tau_I), 0, 10)

    # 真实对象：含纯滞后的一阶惯性系统
    idx_delayed = k - int(L_true / dt)
    u_eff = u_pid[idx_delayed] if idx_delayed >= 0 else 0.0
    y_pid[k] = y_pid[k-1] + (dt / T_true) * (K_true * u_eff - y_pid[k-1])

# === 史密斯预估器PI控制器 ===
y_smith = np.zeros(N)
u_smith = np.zeros(N)
y_m_nodelay = np.zeros(N)
y_m_delay = np.zeros(N)
integral_smith = 0.0

for k in range(1, N):
    # 核心：修正误差 = SP - (y_real + y_m_nodelay - y_m_delay)
    err_mod = sp[k] - (y_smith[k-1] + y_m_nodelay[k-1] - y_m_delay[k-1])

    integral_smith += err_mod * dt
    u_smith[k] = np.clip(Kc * (err_mod + integral_smith / Tau_I), 0, 10)

    # (a) 真实物理对象
    idx_delayed_true = k - int(L_true / dt)
    u_eff_true = u_smith[idx_delayed_true] if idx_delayed_true >= 0 else 0.0
    y_smith[k] = y_smith[k-1] + (dt / T_true) * (K_true * u_eff_true - y_smith[k-1])

    # (b) 内部无延迟模型
    y_m_nodelay[k] = y_m_nodelay[k-1] + (dt / T_model) * (K_model * u_smith[k] - y_m_nodelay[k-1])

    # (c) 内部带延迟模型
    idx_delayed_model = k - int(L_model / dt)
    u_eff_model = u_smith[idx_delayed_model] if idx_delayed_model >= 0 else 0.0
    y_m_delay[k] = y_m_delay[k-1] + (dt / T_model) * (K_model * u_eff_model - y_m_delay[k-1])

# === 绘图 ===
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

# 子图1：水位响应
ax1.plot(time, sp, 'k:', linewidth=1.5, label='Setpoint')
ax1.plot(time, y_pid, 'r--', linewidth=1.5, label='Standard PI')
ax1.plot(time, y_smith, 'b-', linewidth=2, label='Smith Predictor + PI')
ax1.axvspan(200, 200 + L_true, alpha=0.1, color='gray')
ax1.text(300, 0.3, f'Dead Zone\n({int(L_true)}s)', color='dimgray',
         fontweight='bold', fontsize=10, ha='center')
ax1.set_ylabel('Water Level [m]', fontweight='bold')
ax1.set_title(f'Smith Predictor: Dead-Time Compensation (L={int(L_true)}s, T={int(T_true)}s)',
              fontsize=13, fontweight='bold')
ax1.legend(loc='lower right', fontsize=10)
ax1.grid(True, alpha=0.3)

# 子图2：控制输出
ax2.plot(time, u_pid, 'r--', linewidth=1.5, label='Pump Cmd (Standard PI)')
ax2.plot(time, u_smith, 'b-', linewidth=2, label='Pump Cmd (Smith Predictor)')
ax2.axhline(10.0, color='gray', linestyle=':', linewidth=0.8, label='Physical Max')
ax2.set_xlabel('Time [s]', fontweight='bold')
ax2.set_ylabel('Pump Command', fontweight='bold')
ax2.legend(loc='upper right', fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
save_path = os.path.join(output_dir, "smith_predictor_sim.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')

# === 对比表格 ===
history = []
snapshots = [300, 600, 1000, 1500, 2500, 4000]

for t_val in snapshots:
    idx = int(t_val / dt)
    if idx < N:
        history.append({
            'Time (s)': t_val,
            'Setpoint': sp[idx],
            'PI Level (m)': round(y_pid[idx], 3),
            'Smith Level (m)': round(y_smith[idx], 3),
            'PI Cmd': round(u_pid[idx], 2),
            'Smith Cmd': round(u_smith[idx], 2)
        })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
table_path = os.path.join(output_dir, "smith_table.md")
with open(table_path, "w", encoding="utf-8") as f:
    f.write(md_table)

print(f"Figure saved to: {save_path}")
print(f"Table saved to: {table_path}")
print(f"\n{md_table}")
