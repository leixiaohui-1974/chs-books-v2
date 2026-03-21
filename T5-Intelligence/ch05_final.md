# 第5章 强化学习调度：从仿真到真实水网的迁移

<!-- 知识依赖框 -->

> **本章学习前需掌握：**
>
> | 前置知识 | 对应章节 | 重要程度 |
> |---------|---------|----------|
> | 马尔可夫决策过程（Markov Decision Process, MDP）基本理论 | 附录A | ★★★ |
> | HIL（Hardware-in-the-Loop）仿真框架的系统架构 | 第4章 | ★★★ |
> | HydroOS L2内核的水文-水动力耦合机制 | 第3章 | ★★☆ |
> | 模型预测控制（Model Predictive Control, MPC）基础 | 第2章 | ★★☆ |
> | Python编程与Gymnasium接口（习题部分） | 附录B | ★☆☆ |

---

## 学习目标

> 学完本章，读者应能够：
> 1. 理解强化学习在水利调度中相比传统优化方法的根本优势与适用边界
> 2. 掌握水利调度MDP的完整建模流程，包括状态空间、动作空间、奖励函数的设计原则
> 3. 能够评估和改进多目标奖励函数，平衡防洪、供水、生态、经济等目标
> 4. 理解仿真-真实系统的分布偏移（Distribution Shift）问题及其四类工程对策
> 5. 掌握约束强化学习（Constrained RL）的CMDP框架与Lagrangian对偶方法
> 6. 理解水网自主化等级（WNAL）体系与ODD监测机制，能够设计渐进式部署方案
> 7. 掌握RL策略在HydroOS中与MPC协作的双层架构设计方法

---

## 管理层速览

> **[管理层速览]**
>
> 强化学习在水利调度中的价值体现在三个层面：（1）**自适应性**——无需预先建立精确的水文模型，直接从历史数据和实时反馈中学习最优策略；（2）**非线性处理能力**——传统规则和线性规划在极端气候下失效，RL可处理复杂约束交互；（3）**多目标协调**——通过奖励函数设计，同时优化防洪、供水、发电等目标。
>
> 然而，工程应用的核心障碍不在算法性能，而在**可解释性与责任认定**。一个防洪决策必须能够事后说明为什么，否则无法通过行业审批。本章重点介绍如何在保证可解释性的前提下，设计鲁棒的RL调度系统，并通过WNAL等级体系实现从辅助决策到高度自动化的渐进式部署路径。

---

## 开篇故事

某研究团队花了两年时间，利用深度Q网络（Deep Q-Network, DQN）训练了一个多水库联合调度模型。在HydroOS的仿真环境中，该模型在1998年特大洪水场景下的防洪效益相比传统调度规则高出18%，库容利用率也提升了12%。团队兴高采烈地向某流域水利局提出在真实水库系统中进行为期三个月的试运行。

会议室里，水利局负责人问了一个简单但致命的问题：如果你的AI在某个时刻做出一个让大坝超过汛限水位的决策，导致下游城市被淹，谁来负责？

会议陷入沉默。团队负责人回答：这在我们的约束条件中是不可能的……——但如果发生了呢？——没有答案。因为RL模型本质上是一个黑盒，它能告诉你做什么，但无法清晰解释为什么。在涉及公共安全的关键基础设施中，这是不可接受的。

这个故事揭示了强化学习在水利工程中的两个核心挑战：

1. **可解释性危机**：RL策略的决策过程对人类是不透明的，难以获得工程师和管理者的信任。
2. **安全保障缺陷**：即使设置了约束条件，神经网络仍可能在分布外（Out-of-Distribution, OOD）场景中产生意外行为。

解决这两个问题，是RL从实验室走向水利工程的必经之路。本章将系统阐述这一迁移过程中的关键技术。
---

## 5.1 为什么水利调度适合强化学习 [L1/L2]

### 5.1.1 传统优化方法的根本局限

**线性规划（Linear Programming, LP）** 在水利调度中的应用可追溯到20世纪60年代。其假设前提是目标函数和约束条件均为决策变量的线性函数。然而，真实水利系统存在大量非线性特征：（1）泵站能耗与转速的三次方关系；（2）水库防洪库容随库位变化的非线性特性；（3）下游河道的水流演进方程（Saint-Venant方程）本身为非线性偏微分方程。当采用分段线性近似时，变量维度急剧增加，求解时间呈指数增长。

**动态规划（Dynamic Programming, DP）** 由Bellman（1957）提出，在水利调度中已有60年历史。其核心思想是将多阶段决策问题递归分解。但DP面临维度灾难（Curse of Dimensionality）：当状态变量数量增加时，状态空间规模呈指数增长。以三库联合调度为例，若每个水库库容离散化为100个等级，时段数为12个月，则状态空间规模达 $100^8$，计算量已接近实时决策的极限。

**专家规则系统** 依赖领域专家的经验积累，面临两个致命弱点：（1）**新场景泛化能力差**——极端气候超出历史经验范围，现有规则无法应对；（2）**多目标协调困难**——防洪、供水、发电、生态需水等目标往往相互冲突，难以用简单规则表达帕累托最优前沿（Pareto Frontier）。

### 5.1.2 强化学习的核心优势

强化学习（Reinforcement Learning, RL）提供了一条不同的道路。其核心思想是：**智能体（Agent）通过与环境交互，在试错过程中学习能最大化累积奖励的策略**。

- **非线性处理**：神经网络作为通用函数逼近器（Universal Function Approximator），可自动学习复杂的非线性映射，无需分段线性近似。
- **不确定性的隐式处理**：RL通过直接与仿真环境交互，隐式地学习对不确定性的鲁棒应对，无需显式建模概率分布。
- **多目标学习**：通过加权多目标奖励函数，RL可在单次训练中同时优化多个目标。
- **在线自适应**：随着新运行数据积累，策略可持续微调，适应系统特性的缓慢漂移（Concept Drift）。

[插图：水利调度方法演进时间轴——从1960年代LP到2020年代安全强化学习]

| **维度** | **线性规划** | **动态规划** | **专家规则** | **强化学习** |
|---------|-----------|-----------|----------|----------|
| 非线性处理 | 需近似 | 支持 | 隐式 | 自动学习 |
| 维度可扩展性 | 中等 | 维度灾难 | 高 | 可扩展 |
| 新场景泛化 | 差 | 差 | 极差 | 迁移学习 |
| 多目标协调 | 中等 | 困难 | 困难 | 单次训练 |
| 可解释性 | 极强 | 强 | 极强 | 黑盒 |
| 工程信任度 | 高 | 中等 | 中等 | 低 |

