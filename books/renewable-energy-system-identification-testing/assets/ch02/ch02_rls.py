import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

output_dir = r"D:\cowork\教材\chs-books-v2\books\renewable-energy-system-identification-testing\assets\ch02"
os.makedirs(output_dir, exist_ok=True)

# 电机参数在线辨识 (RLS)
# 传递函数离散化模型: i(k) = -a1*i(k-1) + b1*v(k-1)
# 真实参数 R=0.5, L=0.01

R_true = 0.5
L_true = 0.01
dt = 0.001
time = np.arange(0, 2.0, dt)
N = len(time)

# v_load = 50 * np.sin(2 * np.pi * 50 * time)
v_load = np.random.normal(0, 10, N) # PRBS激励

i_true = np.zeros(N)
for k in range(1, N):
    di = (v_load[k-1] - R_true * i_true[k-1]) / L_true
    i_true[k] = i_true[k-1] + di * dt
    
i_meas = i_true + np.random.normal(0, 0.01, N)

theta = np.zeros((2, N)) # [a1, b1]^T
P = np.eye(2) * 1000.0
lambda_f = 0.99

for k in range(2, N):
    phi = np.array([[i_meas[k-1]], [v_load[k-1]]])
    K = P @ phi / (lambda_f + phi.T @ P @ phi)
    err = i_meas[k] - phi.T @ theta[:, k-1]
    theta[:, k] = theta[:, k-1] + (K * err).flatten()
    P = (P - K @ phi.T @ P) / lambda_f

a1_est = theta[0, :]
b1_est = theta[1, :]

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    R_est = (1 - a1_est) / b1_est
    L_est = dt / b1_est

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
ax1.plot(time, R_est, 'b-', label='Estimated R')
ax1.axhline(R_true, color='k', linestyle='--', label='True R')
ax1.set_ylim(0, 2.0)
ax1.legend()
ax1.grid(True)
ax1.set_title('Online Identification of Stator Resistance (RLS)')

ax2.plot(time, L_est, 'r-', label='Estimated L')
ax2.axhline(L_true, color='k', linestyle='--', label='True L')
ax2.set_ylim(0, 0.05)
ax2.legend()
ax2.grid(True)
ax2.set_title('Online Identification of Inductance (RLS)')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "rls_pmsm_sim.png"), dpi=300)

df = pd.DataFrame([
    {'Parameter': 'Resistance (R)', 'True Value': R_true, 'Estimated Value': round(R_est[-1], 3)},
    {'Parameter': 'Inductance (L)', 'True Value': L_true, 'Estimated Value': round(L_est[-1], 4)}
])
with open(os.path.join(output_dir, "rls_table.md"), "w") as f: f.write(df.to_markdown(index=False))

def create_schematic(path, title):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (1024, 512), color=(240, 245, 250))
    d = ImageDraw.Draw(img)
    d.text((40, 40), title, fill=(20, 40, 100))
    img.save(path)
create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch02: RLS Identification")
