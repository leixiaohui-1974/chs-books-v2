#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第7章 深度Q网络(DQN)在水库离散闸门控制中的应用
============================================

问题背景:
    水库调度是水利工程中的核心问题之一。水库管理者需要在防洪安全、供水保障和
    生态需水等多重目标之间寻求平衡。传统的水库调度规则(如分级调度图)依赖于
    专家经验，难以适应复杂多变的水文情势。

    本案例考虑一个典型的防洪-供水水库，库容面积 As=5×10^6 m²，防洪限制水位
    H_flood=150m，死水位 H_dead=130m，目标水位 H_target=145m。水库通过闸门
    控制出库流量，闸门开度调整为离散动作(7档)，每个时间步长dt=3600s(1小时)，
    模拟周期为30天(720个时间步)。入库流量包含一个洪峰过程和随机扰动。

    强化学习agent需要学习：在洪水来临时适度预泄、洪峰期加大泄量、洪水退去后
    恢复蓄水的最优策略。

解题思路:
    1. 环境建模: 将水库系统建模为Gym风格的强化学习环境(ReservoirEnv)
       - 状态空间: [归一化水位, 归一化入流, 归一化闸门开度, 归一化时间步]
       - 动作空间: 7个离散动作 [-10%, -5%, -2%, 0, +2%, +5%, +10%]
       - 奖励函数: 综合考虑防洪安全、供水保障、目标追踪和操作平稳性

    2. DQN算法:
       - 使用两层全连接网络(64单元)近似Q函数
       - 经验回放缓冲区(容量10000)打破样本相关性
       - 目标网络(每100步更新)稳定训练过程
       - epsilon-greedy策略实现探索-利用平衡，epsilon指数衰减

    3. 安全层: 在agent输出动作后增加安全检查，防止水位超出安全范围

    4. 训练与评估: 训练200个episode，记录奖励曲线，展示最终学到的控制策略

依赖: numpy, torch, matplotlib
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# 中文字体配置
# ============================================================
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 随机种子设置（保证可复现性）
# ============================================================
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)
random.seed(SEED)


