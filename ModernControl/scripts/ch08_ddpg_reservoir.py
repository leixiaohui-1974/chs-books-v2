#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第8章 深度确定性策略梯度(DDPG)在水库连续闸门控制中的应用
======================================================

问题背景:
    在第7章中，我们使用DQN处理了离散动作空间的闸门控制问题。然而，实际水库
    闸门的开度是连续可调的，将其离散化会损失控制精度。DDPG (Deep Deterministic
    Policy Gradient) 是一种适用于连续动作空间的Actor-Critic算法，能够直接输出
    连续的闸门开度调整量。

    本案例使用与第7章相同的水库参数(As=5×10^6 m², H_flood=150m, H_dead=130m,
    H_target=145m)，但动作空间改为连续值[-1, 1]，映射到闸门开度变化量±0.1。
    这使得agent可以进行更精细的闸门调节，理论上能获得更优的控制性能。

解题思路:
    1. 连续动作空间环境: 动作为[-1,1]的连续值，通过线性映射转换为闸门开度变化量

    2. DDPG算法核心组件:
       - Actor网络: 输入状态，输出确定性动作 (tanh激活确保[-1,1])
       - Critic网络: 输入(状态, 动作)对，输出Q值估计
       - 4个网络: Actor/Critic各有online和target版本
       - 软更新(Polyak平均): target参数 = tau*online + (1-tau)*target

    3. 探索机制:
       - 在Actor输出的确定性动作上添加高斯噪声
       - 噪声标准差从0.2逐步衰减，实现探索到利用的过渡

    4. 经验回放: 与DQN类似，使用缓冲区存储转移元组并随机采样

依赖: numpy, torch, matplotlib
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
import copy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# 中文字体配置
# ============================================================
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 随机种子设置
# ============================================================
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)
random.seed(SEED)


# ============================================================
# 水库环境类 (连续动作空间)
# ============================================================
class ReservoirEnvContinuous:
    """
    水库连续闸门控制环境

    与离散版本的主要区别:
    - 动作空间: 连续值 [-1, 1]，映射到闸门开度变化 [-0.1, +0.1]
    - 状态空间: 同离散版，4维归一化向量

    水量平衡方程: dH = (Q_in - Q_out) * dt / As
    其中 Q_out = gate * Q_max
    """

    def __init__(self):
        self.As = 5e6          # 库容面积 m²
        self.H_flood = 150.0   # 防洪限制水位 m
        self.H_dead = 130.0    # 死水位 m
        self.H_target = 145.0  # 目标水位 m
        self.Q_max = 2000.0    # 最大泄流 m³/s
        self.dt = 3600.0       # 时间步长 s
        self.T_max = 720       # 总步数 (30天)
        self.state_dim = 4     # 状态维度
        self.action_dim = 1    # 动作维度 (连续)

    def reset(self):
        """重置环境"""
        self.H = 140.0
        self.gate = 0.3
        self.t = 0
        self.prev_gate = self.gate
        return self._get_state()

    def _get_inflow(self, t):
        """
        入库流量模型

        组成: 基流(300) + 高斯洪峰(峰值800, 中心第15天) + 随机噪声
        """
        base = 300.0
        flood = 800.0 * np.exp(-0.5 * ((t - 360) / 48.0) ** 2)
        noise = np.random.normal(0, 30)
        return max(0, base + flood + noise)

    def _get_state(self):
        """构造归一化状态向量"""
        h_norm = (self.H - self.H_dead) / (self.H_flood - self.H_dead)
        q_in = self._get_inflow(self.t)
        q_norm = q_in / self.Q_max
        t_norm = self.t / self.T_max
        return np.array([h_norm, q_norm, self.gate, t_norm], dtype=np.float32)

    def _safety_layer(self, gate_new):
        """
        安全层约束

        确保在极端水位条件下的系统安全:
        - 高水位时强制加大泄流
        - 低水位时限制出流
        """
        gate_new = np.clip(gate_new, 0.0, 1.0)

        if self.H > 148.0:
            min_gate = 0.5 + (self.H - 148.0) / (self.H_flood - 148.0) * 0.5
            gate_new = max(gate_new, min_gate)

        if self.H < 132.0:
            max_gate = 0.2 * max(0, (self.H - self.H_dead) / 2.0)
            gate_new = min(gate_new, max(0.0, max_gate))

        return gate_new

    def step(self, action):
        """
        执行一步环境转移

        参数:
            action: 连续动作值 [-1, 1]，映射到闸门变化 [-0.1, +0.1]
        """
        # 连续动作映射: [-1,1] -> [-0.1, +0.1]
        action = np.clip(action, -1.0, 1.0)
        delta = float(action) * 0.1
        gate_new = self.gate + delta

        # 安全层
        gate_new = self._safety_layer(gate_new)

        # 水量平衡
        Q_out = gate_new * self.Q_max
        Q_in = self._get_inflow(self.t)
        dH = (Q_in - Q_out) * self.dt / self.As
        self.H += dH
        self.H = np.clip(self.H, self.H_dead - 1, self.H_flood + 2)

        # 计算奖励
        reward = self._compute_reward(Q_in, Q_out, gate_new)

        # 更新状态
        self.prev_gate = self.gate
        self.gate = gate_new
        self.t += 1
        done = self.t >= self.T_max

        info = {'H': self.H, 'Q_in': Q_in, 'Q_out': Q_out, 'gate': self.gate}
        return self._get_state(), reward, done, info

    def _compute_reward(self, Q_in, Q_out, gate_new):
        """
        复合奖励函数

        与DQN版本相同的四分量设计:
        防洪惩罚 + 死水位惩罚 + 目标追踪 + 操作平稳性
        """
        reward = 0.0

        # 防洪惩罚
        if self.H > self.H_flood:
            reward -= 10.0 * (self.H - self.H_flood)
        elif self.H > self.H_flood - 2:
            reward -= 2.0 * (self.H - (self.H_flood - 2))

        # 死水位惩罚
        if self.H < self.H_dead:
            reward -= 10.0 * (self.H_dead - self.H)
        elif self.H < self.H_dead + 2:
            reward -= 2.0 * ((self.H_dead + 2) - self.H)

        # 目标追踪
        dist = abs(self.H - self.H_target)
        reward -= 0.1 * dist

        # 操作平稳性
        gate_change = abs(gate_new - self.prev_gate)
        reward -= 1.0 * gate_change

        # 基础奖励
        reward += 0.1

        return reward