> **AI解读：** RL在水利调度中的优势不是因为更聪明，而是因为**问题结构的匹配**。水利调度天然具备高维状态空间、复杂时间依赖和多目标协调需求，这些特征与RL的数据驱动学习机制高度契合。但这种高效性的代价是黑盒性质——本章的核心任务，正是解决这一工程化障碍。
---

## 5.2 水利调度的MDP建模 [L2/L3]

### 5.2.1 MDP的形式化定义

马尔可夫决策过程（Markov Decision Process, MDP）由五元组 $\mathcal{M} = \langle \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \gamma \rangle$ 定义，其中各要素含义如下：

$$\mathcal{S}: \text{状态空间（State Space）}$$

$$\mathcal{A}: \text{动作空间（Action Space）}$$

$$\mathcal{P}(s'|s,a): \text{状态转移概率（Transition Probability）}$$

$$\mathcal{R}(s,a,s'): \text{奖励函数（Reward Function）}$$

$$\gamma \in [0,1]: \text{折扣因子（Discount Factor）}$$

马尔可夫性假设（Markov Property）要求未来状态只依赖当前状态和动作，与历史无关：

$P(s_{t+1}|s_t, a_t, s_{t-1}, a_{t-1}, \ldots) = P(s_{t+1}|s_t, a_t)$

RL的目标是找到最优策略 $\pi^*$，使期望累积折扣奖励最大化：

$$\pi^* = \arg\max_{\pi} \mathbb{E}_{\pi}\eft[\sum_{t=0}^{T} \gamma^t \mathcal{R}(s_t, a_t, s_{t+1})
\
\right]$$

[插图：水利调度MDP建模框架图——智能体-环境交互循环，状态/动作/奖励/转移四要素及水利实例标注]

### 5.2.2 状态空间设计

状态向量应满足马尔可夫性：给定当前状态，历史信息不再提供额外预测价值。水利调度的状态向量由以下四类分量构成：

**（1）水文状态**：各水库库容 $V_i(t)$（$i=1,\ldots,N_{\text{res}}$）、各断面入流 $Q_{\text{in},j}(t)$、各河道蓄水量 $S_k(t)$

**（2）气象预报状态**：未来7日降雨预报序列 $\hat{P}(t+1:t+7)$、未来14日来水预报 $\hat{Q}(t+1:t+14)$

**（3）时间与周期性特征**：为保持连续性，采用正弦/余弦编码：

$$\phi_{\text{season}}(t) = \eft[\sin!\eft(\\frac{2\pi t}{365}
\r
\right), \cos!\eft(\\frac{2\pi t}{365}
\r
\right)
\
\right]$$

以及汛期标记 $I_{\text{flood}}(t) \in \{0,1\}$

**（4）设备与约束状态**：各泵站运行状态 $\mathbf{b}_{\text{pump}}$、闸门实际开度 $\bboldsymbol{\theta}_{\text{gate}}$

完整状态向量 $s_t \in \mathbb{R}^d$（$d$ 通常为50～200）需经归一化处理：$\tilde{s}_t = (s_t - \mu_s)/(\sigma_s + \varepsilon)$，其中 $\varepsilon = 10^{-8}$ 防止除零。

### 5.2.3 动作空间设计

**离散动作空间**适用于闸门开/关、泵站启停等场景。对于单水库调度，可将出库流量离散化为 $K$ 个等级：

$$a \in \left\{0, \\frac{Q_{max}}{K-1}, \ldots, Q_{max}
\right\}$$

**连续动作空间**适用于闸门开度精细调节，动作向量经 Tanh 压缩后映射到物理范围：

$$a_i^{\text{phys}} = a_i^{min} + \\frac{1 + \tanh(\tilde{a}_i)}{2} \cdot (a_i^{max} - a_i^{min})$$

**动作平滑约束**——为防止水锤效应，在奖励函数中加入：

$$r_{\text{smooth}} = -\lambda_{\text{smooth}} \sum_{i=1}^{m} \eft(a_{i,t} - a_{i,t-1}
\r
\right)^2$$

### 5.2.4 奖励函数设计

水利调度的多目标加权奖励函数：

$$r(s_t, a_t) = w_1 r_{\text{flood}} + w_2 r_{\text{supply}} + w_3 r_{\text{eco}} + w_4 r_{\text{energy}} - w_5 r_{\text{viol}}$$

各子奖励的具体定义：

**（1）防洪奖励**——惩罚水位超限及下游超安全流量：

$$r_{\text{flood}} = -\alpha_1 \max(h_t - h_{\text{flood}}, 0)^2 - \alpha_2 \max(q_{\text{out},t} - q_{\text{safe}}, 0)^2$$

**（2）供水奖励**——以供需比衡量，惩罚供水缺口：

$$r_{\text{supply}} = \min!\eft(\\frac{Q_{\text{supply},t}}{D_{\text{demand},t}}, 1
\r
\right) - \eta \cdot \max!\eft(1 - \\frac{Q_{\text{supply},t}}{D_{\text{demand},t}}, 0
\r
\right)$$

**（3）生态奖励**——维持河道最小生态流量 $Q_{\text{eco,min}}$：

$$r_{\text{eco}} = -\gamma_e \cdot \max(Q_{\text{eco,min}} - Q_{\text{river},t}, 0)$$

**（4）能耗奖励**——结合分时电价 $p_e(t)$ 鼓励峰谷调节：

$$r_{\text{energy}} = -p_e(t) \cdot \sum_{j} P_{\text{pump},j}(a_t) \cdot \Delta t$$

**（5）约束违反惩罚**——对任何约束违反施以大惩罚（$M_i$ 典型取值500～2000）：

$$r_{\text{viol}} = \sum_{i} \mathbb{1}[c_i(s_t, a_t) > 0] \cdot M_i$$

权重设置应遵循 $w_5 \gg w_1 \geq w_2 > w_3 \geq w_4$ 的优先级原则。对于稀疏奖励问题，可引入势函数（Potential Function） $\Phi(s)$ 进行奖励塑形（Reward Shaping），不改变最优策略的前提下加速收敛（Ng et al., 1999）：

$$r'(s, a, s') = r(s, a, s') + \gamma \Phi(s') - \Phi(s)$$

### 5.2.5 环境模型构建

三种实现路径：（1）**基于物理模型的环境**——将HydroOS L2内核封装为Gymnasium接口，物理保真度高，但推理速度慢（每步约0.1～10秒）；（2）**数据驱动代理模型（Surrogate Model）**——用LSTM或图神经网络（Graph Neural Network, GNN）拟合物理模型，速度提升3～4个数量级；（3）**混合残差模型**（推荐）：

$$s_{t+1} = f_{\text{phys}}(s_t, a_t) + \Delta f_{\text{NN}}(s_t, a_t; \theta)$$

混合残差模型在保留物理一致性的同时修正参数误差，是目前工程实践中最受推荐的方案（Bai et al., 2023）。

> **AI解读：** 奖励函数设计是RL水利应用中最需要领域知识的环节。一个常见的错误是将奖励函数设计得过于简单，导致策略产生奖励黑客（Reward Hacking）行为——找到了技术上满足奖励函数但违背调度意图的捷径。建议在设计后，通过蒙特卡洛仿真验证各目标的实际满足率，而非仅看总奖励值。
---

## 5.3 主流RL算法的水利适配 [L2/L3]

### 5.3.1 PPO算法：稳定性优先的策略梯度

近端策略优化（Proximal Policy Optimization, PPO, Schulman et al., 2017）是on-policy的策略梯度算法，通过引入裁剪机制在单调性保证与计算稳定性之间取得平衡。定义重要性采样比：

$$r_t(\theta) = \\frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)}$$

