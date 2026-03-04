<!-- 变更日志
v4 2026-03-03: T2a/T2b分工红线合规——§4.3 Saint-Venant PINN开头增加T2a第二章交叉引用边界声明
v3 2026-03-02: P0修复——15条未引用参考文献全部在正文自然引用(LeCun/Shen/He&Baxter/Brunton/Goodfellow/Litrico/Cai/Mao/Sun/Raissi2020/Chen/Kissas/McClenny/Cuomo/Yang各补1处)
v2 2026-03-02: 从骨架版(5.5k字)全面扩写至~3万字；新增PINN理论基础(§4.2)、自动微分(§4.2.3)、Saint-Venant PINN(§4.3)、正/反问题详解(§4.4)、训练策略(§4.5)、与传统方法对比(§4.6)、工程门禁(§4.7)、4例题、15习题、25篇参考文献
v1 2026-02-16: 初稿（骨架版）
-->

# 第四章 物理信息神经网络（PINN）

---

## 学习目标

完成本章后，你应能够：

1. 解释 PINN 将偏微分方程约束注入神经网络训练的基本思想，理解其与纯数据驱动模型的本质区别；
2. 构建面向水动力学场景的 PINN 损失函数，包括数据项、物理残差项、边界条件项和初值条件项；
3. 运用自动微分技术计算 PDE 残差，掌握配置点采样策略；
4. 区分正问题（状态预测）与反问题（参数反演）两类任务，设计相应的 PINN 求解流程；
5. 识别 PINN 训练中的收敛困难，运用损失权重自适应、课程学习和分域训练等策略改善训练；
6. 设计 PINN 模型接入 ODD、Safety Envelope 与在环验证的工程部署门禁流程。

---

> **章首衔接（承接 ch03）**
> 上一章介绍了深度学习模型在时空建模中的应用——CNN/LSTM/Transformer 从数据中自动学习时空特征，但不保证预测结果服从物理定律。在水系统中，这可能导致严重后果：预测出负流量、违反质量守恒、或在极端工况下产生物理上不可能的水位。本章引入物理信息神经网络（PINN），将物理方程显式纳入训练目标，解决"数据驱动精度高但物理一致性不足"的问题。PINN 是 CHS 混合驱动范式（Lei 2025a）的技术实现之一——用机理方程约束数据学习，实现物理AI与认知AI的深度融合。

---

> **本章阅读指引**
>
> **适合读者**：有偏微分方程和深度学习基础的读者。对 PDE 不熟悉的读者建议先阅读 T2a 第二章（Saint-Venant 方程推导）。
>
> **核心概念**（8个）：物理信息神经网络（PINN）、物理残差损失、自动微分、配置点采样、正问题、反问题、课程学习、损失权重自适应。

---

## 4.1 PINN 的核心思想与动机

### 4.1.1 纯数据驱动模型的物理一致性问题

ch03 介绍的深度学习模型（LSTM/Transformer/GNN，参见 LeCun et al., 2015 的综述）本质上是从数据中学习输入-输出映射 $f: \mathbf{x} \to y$，不对输出施加物理约束。Shen（2018）系统梳理了深度学习在水资源科学中的应用潜力与局限性，指出物理一致性是关键短板。这在水系统中带来三个风险：

**（1）违反守恒律**。纯数据模型可能预测出上游流量大于下游流量但渠段内无蓄水变化的结果——违反质量守恒 $\partial A/\partial t + \partial Q/\partial x = q_l$。这种预测在正常工况下可能不明显（训练数据隐含了守恒关系），但在极端或罕见工况下易暴露。

**（2）非物理外推**。深度学习模型在训练数据覆盖范围外的预测没有物理约束。例如，模型可能预测出负水深、超音速水流、或者不符合 Manning 方程的流速-水深关系。

**（3）数据稀缺时过拟合**。水系统的极端工况数据天然稀缺。纯数据驱动模型在少量极端样本上容易过拟合噪声，而非学到真实的物理规律。

### 4.1.2 PINN 的基本思想

用神经网络求解偏微分方程的思想可追溯至早期探索（Lagaris et al., 1998），但真正具备工程可行性的突破是物理信息神经网络（Raissi et al., 2019），其核心思想极其简洁：**将物理方程的残差作为正则化项加入神经网络的损失函数**。

设物理系统的控制方程为 $\mathcal{N}[u; \lambda] = 0$（其中 $\mathcal{N}$ 是微分算子，$u$ 是状态变量，$\lambda$ 是物理参数），神经网络 $\hat{u}(\mathbf{x}, t; \theta)$ 逼近 $u$，则 PINN 不仅要求 $\hat{u}$ 拟合观测数据，还要求在整个定义域内满足：

$$
\mathcal{N}[\hat{u}; \lambda] \approx 0 \tag{4-1}
$$

这使得神经网络在数据稀疏的区域仍被物理方程"引导"到合理的解空间中。

### 4.1.3 PINN 在 CHS 框架中的定位

在 CHS 混合驱动范式中，PINN 是 **物理AI引擎与认知AI引擎的融合点**：

- **物理AI提供方程约束**：Saint-Venant 方程、管网水力方程、水质方程等（T2a 全书内容）为 PINN 提供物理残差项
- **认知AI提供学习能力**：神经网络从观测数据中学习方程参数的空间变异性、未建模动态等
- **融合产物**：一个既拟合数据又服从物理定律的混合模型

与 ch02-ch03 的纯数据驱动模型相比，PINN 在数据稀缺场景（如新建工程、极端工况、传感器失效）中具有显著优势（Brunton & Kutz, 2019 第12章对此有系统论述）。Karniadakis et al.（2021）在综述中系统阐述了物理信息机器学习的理论基础和应用前景。

---

