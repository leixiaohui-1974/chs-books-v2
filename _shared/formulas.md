# CHS书系 核心公式库

> **版本**: v1, 2026-04-27
> **目的**: 全书系核心公式只在此处定稿，各卷引用时不得擅自修改公式形式、编号和变量符号
> **编号规则**: 公式在本书系中的统一编号为 `(T1-CN X-Y)` 格式，指向首次完整定义的来源

---

## 1. Saint-Venant方程（圣维南方程组）

**编号**: (T1-CN 4-1, 4-2)

**连续方程**（质量守恒）：
$$
\frac{\partial A}{\partial t} + \frac{\partial Q}{\partial x} = q_l \tag{T1-CN 4-1}
$$

**动量方程**（动量守恒）：
$$
\frac{\partial Q}{\partial t} + \frac{\partial}{\partial x}\left(\frac{Q^2}{A}\right) + gA\frac{\partial h}{\partial x} + gA(S_f - S_0) = 0 \tag{T1-CN 4-2}
$$

**变量说明**：
- $A$：过水断面面积（m²）
- $Q$：流量（m³/s）
- $h$：水深（m）
- $q_l$：侧向入流（m²/s）
- $S_f$：摩阻比降
- $S_0$：渠底比降
- $g$：重力加速度（9.81 m/s²）

**首次出现**: T1-CN §4.1
**被引用**: T2a ch03—ch05

---

## 2. IDZ传递函数（积分-延迟-零点模型）

**编号**: (T1-CN 4-5)

**标准形式**：
$$
G(s) = \frac{1 + \tau_m s}{A_s \cdot s} e^{-\tau_d s} \tag{T1-CN 4-5}
$$

**扩展形式（含零点）**：
$$
G(s) = \frac{(1 + \tau_m s) e^{-\tau_d s}}{A_s \cdot s} \tag{T1-CN 4-6}
$$

**变量说明**：
- $A_s$：背水面积（m²），表征渠段的积分（蓄水）特性
- $\tau_d$：传输延迟时间（s），表征水波从上游传播到下游所需时间
- $\tau_m$：零点时间常数（s），表征下游水位对上游出流的瞬时响应分量

**首次出现**: T1-CN §4.4
**被引用**: T2a ch05—ch07, T2b

---

## 3. 线性状态空间表达

**编号**: (T1-CN 2-1, 2-2)

**状态方程**：
$$
\dot{\mathbf{x}} = \mathbf{A}\mathbf{x} + \mathbf{B}\mathbf{u} + \mathbf{E}\mathbf{w} \tag{T1-CN 2-1}
$$

**观测方程**：
$$
\mathbf{y} = \mathbf{C}\mathbf{x} + \mathbf{D}\mathbf{u} + \mathbf{v} \tag{T1-CN 2-2}
$$

**变量说明**：
- $\mathbf{x} \in \mathbb{R}^n$：状态向量
- $\mathbf{u} \in \mathbb{R}^m$：控制输入向量
- $\mathbf{w}$：过程扰动
- $\mathbf{y} \in \mathbb{R}^p$：观测输出向量
- $\mathbf{v}$：观测噪声

**首次出现**: T1-CN §2.3
**被引用**: T2a ch02, ch08

---

## 4. 可控性与可观性判据

**编号**: (T1-CN 6-1, 6-2)

**可控性矩阵**：
$$
\mathcal{C} = [\mathbf{B} \;\; \mathbf{AB} \;\; \cdots \;\; \mathbf{A}^{n-1}\mathbf{B}] \tag{T1-CN 6-1}
$$

**可观性矩阵**：
$$
\mathcal{O} = [\mathbf{C}^\top \;\; \mathbf{A}^\top\mathbf{C}^\top \;\; \cdots \;\; (\mathbf{A}^\top)^{n-1}\mathbf{C}^\top]^\top \tag{T1-CN 6-2}
$$

**判据**：$\text{rank}(\mathcal{C}) = n$ 则完全可控；$\text{rank}(\mathcal{O}) = n$ 则完全可观。

**首次出现**: T1-CN §6.3
**被引用**: T2a ch08; T1-CN ch00

---

## 5. Kalman滤波（卡尔曼滤波）

**编号**: (T1-CN 6-3, 6-4)

