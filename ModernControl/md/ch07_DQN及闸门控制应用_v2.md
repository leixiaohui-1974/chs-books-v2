# 第7章 DQN及闸门控制应用

<!-- 变更日志
v2 2026-03-05: 结构性重写——精简RL基础(引用T2b)、统一编号、修复公式、补PyTorch代码、补参考文献
v1 2026-03-04: 原始版本（许/黄）——理论深度好，无代码/图表/参考文献
-->

## 学习目标

通过本章学习，读者应能够：

1. 理解强化学习的核心思想及其与传统控制论的关系；
2. 掌握马尔可夫决策过程（MDP）的五元组建模方法，并将闸门调度问题建模为MDP；
3. 掌握DQN算法的两大创新机制（经验回放、目标网络）及其训练流程；
4. 掌握闸门控制的状态空间、动作空间和复合奖励函数的设计方法；
5. 能够使用Python/PyTorch实现简单的DQN闸门控制智能体。

---

## 7.1 强化学习概述

### 7.1.1 从控制到学习：为什么需要强化学习

前面各章介绍的MPC、自适应控制和鲁棒控制方法，都建立在一个共同的前提之上——**需要已知的系统模型**。然而，水系统的复杂性有时使得精确建模极为困难：流域水文过程包含强烈的非线性和随机性，多目标多约束的调度需求难以用单一的优化目标函数完全刻画。

强化学习（Reinforcement Learning, RL）提供了一种截然不同的思路：不依赖精确模型，而是让智能体（Agent）通过与环境的反复交互，在"试错"中学习最优的决策策略。这种学习范式与人类通过实践积累经验的方式高度相似。

RL与机器学习其他分支的核心区别在于：

**表7-1 三种机器学习范式对比**

| 特征 | 监督学习 | 无监督学习 | 强化学习 |
|------|---------|----------|---------|
| 反馈信号 | 标准答案（标签） | 无外部反馈 | 延迟的评价（奖励） |
| 数据特性 | i.i.d.，带标签 | i.i.d.，无标签 | 序贯相关，交互产生 |
| 学习目标 | 预测准确性 | 发现数据结构 | 最大化累积奖励 |
| 水系统应用 | 入库流量预测 | 工况模式聚类 | **闸门调度策略学习** |

### 7.1.2 RL的思想根源

强化学习的思想根源于对生物学习机制的观察和抽象，理解这些根源有助于把握RL的本质（Sutton and Barto, 2018）。

**效果律与试错学习**：心理学家桑代克通过"迷箱"实验发现，动物会逐渐增加导致满意结果的行为频率——这正是RL中策略 $\pi(a|s)$ 学习的生物原型。

**多巴胺与TD误差**：神经科学发现，大脑中多巴胺神经元的活动模式与RL中的时序差分（TD）误差信号高度吻合——当实际奖励超出预期时，多巴胺脉冲发放（正TD误差）；当预期奖励未出现时，多巴胺活动抑制（负TD误差）。这表明大脑本身就在执行类似TD学习的算法（Schultz et al., 1997）。

这种生物学根源使得RL不仅是一种有效的计算方法，更是一种符合自然学习规律的智能理论。将源于自然的学习方法应用于水利工程这一改造自然的领域，具有深刻的意义。

---

## 7.2 马尔可夫决策过程（MDP）

MDP是RL的数学基础，它为序贯决策问题提供了形式化语言。关于MDP的完整理论，读者可参阅T2b第5章。本节聚焦于MDP在水系统中的建模应用。

### 7.2.1 MDP五元组

一个MDP由五元组 $(\mathcal{S}, \mathcal{A}, P, R, \gamma)$ 定义：

$$
P(s'|s,a) = \Pr(S_{t+1}=s' \mid S_t=s, A_t=a) \tag{7.1}
$$

$$
G_t = \sum_{k=0}^{\infty} \gamma^k R_{t+k+1} \tag{7.2}
$$