## 4.2 PINN 理论基础

### 4.2.1 通用框架

考虑一般的偏微分方程初边值问题：

$$
\begin{cases}
\mathcal{N}[u(\mathbf{x}, t); \lambda] = 0, & (\mathbf{x}, t) \in \Omega \times [0, T] \\
\mathcal{B}[u(\mathbf{x}, t)] = g(\mathbf{x}, t), & (\mathbf{x}, t) \in \partial\Omega \times [0, T] \\
u(\mathbf{x}, 0) = u_0(\mathbf{x}), & \mathbf{x} \in \Omega
\end{cases} \tag{4-2}
$$

其中 $\mathcal{N}$ 是微分算子（如对流扩散算子），$\mathcal{B}$ 是边界算子（如 Dirichlet 或 Neumann），$\Omega$ 是空间域，$\lambda$ 是物理参数。

PINN 用一个全连接神经网络 $\hat{u}(\mathbf{x}, t; \theta)$ 逼近 $u$，其中 $\theta$ 是网络参数。定义物理残差为：

$$
r(\mathbf{x}, t; \theta) = \mathcal{N}[\hat{u}(\mathbf{x}, t; \theta); \lambda] \tag{4-3}
$$

如果 $\hat{u}$ 完美满足方程，则 $r = 0$ 处处成立。

### 4.2.2 损失函数构造

PINN 的总损失函数由四项组成：

$$
\mathcal{L}(\theta) = \lambda_d \mathcal{L}_{\text{data}} + \lambda_p \mathcal{L}_{\text{physics}} + \lambda_b \mathcal{L}_{\text{bc}} + \lambda_i \mathcal{L}_{\text{ic}} \tag{4-4}
$$

**数据项** $\mathcal{L}_{\text{data}}$——拟合观测数据：

$$
\mathcal{L}_{\text{data}} = \frac{1}{N_d} \sum_{j=1}^{N_d} |\hat{u}(\mathbf{x}_j^d, t_j^d) - u_j^{\text{obs}}|^2
$$

其中 $\{(\mathbf{x}_j^d, t_j^d, u_j^{\text{obs}})\}_{j=1}^{N_d}$ 是 $N_d$ 个观测数据点。

**物理残差项** $\mathcal{L}_{\text{physics}}$——在配置点（collocation points）上满足方程：

$$
\mathcal{L}_{\text{physics}} = \frac{1}{N_r} \sum_{j=1}^{N_r} |r(\mathbf{x}_j^r, t_j^r)|^2
$$

其中 $\{(\mathbf{x}_j^r, t_j^r)\}_{j=1}^{N_r}$ 是 $N_r$ 个配置点，分布在整个时空域 $\Omega \times [0, T]$ 上。

**边界条件项** $\mathcal{L}_{\text{bc}}$——满足边界条件：

$$
\mathcal{L}_{\text{bc}} = \frac{1}{N_b} \sum_{j=1}^{N_b} |\mathcal{B}[\hat{u}(\mathbf{x}_j^b, t_j^b)] - g_j|^2
$$

**初值条件项** $\mathcal{L}_{\text{ic}}$——满足初始条件：

$$
\mathcal{L}_{\text{ic}} = \frac{1}{N_i} \sum_{j=1}^{N_i} |\hat{u}(\mathbf{x}_j^i, 0) - u_0(\mathbf{x}_j^i)|^2
$$

**物理直觉**：$\mathcal{L}_{\text{data}}$ 让网络"跟着数据走"，$\mathcal{L}_{\text{physics}}$ 让网络"按方程走"，两者共同约束网络既拟合现实又服从物理。当数据充足时，$\mathcal{L}_{\text{data}}$ 主导；当数据稀缺时，$\mathcal{L}_{\text{physics}}$ 起到"虚拟数据"的作用，用物理先验填补数据空白。

### 4.2.3 自动微分

PINN 的一个关键技术优势是 **自动微分**（Automatic Differentiation, AD）。计算物理残差 $r = \mathcal{N}[\hat{u}]$ 需要求 $\hat{u}$ 对 $\mathbf{x}$ 和 $t$ 的偏导数（如 $\partial \hat{u}/\partial t$、$\partial^2 \hat{u}/\partial x^2$）。

自动微分（Baydin et al., 2018）利用链式法则，在神经网络的计算图（Goodfellow et al., 2016 第6章详述了计算图的概念）上精确（非近似）计算任意阶导数：

$$
\frac{\partial \hat{u}}{\partial x} = \frac{\partial \hat{u}}{\partial z_L} \cdot \frac{\partial z_L}{\partial z_{L-1}} \cdots \frac{\partial z_1}{\partial x} \tag{4-5}
$$

其中 $z_1, \ldots, z_L$ 是网络各层的中间变量。

**与有限差分的对比**：传统 PDE 求解器用有限差分近似导数（$\partial u/\partial x \approx (u_{i+1} - u_{i-1})/2\Delta x$），存在截断误差和网格依赖。自动微分在浮点精度范围内精确计算导数，无需网格，且对不规则域自然适用。

在 PyTorch 和 TensorFlow 等深度学习框架中，自动微分已内置于反向传播机制。计算 PINN 物理残差只需额外几行代码。

---

## 4.3 水动力学 PINN

### 4.3.1 Saint-Venant 方程的 PINN 形式

> **T2a/T2b 边界声明**: 以下 Saint-Venant 方程的物理推导详见 T2a 第二章。本节仅列出 PINN 训练所需的残差方程形式，不作独立推导。对物理方程不熟悉的读者，只需理解：这些方程描述了水在渠道中的守恒关系；PINN 将这些守恒关系作为训练约束，使神经网络的预测始终满足物理定律，即使在缺少实测数据的区域也能给出物理一致的结果。

