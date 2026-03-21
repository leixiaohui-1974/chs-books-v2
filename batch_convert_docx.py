"""批量将书稿 .md 文件用 pandoc 转换为 .docx，支持中文排版参考模板。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# 可选依赖：tqdm
# ---------------------------------------------------------------------------
try:
    from tqdm import tqdm as _tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
BASE_DIR = Path("Z:/research/chs-books-v2")
REFERENCE_DOCX = BASE_DIR / "reference.docx"
DEFAULT_OUTPUT_DIR = BASE_DIR / "docx_output"
PANDOC_EXE = Path("/c/Users/lxh/AppData/Local/Pandoc/pandoc.exe")
PANDOC_FORMAT = "markdown+tex_math_dollars+pipe_tables+footnotes+smart"


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class BookSpec:
    """描述一本书：名称、md 文件列表（已排序）。"""

    name: str
    md_files: list[Path] = field(default_factory=list)


@dataclass
class ConvertResult:
    """单次转换结果。"""

    source: Path
    dest: Path
    success: bool
    message: str = ""


# ---------------------------------------------------------------------------
# 书目发现
# ---------------------------------------------------------------------------
def _sorted_md(directory: Path, pattern: str) -> list[Path]:
    """返回目录下匹配 glob 模式的 md 文件，按文件名排序。"""
    return sorted(directory.glob(pattern))


def discover_books(base_dir: Path) -> dict[str, BookSpec]:
    """
    扫描所有书稿，返回 {书名: BookSpec} 字典。

    固定书目来自根目录子文件夹；动态书目来自 books/ 子目录。
    """
    books: dict[str, BookSpec] = {}

    # 固定书目（顺序保留）
    fixed_specs: list[tuple[str, Path, str]] = [
        ("T1-CN",           base_dir / "T1-CN",                "ch*_final.md"),
        ("T2a",             base_dir / "T2a",                  "ch*_final.md"),
        ("T2b",             base_dir / "T2b",                  "ch*_final.md"),
        ("T2-CN",           base_dir / "T2-CN",                "ch*_revised.md"),
        ("T3-Engineering",  base_dir / "T3-Engineering",        "ch*.md"),
        ("T4-Platform",     base_dir / "T4-Platform",           "ch*_draft.md"),
        ("T5-Intelligence", base_dir / "T5-Intelligence",       "ch*_draft.md"),
        ("ModernControl",   base_dir / "ModernControl" / "md", "ch*_v2.md"),
    ]

    for name, directory, pattern in fixed_specs:
        if not directory.is_dir():
            continue
        md_files = _sorted_md(directory, pattern)
        if md_files:
            books[name] = BookSpec(name=name, md_files=md_files)

    # books/ 子目录下的动态书目
    books_root = base_dir / "books"
    if books_root.is_dir():
        for sub in sorted(books_root.iterdir()):
            if not sub.is_dir():
                continue
            if sub.name.startswith("_") or sub.name.startswith("."):
                continue
            md_files = _sorted_md(sub, "ch*.md")
            if not md_files:
                continue
            books[sub.name] = BookSpec(name=sub.name, md_files=md_files)

    return books


# ---------------------------------------------------------------------------
# pandoc 命令构建
# ---------------------------------------------------------------------------
def build_pandoc_cmd(
    source: Path,
    dest: Path,
    reference_doc: Path,
    *,
    highlight_style: str = "tango",
) -> list[str]:
    """构造单文件转换的 pandoc 命令行参数列表。"""
    resource_path = str(source.parent)
    return [
        str(PANDOC_EXE),
        str(source),
        f"--reference-doc={reference_doc}",
        f"--resource-path={resource_path}",
        "--toc",
        "--number-sections",
        f"--highlight-style={highlight_style}",
        "--wrap=auto",
        f"-f {PANDOC_FORMAT}",
        "-o", str(dest),
    ]


def build_pandoc_cmd_merge(
    sources: list[Path],
    dest: Path,
    reference_doc: Path,
    *,
    highlight_style: str = "tango",
) -> list[str]:
    """构造合并多个 md 文件为单个 docx 的 pandoc 命令。"""
    resource_path = str(sources[0].parent)
    return [
        str(PANDOC_EXE),
        *[str(s) for s in sources],
        f"--reference-doc={reference_doc}",
        f"--resource-path={resource_path}",
        "--toc",
        "--number-sections",
        f"--highlight-style={highlight_style}",
        "--wrap=auto",
        f"-f {PANDOC_FORMAT}",
        "-o", str(dest),
    ]


# ---------------------------------------------------------------------------
# 单文件转换
# ---------------------------------------------------------------------------
def convert_one(
    source: Path,
    dest: Path,
    reference_doc: Path,
    *,
    dry_run: bool = False,
) -> ConvertResult:
    """调用 pandoc 将单个 md 转换为 docx。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_pandoc_cmd(source, dest, reference_doc)
    if dry_run:
        joined = " ".join(cmd)
        print(f"  [DRY-RUN] {joined}")
        return ConvertResult(source=source, dest=dest, success=True, message="dry-run")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        return ConvertResult(
            source=source,
            dest=dest,
            success=False,
            message=f"pandoc 未找到: {PANDOC_EXE}",
        )
    except subprocess.TimeoutExpired:
        return ConvertResult(source=source, dest=dest, success=False, message="超时（>120s）")
    if proc.returncode == 0:
        return ConvertResult(source=source, dest=dest, success=True)
    return ConvertResult(
        source=source, dest=dest, success=False, message=(proc.stderr or "")[:200]
    )


