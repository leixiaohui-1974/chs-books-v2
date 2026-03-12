#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成Phase 4全部126张架构图/拓扑图/概念图
使用nano-banana-pro（Gemini 3 Pro）生成
"""

import os
import subprocess
import time

# 9本书的章节配置
books_config = {
    'reservoir-operation-optimization': {
        'name': '水库调度优化与决策',
        'chapters': 8,
    },
    'flood-forecasting-control': {
        'name': '洪水预报与防洪调度',
        'chapters': 8,
    },
    'dam-safety-monitoring': {
        'name': '大坝安全监测与预警',
        'chapters': 6,
    },
    'river-sediment-dynamics': {
        'name': '河流泥沙动力学与河床演变',
        'chapters': 6,
    },
    'inland-waterway-navigation': {
        'name': '内河航道与通航水力学',
        'chapters': 6,
    },
    'ship-lock-automation': {
        'name': '船闸调度优化与自动化',
        'chapters': 5,
    },
    'water-energy-food-nexus': {
        'name': '水-能源-粮食纽带关系',
        'chapters': 6,
    },
    'digital-twin-river-basin': {
        'name': '流域数字孪生与智能决策',
        'chapters': 8,
    },
    'ai-for-water-engineering': {
        'name': '人工智能与水利水电工程',
        'chapters': 10,
    },
}

base_dir = 'D:/cowork/教材/chs-books-v2/books'
nano_script = 'D:/cowork/openclaw-sync/skills/nano-banana-pro/scripts/generate_image.py'

# 统一配色方案
COLOR_SCHEME = """
要求：
1. 中文标注，宋体/黑体
2. 统一配色方案：
   - 主色：深蓝#1565C0（水/控制）
   - 辅色1：绿色#4CAF50（安全/正常）
   - 辅色2：紫色#7B1FA2（认知AI）
   - 辅色3：橙红#FF7043（警告/扰动）
   - 背景：白色，辅助线#E0E0E0
3. 扁平矢量风格，白底
4. 180mm × 120mm，300dpi
5. 学术教材风格，清晰易读
6. 避免过度装饰，信息密度适中
"""

def read_chapter_title(book_dir, ch_num):
    """读取章节标题"""
    ch_file = os.path.join(book_dir, f'ch{ch_num:02d}.md')
    if not os.path.exists(ch_file):
        return f'第{ch_num}章'

    with open(ch_file, 'r', encoding='utf-8', errors='ignore') as f:
        first_line = f.readline().strip()
        # 提取# 后的标题
        if first_line.startswith('#'):
            return first_line.lstrip('#').strip()
    return f'第{ch_num}章'

def generate_architecture_prompt(book_name, chapter_title, ch_num):
    """生成架构图提示词"""
    # 根据章节号和书名定制提示词
    base_prompt = f"""为教材《{book_name}》{chapter_title}生成系统架构图。

内容：展示本章核心系统架构或技术框架。"""

    # 根据章节号添加具体内容
    if ch_num == 1:
        specific = "展示整体概览架构，包含主要组成部分和它们之间的关系。"
    elif ch_num == 2:
        specific = "展示理论框架或方法体系，包含关键概念和层次结构。"
    elif ch_num == 3:
        specific = "展示技术路线或算法流程，包含主要步骤和数据流。"
    else:
        specific = "展示系统组成或工程实施架构，包含关键模块和接口关系。"

    return base_prompt + "\n" + specific + "\n" + COLOR_SCHEME

def generate_concept_prompt(book_name, chapter_title, ch_num):
    """生成概念图提示词"""
    return f"""为教材《{book_name}》{chapter_title}生成概念示意图。

内容：用简洁的图形和图标展示本章核心概念或物理过程。
风格：概念化、抽象化，避免过多细节。
{COLOR_SCHEME}"""

def generate_figures_with_nano():
    """使用nano批量生成架构图和概念图"""
    total = 0
    success = 0
    failed = []

    # 设置API key
    os.environ['GEMINI_API_KEY'] = 'AIzaSyDgYPmfmRezC1NURx86z_n8xV_hn6z-iBY'

    # 检查nano脚本是否存在
    if not os.path.exists(nano_script):
        print(f'错误: nano脚本不存在: {nano_script}')
        return

    for book_id, config in books_config.items():
        book_name = config['name']
        num_chapters = config['chapters']
        book_dir = os.path.join(base_dir, book_id)
        figures_dir = os.path.join(book_dir, 'figures')

        os.makedirs(figures_dir, exist_ok=True)

        print(f'\n=== {book_name} ===')

        for ch_num in range(1, num_chapters + 1):
            chapter_title = read_chapter_title(book_dir, ch_num)
            ch_name = f'ch{ch_num:02d}'

            # 生成架构图
            total += 1
            arch_prompt = generate_architecture_prompt(book_name, chapter_title, ch_num)
            arch_file = f'{ch_name}_architecture.png'

            print(f'  生成 {ch_name} 架构图...')
            try:
                result = subprocess.run(
                    ['python', nano_script,
                     '--prompt', arch_prompt,
                     '--filename', arch_file],
                    cwd=figures_dir,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.returncode == 0 and os.path.exists(os.path.join(figures_dir, arch_file)):
                    print(f'    [OK] 架构图生成成功')
                    success += 1
                else:
                    print(f'    [FAIL] {result.stderr[:100]}')
                    failed.append(f'{book_id}/{ch_name}_architecture')

                time.sleep(2)  # 避免API限流

            except Exception as e:
                print(f'    [ERROR] {str(e)[:100]}')
                failed.append(f'{book_id}/{ch_name}_architecture')

            # 生成概念图
            total += 1
            concept_prompt = generate_concept_prompt(book_name, chapter_title, ch_num)
            concept_file = f'{ch_name}_concept.png'

            print(f'  生成 {ch_name} 概念图...')
            try:
                result = subprocess.run(
                    ['python', nano_script,
                     '--prompt', concept_prompt,
                     '--filename', concept_file],
                    cwd=figures_dir,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.returncode == 0 and os.path.exists(os.path.join(figures_dir, concept_file)):
                    print(f'    [OK] 概念图生成成功')
                    success += 1
                else:
                    print(f'    [FAIL] {result.stderr[:100]}')
                    failed.append(f'{book_id}/{ch_name}_concept')

                time.sleep(2)  # 避免API限流

            except Exception as e:
                print(f'    [ERROR] {str(e)[:100]}')
                failed.append(f'{book_id}/{ch_name}_concept')

    # 总结
    print(f'\n=== nano图片生成完成 ===')
    print(f'总计: {total}张')
    print(f'成功: {success}张')
    print(f'失败: {len(failed)}张')

    if failed:
        print(f'\n失败列表:')
        for item in failed:
            print(f'  - {item}')

if __name__ == '__main__':
    print('开始批量生成架构图和概念图...')
    print('注意: 需要设置GEMINI_API_KEY环境变量')
    generate_figures_with_nano()