Saint-Venant 方程（线性化形式，参见 T2a 第二章推导；完整模型参见 Litrico & Fromion, 2009）描述明渠非恒定流。Cai et al.（2021）系统综述了 PINN 在流体力学中的应用，明渠水动力学是其中的典型场景：

**连续方程**：
$$
\frac{\partial A}{\partial t} + \frac{\partial Q}{\partial x} = q_l \tag{4-6a}
$$

**动量方程**：
$$
\frac{\partial Q}{\partial t} + \frac{\partial}{\partial x}\left(\frac{Q^2}{A}\right) + gA\frac{\partial h}{\partial x} = gA(S_0 - S_f) + q_l v_l \tag{4-6b}
$$

PINN 形式：设网络输出 $\hat{h}(x, t; \theta)$ 和 $\hat{Q}(x, t; \theta)$（水位和流量），则物理残差为：

$$
r_1 = \frac{\partial \hat{A}}{\partial t} + \frac{\partial \hat{Q}}{\partial x} - q_l \tag{4-7a}
$$

$$
r_2 = \frac{\partial \hat{Q}}{\partial t} + \frac{\partial}{\partial x}\left(\frac{\hat{Q}^2}{\hat{A}}\right) + g\hat{A}\frac{\partial \hat{h}}{\partial x} - g\hat{A}(S_0 - S_f) \tag{4-7b}
$$

其中 $\hat{A} = A(\hat{h})$ 通过断面几何关系（如梯形断面 $A = (B + mh)h$）从 $\hat{h}$ 计算，$S_f$ 由 Manning 方程给出（$S_f = n^2 Q^2 / (A^2 R_h^{4/3})$，$R_h$ 为水力半径）。所有偏导数通过自动微分精确计算。

### 4.3.2 配置点采样策略

配置点是 PINN 在物理残差项上采样的时空点。采样策略直接影响训练效率和收敛性：

**均匀采样**：在时空域 $[0, L] \times [0, T]$ 上等间距网格采样。简单但不高效——平稳区域浪费算力，剧变区域采样不足。

**拉丁超方格采样（LHS）**：在多维空间中保证各维度的均匀覆盖，比纯随机采样更高效。推荐作为默认方法。

**自适应采样（Residual-Based Adaptive Refinement, RAR）**：训练若干轮后，在物理残差 $|r|$ 较大的区域增加配置点密度。这类似传统数值方法的自适应网格加密，但不需要显式网格。

**水系统中的实践建议**：
- 在闸门/泵站等执行器位置加密采样——该处流量突变，方程残差较大
- 在波前传播路径上加密——水位波动剧烈区域需要更多约束
- 在初始时刻和边界附近加密——初/边值条件是 PINN 训练的关键约束

配置点数量的经验法则：$N_r = 10 \times N_d$（配置点数量为观测数据点的 10 倍），确保物理约束足够密集。

### 4.3.3 边界条件处理

水系统的边界条件通常包括：

**上游边界**：入流流量 $Q(0, t) = Q_{\text{in}}(t)$（Dirichlet 类型）

**下游边界**：水位控制 $h(L, t) = h_{\text{dn}}(t)$ 或水位-流量关系 $Q(L, t) = f(h(L, t))$

**内部边界**：闸门/泵站处的流量-开度关系 $Q_{\text{gate}} = C_d \cdot A_{\text{gate}} \cdot \sqrt{2g \Delta h}$

**两种处理方式**：

**软约束（Soft Constraint）**：将边界条件作为损失项 $\mathcal{L}_{\text{bc}}$ 加入总损失。简单灵活，但边界精度受权重 $\lambda_b$ 影响，可能不严格满足。

**硬约束（Hard Constraint）**：将网络输出结构化为自动满足边界条件的形式。例如，对 Dirichlet 条件 $u(0, t) = g(t)$，构造 $\hat{u}(x, t) = g(t) + x \cdot \text{NN}(x, t)$，则 $\hat{u}(0, t) = g(t)$ 自动成立。硬约束精度更高但设计更复杂。

**推荐**：上下游边界使用硬约束（这些是水系统最重要的边界，必须精确满足），内部边界和初值使用软约束。

### 4.3.4 管网水力学 PINN

对于压力管网，控制方程为（参见 T2a 第三章）：

**连续方程（节点）**：$\sum Q_{\text{in}} - \sum Q_{\text{out}} = D$（节点流量平衡，$D$ 为节点需水量）

**动量方程（管段）**：$H_i - H_j = R \cdot Q_{ij} \cdot |Q_{ij}|$（Hazen-Williams 或 Darcy-Weisbach 阻力关系）

PINN 可以同时学习全管网的水头 $H$ 和流量 $Q$ 分布，物理残差为节点流量平衡残差和管段阻力方程残差。与明渠 PINN 相比，管网 PINN 的优势在于：

- 管网方程是代数方程（稳态）或 ODE（瞬变），比 PDE 更容易求解
- 管网拓扑天然适合图结构，可与 GNN 结合（参见 ch03 §3.6.1）

Tartakovsky et al.（2020）展示了物理信息深度神经网络在地下水流参数学习中的应用，其方法论可扩展到管网水力学。类似地，Mao et al.（2020）将 PINN 应用于高速流动问题，验证了其处理激波等强非线性特征的能力。

---

## 4.4 正问题与反问题

### 4.4.1 正问题：状态预测

**正问题定义**：给定物理参数（Manning $n$、底坡 $S_0$、断面几何等）和边界/初值条件，求解状态变量（水位 $h$、流量 $Q$）随时间和空间的演化。

在正问题中，$\lambda$ 已知，网络参数 $\theta$ 是唯一的优化变量：

$$
\theta^* = \arg\min_\theta \mathcal{L}(\theta) \tag{4-8}
$$

