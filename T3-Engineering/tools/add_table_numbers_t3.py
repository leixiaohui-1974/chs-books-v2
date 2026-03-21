#!/usr/bin/env python3
import re, os, shutil, sys
from pathlib import Path
from glob import glob

directory = sys.argv[1] if len(sys.argv) > 1 else "."
SEP = re.compile(r"^\|\s*[:\-| ]+\|?\s*$")
EX = re.compile(r"\*\*\u8868\d+-\d+\*\*")

total = 0
for p in sorted(glob(os.path.join(directory, "ch*.md"))):
    name = os.path.basename(p)
    m = re.match(r"ch(\d{1,2})\.md", name)
    if not m:
        continue
    chap = int(m.group(1))

    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()

    seq = added = 0
    i = 0
    while i < len(lines):
        if lines[i].startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            block = lines[i:j]
            has_data = any(l.startswith("|") and not SEP.match(l.strip()) for l in block)
            if has_data:
                seq += 1
                k = i - 1
                while k >= 0 and lines[k].strip() == "":
                    k -= 1
                if k < 0 or not EX.search(lines[k]):
                    cap = f"\n**\u8868{chap}-{seq}**\n\n"
                    lines.insert(i, cap)
                    added += 1
                    i = j + 1
                    continue
            i = j
        else:
            i += 1

    if added:
        shutil.copy2(p, p + ".bak")
        with open(p, "w", encoding="utf-8") as f:
            f.write("".join(lines))
    total += added
    with open(os.path.join(directory, "tools", "table_log.txt"), "a", encoding="utf-8") as log:
        log.write(f"ch{chap:02d}: +{added}\n")

with open(os.path.join(directory, "tools", "table_log.txt"), "a", encoding="utf-8") as log:
    log.write(f"Total: +{total}\n")
