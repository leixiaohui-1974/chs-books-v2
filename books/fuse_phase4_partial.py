#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 部分融合脚本 - 融合已完成的Gemini和Codex输出
"""
import os
import re

# 已完成的Gemini章节（38章）
gemini_done = {
    'reservoir-operation-optimization': [1, 2, 3, 4, 5],
    'flood-forecasting-control': [1, 2, 3, 4, 5],
    'dam-safety-monitoring': [1, 2, 3],
    'river-sediment-dynamics': [1, 2, 3, 4],
    'inland-waterway-navigation': [1, 2, 3, 4, 5],
    'ship-lock-automation': [1, 2, 3, 4, 5],
    'water-energy-food-nexus': [1, 2, 3, 4],
    'digital-twin-river-basin': [1, 2, 3],
    'ai-for-water-engineering': [1, 2, 3, 4],
}

# 已完成的Codex章节（21章）
codex_done = {
    'reservoir-operation-optimization': [1],
    'flood-forecasting-control': [1],
    'dam-safety-monitoring': [1, 2, 3],
    'river-sediment-dynamics': [1, 2],
    'inland-waterway-navigation': [1, 2],
    'ship-lock-automation': [1, 2, 3],
    'water-energy-food-nexus': [1, 2],
    'digital-twin-river-basin': [1, 2, 3, 4],
    'ai-for-water-engineering': [1, 2, 3],
}

def fuse_chapter(book, ch_num):
    """融合单个章节的Gemini和Codex输出"""
    ch = f'ch{ch_num:02d}'
    gemini_file = os.path.join(book, f'{ch}_gemini_v2.md')
    codex_file = os.path.join(book, f'{ch}_codex_v2.md')
    target_file = os.path.join(book, f'{ch}.md')

    # 读取Gemini扩写内容
    if os.path.exists(gemini_file):
        with open(gemini_file, 'r', encoding='utf-8', errors='ignore') as f:
            gemini_text = f.read().strip()

        # 替换原始章节内容
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(gemini_text)
        print(f'  [OK] {book}/{ch}: Gemini融合完成')

    # 追加Codex代码解读
    if os.path.exists(codex_file):
        with open(codex_file, 'r', encoding='utf-8', errors='ignore') as f:
            codex_text = f.read().strip()

        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            current_text = f.read()

        if '仿真代码解读' not in current_text:
            with open(target_file, 'a', encoding='utf-8') as f:
                f.write(f'\n\n---\n\n## 仿真代码解读\n\n> 本节由Codex引擎生成，提供本章核心算法的Python实现与解读。\n\n{codex_text}\n')
            print(f'  [OK] {book}/{ch}: Codex融合完成')

# 执行融合
print('=== Phase 4 部分融合开始 ===\n')

for book, chapters in gemini_done.items():
    print(f'{book}:')
    for ch_num in chapters:
        fuse_chapter(book, ch_num)

print('\n=== 融合完成 ===')
