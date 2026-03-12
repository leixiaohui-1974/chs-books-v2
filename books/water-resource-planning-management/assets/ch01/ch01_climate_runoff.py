"""
第1章：全球变暖下的水资源挑战
模拟内容：气候变化对流域年径流量的影响分析
- 基于Budyko水热耦合平衡框架，计算不同气温升幅下蒸发与径流的响应
- 对比基准期(1961-1990)与未来情景(RCP4.5/RCP8.5)的径流变化率
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

# ========== Budyko 框架 ==========
# Fu公式: E/P = 1 + PET/P - (1 + (PET/P)^w)^(1/w)
# 其中 E=实际蒸发, P=降水, PET=潜在蒸发, w=下垫面参数

def budyko_fu(P, PET, w=2.5):
    """Fu's Budyko formulation"""
    phi = PET / P  # 干燥指数
    E = P * (1 + phi - (1 + phi**w)**(1.0/w))
    R = P - E  # 径流 = 降水 - 蒸发
    return E, R, phi

# 基准期参数 (华北半湿润流域典型值)
P_base = 550.0   # mm/yr 基准降水
T_base = 12.5     # °C 基准气温
PET_base = 950.0  # mm/yr 基准潜在蒸发(Hargreaves公式估算)
w = 2.6           # 下垫面参数(华北典型)

E_base, R_base, phi_base = budyko_fu(P_base, PET_base, w)
print(f"基准期: P={P_base} mm, PET={PET_base} mm, E={E_base:.1f} mm, R={R_base:.1f} mm")
print(f"基准期径流系数: {R_base/P_base:.3f}, 干燥指数: {phi_base:.2f}")

# ========== 气候变化情景 ==========
# 气温每升高1°C, PET增加约4.5%(Budyko经验)
# 降水变化: RCP4.5约+5%, RCP8.5约+2%(华北降水变化不确定性大)

scenarios = {
    '基准期\n(1961-1990)': {'dT': 0.0, 'dP_pct': 0.0},
    'RCP4.5\n(2041-2060)': {'dT': 1.8, 'dP_pct': 5.0},
    'RCP4.5\n(2081-2100)': {'dT': 2.5, 'dP_pct': 7.0},
    'RCP8.5\n(2041-2060)': {'dT': 2.8, 'dP_pct': 2.0},
    'RCP8.5\n(2081-2100)': {'dT': 4.5, 'dP_pct': 3.0},
}

results = []
for name, sc in scenarios.items():
    P_new = P_base * (1 + sc['dP_pct']/100)
    PET_new = PET_base * (1 + 0.045 * sc['dT'])
    E_new, R_new, phi_new = budyko_fu(P_new, PET_new, w)
    dR_pct = (R_new - R_base) / R_base * 100
    results.append({
        'scenario': name,
        'dT': sc['dT'],
        'P': P_new,
        'PET': PET_new,
        'E': E_new,
        'R': R_new,
        'dR_pct': dR_pct,
        'phi': phi_new
    })
    print(f"{name.replace(chr(10),' ')}: dT=+{sc['dT']}°C, P={P_new:.0f}, PET={PET_new:.0f}, "
          f"R={R_new:.1f} mm, dR={dR_pct:+.1f}%")

# ========== 敏感性分析：径流对气温和降水的弹性 ==========
dT_range = np.linspace(0, 5, 50)
dP_range = np.array([-10, -5, 0, 5, 10])  # %

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# 图1: 不同降水变化率下，径流随气温升幅的变化
ax1 = axes[0]
for dp in dP_range:
    R_series = []
    for dt in dT_range:
        P_s = P_base * (1 + dp/100)
        PET_s = PET_base * (1 + 0.045*dt)
        _, R_s, _ = budyko_fu(P_s, PET_s, w)
        R_series.append((R_s - R_base)/R_base * 100)
    label = f'$\\Delta P$ = {dp:+.0f}%'
    ax1.plot(dT_range, R_series, linewidth=2, label=label)

ax1.axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax1.set_xlabel('气温升幅 ($\\Delta T$, °C)', fontsize=12)
ax1.set_ylabel('径流变化率 (%)', fontsize=12)
ax1.set_title('(a) Budyko框架下径流对气候变化的响应', fontsize=13)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 5)

# 图2: 各情景柱状图
ax2 = axes[1]
names = [r['scenario'] for r in results]
dR_vals = [r['dR_pct'] for r in results]
colors = ['#2196F3', '#4CAF50', '#66BB6A', '#FF7043', '#E53935']
bars = ax2.bar(range(len(names)), dR_vals, color=colors, edgecolor='black', linewidth=0.5, width=0.6)
ax2.set_xticks(range(len(names)))
ax2.set_xticklabels(names, fontsize=9)
ax2.set_ylabel('径流变化率 (%)', fontsize=12)
ax2.set_title('(b) 不同RCP情景下的径流变化', fontsize=13)
ax2.axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax2.grid(True, alpha=0.3, axis='y')

for bar, val in zip(bars, dR_vals):
    ypos = val + 0.5 if val >= 0 else val - 1.5
    ax2.text(bar.get_x() + bar.get_width()/2, ypos, f'{val:+.1f}%',
             ha='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "climate_runoff_response.png"), dpi=300, bbox_inches='tight')
print(f"\n图片已保存: climate_runoff_response.png")

# ========== 输出KPI表 ==========
print("\n===== KPI TABLE =====")
print(f"| 情景 | 气温升幅(°C) | 降水(mm) | 潜在蒸发(mm) | 径流(mm) | 径流变化率(%) |")
print(f"|------|-------------|----------|-------------|----------|-------------|")
for r in results:
    sname = r['scenario'].replace('\n', ' ')
    print(f"| {sname} | +{r['dT']:.1f} | {r['P']:.0f} | {r['PET']:.0f} | {r['R']:.1f} | {r['dR_pct']:+.1f} |")
