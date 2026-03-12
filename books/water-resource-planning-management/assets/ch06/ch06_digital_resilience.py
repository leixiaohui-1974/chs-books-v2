"""
第6章：数字孪生流域与智能规划
模拟内容：基于WEAP简化框架的流域水资源配置 + 干旱韧性压力测试
- 构建简化的流域水资源系统模型(3个需水节点, 1座水库, 2条河段)
- Monte Carlo模拟极端干旱情景
- 计算系统韧性指标(可靠度、回弹性、脆弱性)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

np.random.seed(2024)

# ========== 流域系统模型 ==========
# 拓扑: 上游入流 -> 水库 -> 河段1 -> 城市取水 -> 河段2 -> 农业取水 -> 出口
#                                         |-> 工业取水

T = 120  # 模拟月数(10年)
months = np.arange(1, T+1)

# 月入流量 (亿m3) - 基于季节模式 + 随机波动
def generate_inflow(T, drought_factor=1.0):
    """生成月入流序列, drought_factor<1表示干旱"""
    seasonal = np.tile(np.array([1.5, 1.2, 1.8, 2.5, 4.0, 6.5, 8.0, 7.2, 5.0, 3.2, 2.0, 1.6]), T//12 + 1)[:T]
    noise = np.random.lognormal(0, 0.3, T)
    return seasonal * noise * drought_factor

# 需水量 (亿m3/月)
demand_city = np.tile(np.array([1.0, 1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.5, 1.3, 1.1, 1.0, 1.0]), T//12+1)[:T]
demand_industry = np.ones(T) * 0.8
demand_agri = np.tile(np.array([0.2, 0.2, 0.5, 1.0, 2.0, 2.5, 2.0, 1.5, 0.8, 0.3, 0.2, 0.2]), T//12+1)[:T]
demand_eco = np.ones(T) * 0.3  # 生态基流

total_demand = demand_city + demand_industry + demand_agri + demand_eco

# 水库参数
V_max = 20.0    # 亿m3 总库容
V_dead = 3.0    # 死库容
V_flood = 16.0  # 汛限库容
V_init = 12.0

# ========== 水资源配置模型 ==========
def simulate_system(inflow, priorities=[1, 2, 3, 4]):
    """
    按优先级分配水量
    priorities: [城市, 工业, 农业, 生态] 优先级(1最高)
    """
    V = np.zeros(T+1)
    V[0] = V_init

    supply = np.zeros((T, 4))  # 城市, 工业, 农业, 生态
    deficit = np.zeros((T, 4))
    spill = np.zeros(T)

    demands = np.column_stack([demand_city, demand_industry, demand_agri, demand_eco])

    for t in range(T):
        # 可用水量 = 库存 + 入流 - 死库容
        available = V[t] + inflow[t] - V_dead

        # 按优先级分配
        remaining = max(available, 0)
        order = np.argsort(priorities)  # 按优先级排序

        for idx in order:
            alloc = min(demands[t, idx], remaining)
            supply[t, idx] = alloc
            deficit[t, idx] = demands[t, idx] - alloc
            remaining -= alloc

        # 水库蓄水更新
        total_release = np.sum(supply[t, :])
        V[t+1] = V[t] + inflow[t] - total_release

        # 溢洪
        if V[t+1] > V_max:
            spill[t] = V[t+1] - V_max
            V[t+1] = V_max
        if V[t+1] < V_dead:
            V[t+1] = V_dead

    return V, supply, deficit, spill

# ========== 情景1: 正常来水 ==========
inflow_normal = generate_inflow(T, drought_factor=1.0)
V_norm, supply_norm, deficit_norm, spill_norm = simulate_system(inflow_normal)

# ========== 情景2: 中度干旱(来水减少30%) ==========
inflow_drought1 = generate_inflow(T, drought_factor=0.70)
V_dr1, supply_dr1, deficit_dr1, spill_dr1 = simulate_system(inflow_drought1)

# ========== 情景3: 重度干旱(来水减少50%) ==========
inflow_drought2 = generate_inflow(T, drought_factor=0.50)
V_dr2, supply_dr2, deficit_dr2, spill_dr2 = simulate_system(inflow_drought2)

# ========== 韧性指标计算 ==========
def calc_resilience_metrics(supply, demands_array):
    """计算Hashimoto三指标: 可靠度、回弹性、脆弱性"""
    total_supply = np.sum(supply, axis=1)
    total_demand = np.sum(demands_array, axis=1)

    # 可靠度: 供需满足的时段占比
    satisfied = total_supply >= total_demand * 0.95  # 允许5%的小缺口
    reliability = np.mean(satisfied)

    # 回弹性: 从失败恢复到成功的概率
    transitions = 0
    fail_count = 0
    for t in range(1, len(satisfied)):
        if not satisfied[t-1]:
            fail_count += 1
            if satisfied[t]:
                transitions += 1
    resiliency = transitions / max(fail_count, 1)

    # 脆弱性: 失败时段的平均缺水率
    deficit_total = total_demand - total_supply
    fail_deficits = deficit_total[~satisfied]
    fail_demands = total_demand[~satisfied]
    if len(fail_deficits) > 0:
        vulnerability = np.mean(fail_deficits / fail_demands) * 100
    else:
        vulnerability = 0.0

    return reliability, resiliency, vulnerability

demands_arr = np.column_stack([demand_city, demand_industry, demand_agri, demand_eco])

metrics_normal = calc_resilience_metrics(supply_norm, demands_arr)
metrics_dr1 = calc_resilience_metrics(supply_dr1, demands_arr)
metrics_dr2 = calc_resilience_metrics(supply_dr2, demands_arr)

print("===== 韧性指标 =====")
for name, m in [('正常来水', metrics_normal), ('中度干旱(-30%)', metrics_dr1), ('重度干旱(-50%)', metrics_dr2)]:
    print(f"{name}: 可靠度={m[0]:.3f}, 回弹性={m[1]:.3f}, 脆弱性={m[2]:.1f}%")

# ========== Monte Carlo 压力测试 ==========
n_mc = 500
drought_factors = np.linspace(0.3, 1.2, 30)
mc_reliability = np.zeros((len(drought_factors), n_mc))

for i, df in enumerate(drought_factors):
    for j in range(n_mc):
        np.random.seed(j * 1000 + i)
        inflow_mc = generate_inflow(T, drought_factor=df)
        _, supply_mc, _, _ = simulate_system(inflow_mc)
        r, _, _ = calc_resilience_metrics(supply_mc, demands_arr)
        mc_reliability[i, j] = r

mc_mean = np.mean(mc_reliability, axis=1)
mc_p10 = np.percentile(mc_reliability, 10, axis=1)
mc_p90 = np.percentile(mc_reliability, 90, axis=1)

# ========== 绘图 ==========
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (a) 水库蓄水过程对比
ax1 = axes[0, 0]
ax1.plot(months, V_norm[:-1], 'b-', linewidth=1.5, alpha=0.8, label='正常来水')
ax1.plot(months, V_dr1[:-1], 'orange', linewidth=1.5, alpha=0.8, label='中度干旱(-30%)')
ax1.plot(months, V_dr2[:-1], 'r-', linewidth=1.5, alpha=0.8, label='重度干旱(-50%)')
ax1.axhline(V_max, color='gray', linestyle=':', label=f'总库容 {V_max}')
ax1.axhline(V_dead, color='brown', linestyle=':', label=f'死库容 {V_dead}')
ax1.fill_between(months, V_dead, V_max, alpha=0.05, color='blue')
ax1.set_xlabel('月', fontsize=11)
ax1.set_ylabel('蓄水量 (亿m$^3$)', fontsize=11)
ax1.set_title('(a) 水库蓄水过程对比', fontsize=12)
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# (b) 供需对比(重度干旱)
ax2 = axes[0, 1]
sector_names = ['城市', '工业', '农业', '生态']
colors_supply = ['#42A5F5', '#66BB6A', '#FFA726', '#AB47BC']
total_supply_dr2 = np.sum(supply_dr2, axis=1)
ax2.plot(months, np.sum(demands_arr, axis=1), 'k--', linewidth=2, label='总需水')
ax2.stackplot(months, supply_dr2.T, labels=[f'{s}供水' for s in sector_names],
              colors=colors_supply, alpha=0.7)
ax2.set_xlabel('月', fontsize=11)
ax2.set_ylabel('水量 (亿m$^3$/月)', fontsize=11)
ax2.set_title('(b) 重度干旱下分部门供水', fontsize=12)
ax2.legend(fontsize=8, loc='upper left')
ax2.grid(True, alpha=0.3)

# (c) 韧性指标雷达图
ax3 = axes[1, 0]
categories = ['可靠度', '回弹性', '1-脆弱性']
N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]

def make_radar_data(metrics):
    return [metrics[0], metrics[1], 1-metrics[2]/100] + [metrics[0]]

for name, m, color in [('正常来水', metrics_normal, 'blue'),
                        ('中度干旱', metrics_dr1, 'orange'),
                        ('重度干旱', metrics_dr2, 'red')]:
    vals = make_radar_data(m)
    ax3.plot(angles, vals, 'o-', linewidth=2, color=color, label=name, markersize=6)
    ax3.fill(angles, vals, alpha=0.1, color=color)

ax3.set_xticks(angles[:-1])
ax3.set_xticklabels(categories, fontsize=11)
ax3.set_ylim(0, 1.05)
ax3.set_title('(c) 韧性指标对比', fontsize=12)
ax3.legend(fontsize=9, loc='lower right')
ax3.grid(True, alpha=0.3)

# (d) Monte Carlo压力测试
ax4 = axes[1, 1]
ax4.plot(drought_factors*100, mc_mean*100, 'b-', linewidth=2, label='均值')
ax4.fill_between(drought_factors*100, mc_p10*100, mc_p90*100, alpha=0.2, color='blue', label='10%-90%分位')
ax4.axhline(90, color='green', linestyle='--', label='可靠度目标(90%)')
ax4.axhline(75, color='orange', linestyle='--', label='可靠度警戒(75%)')
ax4.axvline(100, color='gray', linestyle=':', alpha=0.5)
ax4.set_xlabel('来水比例 (%, 100%=正常)', fontsize=11)
ax4.set_ylabel('系统可靠度 (%)', fontsize=11)
ax4.set_title('(d) Monte Carlo干旱压力测试 (N=500)', fontsize=12)
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)
ax4.set_xlim(30, 120)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "digital_resilience.png"), dpi=300, bbox_inches='tight')
print(f"\n图片已保存: digital_resilience.png")

# ========== KPI输出 ==========
# 找到可靠度降至90%的来水比例
idx_90 = np.argmin(np.abs(mc_mean - 0.90))
threshold_90 = drought_factors[idx_90] * 100

print("\n===== KPI TABLE =====")
print("| 指标 | 正常来水 | 中度干旱(-30%) | 重度干旱(-50%) |")
print("|------|---------|---------------|---------------|")
print(f"| 可靠度 | {metrics_normal[0]:.3f} | {metrics_dr1[0]:.3f} | {metrics_dr2[0]:.3f} |")
print(f"| 回弹性 | {metrics_normal[1]:.3f} | {metrics_dr1[1]:.3f} | {metrics_dr2[1]:.3f} |")
print(f"| 脆弱性(%) | {metrics_normal[2]:.1f} | {metrics_dr1[2]:.1f} | {metrics_dr2[2]:.1f} |")
print(f"\n| 压力测试指标 | 数值 |")
print(f"|-------------|------|")
print(f"| Monte Carlo模拟次数 | {n_mc} |")
print(f"| 可靠度降至90%的来水比例 | {threshold_90:.0f}% |")
print(f"| 来水50%时的平均可靠度 | {mc_mean[np.argmin(np.abs(drought_factors-0.5))]*100:.1f}% |")
print(f"| 来水30%时的平均可靠度 | {mc_mean[0]*100:.1f}% |")
