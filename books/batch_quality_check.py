#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 4 九本书批量字数统计与质量检查
"""

import os
import re
from pathlib import Path

# Phase 4 九本书目录
BOOKS = [
    "reservoir-operation-optimization",
    "flood-forecasting-control",
    "dam-safety-monitoring",
    "river-sediment-dynamics",
    "inland-waterway-navigation",
    "ship-lock-automation",
    "water-energy-food-nexus",
    "digital-twin-river-basin",
    "ai-for-water-engineering"
]

BASE_DIR = Path("D:/cowork/教材/chs-books-v2/books")

def count_chinese_chars(file_path):
    """统计文件中的中文字符数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese_chars)
    except Exception as e:
        return 0

def check_references(file_path):
    """检查是否有参考文献"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        # 检查是否有参考文献标记
        has_refs = bool(re.search(r'(参考文献|References|Lei.*202[0-9]|et al\.|doi:|DOI:)', text))
        return has_refs
    except:
        return False

def analyze_book(book_name):
    """分析单本书的所有章节"""
    book_dir = BASE_DIR / book_name
    if not book_dir.exists():
        return None

    chapters = sorted([f for f in book_dir.glob("ch*.md") if f.stem != "ch00"])

    results = {
        "book": book_name,
        "total_chapters": len(chapters),
        "chapters": []
    }

    total_chars = 0
    below_4000 = []
    no_refs = []

    for ch_file in chapters:
        char_count = count_chinese_chars(ch_file)
        has_refs = check_references(ch_file)

        total_chars += char_count

        ch_info = {
            "file": ch_file.name,
            "chars": char_count,
            "has_refs": has_refs,
            "status": "✅" if char_count >= 4000 else "⚠️"
        }

        results["chapters"].append(ch_info)

        if char_count < 4000:
            below_4000.append(ch_file.name)
        if not has_refs:
            no_refs.append(ch_file.name)

    results["total_chars"] = total_chars
    results["avg_chars"] = total_chars // len(chapters) if chapters else 0
    results["below_4000"] = below_4000
    results["no_refs"] = no_refs

    return results

def generate_report():
    """生成完整评审报告"""
    print("# Phase 4 九本书字数统计与质量检查报告\n")
    print(f"生成时间: 2026-03-08\n")
    print("---\n")

    all_results = []

    for book in BOOKS:
        result = analyze_book(book)
        if result:
            all_results.append(result)

    # 汇总统计
    print("## 一、汇总统计\n")
    print("| 书名 | 章数 | 总字数 | 平均字数/章 | <4000字章节 | 无参考文献章节 |")
    print("|------|------|--------|-------------|-------------|----------------|")

    for r in all_results:
        print(f"| {r['book']} | {r['total_chapters']} | {r['total_chars']:,} | {r['avg_chars']:,} | {len(r['below_4000'])} | {len(r['no_refs'])} |")

    print("\n---\n")

    # 详细章节统计
    print("## 二、详细章节统计\n")

    for r in all_results:
        print(f"### {r['book']}\n")
        print("| 章节 | 字数 | 状态 | 参考文献 |")
        print("|------|------|------|----------|")

        for ch in r['chapters']:
            refs_status = "✅" if ch['has_refs'] else "❌"
            print(f"| {ch['file']} | {ch['chars']:,} | {ch['status']} | {refs_status} |")

        print(f"\n**总计**: {r['total_chars']:,}字, 平均{r['avg_chars']:,}字/章\n")

        if r['below_4000']:
            print(f"⚠️ **低于4000字**: {', '.join(r['below_4000'])}\n")

        if r['no_refs']:
            print(f"❌ **缺少参考文献**: {', '.join(r['no_refs'])}\n")

        print("---\n")

    # 问题汇总
    print("## 三、问题汇总\n")

    total_below_4000 = sum(len(r['below_4000']) for r in all_results)
    total_no_refs = sum(len(r['no_refs']) for r in all_results)
    total_chapters = sum(r['total_chapters'] for r in all_results)

    print(f"- **总章节数**: {total_chapters}")
    print(f"- **低于4000字章节**: {total_below_4000} ({total_below_4000/total_chapters*100:.1f}%)")
    print(f"- **缺少参考文献章节**: {total_no_refs} ({total_no_refs/total_chapters*100:.1f}%)")

    print("\n### 优先修订清单\n")
    print("#### 1. 字数不足章节 (需扩写至4500-5500字)\n")
    for r in all_results:
        if r['below_4000']:
            for ch in r['below_4000']:
                print(f"- {r['book']}/{ch}")

    print("\n#### 2. 参考文献缺失章节 (需补充)\n")
    for r in all_results:
        if r['no_refs']:
            for ch in r['no_refs']:
                print(f"- {r['book']}/{ch}")

if __name__ == "__main__":
    generate_report()
