#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三引擎评审进度追踪工具

功能:
1. 统计各书的评审进度
2. 生成进度报告
3. 识别待评审章节

使用方法:
    python review_progress.py
"""

import os
from pathlib import Path
from datetime import datetime


def check_review_status(book_dir, chapter_num):
    """检查单个章节的评审状态"""
    review_dir = book_dir / "reviews"

    codex_file = review_dir / f"ch{chapter_num}_codex_review.txt"
    gemini_file = review_dir / f"ch{chapter_num}_gemini_review.txt"
    summary_file = review_dir / f"ch{chapter_num}_summary.md"

    status = {
        'codex': codex_file.exists(),
        'gemini': gemini_file.exists(),
        'summary': summary_file.exists()
    }

    if all(status.values()):
        return 'completed'
    elif any(status.values()):
        return 'partial'
    else:
        return 'pending'


def generate_progress_report():
    """生成进度报告"""
    base_dir = Path("D:/cowork/教材/chs-books-v2/books")

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
    report.append("# 三引擎评审进度报告\n")
    report.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    total_chapters = 0
    completed_chapters = 0
    partial_chapters = 0
    pending_chapters = 0

    report.append("| 书名 | 总章节 | 已完成 | 进行中 | 待评审 | 进度 |\n")
    report.append("|------|--------|--------|--------|--------|------|\n")

    for book_name in books:
        book_dir = base_dir / book_name

        if not book_dir.exists():
            continue

        # 获取所有章节
        chapters = sorted(book_dir.glob("ch*.md"))
        chapters = [f for f in chapters if not f.name.startswith('ch00')
                   and 'codex' not in f.name.lower()
                   and 'gemini' not in f.name.lower()]

        book_total = len(chapters)
        book_completed = 0
        book_partial = 0
        book_pending = 0

        for chapter_file in chapters:
            chapter_num = chapter_file.stem.replace('ch', '')
            status = check_review_status(book_dir, chapter_num)

            if status == 'completed':
                book_completed += 1
            elif status == 'partial':
                book_partial += 1
            else:
                book_pending += 1

        total_chapters += book_total
        completed_chapters += book_completed
        partial_chapters += book_partial
        pending_chapters += book_pending

        progress = f"{book_completed/book_total*100:.1f}%" if book_total > 0 else "0%"

        report.append(f"| {book_name} | {book_total} | {book_completed} | {book_partial} | {book_pending} | {progress} |\n")

    # 总计
    overall_progress = f"{completed_chapters/total_chapters*100:.1f}%" if total_chapters > 0 else "0%"
    report.append(f"| **总计** | **{total_chapters}** | **{completed_chapters}** | **{partial_chapters}** | **{pending_chapters}** | **{overall_progress}** |\n")

    # 统计摘要
    report.append("\n## 统计摘要\n\n")
    report.append(f"- 总章节数: {total_chapters}\n")
    report.append(f"- 已完成评审: {completed_chapters} ({completed_chapters/total_chapters*100:.1f}%)\n")
    report.append(f"- 评审进行中: {partial_chapters} ({partial_chapters/total_chapters*100:.1f}%)\n")
    report.append(f"- 待评审: {pending_chapters} ({pending_chapters/total_chapters*100:.1f}%)\n")

    # 预计剩余时间
    if pending_chapters > 0:
        estimated_hours = pending_chapters * 0.75  # 每章约45分钟
        report.append(f"\n## 预计剩余工作量\n\n")
        report.append(f"- 待评审章节: {pending_chapters}章\n")
        report.append(f"- 预计时间: {estimated_hours:.1f}小时 (约{estimated_hours/8:.1f}个工作日)\n")

    # 下一步建议
    report.append("\n## 下一步建议\n\n")

    if pending_chapters > 0:
        report.append("### 待评审章节\n\n")

        for book_name in books:
            book_dir = base_dir / book_name

            if not book_dir.exists():
                continue

            chapters = sorted(book_dir.glob("ch*.md"))
            chapters = [f for f in chapters if not f.name.startswith('ch00')
                       and 'codex' not in f.name.lower()
                       and 'gemini' not in f.name.lower()]

            pending_list = []

            for chapter_file in chapters:
                chapter_num = chapter_file.stem.replace('ch', '')
                status = check_review_status(book_dir, chapter_num)

                if status == 'pending':
                    pending_list.append(chapter_num)

            if pending_list:
                report.append(f"**{book_name}**: ch{', ch'.join(pending_list)}\n\n")

        report.append("**执行命令**:\n")
        report.append("```bash\n")
        report.append("# 批量评审单本书\n")
        report.append("bash batch_three_engine_review.sh reservoir-operation-optimization\n")
        report.append("\n# 或单章评审\n")
        report.append("bash three_engine_review.sh reservoir-operation-optimization 02\n")
        report.append("```\n")

    else:
        report.append("✓ 所有章节评审已完成!\n\n")
        report.append("下一步: 分析评审意见并生成修改方案\n")

    return "".join(report)


def main():
    report = generate_progress_report()

    # 保存报告
    output_file = Path("D:/cowork/教材/chs-books-v2/books/评审进度报告.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print(f"\n报告已保存到: {output_file}")


if __name__ == "__main__":
    main()