- $\mathcal{S}$：状态空间——环境在某一时刻的完整描述
- $\mathcal{A}$：动作空间——智能体可执行的操作集合
- $P$：状态转移概率——描述环境动力学
- $R$：奖励函数——对动作好坏的即时评价
- $\gamma \in [0,1)$：折扣因子——权衡即时与未来奖励

**马尔可夫性质**：系统下一状态仅取决于当前状态和动作，与历史无关。这要求状态表示必须包含足够的决策信息。

### 7.2.2 闸门控制的MDP建模

将闸门调度问题转化为MDP是应用DRL的关键步骤。

**状态空间**设计需要综合水利专业知识和算法需求。一个较为完备的状态向量为：

$$
\mathbf{s}_t = \left[H_{\text{up},t}, \, Q_{\text{in},t}, \, Q_{\text{out},t}, \, H_{\text{target}}, \, \Delta t_{\text{flood}}, \, P_{\text{24h}}, \, T_{\text{season}}\right] \tag{7.3}
$$

**表7-2 闸门控制状态空间设计**

| 状态变量 | 符号 | 含义 | 典型范围 |
|---------|------|------|---------|
| 上游水位 | $H_{\text{up},t}$ | 当前库水位 | 140~160 m |
| 入库流量 | $Q_{\text{in},t}$ | 当前来水 | 0~5000 m³/s |
| 出库流量 | $Q_{\text{out},t}$ | 当前泄流 | 0~3000 m³/s |
| 目标水位 | $H_{\text{target}}$ | 调度目标 | 汛限/正常蓄水位 |
| 洪峰间隔 | $\Delta t_{\text{flood}}$ | 距洪峰时间 | 0~72 h |
| 降雨预报 | $P_{\text{24h}}$ | 未来24h雨量 | 0~200 mm |
| 季节指示 | $T_{\text{season}}$ | 当前月份 | 1~12 |

**注意**：所有状态变量在输入神经网络前须进行归一化（如Min-Max缩放到[0,1]），以消除量纲差异，加速训练收敛。

**动作空间**：DQN原生支持离散动作。将闸门调节离散化为若干档位：

$$
\mathcal{A} = \{-10\%, -5\%, -2\%, 0, +2\%, +5\%, +10\%\} \tag{7.4}
$$

其中数值表示闸门开度的调节增量。动作数量控制在5~15个为宜。

**奖励函数**设计是整个MDP建模的核心。复合奖励函数将多目标调度需求量化为标量信号：

$$
R_t = w_f R_{\text{flood}} + w_s R_{\text{supply}} + w_h R_{\text{target}} + w_m R_{\text{smooth}} \tag{7.5}
$$

各分项定义如下：

**防洪安全**（最高优先级）：
$$
R_{\text{flood}} = -C_{f} \cdot \max(0, \, H_{\text{up}} - H_{\text{flood}})^2 \tag{7.6}
$$

**供水安全**：
$$
R_{\text{supply}} = -C_{s} \cdot \max(0, \, H_{\text{dead}} - H_{\text{up}})^2 \tag{7.7}
$$

**水位跟踪**：
$$
R_{\text{target}} = -C_{h} \cdot (H_{\text{up}} - H_{\text{target}})^2 \tag{7.8}
$$

**操作平稳性**：
$$
R_{\text{smooth}} = -C_{m} \cdot (a_t - a_{t-1})^2 \tag{7.9}
$$

权重 $w_f \gg w_s > w_h > w_m$，确保安全约束具有最高优先级。汛期应增大 $w_f$，枯水期增大 $w_s$。

---

## 7.3 价值函数与贝尔曼方程

### 7.3.1 价值函数

**状态价值函数** $V^\pi(s)$：从状态 $s$ 出发，遵循策略 $\pi$ 的期望回报：

$$
V^\pi(s) = \mathbb{E}_\pi\left[\sum_{k=0}^{\infty} \gamma^k R_{t+k+1} \;\middle|\; S_t = s\right] \tag{7.10}
$$