# ============================================================
# Actor网络 (策略网络)
# ============================================================
class Actor(nn.Module):
    """
    Actor网络 — 确定性策略

    结构: 状态(4) -> FC(64) -> ReLU -> FC(64) -> ReLU -> FC(1) -> tanh
    输出: [-1, 1]的连续动作值

    tanh激活函数确保输出在[-1,1]范围内，对应闸门开度变化[-0.1, +0.1]
    """

    def __init__(self, state_dim, action_dim):
        super(Actor, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
            nn.Tanh()  # 输出限制在[-1, 1]
        )

    def forward(self, state):
        return self.net(state)


# ============================================================
# Critic网络 (价值网络)
# ============================================================
class Critic(nn.Module):
    """
    Critic网络 — Q值估计

    结构: 先分别处理状态和动作，然后在隐藏层拼接
    - 状态 -> FC(64) -> ReLU
    - [状态特征; 动作] -> FC(64) -> ReLU -> FC(1)

    输出: Q(s, a)的估计值
    """

    def __init__(self, state_dim, action_dim):
        super(Critic, self).__init__()
        # 第一层: 处理状态
        self.fc1 = nn.Linear(state_dim, 64)
        # 第二层: 拼接动作后处理
        self.fc2 = nn.Linear(64 + action_dim, 64)
        # 输出层: Q值
        self.fc3 = nn.Linear(64, 1)

    def forward(self, state, action):
        # 状态通过第一层
        x = torch.relu(self.fc1(state))
        # 拼接动作
        x = torch.cat([x, action], dim=1)
        # 通过第二层
        x = torch.relu(self.fc2(x))
        # 输出Q值
        return self.fc3(x)


# ============================================================
# 经验回放缓冲区
# ============================================================
class ReplayBuffer:
    """经验回放缓冲区 (与DQN版本相同)"""

    def __init__(self, capacity=50000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions, dtype=np.float32),
            np.array(rewards, dtype=np.float32),
            np.array(next_states),
            np.array(dones, dtype=np.float32)
        )

    def __len__(self):
        return len(self.buffer)