**PINN 正问题 vs 传统数值方法**：
| 维度 | 传统数值方法（有限差分/有限元） | PINN |
|:---|:---|:---|
| 网格依赖 | 需要结构化或非结构化网格 | 无网格，配置点可任意分布 |
| 不规则域 | 网格生成复杂 | 自然适用 |
| 高维问题 | 维度灾难 | 受影响较小 |
| 计算精度 | 高（$10^{-6}$ 级） | 中等（$10^{-3}$ 级） |
| 实时性 | 快（一次求解） | 慢（需训练） |
| 参数变化 | 需重新求解 | 可通过微调适应 |

**工程选择**：对于精度要求极高（如防洪调度）的场景，传统数值方法仍是首选。Sun et al.（2020）展示了在完全无仿真数据的条件下，仅依赖物理约束也能训练出合理的流场代理模型。PINN 的优势在于——（a）数据-模型融合：可以同化观测数据修正模型偏差；（b）不规则域：复杂水系拓扑无需网格生成；（c）快速迁移：参数变化后微调即可，无需重新求解。Raissi et al.（2020）在 *Science* 上发表的隐流体力学工作进一步证明，PINN 可以从流动可视化数据中同时学习速度场和压力场，为水系统的非侵入式监测开辟了新可能。

### 4.4.2 反问题：参数反演

**反问题定义**：给定观测数据和物理方程，反演未知的物理参数 $\lambda$（如 Manning 粗糙系数 $n$、管道粗糙度、渗漏系数等）。

在反问题中，网络参数 $\theta$ 和物理参数 $\lambda$ 同时作为优化变量：

$$
(\theta^*, \lambda^*) = \arg\min_{\theta, \lambda} \mathcal{L}(\theta, \lambda) \tag{4-9}
$$

PINN 反问题的应用已扩展到多个领域：Chen et al.（2020）将其用于纳米光学参数反演，Kissas et al.（2020）将其用于心血管血流动力学的非侵入式血压预测，证明了该方法论的跨领域通用性。

**关键技巧**：
- **参数约束**：物理参数有物理意义上的范围。Manning $n$ 通常在 $[0.010, 0.050]$ 范围内（混凝土渠 $\sim 0.013$，天然河道 $\sim 0.030$）。使用 Sigmoid 变换将无约束优化映射到可行范围：$n = n_{\min} + (n_{\max} - n_{\min}) \cdot \sigma(\hat{n})$
- **分步训练**：先固定 $\lambda$ 为初始估计值，训练 $\theta$ 至基本收敛；再解冻 $\lambda$，联合优化 $\theta$ 和 $\lambda$。这比从一开始就联合优化更稳定
- **正则化**：对 $\lambda$ 添加先验约束 $\mathcal{L}_{\text{prior}} = \|\lambda - \lambda_0\|^2$（$\lambda_0$ 为先验估计值），防止反演出非物理参数

### 4.4.3 空间变异参数反演

在实际水系统中，Manning $n$ 并非全渠段均匀——河床材质变化、淤积程度不同、植被覆盖差异都导致 $n$ 在空间上变化。PINN 可以将 $n$ 也参数化为神经网络 $\hat{n}(x; \phi)$，学习粗糙系数的空间分布：

$$
(\theta^*, \phi^*) = \arg\min_{\theta, \phi} \left[\mathcal{L}_{\text{data}} + \lambda_p \mathcal{L}_{\text{physics}}(\hat{u}, \hat{n}) + \lambda_s \|\nabla_x \hat{n}\|^2\right] \tag{4-10}
$$

其中 $\|\nabla_x \hat{n}\|^2$ 是空间平滑正则项——假设粗糙系数在空间上平滑变化，不会出现突变。

---

## 4.5 训练策略与收敛技巧

### 4.5.1 损失权重自适应

式(4-4)中的权重 $\lambda_d, \lambda_p, \lambda_b, \lambda_i$ 对训练收敛至关重要。如果 $\lambda_p$ 过大，网络过度拟合方程而忽视数据；如果 $\lambda_p$ 过小，物理约束形同虚设。

**NTK 自适应方法**（Wang et al., 2021）：基于神经正切核（Neural Tangent Kernel）理论，自动调整各损失项的权重，使各项的梯度贡献在训练过程中保持平衡：

$$
\lambda_k^{(t+1)} = \frac{\max_k \overline{|\nabla_\theta \mathcal{L}_k^{(t)}|}}{\overline{|\nabla_\theta \mathcal{L}_k^{(t)}|}} \cdot \lambda_k^{(t)} \tag{4-11}
$$

其中 $\overline{|\nabla_\theta \mathcal{L}_k|}$ 是第 $k$ 项损失的平均梯度幅值。

McClenny & Braga-Neto（2023）进一步提出了自适应 PINN 方法，自动学习各配置点的权重，将自适应从损失层级细化到了采样点层级。

**实践建议**：初始阶段设 $\lambda_d = \lambda_b = \lambda_i = 1.0$，$\lambda_p = 0.01$（物理项权重较小，让网络先拟合数据），然后每 1000 步按 NTK 方法更新权重。

### 4.5.2 课程学习

**课程学习（Curriculum Learning）**的思想是"先易后难"：

**时间域课程**：先在短时间窗口 $[0, T_1]$ 上训练至收敛，再逐步扩展到 $[0, T_2]$, $[0, T_3]$, ..., $[0, T]$。水动力学问题中，长时间模拟的解可能非常复杂（多次波反射叠加），课程学习帮助网络逐步适应复杂度。

**方程复杂度课程**：先用简化方程（如扩散波方程）训练，再切换到完整 Saint-Venant 方程。简化方程的解更光滑、更容易学习，可以为完整方程提供良好的初始化。

