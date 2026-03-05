#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第9章 Advantage Actor-Critic (A2C) 水库连续闸门控制
====================================================

问题背景:
    第7章使用DQN处理离散动作空间的闸门控制，第8章使用DDPG处理连续动作空间。
    两者分别属于"纯价值方法"和"确定性策略梯度方法"。本章引入A2C
    (Advantage Actor-Critic)，它是随机策略梯度方法的标准实现形式，
    融合了价值方法的低方差优势和策略方法的连续动作灵活性。

    A2C的核心创新在于：
    1. Actor输出随机策略 π_θ(a|s) = N(μ, σ²)，策略本身的随机性提供
       内生探索能力，无需像DDPG那样额外添加探索噪声；
    2. Critic学习状态价值函数 V_w(s)，通过TD误差 δ_t = R + γV(s') - V(s)
       作为优势函数的无偏估计（第9.4节核心定理），同时驱动Actor和Critic学习；
    3. 熵正则化项鼓励策略保持适度的随机性，防止过早收敛到局部最优。

    本案例使用与前两章相同的水库参数，但采用A2C算法训练300轮，展示
    随机策略在水库调度中的学习过程和最终控制效果。

解题思路:
    1. 环境建模: 与第8章相同的连续动作水库环境，5维状态空间
       [归一化水位, 归一化入流, 归一化出流, 归一化目标, 闸门开度]
       动作为[-1,1]连续值，映射到闸门开度变化±0.1

    2. A2C网络架构:
       - Actor和Critic共享底层特征提取网络（64×64 ReLU）
       - Actor头: 输出高斯分布的均值μ（tanh激活确保[-1,1]）
       - 可学习的对数标准差 log_σ（全局参数，随训练自动调整）
       - Critic头: 输出状态价值V(s)

    3. 训练机制:
       - 在策略(on-policy)学习: 每个episode的数据仅用一次
       - 三项损失函数: Actor损失 + Critic损失 + 熵正则
       - 梯度裁剪防止更新过大

    4. 与DQN/DDPG的对比分析

依赖: numpy, torch, matplotlib
作者: 雷晓辉 教授 | 河北工程大学
"""

import os
import sys
import io

# Windows UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Normal
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


# ============================================================
# 水库环境类（连续动作版，5维状态）
# ============================================================
class ReservoirEnvContinuous:
    """
    水库闸门连续控制环境

    状态空间（5维归一化向量）:
        [0] 归一化水位: (H - H_dead) / (H_flood - H_dead)
        [1] 归一化入流: Q_in / Q_max
        [2] 归一化出流: Q_out / Q_max
        [3] 归一化目标: (H_target - H_dead) / (H_flood - H_dead)
        [4] 当前闸门开度: gate ∈ [0, 1]

    动作空间:
        连续值 a ∈ [-1, 1]，映射到闸门开度变化 Δgate = a × 0.1

    奖励函数:
        r = r_flood + r_supply + r_target + r_smooth
        - 防洪惩罚: -100 × max(0, H - H_flood)²
        - 供水惩罚: -100 × max(0, H_dead - H)²
        - 目标追踪: -0.5 × (H - H_target)²
        - 操作平稳: -5.0 × (gate_new - gate_old)²

    水量平衡:
        ΔH = (Q_in - Q_out) × dt / As
    """

    def __init__(self):
        self.As = 5e6          # 库容面积 m²
        self.H_flood = 150.0   # 防洪限制水位 m
        self.H_dead = 130.0    # 死水位 m
        self.H_target = 145.0  # 目标水位 m
        self.Q_max = 2000.0    # 最大泄流 m³/s
        self.dt = 3600         # 时间步长 s (1小时)

    def reset(self):
        """重置环境，初始水位在目标附近随机扰动"""
        self.H = 145.0 + np.random.randn() * 1.0
        self.gate = 0.3
        self.t = 0
        self.T_max = 720  # 30天

        # 预生成入流过程（含洪峰+随机噪声）
        t = np.arange(self.T_max)
        self.Qin = 300 + 800 * np.exp(-0.5 * ((t - 360) / 48)**2) \
                   + np.random.randn(self.T_max) * 30
        self.Qin = np.clip(self.Qin, 0, 5000)

        return self._state()

    def _state(self):
        """构造5维归一化状态向量"""
        Qin = self.Qin[min(self.t, self.T_max - 1)]
        Qout = self.gate * self.Q_max
        return np.array([
            (self.H - 130) / 30,         # 归一化水位
            Qin / 2000,                   # 归一化入流
            Qout / 2000,                  # 归一化出流
            (self.H_target - 130) / 30,   # 归一化目标
            self.gate                     # 闸门开度
        ], dtype=np.float32)

    def step(self, action):
        """
        执行一步环境转移

        参数:
            action: float, 连续动作值 ∈ [-1, 1]

        返回:
            state: 新状态向量
            reward: 即时奖励
            done: 是否终止
        """
        # 动作映射: [-1,1] → 闸门变化 [-0.1, +0.1]
        delta = float(np.clip(action, -1, 1)) * 0.1
        old_gate = self.gate
        self.gate = np.clip(self.gate + delta, 0, 1)

        # 安全层: 高水位强制加大泄流，低水位限制出流
        if self.H > 148.0:
            min_gate = 0.5 + (self.H - 148.0) / 2.0 * 0.5
            self.gate = max(self.gate, min_gate)
        if self.H < 132.0:
            max_gate = 0.2 * max(0, (self.H - self.H_dead) / 2.0)
            self.gate = min(self.gate, max(0.0, max_gate))

        # 水量平衡
        Qin = self.Qin[min(self.t, self.T_max - 1)]
        Qout = self.gate * self.Q_max
        self.H += (Qin - Qout) * self.dt / self.As

        # 物理约束
        self.H = np.clip(self.H, self.H_dead - 1, self.H_flood + 2)

        # 复合奖励函数
        r_flood = -100.0 * max(0, self.H - self.H_flood)**2
        r_supply = -100.0 * max(0, self.H_dead - self.H)**2
        r_target = -0.5 * (self.H - self.H_target)**2
        r_smooth = -5.0 * (self.gate - old_gate)**2
        reward = r_flood + r_supply + r_target + r_smooth

        self.t += 1
        done = (self.t >= self.T_max) or (self.H > 160) or (self.H < 125)

        return self._state(), reward, done


# ============================================================
# Actor-Critic 共享网络
# ============================================================
class ActorCritic(nn.Module):
    """
    Actor-Critic共享特征提取网络

    架构:
        共享层: 输入(5) → FC(64) → ReLU → FC(64) → ReLU
        Actor头: FC(64) → FC(1) → tanh → 高斯分布均值 μ ∈ [-1, 1]
        Critic头: FC(64) → FC(1) → 状态价值 V(s)

    可学习参数:
        actor_log_std: 高斯分布的对数标准差（全局共享）

    设计理由:
        共享底层特征层减少参数量、加速收敛。
        Actor和Critic从同一组学到的特征中分别提取决策和评估信息。
    """

    def __init__(self, n_state, n_action):
        super().__init__()
        # 共享特征层
        self.shared = nn.Sequential(
            nn.Linear(n_state, 64), nn.ReLU(),
            nn.Linear(64, 64), nn.ReLU()
        )
        # Actor头: 输出高斯分布的均值
        self.actor_mean = nn.Linear(64, n_action)
        # 可学习的对数标准差（初始为0 → σ=1.0，随训练自动调整）
        self.actor_log_std = nn.Parameter(torch.zeros(n_action))
        # Critic头: 输出状态价值 V(s)
        self.critic = nn.Linear(64, 1)

    def forward(self, s):
        """
        前向传播

        返回:
            mean: 策略均值 μ(s) ∈ [-1, 1]
            std:  策略标准差 σ（对所有状态相同）
            value: 状态价值 V(s)
        """
        feat = self.shared(s)
        mean = torch.tanh(self.actor_mean(feat))
        std = self.actor_log_std.exp().expand_as(mean)
        value = self.critic(feat)
        return mean, std, value


# ============================================================
# A2C 智能体
# ============================================================
class A2CAgent:
    """
    Advantage Actor-Critic (A2C) 智能体

    核心机制:
    1. 在策略(on-policy)学习: 用当前策略收集数据，更新后丢弃
    2. 优势函数: A(s,a) ≈ δ_t = R + γV(s') - V(s) (TD误差)
    3. 三项损失:
       - Actor损失: -E[log π(a|s) × A(s,a)] (策略梯度)
       - Critic损失: MSE(V(s), G_t) (价值预测)
       - 熵正则: -α × H(π) (鼓励探索)
    4. 共享优化器: Actor和Critic共享一个Adam优化器

    超参数:
        gamma: 折扣因子 (0.99)
        lr: 学习率 (3×10⁻⁴)
        entropy_coeff: 熵正则系数 (0.01)
    """

    def __init__(self, n_state=5, n_action=1, lr=3e-4,
                 gamma=0.99, entropy_coeff=0.01):
        self.gamma = gamma
        self.entropy_coeff = entropy_coeff
        self.net = ActorCritic(n_state, n_action)
        self.optimizer = optim.Adam(self.net.parameters(), lr=lr)

    def select_action(self, state):
        """
        从随机策略中采样动作

        策略: π(a|s) = N(μ(s), σ²)
        采样: a ~ N(μ, σ²)

        返回:
            action: 采样的动作值
            log_prob: 该动作的对数概率 (用于策略梯度)
            value: 状态价值估计 V(s) (用于优势计算)
        """
        s = torch.FloatTensor(state).unsqueeze(0)
        mean, std, value = self.net(s)
        dist = Normal(mean, std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=-1)
        return (action.squeeze(0).detach().numpy(),
                log_prob, value.squeeze())

    def select_action_deterministic(self, state):
        """
        确定性动作选择（用于评估阶段）

        直接使用策略均值 μ(s)，不添加随机性
        """
        s = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            mean, _, _ = self.net(s)
        return mean.squeeze(0).numpy()

    def update(self, rewards, log_probs, values, dones):
        """
        基于收集的完整episode数据进行A2C更新

        步骤:
        1. 反向计算折扣回报 G_t = R_t + γR_{t+1} + γ²R_{t+2} + ...
        2. 计算优势函数 A_t = G_t - V(s_t)
        3. 计算三项损失并反向传播

        参数:
            rewards: 每步奖励列表
            log_probs: 每步动作的对数概率列表
            values: 每步状态价值估计列表
            dones: 每步终止标志列表
        """
        # 反向计算折扣回报
        returns = []
        R = 0
        for r, d in zip(reversed(rewards), reversed(dones)):
            R = r + self.gamma * R * (1 - d)
            returns.insert(0, R)

        returns = torch.FloatTensor(returns)
        log_probs = torch.stack(log_probs)
        values = torch.stack(values)

        # 优势函数 = 折扣回报 - 价值估计
        # 这是TD误差的多步形式: A_t ≈ G_t - V(s_t)
        advantages = returns - values.detach()

        # --- Actor损失 ---
        # 策略梯度: -E[log π(a|s) × A(s,a)]
        # 取负号是因为优化器做梯度下降（我们需要梯度上升）
        actor_loss = -(log_probs * advantages).mean()

        # --- Critic损失 ---
        # 价值预测误差: MSE(V(s), G_t)
        critic_loss = nn.MSELoss()(values, returns)

        # --- 熵正则化 ---
        # 鼓励策略保持随机性，防止过早收敛
        # 高斯分布的熵: H(N(μ,σ²)) = 0.5 × ln(2πeσ²)
        std = self.net.actor_log_std.exp()
        entropy = Normal(torch.zeros_like(std), std).entropy().mean()

        # --- 总损失 ---
        # actor_loss: 最大化优势加权的对数概率
        # 0.5 × critic_loss: 价值函数拟合（系数0.5降低其对共享层的梯度影响）
        # -entropy_coeff × entropy: 鼓励探索
        loss = actor_loss + 0.5 * critic_loss - self.entropy_coeff * entropy

        self.optimizer.zero_grad()
        loss.backward()
        # 梯度裁剪防止更新过大
        nn.utils.clip_grad_norm_(self.net.parameters(), 0.5)
        self.optimizer.step()

        return actor_loss.item(), critic_loss.item()


# ============================================================
# 训练函数
# ============================================================
def train_a2c(n_episodes=300):
    """
    A2C训练主循环

    每个episode:
    1. 重置环境，生成新的入流过程
    2. Actor与环境交互，收集完整轨迹
    3. 用收集的数据计算折扣回报和优势函数
    4. 更新Actor和Critic（在策略，数据用完即弃）

    参数:
        n_episodes: 训练轮数

    返回:
        agent: 训练好的A2C智能体
        episode_rewards: 每轮累计奖励列表
        actor_losses: Actor损失记录
        critic_losses: Critic损失记录
    """
    env = ReservoirEnvContinuous()
    agent = A2CAgent(n_state=5, n_action=1, lr=3e-4,
                     gamma=0.99, entropy_coeff=0.01)

    episode_rewards = []
    actor_losses = []
    critic_losses = []

    for ep in range(n_episodes):
        state = env.reset()
        total_reward = 0
        ep_rewards, ep_log_probs, ep_values, ep_dones = [], [], [], []

        while True:
            # Actor采样动作
            action, log_prob, value = agent.select_action(state)

            # 执行动作
            next_state, reward, done = env.step(action)

            # 记录轨迹数据
            ep_rewards.append(reward)
            ep_log_probs.append(log_prob)
            ep_values.append(value)
            ep_dones.append(float(done))

            state = next_state
            total_reward += reward

            if done:
                break

        # 每个episode结束后更新网络
        a_loss, c_loss = agent.update(ep_rewards, ep_log_probs, ep_values, ep_dones)
        episode_rewards.append(total_reward)
        actor_losses.append(a_loss)
        critic_losses.append(c_loss)

        # 每50轮打印进度
        if (ep + 1) % 50 == 0:
            avg = np.mean(episode_rewards[-50:])
            std_sigma = agent.net.actor_log_std.exp().item()
            print(f"  轮次 {ep+1}/{n_episodes}, "
                  f"近50轮平均奖励: {avg:.1f}, "
                  f"策略σ: {std_sigma:.4f}")

    return agent, episode_rewards, actor_losses, critic_losses


# ============================================================
# 评估函数
# ============================================================
def evaluate(agent, n_eval=1):
    """
    用训练好的策略运行评估episode

    评估时使用确定性策略（取均值μ，不添加随机性），
    这是A2C/PPO的标准部署方式。

    返回:
        water_levels: 水位时间序列
        gate_openings: 闸门开度时间序列
        inflows: 入库流量时间序列
        outflows: 出库流量时间序列
        total_reward: 累计奖励
    """
    env = ReservoirEnvContinuous()
    # 固定入流种子以便复现
    np.random.seed(123)
    state = env.reset()

    water_levels = [env.H]
    gate_openings = [env.gate]
    inflows = []
    outflows = []
    total_reward = 0

    done = False
    while not done:
        # 评估时使用确定性策略
        action = agent.select_action_deterministic(state)
        state, reward, done = env.step(action)

        water_levels.append(env.H)
        gate_openings.append(env.gate)
        Qin = env.Qin[min(env.t - 1, env.T_max - 1)]
        inflows.append(Qin)
        outflows.append(env.gate * env.Q_max)
        total_reward += reward

    return water_levels, gate_openings, inflows, outflows, total_reward


# ============================================================
# 绘图函数
# ============================================================
def plot_results(episode_rewards, water_levels, gate_openings,
                 inflows, outflows, save_path):
    """
    绘制A2C训练结果四子图

    子图1(左上): 训练奖励曲线（含平滑线）
    子图2(右上): 水位与闸门开度控制效果
    子图3(左下): 入流与出流对比
    子图4(右下): DQN vs DDPG vs A2C 方法对比表
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle('第9章 A2C水库连续闸门控制', fontsize=16, fontweight='bold')

    # ---- 子图1: 训练奖励曲线 ----
    ax1 = axes[0, 0]
    ax1.plot(episode_rewards, alpha=0.3, color='steelblue', label='每轮奖励')

    window = 30
    if len(episode_rewards) >= window:
        smoothed = np.convolve(episode_rewards,
                               np.ones(window) / window, mode='valid')
        ax1.plot(range(window - 1, len(episode_rewards)), smoothed,
                 color='darkblue', linewidth=2, label=f'滑动平均({window}轮)')

    ax1.set_xlabel('训练轮次', fontsize=12)
    ax1.set_ylabel('累计奖励', fontsize=12)
    ax1.set_title('(a) A2C训练奖励曲线', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # ---- 子图2: 水位与闸门开度 ----
    ax2 = axes[0, 1]
    hours = np.arange(len(water_levels))
    days = hours / 24.0

    # 水位（左纵轴）
    color_h = 'royalblue'
    ax2.plot(days, water_levels, color=color_h, linewidth=1.5, label='水位')
    ax2.axhline(y=150, color='red', linestyle='--', linewidth=1,
                alpha=0.7, label='防洪限制水位')
    ax2.axhline(y=145, color='green', linestyle='--', linewidth=1,
                alpha=0.7, label='目标水位')
    ax2.axhline(y=130, color='orange', linestyle='--', linewidth=1,
                alpha=0.7, label='死水位')
    ax2.set_xlabel('时间 (天)', fontsize=12)
    ax2.set_ylabel('水位 (m)', fontsize=12, color=color_h)
    ax2.tick_params(axis='y', labelcolor=color_h)

    # 闸门开度（右纵轴）
    ax2b = ax2.twinx()
    color_g = 'darkorange'
    ax2b.plot(days, gate_openings, color=color_g, linewidth=1.2,
              alpha=0.7, label='闸门开度')
    ax2b.set_ylabel('闸门开度', fontsize=12, color=color_g)
    ax2b.tick_params(axis='y', labelcolor=color_g)
    ax2b.set_ylim(-0.05, 1.05)

    ax2.set_title('(b) A2C控制效果（评估轮次）', fontsize=13, fontweight='bold')

    # 合并图例
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc='upper left')
    ax2.grid(True, alpha=0.3)

    # ---- 子图3: 入流与出流对比 ----
    ax3 = axes[1, 0]
    days_flow = np.arange(len(inflows)) / 24.0

    ax3.fill_between(days_flow, 0, inflows, alpha=0.2, color='steelblue')
    ax3.plot(days_flow, inflows, 'b-', linewidth=1.2, label='入库流量 $Q_{in}$')
    ax3.plot(days_flow, outflows, 'r-', linewidth=1.5, label='出库流量 $Q_{out}$')

    # 标注洪峰
    peak_idx = np.argmax(inflows)
    ax3.annotate(f'洪峰: {inflows[peak_idx]:.0f} m³/s',
                 xy=(days_flow[peak_idx], inflows[peak_idx]),
                 xytext=(days_flow[peak_idx] + 2, inflows[peak_idx] - 100),
                 arrowprops=dict(arrowstyle='->', color='darkblue'),
                 fontsize=10, color='darkblue')

    ax3.set_xlabel('时间 (天)', fontsize=12)
    ax3.set_ylabel('流量 (m³/s)', fontsize=12)
    ax3.set_title('(c) 入流与出流对比', fontsize=13, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(bottom=0)

    # ---- 子图4: 三种方法对比表 ----
    ax4 = axes[1, 1]
    ax4.axis('off')

    table_data = [
        ['特征', 'DQN (ch07)', 'DDPG (ch08)', 'A2C (ch09)'],
        ['动作空间', '离散(7档)', '连续', '连续'],
        ['策略类型', '隐式(argmax Q)', '确定性μ(s)', '随机π(a|s)'],
        ['探索方式', 'ε-greedy', '外加噪声', '策略本身随机性'],
        ['数据利用', '离策略(经验回放)', '离策略(经验回放)', '在策略(用完即弃)'],
        ['网络数量', '2(在线+目标)', '4(Actor+Critic×2)', '1(共享网络)'],
        ['训练稳定性', '中等', '较低(超参敏感)', '较高'],
        ['样本效率', '高', '较高', '较低'],
    ]

    table = ax4.table(
        cellText=table_data[1:],
        colLabels=table_data[0],
        cellLoc='center',
        loc='center',
        colWidths=[0.22, 0.26, 0.26, 0.26]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.8)

    # 表头样式
    for j in range(4):
        table[0, j].set_facecolor('#2E75B6')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # 数据行交替颜色
    for i in range(1, 8):
        color = '#D6E4F0' if i % 2 == 1 else '#FFFFFF'
        for j in range(4):
            table[i, j].set_facecolor(color)

    ax4.set_title('(d) DQN vs DDPG vs A2C 方法对比',
                  fontsize=13, fontweight='bold', pad=20)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # 保存图片
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n  图片已保存: {save_path}")


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    print("=" * 70)
    print("  第9章 A2C (Advantage Actor-Critic) 水库连续闸门控制")
    print("=" * 70)

    # 创建输出目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fig_dir = os.path.join(os.path.dirname(script_dir), 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    # ──────────────────────────────────────────────
    # 训练
    # ──────────────────────────────────────────────
    print("\n[1] 开始A2C训练 (300轮)...")
    print("    每轮最多720步（模拟30天水库调度）")
    print("    在策略学习: 每轮数据仅用一次更新")
    print()

    agent, episode_rewards, actor_losses, critic_losses = train_a2c(n_episodes=300)

    # ──────────────────────────────────────────────
    # 评估
    # ──────────────────────────────────────────────
    print("\n[2] 评估训练后的策略（确定性模式）...")
    water_levels, gate_openings, inflows, outflows, eval_reward = evaluate(agent)
    print(f"    评估奖励: {eval_reward:.1f}")

    # ──────────────────────────────────────────────
    # 绘图
    # ──────────────────────────────────────────────
    save_path = os.path.join(fig_dir, 'ch09_a2c_reservoir.png')
    plot_results(episode_rewards, water_levels, gate_openings,
                 inflows, outflows, save_path)

    # ──────────────────────────────────────────────
    # 结论与建议
    # ──────────────────────────────────────────────
    std_final = agent.net.actor_log_std.exp().item()

    print("\n" + "=" * 70)
    print("  结论与建议")
    print("=" * 70)
    print(f"""
  1. 训练概况:
     - 训练轮数: 300轮，每轮最多720步（30天模拟）
     - 初始奖励(前50轮均值): {np.mean(episode_rewards[:50]):.1f}
     - 最终奖励(后50轮均值): {np.mean(episode_rewards[-50:]):.1f}
     - 策略标准差σ: 初始=1.0 → 最终={std_final:.4f}
       （σ自动从高探索衰减到低探索，无需手动调节）

  2. 控制效果:
     - 水位范围: [{min(water_levels):.1f}m, {max(water_levels):.1f}m]
     - 是否超过防洪限制(150m): {"是" if max(water_levels) > 150 else "否"}
     - 是否低于死水位(130m): {"是" if min(water_levels) < 130 else "否"}
     - 最大洪峰入流: {max(inflows):.0f} m³/s
     - 最大出库流量: {max(outflows):.0f} m³/s
     - 洪峰削减率: {(1 - max(outflows)/max(inflows))*100:.1f}%

  3. A2C算法特点:
     - 随机策略提供内生探索能力（无需外加噪声机制）
     - 策略标准差σ作为可学习参数，自动调整探索-利用平衡
     - 在策略学习保证了策略和数据分布的一致性，训练更稳定
     - 共享特征层减少参数量，加速收敛
     - 熵正则化防止策略过早坍缩到确定性

  4. A2C vs DDPG:
     - A2C训练更稳定（不需要调节噪声参数和目标网络更新速率）
     - DDPG样本效率更高（经验回放可重复利用数据）
     - 在仿真环境计算代价低的情况下，A2C的稳定性优势更明显
     - 实际部署时两者均可取均值作为确定性策略

  5. CHS工程应用:
     - A2C/PPO的随机策略在训练中提供探索能力
     - 部署时取均值μ(s)转化为确定性策略
     - 输出须经安全层校验（不违反汛限水位等硬约束）
     - 在CHS框架中: DRL智能体→安全层→执行器的三级决策链

  6. 改进建议:
     - 可升级为PPO（加入裁剪机制进一步稳定训练）
     - 可引入GAE(λ)实现偏差-方差的灵活权衡
     - 多水库协调可采用多智能体A2C/MAPPO
     - 建议在离线仿真中充分训练后，通过xIL逐步验证部署
""")
