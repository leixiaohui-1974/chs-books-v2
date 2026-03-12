import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

output_dir = r"D:\cowork\教材\chs-books-v2\books\water-resource-planning-management\assets\ch03"
os.makedirs(output_dir, exist_ok=True)

# 动态规划 (Dynamic Programming, DP) 水库调度
# 场景：给定一年的入流预测，在保证水位不越限的情况下最大化发电量 (或经济效益)

months = 12
time = np.arange(1, months + 1)
# 预测的每月入流 (千万m3)
inflow = np.array([20, 30, 40, 60, 150, 200, 180, 120, 80, 50, 30, 20])
# 初始和最终水量限制
V_min = 50
V_max = 300
V_init = 100
V_end_target = 100

# 离散化状态空间 (水量)
num_states = 26 # 50, 60, ..., 300 (步长10)
states = np.linspace(V_min, V_max, num_states)

# DP 表：存放最大收益及对应的上一状态
dp_val = np.ones((months + 1, num_states)) * -np.inf
dp_ptr = np.zeros((months + 1, num_states), dtype=int)

# 初始化
init_idx = np.argmin(np.abs(states - V_init))
dp_val[0, init_idx] = 0.0

# 目标函数：收益 = (V_current + V_next)/2 * Release (简化的发电收益模型)
def calc_reward(v_curr, v_next, in_flow):
    release = v_curr + in_flow - v_next
    if release < 10: return -np.inf # 必须满足生态基流 10
    if release > 100: return -np.inf # 超过机组最大过流能力，弃水不发电
    head = (v_curr + v_next) / 2.0
    return head * release * 0.01 # 收益

# 前向 DP
for t in range(months):
    for i, v_curr in enumerate(states):
        if dp_val[t, i] == -np.inf: continue
        for j, v_next in enumerate(states):
            reward = calc_reward(v_curr, v_next, inflow[t])
            if reward > -np.inf:
                new_val = dp_val[t, i] + reward
                if new_val > dp_val[t+1, j]:
                    dp_val[t+1, j] = new_val
                    dp_ptr[t+1, j] = i

# 回溯寻找最优路径
end_idx = np.argmin(np.abs(states - V_end_target))
if dp_val[months, end_idx] == -np.inf:
    # 如果目标不可达，找最高的一个
    end_idx = np.argmax(dp_val[months, :])

opt_states = np.zeros(months + 1)
opt_states[months] = states[end_idx]

curr_ptr = end_idx
for t in range(months, 0, -1):
    curr_ptr = dp_ptr[t, curr_ptr]
    opt_states[t-1] = states[curr_ptr]

opt_releases = opt_states[:-1] + inflow - opt_states[1:]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.plot(time, inflow, 'k--', marker='o', label='Inflow Forecast')
ax1.plot(time, opt_releases, 'b-', marker='s', linewidth=2, label='Optimal Release (DP)')
ax1.set_ylabel('Flow ($10^7 m^3$)')
ax1.set_title('Reservoir Monthly Dispatch (Dynamic Programming)')
ax1.legend()
ax1.grid(True)

ax2.plot(range(months+1), opt_states, 'g-', marker='^', linewidth=2, label='Optimal Storage Volume')
ax2.axhline(V_max, color='r', linestyle=':', label='Max Capacity')
ax2.axhline(V_min, color='orange', linestyle=':', label='Dead Storage')
ax2.set_xlabel('Month')
ax2.set_ylabel('Storage Volume ($10^7 m^3$)')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "dp_reservoir_sim.png"), dpi=300)

df = pd.DataFrame([
    {'Total Economic Benefit': round(np.max(dp_val[months, :]), 2), 'Algorithm': 'Dynamic Programming (Bellman Eq)'}
])
with open(os.path.join(output_dir, "dp_table.md"), "w") as f: f.write(df.to_markdown(index=False))

def create_schematic(path, title):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (1024, 512), color=(240, 245, 250))
    d = ImageDraw.Draw(img)
    d.text((40, 40), title, fill=(20, 40, 100))
    img.save(path)
create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch03: Reservoir DP Optimization")
