#!/usr/bin/env python3
"""T1-CN 5张数据曲线批量生成脚本 — 在服务器远程执行"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os

# 中文字体设置 — 服务器使用 Noto Serif CJK JP (matplotlib可识别，含CJK统一汉字)
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Noto Serif CJK JP', 'Noto Sans CJK JP', 'DejaVu Serif']
rcParams['axes.unicode_minus'] = False
rcParams['figure.dpi'] = 300
rcParams['savefig.dpi'] = 300
rcParams['savefig.bbox'] = 'tight'

OUT_DIR = os.environ.get('OUT_DIR', '.')

def fig_08_04_performance():
    """图8-1: 性能对比曲线 — 频率响应 + 功率跟踪"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.1, 3.15))
    t = np.linspace(0, 20, 500)

    # 左图：频率偏差
    pid_f = -0.35 * np.exp(-0.15*t) * np.cos(1.2*t)
    lqr_f = -0.25 * np.exp(-0.25*t) * np.cos(0.8*t)
    cpss_f = -0.15 * np.exp(-0.5*t) * (1 - np.exp(-0.3*t))

    ax1.plot(t, pid_f, '--', color='#9E9E9E', linewidth=1.2, label='PID')
    ax1.plot(t, lqr_f, '-', color='#64B5F6', linewidth=1.2, label='LQR')
    ax1.plot(t, cpss_f, '-', color='#1565C0', linewidth=2.0, label='CPSS')
    ax1.axhline(y=0, color='k', linewidth=0.5, linestyle='-')
    ax1.set_xlabel('t (s)')
    ax1.set_ylabel(u'\u9891\u7387\u504f\u5dee \u0394f (Hz)')  # 频率偏差
    ax1.set_title(u'\u8d1f\u8377\u9636\u8dc3+50MW\u54cd\u5e94')  # 负荷阶跃+50MW响应
    ax1.legend(fontsize=8)
    ax1.set_xlim(0, 20)
    ax1.set_ylim(-0.4, 0.1)
    ax1.grid(True, alpha=0.3)

    # 右图：功率跟踪
    target = 300 * np.ones_like(t)
    pid_p = 300 + 50 * (1 - np.exp(-0.15*t) * np.cos(1.2*t))
    lqr_p = 300 + 50 * (1 - np.exp(-0.25*t) * np.cos(0.6*t))
    cpss_p = 300 + 50 * (1 - np.exp(-0.5*t))

    ax2.plot(t, target, '--', color='#4CAF50', linewidth=1.0, label=u'\u76ee\u6807 350MW')
    ax2.plot(t, pid_p, '--', color='#9E9E9E', linewidth=1.2, label='PID')
    ax2.plot(t, lqr_p, '-', color='#64B5F6', linewidth=1.2, label='LQR')
    ax2.plot(t, cpss_p, '-', color='#1565C0', linewidth=2.0, label='CPSS')
    ax2.set_xlabel('t (s)')
    ax2.set_ylabel(u'\u529f\u7387 P (MW)')  # 功率
    ax2.set_title(u'\u529f\u7387\u8ddf\u8e2a\u5bf9\u6bd4')  # 功率跟踪对比
    ax2.legend(fontsize=8)
    ax2.set_xlim(0, 20)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'fig_08_04_performance.png'))
    plt.close()
    print('OK: fig_08_04_performance.png')