# ============================================================
# 水库环境类 (离散动作空间)
# ============================================================
class ReservoirEnv:
    """
    水库离散闸门控制环境

    参数说明:
        As       : 库容面积 (m²)，用于水量平衡计算 dH = (Q_in - Q_out)*dt / As
        H_flood  : 防洪限制水位 (m)，超过此水位将受到严重惩罚
        H_dead   : 死水位 (m)，低于此水位无法正常供水
        H_target : 目标运行水位 (m)，正常运行期望维持的水位
        Q_max    : 最大泄流能力 (m³/s)
        dt       : 时间步长 (s)，1小时
        T_max    : 最大时间步数，720步 = 30天
    """

    def __init__(self):
        self.As = 5e6          # 库容面积 m²
        self.H_flood = 150.0   # 防洪限制水位 m
        self.H_dead = 130.0    # 死水位 m
        self.H_target = 145.0  # 目标水位 m
        self.Q_max = 2000.0    # 最大泄流 m³/s
        self.dt = 3600.0       # 时间步长 s (1小时)
        self.T_max = 720       # 总步数 (30天)

        # 7个离散动作: 闸门开度调整量 (相对于当前开度的百分比变化)
        self.action_deltas = np.array([-0.10, -0.05, -0.02, 0.0, 0.02, 0.05, 0.10])
        self.n_actions = len(self.action_deltas)

        # 状态空间维度: [归一化水位, 归一化入流, 闸门开度, 归一化时间]
        self.state_dim = 4

    def reset(self):
        """重置环境到初始状态"""
        self.H = 140.0              # 初始水位 m
        self.gate = 0.3             # 初始闸门开度 (0~1)
        self.t = 0                  # 当前时间步
        self.prev_gate = self.gate  # 上一步闸门开度（用于计算平稳性）
        return self._get_state()

    def _get_inflow(self, t):
        """
        计算t时刻的入库流量

        入流模型: 基流(300 m³/s) + 洪峰(高斯型，峰值800 m³/s，中心在第360步即第15天)
                  + 随机扰动(±30 m³/s)
        """
        base = 300.0
        # 高斯型洪峰: 峰值800, 中心t=360(第15天), 标准差48(约2天)
        flood = 800.0 * np.exp(-0.5 * ((t - 360) / 48.0) ** 2)
        noise = np.random.normal(0, 30)
        return max(0, base + flood + noise)

    def _get_state(self):
        """
        构造归一化状态向量

        归一化策略:
        - 水位: (H - H_dead) / (H_flood - H_dead)，映射到[0,1]
        - 入流: Q_in / Q_max，映射到约[0,1]
        - 闸门开度: 已经在[0,1]范围
        - 时间: t / T_max，映射到[0,1]
        """
        h_norm = (self.H - self.H_dead) / (self.H_flood - self.H_dead)
        q_in = self._get_inflow(self.t)
        q_norm = q_in / self.Q_max
        t_norm = self.t / self.T_max
        return np.array([h_norm, q_norm, self.gate, t_norm], dtype=np.float32)

    def _safety_layer(self, gate_new):
        """
        安全层: 对agent输出的动作进行安全约束

        规则:
        1. 闸门开度限制在[0, 1]
        2. 水位接近防洪限制时，强制增大开度
        3. 水位接近死水位时，强制减小开度
        """
        # 基本约束: 闸门开度在[0,1]之间
        gate_new = np.clip(gate_new, 0.0, 1.0)

        # 防洪安全: 水位超过148m时，强制闸门开度不低于一定值
        if self.H > 148.0:
            min_gate = 0.5 + (self.H - 148.0) / (self.H_flood - 148.0) * 0.5
            gate_new = max(gate_new, min_gate)

        # 死水位保护: 水位低于132m时，限制最大出流
        if self.H < 132.0:
            max_gate = 0.2 * (self.H - self.H_dead) / 2.0
            gate_new = min(gate_new, max(0.0, max_gate))

        return gate_new

    def step(self, action_idx):
        """
        执行一步环境转移

        参数:
            action_idx: 动作索引 (0-6)

        返回:
            state: 新的状态向量
            reward: 即时奖励
            done: 是否终止
            info: 附加信息字典
        """
        # 1. 解析动作: 将离散索引转为闸门开度变化量
        delta = self.action_deltas[action_idx]
        gate_new = self.gate + delta

        # 2. 安全层处理
        gate_new = self._safety_layer(gate_new)

        # 3. 计算出库流量 (闸门开度 × 最大泄流能力)
        Q_out = gate_new * self.Q_max

        # 4. 计算入库流量
        Q_in = self._get_inflow(self.t)

        # 5. 水量平衡: dH = (Q_in - Q_out) * dt / As
        dH = (Q_in - Q_out) * self.dt / self.As
        self.H += dH

        # 6. 水位硬约束 (物理极限)
        self.H = np.clip(self.H, self.H_dead - 1, self.H_flood + 2)

        # 7. 计算复合奖励
        reward = self._compute_reward(Q_in, Q_out, gate_new)

        # 8. 更新状态
        self.prev_gate = self.gate
        self.gate = gate_new
        self.t += 1

        # 9. 判断是否终止
        done = self.t >= self.T_max

        info = {
            'H': self.H,
            'Q_in': Q_in,
            'Q_out': Q_out,
            'gate': self.gate
        }

        return self._get_state(), reward, done, info

    def _compute_reward(self, Q_in, Q_out, gate_new):
        """
        复合奖励函数设计

        四个分量:
        1. 防洪惩罚: 水位超过H_flood时给予大幅惩罚
        2. 供水惩罚: 水位低于H_dead时给予惩罚
        3. 目标追踪: 鼓励水位接近目标水位H_target
        4. 操作平稳: 惩罚闸门开度的剧烈变化
        """
        reward = 0.0

        # 分量1: 防洪惩罚 (水位超限时惩罚，严重超限加倍惩罚)
        if self.H > self.H_flood:
            reward -= 10.0 * (self.H - self.H_flood)
        elif self.H > self.H_flood - 2:
            # 接近防洪水位时给予警告性惩罚
            reward -= 2.0 * (self.H - (self.H_flood - 2))

        # 分量2: 死水位惩罚
        if self.H < self.H_dead:
            reward -= 10.0 * (self.H_dead - self.H)
        elif self.H < self.H_dead + 2:
            reward -= 2.0 * ((self.H_dead + 2) - self.H)

        # 分量3: 目标水位追踪 (水位越接近目标，奖励越高)
        dist = abs(self.H - self.H_target)
        reward -= 0.1 * dist  # 距离惩罚

        # 分量4: 操作平稳性 (惩罚闸门开度的剧烈变化)
        gate_change = abs(gate_new - self.prev_gate)
        reward -= 1.0 * gate_change

        # 基础生存奖励 (鼓励agent存活更久)
        reward += 0.1

        return reward