**预测步**：
$$
\hat{\mathbf{x}}_{k|k-1} = \mathbf{A}_d \hat{\mathbf{x}}_{k-1|k-1} + \mathbf{B}_d \mathbf{u}_{k-1}
$$
$$
\mathbf{P}_{k|k-1} = \mathbf{A}_d \mathbf{P}_{k-1|k-1} \mathbf{A}_d^\top + \mathbf{Q} \tag{T1-CN 6-3}
$$

**更新步**：
$$
\mathbf{K}_k = \mathbf{P}_{k|k-1} \mathbf{C}^\top (\mathbf{C} \mathbf{P}_{k|k-1} \mathbf{C}^\top + \mathbf{R})^{-1}
$$
$$
\hat{\mathbf{x}}_{k|k} = \hat{\mathbf{x}}_{k|k-1} + \mathbf{K}_k (\mathbf{y}_k - \mathbf{C} \hat{\mathbf{x}}_{k|k-1})
$$
$$
\mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K}_k \mathbf{C}) \mathbf{P}_{k|k-1} \tag{T1-CN 6-4}
$$

**变量说明**：
- $\hat{\mathbf{x}}$：状态估计
- $\mathbf{P}$：估计误差协方差矩阵
- $\mathbf{K}$：Kalman增益
- $\mathbf{Q}$：过程噪声协方差
- $\mathbf{R}$：观测噪声协方差

**首次出现**: T1-CN §6.4
**被引用**: T2a ch08

---

## 6. MPC QP标准形式（模型预测控制二次规划）

**编号**: (T1-CN 4-10)

**QP问题**：
$$
\min_{\Delta \mathbf{U}} \; J = \sum_{i=1}^{N_p} \| \mathbf{y}_{k+i|k} - \mathbf{r}_{k+i} \|_{\mathbf{Q}_y}^2 + \sum_{i=0}^{N_c-1} \| \Delta \mathbf{u}_{k+i|k} \|_{\mathbf{R}_u}^2 \tag{T1-CN 4-10}
$$

**约束**：
$$
\mathbf{u}_{\min} \leq \mathbf{u}_{k+i|k} \leq \mathbf{u}_{\max}
$$
$$
\Delta \mathbf{u}_{\min} \leq \Delta \mathbf{u}_{k+i|k} \leq \Delta \mathbf{u}_{\max}
$$
$$
\mathbf{y}_{\min} \leq \mathbf{y}_{k+i|k} \leq \mathbf{y}_{\max}
$$

**变量说明**：
- $N_p$：预测时域
- $N_c$：控制时域
- $\mathbf{r}$：参考轨迹
- $\mathbf{Q}_y$：输出权重矩阵
- $\mathbf{R}_u$：控制增量权重矩阵
- $\Delta \mathbf{u}$：控制增量

**首次出现**: T1-CN §4.6
**被引用**: T2a ch07; T5

---

## 7. 安全包络三区数学定义

**编号**: (T1-CN 11-1)

$$
\begin{cases}
\text{绿区（Green Zone）:} & x \in [x_{\min}+\delta, x_{\max}-\delta] \\
\text{黄区（Yellow Zone）:} & x \in [x_{\min}, x_{\min}+\delta) \cup (x_{\max}-\delta, x_{\max}] \\
\text{红区（Red Zone）:} & x \notin [x_{\min}, x_{\max}]
\end{cases} \tag{T1-CN 11-1}
$$

**变量说明**：
- $x$：关键变量（水位/流量/压力等）
- $[x_{\min}, x_{\max}]$：设计运行范围
- $\delta$：安全裕度（通常取设计范围的5-15%）

**安全裕度确定方法**：
1. 基于扰动分析：$\delta \geq \max\{|\Delta x_{\text{disturbance}}|\}$
2. 基于历史数据：$\delta = k \cdot \sigma_x$，$k=2\sim3$
3. 基于响应时间：$\delta \geq v_{\max} \cdot T_{\text{response}}$
4. 基于传递函数：$\delta \geq v_{\max}(\tau_m + \tau_d + \tau_{exec}) + \varepsilon_{model}$

**首次出现**: T1-CN §11.1
**被引用**: T3 ch04—ch06

---

## 8. WNAL区段综合等级

**编号**: (T1-CN 10-2)

$$
\mathrm{WNAL}_{\text{seg}} = \min_{d \in \mathcal{D}} \mathrm{WNAL}_d \tag{T1-CN 10-2}
$$

**说明**：区段综合等级由最薄弱能力域决定（木桶原理）。其中 $\mathcal{D}$ 为感知、决策、执行、安全等能力域。