# ---------------------------------------------------------------------------
# 单本书合并转换
# ---------------------------------------------------------------------------
def convert_book_merge(
    spec: BookSpec,
    output_dir: Path,
    reference_doc: Path,
    *,
    dry_run: bool = False,
) -> ConvertResult:
    """将一本书的所有章节合并为单个 docx。"""
    book_out_dir = output_dir / spec.name
    book_out_dir.mkdir(parents=True, exist_ok=True)
    dest = book_out_dir / f"{spec.name}.docx"
    cmd = build_pandoc_cmd_merge(spec.md_files, dest, reference_doc)
    if dry_run:
        joined = " ".join(cmd)
        print(f"  [DRY-RUN] {joined}")
        return ConvertResult(source=spec.md_files[0], dest=dest, success=True, message="dry-run")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return ConvertResult(
            source=spec.md_files[0],
            dest=dest,
            success=False,
            message=f"pandoc 未找到: {PANDOC_EXE}",
        )
    except subprocess.TimeoutExpired:
        return ConvertResult(
            source=spec.md_files[0], dest=dest, success=False, message="超时（>300s）"
        )
    if proc.returncode == 0:
        return ConvertResult(source=spec.md_files[0], dest=dest, success=True)
    return ConvertResult(
        source=spec.md_files[0],
        dest=dest,
        success=False,
        message=(proc.stderr or "")[:200],
    )


# ---------------------------------------------------------------------------
# 进度辅助
# ---------------------------------------------------------------------------
class SimpleCounter:
    """无 tqdm 时的简单进度计数器（上下文管理器，接口兼容 tqdm）。"""

    def __init__(self, total: int, desc: str = "") -> None:
        self.total = total
        self.desc = desc
        self._n = 0

    def __enter__(self) -> "SimpleCounter":
        if self.desc:
            print(f"{self.desc}  (共 {self.total} 项)")
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def update(self, n: int = 1) -> None:
        self._n += n

    def set_description(self, desc: str) -> None:
        pass


def _make_progress(total: int, desc: str = "") -> SimpleCounter:
    if HAS_TQDM:
        return _tqdm(total=total, desc=desc, unit="file")  # type: ignore[return-value]
    return SimpleCounter(total=total, desc=desc)