PPO的裁剪目标函数：

$$L^{\text{CLIP}}(\theta) = \mathbb{E}_t\eft[\min!\eft(r_t(\theta)\hat{A}_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t
\r
\right)
\
\right]$$

广义优势估计（Generalized Advantage Estimation, GAE）用于降低方差：

$$\hat{A}_t = \sum_{l=0}^{\infty}(\gamma\lambda)^l\delta_{t+l}^V, \qquad \delta_t^V = r_t + \gamma V(s_{t+1}) - V(s_t)$$

裁剪机制确保策略更新步长受控，避免过大参数变化导致性能崩溃。水利场景推荐超参数：$\epsilon=0.2$，$\gamma=0.99$（捕捉跨季度的长期依赖），$\lambda=0.95$。

### 5.3.2 SAC算法：最大熵连续控制

SAC（Soft Actor-Critic, Haarnoja et al., 2018）融合最大熵RL与off-policy方法，目标函数在最大化奖励的同时最大化策略熵：

$$J(\pi) = \mathbb{E}_{s \sim 
\rho^{\pi}\eft[\mathbb{E}_{a \sim \pi(\cdot|s)}\eft[Q(s,a) - \alpha \log \pi(a|s)
\
\right]
\
\right]$$

评论家网络更新（使用软目标 $\phi'$ 稳定训练）：

$$L_Q(\phi) = \mathbb{E}\eft[\eft(Q_\phi(s,a) - \eft(r + \gamma\mathbb{E}_{a'}\eft[Q_{\phi'}(s',a') - \alpha \log \pi(a'|s')
\
\right]
\r
\right)
\r
\right)^2
\
\right]$$

温度参数 $\alpha$ 通过自适应调整保持目标熵：

$$L_\alpha(\alpha) = -\alpha\,\mathbb{E}_{a \sim \pi}!\eft[\log \pi(a|s) + H_0
\
\right], \qquad H_0 = -\dim(\mathcal{A})$$

SAC特别适合连续闸门开度调节，使用Tanh压缩将无界高斯输出映射到 $[0,1]$。最大熵项的存在使策略保持探索多样性，有助于发现非直觉的调度策略（如在某些场景下主动预泄以为后续洪峰腾库）。

### 5.3.3 TD3算法：低延迟确定性控制

TD3（Twin Delayed Deep Deterministic Policy Gradient, Fujimoto et al., 2018）在DDPG基础上引入双评论家、延迟策略更新和目标策略平滑三项改进，双评论家目标值计算：

$$y = r + \gamma\min_{i=1,2}Q_{\phi'_i}!\eft(s', \mu_{\theta'}(s') + \epsilon
\r
\right), \qquad \epsilon \sim \text{Clip}!\eft(\mathcal{N}(0, \sigma), -c, c
\r
\right)$$

确定性策略 $\mu_\theta(s)$ 推理计算量远低于随机策略的采样过程，适合泵站秒级响应的低延迟实时控制场景。延迟策略更新（每两步评论家更新对应一步演员更新）有效缓解了过估计偏差。

### 5.3.4 多智体强化学习（MARL）：多库联合调度

多水库联合调度需要协调多个决策主体。**中心化训练-去中心化执行（Centralized Training with Decentralized Execution, CTDE）** 范式在训练阶段使用全局状态和联合动作，全局评论家：

$$L_Q = \mathbb{E}!\eft[\eft(Q_{\text{global}}(\mathbf{s}, \mathbf{a}) - \eft(r + \gamma Q'_{\text{global}}(\mathbf{s}', \mathbf{a}')
\r
\right)
\r
\right)^2
\
\right]$$

执行阶段各智体仅依赖局部信息：$a_i = \pi_i(s_i^{\text{local}})$，无需全局通讯，适应水利现场通讯带宽受限的工程约束。**QMIX混合网络**（Rashid et al., 2018）保证个体-全局单调性（Individual-Global-Max, IGM）：

$$Q_{\text{tot}}(\mathbf{s}, \mathbf{a}) = f_{\text{mix}}!\eft(Q_1(s_1,a_1), \ldots, Q_n(s_n,a_n); \mathbf{s}
\r
\right)$$

近年来，**MAPPO（Multi-Agent PPO）** 因其稳定性和工程友好性，在水资源联合调度中获得广泛应用（Zhao et al., 2023）。

[插图：水利RL算法选择决策树——根据动作类型（连续/离散）、水库数量（单/多）、延迟需求（秒级/分钟级）依次路由至PPO/SAC/TD3/MARL]

| **算法** | **动作类型** | **样本效率** | **稳定性** | **多智体支持** | **推荐场景** |
|--------|-----------|-----------|---------|-----------|-----------:|
| PPO | 离散/连续 | 中 | 高 | 支持（MAPPO） | 小规模日调度 |
| SAC | 连续 | 高 | 高 | 困难 | 连续闸门控制 |
| TD3 | 连续 | 高 | 中 | 困难 | 低延迟实时控制 |
| MARL | 离散/连续 | 中 | 中 | 原生支持 | 多库联合调度 |

> **AI解读：** 算法选择不是非此即彼的问题。实际工程中，常见的做法是**分层架构**：上层用MARL协调各水库的目标值，下层用SAC或TD3执行单水库的精细控制。这种粗调+精调的分层策略既保留了MARL的全局协调能力，又利用了SAC/TD3的样本效率优势。
---

## 5.4 Sim-to-Real鸿沟：最核心的工程挑战 [L2/L3]

### 5.4.1 鸿沟的来源分析

仿真到真实的鸿沟（Sim-to-Real Gap）是RL工程化的核心障碍，主要来源于三个方面：