### 4.5.3 分域训练（Domain Decomposition）

对于大尺度水系统（如数百公里的调水工程），单个 PINN 难以同时精确拟合整个时空域。分域训练将问题分解为多个子域，每个子域训练一个独立的 PINN，子域间通过界面条件耦合。

**XPINN**（Jagtap & Karniadakis, 2020）是分域 PINN 的代表方法：
- 将空间域划分为 $K$ 个子域 $\Omega_1, \ldots, \Omega_K$
- 每个子域有独立的神经网络 $\hat{u}_k$
- 子域界面添加连续性约束：$\hat{u}_k = \hat{u}_{k+1}$ 和 $\partial \hat{u}_k / \partial \mathbf{n} = \partial \hat{u}_{k+1} / \partial \mathbf{n}$

在水系统中，分域边界自然对应渠段分界点或节点——这与 T2a 中的分段建模和分布式控制（参见 T2a 第十二章）思想一致。

### 4.5.4 网络架构选择

**全连接网络（MLP）**：PINN 最常用的架构。典型配置：4~8 层，每层 64~256 神经元，激活函数 $\tanh$（比 ReLU 更适合 PINN，因为 $\tanh$ 是光滑函数，导数性质好）。

**修改的 MLP（Modified MLP）**：引入残差连接、层归一化或 Fourier 特征映射，改善训练收敛。Fourier 特征映射 $\gamma(\mathbf{x}) = [\cos(2\pi \mathbf{B} \mathbf{x}), \sin(2\pi \mathbf{B} \mathbf{x})]$ 帮助网络学习高频特征。

**DeepONet**（Lu et al., 2021）：学习算子映射而非单个函数，可以一次训练后泛化到不同的边界/初值条件。适合需要频繁更换边界条件的水系统运行场景。

---

## 4.6 PINN 与传统方法的对比

### 4.6.1 与数值 PDE 求解器的对比

[表 4-1: PINN vs 传统数值方法]
| 维度 | 有限差分/有限体积 | 有限元 | PINN |
|:---|:---|:---|:---|
| 网格需求 | 需要结构化网格 | 需要非结构化网格 | 无网格 |
| 精度 | 高（$10^{-6}$） | 高 | 中等（$10^{-3}$） |
| 数据融合 | 需额外同化步骤（如 Kalman） | 同上 | 原生支持 |
| 反问题 | 需伴随方法 | 同上 | 原生支持 |
| 高维扩展 | 维度灾难 | 同上 | 较好 |
| 实时计算 | 快 | 较快 | 训练慢，推理快 |
| 工程成熟度 | 高 | 高 | 低（发展中） |

### 4.6.2 与纯数据驱动模型的对比

Cuomo et al.（2022）对 PINN 的发展脉络和未来方向做了全面综述，指出 PINN 在精度、效率和扩展性方面仍有显著改进空间。

| 维度 | 纯数据驱动（LSTM/Transformer） | PINN |
|:---|:---|:---|
| 物理一致性 | 不保证 | 显式约束 |
| 数据需求 | 高 | 中低 |
| 外推能力 | 差 | 较好（物理引导） |
| 可解释性 | 低 | 中（可检查残差分布） |
| 训练难度 | 低 | 高（多项损失平衡） |
| 适用场景 | 数据丰富、精度优先 | 数据稀缺、物理一致性优先 |

### 4.6.3 适用场景建议

- **数据丰富 + 精度优先** → ch03 的 LSTM/Transformer
- **数据稀缺 + 物理一致性优先** → PINN
- **精度极高 + 实时性** → 传统数值方法（T2a）
- **参数反演** → PINN（显著优于传统伴随方法的编程复杂度）
- **数据+模型融合** → PINN + Kalman 滤波（T2a 第十一章）

---

## 4.7 PINN 工程部署门禁

### 4.7.1 物理一致性门禁

PINN 上线前必须通过物理一致性检查：

**守恒性验证**：在关键渠段检查质量守恒——选取上下游两个断面和中间的侧入流，验证 $\int_0^T [Q_{\text{in}}(t) - Q_{\text{out}}(t) + Q_{\text{lateral}}(t)] dt \approx \Delta V$（蓄水量变化）。偏差应 < 1%。

**方程残差统计**：在全时空域上计算物理残差 $|r|$ 的分布。残差的 95% 分位数应低于工程可接受的阈值（如对于水位预测，$|r_{0.95}| < 0.01$ m/s）。

**残差热图**：可视化方程残差在时空域上的分布。如果残差集中在某些区域（如闸门附近），说明该区域的物理约束不足，需增加配置点或调整网络架构。

### 4.7.2 预测性能门禁

与 ch03 §3.9.1 的性能门禁一致：
- 测试集 RMSE 达标
- 极端工况子集单独评估
- 分位误差 $E_{0.95}$ 在安全裕度内
- 连续 30 天回放测试无异常

### 4.7.3 安全与治理门禁

**安全门禁**：在 SIL 环境中（Lei 2025b），将 PINN 预测接入 MPC 控制器，验证闭环性能。特别关注 PINN 是否在 ODD 边界附近产生不合理的物理预测。Yang et al.（2021）提出的贝叶斯 PINN（B-PINNs）可以为预测结果提供不确定性区间，辅助安全门禁判断——当不确定性超过阈值时自动触发保守回退。

**治理门禁**：模型版本、训练数据、配置点分布、损失权重历史全部存档。PINN 的特殊治理要求是——物理方程版本也需存档（如使用了哪种 Saint-Venant 简化形式）。

