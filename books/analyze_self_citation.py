#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计Phase 4九本书的自引率

使用方法:
    python analyze_self_citation.py
"""

import os
import re
from pathlib import Path
from collections import defaultdict


def count_references(file_path):
    """统计单个文件的参考文献数量"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找参考文献段落
        ref_match = re.search(r'## 参考文献\n\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if not ref_match:
            return 0, 0

        ref_section = ref_match.group(1)

        # 统计总参考文献数量
        total_refs = len(re.findall(r'^\d+\.\s', ref_section, re.MULTILINE))

        # 统计Lei自引数量
        lei_refs = len(re.findall(r'Lei et al\. \(2025', ref_section))

        return total_refs, lei_refs

    except Exception as e:
        return 0, 0


def main():
    base_dir = Path(__file__).parent

    books = [
        "reservoir-operation-optimization",
        "flood-forecasting-control",
        "dam-safety-monitoring",
        "river-sediment-dynamics",
        "inland-waterway-navigation",
        "ship-lock-automation",
        "water-energy-food-nexus",
        "digital-twin-river-basin",
        "ai-for-water-engineering",
    ]

    print("# Phase 4 自引率统计报告\n")
    print("| 书名 | 章节 | 总参考文献 | Lei自引 | 自引率 | 评级 |")
    print("|------|------|-----------|---------|--------|------|")

    grand_total_refs = 0
    grand_total_lei = 0
    book_stats = []

    for book_name in books:
        book_dir = base_dir / book_name

        if not book_dir.exists():
            continue

        chapter_files = sorted(book_dir.glob("ch*.md"))
        # 排除ch00和特殊文件
        chapter_files = [f for f in chapter_files if not f.name.startswith('ch00')
                        and not 'codex' in f.name.lower()
                        and not 'gemini' in f.name.lower()]

        book_total_refs = 0
        book_total_lei = 0

        for chapter_file in chapter_files:
            total_refs, lei_refs = count_references(chapter_file)
            book_total_refs += total_refs
            book_total_lei += lei_refs

        if book_total_refs > 0:
            self_cite_rate = book_total_lei / book_total_refs * 100

            # 评级
            if self_cite_rate <= 15:
                grade = "[OK]"
            elif self_cite_rate <= 20:
                grade = "[HIGH]"
            else:
                grade = "[TOO HIGH]"

            print(f"| {book_name} | {len(chapter_files)} | {book_total_refs} | {book_total_lei} | {self_cite_rate:.1f}% | {grade} |")

            book_stats.append({
                'name': book_name,
                'chapters': len(chapter_files),
                'total_refs': book_total_refs,
                'lei_refs': book_total_lei,
                'rate': self_cite_rate
            })

            grand_total_refs += book_total_refs
            grand_total_lei += book_total_lei

    # 总计
    if grand_total_refs > 0:
        grand_rate = grand_total_lei / grand_total_refs * 100
        print(f"| **总计** | **{sum(s['chapters'] for s in book_stats)}** | **{grand_total_refs}** | **{grand_total_lei}** | **{grand_rate:.1f}%** | - |")

    print("\n## 详细分析\n")
    print(f"- 总章节数: {sum(s['chapters'] for s in book_stats)}")
    print(f"- 总参考文献: {grand_total_refs}")
    print(f"- Lei自引总数: {grand_total_lei}")
    print(f"- 平均自引率: {grand_rate:.1f}%")
    print(f"- 目标自引率: 10-15%")

    if grand_rate > 15:
        print(f"\n[WARNING] Need adjustment: Current rate({grand_rate:.1f}%) exceeds target(10-15%)")
        print(f"   Suggest reducing {grand_total_lei - int(grand_total_refs * 0.15)} Lei citations")
    else:
        print(f"\n[OK] Meets standard: Current rate({grand_rate:.1f}%) within target range")


if __name__ == "__main__":
    main()
