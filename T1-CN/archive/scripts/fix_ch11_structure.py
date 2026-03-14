"""Fix ch11 structure: deduplicate section numbers, move CBF/Intl before summary, fix image paths and figure numbers."""
import re

with open('ch11_final.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Fix image paths (P0-4)
replacements = {
    './H/fig_11_01_safety_envelope.png': './H/fig_11_01.png',
    './H/fig_11_02_xil_wnal.png': './H/fig_11_02.png',
    './H/fig_11_03_safety_wnal_evolution.png': './H/fig_11_03.png',
    './H/fig_11_04_p4_p5_synergy.png': './H/fig_11_04.png',
}
for old, new in replacements.items():
    content = content.replace(old, new)

# Fix missing fig_11_05
content = content.replace(
    '![图11-5: L2→L3 跃迁的验证路径](./H/fig_11_05_l2_l3_verification_path.png)',
    '<!-- 图11-5: L2→L3 跃迁的验证路径 [待生成] -->'
)

lines = content.split('\n')

# Step 2: Identify the duplicate sections at end of file
# The "good" sections are lines 0 to line where first §11.15 小结 starts
# The "displaced" sections start from the second §11.7 (CBF) at ~L1221

first_summary_idx = None
cbf_dup_idx = None
second_summary_idx = None
intl_dup_idx = None
refs_idx = None
recommend_idx = None
exercises_idx = None
glossary_idx = None

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == '## 11.15 本章小结':
        first_summary_idx = i
    elif stripped.startswith('## 推荐阅读'):
        recommend_idx = i
    elif stripped.startswith('## 本章练习'):
        exercises_idx = i
    elif stripped.startswith('## 本章术语表'):
        glossary_idx = i
    elif '控制屏障函数' in stripped and stripped.startswith('## 11.'):
        cbf_dup_idx = i
    elif stripped.startswith('## 11.8 本章小结') or (stripped.startswith('## 11.') and '本章小结' in stripped and i > 1200):
        second_summary_idx = i
    elif '国际标准对比' in stripped and stripped.startswith('## 11.'):
        intl_dup_idx = i
    elif stripped.startswith('## 本章参考文献'):
        refs_idx = i

print(f"First summary: L{first_summary_idx+1}")
print(f"Recommend: L{recommend_idx+1}")
print(f"Exercises: L{exercises_idx+1}")
print(f"Glossary: L{glossary_idx+1}")
print(f"CBF dup: L{cbf_dup_idx+1}")
print(f"Second summary: L{second_summary_idx+1}")
print(f"Intl dup: L{intl_dup_idx+1}")
print(f"Refs: L{refs_idx+1}")

# Step 3: Extract sections
# Main body: lines[0:first_summary_idx]
main_body = lines[:first_summary_idx]

# First summary block: lines[first_summary_idx:recommend_idx or exercises_idx]
first_summary = lines[first_summary_idx:recommend_idx]

# Recommend + exercises + glossary: lines[recommend_idx:glossary_end]
# Find end of glossary (next ## or cbf_dup_idx)
rec_ex_glos = lines[recommend_idx:cbf_dup_idx]

# CBF section: lines[cbf_dup_idx:second_summary_idx]
cbf_section = lines[cbf_dup_idx:second_summary_idx]

# Second summary: lines[second_summary_idx:intl_dup_idx]
second_summary = lines[second_summary_idx:intl_dup_idx]

# Intl section: lines[intl_dup_idx:refs_idx]
intl_section = lines[intl_dup_idx:refs_idx]

# Refs: lines[refs_idx:]
refs = lines[refs_idx:]

# Step 4: Renumber and fix
# CBF becomes §11.15
cbf_text = '\n'.join(cbf_section)
cbf_text = re.sub(r'## 11\.\d+ 控制屏障函数', '## 11.15 控制屏障函数', cbf_text)
cbf_text = re.sub(r'### 11\.\d+\.(\d+)', r'### 11.15.\1', cbf_text)

# Fix CBF figure numbers (11-1 -> 11-6, etc.) - only in CBF section
cbf_text = re.sub(r'图11-1([:：\s*])', r'图11-6\1', cbf_text)
cbf_text = cbf_text.replace('**图11-1**:', '**图11-6**:')
cbf_text = re.sub(r'图11-2([:：\s*])', r'图11-7\1', cbf_text)
cbf_text = cbf_text.replace('**图11-2**:', '**图11-7**:')
cbf_text = re.sub(r'图11-3([:：\s*])', r'图11-8\1', cbf_text)
cbf_text = cbf_text.replace('**图11-3**:', '**图11-8**:')

# Fix CBF image paths
cbf_text = cbf_text.replace('./figures/ch11_cbf_safe_set.png', './H/fig_11_06.png')
cbf_text = cbf_text.replace('./figures/ch11_cbf_qp_architecture.png', './H/fig_11_07.png')
# ch11_cbf_pump_case.png exists in figures/, keep it

# Intl becomes §11.16
intl_text = '\n'.join(intl_section)
intl_text = re.sub(r'## 11\.\d+ 国际标准', '## 11.16 国际标准', intl_text)
intl_text = re.sub(r'### 11\.\d+\.(\d+)', r'### 11.16.\1', intl_text)

# Merge first and second summaries -> §11.17
# Keep first summary content, append unique content from second summary
first_sum_text = '\n'.join(first_summary)
first_sum_text = first_sum_text.replace('## 11.15 本章小结', '## 11.17 本章小结')
# Update references to moved sections
first_sum_text = first_sum_text.replace('（§11.16）', '（§11.15）')
first_sum_text = first_sum_text.replace('（§11.17）', '（§11.16）')

# Step 5: Reassemble
# Order: main_body + CBF(§11.15) + Intl(§11.16) + Summary(§11.17) + Recommend + Exercises + Glossary + Refs
output = '\n'.join(main_body) + '\n'
output += '\n---\n\n' + cbf_text.strip() + '\n'
output += '\n---\n\n' + intl_text.strip() + '\n'
output += '\n---\n\n' + first_sum_text.strip() + '\n'
output += '\n---\n\n' + '\n'.join(rec_ex_glos).strip() + '\n'
output += '\n---\n\n' + '\n'.join(refs) + '\n'

with open('ch11_final.md', 'w', encoding='utf-8') as f:
    f.write(output)

# Verification
with open('ch11_final.md', 'r', encoding='utf-8') as f:
    verify = f.read()

sections = re.findall(r'^## 11\.(\d+)', verify, re.MULTILINE)
print(f'\nSection numbers: {sections}')

# Check for duplicate section numbers
from collections import Counter
dupes = {k: v for k, v in Counter(sections).items() if v > 1}
if dupes:
    print(f'DUPLICATE sections: {dupes}')
else:
    print('No duplicate sections')

figs = sorted(set(re.findall(r'图11-(\d+)', verify)), key=int)
print(f'Figure refs: {figs}')
print(f'Total lines: {len(verify.splitlines())}')