[表 4-2: PINN 部署门禁清单]
| 门禁类别 | 具体判据 | 不满足处置 |
|:---|:---|:---|
| 物理一致性 | 质量守恒偏差 < 1%，残差 $\lvert r_{0.95} \rvert$ 低于阈值 | 退回训练重标定 |
| 预测性能 | 关键断面 RMSE 达标，极端子集单独达标 | 禁止上线 |
| 工程安全 | SIL 闭环验证通过，ODD 边界无异常 | 启动保守回退 |
| 治理能力 | 方程版本+训练配置+模型权重全存档 | 暂缓发布 |

---

## 4.8 例题

### 例 4-1：PINN 求解单渠段非恒定流（正问题）

**已知**：某梯形明渠，长度 $L = 5$ km，底宽 $B = 6$ m，边坡 $m = 1.5$，底坡 $S_0 = 0.0002$，Manning $n = 0.016$。上游入流 $Q_{\text{in}}(t)$ 为正弦波动（均值 10 m³/s，振幅 3 m³/s，周期 12 h）。下游水位恒定 $h_{\text{dn}} = 2.0$ m。观测数据：沿渠每 1 km 一个水位传感器，每 30 分钟采样一次，共 48 小时数据。

**求解**：用 PINN 求解全渠段水位-流量时空分布。

**解题过程**：

步骤 1：网络设计——输入 $(x, t)$，输出 $(\hat{h}, \hat{Q})$。4 层 MLP，每层 128 神经元，激活函数 $\tanh$。

步骤 2：损失构造——数据项：5 个传感器 × 96 个时间步 = 480 个数据点。物理项：LHS 采样 5000 个配置点。上游边界（硬约束）：$\hat{Q}(0, t) = Q_{\text{in}}(t)$。下游边界（硬约束）：$\hat{h}(L, t) = 2.0$ m。初值（软约束）：稳态解 $h_0(x), Q_0(x)$。

步骤 3：训练——Adam 优化器，学习率 $10^{-3}$，训练 50,000 步。前 10,000 步 $\lambda_p = 0.01$，之后用 NTK 自适应调整。

步骤 4：结果验证——PINN 预测与有限差分法（Preissmann 格式，$\Delta x = 100$ m, $\Delta t = 60$ s）对比，水位 RMSE = 1.2 cm，流量 RMSE = 0.15 m³/s。质量守恒偏差 0.3%。

**结果讨论**：PINN 精度虽低于精细有限差分（RMSE 差 3~5 倍），但无需网格生成，且能自然同化观测数据。在传感器观测点附近，PINN 精度与有限差分相当。

---

### 例 4-2：PINN 反演 Manning 粗糙系数

**已知**：例 4-1 的渠段经过 3 个月运行后，河床淤积导致粗糙系数变化。现有 72 小时密集观测数据（5 个水位传感器 + 上下游流量计），需要反演当前的 Manning $n$。

**求解**：设计 PINN 反问题求解流程。

**解题过程**：

步骤 1：将 $n$ 作为可优化参数。使用 Sigmoid 约束：$n = 0.010 + 0.040 \times \sigma(\hat{n}_{\text{raw}})$，初始化 $\hat{n}_{\text{raw}} = 0$（对应 $n = 0.030$）。

步骤 2：分步训练——第一阶段固定 $n = 0.030$，训练网络参数 $\theta$ 至收敛（20,000 步）。第二阶段解冻 $n$，联合优化 $\theta$ 和 $n$（再训练 30,000 步，$n$ 的学习率设为网络参数的 1/10）。

步骤 3：反演结果——$n = 0.021 \pm 0.002$（相比原始 $n = 0.016$ 增大了 31%，与淤积现象一致）。

步骤 4：验证——用反演的 $n = 0.021$ 代入有限差分求解器，独立验证水位预测精度。反演后的模型在独立验证集上 RMSE 从 5.8 cm（旧 $n$）降至 1.5 cm（新 $n$）。

步骤 5：接入调度系统——在 SIL 环境中用新参数更新 MPC 模型，验证控制性能无劣化后上线。

**结果讨论**：PINN 反演不需要推导伴随方程（传统方法所需），大幅降低了参数标定的编程复杂度。反演结果应结合工程判断——如果反演出 $n > 0.04$，应考虑是否存在更严重的渠道问题（如结构破损）。

---

### 例 4-3：PINN 与 Kalman 滤波的数据同化对比

**已知**：某渠段同时部署了 PINN 模型和 Kalman 滤波器（T2a 第十一章）进行状态估计。传感器故障导致中间 2 km 区段 12 小时无数据。

**求解**：比较两种方法在数据缺失期间的表现。

**解题过程**：

步骤 1：Kalman 滤波——在数据缺失期间依赖状态预测（模型传播），预测误差随时间线性增长。12 小时后水位估计误差达 8 cm。

步骤 2：PINN——在缺失区域仍有物理残差约束（配置点覆盖整个时空域）。利用上下游传感器数据和物理方程"推断"中间区段的状态。12 小时后水位估计误差仅 2.5 cm。

步骤 3：联合方案——用 Kalman 滤波提供初始状态估计和不确定性量化，PINN 在数据缺失区域提供物理约束补充。联合方案的 12 小时误差为 1.8 cm。

**结果讨论**：PINN 在数据缺失场景的优势在于——物理方程本身就是一种"虚拟传感器"，可以在无观测区域推断状态。这对于传感器故障频发的水系统具有重要工程价值。两种方法互补使用优于单独使用。

---

### 例 4-4：空间变异粗糙系数反演

**已知**：某 20 km 长的天然河道，河床材质从上游卵石段逐渐变为下游砂质段。沿河 10 个水位站提供 1 周密集观测数据。

**求解**：用 PINN 反演 Manning $n$ 的空间分布 $n(x)$。

**解题过程**：

