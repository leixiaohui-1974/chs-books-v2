"""
第5章：生态需水保障与水质规划
模拟内容：
- Tennant法计算逐月最小生态基流
- 一维河流BOD-DO水质模型(Streeter-Phelps方程)
- 纳污能力计算与限排总量控制
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

# ========== 1. Tennant法生态基流 ==========
# 基于多年平均流量的百分比确定最小生态流量
# 典型标准: 丰水期30%, 枯水期10%(最低), 一般推荐枯水期20%

months = np.arange(1, 13)
month_names = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']

# 多年月平均流量 (m3/s) - 北方半湿润河流典型
Q_monthly_avg = np.array([12.5, 10.8, 15.2, 22.0, 35.6, 48.3, 85.2, 72.4, 45.1, 28.3, 18.5, 14.0])
Q_annual_avg = np.mean(Q_monthly_avg)  # 年均流量

# Tennant法分级
tennant_levels = {
    '最低(10%)': 0.10,
    '较差(20%)': 0.20,
    '良好(30%)': 0.30,
    '优秀(40%)': 0.40,
}

# 推荐方案: 枯水期(11-4月)20%, 丰水期(5-10月)30%
eco_flow_recommended = np.zeros(12)
for i in range(12):
    if i+1 in [11, 12, 1, 2, 3, 4]:  # 枯水期
        eco_flow_recommended[i] = Q_annual_avg * 0.20
    else:  # 丰水期
        eco_flow_recommended[i] = Q_annual_avg * 0.30

print("===== Tennant法生态基流 =====")
print(f"多年平均流量: {Q_annual_avg:.1f} m3/s")
print(f"推荐生态基流(枯水期20%): {Q_annual_avg*0.20:.1f} m3/s")
print(f"推荐生态基流(丰水期30%): {Q_annual_avg*0.30:.1f} m3/s")
for i in range(12):
    ratio = eco_flow_recommended[i] / Q_monthly_avg[i] * 100
    print(f"  {month_names[i]}: 天然={Q_monthly_avg[i]:.1f}, 生态基流={eco_flow_recommended[i]:.1f} m3/s, 占比={ratio:.0f}%")

# ========== 2. Streeter-Phelps BOD-DO模型 ==========
# dL/dt = -K1*L (BOD衰减)
# dD/dt = K1*L - K2*D (溶解氧亏损)
# D = DO_sat - DO

# 河段参数
Q_river = 25.0    # m3/s 河流流量
v_river = 0.5     # m/s 流速
K1 = 0.3          # 1/d 耗氧系数(20°C)
K2 = 0.5          # 1/d 复氧系数(20°C)
DO_sat = 8.5      # mg/L 饱和溶解氧(20°C)

# 上游初始条件
DO_upstream = 7.5   # mg/L
L_upstream = 2.0    # mg/L 上游BOD

# 排污口
Q_waste = 0.8       # m3/s 排污流量
BOD_waste = 150.0   # mg/L 排污BOD浓度
DO_waste = 2.0      # mg/L 排污口溶解氧

# 混合后初始浓度
Q_mix = Q_river + Q_waste
L0 = (Q_river * L_upstream + Q_waste * BOD_waste) / Q_mix
D0 = DO_sat - (Q_river * DO_upstream + Q_waste * DO_waste) / Q_mix

print(f"\n===== Streeter-Phelps模型 =====")
print(f"混合后: BOD={L0:.2f} mg/L, DO亏损={D0:.2f} mg/L, DO={DO_sat-D0:.2f} mg/L")

# 求解
x_km = np.linspace(0, 50, 500)  # 0-50km
t_days = x_km * 1000 / (v_river * 86400)  # 距离转时间

# BOD沿程衰减
L_x = L0 * np.exp(-K1 * t_days)

# DO亏损 (Streeter-Phelps解析解)
D_x = (K1 * L0 / (K2 - K1)) * (np.exp(-K1 * t_days) - np.exp(-K2 * t_days)) + D0 * np.exp(-K2 * t_days)

# DO浓度
DO_x = DO_sat - D_x

# 临界点(最低DO位置)
# dD/dx = 0 => t_c = ln(K2/K1 * (1 - D0*(K2-K1)/(K1*L0))) / (K2-K1)
ratio_term = (K2/K1) * (1 - D0*(K2-K1)/(K1*L0))
if ratio_term > 0:
    t_critical = np.log(ratio_term) / (K2 - K1)
    x_critical = t_critical * v_river * 86400 / 1000  # km
    D_critical = (K1*L0/(K2-K1)) * (np.exp(-K1*t_critical) - np.exp(-K2*t_critical)) + D0*np.exp(-K2*t_critical)
    DO_critical = DO_sat - D_critical
    print(f"临界点: x={x_critical:.1f} km, DO={DO_critical:.2f} mg/L")
else:
    x_critical = 0
    DO_critical = DO_sat - D0
    print(f"临界点在混合点处: DO={DO_critical:.2f} mg/L")

# ========== 3. 纳污能力计算 ==========
# III类水质标准: DO >= 5 mg/L, BOD <= 4 mg/L
DO_standard = 5.0
BOD_standard = 4.0

# 纳污能力 = 允许的最大排污负荷 - 上游本底
# 逆推: 在最低DO点满足标准时的最大排入BOD

# 二分法求最大允许排污浓度
def calc_min_DO(BOD_conc):
    L0_test = (Q_river * L_upstream + Q_waste * BOD_conc) / Q_mix
    D0_test = DO_sat - (Q_river * DO_upstream + Q_waste * DO_waste) / Q_mix
    t_test = np.linspace(0, 5, 1000)
    D_test = (K1*L0_test/(K2-K1)) * (np.exp(-K1*t_test) - np.exp(-K2*t_test)) + D0_test*np.exp(-K2*t_test)
    return DO_sat - np.max(D_test)

# 搜索
BOD_low, BOD_high = 0, 500
for _ in range(50):
    BOD_mid = (BOD_low + BOD_high) / 2
    if calc_min_DO(BOD_mid) > DO_standard:
        BOD_low = BOD_mid
    else:
        BOD_high = BOD_mid

BOD_max_allowed = BOD_low
load_capacity = Q_waste * BOD_max_allowed * 86400 / 1e6  # t/d
load_current = Q_waste * BOD_waste * 86400 / 1e6
load_reduction = max(0, load_current - load_capacity)

print(f"\n===== 纳污能力分析 =====")
print(f"III类水质标准: DO >= {DO_standard} mg/L")
print(f"最大允许排污BOD浓度: {BOD_max_allowed:.1f} mg/L")
print(f"纳污能力: {load_capacity:.2f} t/d")
print(f"当前排污负荷: {load_current:.2f} t/d")
print(f"需削减: {load_reduction:.2f} t/d ({load_reduction/load_current*100:.0f}%)")

# ========== 绘图 ==========
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (a) Tennant法生态基流
ax1 = axes[0, 0]
ax1.fill_between(months, 0, Q_monthly_avg, alpha=0.2, color='#2196F3', label='天然径流')
ax1.plot(months, Q_monthly_avg, 'b-o', linewidth=2, markersize=6, label='月均流量')
for level_name, ratio in tennant_levels.items():
    ax1.axhline(Q_annual_avg*ratio, linestyle='--', alpha=0.6, label=f'Tennant {level_name}')
ax1.plot(months, eco_flow_recommended, 'r-s', linewidth=2.5, markersize=7, label='推荐生态基流')
ax1.set_xticks(months)
ax1.set_xticklabels(month_names, fontsize=9)
ax1.set_ylabel('流量 (m$^3$/s)', fontsize=11)
ax1.set_title('(a) Tennant法逐月生态基流', fontsize=12)
ax1.legend(fontsize=8, loc='upper left')
ax1.grid(True, alpha=0.3)

# (b) BOD沿程衰减
ax2 = axes[0, 1]
ax2.plot(x_km, L_x, 'r-', linewidth=2, label='BOD')
ax2.axhline(BOD_standard, color='orange', linestyle='--', label=f'III类标准 ({BOD_standard} mg/L)')
ax2.set_xlabel('距排污口距离 (km)', fontsize=11)
ax2.set_ylabel('BOD (mg/L)', fontsize=11)
ax2.set_title('(b) BOD沿程衰减', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# (c) DO沿程变化(氧垂曲线)
ax3 = axes[1, 0]
ax3.plot(x_km, DO_x, 'b-', linewidth=2.5, label='DO浓度')
ax3.axhline(DO_standard, color='red', linestyle='--', linewidth=1.5, label=f'III类标准 ({DO_standard} mg/L)')
ax3.axhline(DO_sat, color='gray', linestyle=':', label=f'饱和DO ({DO_sat} mg/L)')
if x_critical > 0:
    ax3.plot(x_critical, DO_critical, 'rv', markersize=12, zorder=5, label=f'临界点 ({x_critical:.1f}km)')
    ax3.annotate(f'DO={DO_critical:.2f} mg/L', xy=(x_critical, DO_critical),
                xytext=(x_critical+5, DO_critical-0.5), fontsize=10,
                arrowprops=dict(arrowstyle='->', color='red'))
ax3.fill_between(x_km, DO_standard, DO_x, where=DO_x<DO_standard,
                 alpha=0.3, color='red', label='不达标区间')
ax3.set_xlabel('距排污口距离 (km)', fontsize=11)
ax3.set_ylabel('DO (mg/L)', fontsize=11)
ax3.set_title('(c) 溶解氧沿程变化(氧垂曲线)', fontsize=12)
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# (d) 排污方案对比
ax4 = axes[1, 1]
scenarios_bod = [50, 100, 150, 200, 250]
for bod_s in scenarios_bod:
    L0_s = (Q_river * L_upstream + Q_waste * bod_s) / Q_mix
    D0_s = DO_sat - (Q_river * DO_upstream + Q_waste * DO_waste) / Q_mix
    D_s = (K1*L0_s/(K2-K1)) * (np.exp(-K1*t_days) - np.exp(-K2*t_days)) + D0_s*np.exp(-K2*t_days)
    DO_s = DO_sat - D_s
    ax4.plot(x_km, DO_s, linewidth=1.5, label=f'排污BOD={bod_s} mg/L')
ax4.axhline(DO_standard, color='red', linestyle='--', linewidth=1.5, label='III类标准')
ax4.set_xlabel('距排污口距离 (km)', fontsize=11)
ax4.set_ylabel('DO (mg/L)', fontsize=11)
ax4.set_title('(d) 不同排污强度下的DO响应', fontsize=12)
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "eco_water_quality.png"), dpi=300, bbox_inches='tight')
print(f"\n图片已保存: eco_water_quality.png")

# ========== KPI输出 ==========
print("\n===== KPI TABLE =====")
print("| 指标 | 数值 |")
print("|------|------|")
print(f"| 多年平均流量 | {Q_annual_avg:.1f} m3/s |")
print(f"| 推荐枯水期生态基流 | {Q_annual_avg*0.20:.1f} m3/s |")
print(f"| 推荐丰水期生态基流 | {Q_annual_avg*0.30:.1f} m3/s |")
print(f"| 混合后BOD | {L0:.2f} mg/L |")
print(f"| 临界点距离 | {x_critical:.1f} km |")
print(f"| 临界点最低DO | {DO_critical:.2f} mg/L |")
print(f"| 纳污能力 | {load_capacity:.2f} t/d |")
print(f"| 当前排污负荷 | {load_current:.2f} t/d |")
print(f"| 需削减比例 | {load_reduction/load_current*100:.0f}% |")
