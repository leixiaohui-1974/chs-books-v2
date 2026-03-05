#!/usr/bin/env python3
"""
Orchestrate Codex CLI rewrites for mock case blocks in markdown chapters.

Default behavior (safe pilot mode):
- Scan books/open-channel-hydraulics
- Process only one markdown file (ch01.md if present)
- Use concurrency = 1
- For each detected case block (from "案例背景/Context" onward), call:
    codex exec --full-auto "<prompt>"
  and replace the block with the model output.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import logging
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOK_DIR = REPO_ROOT / "books" / "open-channel-hydraulics"
DEFAULT_TARGET_FILE = "ch01.md"

BACKGROUND_START_RE = re.compile(
    r"(?im)^[ \t]*###[ \t]+.*(?:案例背景|Context).*?$"
)
CASE_HEADING_RE = re.compile(r"(?im)^[ \t]*###[ \t]+Case\b.*?$")
REFLECTION_RE = re.compile(r"(?im)reflection[ \t_-]*task")

MOCK_SIGNAL_PATTERNS = [
    re.compile(r"(?im)^[ \t]*###[ \t]+.*(?:问题描述|Problem).*?$"),
    re.compile(r"(?im)^[ \t]*###[ \t]+.*(?:解题思路|Solution).*?$"),
    re.compile(r"(?im)^[ \t]*###[ \t]+.*(?:代码执行|Code).*?$"),
    re.compile(r"(?im)^[ \t]*###[ \t]+.*(?:结果|Result).*?$"),
]

MARKDOWN_FENCE_RE = re.compile(
    r"```(?:markdown|md)?\s*(.*?)```", re.IGNORECASE | re.DOTALL
)


@dataclass
class BlockSpan:
    start: int
    end: int
    case_title: str
    has_reflection: bool


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def list_target_files(
    book_dir: Path, max_files: int, prefer_file: str = DEFAULT_TARGET_FILE
) -> List[Path]:
    files = sorted(book_dir.glob("*.md"))
    if not files:
        return []

    preferred = [p for p in files if p.name == prefer_file]
    others = [p for p in files if p.name != prefer_file]
    ordered = preferred + others
    return ordered[: max(1, max_files)]


def find_previous_case_title(text: str, idx: int) -> str:
    title = "Unknown Case"
    for match in CASE_HEADING_RE.finditer(text):
        if match.start() >= idx:
            break
        title = match.group(0).strip()
    return title


def _looks_like_mock_case_block(segment: str) -> bool:
    signals = sum(1 for p in MOCK_SIGNAL_PATTERNS if p.search(segment))
    return signals >= 2


def extract_case_blocks(text: str) -> List[BlockSpan]:
    starts = list(BACKGROUND_START_RE.finditer(text))
    if not starts:
        return []

    spans: List[BlockSpan] = []
    for i, start_match in enumerate(starts):
        start = start_match.start()
        next_start = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        segment = text[start:next_start]
        has_reflection = bool(REFLECTION_RE.search(segment))

        if has_reflection or _looks_like_mock_case_block(segment):
            spans.append(
                BlockSpan(
                    start=start,
                    end=next_start,
                    case_title=find_previous_case_title(text, start),
                    has_reflection=has_reflection,
                )
            )

    return spans


def count_words_mixed(text: str) -> int:
    english_words = len(re.findall(r"\b[\w-]+\b", text, flags=re.UNICODE))
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return english_words + (cjk_chars // 2)  # approx


def extract_best_markdown(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    blocks = MARKDOWN_FENCE_RE.findall(raw)
    if blocks:
        return max(blocks, key=len).strip()
    return raw


def build_prompt(case_title: str, file_path: Path, block_text: str) -> str:
    return f"""
You are a senior hydraulic engineering and scientific Python educator.

Task:
Rewrite the following markdown case block into a technically deep explanation
of the specific Python code behavior and specific output/result interpretation
shown in the block.

Hard requirements:
1) Output must be valid markdown only, with no preface or epilogue.
2) Keep the same section structure/headings and preserve existing image/code links.
3) Produce at least 1000 words of substantive technical content.
4) Explain equations, algorithm flow, numerical stability, assumptions, units,
   convergence logic, and why the shown output values/charts make sense.
5) If empirical checks or KPIs are mentioned, explain what they validate and limits.
6) Do not invent new file paths or fake experiments; ground analysis in given block.
7) Keep language professional and textbook-grade.

Context:
- Chapter file: {file_path.as_posix()}
- Case label: {case_title}

