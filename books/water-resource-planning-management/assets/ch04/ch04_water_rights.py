"""
第4章：水权交易与博弈分配
模拟内容：基于合作博弈论的跨区域水权分配
- 3个用水区域的初始水权分配
- Shapley值法计算公平分配方案
- 影子价格(边际水价)分析
- 水权交易前后的福利变化
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from itertools import combinations, permutations
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# ========== 问题定义 ==========
# 3个用水区域: A=农业区, B=工业区, C=城市区
# 可用总水量: 10亿m3
W_total = 10.0  # 亿m3

# 各区域效用函数 (凹函数, 亿元/亿m3)
# V_i(w) = a_i * w - b_i * w^2 (收益递减)
params = {
    'A': {'name': '农业区', 'a': 3.0, 'b': 0.3, 'w_max': 5.0, 'color': '#FFA726'},
    'B': {'name': '工业区', 'a': 8.0, 'b': 0.8, 'w_max': 5.0, 'color': '#42A5F5'},
    'C': {'name': '城市区', 'a': 12.0, 'b': 1.5, 'w_max': 4.0, 'color': '#66BB6A'},
}
regions = ['A', 'B', 'C']

def utility(region, w):
    """区域效用函数 V(w) = a*w - b*w^2"""
    p = params[region]
    w = min(w, p['w_max'])
    w = max(w, 0)
    return p['a'] * w - p['b'] * w**2

def marginal_utility(region, w):
    """边际效用 = dV/dw = a - 2bw (即影子价格)"""
    p = params[region]
    return p['a'] - 2*p['b']*w

# ========== 1. 初始分配(按现状用水比例) ==========
w_initial = {'A': 5.0, 'B': 3.0, 'C': 2.0}
print("===== 初始水权分配(现状优先原则) =====")
total_v_init = 0
for r in regions:
    v = utility(r, w_initial[r])
    mu = marginal_utility(r, w_initial[r])
    total_v_init += v
    print(f"  {params[r]['name']}: 水量={w_initial[r]:.1f}亿m3, 效益={v:.2f}亿元, 边际水价={mu:.2f}元/m3")
print(f"  社会总效益: {total_v_init:.2f}亿元")

# ========== 2. 最优分配(拉格朗日乘子法) ==========
# 最优条件: 各区域边际效用相等 = lambda(影子价格)
# a_i - 2*b_i*w_i = lambda, sum(w_i) = W_total
# w_i = (a_i - lambda) / (2*b_i)

from scipy.optimize import fsolve

def equations(lam):
    lam = lam[0]
    w_opt = []
    for r in regions:
        p = params[r]
        w = (p['a'] - lam) / (2*p['b'])
        w = max(0, min(w, p['w_max']))
        w_opt.append(w)
    return [sum(w_opt) - W_total]

lam_sol = fsolve(equations, 3.0)[0]
w_optimal = {}
for r in regions:
    p = params[r]
    w = (p['a'] - lam_sol) / (2*p['b'])
    w = max(0, min(w, p['w_max']))
    w_optimal[r] = w

print(f"\n===== 最优分配(边际效用均等) =====")
print(f"  影子价格(边际水价): {lam_sol:.2f} 元/m3")
total_v_opt = 0
for r in regions:
    v = utility(r, w_optimal[r])
    total_v_opt += v
    print(f"  {params[r]['name']}: 水量={w_optimal[r]:.2f}亿m3, 效益={v:.2f}亿元")
print(f"  社会总效益: {total_v_opt:.2f}亿元")
print(f"  效益提升: {total_v_opt - total_v_init:.2f}亿元 ({(total_v_opt-total_v_init)/total_v_init*100:.1f}%)")

# ========== 3. Shapley值分配 ==========
# 联盟博弈: v(S)为联盟S的最优总收益

def coalition_value(coalition):
    """计算联盟的最优收益"""
    members = list(coalition)
    w_avail = sum(w_initial[r] for r in members)  # 联盟拥有的总水量

    if len(members) == 1:
        return utility(members[0], w_avail)

    # 对联盟内部做最优分配
    from scipy.optimize import minimize

    def neg_total(ws):
        return -sum(utility(members[i], ws[i]) for i in range(len(members)))

    bounds = [(0, params[r]['w_max']) for r in members]
    cons = {'type': 'eq', 'fun': lambda ws: sum(ws) - w_avail}
    x0 = [w_avail/len(members)] * len(members)
    result = minimize(neg_total, x0, method='SLSQP', bounds=bounds, constraints=cons)
    return -result.fun

# 计算所有联盟值
all_coalitions = {}
for size in range(1, 4):
    for combo in combinations(regions, size):
        val = coalition_value(combo)
        all_coalitions[frozenset(combo)] = val
        print(f"  v({set(combo)}) = {val:.2f}")

# Shapley值
def shapley_value(player, all_players, v_func):
    n = len(all_players)
    phi = 0
    others = [p for p in all_players if p != player]
    for perm in permutations(others):
        # 考虑player加入前后的边际贡献
        pred = set()
        for p in perm:
            pred.add(p)
        # 对每个排列，计算player在各位置的边际贡献
        pass

    # 直接用公式
    phi = 0
    for size in range(0, n):
        for combo in combinations(others, size):
            S = frozenset(combo)
            S_with_i = frozenset(combo + (player,))
            v_S = v_func.get(S, 0)
            v_Si = v_func.get(S_with_i, 0)
            from math import factorial
            weight = factorial(size) * factorial(n-size-1) / factorial(n)
            phi += weight * (v_Si - v_S)
    return phi

shapley = {}
print(f"\n===== Shapley值分配 =====")
for r in regions:
    sv = shapley_value(r, regions, all_coalitions)
    shapley[r] = sv
    print(f"  {params[r]['name']}: Shapley值 = {sv:.2f}亿元")
print(f"  Shapley总和: {sum(shapley.values()):.2f}亿元")

# ========== 4. 水权交易分析 ==========
# 交易量 = 最优分配 - 初始分配
print(f"\n===== 水权交易 =====")
transfers = {}
for r in regions:
    diff = w_optimal[r] - w_initial[r]
    transfers[r] = diff
    action = "买入" if diff > 0 else "卖出"
    print(f"  {params[r]['name']}: {action} {abs(diff):.2f}亿m3")
    # 交易价格 = 影子价格
    payment = abs(diff) * lam_sol
    print(f"    交易金额: {payment:.2f}亿元 (按影子价格 {lam_sol:.2f} 元/m3)")

# ========== 绘图 ==========
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (a) 效用函数与边际效用
ax1 = axes[0, 0]
w_range = np.linspace(0, 5.5, 100)
for r in regions:
    p = params[r]
    v_vals = [utility(r, w) for w in w_range]
    ax1.plot(w_range, v_vals, linewidth=2, color=p['color'], label=f"{p['name']}")
ax1.set_xlabel('用水量 (亿m$^3$)', fontsize=11)
ax1.set_ylabel('效益 (亿元)', fontsize=11)
ax1.set_title('(a) 各区域效用函数', fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# (b) 边际水价(影子价格)
ax2 = axes[0, 1]
for r in regions:
    p = params[r]
    mu_vals = [marginal_utility(r, w) for w in w_range]
    ax2.plot(w_range, mu_vals, linewidth=2, color=p['color'], label=f"{p['name']}")
ax2.axhline(lam_sol, color='red', linestyle='--', linewidth=1.5, label=f'均衡价格 {lam_sol:.2f}')
ax2.set_xlabel('用水量 (亿m$^3$)', fontsize=11)
ax2.set_ylabel('边际水价 (元/m$^3$)', fontsize=11)
ax2.set_title('(b) 边际水价与影子价格', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_ylim(bottom=0)

# (c) 初始分配 vs 最优分配
ax3 = axes[1, 0]
x_pos = np.arange(len(regions))
width = 0.35
bars1 = ax3.bar(x_pos - width/2, [w_initial[r] for r in regions], width,
                label='初始分配', color='#90CAF9', edgecolor='black', linewidth=0.5)
bars2 = ax3.bar(x_pos + width/2, [w_optimal[r] for r in regions], width,
                label='最优分配', color='#1565C0', edgecolor='black', linewidth=0.5)
ax3.set_xticks(x_pos)
ax3.set_xticklabels([params[r]['name'] for r in regions], fontsize=11)
ax3.set_ylabel('水量 (亿m$^3$)', fontsize=11)
ax3.set_title('(c) 水权交易前后的水量分配', fontsize=12)
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3, axis='y')

# 标注交易量
for i, r in enumerate(regions):
    diff = transfers[r]
    arrow = '↑' if diff > 0 else '↓'
    ax3.annotate(f'{arrow}{abs(diff):.1f}', xy=(x_pos[i]+width/2, w_optimal[r]),
                xytext=(x_pos[i]+width/2, w_optimal[r]+0.3),
                ha='center', fontsize=10, color='red', fontweight='bold')

# (d) Shapley值 vs 初始收益 vs 最优收益
ax4 = axes[1, 1]
v_init_list = [utility(r, w_initial[r]) for r in regions]
v_opt_list = [utility(r, w_optimal[r]) for r in regions]
sv_list = [shapley[r] for r in regions]

width3 = 0.25
bars_i = ax4.bar(x_pos - width3, v_init_list, width3, label='初始收益', color='#FFCC80', edgecolor='black', linewidth=0.5)
bars_o = ax4.bar(x_pos, v_opt_list, width3, label='最优收益', color='#4CAF50', edgecolor='black', linewidth=0.5)
bars_s = ax4.bar(x_pos + width3, sv_list, width3, label='Shapley分配', color='#7B1FA2', edgecolor='black', linewidth=0.5)
ax4.set_xticks(x_pos)
ax4.set_xticklabels([params[r]['name'] for r in regions], fontsize=11)
ax4.set_ylabel('效益 (亿元)', fontsize=11)
ax4.set_title('(d) 效益分配方案对比', fontsize=12)
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "water_rights_game.png"), dpi=300, bbox_inches='tight')
print(f"\n图片已保存: water_rights_game.png")

# ========== KPI输出 ==========
print("\n===== KPI TABLE =====")
print("| 指标 | 数值 |")
print("|------|------|")
print(f"| 可分配总水量 | {W_total:.1f} 亿m3 |")
print(f"| 初始分配总效益 | {total_v_init:.2f} 亿元 |")
print(f"| 最优分配总效益 | {total_v_opt:.2f} 亿元 |")
print(f"| 效益提升率 | {(total_v_opt-total_v_init)/total_v_init*100:.1f}% |")
print(f"| 影子价格(均衡水价) | {lam_sol:.2f} 元/m3 |")
print(f"| 农业区交易量 | {transfers['A']:+.2f} 亿m3 |")
print(f"| 工业区交易量 | {transfers['B']:+.2f} 亿m3 |")
print(f"| 城市区交易量 | {transfers['C']:+.2f} 亿m3 |")