# ---------------------------------------------------------------------------
# 批量转换
# ---------------------------------------------------------------------------
def run_batch(
    books: dict[str, BookSpec],
    output_dir: Path,
    reference_doc: Path,
    *,
    merge: bool = False,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    批量转换所有指定书目。

    Args:
        books: 书目字典 {书名: BookSpec}
        output_dir: 输出根目录
        reference_doc: reference.docx 路径
        merge: 是否合并模式（每本书输出单个 docx）
        dry_run: 是否演习模式（只打印命令）

    Returns:
        (成功数, 失败数)
    """
    if not dry_run and not PANDOC_EXE.exists():
        print(f"[ERROR] pandoc 未找到: {PANDOC_EXE}", file=sys.stderr)
        print("请从 https://pandoc.org/installing.html 安装 pandoc。", file=sys.stderr)
        sys.exit(1)
    if not reference_doc.exists():
        print(
            f"[WARNING] reference.docx 不存在: {reference_doc}，将使用 pandoc 默认样式继续。",
            file=sys.stderr,
        )
    ok = 0
    fail = 0
    if merge:
        total = len(books)
        with _make_progress(total, desc="合并转换") as pbar:
            for idx, (_, spec) in enumerate(books.items(), 1):
                print(f"[{idx}/{total}] 合并: {spec.name}  ({len(spec.md_files)} 章)")
                result = convert_book_merge(spec, output_dir, reference_doc, dry_run=dry_run)
                if result.success:
                    print(f"  OK -> {result.dest}")
                    ok += 1
                else:
                    print(f"  FAILED: {result.message}", file=sys.stderr)
                    fail += 1
                pbar.update(1)
    else:
        all_tasks: list[tuple[str, Path]] = [
            (spec.name, md)
            for spec in books.values()
            for md in spec.md_files
        ]
        total = len(all_tasks)
        with _make_progress(total, desc="逐文件转换") as pbar:
            for idx, (book_name, md_file) in enumerate(all_tasks, 1):
                dest = output_dir / book_name / md_file.with_suffix(".docx").name
                print(f"[{idx}/{total}] 转换: {book_name}/{md_file.name}")
                result = convert_one(md_file, dest, reference_doc, dry_run=dry_run)
                if result.success:
                    print(f"  OK -> {result.dest}")
                    ok += 1
                else:
                    print(f"  FAILED: {result.message}", file=sys.stderr)
                    fail += 1
                pbar.update(1)
    return ok, fail


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="批量将书稿 .md 文件用 pandoc 转换为 .docx（中文排版参考模板）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python batch_convert_docx.py --list\n"
            "  python batch_convert_docx.py --book T1-CN\n"
            "  python batch_convert_docx.py --book T1-CN --book T2a\n"
            "  python batch_convert_docx.py --all\n"
            "  python batch_convert_docx.py --all --merge\n"
            "  python batch_convert_docx.py --book ModernControl --dry-run\n"
            "  python batch_convert_docx.py --all --output-dir /tmp/docx_out"
        ),
    )
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--book",
        metavar="NAME",
        action="append",
        help="指定要转换的书名（可重复使用以指定多本）",
    )
    target_group.add_argument("--all", action="store_true", help="转换所有已发现的书目")
    target_group.add_argument("--list", action="store_true", help="列出所有可用书目，不转换")
    parser.add_argument(
        "--output-dir",
        metavar="PATH",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"输出根目录（默认：{DEFAULT_OUTPUT_DIR}）",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="合并模式：每本书的所有章节合并为单个 docx",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印 pandoc 命令，不实际执行",
    )
    parser.add_argument(
        "--base-dir",
        metavar="PATH",
        default=str(BASE_DIR),
        help=f"书稿根目录（默认：{BASE_DIR}）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """脚本主入口。"""
    args = parse_args(argv)
    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    reference_doc = base_dir / "reference.docx"
    all_books = discover_books(base_dir)
    if args.list:
        print(f"发现 {len(all_books)} 本书稿：\n")
        for name, spec in all_books.items():
            print(f"  {name:<45} {len(spec.md_files):>3} 章  {spec.md_files[0].parent}")
        return
    if args.all:
        target_books = all_books
    elif args.book:
        target_books: dict[str, BookSpec] = {}
        for name in args.book:
            if name not in all_books:
                print(f"[WARNING] 未找到书目: {name}（用 --list 查看可用书目）", file=sys.stderr)
            else:
                target_books[name] = all_books[name]
        if not target_books:
            print("[ERROR] 没有可转换的书目。", file=sys.stderr)
            sys.exit(1)
    else:
        print("请指定 --book NAME、--all 或 --list。", file=sys.stderr)
        sys.exit(1)
    mode_merge = "是" if args.merge else "否"
    mode_dry = "是" if args.dry_run else "否"
    print(f"目标书目: {len(target_books)} 本")
    print(f"输出目录: {output_dir}")
    print(f"参考模板: {reference_doc}")
    print(f"合并模式: {mode_merge}")
    print(f"演习模式: {mode_dry}")
    print("-" * 60)
    ok, fail = run_batch(
        target_books,
        output_dir,
        reference_doc,
        merge=args.merge,
        dry_run=args.dry_run,
    )
    print("-" * 60)
    print(f"转换完成: 成功 {ok} 个，失败 {fail} 个")
    print(f"输出目录: {output_dir}")
    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
