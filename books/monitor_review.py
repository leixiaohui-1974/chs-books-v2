#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控三引擎评审任务

功能:
1. 监控后台评审任务
2. 显示实时进度
3. 自动汇总结果

使用方法:
    python monitor_review.py
"""

import os
import time
from pathlib import Path
from datetime import datetime


def check_file_status(file_path):
    """检查文件状态"""
    if not file_path.exists():
        return "pending", 0

    size = file_path.stat().st_size
    if size == 0:
        return "running", 0

    return "completed", size


def monitor_reviews(book_name, chapter_num):
    """监控单章评审进度"""
    base_dir = Path("D:/cowork/教材/chs-books-v2/books")
    book_dir = base_dir / book_name
    review_dir = book_dir / "reviews"

    codex_file = review_dir / f"ch{chapter_num}_codex_review.txt"
    gemini_file = review_dir / f"ch{chapter_num}_gemini_review.txt"
    summary_file = review_dir / f"ch{chapter_num}_summary.md"

    print(f"\n{'='*60}")
    print(f"监控评审任务: {book_name}/ch{chapter_num}")
    print(f"{'='*60}\n")

    start_time = time.time()
    last_update = {}

    while True:
        # 检查Codex评审
        codex_status, codex_size = check_file_status(codex_file)
        gemini_status, gemini_size = check_file_status(gemini_file)
        summary_status, summary_size = check_file_status(summary_file)

        # 显示状态
        elapsed = int(time.time() - start_time)
        print(f"\r[{elapsed}s] Codex: {codex_status} ({codex_size}B) | "
              f"Gemini: {gemini_status} ({gemini_size}B) | "
              f"Summary: {summary_status} ({summary_size}B)", end="", flush=True)

        # 检查是否完成
        if codex_status == "completed" and gemini_status == "completed":
            print("\n\n✓ 评审完成!")
            break

        # 检查是否有新内容
        current_state = (codex_size, gemini_size)
        if current_state != last_update.get('state'):
            last_update['state'] = current_state
            last_update['time'] = time.time()
        elif time.time() - last_update.get('time', start_time) > 300:
            # 5分钟无更新,可能卡住了
            print("\n\n⚠️ 警告: 5分钟无更新,任务可能卡住")
            break

        time.sleep(5)

    # 显示结果
    print(f"\n{'='*60}")
    print("评审结果:")
    print(f"{'='*60}\n")

    if codex_file.exists():
        print("--- Codex评审 (前30行) ---")
        with open(codex_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:30]
            print("".join(lines))

    if gemini_file.exists():
        print("\n--- Gemini评审 (前30行) ---")
        with open(gemini_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:30]
            print("".join(lines))


def main():
    import sys

    if len(sys.argv) < 3:
        print("使用方法: python monitor_review.py <book_name> <chapter_num>")
        print("示例: python monitor_review.py reservoir-operation-optimization 01")
        sys.exit(1)

    book_name = sys.argv[1]
    chapter_num = sys.argv[2]

    monitor_reviews(book_name, chapter_num)


if __name__ == "__main__":
    main()
