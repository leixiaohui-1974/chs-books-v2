#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import shutil
from datetime import datetime
from glob import glob


FILE_PATTERN = re.compile(r"^ch(\d{2})_final\.md$")
SEPARATOR_RE = re.compile(r"^\|\s*[:\-| ]+\|?\s*$")
EXISTING_CAPTION_RE = re.compile(r"表\s*\d+\s*-\s*\d+")


def starts_with_pipe(line: str) -> bool:
    return line.startswith("|")


def is_separator_line(line: str) -> bool:
    return bool(SEPARATOR_RE.match(line.strip()))


def is_table_block(block_lines) -> bool:
    return any(starts_with_pipe(l) and not is_separator_line(l) for l in block_lines)


def has_existing_caption(lines, table_start_idx: int) -> bool:
    k = table_start_idx - 1
    while k >= 0 and lines[k].strip() == "":
        k -= 1
    if k < 0:
        return False
    return bool(EXISTING_CAPTION_RE.search(lines[k]))


def make_backup(file_path: str) -> str:
    bak_path = file_path + ".bak"
    if os.path.exists(bak_path):
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        bak_path = f"{file_path}.bak.{ts}"
    shutil.copy2(file_path, bak_path)
    return bak_path


def process_file(file_path: str, chapter_num: int):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original = "".join(lines)
    seq = 0
    added = 0

    i = 0
    while i < len(lines):
        if starts_with_pipe(lines[i]):
            j = i
            while j < len(lines) and starts_with_pipe(lines[j]):
                j += 1

            block = lines[i:j]
            if is_table_block(block):
                seq += 1
                if not has_existing_caption(lines, i):
                    caption = f"\n**表{chapter_num}-{seq}**\n\n"
                    lines.insert(i, caption)
                    added += 1
                    i = j + 1
                    continue
            i = j
        else:
            i += 1

    updated = "".join(lines)
    changed = updated != original

    if changed:
        make_backup(file_path)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated)

    return {
        "chapter": chapter_num,
        "file": file_path,
        "added": added,
        "changed": changed,
        "tables_seen": seq,
    }


def main():
    parser = argparse.ArgumentParser(description="为教材章节 Markdown 表格自动补充表号")
    parser.add_argument("directory", help="包含 ch01_final.md ... ch15_final.md 的目录路径")
    args = parser.parse_args()

    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        raise SystemExit(f"目录不存在: {directory}")

    files = []
    for path in glob(os.path.join(directory, "ch*_final.md")):
        name = os.path.basename(path)
        m = FILE_PATTERN.match(name)
        if not m:
            continue
        chap = int(m.group(1))
        if 1 <= chap <= 15:
            files.append((chap, path))

    files.sort(key=lambda x: x[0])

    if not files:
        raise SystemExit("未找到匹配文件（ch01_final.md ~ ch15_final.md）")

    stats = {}
    for chap, path in files:
        result = process_file(path, chap)
        stats[chap] = result["added"]

    print("表号添加统计：")
    total_added = 0
    for chap in range(1, 16):
        added = stats.get(chap, 0)
        total_added += added
        print(f"第{chap}章: 新增 {added} 个表号")
    print(f"总计新增: {total_added} 个表号")


if __name__ == "__main__":
    main()