**首次出现**: T1-CN §10.3
**被引用**: T3 ch03

---

## 9. ODD六维空间定义

**编号**: (T1-CN 10-3)

$$
\mathbf{x}_{\mathrm{ODD}} = [H, P, D, E, C, G]^\top \tag{T1-CN 10-3}
$$

$$
X_{\mathrm{ODD}} = H \cap P \cap D \cap E \cap C \cap G \tag{T1-CN 10-4}
$$

**六维要素**：
- $H$：水文气象（Hydrological Limits）
- $P$：工程物理（Physical Infrastructure）
- $D$：数据质量（Data Quality）
- $E$：环境气象（Environmental Conditions）
- $C$：网络算力（Cyber-Infrastructure）
- $G$：治理规则（Governance & Rules）

**首次出现**: T1-CN §10.4
**被引用**: T3 ch05

---

## 10. 控制障碍函数（CBF）

**编号**: (T1-CN 11-3)

设安全集 $\mathcal{C} = \{x \in \mathbb{R}^n : h(x) \geq 0\}$，其中 $h(x)$ 为障碍函数。若存在扩展类 $\mathcal{K}$ 函数 $\alpha$ 使得：

$$
\sup_{u \in \mathcal{U}} [L_f h(x) + L_g h(x) u + \alpha(h(x))] \geq 0 \tag{T1-CN 11-3}
$$

则 $h(x)$ 为控制障碍函数，任何满足上述不等式的控制律都保证 $\mathcal{C}$ 的前向不变性（即系统不离开安全集）。

**变量说明**：
- $h(x)$：障碍函数，$h(x) \geq 0$ 定义安全集
- $L_f h$, $L_g h$：$h$ 沿 $f$, $g$ 方向的Lie导数
- $\alpha$：扩展类 $\mathcal{K}$ 函数

**首次出现**: T1-CN §11.4
**被引用**: T2a（可选，进阶内容）

---

## 11. 双引擎仲裁逻辑

**编号**: (T1-CN 14-1)

$$
\mathbf{u}_{\text{exec}} =
\begin{cases}
\mathbf{u}_{\text{agent}}, & \text{if } (\mathbf{u}_{\text{agent}} \in \mathcal{U}_{\text{safe}}) \land (\mathbf{x} \in X_{\mathrm{ODD}}) \land (r \leq r_{\max}) \\
\mathbf{u}_{\text{baseline}}, & \text{otherwise}
\end{cases} \tag{T1-CN 14-1}
$$

**说明**：HydroClaw（认知AI）提出的候选动作只有同时满足安全包络集合 $\mathcal{U}_{\text{safe}}$、ODD条件 $\mathbf{x} \in X_{\mathrm{ODD}}$、且风险评估指标 $r$ 不超过阈值时，才可执行；否则回退至HydroCore基线策略。

**变量说明**：
- $\mathbf{u}_{\text{agent}}$：认知AI提出的候选动作
- $\mathbf{u}_{\text{baseline}}$：物理AI的基线策略
- $\mathcal{U}_{\text{safe}}$：安全包络约束集
- $X_{\mathrm{ODD}}$：运行设计域
- $r$：风险评估指标

**首次出现**: T1-CN §14.3
**被引用**: T4; T5

---

## 12. 欧拉涡轮方程

**编号**: (T1-CN 9-2)

$$
P = \eta \rho g Q H \tag{T1-CN 9-2}
$$

**变量说明**：
- $P$：水轮机出力（W）
- $\eta$：水轮机效率
- $\rho$：水的密度（1000 kg/m³）
- $g$：重力加速度（9.81 m/s²）
- $Q$：过机流量（m³/s）
- $H$：净水头（m）

**首次出现**: T1-CN §9.1
**被引用**: T2a ch15

---

## 公式使用规范

1. **首次引用**: 在正文中首次引用核心公式时，标注来源 `(T1-CN X-Y)`
2. **变量一致**: 同一变量在全系列中使用相同的符号和定义
3. **编号格式**: 各卷使用自己的编号体系 `(X-Y)`，但在跨卷引用时使用统一编号 `(T1-CN X-Y)`
4. **LaTeX规范**: 行内公式用 `$ $`，行间公式用 `$$ $$`，编号用 `\tag{X-Y}`

---

*本文件为CHS书系核心公式的唯一权威来源。任何公式修改须经审核后更新本表。*
