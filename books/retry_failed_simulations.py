#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成失败的26章数据曲线图
"""

import os
import re
import subprocess

base_dir = 'D:/cowork/教材/chs-books-v2/books'

# 失败的章节列表
failed_chapters = [
    ('reservoir-operation-optimization', [2, 3, 6, 8]),
    ('flood-forecasting-control', [4, 6]),
    ('dam-safety-monitoring', [3, 5]),
    ('river-sediment-dynamics', [2]),
    ('inland-waterway-navigation', [4, 6]),
    ('ship-lock-automation', [5]),
    ('water-energy-food-nexus', [3]),
    ('digital-twin-river-basin', [5]),
    ('ai-for-water-engineering', [3, 5, 6, 7, 8, 9, 10]),
]

def extract_python_code(chapter_file):
    """从章节文件提取Python代码"""
    with open(chapter_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    match = re.search(r'## 仿真代码解读.*?```python\n(.*?)```', content, re.DOTALL)
    if match:
        return match.group(1)
    return None

def modify_script(code, ch_num):
    """修改脚本：添加中文字体、禁用弹窗、保存图片"""

    # 添加Agg后端
    if 'import matplotlib.pyplot' in code and 'matplotlib.use' not in code:
        code = code.replace(
            'import matplotlib.pyplot as plt',
            'import matplotlib\nmatplotlib.use(\'Agg\')\nimport matplotlib.pyplot as plt'
        )

    # 添加中文字体配置
    if 'font.sans-serif' not in code:
        font_config = "\nplt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']\nplt.rcParams['axes.unicode_minus'] = False\n"
        code = re.sub(r'(plt\.(?:subplots|figure))', font_config + r'\1', code, count=1)

    # 修改savefig
    ch_name = f'ch{ch_num:02d}'
    if 'plt.savefig' in code:
        code = re.sub(
            r'plt\.savefig\([\'"].*?[\'"]\s*,',
            f'plt.savefig(\'{ch_name}_simulation_result.png\',',
            code
        )
    else:
        code = re.sub(
            r'plt\.show\(\)',
            f'plt.savefig(\'{ch_name}_simulation_result.png\', dpi=300, bbox_inches=\'tight\')\nprint(f"图片已保存: {ch_name}_simulation_result.png")\n# plt.show()',
            code
        )

    # 注释掉plt.show()
    if '# plt.show()' not in code:
        code = code.replace('plt.show()', '# plt.show()')

    # 确保有dpi=300
    if 'dpi=' not in code and 'plt.savefig' in code:
        code = re.sub(
            r'plt\.savefig\(([^,]+)\)',
            r'plt.savefig(\1, dpi=300, bbox_inches=\'tight\')',
            code
        )

    return code

def retry_failed_chapters():
    """重新生成失败的章节"""
    total = 0
    success = 0
    failed = []

    for book, chapters in failed_chapters:
        book_dir = os.path.join(base_dir, book)
        figures_dir = os.path.join(book_dir, 'figures')

        os.makedirs(figures_dir, exist_ok=True)

        print(f'\n=== {book} ===')

        for ch_num in chapters:
            total += 1
            ch_file = os.path.join(book_dir, f'ch{ch_num:02d}.md')

            if not os.path.exists(ch_file):
                print(f'  [SKIP] ch{ch_num:02d}: 文件不存在')
                continue

            # 提取代码
            code = extract_python_code(ch_file)
            if not code:
                print(f'  [SKIP] ch{ch_num:02d}: 未找到Python代码')
                failed.append(f'{book}/ch{ch_num:02d}')
                continue

            # 修改代码
            modified_code = modify_script(code, ch_num)

            # 保存脚本
            script_file = os.path.join(figures_dir, f'ch{ch_num:02d}_simulation.py')
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(modified_code)

            # 执行脚本
            try:
                result = subprocess.run(
                    ['python', script_file],
                    cwd=figures_dir,
                    capture_output=True,
                    text=True,
                    timeout=180,  # 增加到180秒
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.returncode == 0:
                    print(f'  [OK] ch{ch_num:02d}: 图片生成成功')
                    success += 1
                else:
                    error_msg = result.stderr[:200] if result.stderr else 'Unknown error'
                    print(f'  [FAIL] ch{ch_num:02d}: {error_msg}')
                    failed.append(f'{book}/ch{ch_num:02d}')
            except subprocess.TimeoutExpired:
                print(f'  [TIMEOUT] ch{ch_num:02d}: 执行超时（180秒）')
                failed.append(f'{book}/ch{ch_num:02d}')
            except Exception as e:
                print(f'  [ERROR] ch{ch_num:02d}: {str(e)[:200]}')
                failed.append(f'{book}/ch{ch_num:02d}')

    # 总结
    print(f'\n=== 重新生成完成 ===')
    print(f'总计: {total}章')
    print(f'成功: {success}章')
    print(f'失败: {len(failed)}章')

    if failed:
        print(f'\n仍然失败的章节:')
        for item in failed:
            print(f'  - {item}')

if __name__ == '__main__':
    print('开始重新生成失败的26章数据曲线图...\n')
    retry_failed_chapters()
