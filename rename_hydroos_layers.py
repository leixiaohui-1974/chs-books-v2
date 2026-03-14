"""
HydroOS 三层术语统一重命名脚本

规则：
- PAI（物理AI引擎缩写）→ HydroCore
- CAI（认知AI引擎缩写）→ HydroClaw
- SIL（调度与智能层，HydroOS层名）→ HydroCore
- SAL（服务与应用层，HydroOS层名）→ HydroClaw
- DAL 保持不变

关键：SIL 在 xIL 语境（MIL/SIL/HIL 在环测试）中不改！
"""
import re
from pathlib import Path

BASE = Path(r"D:\cowork\教材\chs-books-v2")

# ============================================================
# Phase 1: PAI → HydroCore, CAI → HydroClaw (T1-CN)
# 这些是无歧义的替换
# ============================================================
PAI_CAI_REPLACEMENTS = [
    # 带括号的定义形式
    ("PAI（物理AI引擎）", "HydroCore（物理AI引擎）"),
    ("PAI（物理 AI 引擎）", "HydroCore（物理AI引擎）"),
    ("CAI（认知AI引擎）", "HydroClaw（认知AI引擎）"),
    ("CAI（认知 AI 引擎）", "HydroClaw（认知AI引擎）"),
    # 反向括号
    ("物理AI引擎（PAI）", "物理AI引擎（HydroCore）"),
    ("物理 AI 引擎（PAI）", "物理AI引擎（HydroCore）"),
    ("认知AI引擎（CAI）", "认知AI引擎（HydroClaw）"),
    ("认知 AI 引擎（CAI）", "认知AI引擎（HydroClaw）"),
    # 英文括号
    ("PAI(物理AI引擎)", "HydroCore(物理AI引擎)"),
    ("CAI(认知AI引擎)", "HydroClaw(认知AI引擎)"),
    ("物理AI引擎(PAI)", "物理AI引擎(HydroCore)"),
    ("认知AI引擎(CAI)", "认知AI引擎(HydroClaw)"),
    # 带斜杠的对照形式 (ch01, ch13)
    ("PAI / SIL", "HydroCore"),
    ("CAI / SAL", "HydroClaw"),
    ("PAI/SIL", "HydroCore"),
    ("CAI/SAL", "HydroClaw"),
    ("SIL/PAI", "HydroCore"),
    ("SAL/CAI", "HydroClaw"),
    # T2b 的 SIL/SAL 层名定义
    ("调度与智能层（Scheduling & Intelligence Layer, SIL）", "物理AI引擎层（HydroCore）"),
    ("调度与智能层（SIL）", "物理AI引擎层（HydroCore）"),
    ("调度与智能层(SIL)", "物理AI引擎层(HydroCore)"),
    ("服务与应用层（Service & Application Layer, SAL）", "认知AI引擎层（HydroClaw）"),
    ("服务与应用层（SAL）", "认知AI引擎层（HydroClaw）"),
    ("服务与应用层(SAL)", "认知AI引擎层(HydroClaw)"),
    # 独立的层名提及
    ("调度与智能层", "物理AI引擎层"),
    ("服务与应用层", "认知AI引擎层"),
]

def replace_pai_cai(text):
    """Phase 1: Replace PAI/CAI and SIL/SAL layer names (non-xIL context)."""
    count = 0
    for old, new in PAI_CAI_REPLACEMENTS:
        if old in text:
            n = text.count(old)
            text = text.replace(old, new)
            count += n
    return text, count

def replace_standalone_abbreviations(text):
    """Phase 2: Replace standalone PAI/CAI abbreviations (word boundary aware)."""
    count = 0

    # PAI as standalone word (not part of other words)
    # Match PAI not preceded/followed by alphanumeric
    pattern_pai = re.compile(r'(?<![A-Za-z])PAI(?![A-Za-z])')
    matches = pattern_pai.findall(text)
    if matches:
        text = pattern_pai.sub('HydroCore', text)
        count += len(matches)

    # CAI as standalone word
    pattern_cai = re.compile(r'(?<![A-Za-z])CAI(?![A-Za-z])')
    matches = pattern_cai.findall(text)
    if matches:
        text = pattern_cai.sub('HydroClaw', text)
        count += len(matches)

    return text, count

def replace_sal_layer(text):
    """Phase 3: Replace standalone SAL (HydroOS layer only, not in xIL context)."""
    count = 0
    # SAL is unambiguous - only used as HydroOS layer name
    pattern_sal = re.compile(r'(?<![A-Za-z])SAL(?![A-Za-z])')
    matches = pattern_sal.findall(text)
    if matches:
        text = pattern_sal.sub('HydroClaw', text)
        count += len(matches)
    return text, count

