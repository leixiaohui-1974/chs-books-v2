#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 4 最终字数统计"""
import os
import re

books_chapters = {
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

print('=== Phase 4 最终字数统计 ===\n')

total_cn = 0
total_chapters = 0
below_4k = []

for book, total_chs in books_chapters.items():
    book_cn = 0
    for ch_num in range(1, total_chs + 1):
        ch_file = os.path.join(book, f'ch{ch_num:02d}.md')
        if os.path.exists(ch_file):
            with open(ch_file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            book_cn += cn_chars
            total_chapters += 1
            if cn_chars < 4000:
                below_4k.append(f'{book}/ch{ch_num:02d}: {cn_chars}')

    total_cn += book_cn
    print(f'{book}: {book_cn:,} 字 ({total_chs}章, 平均{book_cn//total_chs:,}字/章)')

print(f'\n总计: {total_cn:,} 字 ({total_chapters}章)')
print(f'平均: {total_cn // total_chapters:,} 字/章')

if below_4k:
    print(f'\n低于4000字的章节 ({len(below_4k)}章):')
    for item in below_4k:
        print(f'  {item}')
else:
    print('\n全部章节均≥4000字')