# ============================================================
# DDPG智能体
# ============================================================
class DDPGAgent:
    """
    DDPG智能体

    核心机制:
    1. Actor-Critic架构: Actor输出动作，Critic评估Q值
    2. 4个网络: Actor_online, Actor_target, Critic_online, Critic_target
    3. 软更新(Polyak平均): 目标网络参数缓慢跟踪在线网络
    4. 高斯探索噪声: 在确定性动作上添加噪声实现探索
    """

    def __init__(self, state_dim, action_dim,
                 actor_lr=1e-4, critic_lr=1e-3,
                 gamma=0.99, tau=0.005,
                 noise_std=0.2, noise_decay=0.999, noise_min=0.01,
                 buffer_size=50000, batch_size=64):

        self.gamma = gamma            # 折扣因子
        self.tau = tau                # 软更新系数
        self.noise_std = noise_std    # 探索噪声标准差
        self.noise_decay = noise_decay
        self.noise_min = noise_min
        self.batch_size = batch_size
        self.action_dim = action_dim

        # 在线Actor和Critic
        self.actor = Actor(state_dim, action_dim)
        self.critic = Critic(state_dim, action_dim)

        # 目标Actor和Critic (深拷贝)
        self.actor_target = copy.deepcopy(self.actor)
        self.critic_target = copy.deepcopy(self.critic)

        # 优化器 (Actor学习率通常比Critic小)
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=actor_lr)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=critic_lr)

        # 经验回放
        self.buffer = ReplayBuffer(buffer_size)

    def select_action(self, state, add_noise=True):
        """
        选择动作

        参数:
            state: 当前状态
            add_noise: 是否添加探索噪声

        确定性策略 + 高斯噪声 实现探索
        """
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0)
            action = self.actor(state_t).cpu().numpy().flatten()

        if add_noise:
            noise = np.random.normal(0, self.noise_std, size=self.action_dim)
            action = action + noise

        # 裁剪到合法范围
        return np.clip(action, -1.0, 1.0)

    def _soft_update(self, target, source):
        """
        软更新目标网络

        Polyak平均: target = tau * source + (1-tau) * target
        tau通常取很小的值(0.005)，使目标网络缓慢变化
        """
        for target_param, source_param in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(
                self.tau * source_param.data + (1 - self.tau) * target_param.data
            )

    def learn(self):
        """
        DDPG学习更新

        Critic更新:
            target = r + gamma * Q_target(s', Actor_target(s'))
            loss_critic = MSE(Q_online(s,a), target)

        Actor更新:
            loss_actor = -mean(Q_online(s, Actor_online(s)))
            即最大化Critic对Actor输出动作的评价
        """
        if len(self.buffer) < self.batch_size:
            return

        # 采样
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)
        states_t = torch.FloatTensor(states)
        actions_t = torch.FloatTensor(actions).unsqueeze(1) if actions.ndim == 1 else torch.FloatTensor(actions)
        rewards_t = torch.FloatTensor(rewards).unsqueeze(1)
        next_states_t = torch.FloatTensor(next_states)
        dones_t = torch.FloatTensor(dones).unsqueeze(1)

        # 确保actions维度正确
        if actions_t.dim() == 1:
            actions_t = actions_t.unsqueeze(1)

        # ---- 更新Critic ----
        with torch.no_grad():
            # 目标Actor给出下一步动作
            next_actions = self.actor_target(next_states_t)
            # 目标Critic评估(s', a')
            target_q = self.critic_target(next_states_t, next_actions)
            # TD目标: r + gamma * Q_target * (1-done)
            y = rewards_t + self.gamma * target_q * (1 - dones_t)

        current_q = self.critic(states_t, actions_t)
        critic_loss = nn.MSELoss()(current_q, y)

        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        nn.utils.clip_grad_norm_(self.critic.parameters(), 1.0)
        self.critic_optimizer.step()

        # ---- 更新Actor ----
        # 策略梯度: 最大化 Q(s, Actor(s))
        pred_actions = self.actor(states_t)
        actor_loss = -self.critic(states_t, pred_actions).mean()

        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        nn.utils.clip_grad_norm_(self.actor.parameters(), 1.0)
        self.actor_optimizer.step()

        # ---- 软更新目标网络 ----
        self._soft_update(self.actor_target, self.actor)
        self._soft_update(self.critic_target, self.critic)

    def decay_noise(self):
        """衰减探索噪声"""
        self.noise_std = max(self.noise_min, self.noise_std * self.noise_decay)


