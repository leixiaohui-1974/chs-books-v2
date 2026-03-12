#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""融合10个扩写章节"""
import os
import shutil

expanded_files = [
    'reservoir-operation-optimization/ch04_expanded.md',
    'flood-forecasting-control/ch04_expanded.md',
    'flood-forecasting-control/ch06_expanded.md',
    'river-sediment-dynamics/ch03_expanded.md',
    'inland-waterway-navigation/ch03_expanded.md',
    'inland-waterway-navigation/ch04_expanded.md',
    'inland-waterway-navigation/ch06_expanded.md',
    'ship-lock-automation/ch04_expanded.md',
    'water-energy-food-nexus/ch03_expanded.md',
    'ai-for-water-engineering/ch03_expanded.md',
]

print('=== 融合10个扩写章节 ===\n')

for exp_file in expanded_files:
    target_file = exp_file.replace('_expanded.md', '.md')

    if os.path.exists(exp_file):
        # 读取扩写内容（不含Codex部分）
        with open(exp_file, 'r', encoding='utf-8', errors='ignore') as f:
            expanded_text = f.read()

        # 读取原文件的Codex部分
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            original_text = f.read()

        # 提取Codex部分
        if '## 仿真代码解读' in original_text:
            codex_part = original_text.split('## 仿真代码解读', 1)[1]
            codex_section = '## 仿真代码解读' + codex_part
        else:
            codex_section = ''

        # 写入：扩写内容 + Codex部分
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(expanded_text)
            if codex_section:
                f.write('\n\n---\n\n' + codex_section)

        print(f'[OK] {target_file}')

print('\n=== 融合完成 ===')
