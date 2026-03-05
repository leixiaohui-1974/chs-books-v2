#!/usr/bin/env python3
"""
book_weaver.py

Rebuild extracted case markdown files into full, independent book drafts.

Default behavior:
1) Read source books from:
   D:\cowork\chs-knowledge-platform\books
2) Read chapter seeds (intro.md + ch*.md) and extracted case markdowns (case_*.md)
3) Expand each case with a pedagogical 6-pillar structure and chapter-level background
4) Save generated drafts into:
   D:\cowork\教材\chs-books-v2\books

By default, the script only weaves "new" books (source folders with case files that are
not already present under the target books root). It expects 14 new books unless
--allow-count-mismatch is used.

LLM modes:
- placeholder (default): deterministic long-form placeholder expansions.
- gemini: use Gemini API if configured.
- codex: use OpenAI API if configured.
- auto: try Gemini, then Codex, then placeholder.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

SOURCE_BOOKS_ROOT = Path(r"D:\cowork\chs-knowledge-platform\books")
TARGET_BOOKS_ROOT = Path(r"D:\cowork\教材\chs-books-v2\books")
EXPECTED_NEW_BOOKS = 14

READ_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "gbk", "cp936")

@dataclass
class ChapterSeed:
    file_path: Path
    number: int
    title: str
    frontmatter: Dict[str, str]
    body: str

@dataclass
class CaseSeed:
    file_path: Path
    number: int
    title: str
    frontmatter: Dict[str, str]
    body: str

@dataclass
class BookSeed:
    name: str
    dir_path: Path
    intro_frontmatter: Dict[str, str]
    intro_body: str
    chapters: List[ChapterSeed]
    cases: List[CaseSeed]
    last_modified_ts: float

@dataclass
class WeaverStats:
    selected_books: int = 0
    generated_books: int = 0
    skipped_books: int = 0
    failed_books: int = 0

def log(msg: str) -> None:
    print(msg, flush=True)

def read_text_best_effort(path: Path) -> str:
    last_error: Optional[Exception] = None
    for enc in READ_ENCODINGS:
        try:
            return path.read_text(encoding=enc)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Unable to read file with supported encodings: {path}") from last_error

def write_text_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")

def split_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}, text.strip()

    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text.strip()

    raw_frontmatter = parts[0][4:]
    body = parts[1].strip()
    fm: Dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body

def first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("#"):
            return line.strip().lstrip("#").strip()
    return ""

def markdown_title_from_path(path: Path, fallback_prefix: str) -> str:
    stem = path.stem
    cleaned = re.sub(r"[_\-]+", " ", stem).strip()
    if cleaned:
        return cleaned
    return f"{fallback_prefix} {path.stem}"

def parse_index_from_name(name: str, default: int = 9999) -> int:
    m = re.search(r"(\d+)", name)
    if not m:
        return default
    return int(m.group(1))

def strip_duplicate_title_heading(body: str, title: str) -> str:
    lines = body.splitlines()
    if not lines:
        return body.strip()
    first = lines[0].strip()
    normalized_title = re.sub(r"\s+", " ", title).strip().lower()
    normalized_first = re.sub(r"\s+", " ", first.lstrip("#").strip()).lower()
    if first.startswith("#") and normalized_first == normalized_title:
        return "\n".join(lines[1:]).strip()
    return body.strip()

def load_chapter(path: Path) -> ChapterSeed:
    raw = read_text_best_effort(path)
    fm, body = split_frontmatter(raw)
    title = fm.get("title") or first_heading(body) or markdown_title_from_path(path, "Chapter")
    title = title.strip()
    number = parse_index_from_name(path.stem)
    body = strip_duplicate_title_heading(body, title)
    return ChapterSeed(
        file_path=path,
        number=number,
        title=title,
        frontmatter=fm,
        body=body,
    )

def load_case(path: Path) -> CaseSeed:
    raw = read_text_best_effort(path)
    fm, body = split_frontmatter(raw)
    title = fm.get("title") or first_heading(body) or markdown_title_from_path(path, "Case")
    title = title.strip()
    number = parse_index_from_name(path.stem)
    body = strip_duplicate_title_heading(body, title)
    return CaseSeed(
        file_path=path,
        number=number,
        title=title,
        frontmatter=fm,
        body=body,
    )

def slug_to_readable(slug: str) -> str:
    return re.sub(r"[-_]+", " ", slug).strip().title()

def discover_book_seed(book_dir: Path) -> Optional[BookSeed]:
    if not book_dir.is_dir():
        return None

    intro_path = book_dir / "intro.md"
    chapter_paths = sorted(book_dir.glob("ch*.md"), key=lambda p: parse_index_from_name(p.name))
    case_paths = sorted(book_dir.glob("case_*.md"), key=lambda p: parse_index_from_name(p.name))

    if not intro_path.exists() or not chapter_paths or not case_paths:
        return None

    intro_raw = read_text_best_effort(intro_path)
    intro_fm, intro_body = split_frontmatter(intro_raw)
    intro_title = intro_fm.get("title") or first_heading(intro_body)
    if intro_title:
        intro_body = strip_duplicate_title_heading(intro_body, intro_title)

    chapters = [load_chapter(p) for p in chapter_paths]
    cases = [load_case(p) for p in case_paths]
    mtime = max(p.stat().st_mtime for p in [intro_path, *chapter_paths, *case_paths])

    return BookSeed(
        name=book_dir.name,
        dir_path=book_dir,
        intro_frontmatter=intro_fm,
        intro_body=intro_body,
        chapters=chapters,
        cases=cases,
        last_modified_ts=mtime,
    )

def discover_source_books(source_root: Path) -> List[BookSeed]:
    seeds: List[BookSeed] = []
    for d in sorted(source_root.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        seed = discover_book_seed(d)
        if seed is not None:
            seeds.append(seed)
    return seeds

def discover_existing_target_book_names(target_root: Path) -> set[str]:
    if not target_root.exists():
        return set()
    return {d.name for d in target_root.iterdir() if d.is_dir()}

def build_book_selection(
    source_books: Sequence[BookSeed],
    existing_target_names: set[str],
    explicit_book_names: Optional[Sequence[str]],
    expected_count: int,
    allow_count_mismatch: bool,
) -> List[BookSeed]:
    by_name = {b.name: b for b in source_books}
    if explicit_book_names:
        selected: List[BookSeed] = []
        missing: List[str] = []
        for name in explicit_book_names:
            if name in by_name:
                selected.append(by_name[name])
            else:
                missing.append(name)
        if missing:
            raise ValueError(f"Requested books not found in source root: {', '.join(missing)}")
        return selected

    new_books = [b for b in source_books if b.name not in existing_target_names]
    new_books.sort(key=lambda b: b.name.lower())

    if len(new_books) != expected_count and not allow_count_mismatch:
        names = ", ".join(b.name for b in new_books)
        raise RuntimeError(
            f"Expected {expected_count} new case-based books but found {len(new_books)}. "
            f"Use --allow-count-mismatch to continue. Detected: [{names}]"
        )
    return new_books

def find_case_numbers_in_text(text: str) -> List[int]:
    nums: set[int] = set()
    for a, b in re.findall(
        r"(?i)(?:case|cases|案例)\s*0*(\d{1,2})\s*[-~～至到]\s*0*(\d{1,2})", text
    ):
        start, end = int(a), int(b)
        if start > end:
            start, end = end, start
        nums.update(range(start, end + 1))

    for n in re.findall(r"(?i)(?:case|cases|案例)\s*0*(\d{1,2})", text):
        nums.add(int(n))

    return sorted(nums)

def assign_cases_to_chapters(chapters: Sequence[ChapterSeed], cases: Sequence[CaseSeed]) -> Dict[int, List[CaseSeed]]:
    if not chapters:
        return {}
    if not cases:
        return {i: [] for i in range(len(chapters))}

    cases_by_number: Dict[int, CaseSeed] = {c.number: c for c in cases}
    mapping: Dict[int, List[CaseSeed]] = {i: [] for i in range(len(chapters))}

    explicit_coverage = 0
    assigned_numbers: set[int] = set()
    for idx, chapter in enumerate(chapters):
        nums = [n for n in find_case_numbers_in_text(chapter.body) if n in cases_by_number]
        if not nums:
            continue
        explicit_coverage += len(nums)
        for n in nums:
            if n in assigned_numbers:
                continue
            mapping[idx].append(cases_by_number[n])
            assigned_numbers.add(n)

    if explicit_coverage < max(2, int(0.5 * len(cases))):
        mapping = {i: [] for i in range(len(chapters))}
        sorted_cases = sorted(cases, key=lambda c: (c.number, c.file_path.name.lower()))
        n_cases = len(sorted_cases)
        n_ch = len(chapters)
        base = n_cases // n_ch
        rem = n_cases % n_ch
        cursor = 0
        for i in range(n_ch):
            take = base + (1 if i < rem else 0)
            mapping[i] = sorted_cases[cursor : cursor + take]
            cursor += take
        return mapping

    unassigned = [c for c in sorted(cases, key=lambda x: x.number) if c.number not in assigned_numbers]
    if unassigned:
        mapping[len(chapters) - 1].extend(unassigned)

    for i in mapping:
        mapping[i] = sorted(mapping[i], key=lambda c: (c.number, c.file_path.name.lower()))
    return mapping

class LLMEngine:
    def __init__(self, mode: str, model: Optional[str], temperature: float) -> None:
        self.mode = mode
        self.model = model
        self.temperature = temperature
        self.resolved_mode = self._resolve_mode(mode)
        self._openai_client = None
        self._gemini_model = None

    def _resolve_mode(self, mode: str) -> str:
        if mode != "auto":
            return mode
        if os.getenv("GEMINI_API_KEY"):
            return "gemini"
        if os.getenv("OPENAI_API_KEY"):
            return "codex"
        return "placeholder"

    def _ensure_gemini(self):
        if self._gemini_model is not None:
            return self._gemini_model
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=api_key)
        model_name = self.model or "gemini-1.5-pro"
        self._gemini_model = genai.GenerativeModel(model_name)
        return self._gemini_model

    def _ensure_openai(self):
        if self._openai_client is not None:
            return self._openai_client
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def generate(self, prompt: str, placeholder_fallback: str) -> str:
        if self.resolved_mode == "placeholder":
            return placeholder_fallback

        if self.resolved_mode == "gemini":
            try:
                model = self._ensure_gemini()
                resp = model.generate_content(prompt)
                text = getattr(resp, "text", None)
                if text and text.strip():
                    return text.strip()
            except Exception as exc:
                return f"{placeholder_fallback}\n\n> [LLM fallback] Gemini generation failed: {exc}"
            return placeholder_fallback

        if self.resolved_mode == "codex":
            try:
                client = self._ensure_openai()
                model_name = self.model or "gpt-5-mini"
                resp = client.responses.create(
                    model=model_name,
                    input=prompt,
                    temperature=self.temperature,
                )
                output_text = getattr(resp, "output_text", None)
                if output_text and output_text.strip():
                    return output_text.strip()

                chunks: List[str] = []
                for item in getattr(resp, "output", []) or []:
                    for c in getattr(item, "content", []) or []:
                        if getattr(c, "type", "") == "output_text":
                            chunks.append(getattr(c, "text", ""))
                merged = "\n".join(s for s in chunks if s).strip()
                if merged:
                    return merged
            except Exception as exc:
                return f"{placeholder_fallback}\n\n> [LLM fallback] Codex generation failed: {exc}"
            return placeholder_fallback

        return placeholder_fallback

def _shorten_excerpt(text: str, max_lines: int = 12) -> str:
    lines = [ln.rstrip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines]) + "\n..."

def placeholder_chapter_background(book_name: str, chapter_title: str, case_numbers: Sequence[int]) -> str:
    case_span = "none"
    if case_numbers:
        case_span = f"{min(case_numbers):02d}-{max(case_numbers):02d}"
    readable = slug_to_readable(book_name)
    return textwrap.dedent(
        f"""\
        This chapter belongs to **{readable}** and frames a coherent learning arc for cases {case_span}.
        It reconstructs first-principles theory, links those principles to real constraints, and
        connects model-based reasoning with deployable decisions.

        Learning progression:
        1. Understand dominant mechanisms
        2. Build quantitative formulations
        3. Validate and decide under constraints
        """
    ).strip()

def placeholder_case_expansion(
    book_name: str,
    chapter_title: str,
    case_title: str,
    case_body: str,
) -> str:
    readable = slug_to_readable(book_name)
    excerpt = _shorten_excerpt(case_body, max_lines=8)
    return textwrap.dedent(
        f"""\
        ### 🌟 案例背景 (Context)
        This case in **{readable} / {chapter_title}** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        {excerpt}

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.
        """
    ).strip()

def build_chapter_markdown(
    engine: LLMEngine,
    book: BookSeed,
    chapter: ChapterSeed,
    chapter_cases: Sequence[CaseSeed],
    chapter_position: int,
) -> str:
    case_numbers = [c.number for c in chapter_cases]
    fallback_bg = placeholder_chapter_background(book.name, chapter.title, case_numbers)
    bg_prompt = textwrap.dedent(
        f"""\
        Expand chapter-level theoretical background and problem context.
        Book: {book.name}
        Chapter: {chapter.title}
        Cases: {case_numbers}
        """
    )
    chapter_background = engine.generate(bg_prompt, fallback_bg).strip()

    title = chapter.title or f"Chapter {chapter.number:02d}"
    lines: List[str] = []
    lines.append("---")
    lines.append(f'title: "{title}"')
    lines.append(f"sidebar_position: {chapter_position}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Reconstructed Theoretical Background")
    lines.append(chapter_background)
    lines.append("")
    lines.append("## Original Chapter Seed")
    lines.append(chapter.body.strip() or "(empty)")
    lines.append("")
    lines.append("## Expanded Case Set")
    lines.append("")

    for case in chapter_cases:
        fallback_exp = placeholder_case_expansion(
            book_name=book.name,
            chapter_title=title,
            case_title=case.title,
            case_body=case.body,
        )
        case_prompt = textwrap.dedent(
            f"""\
            Expand this case into a pedagogical six-pillar section.
            Book: {book.name}
            Chapter: {title}
            Case number: {case.number}
            Case title: {case.title}

            Source case markdown:
            {case.body[:7000]}
            """
        )
        expansion = engine.generate(case_prompt, fallback_exp).strip()
        lines.append(f"### Case {case.number:02d}: {case.title}")
        lines.append("")
        lines.append(expansion)
        lines.append("")

    return "\n".join(lines).strip() + "\n"

def build_outline_markdown(book: BookSeed, chapter_map: Dict[int, List[CaseSeed]]) -> str:
    lines: List[str] = []
    lines.append(f"# {book.name} - OUTLINE")
    lines.append("")
    lines.append("## Source")
    lines.append(f"- folder: `{book.dir_path}`")
    lines.append(f"- detected chapters: {len(book.chapters)}")
    lines.append(f"- detected cases: {len(book.cases)}")
    lines.append("")
    lines.append("## Chapter to Case Mapping")
    for i, ch in enumerate(book.chapters):
        cases = chapter_map.get(i, [])
        case_label = ", ".join(f"{c.number:02d}" for c in cases) if cases else "(none)"
        lines.append(f"- `ch{ch.number:02d}.md` {ch.title}: {case_label}")
    lines.append("")
    return "\n".join(lines).strip() + "\n"

def build_full_book_markdown(book: BookSeed, chapter_files: Sequence[Tuple[str, str]], engine_mode: str) -> str:
    readable = slug_to_readable(book.name)
    lines: List[str] = []
    lines.append(f"# {readable} - Independent Draft")
    lines.append("")
    lines.append("## Generation Metadata")
    lines.append(f"- generated_at_utc: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- engine_mode: {engine_mode}")
    lines.append(f"- chapter_count: {len(book.chapters)}")
    lines.append(f"- case_count: {len(book.cases)}")
    lines.append("")
    lines.append("## Intro Seed")
    lines.append(book.intro_body.strip() or "(empty)")
    lines.append("")
    lines.append("---")
    lines.append("")

    for rel_name, content in chapter_files:
        lines.append(f"## Included File: `{rel_name}`")
        lines.append("")
        lines.append(content.strip())
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).strip() + "\n"

def generate_book(
    book: BookSeed,
    target_books_root: Path,
    engine: LLMEngine,
    dry_run: bool,
    overwrite: bool,
) -> Tuple[bool, str]:
    out_dir = target_books_root / book.name
    if out_dir.exists() and not overwrite:
        return False, f"Skip existing target directory (use --overwrite to replace): {out_dir}"

    chapter_map = assign_cases_to_chapters(book.chapters, book.cases)
    outline_md = build_outline_markdown(book, chapter_map)

    chapter_outputs: List[Tuple[str, str]] = []
    for idx, chapter in enumerate(book.chapters):
        chapter_cases = chapter_map.get(idx, [])
        rel_name = f"ch{chapter.number:02d}.md"
        chapter_md = build_chapter_markdown(
            engine=engine,
            book=book,
            chapter=chapter,
            chapter_cases=chapter_cases,
            chapter_position=idx + 2,
        )
        chapter_outputs.append((rel_name, chapter_md))

    full_book_md = build_full_book_markdown(book, chapter_outputs, engine.resolved_mode)
    manifest = {
        "book_name": book.name,
        "source_dir": str(book.dir_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "engine_mode": engine.resolved_mode,
        "chapters": [
            {
                "source": str(ch.file_path),
                "target": rel_name,
                "case_numbers": [c.number for c in chapter_map.get(i, [])],
            }
            for i, (ch, (rel_name, _)) in enumerate(zip(book.chapters, chapter_outputs))
        ],
        "case_count": len(book.cases),
    }

    if dry_run:
        return True, f"[DRY RUN] Would generate: {out_dir}"

    out_dir.mkdir(parents=True, exist_ok=True)
    write_text_utf8(out_dir / "OUTLINE.md", outline_md)
    write_text_utf8(out_dir / "INTRO.md", book.intro_body.strip() + "\n")
    for rel_name, chapter_md in chapter_outputs:
        write_text_utf8(out_dir / rel_name, chapter_md)
    write_text_utf8(out_dir / "BOOK_DRAFT.md", full_book_md)
    write_text_utf8(out_dir / "weaver_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    return True, f"Generated: {out_dir}"

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weave extracted case markdowns into full textbook drafts.")
    parser.add_argument("--source-root", type=Path, default=SOURCE_BOOKS_ROOT)
    parser.add_argument("--target-root", type=Path, default=TARGET_BOOKS_ROOT)
    parser.add_argument("--expected-new-count", type=int, default=EXPECTED_NEW_BOOKS)
    parser.add_argument("--allow-count-mismatch", action="store_true")
    parser.add_argument(
        "--books",
        type=str,
        default="",
        help="Comma-separated source book folder names to process. If omitted, auto-select new books.",
    )
    parser.add_argument("--mode", choices=("auto", "placeholder", "gemini", "codex"), default="placeholder")
    parser.add_argument("--model", type=str, default="")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    return parser.parse_args(argv)

def validate_paths(source_root: Path, target_root: Path) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"Source root does not exist: {source_root}")
    if not source_root.is_dir():
        raise NotADirectoryError(f"Source root is not a directory: {source_root}")
    if not target_root.exists():
        log(f"[INFO] Target root does not exist yet. It will be created on write: {target_root}")

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    source_root = args.source_root
    target_root = args.target_root
    explicit_books = [s.strip() for s in args.books.split(",") if s.strip()]

    validate_paths(source_root, target_root)

    log(f"[INFO] Source root: {source_root}")
    log(f"[INFO] Target root: {target_root}")

    source_books = discover_source_books(source_root)
    if not source_books:
        log("[ERROR] No case-based source books discovered (requires intro.md + ch*.md + case_*.md).")
        return 2

    existing_target_names = discover_existing_target_book_names(target_root)
    selected = build_book_selection(
        source_books=source_books,
        existing_target_names=existing_target_names,
        explicit_book_names=explicit_books if explicit_books else None,
        expected_count=args.expected_new_count,
        allow_count_mismatch=args.allow_count_mismatch,
    )

    engine = LLMEngine(mode=args.mode, model=args.model or None, temperature=args.temperature)
    log(f"[INFO] Expansion mode resolved to: {engine.resolved_mode}")
    log(f"[INFO] Books selected: {len(selected)}")
    for b in selected:
        log(f"  - {b.name} (chapters={len(b.chapters)}, cases={len(b.cases)})")

    stats = WeaverStats(selected_books=len(selected))
    for book in selected:
        try:
            ok, message = generate_book(
                book=book,
                target_books_root=target_root,
                engine=engine,
                dry_run=args.dry_run,
                overwrite=args.overwrite,
            )
            if ok:
                stats.generated_books += 1
            else:
                stats.skipped_books += 1
            log(f"[BOOK] {book.name}: {message}")
        except Exception as exc:
            stats.failed_books += 1
            log(f"[ERROR] Failed book {book.name}: {exc}")
            if args.continue_on_error:
                continue
            raise

    log("")
    log("[SUMMARY]")
    log(f"- selected: {stats.selected_books}")
    log(f"- generated: {stats.generated_books}")
    log(f"- skipped: {stats.skipped_books}")
    log(f"- failed: {stats.failed_books}")

    return 0 if stats.failed_books == 0 else 1

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("\n[INTERRUPTED] Cancelled by user.")
        raise SystemExit(130)
    except Exception as exc:
        log(f"[FATAL] {exc}")
        raise SystemExit(1)
