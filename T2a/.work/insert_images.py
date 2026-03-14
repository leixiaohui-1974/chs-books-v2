"""Replace text placeholders with markdown image references in T2a chapters."""
import re
from pathlib import Path

BASE = Path(r"D:\cowork\教材\chs-books-v2\T2a")

# Mapping: (figure_id_pattern, image_path)
REPLACEMENTS = {
    "图1-1": ("CHS六元受控系统架构图", "assets/ch01/fig_01_01_chs_six_element.png"),
    "图1-2": ("八原理五层依赖结构图", "assets/ch01/fig_01_02_eight_principles.png"),
    "图1-3": ("八原理—本册章节映射图", "assets/ch01/fig_01_03_principles_chapter_map.png"),
    "图1-4": ("WNAL L0-L5阶梯图", "assets/ch01/fig_01_04_wnal_levels.png"),
    "图1-5": ("ODD与Safety Envelope的包含关系示意", "assets/ch01/fig_01_05_odd_safety_envelope.png"),
    "图1-6": ("本书结构导读图", "assets/ch01/fig_01_06_book_structure.png"),
    "图3-1": ("稳态—瞬态联合校核与控制上线流程图", "assets/ch03/fig_03_01_verification_flow.png"),
    "图3-2": ("三节点管网拓扑示意", "assets/ch03/fig_03_02_three_node_network.png"),
    "图7-1": ("MPC在CHS四层架构中的位置", "assets/ch07/fig_07_01_mpc_in_hdc.png"),
    "图7-2a": ("线性MPC vs NMPC选型决策树", "assets/ch07/fig_07_02a_mpc_nmpc_decision.png"),
    "图7-2": ("三渠池Θ矩阵稀疏结构示意", "assets/ch07/fig_07_02_theta_matrix.png"),
    "图7-3": ("集中式与分布式MPC架构对比", "assets/ch07/fig_07_03_centralized_vs_distributed.png"),
    "图7-4": ("MPC约束与安全包络三区间的对应关系", "assets/ch07/fig_07_04_mpc_safety_zones.png"),
    "图8-1": ("多目标优化的Pareto前沿示意", "assets/ch08/fig_08_01_pareto_front.png"),
    "图8-2": ("优化方法选择决策树", "assets/ch08/fig_08_02_algorithm_decision_tree.png"),
    "图10-1": ("红/黄/绿三区间安全分级示意图", "assets/ch10/fig_10_01_safety_three_zones.png"),
    "图11-1": ("水系统状态估计与数据融合双层架构", "assets/ch11/fig_11_01_data_fusion.png"),
    "图12-1": ("HDC三向信息流示意图", "assets/ch12/fig_12_01_hdc_info_flow.png"),
}

def process_file(filepath):
    text = filepath.read_text(encoding="utf-8")
    changed = False

    for fig_id, (caption, img_path) in REPLACEMENTS.items():
        # Match: [图X-Y: caption]\n{描述: ...}\n{尺寸: ...}
        # The pattern needs to handle multi-line blocks
        pattern = re.compile(
            r'\[' + re.escape(fig_id) + r'[:\s][^\]]*\]\s*\n'
            r'\{描述[:\s][^\}]*\}\s*\n'
            r'\{尺寸[:\s][^\}]*\}',
            re.DOTALL
        )

        replacement = f'![{fig_id} {caption}]({img_path})'

        new_text, count = pattern.subn(replacement, text)
        if count > 0:
            text = new_text
            changed = True
            print(f"  OK {filepath.name}: {fig_id} -> {img_path}")

    # Also try single-line placeholders (no description/size lines)
    for fig_id, (caption, img_path) in REPLACEMENTS.items():
        pattern = re.compile(r'\[' + re.escape(fig_id) + r'[:\s][^\]]*\](?!\()')
        if pattern.search(text):
            replacement = f'![{fig_id} {caption}]({img_path})'
            new_text, count = pattern.subn(replacement, text)
            if count > 0:
                text = new_text
                changed = True
                print(f"  OK {filepath.name}: {fig_id} (single-line) -> {img_path}")

    if changed:
        filepath.write_text(text, encoding="utf-8")

total = 0
for md in sorted(BASE.glob("ch*_final.md")):
    print(f"Processing {md.name}...")
    process_file(md)

print("\nDone!")