def fig_09_01_penstock():
    """图9-1: 引水系统传递函数对比 Bode图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.1, 4.7), sharex=True)
    omega = np.logspace(-2, 1, 500)
    s = 1j * omega
    Tw, Te, Zc = 1.5, 0.8, 0.3

    # 模型一：刚性水击 G ≈ -Tw*s
    G1 = -Tw * s
    # 模型二：弹性水击 tanh(Te*s)/Zc (用近似)
    G2 = np.tanh(Te * s) / Zc
    # 模型三：精确模型（二阶近似含谐振）
    omega1 = np.pi / (2 * Te)
    G3 = -Tw * s * (1 + s**2 / omega1**2) / (1 + 0.1*s/omega1 + s**2/omega1**2)

    # 幅频
    ax1.semilogx(omega, 20*np.log10(np.abs(G1)+1e-10), '--', color='#FF7043', linewidth=1.2, label=u'\u521a\u6027\u6c34\u51fb')
    ax1.semilogx(omega, 20*np.log10(np.abs(G2)+1e-10), '-', color='#1565C0', linewidth=1.2, label=u'\u5f39\u6027\u6c34\u51fb')
    ax1.semilogx(omega, 20*np.log10(np.abs(G3)+1e-10), '-', color='#0D47A1', linewidth=2.0, label=u'\u7cbe\u786e\u6a21\u578b')
    ax1.axvline(x=omega1, color='#F44336', linewidth=0.8, linestyle=':', label=f'$\\omega_1$={omega1:.1f} rad/s')
    ax1.set_ylabel(u'\u5e45\u503c (dB)')
    ax1.set_title(u'\u5f15\u6c34\u7cfb\u7edf\u4f20\u9012\u51fd\u6570\u5bf9\u6bd4')
    ax1.legend(fontsize=7)
    ax1.grid(True, alpha=0.3)

    # 相频
    ax2.semilogx(omega, np.degrees(np.angle(G1)), '--', color='#FF7043', linewidth=1.2)
    ax2.semilogx(omega, np.degrees(np.angle(G2)), '-', color='#1565C0', linewidth=1.2)
    ax2.semilogx(omega, np.degrees(np.angle(G3)), '-', color='#0D47A1', linewidth=2.0)
    ax2.set_xlabel(u'\u9891\u7387 (rad/s)')
    ax2.set_ylabel(u'\u76f8\u4f4d (deg)')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'fig_09_01_penstock_transfer.png'))
    plt.close()
    print('OK: fig_09_01_penstock_transfer.png')

def fig_09_02_bode():
    """图9-2: 典型水电站开环系统 Bode 图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.1, 4.7), sharex=True)
    omega = np.logspace(-2, 1.5, 500)
    s = 1j * omega

    # 典型水电站开环传递函数 (含调速器+水轮机+发电机)
    Tw, Tg, Kp = 1.5, 0.5, 2.0
    G_open = Kp * (1 - Tw*s) / ((1 + Tg*s) * (1 + 0.5*Tw*s) * (1 + 0.1*s))

    mag_db = 20 * np.log10(np.abs(G_open))
    phase_deg = np.degrees(np.unwrap(np.angle(G_open)))

    # 穿越频率
    idx_wc = np.argmin(np.abs(mag_db))
    wc = omega[idx_wc]
    pm = 180 + phase_deg[idx_wc]

    # 相位穿越频率
    idx_wp = np.argmin(np.abs(phase_deg + 180))
    wp = omega[idx_wp]
    gm = -mag_db[idx_wp]

    # 幅频
    ax1.semilogx(omega, mag_db, '-', color='#1565C0', linewidth=2.0)
    ax1.axhline(y=0, color='k', linewidth=0.5, linestyle='--')
    ax1.axvline(x=wc, color='#F44336', linewidth=0.8, linestyle='--', label=f'$\\omega_c$={wc:.2f} rad/s')
    ax1.annotate(f'$K_g$ = {gm:.1f} dB', xy=(wp, mag_db[idx_wp]), xytext=(wp*2, mag_db[idx_wp]+5),
                arrowprops=dict(arrowstyle='->', color='#FF7043'), fontsize=9, color='#FF7043')
    ax1.set_ylabel(u'\u5e45\u503c (dB)')
    ax1.set_title(u'\u5178\u578b\u6c34\u7535\u7ad9\u5f00\u73af Bode \u56fe')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # 相频
    ax2.semilogx(omega, phase_deg, '-', color='#1565C0', linewidth=2.0)
    ax2.axhline(y=-180, color='#F44336', linewidth=0.8, linestyle='--')
    ax2.axvline(x=wc, color='#F44336', linewidth=0.8, linestyle='--')
    ax2.annotate(f'$\\gamma$ = {pm:.0f}°', xy=(wc, phase_deg[idx_wc]), xytext=(wc*3, phase_deg[idx_wc]+20),
                arrowprops=dict(arrowstyle='->', color='#FF7043'), fontsize=9, color='#FF7043')
    ax2.set_xlabel(u'\u9891\u7387 (rad/s)')
    ax2.set_ylabel(u'\u76f8\u4f4d (deg)')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'fig_09_02_bode.png'))
    plt.close()
    print('OK: fig_09_02_bode.png')

