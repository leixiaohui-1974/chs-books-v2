"""
第2章：供需平衡分析 (Water Balance)
模拟内容：基于P-III型频率曲线的设计来水分析 + 供需平衡计算
- 生成50年径流系列，拟合P-III型分布
- 计算不同保证率(P=50%, 75%, 90%, 95%)下的设计来水量
- 需水预测：定额法估算2025-2040年分部门需水
- 供需平衡分析与缺水率计算
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from scipy.special import gamma as gamma_func
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

np.random.seed(42)

# ========== 1. 生成50年年径流序列(P-III分布) ==========
# 参数: 均值Q_mean, 变差系数Cv, 偏态系数Cs
Q_mean = 8.5   # 亿m3/yr
Cv = 0.35
Cs_ratio = 2.0  # Cs/Cv = 2.0(华北常见)
Cs = Cv * Cs_ratio

sigma = Q_mean * Cv
# P-III分布(即Pearson III) = 位移的Gamma分布
# 形状参数 alpha = 4/Cs^2, 尺度 beta = sigma*Cs/2, 位置 x0 = Q_mean - 2*sigma/Cs
alpha_p3 = 4.0 / (Cs**2)
beta_p3 = sigma * Cs / 2.0
x0_p3 = Q_mean - 2*sigma/Cs

# 用scipy gamma分布生成
runoff_series = stats.gamma.rvs(a=alpha_p3, loc=x0_p3, scale=beta_p3, size=50)
runoff_series = np.maximum(runoff_series, 0.5)  # 确保非负

years = np.arange(1971, 2021)
print(f"径流统计: 均值={np.mean(runoff_series):.2f}, Cv={np.std(runoff_series)/np.mean(runoff_series):.3f}")

# ========== 2. 频率分析：计算设计来水 ==========
sorted_runoff = np.sort(runoff_series)[::-1]  # 降序排列
n = len(sorted_runoff)
# 经验频率 (P = m/(n+1))
empirical_p = np.arange(1, n+1) / (n+1)

# 理论P-III线(用矩法估计参数)
Q_hat = np.mean(runoff_series)
sigma_hat = np.std(runoff_series, ddof=1)
Cv_hat = sigma_hat / Q_hat
skew_hat = stats.skew(runoff_series, bias=False)
Cs_hat = skew_hat

alpha_fit = 4.0 / max(Cs_hat, 0.01)**2
beta_fit = sigma_hat * max(Cs_hat, 0.01) / 2.0
x0_fit = Q_hat - 2*sigma_hat/max(Cs_hat, 0.01)

# 设计保证率下的来水量
design_probs = [0.50, 0.75, 0.90, 0.95]
design_flows = {}
for p in design_probs:
    # P-III分布: 超过概率p对应的分位数 = 1-p的累积分布
    q = stats.gamma.ppf(1-p, a=alpha_fit, loc=x0_fit, scale=beta_fit)
    design_flows[p] = max(q, 0.5)
    print(f"保证率P={p*100:.0f}%: 设计来水量 = {design_flows[p]:.2f} 亿m3")

# ========== 3. 需水预测(定额法) ==========
pred_years = np.array([2025, 2030, 2035, 2040])

# 人口(万人)
pop = np.array([380, 395, 405, 410])
# 人均生活用水定额(L/d)
quota_life = np.array([120, 125, 128, 130])
# 工业产值(亿元)
gdp_industry = np.array([850, 1020, 1180, 1300])
# 万元工业增加值用水量(m3/万元)
quota_ind = np.array([35, 28, 23, 19])
# 灌溉面积(万亩)
irrig_area = np.array([180, 175, 170, 165])
# 亩均灌溉用水定额(m3/亩)
quota_irrig = np.array([380, 350, 320, 300])
# 生态需水(亿m3)
eco_water = np.array([1.2, 1.5, 1.8, 2.0])

# 计算各部门需水量(亿m3)
demand_life = pop * quota_life * 365 / 1e8
demand_ind = gdp_industry * quota_ind / 1e4
demand_agri = irrig_area * quota_irrig / 1e4
demand_total = demand_life + demand_ind + demand_agri + eco_water

print("\n===== 需水预测 =====")
for i, y in enumerate(pred_years):
    print(f"{y}: 生活={demand_life[i]:.2f}, 工业={demand_ind[i]:.2f}, "
          f"农业={demand_agri[i]:.2f}, 生态={eco_water[i]:.2f}, 合计={demand_total[i]:.2f} 亿m3")

# ========== 4. 供需平衡 ==========
# 供水能力 = 设计来水量(P=75%) + 再生水 + 跨流域调水
supply_base = design_flows[0.75]
reclaimed = np.array([0.3, 0.5, 0.8, 1.0])  # 再生水利用
transfer = np.array([1.5, 2.0, 2.5, 3.0])    # 调水工程
supply_total = supply_base + reclaimed + transfer

deficit = demand_total - supply_total
deficit_rate = np.where(deficit > 0, deficit / demand_total * 100, 0)

print("\n===== 供需平衡 =====")
for i, y in enumerate(pred_years):
    status = f"缺水{deficit[i]:.2f}亿m3 ({deficit_rate[i]:.1f}%)" if deficit[i] > 0 else "盈余"
    print(f"{y}: 供水={supply_total[i]:.2f}, 需水={demand_total[i]:.2f}, {status}")

# ========== 绘图 ==========
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (a) 径流序列与频率曲线
ax1 = axes[0, 0]
ax1.bar(years, runoff_series, color='#2196F3', alpha=0.7, width=0.8)
ax1.axhline(Q_hat, color='red', linestyle='--', linewidth=1.5, label=f'均值 {Q_hat:.1f} 亿m$^3$')
ax1.set_xlabel('年份', fontsize=11)
ax1.set_ylabel('年径流量 (亿m$^3$)', fontsize=11)
ax1.set_title('(a) 50年年径流量序列', fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# (b) P-III频率曲线
ax2 = axes[0, 1]
ax2.plot(empirical_p*100, sorted_runoff, 'bo', markersize=5, label='经验频率点')
# 理论曲线
p_theory = np.linspace(0.01, 0.99, 200)
q_theory = stats.gamma.ppf(1-p_theory, a=alpha_fit, loc=x0_fit, scale=beta_fit)
ax2.plot(p_theory*100, q_theory, 'r-', linewidth=2, label='P-III理论曲线')
# 标注设计值
for p_val in design_probs:
    ax2.plot(p_val*100, design_flows[p_val], 'r^', markersize=12, zorder=5)
    ax2.annotate(f'P={p_val*100:.0f}%: {design_flows[p_val]:.1f}',
                xy=(p_val*100, design_flows[p_val]),
                xytext=(p_val*100+5, design_flows[p_val]+0.5),
                fontsize=9, arrowprops=dict(arrowstyle='->', color='red'))
ax2.set_xlabel('频率 P (%)', fontsize=11)
ax2.set_ylabel('年径流量 (亿m$^3$)', fontsize=11)
ax2.set_title('(b) P-III型频率曲线', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# (c) 需水预测堆叠图
ax3 = axes[1, 0]
bar_width = 3
ax3.bar(pred_years, demand_life, bar_width, label='生活用水', color='#42A5F5')
ax3.bar(pred_years, demand_ind, bar_width, bottom=demand_life, label='工业用水', color='#66BB6A')
ax3.bar(pred_years, demand_agri, bar_width, bottom=demand_life+demand_ind, label='农业用水', color='#FFA726')
ax3.bar(pred_years, eco_water, bar_width, bottom=demand_life+demand_ind+demand_agri,
        label='生态用水', color='#AB47BC')
ax3.plot(pred_years, supply_total, 'rs--', linewidth=2, markersize=8, label='供水能力')
ax3.set_xlabel('年份', fontsize=11)
ax3.set_ylabel('水量 (亿m$^3$)', fontsize=11)
ax3.set_title('(c) 分部门需水预测与供水能力', fontsize=12)
ax3.legend(fontsize=9, loc='upper left')
ax3.grid(True, alpha=0.3, axis='y')

# (d) 供需差与缺水率
ax4 = axes[1, 1]
colors_bar = ['#4CAF50' if d <= 0 else '#E53935' for d in deficit]
ax4.bar(pred_years, deficit, bar_width, color=colors_bar, edgecolor='black', linewidth=0.5)
ax4.axhline(0, color='gray', linestyle='-', linewidth=0.8)
ax4.set_xlabel('年份', fontsize=11)
ax4.set_ylabel('供需差 (亿m$^3$, 负值=缺水)', fontsize=11)
ax4.set_title('(d) 供需平衡分析', fontsize=12)
ax4.grid(True, alpha=0.3, axis='y')

for i, y in enumerate(pred_years):
    if deficit[i] > 0:
        ax4.text(y, deficit[i]+0.1, f'缺{deficit_rate[i]:.1f}%', ha='center', fontsize=10, color='red')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "water_balance_analysis.png"), dpi=300, bbox_inches='tight')
print(f"\n图片已保存: water_balance_analysis.png")

# ========== KPI输出 ==========
print("\n===== KPI TABLE =====")
print("| 指标 | 数值 |")
print("|------|------|")
print(f"| 径流均值 | {Q_hat:.2f} 亿m3 |")
print(f"| 变差系数 Cv | {Cv_hat:.3f} |")
print(f"| P=75%设计来水 | {design_flows[0.75]:.2f} 亿m3 |")
print(f"| P=90%设计来水 | {design_flows[0.90]:.2f} 亿m3 |")
print(f"| 2025年总需水 | {demand_total[0]:.2f} 亿m3 |")
print(f"| 2040年总需水 | {demand_total[3]:.2f} 亿m3 |")
print(f"| 2025年缺水率 | {deficit_rate[0]:.1f}% |")
print(f"| 2040年缺水率 | {deficit_rate[3]:.1f}% |")