**（1）物理模型参数误差**：水动力仿真中的糙率系数（Manning公式）、渗漏系数、蒸发参数均依赖现场实测，即使经过率定，仍存在10%～30%的不确定性。在极端工况下，这种误差会导致仿真与真实系统的状态偏差累积放大。

**（2）设备非理想特性**：真实执行机构存在（a）响应延迟（闸门从接收指令到到位约5～30秒）；（b）测量噪声（水位传感器精度约 ±1～5 mm）；（c）阶段性故障（泵站维修期间的调度切换）。

**（3）极端工况覆盖不足**：历史实测数据中，百年一遇洪水样本极为稀少，导致RL策略在真实极端工况下的外推行为不可预测，构成潜在的安全风险。

### 5.4.2 解决策略一：域随机化

域随机化（Domain Randomization, DR）的核心思想是：在训练时将仿真参数从固定值替换为随机分布，使策略学会在参数不确定性下鲁棒工作。训练目标修改为：

$$
J_{\text{DR}}(\pi) = \mathbb{E}_{\xi \sim p(\xi)}\eft[\mathbb{E}_{(s,a) \sim \pi, \xi}\eft[\sum_t \gamma^t r(s_t, a_t)\
\right]\
\right]
$$

其中 $\xi \in \Xi$ 为仿真参数向量，$p(\xi)$ 为参数的随机化分布（通常取截断正态分布）。

水利参数随机化的典型范围：

| **参数** | **标称值** | **随机化范围** | **物理含义** |
|--------|---------|------------|-----------|
| 糙率系数 n | 0.025 | [0.018, 0.035] | 河床阻力 |
| 渗漏系数 k | 1.5e-6 m/s | [0.5e-6, 3.0e-6] | 坝体渗漏 |
| 闸门延迟 $\tau$ | 10 s | [5 s, 30 s] | 执行机构响应 |
| 传感器噪声 $\sigma$ | 2 mm | [1 mm, 8 mm] | 水位测量精度 |

某流域实践案例表明，引入域随机化后，RL策略从仿真迁移至真实系统的可接受运行率（连续30天无安全违规）从34%提升至71%（Chen et al., 2024）。

### 5.4.3 解决策略二：HIL在环训练

HIL在环训练（Hardware-in-the-Loop Training, HIL Training）将真实控制硬件（PLC、SCADA终端）接入训练回路，直接捕获真实硬件的延迟特性和通讯协议。推荐四阶段训练流程：

1. 在高保真软件仿真中预训练（约100万步）
2. 引入域随机化增强策略鲁棒性（约50万步）
3. 迁移至HIL仿真机继续微调（约10万步），动作指令经真实PLC执行
4. 在严格监督下进行受限真实系统试运行（约1万步）

### 5.4.4 解决策略三：物理约束正则化与保守策略

**物理约束正则化（Physics-Constrained Regularization）** 在奖励函数中对物理约束违反施以大惩罚（典型取值500～1000）：

$$
r(s,a) = r_{\text{base}}(s,a) - \beta \cdot \phi_{\text{phys}}(s,a), \qquad \beta \gg 1
$$

**保守Q学习（Conservative Q-Learning, CQL, Kumar et al., 2020）** 通过在值函数更新中加入正则化，抑制策略在数据稀疏区域的Q值高估：

$$
L_{\text{CQL}}(Q) = L_{\text{Bellman}}(Q) + \alpha \eft(\mathbb{E}_{s \sim \mathcal{D}, a \sim \pi}[Q(s,a)] - \mathbb{E}_{s,a \sim \mathcal{D}}[Q(s,a)]\r
\right)
$$

[插图：Sim-to-Real鸿沟示意图——左侧仿真状态分布，右侧真实系统分布，中间鸿沟区域，四种桥接策略以箭头标注]

> **AI解读：** Sim-to-Real不是一个可以彻底解决的问题，而是一个需要持续管理的工程过程。域随机化、HIL训练、保守策略三者互补，建议按四阶段流程推进，每个阶段设定明确的验收指标，未达标不得进入下一阶段。
---

## 5.5 安全约束与ODD集成 [L2/L3]

### 5.5.1 约束强化学习的CMDP框架

约束马尔可夫决策过程（Constrained Markov Decision Process, CMDP）通过显式编码约束条件，从理论上保证策略的安全性。CMDP定义为六元组，其中约束函数向量 $\mathbf{c}(s,a) = [c_1(s,a), \ldots, c_m(s,a)]^T$，$\mathbf{c}(s,a) leq \mathbf{0}$ 表示所有约束均被满足。可行策略集合：

$$
\Pi_{\text{safe}} = \left\{\pi : J_{C_i}(\pi) \leq d_i,\ \forall i\right\}
$$

其中 $J_{C_i}(\pi) = \mathbb{E}\eft[\sum_t \gamma^t c_i(s_t, a_t)
\right]$ 为约束期望累积成本，$d_i$ 为允许阈值。

**Lagrangian松弛方法的推导：** 引入非负Lagrange乘数 $\bboldsymbol{\lambda} \geq \mathbf{0}$，构造Lagrangian函数：

\mathcal{L}(\pi, \bboldsymbol{\lambda}) = J_R(\pi) - \sum_{i=1}^{m} \lambda_i \eft(J_{C_i}(\pi) - d_i\r
\right)
\mathcal{L}(\pi, \bboldsymbol{\lambda}) = J_R(\pi) - \sum_{i=1}^{m} \lambda_i \eft(J_{C_i}(\pi) - d_i\r
\right)
$$

定义**增广奖励函数**（Augmented Reward Function）：

$$
\tilde{R}(s,a; \bboldsymbol{\lambda}) = R(s,a) - \sum_{i=1}^{m} \lambda_i c_i(s,a)
$$

最优策略满足鞍点条件：

$$
\pi^* = \arg\max_{\pi} \min_{\bboldsymbol{\lambda} \geq \mathbf{0}} \mathcal{L}(\pi, \bboldsymbol{\lambda})
$$

在线训练中，Lagrange乘数通过梯度上升更新：

\lambda_i^{(k+1)} = \eft[\lambda_i^{(k)} + \alpha_\lambda \eft(\hat{J}_{C_i}(\pi^{(k)}) - d_i\r
\right)\
\right]_+
\lambda_i^{(k+1)} = \eft[\lambda_i^{(k)} + \alpha_\lambda \eft(\hat{J}_{C_i}(\pi^{(k)}) - d_i\r
\right)\
\right]_+
$$

水网约束的典型编码形式：

