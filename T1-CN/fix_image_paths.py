"""
全书图片路径修复脚本
将 GitHub raw URL 替换为本地相对路径 ./H/fig_XX_YY_name.png
"""
import re
import os
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 匹配 GitHub raw URL 图片引用
GITHUB_RAW_PATTERN = re.compile(
    r'(!\[([^\]]*)\]\()'  # ![alt](
    r'https?://raw\.githubusercontent\.com/[^)]+/H/([^)]+\.png)'  # URL
    r'(\))'  # )
)

# 匹配 <img src="..."> 形式
IMG_TAG_PATTERN = re.compile(
    r'(<img\s+[^>]*src=["\'])'
    r'https?://raw\.githubusercontent\.com/[^"\']+/H/([^"\']+\.png)'
    r'(["\'][^>]*>)'
)


def fix_chapter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    ch_num = re.search(r'ch(\d+)', os.path.basename(filepath))
    ch_num = ch_num.group(1) if ch_num else '00'

    changes = []

    # 修复 ![alt](url) 形式
    def replace_md_img(m):
        prefix, alt, filename, suffix = m.group(1), m.group(2), m.group(3), m.group(4)
        new_path = f'./H/{filename}'
        changes.append(f'  MD: {filename}')
        return f'{prefix}{new_path}{suffix}'

    content = GITHUB_RAW_PATTERN.sub(replace_md_img, content)

    # 修复 <img src="url"> 形式
    def replace_img_tag(m):
        prefix, filename, suffix = m.group(1), m.group(2), m.group(3)
        new_path = f'./H/{filename}'
        changes.append(f'  IMG: {filename}')
        return f'{prefix}{new_path}{suffix}'

    content = IMG_TAG_PATTERN.sub(replace_img_tag, content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'ch{ch_num}: 修复 {len(changes)} 处图片路径')
        for c in changes:
            print(c)
    else:
        print(f'ch{ch_num}: 无需修复')

    return len(changes)


def main():
    total = 0
    for f in sorted(glob.glob(os.path.join(SCRIPT_DIR, 'ch*_final.md'))):
        total += fix_chapter(f)
    print(f'\n总计修复 {total} 处图片路径')


if __name__ == '__main__':
    main()