# ============================================================
# DQN网络结构
# ============================================================
class DQNetwork(nn.Module):
    """
    深度Q网络

    结构: 输入(4) -> 全连接(64) -> ReLU -> 全连接(64) -> ReLU -> 输出(7)

    输入: 4维状态向量 [归一化水位, 归一化入流, 闸门开度, 归一化时间]
    输出: 7个动作对应的Q值
    """

    def __init__(self, state_dim, n_actions):
        super(DQNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),   # 第一隐藏层: 64个神经元
            nn.ReLU(),
            nn.Linear(64, 64),          # 第二隐藏层: 64个神经元
            nn.ReLU(),
            nn.Linear(64, n_actions)    # 输出层: 每个动作一个Q值
        )

    def forward(self, x):
        return self.net(x)


# ============================================================
# 经验回放缓冲区
# ============================================================
class ReplayBuffer:
    """
    经验回放缓冲区

    功能: 存储(s, a, r, s', done)转移元组，支持随机采样
    作用: 打破样本间的时序相关性，提高训练稳定性
    """

    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """存储一条经验"""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        """随机采样一批经验"""
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards, dtype=np.float32),
            np.array(next_states),
            np.array(dones, dtype=np.float32)
        )

    def __len__(self):
        return len(self.buffer)


