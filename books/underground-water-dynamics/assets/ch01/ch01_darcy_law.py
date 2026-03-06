import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\underground-water-dynamics\assets\ch01"
os.makedirs(output_dir, exist_ok=True)

# 达西定律实验模拟 (Darcy's Law Simulation)
# 模拟一维圆柱形砂柱透水实验

# 参数设置
L = 1.0           # 砂柱长度 m
D = 0.1           # 砂柱直径 m
A = np.pi * (D**2) / 4.0 # 横截面积 m^2

# 测试不同材质的渗透系数 K (m/s)
materials = {
    'Gravel (砾石)': 1e-2,
    'Coarse Sand (粗砂)': 1e-3,
    'Fine Sand (细砂)': 1e-4,
    'Silt (粉砂)': 1e-6
}

# 施加的水头差范围 (dH) m
dh_values = np.linspace(0.1, 2.0, 20)

plt.figure(figsize=(10, 6))

history = []

for name, K in materials.items():
    Q_values = []
    V_values = []
    
    for dh in dh_values:
        # 水力梯度 Hydraulic Gradient
        I = dh / L
        # 达西速度 (渗流速度) Darcy Velocity
        v = K * I
        # 流量 Discharge
        Q = v * A
        
        Q_values.append(Q * 1000 * 3600) # 转换为 L/h (升/小时) 以方便显示
        V_values.append(v)
        
        # 记录特定 dh 下的数据用于表格 (例如 dH = 1.0m)
        if abs(dh - 1.0) < 0.05:
            history.append({
                'Material': name,
                'Hydraulic Conductivity K (m/s)': K,
                'Head Diff dH (m)': 1.0,
                'Gradient I': round(1.0/L, 2),
                'Darcy Velocity v (m/s)': f"{v:.1e}",
                'Discharge Q (L/h)': round(Q * 1000 * 3600, 2)
            })

    plt.plot(dh_values, Q_values, marker='o', linestyle='-', linewidth=2, label=f'{name} ($K={K}$ m/s)')

plt.xlabel('Head Difference $\Delta H$ (m)', fontsize=12)
plt.ylabel('Discharge $Q$ (L/h)', fontsize=12)
plt.title("Darcy's Law: Discharge vs Head Difference for Various Soils", fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.yscale('log') # 使用对数坐标轴，因为渗透系数跨度太大
plt.savefig(os.path.join(output_dir, "darcy_law_plot.png"), dpi=300, bbox_inches='tight')

# 生成对比表格
df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "darcy_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

print("Files generated successfully.")