- 水位越限：$c_1(s,a) = \max(h - h_{\max}, 0) + \max(h_{\min} - h, 0)$
- 流量安全：$c_2(s,a) = \max(q - q_{\max}, 0)$
- 泵站额定功率：$c_3(s,a) = \max(P(a) - P_{\text{rated}}, 0)$
- 供水可靠性（需求不满足度）：$c_4(s,a) = \max(D_{\text{demand}} - Q_{\text{supply}}, 0)$

> **AI解读：** Lagrangian对偶的核心创新在于将硬约束转化为自适应惩罚项。当某约束被频繁违反时，对应的 $\lambda_i$ 自动增大，使策略学会提前预防（如提前泄洪为洪峰腾库）。这与水利调度的实际操作逻辑高度一致。

### 5.5.2 WNAL等级与RL控制权限

水网自主化等级（Water Network Autonomy Level, WNAL）体系参考自动驾驶SAE等级框架：

| WNAL等级 | 名称 | RL角色 | 执行方式 | 适用场景 |
|---------|------|--------|--------|--------|
| L0 | 无自动化 | 无 | 全人工操作 | 传统手工调度 |
| L1 | 决策辅助 | 建议生成 | 人工审批后执行 | 中小型水网 |
| L2 | 条件自动化 | 条件执行 | 正常工况自动，异常人工接管 | 大型水网常规工况 |
| L3 | 高度自动化 | 自主决策 | 自动执行，异常自动降级 | 特大型水网全工况 |

综合自主化指标：

$$
\text{WNAL Score} = 0.35 \cdot M_{\text{infra}} + 0.40 \cdot T_{\text{algo}} + 0.25 \cdot C_{\text{ops}}
$$

其中 $M_{\text{infra}}$（基础设施成熟度）、$T_{\text{algo}}$（算法可信度）、$C_{\text{ops}}$（运维能力）分别由传感器覆盖率、历史约束违反率、人员培训覆盖率等子指标综合计算。等级划分阈值：L1为0.30～0.50，L2为0.50～0.70，L3为0.70～0.85。

[插图：WNAL等级与RL控制权限矩阵——纵轴为WNAL等级L0-L3，横轴为工况类型（正常/异常/极端），格中以颜色编码标注控制权限]

### 5.5.3 ODD监测与自动降级

操作设计域（Operational Design Domain, ODD）定义了RL策略可安全运行的状态空间边界。ODD的关键监测指标包括三类：

**（1）状态异常度**（变分自编码器 VAE 重构误差）：

$$
d_{\text{ODD}}(s_t) = \|s_t - \text{VAE}(s_t)\|_2
$$

**（2）预测不确定性**（集成网络方差）：

$$
\sigma_{\text{ens}}^2(s,a) = \text{Var}\!\eft[\{Q_\theta^{(i)}(s,a)\}_{i=1}^K\
\right]
$$

**（3）约束裕量**：$\delta_{\text{margin}} = \min_i (d_i - J_{C_i}(\pi, s_t)) / d_i$

降级决策逻辑采用三级阈值机制：

$$
\text{Control Mode} = \b\begin{cases} \text{RL Full Control} & d_{\text{ODD}} \leq \theta_1 \text{ and } \delta_{\text{margin}} \geq \delta_{\text{safe}} \\ \text{RL + Human Supervision} & \theta_1 < d_{\text{ODD}} \leq \theta_2 \\ \text{Rule Engine Fallback} & d_{\text{ODD}} > \theta_2 \text{ or } \delta_{\text{margin}} < 0 \end{cases}
$$

降级切换必须是无扰切换，防止水锤效应。所有切换事件需完整记录，作为后续模型改进的数据来源。

> **AI解读：** ODD监测本质上是对RL策略不知道自己不知道（Unknown Unknowns）问题的工程化应对。VAE重构误差和集成网络不确定性从不同角度度量策略的认知可信度，两者结合提供了更鲁棒的监测能力，是RL系统安全部署的工程基石。
---

## 5.6 在HydroOS中的部署 [L2]

### 5.6.1 RL策略作为L3层Skill

在HydroOS架构中，RL策略以Skill形式注册于L3层（目标决策层）。Skill接口规范定义三个核心方法：

```python
class RLDispatchSkill:
    """HydroOS L3层强化学习调度Skill接口。"""

    def observe(self, state: HydroState) -> None:
        """接收当前水网状态，更新策略网络的内部观测缓存。"""
        ...

    def act(self, horizon: int = 3600) -> DispatchTarget:
        """
        推理一步，返回目标设定值向量。

        Args:
            horizon: 决策步长（秒），默认1小时
        Returns:
            DispatchTarget: 含各水库目标库容、各泵站目标出力、各闸门目标开度
        """
        ...

    def confidence(self) -> float:
        """返回当前决策置信度 [0, 1]，供ODD监测模块使用。"""
        ...
```

`act()` 方法返回的 `DispatchTarget` 为目标值向量，包含各水库的目标库容、各泵站的目标出力、各闸门的目标开度。Skill需通过覆盖率测试、极端场景回归、安全约束验证三类认证测试后，方可上线至生产环境。

### 5.6.2 与L2层MPC的协作架构

RL（L3层）与MPC（L2层）形成双层控制架构，实现战略决策与精确执行的职责分离：

- **L3层（RL）**：以小时为决策步长，输出目标设定值（Target Setpoint） $\mathbf{y}^*$
- **L2层（MPC）**：以分钟为控制步长，在约束集合内求解实现目标设定值的精确控制指令

L2层MPC的滚动优化问题（预测步长 $H$）：

$$
\min_{\mathbf{u}_{0:H}} \sum_{k=0}^{H} \eft(\|\mathbf{y}_{t+k} - \mathbf{y}^*\|_Q^2 + \|\mathbf{u}_k - \mathbf{u}_{k-1}\|_R^2\r
\right)
$$

$$
\text{s.t.} \quad \mathbf{x}_{k+1} = f(\mathbf{x}_k, \mathbf{u}_k), \quad \mathbf{u}_k \in \mathcal{U}, \quad \mathbf{x}_k \in \mathcal{X}
$$

其中 $ 为跟踪误差权重矩阵，$ 为控制平滑权重矩阵，$\mathcal{U}$、$\mathcal{X}$ 分别为控制约束集和状态约束集。即使RL给出的目标设定值略有偏差，MPC的显式约束处理也能作为最后一道安全防线，确保实际执行指令满足物理约束。

[插图：HydroOS中RL策略部署架构图——L3 RL Skill输出Target Setpoint，经L2 MPC优化层到达执行机构（闸门/泵站），ODD监测模块横跨各层并连接降级开关]

### 5.6.3 在线微调与离线重训的决策逻辑

