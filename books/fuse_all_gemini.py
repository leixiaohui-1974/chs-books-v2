#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 4 全部Gemini融合脚本"""
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

print('=== Phase 4 Gemini全量融合 ===\n')

for book, total_chs in books_chapters.items():
    print(f'{book}:')
    for ch_num in range(1, total_chs + 1):
        ch = f'ch{ch_num:02d}'
        gemini_file = os.path.join(book, f'{ch}_gemini_v2.md')
        target_file = os.path.join(book, f'{ch}.md')

        if os.path.exists(gemini_file):
            with open(gemini_file, 'r', encoding='utf-8', errors='ignore') as f:
                gemini_text = f.read().strip()

            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(gemini_text)
            print(f'  [OK] {ch}')

print('\n=== Gemini融合完成 ===')
