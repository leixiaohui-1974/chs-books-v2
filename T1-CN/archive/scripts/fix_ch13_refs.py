"""修复ch13参考文献：删除僵尸引用、调整自引率、重新编号"""
import re

with open('ch13_final.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Remove inline citations of [13-7] and [13-10] (to be deleted)
content = content.replace(' [13-7]，包括胶东调水工程从', '，包括胶东调水工程从')
content = content.replace(' [13-7]，其中约', '，其中约')
content = content.replace(' [13-10]，', '，')

# Step 2: References to delete
refs_to_delete = {7, 10, 17, 18, 19, 20, 21, 22, 23}

# New third-party references
new_refs = [
    'Malaterre P-O, Rogers D C, Schuurmans J. Classification of canal control algorithms [J]. Journal of Irrigation and Drainage Engineering, 1998, 124(1): 3-10.',
    'Litrico X, Fromion V. Modeling and Control of Hydrosystems [M]. London: Springer, 2009.',
    "Rossman L A. EPANET 2.2 User's Manual [R]. Cincinnati, OH: U.S. EPA, 2020.",
    'Smith R G. The Contract Net Protocol: High-level communication and control in a distributed problem solver [J]. IEEE Transactions on Computers, 1980, C-29(12): 1104-1113.',
    'Amin S, Litrico X, Sastry S S, et al. Cyber security of water SCADA systems—Part I: Analysis and experimentation of stealthy deception attacks [J]. IEEE Transactions on Control Systems Technology, 2013, 21(5): 1963-1970.',
]

# Step 3: Parse references
ref_pattern = re.compile(r'^\[13-(\d+)\]\s+(.+)$', re.MULTILINE)
existing_refs = []
for m in ref_pattern.finditer(content):
    num = int(m.group(1))
    text = m.group(2)
    if num not in refs_to_delete:
        existing_refs.append((num, text))

# Build old->new mapping
old_to_new = {}
new_num = 1
for old_num, text in existing_refs:
    old_to_new[old_num] = new_num
    new_num += 1
new_ref_start = new_num

print('Reference mapping:')
for old, new in sorted(old_to_new.items()):
    marker = ' *' if old != new else ''
    print(f'  [13-{old}] -> [13-{new}]{marker}')
print(f'New refs: [13-{new_ref_start}] to [13-{new_ref_start + len(new_refs) - 1}]')

# Step 4: Split body and refs
first_ref = content.index('\n[13-1] ')
body = content[:first_ref]
ref_section = content[first_ref:]

# Step 5: Replace citation numbers in body (descending order to avoid collisions)
# Use temporary placeholders first
for old_num in sorted(old_to_new.keys(), reverse=True):
    new_n = old_to_new[old_num]
    body = body.replace(f'[13-{old_num}]', f'[13-TEMP{new_n}]')

# Resolve placeholders
for new_n in range(1, new_num):
    body = body.replace(f'[13-TEMP{new_n}]', f'[13-{new_n}]')

# Step 6: Build new reference block
ref_lines = []
for old_num, text in existing_refs:
    new_n = old_to_new[old_num]
    ref_lines.append(f'[13-{new_n}] {text}')

for i, text in enumerate(new_refs):
    ref_lines.append(f'[13-{new_ref_start + i}] {text}')

new_ref_block = '\n\n'.join(ref_lines)

# Step 7: Combine (keep any section header before refs)
final = body + '\n' + new_ref_block + '\n'

with open('ch13_final.md', 'w', encoding='utf-8') as f:
    f.write(final)

# Verify
with open('ch13_final.md', 'r', encoding='utf-8') as f:
    verify = f.read()

first_ref_v = verify.index('\n[13-1] ')
body_v = verify[:first_ref_v]
cited = set(re.findall(r'\[13-(\d+)\]', body_v))
ref_nums_v = set(re.findall(r'^\[13-(\d+)\]', verify, re.MULTILINE))

print(f'\nVerification:')
print(f'  Body citations: {sorted(cited, key=int)}')
print(f'  Refs in list: {sorted(ref_nums_v, key=int)}')

zombies = ref_nums_v - cited
orphans = cited - ref_nums_v
print(f'  Zombies: {sorted(zombies, key=int)}')
print(f'  Orphans: {sorted(orphans, key=int)}')

# Self-citation check
lei_count = 0
total_refs = len(ref_nums_v)
for m in re.finditer(r'^\[13-(\d+)\]\s+(.+)$', verify, re.MULTILINE):
    text = m.group(2)
    if '雷晓辉' in text or '王浩' in text or '叶尚君' in text:
        lei_count += 1
        print(f'  Lei ref: [13-{m.group(1)}] {text[:50]}...')

print(f'  Self-citation: {lei_count}/{total_refs} = {lei_count/total_refs*100:.1f}%')
print(f'  Total lines: {len(verify.splitlines())}')
