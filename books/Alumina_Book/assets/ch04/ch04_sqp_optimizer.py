import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import minimize

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 核心算法实现：序列二次规划 (SQP) 在蒸发汽耗比寻优中的应用
# 场景：给定当前进料流量和浓度，求解一组阀门开度(蒸汽量)，
# 在满足“出料浓度>=240”的硬约束下，使“总蒸汽消耗”绝对最小化。

# 1. 简化的多效蒸发物理模型 (前向黑盒)
# x = [steam_flow, pressure_valve]
# 我们用一个简化的非线性函数来代替深度的热质平衡求解器
def evaporation_process(steam_flow, flash_valve):
    # 进料
    feed_flow = 300.0 # t/h
    feed_conc = 140.0 # g/L
    
    # 闪蒸阀门开度 (0~1) 影响内部二次蒸汽的回收率
    # 开度过大导致压力破坏，过小导致利用率低
    flash_efficiency = 1.0 - 2.0 * (flash_valve - 0.5)**2 
    
    # 蒸发量 = (原生蒸汽 * k + 闪蒸回收 * 蒸汽)
    # k为基础传热转化率
    k_base = 2.0
    evap_water = steam_flow * (k_base + 0.8 * flash_efficiency)
    
    # 质量守恒计算出料浓度
    out_flow = feed_flow - evap_water
    out_flow = max(1.0, out_flow) # 防止除零
    out_conc = (feed_flow * feed_conc) / out_flow
    
    return out_conc

# 2. 定义 SQP 优化问题
# 目标函数：最小化蒸汽消耗
def objective(x):
    steam_flow, flash_valve = x
    return steam_flow # 极其单纯，就是要省钱

# 约束条件函数：出料浓度 >= 240
def constraint_conc(x):
    steam_flow, flash_valve = x
    out_conc = evaporation_process(steam_flow, flash_valve)
    # scipy 约束形式: >= 0
    return out_conc - 240.0 

# 操作变量的物理边界
# 蒸汽阀门 20~100 t/h, 闪蒸阀门 0~1 (0% - 100%)
bounds = ((20.0, 100.0), (0.0, 1.0))

# 组装约束字典 (类型为不等式 ineq)
cons = {'type': 'ineq', 'fun': constraint_conc}

# 3. 运行 SQP 优化器 (SLSQP 算法)
# 故意给一个极差的初始瞎猜值
x0_bad = np.array([80.0, 0.1]) 
out_conc_bad = evaporation_process(x0_bad[0], x0_bad[1])

print("Starting SQP Optimization...")
# 利用 SLSQP (Sequential Least SQuares Programming)
res = minimize(objective, x0_bad, method='SLSQP', bounds=bounds, constraints=cons, options={'disp': True, 'maxiter': 50})

x_opt = res.x
out_conc_opt = evaporation_process(x_opt[0], x_opt[1])

# 4. 可视化寻优过程的“梯度下降与碰壁” (用网格扫描生成等高线辅助说明)
steam_grid = np.linspace(20, 90, 100)
flash_grid = np.linspace(0, 1, 100)
S, F = np.meshgrid(steam_grid, flash_grid)

# 计算整个平面的浓度场和目标函数场
Z_conc = np.zeros_like(S)
for i in range(100):
    for j in range(100):
        Z_conc[i, j] = evaporation_process(S[i, j], F[i, j])

fig, ax = plt.subplots(figsize=(10, 8))

# 画目标函数等高线 (蒸汽量，竖直的线)
CS_obj = ax.contour(S, F, S, levels=15, colors='blue', alpha=0.3)
ax.clabel(CS_obj, inline=True, fontsize=8, fmt='Steam=%1.0f')

# 画约束边界线 (浓度 = 240)
CS_cons = ax.contour(S, F, Z_conc, levels=[240.0], colors='red', linewidths=3)
ax.clabel(CS_cons, inline=True, fontsize=12, fmt='Constraint: Conc=240')

# 阴影填充不可行区域 (浓度 < 240)
ax.contourf(S, F, Z_conc, levels=[0, 240.0], colors='gray', alpha=0.3)
ax.text(30, 0.5, 'Infeasible Region\n(Concentration < 240)', color='black', fontsize=14, weight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.6))

# 画初始点与最优点
ax.plot(x0_bad[0], x0_bad[1], 'rs', markersize=10, label=f'Initial Guess\n(Steam={x0_bad[0]}, Conc={out_conc_bad:.1f})')
ax.plot(x_opt[0], x_opt[1], 'g*', markersize=15, label=f'SQP Optimum\n(Steam={x_opt[0]:.1f}, Conc={out_conc_opt:.1f})')

# 模拟优化轨迹 (用直线连接表示)
ax.annotate('', xy=(x_opt[0], x_opt[1]), xytext=(x0_bad[0], x0_bad[1]),
            arrowprops=dict(facecolor='green', shrink=0.05, width=2, headwidth=10))

ax.set_xlabel('Decision Variable 1: Steam Flow (t/h)', fontsize=12)
ax.set_ylabel('Decision Variable 2: Flash Valve Position (0-1)', fontsize=12)
ax.set_title('SQP Optimizer navigating the Non-linear Constraint Space', fontsize=14)
ax.legend(loc='upper right')
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "sqp_optimization_sim.png"), dpi=300, bbox_inches='tight')

# 5. 生成对比表格
history = [
    {'Status': 'Initial Blind Guess', 'Steam Flow (t/h)': x0_bad[0], 'Flash Valve': x0_bad[1], 'Output Conc.': round(out_conc_bad, 1), 'Constraint Satisfied?': 'Yes (Wasteful)'},
    {'Status': 'SQP Optimized Point', 'Steam Flow (t/h)': round(x_opt[0], 2), 'Flash Valve': round(x_opt[1], 2), 'Output Conc.': round(out_conc_opt, 1), 'Constraint Satisfied?': 'Yes (Exactly 240)'},
    {'Status': 'Financial Impact', 'Steam Flow (t/h)': f"-{round(x0_bad[0] - x_opt[0], 2)}", 'Flash Valve': 'Optimal tuned', 'Output Conc.': 'Zero giveaway', 'Constraint Satisfied?': 'Massive Steam Savings'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "sqp_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 生成占位图
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch04: SQP Optimizer & FastMCP", "Diagram showing a software architecture. An AI Agent connects via FastMCP protocol to a robust SQP math solver. The solver slides along a constraint boundary curve to find the lowest possible steam cost without breaking product quality rules.")

print("Files generated successfully.")
