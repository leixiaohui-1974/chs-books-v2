import numpy as np
import matplotlib.pyplot as plt

episodes = np.arange(1, 1001)
N = len(episodes)

np.random.seed(42)
base_cost = 5000 * np.exp(-episodes / 150) + 200

noise_decay = np.exp(-episodes / 300)
exploration_noise = np.random.normal(0, 400, N) * noise_decay
total_cost = base_cost + exploration_noise

total_cost = np.clip(total_cost, 100, None)

def moving_average(a, n=50):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

rolling_cost = moving_average(total_cost)

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(episodes, total_cost, color='lightgray', alpha=0.8, label='Episode Cost (Exploration Variance)')
ax.plot(episodes[49:], rolling_cost, 'b-', linewidth=3, label='50-Episode Moving Average')
ax.axhline(250, color='r', linestyle='--', linewidth=2, label='Theoretical LQR Optimal Cost')

ax.annotate('Random Exploration Phase', xy=(100, 3500), xytext=(200, 4500),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))
            
ax.annotate('Convergence to Near-Optimal', xy=(800, 300), xytext=(600, 1500),
            arrowprops=dict(facecolor='blue', shrink=0.05, width=1.5, headwidth=6), color='blue')

ax.set_xlabel('Training Episodes', fontweight='bold')
ax.set_ylabel('Total Episodic Cost (Energy + Error)', fontweight='bold')
ax.set_title('Figure 10.1: DRL Agent Learning Curve in Digital Twin Environment', fontweight='bold', fontsize=14)
ax.legend(loc='upper right')
ax.grid(True, alpha=0.4)
ax.set_ylim(0, 6000)

plt.tight_layout()
save_path = r'D:/cowork/教材/chs-books-v2/books/water-system-control/assets/ch10/rl_learning_curve.png'
plt.savefig(save_path, dpi=300)