| **触发条件** | **判断标准** | **建议方案** | **说明** |
|-----------|-----------|-----------|--------|
| 日常运行数据积累 | 分布偏移 < 20% | 在线微调 | 小批量梯度更新，保持策略连续性 |
| 设备更换或参数重新标定 | 分布偏移 20%～50% | 离线增量重训 | 以新数据 fine-tune 已有策略权重 |
| 水系结构变化（新建水库等） | 分布偏移 > 50% | 完整离线重训 | 从预训练权重重新训练，通过完整验证流程 |
| 重大安全事件 | 任意约束违反导致实际损失 | 立即离线重训+回归测试 | 不得在线微调，需完整验证流程后重新上线 |

分布偏移程度可通过滑动窗口计算在线数据与训练数据的KL散度进行量化监测：$\text{KL}(p_{\text{train}} \| p_{\text{online}}) > \theta_{\text{drift}}$ 时触发对应方案。

> **AI解读：** RL+MPC的分层架构是目前工业控制中最受认可的落地路径。RL擅长在复杂不确定环境中做出自适应决策，但难以精确满足约束；MPC在已知模型下可精确处理约束，但对模型依赖强。分层架构让两者各司其职，扬长避短——这不仅是技术上的最优选择，也是工程实践中获得监管机构信任的有效路径。
---


## 5.7 典型案例：某流域水网RL调度系统工程实践 [L2/L3]

### 5.7.1 系统概况与工程挑战

某大型流域水网位于华东地区，是典型的复杂多目标水利系统。该流域集水面积28000 km²，多年平均降雨量1200 mm，汛期（5-9月）降雨量占年均的65%。水网由3座大型水库（总库容150亿m³）、12座中小型水库、47个泵站、89组水闸及其互联的渠道网络组成，服务于500万城市人口供水、300万亩农业灌溉、工业用水及生态流量维护。

系统面临的主要工程挑战包括：（1）**拓扑复杂性**——支流汇流时滞差异显著（上游干流时滞6-8小时，支流时滞1-3小时），传统集中式调度难以协调；（2）**极端气候频发**——近十年极端降雨事件增加33%（Duan et al., 2022），传统规则表难以覆盖；（3）**多目标冲突**——防洪、供水、灌溉、生态目标存在本质矛盾，历史规则调度在汛限水位与供水保证率间的权衡效率仅为62%；（4）**决策时滞**——传统人工决策周期45分钟，极端洪水难以快速响应。

在2021-2022年连续两个特大洪水年，传统规则调度分别导致下游堤防超设防高度0.38 m和0.42 m，险些引发决堤。这一现实困境驱动了该系统的RL调度系统工程化实践。

[插图：某流域水网拓扑示意图，包含3座大型水库、支流汇流节点、关键控制断面位置标注]

### 5.7.2 系统辨识与仿真环境构建

**参数辨识**采用**贝叶斯优化（Bayesian Optimization）**框架，以高斯过程（Gaussian Process）作为代理模型加速参数搜索。需标定的关键参数包括：各水库Manning糙率、堤防渗透系数、河道糙率分段参数（共20+个）、泵站效率曲线、水闸流量系数等。标定数据集为2019-2020年连续水文年观测记录（含1场50年一遇洪水过程），标定集与验证集各12个月。

初始均匀网格搜索的基准精度为RMSE = 0.18 m；贝叶斯优化经过85次高保真仿真迭代后，RMSE降至**0.06 m，辨识精度提升67%**。在独立的2021年洪水验证集上，关键控制断面水位预报误差保持在 ±0.08 m 以内，满足调度规范要求（±0.15 m）。

**仿真环境**基于Gymnasium标准接口开发，主要技术指标：

- **仿真步长**：15分钟（与实际调度决策周期一致）
- **代理模型加速**：高斯过程代理模型替代全量水动力模型，单步推理时间 < 50 ms（相比全量MIKE HYDRO模型的3-5分钟，加速约100倍）
- **域随机化**：随机扰动Manning糙率（±8%）、泵站效率（±5%）、水闸系数（±3%），覆盖实际参数漂移范围
- **观测维度**：90维，涵盖各水库库容（3维）、入流量（3维）、12小时降雨预报（4维）、各控制断面水位（8维）、泵站运行状态（47维）、水闸开度（89维，降维后）、时间周期编码（8维，正弦/余弦）

### 5.7.3 RL模型训练与验证

**算法选择**为PPO（Proximal Policy Optimization），主要考量：（1）PPO单调改进保证使训练过程可审计，便于通过WNAL认证；（2）对超参数不敏感，工程鲁棒性强；（3）on-policy特性便于与CMDP约束的Lagrangian更新联合实现。

**安全约束**采用CMDP框架，定义5类约束：

1. 库容约束：$h_i^{\min} \leq h_i(t) \leq h_i^{\max}$，防止淹没和死库容
2. 最大下泄流量：$q_i(t) \leq q_i^{\max}$，保护下游堤防安全
3. 最小生态流量：$q_{\text{eco}}(t) \geq q_{\text{eco}}^{\min}$，维持河道生态
4. 泵站额定功率：$P_i(t) \leq P_i^{\text{rated}}$，保护设备安全
5. 汛期汛限水位：汛期（5-9月）$h_i(t) \leq h_i^{\text{flood}}$

Lagrangian增广奖励（参见5.5.1节推导）：$	ilde{R}(s,a;boldsymbol{\lambda}) = R(s,a) - \sum_{k=1}^{5} \lambda_k c_k(s,a)$。乘数更新轨迹：训练前200万步 $\lambda_k$ 快速上升，700万步后稳定收敛于区间 $[0.3, 1.8]$。

**训练规模**：1000万步，8×NVIDIA A100 GPU并行，历时约3个月；策略与价值网络均为3层MLP（256-256-128），超参数 $\gamma=0.99$，$\epsilon=0.2$，GAE $\lambda=0.95$。

**仿真验证结果**（1000个历史场景，覆盖干旱年、平水年、洪水年）：

| 指标 | 传统规则调度 | RL策略 | 提升幅度 |
|------|------------|--------|---------|
| 防洪约束违反率 | 2.1% | 0.3% | ↓85.7% |
| 年均供水保证率 | 79% | 92% | ↑16.5% |
| 泵站综合电耗 | 基准值 | -8% | ↓8% |
| 极端洪水响应时间 | 45 min | 8 s | ↓99.7% |
| 灌溉供水可靠度 | 73% | 87% | ↑19.2% |

极端洪水响应时间的改善最为显著：RL策略在观测到入流异常的同一决策步内即调整动作，完全消除了人工决策周期带来的45分钟时滞。

### 5.7.4 渐进式部署与迁移验证

遵循WNAL认证框架，系统采用**V-Model四阶段渐进部署**，总耗时约12个月：

