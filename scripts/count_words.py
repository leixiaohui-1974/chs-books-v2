"""统计所有书稿的逐章字数"""
import os, re, glob

def count_words(filepath):
    with open(filepath, encoding='utf-8') as f:
        text = f.read()
    chs = len(re.findall(r'[\u4e00-\u9fff]', text))
    eng = len(re.findall(r'[a-zA-Z]+', text))
    return chs, eng, chs + int(eng * 0.5)

base = r'D:\cowork\教材\chs-books-v2'

# 17本新书
print("=" * 70)
print("一、17本新书 (books/)")
print("=" * 70)
books_dir = os.path.join(base, 'books')
grand_total = 0
book_summary = []
for book in sorted(os.listdir(books_dir)):
    book_path = os.path.join(books_dir, book)
    if not os.path.isdir(book_path):
        continue
    chapters = sorted(glob.glob(os.path.join(book_path, 'ch*.md')))
    if not chapters:
        continue
    print(f"\n--- {book} ({len(chapters)}章) ---")
    book_total = 0
    for ch in chapters:
        chs, eng, total = count_words(ch)
        print(f"  {os.path.basename(ch):20s} {total:6d} 字 (中{chs} 英{eng})")
        book_total += total
    print(f"  {'合计':20s} {book_total:6d} 字")
    book_summary.append((book, len(chapters), book_total))
    grand_total += book_total

print(f"\n{'='*70}")
print(f"17本书总计: {grand_total:,} 字")

# 5本代表作 + ModernControl
print(f"\n{'='*70}")
print("二、代表作 + ModernControl")
print("=" * 70)
for dirname in ['T1-CN', 'T2-CN', 'T2a', 'T2b', 'T3-Engineering', 'ModernControl']:
    dirpath = os.path.join(base, dirname)
    if not os.path.isdir(dirpath):
        print(f"\n--- {dirname}: 目录不存在 ---")
        continue
    chapters = sorted(glob.glob(os.path.join(dirpath, 'ch*.md')))
    if not chapters:
        # try _final.md
        chapters = sorted(glob.glob(os.path.join(dirpath, 'ch*_final.md')))
    if not chapters:
        # try any .md
        chapters = sorted(glob.glob(os.path.join(dirpath, '*.md')))
    print(f"\n--- {dirname} ({len(chapters)}个md文件) ---")
    dir_total = 0
    for ch in chapters[:30]:  # cap at 30
        chs, eng, total = count_words(ch)
        print(f"  {os.path.basename(ch):35s} {total:6d} 字")
        dir_total += total
    print(f"  {'合计':35s} {dir_total:6d} 字")

# 汇总表
print(f"\n{'='*70}")
print("三、17本书篇幅排名")
print("=" * 70)
print(f"{'书名':40s} {'章数':>4s} {'字数':>8s} {'均章':>6s}")
for name, nch, total in sorted(book_summary, key=lambda x: -x[2]):
    avg = total // nch if nch else 0
    print(f"  {name:38s} {nch:4d} {total:8,d} {avg:6,d}")