步骤 1：将 $n(x)$ 参数化为小型神经网络 $\hat{n}(x; \phi)$：2 层 MLP，每层 32 神经元，输出经 Sigmoid 映射到 $[0.015, 0.045]$。添加空间平滑正则 $\|\partial \hat{n}/\partial x\|^2$。

步骤 2：联合训练——优化状态网络 $\theta$ 和参数网络 $\phi$，总训练 80,000 步。

步骤 3：反演结果——$n(x)$ 从上游 0.032（卵石段合理）平滑过渡到下游 0.022（砂质段合理），中间过渡段 $n$ 在 0.025~0.028 之间。

步骤 4：验证——反演的 $n(x)$ 与工程手册中类似河道的经验值一致（卵石 0.030~0.040，砂质 0.020~0.025）。用反演参数进行 48 小时独立预测，RMSE 比均匀 $n$ 方案降低 35%。

**结果讨论**：空间变异参数反演是 PINN 的独特优势。传统标定方法只能得到分段常数的 $n$ 值，而 PINN 给出连续分布，更接近物理现实。Lei 2025c 讨论的从静态平衡到动态控制范式转变中，PINN 的参数自适应能力是关键使能技术之一。

---

## 4.9 本章小结

本章建立了 PINN 在水系统中的工程化应用框架，核心要点如下：

1. **PINN 的本质是"用方程做正则化"**。将物理残差加入损失函数，约束网络在数据稀疏区域也能给出物理合理的预测。这是 CHS 混合驱动范式的数学实现。

2. **自动微分是 PINN 的技术关键**。它使得任意复杂的 PDE 残差都可以精确计算，无需手动推导或离散化。配置点采样策略（尤其是自适应采样）直接影响训练效率。

3. **反问题是 PINN 的独特优势**。参数反演、空间变异参数辨识——PINN 不需要推导伴随方程，大幅降低了编程复杂度。反演结果应结合物理约束和工程判断。

4. **训练策略决定 PINN 的成败**。损失权重自适应、课程学习、分域训练是应对训练不稳定的三大工具。边界条件推荐使用硬约束。

5. **PINN 并非替代传统方法，而是互补**。数据丰富时用 ch03 的纯数据模型，精度要求极高时用 T2a 的传统数值方法，数据稀缺且需要物理一致性时用 PINN。三者在 CHS 框架中各有位置。

下一章将进入强化学习与水系统控制——在已具备预测能力（ch02-ch04）的前提下，讨论如何让智能体在不确定环境中持续优化控制动作。

---

## 习题

### 基础题

**4-1.** PINN 与 ch03 中纯数据驱动深度学习模型的核心区别是什么？在什么场景下 PINN 更有优势？

**4-2.** 写出 PINN 总损失函数的四个组成部分，并解释每一项的物理含义。

**4-3.** 什么是自动微分？它与有限差分计算导数的区别是什么？

**4-4.** 解释 PINN 正问题和反问题的区别。在参数反演中，为什么需要对物理参数施加范围约束？

**4-5.** 为什么 PINN 推荐使用 $\tanh$ 激活函数而非 ReLU？

### 应用题

**4-6.** 某梯形明渠长 10 km，有 8 个水位传感器和上下游流量计。设计完整的 PINN 正问题求解方案，包括网络架构、配置点采样策略、损失权重设置和验证方法。

**4-7.** 某渠段经检修后粗糙系数变化，需用 72 小时观测数据反演新的 Manning $n$。设计 PINN 反问题方案，包括参数约束方法和分步训练策略。

**4-8.** 设计 PINN 模型的完整工程部署门禁流程（物理一致性+预测性能+安全+治理），每项列出具体判据。

**4-9.** 某 30 km 天然河道需要反演 Manning $n$ 的空间分布。设计空间变异参数 PINN 方案，包括参数网络设计和平滑正则化方法。

**4-10.** 对比 PINN 与 Kalman 滤波在传感器缺失场景下的数据同化能力，提出互补使用方案。

### 思考题

**4-11.** 在观测数据质量较差（噪声大、缺测多）时，PINN 应更依赖物理项还是数据项？如何通过损失权重调整实现这一平衡？

**4-12.** PINN 的物理残差项本质上假设控制方程是精确的。但在实际水系统中，方程本身也有近似误差（如 Saint-Venant 方程忽略了风应力和二次底摩阻）。这对 PINN 有什么影响？如何缓解？

**4-13.** 分域 PINN（XPINN）的子域划分应遵循什么原则？水系统中哪些位置是天然的分域边界？

**4-14.** DeepONet 可以学习从边界条件到解的算子映射。讨论这在水系统运行调度中的潜在应用——如果调度员改变闸门开度序列，DeepONet 能否实时给出整个渠段的水位响应？

**4-15.** 如果一个 PINN 模型通过了物理一致性门禁（守恒性偏差 < 1%）但未通过 SIL 安全门禁（MPC 闭环水位越界），可能的原因是什么？应如何处理？

---

## 拓展阅读

1. Raissi, M., Perdikaris, P. & Karniadakis, G.E. (2019). Physics-informed neural networks. *Journal of Computational Physics*, 378, 686-707.——PINN 方法的原始论文。

2. Karniadakis, G.E. et al. (2021). Physics-informed machine learning. *Nature Reviews Physics*, 3(6), 422-440.——物理信息机器学习的权威综述。

3. Lu, L. et al. (2021). DeepXDE: A deep learning library for solving differential equations. *SIAM Review*, 63(1), 208-228.——PINN 开源框架，含丰富教程。

4. Litrico, X. & Fromion, V. (2009). *Modeling and Control of Hydrosystems*. Springer.——水系统机理建模的经典著作，提供 PINN 物理残差的方程来源。

5. Wang, S., Teng, Y. & Perdikaris, P. (2021). Understanding and mitigating gradient flow pathologies in physics-informed neural networks. *SIAM Journal on Scientific Computing*, 43(5), A3055-A3081.——PINN 训练稳定性分析。