**阶段一：影子模式（Shadow Mode）**，历时2个月。RL策略与传统规则调度并行运行，仅记录RL决策不执行，所有指令仍由规则系统下达。离线评估共发现3处边界情况（极端降雨、库容满溢、多支流同时洪峰），完成策略修正后进入下一阶段。

**阶段二：受监督自动模式**，历时4个月。RL策略开始执行部分控制量（初期仅控制低风险泵站出力），人工监察员7×24小时在线，全程保持随时接管能力。本阶段共发生2次预警性干预，均为主动安全操作而非紧急接管。

**阶段三：WNAL L2自动模式**，历时4个月。RL策略全面接管所有控制量，当库水位距汛限不足0.5 m时自动降级为规则引擎，本阶段运行平稳，零人工干预。

**阶段四：WNAL L3高度自动模式**，当前运行阶段。全工况RL自主运行，规则引擎作为热备份，严格定义的自动降级触发条件（连续3步违反率 > 1.5%，或单步防洪水位超限 $h > h^{\text{flood}} + 0.1$ m）确保任何异常均能在一个决策周期内完成回滚。

[插图：V-Model四阶段部署时间线及各阶段关键指标（约束违反率、人工干预次数、WNAL等级）变化曲线]

**Sim-to-Real迁移性能**：从仿真环境的约束违反率0.3%，上升至真实系统初始运行的0.45%，**迁移损失15%**。主要违反类型为最小生态流量约束（占67%），归因于实际泵站约2分钟的响应时滞未被代理模型完全捕捉。

**在线微调**采用学习率衰减与KL散度双重约束：

$$lpha_t = \frac{lpha_0}{\sqrt{t}} = \frac{3 	imes 10^{-4}}{\sqrt{t}}$$

$$D_{\text{KL}}(P_t \| P_0) = \sum_{s,a} P_t(s,a) \log \frac{P_t(s,a)}{P_0(s,a)} < 0.1 \quad \text{（上限约束）}$$

经过500步在线fine-tuning，约束违反率降至0.38%，接近仿真水平。运行6个月内共触发1次自动降级（上游雨量传感器故障，持续30分钟），故障排除后系统自动恢复RL模式。

### 5.7.5 运行效果与经验总结

**12个月运行统计**（与历史同期2019-2022年均值对比）：

| 指标 | 历史均值 | RL运行期 | 改善幅度 |
|------|---------|---------|---------|
| 防洪人工干预次数 | 7.0次/年 | 0次 | 彻底消除 |
| 年供水保证率 | 79.2% | 92.7% | +13.5% |
| 年节电量 | 基准值 | -1200万kWh | -8.3% |
| 灌溉满足率 | 71.5% | 86.8% | +21.3% |
| 生态流量达标率 | 68% | 94% | +38% |

2023年一次50年一遇洪水过程中，RL策略通过提前6小时预泄释放库容，成功规避汛限水位超限，而传统规则调度在历史同类事件中均发生超限。

**四条核心经验：**

1. **系统辨识质量决定Sim-to-Real成败**：本案例在贝叶斯优化辨识上投入约200工时，将RMSE压缩至<0.1 m，直接导致了仅15%的迁移损失。业界因辨识精度不足（RMSE > 0.3 m）导致迁移损失达40-50%的案例屡见不鲜。建议优先投入系统辨识，不以上线速度换取辨识质量，且验证集必须覆盖极端场景。

2. **渐进部署不可跳步**：四阶段共12个月的部署周期为监管审批提供了可信的证据链。若直接申请L3自动模式，即使仿真验证数据完美，监管机构也无法获得充分信心。建议与监管部门提前沟通各阶段验收指标，以数据驱动审批流程。

3. **在线微调需严格风险管控**：KL散度上限约束防止策略向特定工况过度拟合；衰减学习率使在线学习逐步稳定；定期与仿真环境对标检测策略漂移。在任何情况下均保留快速回滚能力。

4. **备份规则引擎的质量同等重要**：降级至规则引擎时，系统安全性完全依赖规则引擎的质量。本案例的规则引擎经历20年迭代优化，为RL部署提供了坚实的安全底线。建议在部署RL前确保规则引擎已达生产级质量，并持续维护，不因有RL接管而放松对规则引擎的投入。

> **AI解读：** 本案例展现了RL技术从学术研究到关键基础设施工程实践的完整范式转移。其核心启示在于：（1）**可控性优先于最优性**——选择PPO而非理论性能更优的算法，根本原因在于单调改进保证的可审计性，这对零容错的防洪场景价值远超0.X%的性能差距；（2）**迁移损失是可被工程化管理的**——15%的迁移损失不是算法缺陷，而是需要用在线微调、KL散度监控、渐进部署三重机制协同管控的工程问题；（3）**行业标准（WNAL）加速了技术落地**——标准化的自动化等级定义，使得监管审批有据可依，避免了监管机构面对新技术时的"无法可依"困境；（4）**RL的最终价值在于消除人工决策时滞**——从45分钟到8秒的响应时间改善，在极端洪水场景下意味着生命与财产安全的本质差异，这是传统优化方法无法实现的根本性跨越。
---

## 本章小结

本章系统梳理了强化学习在水利调度中从建模到工程部署的完整技术链条。核心知识点总结如下：

1. **方法论定位**：RL在水利调度中的优势源于问题结构的匹配（高维非线性、多目标、长时序依赖），可解释性与安全保障是工程化的主要障碍。

2. **MDP建模规范**：状态空间需兼顾马尔可夫性与信息完整性；奖励函数需遵循优先级权重设置原则（约束违反惩罚 >> 防洪 >= 供水 > 生态 >= 能耗）；环境模型建议采用物理+神经网络的混合残差架构。

3. **算法选择原则**：PPO适合稳定性优先场景，SAC适合连续闸门控制，TD3适合低延迟需求，MARL+CTDE是多水库联合调度的自然选择；分层架构（MARL粗调+SAC/TD3精调）是工程实践的主流范式。

4. **Sim-to-Real管理**：域随机化扩展鲁棒包络，HIL训练捕获设备特性，保守Q学习抑制外推风险；三者互补，应按四阶段流程推进，每阶段设定明确验收指标。

5. **CMDP安全框架**：Lagrangian方法将硬约束转化为自适应惩罚项，通过乘数在线更新实现约束的动态满足，是RL工程部署的必要安全组件。

6. **WNAL渐进部署**：WNAL等级体系提供了从L1辅助决策到L3高度自动化的可审计升级路径，ODD监测与三级降级机制构成运行时安全保障。

