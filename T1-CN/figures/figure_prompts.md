# T1-CN 章节插图生成提示词

## 第八章 CPSS框架

### 图8-1: CPSS三层架构图
**文件名**: `ch08_cpss_architecture.png`
**类型**: 架构图
**提示词**:
```
Create a professional three-layer architecture diagram for CPSS (Cyber-Physical-Social System) framework.
- Top layer (purple): Social Layer - "社会层" with icons for economic optimization, safety constraints, grid coordination
- Middle layer (blue): Cyber Layer - "信息层" with icons for control algorithms, MPC, observers, fault diagnosis
- Bottom layer (green): Physical Layer - "物理层" with icons for hydraulic systems, mechanical systems, electrical systems
- Bidirectional arrows between layers showing data flow and feedback
- Center: unified mathematical language (state space, transfer functions, Lyapunov functions)
- Style: flat vector, white background, Chinese labels, 180mm × 120mm, 300dpi
```

### 图8-2: 多物理场耦合示意图
**文件名**: `ch08_multiphysics_coupling.png`
**类型**: 系统示意图
**提示词**:
```
Create a multi-physics coupling diagram for hydropower station.
- Three subsystems with different colors:
  - Hydraulic system (blue): penstock, surge tank, turbine flow
  - Mechanical system (green): turbine, generator rotor, shaft
  - Electrical system (orange): generator, excitation, grid
- Coupling arrows showing state variable interactions
- State vector equation: x = [z_s, q, ω, y, δ, E_q']^T
- 6th-order nonlinear coupled system annotation
- Style: technical schematic, white background, 180mm × 100mm, 300dpi
```

### 图8-3: 三层融合控制流程图
**文件名**: `ch08_hierarchical_control.png`
**类型**: 流程图
**提示词**:
```
Create a hierarchical control flow diagram showing three-layer fusion.
- Top (Social layer): inputs (grid dispatch, load forecast) → optimal power trajectory P*(t)
- Middle (Cyber layer): inputs (P*(t), system state x) → control commands u
- Bottom (Physical layer): inputs (u) → actual response y
- Feedback loops from bottom to top
- Time scales: minutes (top), seconds (middle), milliseconds (bottom)
- Style: flowchart with rounded rectangles, arrows, Chinese labels, 180mm × 130mm, 300dpi
```

### 图8-4: 性能对比曲线
**文件名**: `ch08_performance_comparison.png`
**类型**: 数据曲线（需用matplotlib生成）
**Python代码**:
```python
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 左图：频率响应
t = np.linspace(0, 60, 300)
f_pid = 50 + 0.5*np.exp(-t/25)*np.sin(2*np.pi*t/12)
f_cpss = 50 + 0.15*np.exp(-t/12)*np.sin(2*np.pi*t/12)

ax1.plot(t, f_pid, 'r--', label='传统PID', linewidth=2)
ax1.plot(t, f_cpss, 'b-', label='CPSS框架', linewidth=2)
ax1.axhline(y=50, color='k', linestyle=':', alpha=0.5)
ax1.set_xlabel('时间 (s)')
ax1.set_ylabel('频率 (Hz)')
ax1.set_title('频率响应对比')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 右图：功率跟踪
P_ref = 250 + 50*np.sin(2*np.pi*t/30)
P_pid = P_ref + 20*np.exp(-t/25)*np.sin(2*np.pi*t/8)
P_cpss = P_ref + 5*np.exp(-t/12)*np.sin(2*np.pi*t/8)

ax2.plot(t, P_ref, 'k:', label='参考功率', linewidth=2)
ax2.plot(t, P_pid, 'r--', label='传统PID', linewidth=2)
ax2.plot(t, P_cpss, 'b-', label='CPSS框架', linewidth=2)
ax2.set_xlabel('时间 (s)')
ax2.set_ylabel('功率 (MW)')
ax2.set_title('功率跟踪对比')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('ch08_performance_comparison.png', dpi=300, bbox_inches='tight')
```

---

## 第九章 统一传递函数族

### 图9-1: 引水系统传递函数对比
**文件名**: `ch09_penstock_transfer_functions.png`
**类型**: 频率响应图（需用matplotlib生成）
**Python代码**:
```python
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 频率范围
w = np.logspace(-3, 1, 500)

# 刚性水击（一阶惯性）
Tw = 2.5
G_rigid = signal.TransferFunction([1], [Tw, 1])
_, mag_rigid, phase_rigid = signal.bode(G_rigid, w)

# 弹性水击（近似）
mag_elastic = 20*np.log10(1/np.sqrt(Tw*w))
phase_elastic = -45*np.ones_like(w)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# 幅频特性
ax1.semilogx(w, mag_rigid, 'b-', label='刚性水击', linewidth=2)
ax1.semilogx(w, mag_elastic, 'r--', label='弹性水击', linewidth=2)
ax1.set_ylabel('幅值 (dB)')
ax1.set_title('引水系统传递函数对比')
ax1.legend()
ax1.grid(True, which='both', alpha=0.3)

# 相频特性
ax2.semilogx(w, phase_rigid, 'b-', label='刚性水击', linewidth=2)
ax2.semilogx(w, phase_elastic, 'r--', label='弹性水击', linewidth=2)
ax2.set_xlabel('频率 (rad/s)')
ax2.set_ylabel('相位 (度)')
ax2.legend()
ax2.grid(True, which='both', alpha=0.3)

plt.tight_layout()
plt.savefig('ch09_penstock_transfer_functions.png', dpi=300, bbox_inches='tight')
```