---

## 参考文献

[4-1] 雷晓辉,龙岩,许慧敏,等.水系统控制论：提出背景、技术框架与研究范式[J].南水北调与水利科技(中英文),2025,23(04):761-769+904.DOI:10.13476/j.cnki.nsbdqk.2025.0077.

[4-2] 雷晓辉,张峥,苏承国,等.自主运行智能水网的在环测试体系[J].南水北调与水利科技(中英文),2025,23(04):787-793.DOI:10.13476/j.cnki.nsbdqk.2025.0080.

[4-3] 雷晓辉,许慧敏,何中政,等.水资源系统分析学科展望：从静态平衡到动态控制[J].南水北调与水利科技(中英文),2025,23(04):770-777.DOI:10.13476/j.cnki.nsbdqk.2025.0078.

[4-4] Raissi, M., Perdikaris, P. & Karniadakis, G.E. (2019). Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. *Journal of Computational Physics*, 378, 686-707.

[4-5] Karniadakis, G.E., Kevrekidis, I.G., Lu, L., Perdikaris, P., Wang, S. & Yang, L. (2021). Physics-informed machine learning. *Nature Reviews Physics*, 3(6), 422-440.

[4-6] Raissi, M., Yazdani, A. & Karniadakis, G.E. (2020). Hidden fluid mechanics: Learning velocity and pressure fields from flow visualizations. *Science*, 367(6481), 1026-1030.

[4-7] Lu, L., Meng, X., Mao, Z. & Karniadakis, G.E. (2021). DeepXDE: A deep learning library for solving differential equations. *SIAM Review*, 63(1), 208-228.

[4-8] Baydin, A.G., Pearlmutter, B.A., Radul, A.A. & Siskind, J.M. (2018). Automatic differentiation in machine learning: A survey. *Journal of Machine Learning Research*, 18(153), 1-43.

[4-9] Wang, S., Teng, Y. & Perdikaris, P. (2021). Understanding and mitigating gradient flow pathologies in physics-informed neural networks. *SIAM Journal on Scientific Computing*, 43(5), A3055-A3081.

[4-10] Jagtap, A.D. & Karniadakis, G.E. (2020). Extended physics-informed neural networks (XPINNs): A generalized space-time domain decomposition based deep learning framework for nonlinear partial differential equations. *Communications in Computational Physics*, 28(5), 2002-2041.

[4-11] Tartakovsky, A.M., Marrero, C.O., Perdikaris, P., Tartakovsky, G.D. & Barajas-Solano, D. (2020). Physics-informed deep neural networks for learning parameters and constitutive relationships in subsurface flow problems. *Water Resources Research*, 56(5), e2019WR026731.

[4-12] Litrico, X. & Fromion, V. (2009). *Modeling and Control of Hydrosystems*. Springer.

[4-13] Brunton, S.L. & Kutz, J.N. (2019). *Data-Driven Science and Engineering: Machine Learning, Dynamical Systems, and Control*. Cambridge University Press.

[4-14] Goodfellow, I., Bengio, Y. & Courville, A. (2016). *Deep Learning*. MIT Press.

[4-15] LeCun, Y., Bengio, Y. & Hinton, G. (2015). Deep learning. *Nature*, 521(7553), 436-444.

[4-16] Lagaris, I.E., Likas, A. & Fotiadis, D.I. (1998). Artificial neural networks for solving ordinary and partial differential equations. *IEEE Transactions on Neural Networks*, 9(5), 987-1000.

[4-17] Cai, S., Mao, Z., Wang, Z., Yin, M. & Karniadakis, G.E. (2021). Physics-informed neural networks (PINNs) for fluid mechanics: A review. *Acta Mechanica Sinica*, 37(12), 1727-1738.

[4-18] Cuomo, S., Di Cola, V.S., Giampaolo, F., Rozza, G., Raissi, M. & Piccialli, F. (2022). Scientific machine learning through physics-informed neural networks: Where we are and what's next. *Journal of Scientific Computing*, 92(3), 88.

[4-19] Chen, Y., Lu, L., Karniadakis, G.E. & Dal Negro, L. (2020). Physics-informed neural networks for inverse problems in nano-optics and metamaterials. *Optics Express*, 28(8), 11618-11633.

[4-20] Kissas, G., Yang, Y., Hwuang, E., Witschey, W.R., Doshi, J.A. & Perdikaris, P. (2020). Machine learning in cardiovascular flows modeling: Predicting arterial blood pressure from non-invasive 4D flow MRI data using physics-informed neural networks. *Computer Methods in Applied Mechanics and Engineering*, 358, 112623.

[4-21] Sun, L., Gao, H., Pan, S. & Wang, J.-X. (2020). Surrogate modeling for fluid flows based on physics-constrained deep learning without simulation data. *Computer Methods in Applied Mechanics and Engineering*, 361, 112732.

[4-22] Mao, Z., Jagtap, A.D. & Karniadakis, G.E. (2020). Physics-informed neural networks for high-speed flows. *Computer Methods in Applied Mechanics and Engineering*, 360, 112789.

[4-23] Yang, L., Meng, X. & Karniadakis, G.E. (2021). B-PINNs: Bayesian physics-informed neural networks for forward and inverse PDE problems with noisy data. *Journal of Computational Physics*, 425, 109913.

[4-24] McClenny, L.D. & Braga-Neto, U.M. (2023). Self-adaptive physics-informed neural networks. *Journal of Computational Physics*, 474, 111722.

[4-25] Shen, C. (2018). A transdisciplinary review of deep learning research and its relevance for water resources scientists. *Water Resources Research*, 54(11), 8558-8593.
