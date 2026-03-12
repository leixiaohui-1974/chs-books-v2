#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计Phase 4已融合章节的中文字数"""
import os
import re

books = {
    'reservoir-operation-optimization': 5,
    'flood-forecasting-control': 5,
    'dam-safety-monitoring': 3,
    'river-sediment-dynamics': 4,
    'inland-waterway-navigation': 5,
    'ship-lock-automation': 5,
    'water-energy-food-nexus': 4,
    'digital-twin-river-basin': 3,
    'ai-for-water-engineering': 4,
}

total_cn = 0
total_chapters = 0

print('=== Phase 4 已融合章节字数统计 ===\n')

for book, num_chs in books.items():
    book_cn = 0
    for i in range(1, num_chs + 1):
        ch_file = os.path.join(book, f'ch{i:02d}.md')
        if os.path.exists(ch_file):
            with open(ch_file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            book_cn += cn_chars
            total_chapters += 1

    total_cn += book_cn
    print(f'{book}: {book_cn:,} 字 ({num_chs}章)')

print(f'\n总计: {total_cn:,} 字 ({total_chapters}章)')
print(f'平均: {total_cn // total_chapters:,} 字/章')