# ============================================================
# DQN智能体
# ============================================================
class DQNAgent:
    """
    DQN智能体

    核心机制:
    1. epsilon-greedy探索策略（epsilon从1.0指数衰减到0.01）
    2. 经验回放（打破样本相关性）
    3. 目标网络（每100步硬更新，稳定Q值估计）
    """

    def __init__(self, state_dim, n_actions, lr=1e-3, gamma=0.99,
                 eps_start=1.0, eps_end=0.01, eps_decay=0.995,
                 buffer_size=10000, batch_size=64,
                 target_update=100):
        self.state_dim = state_dim
        self.n_actions = n_actions
        self.gamma = gamma                # 折扣因子
        self.epsilon = eps_start          # 当前探索率
        self.eps_end = eps_end            # 最小探索率
        self.eps_decay = eps_decay        # 探索率衰减系数
        self.batch_size = batch_size
        self.target_update = target_update
        self.learn_step = 0               # 学习步数计数器

        # 在线网络: 用于选择动作和计算当前Q值
        self.policy_net = DQNetwork(state_dim, n_actions)
        # 目标网络: 用于计算目标Q值，定期从在线网络复制参数
        self.target_net = DQNetwork(state_dim, n_actions)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # 目标网络不需要梯度

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(buffer_size)

    def select_action(self, state):
        """
        epsilon-greedy动作选择

        以epsilon概率随机探索，以(1-epsilon)概率选择Q值最大的动作
        """
        if random.random() < self.epsilon:
            return random.randrange(self.n_actions)
        else:
            with torch.no_grad():
                state_t = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.policy_net(state_t)
                return q_values.argmax(dim=1).item()

    def learn(self):
        """
        从经验回放缓冲区采样并更新网络

        DQN更新公式:
        target = r + gamma * max_a' Q_target(s', a') * (1 - done)
        loss = MSE(Q_online(s, a), target)
        """
        if len(self.buffer) < self.batch_size:
            return

        # 从缓冲区随机采样
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)

        # 转换为PyTorch张量
        states_t = torch.FloatTensor(states)
        actions_t = torch.LongTensor(actions).unsqueeze(1)
        rewards_t = torch.FloatTensor(rewards).unsqueeze(1)
        next_states_t = torch.FloatTensor(next_states)
        dones_t = torch.FloatTensor(dones).unsqueeze(1)

        # 计算当前Q值: Q(s, a) — 只取所执行动作对应的Q值
        current_q = self.policy_net(states_t).gather(1, actions_t)

        # 计算目标Q值: r + gamma * max_a' Q_target(s', a')
        with torch.no_grad():
            next_q = self.target_net(next_states_t).max(1, keepdim=True)[0]
            target_q = rewards_t + self.gamma * next_q * (1 - dones_t)

        # 计算损失并更新
        loss = nn.MSELoss()(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        # 梯度裁剪: 防止梯度爆炸
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # 更新学习步数并定期同步目标网络
        self.learn_step += 1
        if self.learn_step % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        """指数衰减探索率"""
        self.epsilon = max(self.eps_end, self.epsilon * self.eps_decay)


# ============================================================
# 训练函数
# ============================================================
def train_dqn(n_episodes=200):
    """
    DQN训练主循环

    参数:
        n_episodes: 训练轮数

    返回:
        agent: 训练好的DQN agent
        episode_rewards: 每轮的累计奖励列表
        env: 环境实例
    """
    env = ReservoirEnv()
    agent = DQNAgent(
        state_dim=env.state_dim,
        n_actions=env.n_actions,
        lr=1e-3,
        gamma=0.99,
        eps_start=1.0,
        eps_end=0.01,
        eps_decay=0.995,
        buffer_size=10000,
        batch_size=64,
        target_update=100
    )

    episode_rewards = []

    for ep in range(n_episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            # 选择动作
            action = agent.select_action(state)
            # 执行动作
            next_state, reward, done, info = env.step(action)
            # 存入经验回放
            agent.buffer.push(state, action, reward, next_state, done)
            # 学习
            agent.learn()
            # 状态转移
            state = next_state
            total_reward += reward

        # 衰减探索率
        agent.decay_epsilon()
        episode_rewards.append(total_reward)

        # 每20轮打印进度
        if (ep + 1) % 20 == 0:
            avg_reward = np.mean(episode_rewards[-20:])
            print(f"  轮次 {ep+1}/{n_episodes}, "
                  f"平均奖励(近20轮): {avg_reward:.1f}, "
                  f"epsilon: {agent.epsilon:.3f}")

    return agent, episode_rewards, env


# ============================================================
# 评估函数: 用训练好的agent跑一个完整episode
# ============================================================
def evaluate(agent, env):
    """
    评估训练好的策略

    返回:
        water_levels: 水位时间序列
        gate_openings: 闸门开度时间序列
        inflows: 入库流量时间序列
        outflows: 出库流量时间序列
    """
    state = env.reset()
    agent.epsilon = 0.0  # 评估时不探索

    water_levels = [env.H]
    gate_openings = [env.gate]
    inflows = []
    outflows = []

    done = False
    while not done:
        action = agent.select_action(state)
        state, reward, done, info = env.step(action)
        water_levels.append(info['H'])
        gate_openings.append(info['gate'])
        inflows.append(info['Q_in'])
        outflows.append(info['Q_out'])

    return water_levels, gate_openings, inflows, outflows


# ============================================================
# 绘图函数
# ============================================================
def plot_results(episode_rewards, water_levels, gate_openings, save_path):
    """
    绘制训练结果图 (2个子图)

    子图1: 训练奖励曲线（含平滑曲线）
    子图2: 最终episode的水位和闸门开度变化
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ---- 子图1: 训练奖励曲线 ----
    ax1 = axes[0]
    ax1.plot(episode_rewards, alpha=0.3, color='steelblue', label='每轮奖励')

    # 滑动平均平滑 (窗口=20)
    window = 20
    if len(episode_rewards) >= window:
        smoothed = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
        ax1.plot(range(window-1, len(episode_rewards)), smoothed,
                 color='darkblue', linewidth=2, label=f'滑动平均({window}轮)')

    ax1.set_xlabel('训练轮次', fontsize=12)
    ax1.set_ylabel('累计奖励', fontsize=12)
    ax1.set_title('DQN训练奖励曲线', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # ---- 子图2: 最终episode水位与闸门开度 ----
    ax2 = axes[1]
    hours = np.arange(len(water_levels))
    days = hours / 24.0

    # 水位曲线（左纵轴）
    color_h = 'royalblue'
    ax2.plot(days, water_levels, color=color_h, linewidth=1.5, label='水位')
    ax2.axhline(y=150, color='red', linestyle='--', linewidth=1, alpha=0.7, label='防洪限制水位')
    ax2.axhline(y=145, color='green', linestyle='--', linewidth=1, alpha=0.7, label='目标水位')
    ax2.axhline(y=130, color='orange', linestyle='--', linewidth=1, alpha=0.7, label='死水位')
    ax2.set_xlabel('时间 (天)', fontsize=12)
    ax2.set_ylabel('水位 (m)', fontsize=12, color=color_h)
    ax2.tick_params(axis='y', labelcolor=color_h)

    # 闸门开度（右纵轴）
    ax2b = ax2.twinx()
    color_g = 'darkorange'
    ax2b.plot(days, gate_openings, color=color_g, linewidth=1.2, alpha=0.7, label='闸门开度')
    ax2b.set_ylabel('闸门开度', fontsize=12, color=color_g)
    ax2b.tick_params(axis='y', labelcolor=color_g)
    ax2b.set_ylim(-0.05, 1.05)

    ax2.set_title('DQN控制效果 (最终轮次)', fontsize=13, fontweight='bold')

    # 合并图例
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='upper left')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n  图片已保存: {save_path}")


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    print("=" * 70)
    print("第7章 DQN水库离散闸门控制")
    print("=" * 70)

    # 创建输出目录
    fig_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    # 训练
    print("\n[1] 开始DQN训练 (200轮)...")
    agent, episode_rewards, env = train_dqn(n_episodes=200)

    # 评估
    print("\n[2] 评估训练后的策略...")
    water_levels, gate_openings, inflows, outflows = evaluate(agent, env)

    # 绘图
    save_path = os.path.join(fig_dir, 'ch07_dqn_reservoir.png')
    plot_results(episode_rewards, water_levels, gate_openings, save_path)

    # 打印结论
    print("\n" + "=" * 70)
    print("结论与建议")
    print("=" * 70)
    print(f"""
  1. 训练概况:
     - 训练轮数: 200轮，每轮720步（30天模拟期）
     - 初始奖励: {episode_rewards[0]:.1f}
     - 最终奖励(近20轮均值): {np.mean(episode_rewards[-20:]):.1f}
     - 奖励提升比例: {(np.mean(episode_rewards[-20:]) - np.mean(episode_rewards[:20])) / abs(np.mean(episode_rewards[:20])) * 100:.1f}%

  2. 控制效果:
     - 水位范围: [{min(water_levels):.1f}m, {max(water_levels):.1f}m]
     - 是否超过防洪限制(150m): {"是" if max(water_levels) > 150 else "否"}
     - 是否低于死水位(130m): {"是" if min(water_levels) < 130 else "否"}
     - 闸门开度范围: [{min(gate_openings):.2f}, {max(gate_openings):.2f}]

  3. DQN算法特点:
     - 离散动作空间适合闸门档位控制场景
     - 经验回放和目标网络有效提升了训练稳定性
     - 安全层确保了极端工况下的系统安全
     - epsilon指数衰减实现了探索到利用的平滑过渡

  4. 改进建议:
     - 可引入Double DQN减少Q值过估计
     - 可使用Dueling DQN分离状态价值和动作优势
     - 实际应用中应增加更多状态特征（如下游水位、天气预报）
     - 建议结合领域知识设计更精细的奖励函数
""")
