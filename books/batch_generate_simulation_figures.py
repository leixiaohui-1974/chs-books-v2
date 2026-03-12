#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成Phase 4全部63章的数据曲线图
从每章的"仿真代码解读"部分提取Python代码，修改后执行生成图片
"""

import os
import re
import subprocess

# 9本书的章节配置
books_config = {
    'reservoir-operation-optimization': 8,
    'flood-forecasting-control': 8,
    'dam-safety-monitoring': 6,
    'river-sediment-dynamics': 6,
    'inland-waterway-navigation': 6,
    'ship-lock-automation': 5,
    'water-energy-food-nexus': 6,
    'digital-twin-river-basin': 8,
    'ai-for-water-engineering': 10,
}

base_dir = 'D:/cowork/教材/chs-books-v2/books'

def extract_python_code(chapter_file):
    """从章节文件提取仿真代码解读部分的Python代码"""
    with open(chapter_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 查找"## 仿真代码解读"部分
    match = re.search(r'## 仿真代码解读.*?```python\n(.*?)```', content, re.DOTALL)
    if match:
        return match.group(1)
    return None

def modify_script(code, book_name, chapter_num):
    """修改脚本：添加中文字体、禁用弹窗、保存图片"""

    # 在import matplotlib.pyplot之前添加Agg后端
    if 'import matplotlib.pyplot' in code:
        code = code.replace(
            'import matplotlib.pyplot as plt',
            'import matplotlib\nmatplotlib.use(\'Agg\')  # 禁用GUI\nimport matplotlib.pyplot as plt'
        )

    # 如果没有中文字体配置，添加
    if 'font.sans-serif' not in code:
        font_config = """
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
"""
        # 在第一个plt.之前插入
        code = re.sub(r'(plt\.(?:subplots|figure))', font_config + r'\1', code, count=1)

    # 修改savefig，确保保存到正确位置
    ch_name = f'ch{chapter_num:02d}'
    if 'plt.savefig' in code:
        code = re.sub(
            r'plt\.savefig\([\'"].*?[\'"]\s*,',
            f'plt.savefig(\'{ch_name}_simulation_result.png\',',
            code
        )
    else:
        # 如果没有savefig，在plt.show()前添加
        code = re.sub(
            r'plt\.show\(\)',
            f'plt.savefig(\'{ch_name}_simulation_result.png\', dpi=300, bbox_inches=\'tight\')\nprint(f"图片已保存: {ch_name}_simulation_result.png")\n# plt.show()  # 禁用弹窗',
            code
        )

    # 注释掉plt.show()
    if '# plt.show()' not in code:
        code = code.replace('plt.show()', '# plt.show()  # 禁用弹窗')

    # 确保有dpi=300
    if 'dpi=' not in code:
        code = re.sub(
            r'plt\.savefig\((.*?)\)',
            r'plt.savefig(\1, dpi=300, bbox_inches=\'tight\')',
            code
        )

    return code

def generate_figures():
    """批量生成所有数据曲线图"""
    total = 0
    success = 0
    failed = []

    for book, num_chapters in books_config.items():
        book_dir = os.path.join(base_dir, book)
        figures_dir = os.path.join(book_dir, 'figures')

        # 创建figures目录
        os.makedirs(figures_dir, exist_ok=True)

        print(f'\n=== {book} ===')

        for ch_num in range(1, num_chapters + 1):
            total += 1
            ch_file = os.path.join(book_dir, f'ch{ch_num:02d}.md')

            if not os.path.exists(ch_file):
                print(f'  [SKIP] ch{ch_num:02d}: 文件不存在')
                continue

            # 提取Python代码
            code = extract_python_code(ch_file)
            if not code:
                print(f'  [SKIP] ch{ch_num:02d}: 未找到Python代码')
                continue

            # 修改代码
            modified_code = modify_script(code, book, ch_num)

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
                    print(f'  [FAIL] ch{ch_num:02d}: {result.stderr[:100]}')
                    failed.append(f'{book}/ch{ch_num:02d}')
            except subprocess.TimeoutExpired:
                print(f'  [TIMEOUT] ch{ch_num:02d}: 执行超时')
                failed.append(f'{book}/ch{ch_num:02d}')
            except Exception as e:
                print(f'  [ERROR] ch{ch_num:02d}: {str(e)[:100]}')
                failed.append(f'{book}/ch{ch_num:02d}')

    # 总结
    print(f'\n=== 数据曲线图生成完成 ===')
    print(f'总计: {total}章')
    print(f'成功: {success}章')
    print(f'失败: {len(failed)}章')

    if failed:
        print(f'\n失败列表:')
        for item in failed:
            print(f'  - {item}')

if __name__ == '__main__':
    generate_figures()
