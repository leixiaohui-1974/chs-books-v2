"""Generate 6 missing T1-CN figures using matplotlib."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# Chinese font setup
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = r"D:\cowork\教材\chs-books-v2\T1-CN\H"


def fig_08_01_cpss_architecture():
    """CPSS三层架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # Title
    ax.text(6, 6.7, 'CPSS 三层架构图', fontsize=16, fontweight='bold', ha='center', va='center')

    layers = [
        (5.0, '#7B1FA2', 'Social 层（社会空间）', ['多目标优化', '经济调度', '电网协调', '社会约束']),
        (3.3, '#1565C0', 'Cyber 层（信息空间）', ['MPC控制器', '状态观测器', '故障诊断', '数据融合']),
        (1.6, '#4CAF50', 'Physical 层（物理空间）', ['水力系统', '机械系统', '电气系统', '传感器网络']),
    ]

    for y, color, title, items in layers:
        rect = FancyBboxPatch((1, y), 10, 1.2, boxstyle="round,pad=0.1",
                               facecolor=color, alpha=0.15, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(1.5, y + 0.9, title, fontsize=13, fontweight='bold', color=color, va='center')
        for i, item in enumerate(items):
            bx = 2.0 + i * 2.5
            item_rect = FancyBboxPatch((bx, y + 0.15), 2.0, 0.55, boxstyle="round,pad=0.05",
                                        facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
            ax.add_patch(item_rect)
            ax.text(bx + 1.0, y + 0.42, item, fontsize=9, ha='center', va='center', color='black')

    # Arrows between layers
    for y_start, y_end, label_l, label_r in [
        (5.0, 4.55, '社会需求', '优化指令'),
        (3.3, 2.85, '控制指令', '状态反馈'),
    ]:
        ax.annotate('', xy=(4, y_start), xytext=(4, y_end),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
        ax.annotate('', xy=(8, y_end), xytext=(8, y_start),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
        ax.text(3.3, (y_start + y_end) / 2, label_l, fontsize=8, ha='center', va='center', color='#555')
        ax.text(8.7, (y_start + y_end) / 2, label_r, fontsize=8, ha='center', va='center', color='#555')

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'fig_08_01_cpss_architecture.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"OK: {path} ({os.path.getsize(path)} bytes)")


def fig_08_02_multiphysics_coupling():
    """水利系统多物理场耦合示意图 - Venn diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-4, 5)
    ax.axis('off')
    ax.set_aspect('equal')

    ax.text(0, 4.5, '水利系统多物理场耦合示意图', fontsize=16, fontweight='bold', ha='center')

    # Three overlapping ellipses
    from matplotlib.patches import Ellipse
    ellipses = [
        ((-1.2, 1.0), '#1565C0', '水力系统', 'H — 水头\nQ — 流量'),
        ((1.2, 1.0), '#4CAF50', '机械系统', 'ω — 转速\nMt — 转矩'),
        ((0, -0.8), '#FF7043', '电气系统', "E'q — 电势\nPe — 电功率"),
    ]

    for (cx, cy), color, title, params in ellipses:
        e = Ellipse((cx, cy), 4.5, 3.2, alpha=0.12, facecolor=color, edgecolor=color, linewidth=2)
        ax.add_patch(e)
        # Title outside
        tx = cx * 1.8
        ty = cy * 1.6 + (0.8 if cy > 0 else -0.8)
        ax.text(tx, ty, title, fontsize=14, fontweight='bold', color=color, ha='center', va='center')
        ax.text(tx, ty - 0.6, params, fontsize=10, ha='center', va='center', color='#333',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor=color))

    # Center label
    ax.text(0, 0.3, '7阶统一\n动态系统', fontsize=12, fontweight='bold', ha='center', va='center',
            color='#B71C1C',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFEBEE', edgecolor='#B71C1C', linewidth=1.5))

    # Coupling labels in overlap regions
    ax.text(-0.6, 1.8, '水力-机械\n耦合', fontsize=8, ha='center', va='center', color='#555', style='italic')
    ax.text(0.6, -0.1, '机械-电气\n耦合', fontsize=8, ha='center', va='center', color='#555', style='italic')
    ax.text(-0.9, -0.1, '水力-电气\n耦合', fontsize=8, ha='center', va='center', color='#555', style='italic')

    # Bottom note
    ax.text(0, -3.5, '多时间尺度：水力(秒级) — 机械(毫秒级) — 电气(微秒级)',
            fontsize=10, ha='center', va='center', color='#666',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5F5F5', edgecolor='#CCC'))

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'fig_08_02_multiphysics_coupling.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"OK: {path} ({os.path.getsize(path)} bytes)")


def fig_08_03_fusion_control():
    """CPSS框架三层融合控制流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis('off')

    ax.text(6, 8.7, 'CPSS 三层融合控制流程图', fontsize=16, fontweight='bold', ha='center')

    # Three layers top to bottom
    layers = [
        (6.5, '#7B1FA2', 'Social 层', '小时—天',
         [('多目标优化', 2.5), ('约束管理', 5.5), ('社会效益评估', 8.5)],
         '最优运行轨迹'),
        (4.0, '#1565C0', 'Cyber 层', '秒—分钟',
         [('MPC预测控制', 2.5), ('状态观测器', 5.5), ('故障诊断', 8.5)],
         '控制指令序列'),
        (1.5, '#4CAF50', 'Physical 层', '毫秒—秒',
         [('水力模型', 2.5), ('机械模型', 5.5), ('电气模型', 8.5)],
         '实际状态量'),
    ]

    for y, color, title, timescale, blocks, output in layers:
        # Layer background
        rect = FancyBboxPatch((0.5, y), 11, 1.8, boxstyle="round,pad=0.1",
                               facecolor=color, alpha=0.08, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        # Layer title
        ax.text(0.3, y + 0.9, title, fontsize=11, fontweight='bold', color=color,
                va='center', ha='center', rotation=90)
        # Timescale
        ax.text(11.8, y + 0.9, timescale, fontsize=8, color='#888', va='center', ha='center', rotation=90)
        # Blocks
        for label, bx in blocks:
            br = FancyBboxPatch((bx - 1.0, y + 0.3), 2.0, 1.0, boxstyle="round,pad=0.08",
                                 facecolor=color, alpha=0.25, edgecolor=color, linewidth=1.2)
            ax.add_patch(br)
            ax.text(bx, y + 0.8, label, fontsize=10, ha='center', va='center')
        # Output arrow label
        ax.text(10.5, y + 0.15, f'→ {output}', fontsize=8, color=color, va='center')

    # Downward arrows between layers
    for y_top, y_bot in [(6.5, 5.85), (4.0, 3.35)]:
        ax.annotate('', xy=(4, y_bot), xytext=(4, y_top),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=2))
        ax.annotate('', xy=(8, y_top), xytext=(8, y_bot),
                    arrowprops=dict(arrowstyle='->', color='#999', lw=1.5, linestyle='dashed'))

    # Safety envelope on right
    safety_rect = FancyBboxPatch((11.2, 1.5), 0.5, 6.8, boxstyle="round,pad=0.05",
                                  facecolor='#FF7043', alpha=0.15, edgecolor='#FF7043',
                                  linewidth=2, linestyle='dashed')
    ax.add_patch(safety_rect)
    ax.text(11.45, 4.9, '安\n全\n包\n络', fontsize=9, fontweight='bold',
            color='#FF7043', ha='center', va='center')

    # Labels for arrows
    ax.text(3.3, 6.2, '优化指令↓', fontsize=8, color='#333')
    ax.text(8.3, 6.2, '↑状态反馈', fontsize=8, color='#999')
    ax.text(3.3, 3.7, '控制指令↓', fontsize=8, color='#333')
    ax.text(8.3, 3.7, '↑状态量', fontsize=8, color='#999')

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'fig_08_03_fusion_control.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"OK: {path} ({os.path.getsize(path)} bytes)")


def fig_09_04_smith_predictor():
    """Smith预估补偿器结构图 - 经典控制框图"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')

    ax.text(7, 5.7, 'Smith预估补偿器结构图', fontsize=16, fontweight='bold', ha='center')

    # Helper function for blocks
    def draw_block(x, y, w, h, label, color='#1565C0', sublabel=None):
        rect = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.05",
                               facecolor=color, alpha=0.2, edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y + (0.1 if sublabel else 0), label, fontsize=11, ha='center', va='center',
                fontweight='bold')
        if sublabel:
            ax.text(x, y - 0.25, sublabel, fontsize=8, ha='center', va='center', color='#555')

    def draw_sum(x, y, label='+'):
        circle = plt.Circle((x, y), 0.2, facecolor='white', edgecolor='#333', linewidth=1.5)
        ax.add_patch(circle)
        ax.text(x, y, '∑', fontsize=10, ha='center', va='center')

    # Main loop: r → sum1 → C0 → sum2 → Gp·e^(-τs) → y
    # Signal path
    y_main = 3.5

    # Input r
    ax.annotate('', xy=(1.5, y_main), xytext=(0.5, y_main),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
    ax.text(0.3, y_main + 0.2, 'r', fontsize=13, fontweight='bold', color='#1565C0')

    # Sum1
    draw_sum(1.7, y_main)
    ax.text(1.4, y_main + 0.3, '+', fontsize=9, color='#333')
    ax.text(1.4, y_main - 0.3, '-', fontsize=9, color='#B71C1C')

    # Sum1 → C0
    ax.annotate('', xy=(3.0, y_main), xytext=(1.9, y_main),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
    ax.text(2.4, y_main + 0.2, 'e', fontsize=10, style='italic', color='#555')

    # Controller C0
    draw_block(3.8, y_main, 1.4, 0.8, 'C0', '#1565C0', '控制器')

    # C0 → sum_plant
    ax.annotate('', xy=(5.5, y_main), xytext=(4.5, y_main),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
    ax.text(5.0, y_main + 0.2, 'u', fontsize=10, style='italic', color='#555')

    # Plant Gp with delay
    draw_block(7.0, y_main, 2.2, 0.8, r'Gp$\cdot e^{-\tau_d s}$', '#4CAF50', '被控对象(含时滞)')

    # Plant → output y
    ax.annotate('', xy=(13.0, y_main), xytext=(8.1, y_main),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
    ax.text(13.2, y_main, 'y', fontsize=13, fontweight='bold', color='#4CAF50')

    # --- Smith predictor path (dashed box) ---
    y_smith = 1.5

    # Dashed box around Smith predictor
    smith_rect = FancyBboxPatch((4.8, 0.7), 5.6, 2.0, boxstyle="round,pad=0.1",
                                 facecolor='#FF7043', alpha=0.06, edgecolor='#FF7043',
                                 linewidth=2, linestyle='dashed')
    ax.add_patch(smith_rect)
    ax.text(7.6, 2.5, 'Smith预估器', fontsize=10, fontweight='bold', color='#FF7043')

    # Branch point from u
    ax.plot(5.2, y_main, 'ko', markersize=5)
    ax.annotate('', xy=(5.2, y_smith + 0.4), xytext=(5.2, y_main - 0.15),
                arrowprops=dict(arrowstyle='->', color='#FF7043', lw=1.5, linestyle='dashed'))

    # Internal model (no delay)
    draw_block(6.5, y_smith, 1.4, 0.7, 'Gp(hat)', '#FF7043', '内部模型')

    ax.annotate('', xy=(5.8, y_smith), xytext=(5.2, y_smith),
                arrowprops=dict(arrowstyle='->', color='#FF7043', lw=1.2, linestyle='dashed'))

    # Model output
    ax.annotate('', xy=(8.5, y_smith), xytext=(7.2, y_smith),
                arrowprops=dict(arrowstyle='->', color='#FF7043', lw=1.2, linestyle='dashed'))
    ax.text(7.8, y_smith + 0.2, 'y(hat)', fontsize=9, style='italic', color='#FF7043')

    # Sum2 for comparison
    draw_sum(8.7, y_smith)

    # y feedback down to sum2
    ax.plot(10.0, y_main, 'ko', markersize=5)
    ax.plot([10.0, 10.0], [y_main, y_smith], color='#333', lw=1.2)
    ax.annotate('', xy=(8.9, y_smith), xytext=(10.0, y_smith),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.2))
    ax.text(9.0, y_smith + 0.3, '+', fontsize=9, color='#333')
    ax.text(8.4, y_smith - 0.3, '-', fontsize=9, color='#B71C1C')

    # Sum2 output → feedback to sum1
    ax.plot([8.7, 8.7], [y_smith - 0.2, 0.5], color='#333', lw=1.2)
    ax.plot([8.7, 1.7], [0.5, 0.5], color='#333', lw=1.2)
    ax.annotate('', xy=(1.7, y_main - 0.2), xytext=(1.7, 0.5),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.2))

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'fig_09_04_smith_predictor.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"OK: {path} ({os.path.getsize(path)} bytes)")


def fig_14_03_sensor_fault():
    """HydroCore传感器故障检测与容错流程"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.axis('off')

    ax.text(5, 12.7, 'HydroCore 传感器故障检测与容错流程', fontsize=14, fontweight='bold', ha='center')

    # Flow chart elements
    def draw_rect(x, y, w, h, label, color='#1565C0'):
        rect = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.08",
                               facecolor=color, alpha=0.2, edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y, label, fontsize=10, ha='center', va='center', fontweight='bold')

    def draw_diamond(x, y, w, h, label, color='#FF7043'):
        diamond = plt.Polygon([(x, y+h/2), (x+w/2, y), (x, y-h/2), (x-w/2, y)],
                              facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(diamond)
        ax.text(x, y, label, fontsize=9, ha='center', va='center', fontweight='bold')

    def arrow(x1, y1, x2, y2, label=None, color='#333'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx + 0.2, my, label, fontsize=8, color='#555')

    # Step 1: Data acquisition
    draw_rect(5, 12, 3.5, 0.7, '① 传感器数据采集', '#1565C0')

    arrow(5, 11.65, 5, 11.1)

    # Step 2: Parallel checks
    draw_diamond(3.2, 10.5, 2.5, 1.0, 'Chi-Square\n卡方检验', '#FF7043')
    draw_diamond(6.8, 10.5, 2.5, 1.0, '冗余交叉\n验证', '#FF7043')

    ax.plot([5, 5], [11.1, 11.0], color='#333', lw=1.5)
    ax.plot([3.2, 6.8], [11.0, 11.0], color='#333', lw=1.5)
    ax.annotate('', xy=(3.2, 11.0), xytext=(3.2, 11.0),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
    ax.plot([3.2, 3.2], [11.0, 11.0], 'ko', markersize=4)
    ax.plot([6.8, 6.8], [11.0, 11.0], 'ko', markersize=4)

    # Normal path
    arrow(3.2, 9.95, 3.2, 9.3, '正常')
    draw_rect(3.2, 8.9, 2.2, 0.6, '正常运行', '#4CAF50')

    # Abnormal path
    arrow(6.8, 9.95, 6.8, 9.3, '异常')

    # Three-step isolation
    draw_rect(6.8, 8.9, 2.5, 0.6, '② 隔离故障传感器', '#FF7043')
    arrow(6.8, 8.55, 6.8, 8.0)
    draw_rect(6.8, 7.6, 2.5, 0.6, '③ 确认故障类型', '#FF7043')
    arrow(6.8, 7.25, 6.8, 6.7)

    # Decision: redundant sensor?
    draw_diamond(6.8, 6.1, 3.0, 1.0, '有冗余传感器?', '#7B1FA2')

    # Yes path
    arrow(8.3, 6.1, 9.0, 6.1, '是')
    draw_rect(9.0, 5.3, 2.0, 0.6, '切换冗余\n传感器', '#4CAF50')
    ax.plot([9.0, 9.0], [6.1, 5.6], color='#333', lw=1.5)

    # No path
    arrow(5.3, 6.1, 4.0, 6.1, '否')
    draw_rect(3.2, 5.3, 2.2, 0.6, '软测量/\n观测器替代', '#1565C0')
    ax.plot([3.2, 3.2], [6.1, 5.6], color='#333', lw=1.5)

    # Converge
    ax.plot([3.2, 3.2], [5.0, 4.5], color='#333', lw=1.5)
    ax.plot([9.0, 9.0], [5.0, 4.5], color='#333', lw=1.5)
    ax.plot([3.2, 9.0], [4.5, 4.5], color='#333', lw=1.5)
    ax.plot(6.1, 4.5, 'ko', markersize=4)
    arrow(6.1, 4.5, 6.1, 3.9)

    # Final: MPC continues
    draw_rect(6.1, 3.5, 3.5, 0.7, '④ MPC控制不中断', '#4CAF50')

    # Timing note
    ax.text(9.5, 8.5, '15~25秒\n完成全流程', fontsize=9, ha='center', va='center',
            color='#B71C1C', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFEBEE', edgecolor='#B71C1C'))

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'fig_14_03_sensor_fault.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"OK: {path} ({os.path.getsize(path)} bytes)")


def fig_14_07_evolution_roadmap():
    """HydroCore-HydroClaw双引擎技术演进路线图"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')

    ax.text(7, 6.7, 'HydroCore-HydroClaw 双引擎技术演进路线图', fontsize=15, fontweight='bold', ha='center')

    # Three phases
    phases = [
        (0.5, 4.3, '#90CAF9', '当前阶段\n2025-2027', '工具驱动',
         ['HydroCore主导', 'PID/MPC控制', '规则决策', 'WSAL L2'],
         '#1565C0'),
        (5.0, 4.3, '#42A5F5', '近期目标\n2028-2030', 'Agent自主',
         ['HydroClaw增强', '多模态感知', '场景自适应', 'WSAL L3'],
         '#0D47A1'),
        (9.5, 4.3, '#1565C0', '远期愿景\n2031+', '完全自主',
         ['双引擎融合', 'ODD自扩展', '群体智能', 'WSAL L4-L5'],
         '#0D47A1'),
    ]

    for x, y, color, title, subtitle, items, text_color in phases:
        rect = FancyBboxPatch((x, y - 2.5), 4.0, 3.5, boxstyle="round,pad=0.15",
                               facecolor=color, alpha=0.25, edgecolor=text_color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 2.0, y + 0.7, title, fontsize=12, fontweight='bold',
                ha='center', va='center', color=text_color)
        ax.text(x + 2.0, y - 0.1, subtitle, fontsize=11, ha='center', va='center',
                color=text_color, style='italic')

        for i, item in enumerate(items):
            ax.text(x + 0.5, y - 0.7 - i * 0.45, f'- {item}', fontsize=9,
                    va='center', color='#333')

    # Arrows between phases
    for x in [4.5, 9.0]:
        ax.annotate('', xy=(x + 0.5, 3.3), xytext=(x, 3.3),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=2.5))

    # Bottom timeline: WSAL levels
    ax.plot([1.5, 12.5], [1.2, 1.2], color='#1565C0', lw=2)
    wsal_labels = [('L2', 2.5, '#90CAF9'), ('L3', 7.0, '#42A5F5'), ('L4-L5', 11.5, '#1565C0')]
    for label, x, color in wsal_labels:
        ax.plot(x, 1.2, 'o', color=color, markersize=12)
        ax.text(x, 1.2, label, fontsize=8, ha='center', va='center', color='white', fontweight='bold')
    ax.text(7.0, 0.7, 'WSAL 自治等级演进', fontsize=10, ha='center', color='#555')

    # Milestone markers
    milestones = [
        (4.5, 1.6, 'xIL验证体系建成'),
        (9.0, 1.6, 'MAS+ODD自扩展'),
    ]
    for x, y, label in milestones:
        ax.text(x, y, f'▲ {label}', fontsize=8, ha='center', color='#B71C1C')

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'fig_14_07_evolution_roadmap.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"OK: {path} ({os.path.getsize(path)} bytes)")


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating 6 figures to {OUTPUT_DIR}\n")

    fig_08_01_cpss_architecture()
    fig_08_02_multiphysics_coupling()
    fig_08_03_fusion_control()
    fig_09_04_smith_predictor()
    fig_14_03_sensor_fault()
    fig_14_07_evolution_roadmap()

    print("\nAll 6 figures generated.")
