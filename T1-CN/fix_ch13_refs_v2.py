"""
Clean fix for ch13 references.
Current state: body citations are partially renumbered from two script runs.
Strategy: identify each citation by surrounding context, map to correct reference.
"""
import re

with open('ch13_final.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Split body and refs
ref_marker = '\n[13-1] Avizienis'
idx = content.index(ref_marker)
body = content[:idx]
old_ref_section = content[idx:]

# Step 1: Identify all citations in body by context and determine what they SHOULD reference
# Let's find each [13-X] and its surrounding 80 chars
citation_contexts = []
for m in re.finditer(r'\[13-(\d+)\]', body):
    num = int(m.group(1))
    start = max(0, m.start() - 60)
    end = min(len(body), m.end() + 60)
    ctx = body[start:end].replace('\n', ' ')
    citation_contexts.append((m.start(), m.end(), num, ctx))

# The correct reference list should be:
correct_refs = {
    1: ('Avizienis', 'Avizienis A, Laprie J C, Randell B, et al. Basic concepts and taxonomy of dependable and secure computing [J]. IEEE Transactions on Dependable and Secure Computing, 2004, 1(1): 11-33.'),
    2: ('OPC UA', 'OPC Foundation. OPC Unified Architecture Specification Part 1: Framework and Architecture [S]. OPCF, 2023.'),
    3: ('IEC 61131', 'IEC. IEC 61131-3: Programmable Controllers - Part 3: Programming Languages [S]. Geneva: IEC, 2013.'),
    4: ('Wang Hao', '王浩，雷晓辉，尚毅梓。南水北调中线工程智能调控与应急调度关键技术 [J]. 南水北调与水利科技(中英文)，2017, 15(2): 1-8.'),
    5: ('IEC 61588', 'IEC. IEC 61588: Precision clock synchronization protocol for networked measurement and control systems [S]. Geneva: IEC, 2019.'),
    6: ('Kopetz', 'Kopetz H. Time-Triggered Architecture: A Foundation for Dependable Embedded Systems [M]. Boston, MA: Springer, 2003.'),
    7: ('Buyalski', 'Buyalski C P, Ehler D G, Falvey H T, et al. Canal Systems Automation Manual, Volume 1 [M]. Denver: U.S. Bureau of Reclamation, 1991.'),
    8: ('Wooldridge', 'Wooldridge M. An Introduction to MultiAgent Systems [M]. 2nd ed. Hoboken, NJ: Wiley, 2009.'),
    9: ('Lee', 'Lee E A, Seshia S A. Introduction to Embedded Systems: A Cyber-Physical Systems Approach [M]. 2nd ed. Cambridge, MA: MIT Press, 2016.'),
    10: ('NIST CPS', 'NIST. Cyber-Physical Systems Framework Version 1.0 [R]. Gaithersburg, MD: NIST, 2015.'),
    11: ('ISA-95', 'IEC. IEC 62264 (ISA-95): Enterprise-Control System Integration [S]. Geneva: IEC, 2013.'),
    12: ('Lei CHS', '雷晓辉, 龙岩, 许慧敏, 王超. 水系统控制论：基本原理与理论框架[J]. 南水北调与水利科技(中英文), 2025, 23(04): 761-769.'),
    13: ('Lei 学科展望', '雷晓辉, 许慧敏, 何中政, 张峥. 水资源系统分析学科展望：从静态平衡到动态控制[J]. 南水北调与水利科技(中英文), 2025, 23(04): 770-777.'),
    14: ('Lei 自主水网', '雷晓辉, 苏承国, 龙岩, 许慧敏, 刘晓维. 自主水网：概念、架构与关键技术[J]. 南水北调与水利科技(中英文), 2025, 23(04): 778-786.'),
    15: ('Lei xIL', '雷晓辉, 许慧敏, 龙岩, 王超. 水系统在环测试体系：从MiL到PiL[J]. 南水北调与水利科技(中英文), 2025, 23(04): 787-795.'),
    16: ('Malaterre', 'Malaterre P-O, Rogers D C, Schuurmans J. Classification of canal control algorithms [J]. Journal of Irrigation and Drainage Engineering, 1998, 124(1): 3-10.'),
    17: ('Litrico', 'Litrico X, Fromion V. Modeling and Control of Hydrosystems [M]. London: Springer, 2009.'),
    18: ('Rossman', "Rossman L A. EPANET 2.2 User's Manual [R]. Cincinnati, OH: U.S. EPA, 2020."),
    19: ('Smith', 'Smith R G. The Contract Net Protocol: High-level communication and control in a distributed problem solver [J]. IEEE Transactions on Computers, 1980, C-29(12): 1104-1113.'),
    20: ('Amin', 'Amin S, Litrico X, Sastry S S, et al. Cyber security of water SCADA systems—Part I: Analysis and experimentation of stealthy deception attacks [J]. IEEE Transactions on Control Systems Technology, 2013, 21(5): 1963-1970.'),
}

# Step 2: Map each body citation to correct ref number by context
# We'll identify what each citation SHOULD be based on surrounding text
def identify_ref(ctx, current_num):
    """Determine the correct reference number based on context."""
    ctx_lower = ctx.lower()

    if 'avizienis' in ctx_lower or 'dependable' in ctx_lower:
        return 1
    if 'opc ua' in ctx_lower and 'redundancy' in ctx_lower:
        return 2
    if 'iec 61131' in ctx_lower or 'iec 61499' in ctx_lower:
        return 3
    if '南水北调中线' in ctx or '智能调控与应急调度' in ctx:
        return 4
    if 'ntp' in ctx_lower or 'ptp' in ctx_lower or '时钟' in ctx or 'precision clock' in ctx_lower:
        return 5
    if 'kopetz' in ctx_lower or '时间触发' in ctx:
        return 6
    if 'isa-95' in ctx_lower or 'iec 62264' in ctx_lower or '企业—控制' in ctx or 'enterprise' in ctx_lower:
        return 11  # was old [13-13]
    if 'buyalski' in ctx_lower or 'canal systems automation' in ctx_lower:
        return 7
    if 'wooldridge' in ctx_lower or '多智能体系统' in ctx:
        return 8
    if 'lee' in ctx_lower and ('cps' in ctx_lower or '信息物理' in ctx or 'cyber-physical' in ctx_lower or 'embedded' in ctx_lower):
        return 9
    if 'nist' in ctx_lower and 'cps' in ctx_lower:
        return 10

    # Lei team papers
    if '水系统控制论' in ctx and ('框架' in ctx or '原理' in ctx):
        return 12
    if '学科展望' in ctx or '静态平衡' in ctx or '动态控制' in ctx:
        return 13
    if '自主水网' in ctx or '概念、架构' in ctx or '无人驾驶' in ctx or '感知数字化' in ctx:
        return 14
    if '在环测试' in ctx or 'MiL' in ctx or 'MIL' in ctx or 'SIL' in ctx:
        return 15

    # SCADA references context
    if 'scada' in ctx_lower and ('融合' in ctx or '既有' in ctx):
        return 7  # Buyalski canal automation

    # Fallback: keep current
    return current_num

# Process each citation
replacements = []
for pos_start, pos_end, old_num, ctx in citation_contexts:
    new_num = identify_ref(ctx, old_num)
    if new_num != old_num:
        replacements.append((pos_start, pos_end, old_num, new_num, ctx[:80]))

print("Citations to remap:")
for start, end, old, new, ctx in replacements:
    print(f"  [{old}] -> [{new}]: {ctx}")

# Step 3: Apply replacements (reverse order to maintain positions)
# First, use placeholder approach to avoid collisions
new_body = body
# Replace all [13-X] with TEMP markers based on context
for pos_start, pos_end, old_num, ctx in reversed(citation_contexts):
    new_num = identify_ref(ctx, old_num)
    old_str = f'[13-{old_num}]'
    new_str = f'[TEMPREF-{new_num}]'
    new_body = new_body[:pos_start] + new_str + new_body[pos_end:]

# Resolve all TEMPREF markers
for i in range(1, 21):
    new_body = new_body.replace(f'[TEMPREF-{i}]', f'[13-{i}]')

# Step 4: Build reference list
ref_lines = []
for num in sorted(correct_refs.keys()):
    label, text = correct_refs[num]
    ref_lines.append(f'[13-{num}] {text}')

new_ref_block = '\n\n'.join(ref_lines)

# Step 5: Combine
final = new_body + '\n' + new_ref_block + '\n'

with open('ch13_final.md', 'w', encoding='utf-8') as f:
    f.write(final)

# Verify
with open('ch13_final.md', 'r', encoding='utf-8') as f:
    verify = f.read()

ref_start = verify.index('\n[13-1] ')
body_v = verify[:ref_start]
cited = set(re.findall(r'\[13-(\d+)\]', body_v))
ref_nums = set(re.findall(r'^\[13-(\d+)\]', verify, re.MULTILINE))

print(f'\nVerification:')
print(f'  Cited in body: {sorted(cited, key=int)}')
print(f'  In ref list: {sorted(ref_nums, key=int)}')
zombies = ref_nums - cited
orphans = cited - ref_nums
print(f'  Zombies: {sorted(zombies, key=int)} (new refs not yet cited: expected)')
print(f'  Orphans: {sorted(orphans, key=int)}')

# Self-citation
lei_refs = set()
for m in re.finditer(r'^\[13-(\d+)\]\s+(.+)$', verify, re.MULTILINE):
    text = m.group(2)
    if '雷晓辉' in text or '王浩' in text:
        lei_refs.add(m.group(1))
print(f'  Lei refs: {sorted(lei_refs, key=int)} ({len(lei_refs)}/{len(ref_nums)} = {len(lei_refs)/len(ref_nums)*100:.1f}%)')
print(f'  Total lines: {len(verify.splitlines())}')
