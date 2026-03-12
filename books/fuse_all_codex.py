#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 4 全部Codex融合脚本"""
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

print('=== Phase 4 Codex全量融合 ===\n')

for book, total_chs in books_chapters.items():
    print(f'{book}:')
    for ch_num in range(1, total_chs + 1):
        ch = f'ch{ch_num:02d}'
        codex_file = os.path.join(book, f'{ch}_codex_v2.md')
        target_file = os.path.join(book, f'{ch}.md')

        if os.path.exists(codex_file):
            with open(codex_file, 'r', encoding='utf-8', errors='ignore') as f:
                codex_text = f.read().strip()

            with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                current_text = f.read()

            if '仿真代码解读' not in current_text:
                with open(target_file, 'a', encoding='utf-8') as f:
                    f.write(f'\n\n---\n\n## 仿真代码解读\n\n> 本节由Codex引擎生成，提供本章核心算法的Python实现与解读。\n\n{codex_text}\n')
                print(f'  [OK] {ch}')

print('\n=== Codex融合完成 ===')