7. **HydroOS集成**：RL以L3层Skill形式提供目标设定值，MPC在L2层执行精确约束满足控制，双层架构实现了战略自适应与精确执行的有效分工。

[插图：本章知识图谱——以安全部署为核心节点，向外辐射MDP建模、算法选择、Sim-to-Real、CMDP约束、WNAL体系、HydroOS集成六个分支，分支间互联标注依赖关系]

---

## 习题

### 基础题

**1. [L1]** 请列举动态规划在水利调度中面临维度灾难的三个具体表现，并说明RL是如何在原理上避免这一问题的。（提示：从状态离散化、多水库扩展、实时计算三个角度展开）

**2. [L2]** 某水利调度MDP的奖励函数设计为 r(s,a) = w1*r_flood + w2*r_supply - w3*r_energy - w4*r_viol。试分析当 w4 设置过小时可能导致的策略行为，并提出至少两种改进方案，说明各方案的优缺点。

**3. [L2]** 解释PPO中裁剪参数 epsilon 的物理意义。若将 epsilon 从0.2调大到0.5，在水利调度训练中可能产生什么影响？请从策略稳定性、收敛速度、安全约束满足率三个维度分析。

### 进阶题

**4. [L3]** 编程实现一个简化的单水库日调度PPO训练环境：状态为（库容, 入流预报, 日序号正弦/余弦编码），动作为出库流量，奖励为供水可靠性与防洪安全的加权和。要求：使用Python + Gymnasium接口，实现1000个episode的训练，绘制学习曲线，并统计约束违反率随训练步数的变化趋势。

**5. [L3]** 基于第4题的环境，实现CMDP + Lagrangian方法，添加水位不得超过汛限水位的硬约束。对比有约束与无约束训练的策略行为差异，分析Lagrange乘数 lambda 的收敛轨迹，并讨论乘数学习率对约束满足率与奖励性能的权衡影响。

### 思考题

**6. [开放性]** 开篇故事中，水利局负责人提问：如果AI做出错误决策，谁来负责？请从以下三个维度分析这个问题：（a）**法律责任**：在现行水利调度法规框架下，AI辅助决策与AI自主决策的责任主体如何界定？（b）**工程伦理**：强化学习策略的黑盒性是否构成不可接受的伦理风险？技术可解释性的哪些进展可能改变这一判断？（c）**实践建议**：综合WNAL体系的设计，你认为在现有技术条件下，特大型流域（如长江干流）的RL调度系统最高可以合理达到哪个WNAL等级？给出支撑你判断的技术、法规和社会因素。

---

## 参考文献

Bellman, R. (1957). *Dynamic programming*. Princeton University Press.

Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O. (2017). Proximal policy optimization algorithms. *arXiv preprint arXiv:1707.06347*.

Haarnoja, T., Zhou, A., Abbeel, P., & Levine, S. (2018). Soft actor-critic: Off-policy maximum entropy deep reinforcement learning with a stochastic actor. In *Proceedings of the 35th International Conference on Machine Learning* (pp. 1861–1870). PMLR.

Fujimoto, S., van Hoof, H., & Meger, D. (2018). Addressing function approximation error in actor-critic methods. In *Proceedings of the 35th International Conference on Machine Learning* (pp. 1587–1596). PMLR.

Rashid, T., Samvelyan, M., de Witt, C. S., Farquhar, G., Foerster, J., & Whiteson, S. (2018). QMIX: Monotonic value function factorisation for deep multi-agent reinforcement learning. In *Proceedings of the 35th International Conference on Machine Learning* (pp. 4295–4304). PMLR.

Kumar, A., Zhou, A., Tucker, G., & Levine, S. (2020). Conservative Q-learning for offline reinforcement learning. In *Advances in Neural Information Processing Systems*, *33*, 1179–1191.

Ng, A. Y., Harada, D., & Russell, S. (1999). Policy invariance under reward transformations: Theory and application to reward shaping. In *Proceedings of the 16th International Conference on Machine Learning* (pp. 278–287).

Tobin, J., Fong, R., Ray, A., Schneider, J., Zaremba, W., & Abbeel, P. (2017). Domain randomization for transferring deep neural networks from simulation to the real world. In *2017 IEEE/RSJ International Conference on Intelligent Robots and Systems* (pp. 23–30). IEEE.

Altman, E. (1999). *Constrained Markov decision processes*. CRC Press.

Ray, A., Achiam, J., & Amodei, D. (2019). Benchmarking safe exploration in deep reinforcement learning. *arXiv preprint arXiv:1910.01708*.

Zhao, T., Liao, W., & Liu, Y. (2023). Multi-agent reinforcement learning for cooperative reservoir operation in a large-scale river basin. *Water Resources Research*, *59*(4), e2022WR032847.

Zhu, M., Wang, Y., Jiang, Y., & He, X. (2022). Reinforcement learning for multi-objective reservoir operation under climate uncertainty: A Pareto-frontier approach. *Journal of Hydrology*, *612*, 128196.

Bai, T., Zhang, H., Chen, X., & Liu, P. (2023). A hybrid physics-informed machine learning framework for reservoir inflow forecasting and adaptive dispatch. *Water Resources Management*, *37*(8), 3012–3031.

Chen, L., Wu, J., Zheng, S., & Liu, D. (2024). Closing the sim-to-real gap for hydraulic gate control via domain randomization and hardware-in-the-loop fine-tuning. *Journal of Water Resources Planning and Management*, *150*(2), 04023085.

Liu, W., He, Z., & Wang, H. (2022). Safe reinforcement learning for real-time flood control with constrained Markov decision processes. *Advances in Water Resources*, *168*, 104301.

Nian, R., Liu, J., & Huang, B. (2020). A review on reinforcement learning: Introduction and applications in industrial process control. *Computers & Chemical Engineering*, *139*, 106886.

Wang, C., Duan, Q., Tong, C., Di, Z., & Gong, W. (2022). A review on deep reinforcement learning for water management in reservoir and irrigation district systems. *Journal of Water Resources Planning and Management*, *148*(11), 03122005.

Zhang, Y., Zhao, T., He, Y., & Liao, W. (2023). Constrained deep reinforcement learning for real-time multi-objective cascade reservoir operation. *Environmental Modelling & Software*, *167*, 105782.

Loucks, D. P., van Beek, E., Stedinger, J. R., Dijkman, J. P. M., & Villars, M. T. (2005). *Water resources systems planning and management: An introduction to methods, models and applications*. UNESCO Publishing.

Xu, W., Niu, W., Feng, Z., Liao, S., & Liu, Y. (2024). Hierarchical reinforcement learning framework for hydropower scheduling: Integrating multi-agent coordination and model predictive control. *Applied Energy*, *357*, 122498.