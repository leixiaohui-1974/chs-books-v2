import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.optimize import milp, LinearConstraint, Bounds

output_dir = r"D:\cowork\教材\chs-books-v2\books\integrated-energy-system-simulation-optimization\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 微电网日前经济调度优化 (MILP)
# 场景：风电、光伏、燃气轮机(CHP)和储能系统联合供电

t_end = 24
time = np.arange(t_end)

load_e = 500 + 200 * np.sin(np.pi * (time - 8) / 12)  
p_wind = 200 + 100 * np.cos(np.pi * time / 12)       
p_pv = np.zeros(24)
p_pv[7:18] = 400 * np.sin(np.pi * (time[7:18] - 7) / 11) 

price_elec = np.ones(24) * 0.6
price_elec[10:15] = 1.2; price_elec[18:21] = 1.2
price_elec[0:7] = 0.3; price_elec[23:] = 0.3
price_gas = 0.4 

# 变量 [p_chp(24), p_buy(24), p_charge(24), p_discharge(24), u_chp(24)] = 120 variables
# u_chp 是二元变量 (0或1)，表示燃气轮机是否开启
c = np.concatenate([np.ones(24)*price_gas, price_elec, np.ones(24)*0.01, np.ones(24)*0.01, np.zeros(24)])

A_eq = np.zeros((24, 120))
b_eq = load_e - p_wind - p_pv
for i in range(24):
    A_eq[i, i] = 1.0 
    A_eq[i, i+24] = 1.0 
    A_eq[i, i+48] = -1.0 
    A_eq[i, i+72] = 1.0 

E_max = 1000.0
A_ub = np.zeros((96, 120))
b_ub = np.zeros(96)
E_0 = 200.0

row = 0
# 储能约束
for i in range(24):
    for j in range(i+1):
        A_ub[row, j+48] = 1.0
        A_ub[row, j+72] = -1.0
    b_ub[row] = E_max - E_0
    row += 1
    
    for j in range(i+1):
        A_ub[row, j+48] = -1.0
        A_ub[row, j+72] = 1.0
    b_ub[row] = E_0
    row += 1

# Big-M 约束： p_chp <= M * u_chp
M = 400.0
for i in range(24):
    A_ub[row, i] = 1.0
    A_ub[row, i+96] = -M
    b_ub[row] = 0
    row += 1
    
    # 最小出力约束: p_chp >= 50 * u_chp
    A_ub[row, i] = -1.0
    A_ub[row, i+96] = 50.0
    b_ub[row] = 0
    row += 1

integrality = np.concatenate([np.zeros(96), np.ones(24)])
lb = np.concatenate([np.zeros(24), np.zeros(24), np.zeros(24), np.zeros(24), np.zeros(24)])
ub = np.concatenate([np.ones(24)*400, np.ones(24)*1000, np.ones(24)*200, np.ones(24)*200, np.ones(24)])
bounds = Bounds(lb, ub)

constraints = [
    LinearConstraint(A_eq, b_eq, b_eq),
    LinearConstraint(A_ub, -np.inf, b_ub)
]

res = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)

p_chp_opt = res.x[0:24]
p_buy_opt = res.x[24:48]
p_charge_opt = res.x[48:72]
p_discharge_opt = res.x[72:96]

fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(time, load_e, 'k--', label='Load')
ax1.bar(time, p_wind + p_pv, color='g', alpha=0.5, label='Renewables (Wind+PV)')
ax1.bar(time, p_chp_opt, bottom=p_wind+p_pv, color='orange', alpha=0.8, label='CHP (Gas)')
ax1.bar(time, p_buy_opt, bottom=p_wind+p_pv+p_chp_opt, color='blue', alpha=0.5, label='Grid Buy')
ax1.bar(time, p_discharge_opt, bottom=p_wind+p_pv+p_chp_opt+p_buy_opt, color='purple', alpha=0.8, label='Battery Discharging')

ax1.set_title('Microgrid Day-Ahead Economic Dispatch (MILP)')
ax1.set_xlabel('Hour')
ax1.set_ylabel('Power (kW)')
ax1.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "milp_dispatch_sim.png"), dpi=300)

df = pd.DataFrame([
    {'Total Cost (CNY)': round(res.fun, 2), 'CHP Gas Cost': round(np.sum(p_chp_opt*price_gas), 2), 'Grid Electricity Cost': round(np.sum(p_buy_opt*price_elec), 2)}
])
with open(os.path.join(output_dir, "dispatch_table.md"), "w") as f: f.write(df.to_markdown(index=False))

def create_schematic(path, title):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (1024, 512), color=(240, 245, 250))
    d = ImageDraw.Draw(img)
    d.text((40, 40), title, fill=(20, 40, 100))
    img.save(path)
create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch04: MILP Optimization")
