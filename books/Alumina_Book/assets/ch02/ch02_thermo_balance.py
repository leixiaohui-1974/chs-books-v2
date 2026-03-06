import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 氧化铝多效蒸发热质平衡模拟 (Multi-Effect Evaporation Thermo-Mass Balance)
# 模拟单效、双效、三效蒸发系统的蒸汽梯级利用率 (Steam Economy) 及其非线性耦合特性。

# 1. 物理参数假定 (简化模型)
# 进料参数
F_in = 100.0 # 进料量 t/h
X_in = 0.14  # 进料质量浓度 14%
T_in = 70.0  # 进料温度 °C

# 目标参数
X_out_target = 0.24 # 目标出料浓度 24%
# 根据质量守恒：F_in * X_in = L_out * X_out_target
L_out_target = F_in * X_in / X_out_target
# 总需要蒸发的水量
W_evap_total = F_in - L_out_target 

# 热力学常数 (假定为近似常数，简化非线性求解)
Cp_liq = 4.0 # 溶液比热容 kJ/(kg*K)
Lambda_steam = 2200.0 # 蒸汽潜热 kJ/kg (近似值，随压力变化)
DeltaT_BPE = 5.0 # 沸点升高 (Boiling Point Elevation) 

# 2. 核心机理函数：计算特定效数的能量平衡与蒸汽消耗
# 使用迭代逼近法求解各效的蒸发量分配
def solve_multi_effect(num_effects):
    # 假设各效的温度梯级是均匀分布的
    # 新鲜蒸汽温度 160°C，末效冷凝器温度 60°C
    T_steam = 160.0
    T_condenser = 60.0
    total_delta_T = T_steam - T_condenser - num_effects * DeltaT_BPE
    
    if total_delta_T <= 0:
        return None # 无法沸腾
        
    dT_per_effect = total_delta_T / num_effects
    
    # 初始化变量
    T_boil = np.zeros(num_effects)
    W_evap = np.zeros(num_effects) # 各效蒸发量
    Steam_in = 0.0 # 消耗的新鲜蒸汽
    
    # 设定各效沸点
    current_T = T_steam
    for i in range(num_effects):
        T_boil[i] = current_T - dT_per_effect - DeltaT_BPE
        current_T = T_boil[i]
        
    # 迭代求解热质平衡 (假设各效产生的二次蒸汽全部用于下一效加热)
    # 粗略初始猜测：总蒸发量平均分配
    W_evap[:] = W_evap_total / num_effects
    
    for _ in range(50): # 迭代 50 次以收敛
        L_current = F_in
        T_current = T_in
        
        # 第一效需要新鲜蒸汽
        # 显热加热进料 + 潜热蒸发 = 新鲜蒸汽潜热
        Q_sensible_1 = L_current * Cp_liq * max(0, T_boil[0] - T_current)
        Q_latent_1 = W_evap[0] * Lambda_steam
        Steam_in = (Q_sensible_1 + Q_latent_1) / Lambda_steam
        
        # 依次计算后续各效
        for i in range(1, num_effects):
            L_current -= W_evap[i-1]
            T_current = T_boil[i-1]
            
            # 第 i 效的热源是第 i-1 效的二次蒸汽
            Q_source = W_evap[i-1] * Lambda_steam
            # 显热部分 (可能是闪蒸，因为 T_current > T_boil[i])
            Q_sensible = L_current * Cp_liq * (T_current - T_boil[i])
            
            # 新的蒸发量
            W_evap[i] = (Q_source + Q_sensible) / Lambda_steam
            
        # 强制归一化以满足总蒸发量目标
        current_total_evap = np.sum(W_evap)
        W_evap = W_evap * (W_evap_total / current_total_evap)
        
    return Steam_in, W_evap, T_boil

# 3. 运行多组方案对比
effects = [1, 2, 3, 4, 5, 6]
steam_consumptions = []
economies = []

for n in effects:
    result = solve_multi_effect(n)
    if result:
        Steam_in, W_evap, T_boil = result
        steam_consumptions.append(Steam_in)
        # 蒸汽经济性 (Steam Economy) = 总蒸发量 / 消耗新鲜蒸汽
        economies.append(W_evap_total / Steam_in)
    else:
        steam_consumptions.append(np.nan)
        economies.append(np.nan)

# 4. 绘图：多效蒸发的非线性红利与极限
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# A. 蒸汽消耗量断崖式下降
ax1.plot(effects, steam_consumptions, 'b-o', markersize=10, linewidth=3)
ax1.set_xlabel('Number of Effects (效数)', fontsize=12)
ax1.set_ylabel('Fresh Steam Consumption (t/h)', fontsize=12, color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.set_title('Thermodynamic Benefit of Multi-Effect Evaporation', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.6)

# 标注边际效益递减
ax1.annotate('Diminishing Marginal Returns', xy=(4, steam_consumptions[3]), xytext=(3, steam_consumptions[3]+20),
             arrowprops=dict(facecolor='black', shrink=0.05))

# B. 蒸汽经济性 (Economy) 的非线性攀升
ax2.plot(effects, economies, 'r-s', markersize=10, linewidth=3)
ax2.plot([1, 6], [1, 6], 'k--', alpha=0.5, label='Theoretical Ideal (1t steam evaporates N t water)')

ax2.set_xlabel('Number of Effects (效数)', fontsize=12)
ax2.set_ylabel('Steam Economy (Evap / Steam)', fontsize=12, color='r')
ax2.tick_params(axis='y', labelcolor='r')
ax2.set_title('Steam Economy (汽耗比的倒数) Scaling', fontsize=14)
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "thermo_balance_sim.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
history = []
for idx, n in enumerate(effects):
    history.append({
        'System': f"{n}-Effect",
        'Total Evaporation (t/h)': round(W_evap_total, 1),
        'Fresh Steam Req (t/h)': round(steam_consumptions[idx], 1),
        'Steam Economy (t/t)': round(economies[idx], 2),
        'Equivalent Steam Ratio': round(1.0 / economies[idx], 3)
    })

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "multi_effect_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 占位图生成
def create_schematic(path, title, description):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (1024, 512), color=(240, 245, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 1014, 502], outline=(100, 100, 150), width=3)
    try: font_title = ImageFont.truetype('arial.ttf', 36); font_desc = ImageFont.truetype('arial.ttf', 24)
    except: font_title = ImageFont.load_default(); font_desc = ImageFont.load_default()
    d.text((40, 40), title, fill=(20, 40, 100), font=font_title)
    
    words = description.split()
    lines, current_line = [], []
    for word in words:
        current_line.append(word)
        if len(current_line) > 12: lines.append(' '.join(current_line)); current_line = []
    if current_line: lines.append(' '.join(current_line))
        
    y_offset = 120
    for line in lines:
        d.text((40, y_offset), line, fill=(50, 50, 50), font=font_desc)
        y_offset += 35
    img.save(path)

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch02: Multi-Effect Evaporation Physics", "Diagram showing 3 sequential evaporator tanks. Fresh steam enters tank 1 at high pressure. The boiling vapor from tank 1 enters the heating jacket of tank 2 at lower pressure, cascading energy through the system to drastically save steam.")

print("Files generated successfully.")
