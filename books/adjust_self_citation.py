#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调整Phase 4九本书的自引率

策略:
1. 每章只保留1篇Lei 2025系列引用(优先Lei 2025a)
2. 删除多余的Lei 2025b/c/d引用
3. 重新编号参考文献

使用方法:
    python adjust_self_citation.py
"""

import os
import re
from pathlib import Path


def adjust_references(file_path):
    """调整单个文件的参考文献"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找参考文献段落
        ref_match = re.search(r'(## 参考文献\n\n)(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if not ref_match:
            return False, "未找到参考文献段落"

        ref_header = ref_match.group(1)
        ref_section = ref_match.group(2)
        ref_start = ref_match.start()
        ref_end = ref_match.end()

        # 提取所有参考文献
        refs = re.findall(r'^\d+\.\s(.+?)$', ref_section, re.MULTILINE)

        if not refs:
            return False, "参考文献格式异常"

        # 统计Lei引用
        lei_refs = [r for r in refs if 'Lei et al. (2025' in r]
        other_refs = [r for r in refs if 'Lei et al. (2025' not in r]

        original_lei_count = len(lei_refs)

        # 只保留Lei 2025a (如果有的话)
        lei_2025a = [r for r in lei_refs if '2025a' in r]

        if lei_2025a:
            # 保留Lei 2025a
            new_refs = other_refs + [lei_2025a[0]]
        elif lei_refs:
            # 如果没有2025a,保留第一个Lei引用
            new_refs = other_refs + [lei_refs[0]]
        else:
            # 没有Lei引用,保持原样
            new_refs = other_refs

        # 重新编号
        new_ref_section = ref_header
        for i, ref in enumerate(new_refs, 1):
            new_ref_section += f"{i}. {ref}\n"

        # 替换参考文献段落
        new_content = content[:ref_start] + new_ref_section + content[ref_end:]

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        reduced_count = original_lei_count - (1 if lei_refs else 0)

        return True, f"成功调整: 减少{reduced_count}处Lei自引 ({original_lei_count} -> {1 if lei_refs else 0})"

    except Exception as e:
        return False, f"错误: {str(e)}"


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

    report = []
    report.append("# 自引率调整报告\n\n")

    total_chapters = 0
    success_count = 0
    total_reduced = 0

    for book_name in books:
        book_dir = base_dir / book_name

        if not book_dir.exists():
            continue

        report.append(f"## {book_name}\n\n")

        chapter_files = sorted(book_dir.glob("ch*.md"))
        # 排除ch00和特殊文件
        chapter_files = [f for f in chapter_files if not f.name.startswith('ch00')
                        and not 'codex' in f.name.lower()
                        and not 'gemini' in f.name.lower()]

        for chapter_file in chapter_files:
            total_chapters += 1
            success, message = adjust_references(chapter_file)

            if success:
                success_count += 1
                # 提取减少的数量
                match = re.search(r'减少(\d+)处', message)
                if match:
                    total_reduced += int(match.group(1))

            report.append(f"- {chapter_file.name}: {message}\n")

        report.append("\n")

    # 添加统计摘要
    summary = f"""
## 统计摘要

- 总章节数: {total_chapters}
- 成功调整: {success_count}
- 总共减少Lei自引: {total_reduced}处
- 成功率: {success_count/total_chapters*100:.1f}%

## 调整策略

1. 每章只保留1篇Lei 2025系列引用
2. 优先保留Lei 2025a (水系统控制论理论框架)
3. 如果没有2025a,保留第一个Lei引用
4. 删除所有其他Lei 2025b/c/d引用
5. 重新编号参考文献

## 预期效果

- 调整前自引率: 34.8% (92/264)
- 调整后自引率: 约{(92-total_reduced)/264*100:.1f}% ({92-total_reduced}/264)
- 目标自引率: 10-15%
"""

    report.insert(1, summary)

    # 保存报告
    report_file = base_dir / "自引率调整报告.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.writelines(report)

    print("".join(report))
    print(f"\n报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