**动作价值函数** $Q^\pi(s,a)$：在状态 $s$ 执行动作 $a$，然后遵循策略 $\pi$ 的期望回报：

$$
Q^\pi(s,a) = \mathbb{E}_\pi\left[\sum_{k=0}^{\infty} \gamma^k R_{t+k+1} \;\middle|\; S_t = s, A_t = a\right] \tag{7.11}
$$

$Q$ 函数是DQN的核心——如果知道最优 $Q^*(s,a)$，则最优策略为 $\pi^*(s) = \arg\max_a Q^*(s,a)$。

### 7.3.2 贝尔曼最优方程

最优 $Q$ 函数满足贝尔曼最优方程：

$$
Q^*(s,a) = \mathbb{E}_{s'}\left[R(s,a,s') + \gamma \max_{a'} Q^*(s',a')\right] \tag{7.12}
$$

这个方程揭示了 $Q^*$ 的递归结构：当前状态-动作对的最优价值等于即时奖励加上折扣后的下一状态最优价值。Q-Learning算法通过迭代逼近这个不动点。

### 7.3.3 Q-Learning更新规则

$$
Q(S_t, A_t) \leftarrow Q(S_t, A_t) + \alpha \left[\underbrace{R_{t+1} + \gamma \max_a Q(S_{t+1}, a)}_{\text{TD目标}} - Q(S_t, A_t)\right] \tag{7.13}
$$

方括号中的差值称为**TD误差**（Temporal Difference error），它衡量了当前估计与更好估计之间的偏差。Q-Learning是离策略（off-policy）算法：行为策略可以是 $\epsilon$-greedy（探索），而学习目标始终是最优策略（利用）。

---

## 7.4 RL与控制论的关系

RL与控制论都致力于解决动态系统的最优决策问题，但方法论侧重不同。理解二者的异同有助于在水利工程中做出恰当的技术选择。

**表7-3 强化学习与控制论术语对照**

| 控制论 | 强化学习 | 含义 |
|--------|---------|------|
| 被控对象 Plant | 环境 Environment | 被决策影响的系统 |
| 控制律 Control Law | 策略 Policy $\pi$ | 状态→动作的映射 |
| 状态 $\mathbf{x}$ | 状态 $s$ | 系统的当前描述 |
| 控制输入 $\mathbf{u}$ | 动作 $a$ | 施加于系统的操作 |
| 代价函数 $J$ | 负回报 $-G_t$ | 需要最小化/最大化的目标 |
| HJB方程 | 贝尔曼方程 | 最优性的递推条件 |

**表7-4 基于模型与无模型方法对比**

| 特征 | 控制论（MPC等） | 强化学习（DQN等） |
|------|---------------|-----------------|
| 模型需求 | 需要精确模型 | 不需要模型 |
| 数据效率 | 高（基于模型推演） | 低（需要大量交互） |
| 理论保证 | 稳定性/最优性有保证 | 理论保证有限 |
| 非线性处理 | 需要线性化或特殊技术 | 天然处理非线性 |
| 计算时机 | 在线求解优化问题 | 离线训练，在线推理 |
| 适用场景 | 模型可得、安全关键 | 模型难建、复杂非线性 |

**二者的融合**是当前的前沿方向：

1. **RL辅助传统控制**：用RL自动整定PID/MPC参数，适应不同工况；
2. **残差控制**：MPC处理主要动态，RL学习补偿模型残差；
3. **安全层**：在RL策略外加基于控制论的硬约束安全框架，确保输出始终在安全包络内——这与CHS的ODD/安全包络思想一致（Lei 2025a）。

---

## 7.5 DQN算法原理

### 7.5.1 从Q-Learning到DQN

Q-Learning用表格存储每个 $(s,a)$ 的Q值，当状态空间巨大时不可行。DQN的核心创新是用深度神经网络 $Q(s,a;\boldsymbol{\theta})$ 近似 $Q^*$，输入状态向量，输出各离散动作的Q值。

然而，直接将神经网络与Q-Learning结合会导致训练不稳定，因为：(a) 数据前后相关（非i.i.d.）；(b) 更新目标随参数变化而移动。DQN通过两大创新机制解决了这些问题（Mnih et al., 2015）。

### 7.5.2 经验回放（Experience Replay）

将智能体的经验 $(s_t, a_t, r_{t+1}, s_{t+1})$ 存入回放缓冲区 $\mathcal{D}$，训练时随机采样小批量数据。

- **打破相关性**：随机采样消除了数据的时序相关，使训练样本近似i.i.d.；
- **提高数据利用率**：每条经验可被多次采样用于训练。

### 7.5.3 目标网络（Target Network）

使用两个结构相同但参数不同的网络：

- **在线网络** $Q(s,a;\boldsymbol{\theta})$：每步梯度更新，用于选择动作；
- **目标网络** $Q(s,a;\boldsymbol{\theta}^-)$：参数冻结，每 $C$ 步从在线网络同步 $\boldsymbol{\theta}^- \leftarrow \boldsymbol{\theta}$。

TD目标使用目标网络计算，从而固定了学习目标：

$$
y_j = \begin{cases}
r_{j+1} & \text{if } s_{j+1} \text{ is terminal} \\
r_{j+1} + \gamma \max_{a'} Q(s_{j+1}, a'; \boldsymbol{\theta}^-) & \text{otherwise}
\end{cases} \tag{7.14}
$$

### 7.5.4 损失函数与训练

DQN的训练目标是最小化TD误差的均方：

$$
L(\boldsymbol{\theta}) = \mathbb{E}_{(s,a,r,s') \sim \mathcal{D}} \left[(y - Q(s,a;\boldsymbol{\theta}))^2\right] \tag{7.15}
$$

通过反向传播和Adam优化器更新在线网络参数 $\boldsymbol{\theta}$。

**DQN算法流程**：

1. 初始化在线网络 $\boldsymbol{\theta}$、目标网络 $\boldsymbol{\theta}^- \leftarrow \boldsymbol{\theta}$、回放缓冲区 $\mathcal{D}$
2. 对每个episode（如一个完整汛期调度过程）：
   - 获取初始状态 $s_1$
   - 对每个时间步 $t$：
     - 以 $\epsilon$-greedy策略选择动作 $a_t$
     - 执行 $a_t$，观测 $r_{t+1}, s_{t+1}$
     - 存储 $(s_t, a_t, r_{t+1}, s_{t+1})$ 到 $\mathcal{D}$
     - 从 $\mathcal{D}$ 随机采样mini-batch，计算损失，更新 $\boldsymbol{\theta}$
     - 每 $C$ 步同步 $\boldsymbol{\theta}^- \leftarrow \boldsymbol{\theta}$
3. 逐步衰减 $\epsilon$（从探索过渡到利用）

---

## 7.6 案例：水库闸门DQN调度

### 7.6.1 问题设定

考虑一座单库水库，需要通过闸门控制水位，兼顾防洪安全和蓄水目标。

**水库参数**：
- 水面面积 $A_s = 5 \times 10^6$ m²
- 汛限水位 $H_{\text{flood}} = 150$ m，死水位 $H_{\text{dead}} = 130$ m
- 目标蓄水位 $H_{\text{target}} = 145$ m
- 最大泄流能力 $Q_{\text{max}} = 2000$ m³/s
- 调度时间步长 $\Delta t = 1$ h

### 7.6.2 Python/PyTorch实现

```python
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random

# ===== 水库环境 =====
class ReservoirEnv:
    """简化水库闸门调度环境"""

    def __init__(self):
        self.As = 5e6        # 水面面积 [m²]
        self.H_flood = 150.0 # 汛限水位 [m]
        self.H_dead = 130.0  # 死水位 [m]
        self.H_target = 145.0
        self.Q_max = 2000.0  # 最大泄流 [m³/s]
        self.dt = 3600       # 1小时 [s]
        self.n_actions = 7   # 动作数
        self.action_map = [-0.10, -0.05, -0.02, 0, 0.02, 0.05, 0.10]
        self.reset()

    def reset(self):
        self.H = 145.0 + np.random.randn() * 1.0  # 初始水位
        self.gate_ratio = 0.3   # 初始闸门开度比例
        self.t = 0
        self.T_max = 720  # 30天
        # 生成入流过程（含洪水事件）
        t = np.arange(self.T_max)
        self.Qin_series = 300 + 800 * np.exp(-0.5 * ((t - 360) / 48)**2) \
                          + np.random.randn(self.T_max) * 30
        self.Qin_series = np.clip(self.Qin_series, 0, 5000)
        return self._get_state()

    def _get_state(self):
        """归一化状态向量"""
        Qin = self.Qin_series[min(self.t, self.T_max - 1)]
        Qout = self.gate_ratio * self.Q_max
        state = np.array([
            (self.H - 130) / 30,           # 水位归一化
            Qin / 2000,                      # 入流归一化
            Qout / 2000,                     # 出流归一化
            (self.H_target - 130) / 30,      # 目标归一化
            self.gate_ratio,                  # 当前开度
        ], dtype=np.float32)
        return state

    def step(self, action_idx):
        delta = self.action_map[action_idx]
        old_gate = self.gate_ratio
        self.gate_ratio = np.clip(self.gate_ratio + delta, 0, 1)

        Qin = self.Qin_series[min(self.t, self.T_max - 1)]
        Qout = self.gate_ratio * self.Q_max
        self.H += (Qin - Qout) * self.dt / self.As

        # 复合奖励
        r_flood = -100.0 * max(0, self.H - self.H_flood)**2
        r_supply = -100.0 * max(0, self.H_dead - self.H)**2
        r_target = -0.5 * (self.H - self.H_target)**2
        r_smooth = -5.0 * (self.gate_ratio - old_gate)**2
        reward = r_flood + r_supply + r_target + r_smooth

        self.t += 1
        done = (self.t >= self.T_max) or (self.H > 160) or (self.H < 125)
        return self._get_state(), reward, done

# ===== DQN网络 =====
class DQN(nn.Module):
    def __init__(self, n_state, n_action):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_state, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, n_action)
        )

    def forward(self, x):
        return self.net(x)

# ===== DQN智能体 =====
class DQNAgent:
    def __init__(self, n_state=5, n_action=7, lr=1e-3, gamma=0.99,
                 eps_start=1.0, eps_end=0.05, eps_decay=5000,
                 buffer_size=10000, batch_size=64, target_update=100):
        self.n_action = n_action
        self.gamma = gamma
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.batch_size = batch_size
        self.target_update = target_update
        self.steps = 0

        self.policy_net = DQN(n_state, n_action)
        self.target_net = DQN(n_state, n_action)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.buffer = deque(maxlen=buffer_size)

    def select_action(self, state):
        eps = self.eps_end + (self.eps_start - self.eps_end) * \
              np.exp(-self.steps / self.eps_decay)
        self.steps += 1
        if random.random() < eps:
            return random.randrange(self.n_action)
        with torch.no_grad():
            s = torch.FloatTensor(state).unsqueeze(0)
            return self.policy_net(s).argmax(dim=1).item()

    def store(self, s, a, r, s_next, done):
        self.buffer.append((s, a, r, s_next, done))

    def train_step(self):
        if len(self.buffer) < self.batch_size:
            return
        batch = random.sample(self.buffer, self.batch_size)
        s, a, r, s2, d = zip(*batch)

        s = torch.FloatTensor(np.array(s))
        a = torch.LongTensor(a).unsqueeze(1)
        r = torch.FloatTensor(r).unsqueeze(1)
        s2 = torch.FloatTensor(np.array(s2))
        d = torch.FloatTensor(d).unsqueeze(1)

        # 在线网络Q值
        q_val = self.policy_net(s).gather(1, a)

        # 目标网络计算TD目标
        with torch.no_grad():
            q_next = self.target_net(s2).max(dim=1, keepdim=True)[0]
            target = r + self.gamma * q_next * (1 - d)

        loss = nn.MSELoss()(q_val, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 定期同步目标网络
        if self.steps % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

# ===== 训练循环 =====
env = ReservoirEnv()
agent = DQNAgent()
n_episodes = 200
rewards_history = []

for ep in range(n_episodes):
    state = env.reset()
    total_reward = 0
    while True:
        action = agent.select_action(state)
        next_state, reward, done = env.step(action)
        agent.store(state, action, reward, next_state, float(done))
        agent.train_step()
        state = next_state
        total_reward += reward
        if done:
            break
    rewards_history.append(total_reward)
    if (ep + 1) % 50 == 0:
        avg = np.mean(rewards_history[-50:])
        print(f"Episode {ep+1}/{n_episodes}, 近50轮平均奖励: {avg:.1f}")

print(f"\n训练完成。最终50轮平均奖励: {np.mean(rewards_history[-50:]):.1f}")
```

### 7.6.3 安全层设计

工程部署时，DQN的输出必须经过安全层的校验和裁剪，确保不违反硬约束：

```python
def safety_layer(action_idx, H_current, H_flood, H_dead, env):
    """基于规则的安全层，对DQN动作进行强制约束"""
    delta = env.action_map[action_idx]
    new_gate = np.clip(env.gate_ratio + delta, 0, 1)

    # 硬约束1: 水位接近汛限时，禁止关闸
    if H_current > H_flood - 1.0 and delta < 0:
        return 3  # 强制"保持不变"

    # 硬约束2: 水位接近死水位时，禁止开闸
    if H_current < H_dead + 2.0 and delta > 0:
        return 3

    # 硬约束3: 水位超过汛限，强制全开
    if H_current > H_flood:
        return 6  # 最大开闸动作

    return action_idx
```

这种"DQN决策 + 规则安全层"的架构，结合了RL的自适应优化能力和传统控制的安全保障，是水利工程中DRL部署的推荐模式。这与CHS框架中"认知AI提议→物理AI验证→安全层兜底"的三层决策架构一致（Lei 2025b）。

---

## 7.7 本章小结

本章从强化学习的思想根源出发，系统阐述了MDP建模、Q-Learning理论和DQN算法，并将其应用于水库闸门调度控制：

1. **MDP建模**：将闸门调度建模为MDP，关键在于状态空间的设计（需包含充分的水情和预测信息以近似满足马尔可夫性）和复合奖励函数的设计（将多目标调度需求量化为标量信号）。

2. **DQN算法**：通过经验回放打破数据相关性，通过目标网络稳定训练目标，使得深度神经网络可以有效地逼近最优Q函数。

3. **RL与控制论的融合**：纯无模型RL面临样本效率和安全性挑战，纯基于模型的控制面临建模困难。二者融合——用仿真环境训练RL、用安全层保障硬约束——是水利工程的实用路径。

4. **局限性**：DQN仅支持离散动作空间，对连续的闸门开度控制需要离散化处理。第8章将介绍的DDPG算法直接处理连续动作空间，更适合闸门的精细控制。

---

## 习题

**基础题**

1. 简述MDP五元组中各要素的含义，并说明在闸门调度问题中分别对应什么。

2. 解释DQN中经验回放和目标网络各自解决了什么问题。如果去掉其中一个，训练会出现什么现象？

3. 比较表7-4中基于模型方法（MPC）和无模型方法（DQN）的优缺点。在什么场景下你会选择MPC？在什么场景下选择DQN？

**应用题**

4. 修改7.6.2节的代码，将动作空间从7个增加到11个（更精细的离散化），观察训练收敛速度和最终性能的变化。讨论动作空间粒度与控制精度之间的权衡。

5. 在奖励函数中增加发电效益项 $R_{\text{power}} = C_p \cdot Q_{\text{out}} \cdot (H_{\text{up}} - H_{\text{tail}})$，修改代码实现防洪-发电联合调度的DQN。

**思考题**

6. 闸门控制中的奖励函数权重 $w_f, w_s, w_h, w_m$ 如何确定？讨论奖励塑形（Reward Shaping）中的难点和可能的解决方案。

7. DQN训练需要大量的环境交互数据。在水利工程中，为什么不能直接在真实水库上进行"试错"训练？讨论仿真环境（数字孪生）在DRL训练中的必要性。（提示：联系第6章的数字孪生概念和CHS的xIL验证体系）

---

## 参考文献

[1] Sutton R S, Barto A G. Reinforcement Learning: An Introduction[M]. 2nd ed. Cambridge, MA: MIT Press, 2018.

[2] Mnih V, Kavukcuoglu K, Silver D, et al. Human-level control through deep reinforcement learning[J]. Nature, 2015, 518(7540): 529-533.

[3] Schultz W, Dayan P, Montague P R. A neural substrate of prediction and reward[J]. Science, 1997, 275(5306): 1593-1599.

[4] Watkins C J C H, Dayan P. Q-Learning[J]. Machine Learning, 1992, 8(3-4): 279-292.

[5] Silver D, Huang A, Maddison C J, et al. Mastering the game of Go with deep neural networks and tree search[J]. Nature, 2016, 529(7587): 484-489.

[6] Bellman R. Dynamic Programming[M]. Princeton: Princeton University Press, 1957.

[7] Bertsekas D P. Reinforcement Learning and Optimal Control[M]. Belmont: Athena Scientific, 2019.

[8] Wei S, Yang H, Song J, et al. A wavelet-neural network hybrid modelling approach for estimating and predicting river monthly flows[J]. Hydrological Sciences Journal, 2013, 58(2): 374-389.

[9] Castelletti A, Galelli S, Restelli M, et al. Tree-based reinforcement learning for optimal water reservoir operation[J]. Water Resources Research, 2010, 46(9): W09507.

[10] Xu W, Zhang Y, Xia J, et al. Deep reinforcement learning for cascade reservoir operation considering inflow forecasts[J]. Journal of Hydrology, 2022, 614: 128538.

[11] 雷晓辉, 龙岩, 许慧敏, 等. 水系统控制论：提出背景、技术框架与研究范式[J]. 南水北调与水利科技(中英文), 2025, 23(04): 761-769+904. DOI:10.13476/j.cnki.nsbdqk.2025.0077.

[12] 雷晓辉, 苏承国, 龙岩, 等. 基于无人驾驶理念的下一代自主运行智慧水网架构与关键技术[J]. 南水北调与水利科技(中英文), 2025, 23(04): 778-786. DOI:10.13476/j.cnki.nsbdqk.2025.0079.

[13] 雷晓辉, 张峥, 苏承国, 等. 自主运行智能水网的在环测试体系[J]. 南水北调与水利科技(中英文), 2025, 23(04): 787-793. DOI:10.13476/j.cnki.nsbdqk.2025.0080.

[14] Camacho E F, Bordons C. Model Predictive Control[M]. 2nd ed. London: Springer, 2007.

[15] Van Overloop P J. Model Predictive Control on Open Water Systems[D]. Delft: Delft University of Technology, 2006.

[16] Åström K J, Murray R M. Feedback Systems: An Introduction for Scientists and Engineers[M]. 2nd ed. Princeton: Princeton University Press, 2021.

[17] ASCE Task Committee on Canal Automation. Canal Automation for Irrigation Systems (MOP 131)[M]. Reston, VA: ASCE, 2014.
