import re
from pathlib import Path
from datetime import datetime

BOOKS_DIR = Path("Z:/research/chs-books-v2/books")
REPORT_FILE = BOOKS_DIR / "image_audit_report.txt"
IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
EXCLUDED = {"readme.md", "ch00.md", "index.md", "preface.md", "toc.md"}
CH_PAT = re.compile(r"^ch\d+\.md$", re.IGNORECASE)
CH_VARIANT = re.compile(r"^ch\d+(_[a-z0-9]+)+\.md$", re.IGNORECASE)

def is_chapter(p):
    n = p.name.lower()
    return n not in EXCLUDED and not CH_VARIANT.match(n) and bool(CH_PAT.match(n))

def book_dirs():
    return sorted(d for d in BOOKS_DIR.iterdir() if d.is_dir() and ((d/"assets").exists() or (d/"figures").exists()))

def img_dirs(bk):
    return [bk/n for n in ("assets","figures") if (bk/n).exists()]

def scan_refs(md):
    refs = []
    try:
        for i, ln in enumerate(md.read_text(encoding="utf-8",errors="replace").splitlines(), 1):
            for m in IMG_PATTERN.finditer(ln):
                path = m.group(2).strip()
                if not path.startswith(("http://","https://")):
                    refs.append((m.group(1), path, i))
    except Exception as e:
        refs.append(("__ERR__", str(e), 0))
    return refs

def size_warn(p):
    try:
        s = p.stat().st_size
        if s < 1024: return f"< 1 KB ({s} bytes), 可能损坏"
        if s > 5*1024*1024: return f"> 5 MB ({s/1024/1024:.1f} MB), 建议压缩"
    except: return "无法读取大小"
    return None

def audit(bk):
    r = dict(book=bk.name, broken=[], orphan=[], fmt=[], empty_alt=[], size=[], no_img=[])
    pngs = {p.resolve() for d in img_dirs(bk) for p in list(d.rglob("*.png"))+list(d.rglob("*.PNG"))}
    for p in pngs:
        w = size_warn(p)
        if w: r["size"].append((p,w))
    ref_set = set()
    for md in sorted(bk.glob("*.md")):
        refs = scan_refs(md)
        has_img = False
        for alt, raw, ln in refs:
            if raw == "__ERR__": continue
            has_img = True
            if not alt.strip(): r["empty_alt"].append((md.name, ln, raw))
            issues = []
            if " " in raw: issues.append("路径含空格")
            if raw != raw.strip(): issues.append("路径首尾有空白")
            if "\\" in raw: issues.append("含反斜杠")
            if issues: r["fmt"].append((md.name, ln, raw, "; ".join(issues)))
            try:
                abs_p = (md.parent / raw).resolve()
                if abs_p.exists(): ref_set.add(abs_p)
                else: r["broken"].append((md.name, ln, raw, "文件不存在"))
            except Exception as e:
                r["broken"].append((md.name, ln, raw, f"解析错误: {e}"))
        if is_chapter(md) and not has_img:
            r["no_img"].append(md.name)
    r["orphan"] = [p for p in pngs if p not in ref_set]
    return r

def report(results):
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines += ["="*80, "图片审计报告", f"生成时间：{ts}", f"扫描目录：{BOOKS_DIR}", "="*80, ""]
    tb = sum(len(r["broken"]) for r in results)
    to = sum(len(r["orphan"]) for r in results)
    ta = sum(len(r["empty_alt"]) for r in results)
    tf = sum(len(r["fmt"]) for r in results)
    ts2 = sum(len(r["size"]) for r in results)
    tn = sum(len(r["no_img"]) for r in results)
    lines += ["【全局汇总】",
        f"  扫描书籍数: {len(results)}",
        f"  断链图片: {tb} 处",
        f"  孤儿图片: {to} 个",
        f"  空 alt 文本: {ta} 处",
        f"  路径格式问题: {tf} 处",
        f"  文件大小异常: {ts2} 个",
        f"  无图片章节: {tn} 个", ""]
    for r in results:
        lines += ["-"*80, f"书籍: {r['book']}"]
        ok = not any([r["broken"],r["orphan"],r["fmt"],r["empty_alt"],r["size"],r["no_img"]])
        if ok:
            lines += ["  [OK] 无问题", ""]; continue
        if r["broken"]:
            lines.append(f"  [断链图片] {len(r['broken'])} 处")
            for mn,ln,p,reason in sorted(r["broken"]): lines += [f"    {mn}:{ln}  ->  {p}", f"      原因: {reason}"]
        if r["orphan"]:
            lines.append(f"  [孤儿图片] {len(r['orphan'])} 个")
            for p in sorted(r["orphan"]):
                try: lines.append(f"    {p.relative_to(BOOKS_DIR)}  ({p.stat().st_size/1024:.1f} KB)")
                except: lines.append(f"    {p}")
        if r["fmt"]:
            lines.append(f"  [路径格式] {len(r['fmt'])} 处")
            for mn,ln,p,issue in sorted(r["fmt"]): lines += [f"    {mn}:{ln}  ->  {p}", f"      问题: {issue}"]
        if r["empty_alt"]:
            lines.append(f"  [空 alt 文本] {len(r['empty_alt'])} 处")
            for mn,ln,p in sorted(r["empty_alt"]): lines.append(f"    {mn}:{ln}  ->  {p}")
        if r["size"]:
            lines.append(f"  [文件大小异常] {len(r['size'])} 个")
            for p,w in sorted(r["size"]):
                try: lines.append(f"    {p.relative_to(BOOKS_DIR)}  ->  {w}")
                except: lines.append(f"    {p}  ->  {w}")
        if r["no_img"]:
            lines.append(f"  [无图片章节] {len(r['no_img'])} 个")
            for ch in sorted(r["no_img"]): lines.append(f"    {ch}")
        lines.append("")
    lines += ["="*80, "报告结束"]
    return chr(10).join(lines)

def main():
    print(f"扫描: {BOOKS_DIR}")
    bks = book_dirs()
    print(f"发现书籍: {len(bks)} 个")
    results = []
    for i, bk in enumerate(bks, 1):
        print(f"  [{i}/{len(bks)}] {bk.name}")
        results.append(audit(bk))
    txt = report(results)
    REPORT_FILE.write_text(txt, encoding="utf-8")
    print(f"报告已保存: {REPORT_FILE}")
    print(f"断链: {sum(len(r[chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(110)]) for r in results)}, 孤儿: {sum(len(r[chr(111)+chr(114)+chr(112)+chr(104)+chr(97)+chr(110)]) for r in results)}")

main()