def replace_sil_layer(text):
    """Phase 4: Replace SIL as HydroOS layer name, NOT as xIL testing stage.

    SIL-as-layer patterns:
    - "SIL层"
    - "DAL→SIL→SAL" or "DAL/SIL/SAL"
    - "SIL 解决" / "SIL解决"
    - "SIL 的计算" / "SIL的"
    - References within HydroOS architecture context

    SIL-as-xIL patterns (DO NOT CHANGE):
    - "MIL/SIL/HIL"
    - "MIL→SIL→HIL"
    - "SIL（软件在环）"
    - "SiL"
    - "xIL"
    - "Software-in-the-Loop"
    - "SIL/HIL" (testing context)
    - "MIL+SIL"
    """
    count = 0
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        new_line = line

        # Skip lines that are clearly xIL testing context
        xil_indicators = [
            'MIL', 'HIL', 'xIL', 'XiL', 'PiL', 'OiL',
            '在环', '软件在环', 'Software-in-the-Loop',
            'in-the-Loop', 'in the loop',
            'Safety Integrity Level', '安全完整性',
        ]

        is_xil_context = any(ind in line for ind in xil_indicators)

        if is_xil_context:
            # In xIL context, only replace SIL when it's clearly a layer name
            # e.g., "DAL→SIL→SAL" pattern (all three present)
            if 'DAL' in line and ('SAL' in line or 'HydroClaw' in line):
                # This is HydroOS architecture, even in xIL-mentioning line
                new_line = re.sub(r'(?<![A-Za-z/])SIL(?![A-Za-z/（(])', 'HydroCore', new_line)
                if new_line != line:
                    count += 1
        else:
            # Not in xIL context - check if SIL appears as layer name
            if 'SIL' in line:
                # Additional check: is this about HydroOS layers?
                layer_indicators = [
                    'DAL', '设备抽象', 'HydroOS', '三层',
                    '物理AI', '认知AI', '引擎层',
                    'HydroCore', 'HydroClaw',
                ]
                is_layer_context = any(ind in line for ind in layer_indicators)

                if is_layer_context:
                    new_line = re.sub(r'(?<![A-Za-z])SIL(?![A-Za-z])', 'HydroCore', new_line)
                    if new_line != line:
                        count += 1
                else:
                    # Standalone SIL without clear context - check surrounding
                    # Be conservative: only replace if "SIL层" or "SIL 的" etc.
                    sil_layer_patterns = [
                        (r'SIL层', 'HydroCore层'),
                        (r'SIL 层', 'HydroCore 层'),
                        (r'SIL的', 'HydroCore的'),
                        (r'SIL 的', 'HydroCore 的'),
                        (r'SIL解决', 'HydroCore解决'),
                        (r'SIL 解决', 'HydroCore 解决'),
                    ]
                    for old_p, new_p in sil_layer_patterns:
                        if old_p in new_line:
                            new_line = new_line.replace(old_p, new_p)
                            count += 1

        new_lines.append(new_line)

    return '\n'.join(new_lines), count

def process_file(filepath):
    """Process a single file with all replacement phases."""
    text = filepath.read_text(encoding='utf-8')
    original = text
    total_count = 0

    # Phase 1: Named pattern replacements
    text, c = replace_pai_cai(text)
    total_count += c

    # Phase 2: Standalone PAI/CAI
    text, c = replace_standalone_abbreviations(text)
    total_count += c

    # Phase 3: Standalone SAL
    text, c = replace_sal_layer(text)
    total_count += c

    # Phase 4: SIL as layer name (careful)
    text, c = replace_sil_layer(text)
    total_count += c

    if text != original:
        filepath.write_text(text, encoding='utf-8')
        return total_count
    return 0

# ============================================================
# Main: Process all target files
# ============================================================

targets = []

# T1-CN: all ch*_final.md
for f in sorted((BASE / "T1-CN").glob("ch*_final.md")):
    targets.append(f)

# T2b: all ch*_final.md
for f in sorted((BASE / "T2b").glob("ch*_final.md")):
    targets.append(f)

# T2a: all ch*_final.md
for f in sorted((BASE / "T2a").glob("ch*_final.md")):
    targets.append(f)

# T3: all ch*.md
for f in sorted((BASE / "T3-Engineering").glob("ch*.md")):
    targets.append(f)

print(f"Processing {len(targets)} files...\n")

total_all = 0
for f in targets:
    n = process_file(f)
    if n > 0:
        rel = f.relative_to(BASE)
        print(f"  {rel}: {n} replacements")
        total_all += n

print(f"\nTotal: {total_all} replacements across all files")