Block to rewrite:
---BEGIN BLOCK---
{block_text}
---END BLOCK---
""".strip()


def run_codex_exec(
    prompt: str,
    cwd: Path,
    timeout_sec: int,
    min_words: int,
    retries: int,
    retry_sleep_sec: float,
) -> str:
    # Use absolute path to codex for Windows execution
    codex_path = r"C:\Users\lxh\Tools\node\node-v23.9.0-win-x64\codex.cmd"
    cmd = [codex_path, "exec", "--full-auto", prompt]
    last_error: Optional[str] = None

    for attempt in range(1, retries + 1):
        logging.info("Codex call attempt %d/%d", attempt, retries)
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_sec,
                check=False,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Cannot find `codex` in PATH. Install Codex CLI and verify `codex --help`."
            )
        except subprocess.TimeoutExpired as exc:
            last_error = f"Timeout after {timeout_sec}s: {exc}"
            logging.warning(last_error)
            if attempt < retries:
                time.sleep(retry_sleep_sec * attempt)
            continue
        except OSError as exc:
            last_error = f"OS error: {exc}"
            logging.warning(last_error)
            if attempt < retries:
                time.sleep(retry_sleep_sec * attempt)
            continue

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if proc.returncode != 0:
            last_error = (
                f"Codex exited {proc.returncode}. "
                f"stderr={stderr[:500]!r} stdout={stdout[:500]!r}"
            )
            logging.warning(last_error)
            if attempt < retries:
                time.sleep(retry_sleep_sec * attempt)
            continue

        rewritten = extract_best_markdown(stdout)
        if not rewritten:
            last_error = "Codex returned empty output."
            logging.warning(last_error)
            if attempt < retries:
                time.sleep(retry_sleep_sec * attempt)
            continue

        approx_words = count_words_mixed(rewritten)
        if approx_words < min_words:
            last_error = f"Output too short ({approx_words} < {min_words} words approx)."
            logging.warning(last_error)
            if attempt < retries:
                time.sleep(retry_sleep_sec * attempt)
            continue
        return rewritten

    raise RuntimeError(last_error or "Codex rewrite failed for unknown reasons.")


def atomic_write(path: Path, content: str) -> None:
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", delete=False, dir=path.parent
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def enrich_one_file(
    md_file: Path,
    min_words: int,
    timeout_sec: int,
    retries: int,
    retry_sleep_sec: float,
    dry_run: bool,
) -> Tuple[Path, int]:
    text = md_file.read_text(encoding="utf-8")
    blocks = extract_case_blocks(text)
    if not blocks:
        logging.info("[%s] no matching blocks found", md_file.name)
        return md_file, 0

    logging.info("[%s] found %d candidate blocks", md_file.name, len(blocks))

    new_text_parts: List[str] = []
    cursor = 0
    rewritten_count = 0

    for idx, block in enumerate(blocks, start=1):
        original_block = text[block.start : block.end]
        prompt = build_prompt(block.case_title, md_file, original_block)

        logging.info(
            "[%s] rewriting block %d/%d | case=%s | reflection=%s",
            md_file.name,
            idx,
            len(blocks),
            block.case_title,
            block.has_reflection,
        )

        rewritten = run_codex_exec(
            prompt=prompt,
            cwd=REPO_ROOT,
            timeout_sec=timeout_sec,
            min_words=min_words,
            retries=retries,
            retry_sleep_sec=retry_sleep_sec,
        )

        new_text_parts.append(text[cursor : block.start])
        new_text_parts.append(rewritten.rstrip() + "\n\n")
        cursor = block.end
        rewritten_count += 1

    new_text_parts.append(text[cursor:])
    enriched_text = "".join(new_text_parts)

    if dry_run:
        logging.info("[%s] dry-run complete; not writing file", md_file.name)
        return md_file, rewritten_count

    backup = md_file.with_suffix(md_file.suffix + ".bak")
    if not backup.exists():
        backup.write_text(text, encoding="utf-8")
        logging.info("[%s] backup written: %s", md_file.name, backup.name)

    atomic_write(md_file, enriched_text)
    logging.info("[%s] file updated with %d rewritten blocks", md_file.name, rewritten_count)
    return md_file, rewritten_count


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite mock case blocks via Codex CLI (`codex exec --full-auto`)."
    )
    parser.add_argument(
        "--book-dir",
        type=Path,
        default=DEFAULT_BOOK_DIR,
        help=f"Book directory containing markdown files (default: {DEFAULT_BOOK_DIR})",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=1,
        help="Maximum number of markdown files to process (default: 1).",
    )
    parser.add_argument(
        "--prefer-file",
        type=str,
        default=DEFAULT_TARGET_FILE,
        help=f"Preferred first file name (default: {DEFAULT_TARGET_FILE}).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Worker count. Values >1 are clamped to 1 to avoid rate limits.",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=1000,
        help="Minimum approximate words required from Codex output (default: 1000).",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=600,
        help="Timeout per Codex call in seconds (default: 600).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retry attempts per block rewrite (default: 3).",
    )
    parser.add_argument(
        "--retry-sleep-sec",
        type=float,
        default=3.0,
        help="Base sleep (seconds) between retries (default: 3.0).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and call Codex, but do not write files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logs.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    book_dir = args.book_dir.resolve()
    if not book_dir.exists():
        logging.error("Book directory does not exist: %s", book_dir)
        return 2

    concurrency = 1
    if args.concurrency != 1:
        logging.warning("Concurrency forced to 1 to avoid Codex/API rate limits.")

    files = list_target_files(
        book_dir=book_dir,
        max_files=max(1, args.max_files),
        prefer_file=args.prefer_file,
    )
    if not files:
        logging.error("No markdown files found in: %s", book_dir)
        return 2

    logging.info("Processing %d file(s) with concurrency=%d", len(files), concurrency)
    for f in files:
        logging.info("Target file: %s", f.name)

    total_blocks = 0
    failed = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(
                enrich_one_file,
                md_file=f,
                min_words=args.min_words,
                timeout_sec=args.timeout_sec,
                retries=args.retries,
                retry_sleep_sec=args.retry_sleep_sec,
                dry_run=args.dry_run,
            )
            for f in files
        ]
        for fut in concurrent.futures.as_completed(futures):
            try:
                file_path, rewritten = fut.result()
                total_blocks += rewritten
                logging.info("[%s] rewritten blocks: %d", file_path.name, rewritten)
            except Exception as exc:  # pylint: disable=broad-except
                failed = True
                logging.error("File processing failed: %s", exc)

    if failed:
        logging.error("Completed with failures. Total rewritten blocks so far: %d", total_blocks)
        return 1

    logging.info("Completed successfully. Total rewritten blocks: %d", total_blocks)
    return 0


if __name__ == "__main__":
    sys.exit(main())