### 图9-2: Bode图示例
**文件名**: `ch09_bode_plot.png`
**类型**: Bode图（需用matplotlib生成）

### 图9-3: Nyquist图示例
**文件名**: `ch09_nyquist_plot.png`
**类型**: Nyquist图（需用matplotlib生成）

---

## 第十一章 CBF理论

### 图11-1: CBF安全集合示意图
**文件名**: `ch11_cbf_safe_set.png`
**类型**: 概念示意图
**提示词**:
```
Create a 2D state space diagram illustrating Control Barrier Function (CBF) concept.
- X-Y axes representing state space
- Green shaded region: safe set C = {h(x) ≥ 0}
- Red boundary curve: barrier function h(x) = 0
- Blue trajectory: system trajectory staying inside safe set
- Arrows showing vector field
- Annotations: "安全集合 C", "屏障函数 h(x)=0", "系统轨迹"
- Style: mathematical diagram, white background, Chinese labels, 150mm × 150mm, 300dpi
```

### 图11-2: CBF-QP控制器架构
**文件名**: `ch11_cbf_qp_architecture.png`
**类型**: 控制框图
**提示词**:
```
Create a control block diagram for CBF-QP controller.
- Top: Nominal Controller (MPC) block → u_nom
- Middle: CBF-QP Solver block with inputs (u_nom, x, CBF constraints) → u*
- Bottom: Plant block with input u* → output y
- Feedback loop from y to both controllers
- Safety constraints shown as red dashed box around CBF-QP
- Annotations in Chinese
- Style: control systems diagram, white background, 180mm × 100mm, 300dpi
```

### 图11-3: 泵站CBF案例仿真曲线
**文件名**: `ch11_cbf_pump_case.png`
**类型**: 仿真曲线（需用matplotlib生成）
**Python代码**:
```python
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# 时间
t = np.linspace(0, 100, 500)

# 需求阶跃
Q_demand = 50 + 30*(t > 20)

# 压力响应
p_min, p_max = 0.3, 0.8
p_no_cbf = 0.5 + 0.3*np.exp(-(t-20)/10)*np.sin(2*np.pi*(t-20)/15)*(t>20)
p_no_cbf = np.clip(p_no_cbf, 0.2, 0.9)

p_with_cbf = 0.5 + 0.2*np.exp(-(t-20)/8)*np.sin(2*np.pi*(t-20)/15)*(t>20)
p_with_cbf = np.clip(p_with_cbf, p_min, p_max)

# 上图：压力
ax1.plot(t, p_no_cbf, 'r--', label='无CBF', linewidth=2)
ax1.plot(t, p_with_cbf, 'b-', label='有CBF', linewidth=2)
ax1.axhline(y=p_min, color='r', linestyle=':', label='安全下限', linewidth=1.5)
ax1.axhline(y=p_max, color='r', linestyle=':', label='安全上限', linewidth=1.5)
ax1.fill_between(t, p_min, p_max, alpha=0.1, color='g')
ax1.set_ylabel('压力 (MPa)')
ax1.set_title('泵站CBF安全控制仿真')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 下图：流量
Q_no_cbf = Q_demand + 15*np.exp(-(t-20)/10)*np.sin(2*np.pi*(t-20)/12)*(t>20)
Q_with_cbf = Q_demand + 8*np.exp(-(t-20)/8)*np.sin(2*np.pi*(t-20)/12)*(t>20)

ax2.plot(t, Q_demand, 'k:', label='需求流量', linewidth=2)
ax2.plot(t, Q_no_cbf, 'r--', label='无CBF', linewidth=2)
ax2.plot(t, Q_with_cbf, 'b-', label='有CBF', linewidth=2)
ax2.set_xlabel('时间 (s)')
ax2.set_ylabel('流量 (m³/s)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('ch11_cbf_pump_case.png', dpi=300, bbox_inches='tight')
```

---

## 图片生成优先级

### 高优先级（概念图，需AI生成或手绘）
1. 图8-1: CPSS三层架构图
2. 图8-2: 多物理场耦合示意图
3. 图8-3: 三层融合控制流程图
4. 图11-1: CBF安全集合示意图
5. 图11-2: CBF-QP控制器架构

### 中优先级（数据曲线，用Python生成）
1. 图8-4: 性能对比曲线
2. 图9-1: 引水系统传递函数对比
3. 图11-3: 泵站CBF案例仿真曲线

### 低优先级（标准图表，用Python生成）
1. 图9-2: Bode图示例
2. 图9-3: Nyquist图示例

---

## 统一配色方案

- 主色（水/控制）: #1565C0 (深蓝)
- 辅色1（安全/ODD）: #4CAF50 (绿)
- 辅色2（认知智能）: #7B1FA2 (紫)
- 辅色3（扰动/警告）: #FF7043 (橙红)
- 背景: 白色
- 辅助线: #E0E0E0 (浅灰)