# ============================================================
# 训练函数
# ============================================================
def train_ddpg(n_episodes=200):
    """
    DDPG训练主循环

    返回: agent, episode_rewards, env
    """
    env = ReservoirEnvContinuous()
    agent = DDPGAgent(
        state_dim=env.state_dim,
        action_dim=env.action_dim,
        actor_lr=1e-4,
        critic_lr=1e-3,
        gamma=0.99,
        tau=0.005,
        noise_std=0.2,
        noise_decay=0.999,
        noise_min=0.01,
        buffer_size=50000,
        batch_size=64
    )

    episode_rewards = []

    for ep in range(n_episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            # 选择带噪声的动作
            action = agent.select_action(state, add_noise=True)
            # 执行
            next_state, reward, done, info = env.step(action[0])
            # 存储经验
            agent.buffer.push(state, action, reward, next_state, done)
            # 学习
            agent.learn()
            # 状态转移
            state = next_state
            total_reward += reward

        # 衰减噪声
        agent.decay_noise()
        episode_rewards.append(total_reward)

        if (ep + 1) % 20 == 0:
            avg_reward = np.mean(episode_rewards[-20:])
            print(f"  轮次 {ep+1}/{n_episodes}, "
                  f"平均奖励(近20轮): {avg_reward:.1f}, "
                  f"噪声: {agent.noise_std:.4f}")

    return agent, episode_rewards, env


# ============================================================
# 评估函数
# ============================================================
def evaluate(agent, env):
    """用训练好的策略评估一个完整episode"""
    state = env.reset()
    water_levels = [env.H]
    gate_openings = [env.gate]
    inflows = []
    outflows = []

    done = False
    while not done:
        action = agent.select_action(state, add_noise=False)
        state, reward, done, info = env.step(action[0])
        water_levels.append(info['H'])
        gate_openings.append(info['gate'])
        inflows.append(info['Q_in'])
        outflows.append(info['Q_out'])

    return water_levels, gate_openings, inflows, outflows


# ============================================================
# 绘图函数
# ============================================================
def plot_results(episode_rewards, water_levels, gate_openings, inflows, outflows, save_path):
    """
    绘制DDPG训练结果 (2个子图)

    子图1: 训练奖励曲线（含平滑线）
    子图2: 最终episode的控制性能（水位 + 流量）
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ---- 子图1: 训练奖励曲线 ----
    ax1 = axes[0]
    ax1.plot(episode_rewards, alpha=0.3, color='steelblue', label='每轮奖励')

    window = 20
    if len(episode_rewards) >= window:
        smoothed = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
        ax1.plot(range(window-1, len(episode_rewards)), smoothed,
                 color='darkblue', linewidth=2, label=f'滑动平均({window}轮)')

    ax1.set_xlabel('训练轮次', fontsize=12)
    ax1.set_ylabel('累计奖励', fontsize=12)
    ax1.set_title('DDPG训练奖励曲线', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # ---- 子图2: 控制性能 ----
    ax2 = axes[1]
    hours = np.arange(len(water_levels))
    days = hours / 24.0

    # 水位
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

    ax2.set_title('DDPG连续控制效果 (最终轮次)', fontsize=13, fontweight='bold')

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
    print("第8章 DDPG水库连续闸门控制")
    print("=" * 70)

    # 创建输出目录
    fig_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    # 训练
    print("\n[1] 开始DDPG训练 (200轮)...")
    agent, episode_rewards, env = train_ddpg(n_episodes=200)

    # 评估
    print("\n[2] 评估训练后的策略...")
    water_levels, gate_openings, inflows, outflows = evaluate(agent, env)

    # 绘图
    save_path = os.path.join(fig_dir, 'ch08_ddpg_reservoir.png')
    plot_results(episode_rewards, water_levels, gate_openings, inflows, outflows, save_path)

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

  3. DDPG相较于DQN的优势:
     - 连续动作空间允许更精细的闸门调节
     - 确定性策略+高斯噪声实现高效探索
     - Actor-Critic框架同时学习策略和价值函数
     - 软更新(tau=0.005)比硬更新更平稳

  4. DDPG的局限与改进方向:
     - 对超参数敏感，尤其是噪声参数和学习率比
     - 可引入TD3(Twin Delayed DDPG)减少Q值过估计
     - 可使用参数空间噪声(Parameter Space Noise)替代动作噪声
     - 实际工程中建议与模型预测控制(MPC)结合使用
""")