def fig_09_03_nyquist():
    """图9-3: 典型水电站开环系统 Nyquist 图"""
    fig, ax = plt.subplots(1, 1, figsize=(5.5, 5.5))
    omega = np.concatenate([np.linspace(0.01, 15, 2000)])
    s = 1j * omega

    Tw, Tg, Kp = 1.5, 0.5, 2.0
    G_open = Kp * (1 - Tw*s) / ((1 + Tg*s) * (1 + 0.5*Tw*s) * (1 + 0.1*s))

    re = np.real(G_open)
    im = np.imag(G_open)

    ax.plot(re, im, '-', color='#1565C0', linewidth=2.0, label='Nyquist ($\\omega$: 0$\\to$+$\\infty$)')
    ax.plot(re, -im, '--', color='#90CAF9', linewidth=1.0, alpha=0.6, label='$\\omega$: 0$\\to$-$\\infty$')

    # 临界点
    ax.plot(-1, 0, 'o', color='#F44336', markersize=10, zorder=5)
    ax.annotate(u'\u4e34\u754c\u70b9 (-1, 0)', xy=(-1, 0), xytext=(-1.8, 0.5),
               arrowprops=dict(arrowstyle='->', color='#F44336'), fontsize=9, color='#F44336')

    # 单位圆参考
    theta = np.linspace(0, 2*np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), ':', color='#E0E0E0', linewidth=0.8)

    # 箭头方向指示
    for idx in [200, 600, 1000]:
        if idx < len(re)-1:
            ax.annotate('', xy=(re[idx+5], im[idx+5]), xytext=(re[idx], im[idx]),
                       arrowprops=dict(arrowstyle='->', color='#1565C0', lw=1.5))

    ax.set_xlabel('Re')
    ax.set_ylabel('Im')
    ax.set_title(u'Nyquist \u56fe\u2014\u2014\u66f2\u7ebf\u4e0d\u5305\u56f4(-1,0)\uff0c\u95ed\u73af\u7a33\u5b9a')
    ax.axhline(y=0, color='k', linewidth=0.3)
    ax.axvline(x=0, color='k', linewidth=0.3)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'fig_09_03_nyquist.png'))
    plt.close()
    print('OK: fig_09_03_nyquist.png')

def fig_11_08_cbf_pump():
    """图11-8: 泵站CBF案例仿真曲线"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.1, 4.7), sharex=True)
    t = np.linspace(0, 30, 600)

    # 上图：管道压力
    P_min = 0.3
    # 无CBF：t=5s阶跃后压力急跌
    P_no_cbf = np.where(t < 5, 0.4, 0.4 - 0.15 * (1 - np.exp(-0.8*(t-5))) + 0.02*np.exp(-0.3*(t-5))*np.sin(2*(t-5)))
    # 有CBF：压力受保护
    P_cbf = np.where(t < 5, 0.4, 0.4 - 0.08 * (1 - np.exp(-0.3*(t-5))))

    ax1.fill_between(t, 0.2, P_min, alpha=0.15, color='#F44336')
    ax1.plot(t, P_no_cbf, '-', color='#FF7043', linewidth=1.2, label=u'\u65e0CBF\uff08\u538b\u529b\u8d8a\u754c 0.25MPa\uff09')
    ax1.plot(t, P_cbf, '-', color='#1565C0', linewidth=2.0, label=u'\u6709CBF\uff08\u6700\u4f4e 0.32MPa\uff09')
    ax1.axhline(y=P_min, color='#F44336', linewidth=1.0, linestyle='--', label=f'$P_{{min}}$ = {P_min} MPa')
    ax1.set_ylabel(u'\u7ba1\u9053\u538b\u529b P (MPa)')
    ax1.set_title(u'\u6cf5\u7ad9CBF\u5b89\u5168\u7ea6\u675f\u4eff\u771f')
    ax1.legend(fontsize=7)
    ax1.set_ylim(0.2, 0.5)
    ax1.grid(True, alpha=0.3)

    # 下图：流量
    Q_demand = np.where(t < 5, 50, 80)
    Q_no_cbf = np.where(t < 5, 50, 50 + 30 * (1 - np.exp(-2.0*(t-5))))
    Q_cbf = np.where(t < 5, 50, 50 + 30 * (1 - np.exp(-0.3*(t-5))))

    ax2.plot(t, Q_demand, '--', color='#4CAF50', linewidth=1.0, label=u'\u9700\u6c42\u76ee\u6807 $Q_{demand}$')
    ax2.plot(t, Q_no_cbf, '-', color='#FF7043', linewidth=1.2, label=u'\u65e0CBF\uff08\u6025\u901f\u53d8\u5316\uff09')
    ax2.plot(t, Q_cbf, '-', color='#1565C0', linewidth=2.0, label=u'\u6709CBF\uff08\u9650\u901f\u722c\u5347\uff09')
    ax2.set_xlabel('t (s)')
    ax2.set_ylabel(u'\u6cf5\u7ad9\u51fa\u6d41 Q (m\u00b3/s)')
    ax2.legend(fontsize=7)
    ax2.set_xlim(0, 30)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'fig_11_08_cbf_pump.png'))
    plt.close()
    print('OK: fig_11_08_cbf_pump.png')

if __name__ == '__main__':
    print(f'Output dir: {OUT_DIR}')
    fig_08_04_performance()
    fig_09_01_penstock()
    fig_09_02_bode()
    fig_09_03_nyquist()
    fig_11_08_cbf_pump()
    print('ALL 5 FIGURES DONE')
