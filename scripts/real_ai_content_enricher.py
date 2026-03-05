#!/usr/bin/env python3
"""
Gemini Book Publishing Workshop: Integrator/Rewriter Context Enricher.

This script orchestrates the "Gemini图书出版工坊" Integrator/Rewriter persona
(Codex-D) to overhaul un-enriched `### ... (Context)` case sections across
all discovered books.

Key behavior:
- Scans all books under `books/` (default expected count: 17).
- Detects case-level Context sections and identifies likely un-enriched blocks.
- Calls `codex exec --full-auto "<prompt>"` per target block.
- Uses rate limiting + retries + timeout + resumable state journaling.
- Applies each successful rewrite with atomic file replacement.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import time
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Sequence, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOKS_ROOT = REPO_ROOT / "books"
DEFAULT_REPORT_DIR = REPO_ROOT / "publishing_reports"
DEFAULT_STATE_FILE = DEFAULT_REPORT_DIR / "context_enrichment_state.jsonl"

H3_HEADING_RE = re.compile(r"(?m)^###\s+.*$")
CASE_HEADING_RE = re.compile(r"(?im)^###\s+Case\b.*$")
CONTEXT_HEADING_RE = re.compile(r"(?im)^###\s+.*\(Context\)\s*$")
PROBLEM_HEADING_RE = re.compile(r"(?im)^###\s+.*\(Problem\)\s*$")
CODE_HEADING_RE = re.compile(r"(?im)^###\s+.*\(Code\s*&\s*Charts\)\s*$")
RESULT_HEADING_RE = re.compile(r"(?im)^###\s+.*\(Result\s*Interpretation\)\s*$")
IMAGE_LINK_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
MARKDOWN_FENCE_RE = re.compile(
    r"```(?:markdown|md)?\s*(.*?)```", re.IGNORECASE | re.DOTALL
)

GENERIC_CONTEXT_MARKERS = (
    "chs-books",
    "fastmcp",
    "kalman",
    "automated extraction",
    "legacy asset",
)


@dataclass
class ContextBlock:
    file_path: Path
    relative_path: str
    case_title: str
    ordinal: int
    context_heading: str
    context_body: str
    context_body_start: int
    context_body_end: int
    problem_section: str
    code_section: str
    result_section: str
    case_excerpt: str
    figure_links: List[str]
    fingerprint: str


@dataclass
class RunStats:
    books_discovered: int = 0
    files_discovered: int = 0
    context_blocks_discovered: int = 0
    target_blocks: int = 0
    skipped_already_done: int = 0
    rewritten_success: int = 0
    rewritten_failed: int = 0


class RateLimiter:
    def __init__(self, min_interval_sec: float, jitter_sec: float) -> None:
        self.min_interval_sec = max(0.0, min_interval_sec)
        self.jitter_sec = max(0.0, jitter_sec)
        self._next_allowed = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        if now < self._next_allowed:
            time.sleep(self._next_allowed - now)
        jitter = random.uniform(0.0, self.jitter_sec) if self.jitter_sec else 0.0
        self._next_allowed = time.monotonic() + self.min_interval_sec + jitter


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def read_text_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logging.warning("[%s] UTF-8 decode fallback with replacement", path.name)
        return path.read_text(encoding="utf-8", errors="replace")


def atomic_write(path: Path, content: str) -> None:
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", delete=False, dir=path.parent
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def ensure_backup(path: Path, original_text: str, backup_suffix: str) -> Optional[Path]:
    if not backup_suffix:
        return None
    backup_path = path.with_name(path.name + backup_suffix)
    if backup_path.exists():
        return backup_path
    backup_path.write_text(original_text, encoding="utf-8")
    return backup_path


def count_words_mixed(text: str) -> int:
    english_words = len(re.findall(r"\b[\w-]+\b", text, flags=re.UNICODE))
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return english_words + (cjk_chars // 2)


def normalize_fingerprint(text: str) -> str:
    compact = re.sub(r"\s+", " ", text.strip().lower())
    compact = re.sub(r"[^\w\u4e00-\u9fff]+", "", compact)
    return compact


def extract_best_markdown(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    blocks = MARKDOWN_FENCE_RE.findall(raw)
    if blocks:
        return max(blocks, key=len).strip()
    return raw


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)] + "…"


def _skip_newlines(text: str, idx: int) -> int:
    while idx < len(text) and text[idx] in "\r\n":
        idx += 1
    return idx


def _find_section_text(
    text: str,
    headings: List[re.Match[str]],
    pattern: re.Pattern[str],
    fallback_end: int,
) -> str:
    for i, heading in enumerate(headings):
        if pattern.match(heading.group(0).strip()):
            start = _skip_newlines(text, heading.end())
            end = headings[i + 1].start() if i + 1 < len(headings) else fallback_end
            return text[start:end].strip()
    return ""


def extract_context_blocks(file_path: Path, relative_path: str, text: str) -> List[ContextBlock]:
    case_matches = list(CASE_HEADING_RE.finditer(text))
    if not case_matches:
        return []

    blocks: List[ContextBlock] = []
    for i, case_match in enumerate(case_matches, start=1):
        case_start = case_match.start()
        case_end = case_matches[i].start() if i < len(case_matches) else len(text)
        case_title = case_match.group(0).strip()
        case_excerpt = text[case_start:case_end].strip()
        case_headings = list(H3_HEADING_RE.finditer(text, case_start, case_end))
        if not case_headings:
            continue

        context_index: Optional[int] = None
        for h_idx, h_match in enumerate(case_headings):
            if CONTEXT_HEADING_RE.match(h_match.group(0).strip()):
                context_index = h_idx
                break
        if context_index is None:
            continue

        context_heading = case_headings[context_index].group(0).strip()
        context_body_start = _skip_newlines(text, case_headings[context_index].end())
        context_body_end = (
            case_headings[context_index + 1].start()
            if context_index + 1 < len(case_headings)
            else case_end
        )
        context_body = text[context_body_start:context_body_end].strip()

        blocks.append(
            ContextBlock(
                file_path=file_path,
                relative_path=relative_path,
                case_title=case_title,
                ordinal=i,
                context_heading=context_heading,
                context_body=context_body,
                context_body_start=context_body_start,
                context_body_end=context_body_end,
                problem_section=_find_section_text(
                    text, case_headings, PROBLEM_HEADING_RE, case_end
                ),
                code_section=_find_section_text(text, case_headings, CODE_HEADING_RE, case_end),
                result_section=_find_section_text(
                    text, case_headings, RESULT_HEADING_RE, case_end
                ),
                case_excerpt=truncate(case_excerpt, 5000),
                figure_links=IMAGE_LINK_RE.findall(case_excerpt),
                fingerprint=normalize_fingerprint(context_body),
            )
        )

    return blocks


def build_block_id(block: ContextBlock) -> str:
    base = f"{block.relative_path}|{block.case_title}|{block.ordinal}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return f"{block.relative_path}::case{block.ordinal:03d}::{digest}"


def looks_unenriched_context(
    block: ContextBlock,
    duplicate_count: int,
    min_context_chars: int,
    repeat_threshold: int,
) -> bool:
    text = block.context_body.strip()
    if not text:
        return True
    if duplicate_count >= max(2, repeat_threshold):
        return True
    lowered = text.lower()
    if any(marker in lowered for marker in GENERIC_CONTEXT_MARKERS):
        return True
    if len(text) < max(0, min_context_chars):
        return True
    return False


def resolve_codex_bin(codex_bin_arg: str) -> str:
    candidates: List[str] = []
    if codex_bin_arg:
        candidates.append(codex_bin_arg)
    env_bin = os.getenv("CODEX_BIN", "").strip()
    if env_bin:
        candidates.append(env_bin)
    for exe in ("codex", "codex.cmd", "codex.ps1"):
        found = shutil.which(exe)
        if found:
            candidates.append(found)
    candidates.append(r"C:\Users\lxh\Tools\node\node-v23.9.0-win-x64\codex.cmd")

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return str(path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError(
        "Cannot locate codex CLI. Set --codex-bin or CODEX_BIN to the codex executable."
    )


def normalize_context_output(raw_output: str) -> str:
    text = extract_best_markdown(raw_output).replace("\r\n", "\n").strip()
    if not text:
        return text

    context_match = CONTEXT_HEADING_RE.search(text)
    if context_match:
        start = _skip_newlines(text, context_match.end())
        next_heading = H3_HEADING_RE.search(text, start)
        end = next_heading.start() if next_heading else len(text)
        text = text[start:end].strip()

    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("### ")]
    return "\n".join(lines).strip()


def build_prompt(block: ContextBlock, run_label: str) -> str:
    figure_lines = (
        "\n".join(f"- {link}" for link in block.figure_links[:10])
        if block.figure_links
        else "- (No figure links detected in this case block.)"
    )
    return f"""
You are the "Gemini图书出版工坊" Integrator/Rewriter persona (Codex-D).
You are executing an overnight publication overhaul across a 17-book program.

Task:
Rewrite ONLY the markdown body of the existing `### 🌟 案例背景 (Context)` section.

Output constraints:
1) Return markdown body text only. Do not output section headings.
2) 2-4 coherent paragraphs, pedagogical textbook tone.
3) Make it case-specific by grounding in the real code/figure evidence below.
4) Explain what students should understand before running the code.
5) Do not fabricate files, figures, metrics, equations, or experiments.
6) If evidence is sparse, stay conservative and explicitly avoid overclaiming.

Metadata:
- Run label: {run_label}
- Chapter file: {block.relative_path}
- Case heading: {block.case_title}

Current context body (to replace):
---BEGIN CURRENT CONTEXT---
{truncate(block.context_body, 900)}
---END CURRENT CONTEXT---

Problem excerpt:
---BEGIN PROBLEM---
{truncate(block.problem_section, 900)}
---END PROBLEM---

Code & charts excerpt:
---BEGIN CODE_AND_CHARTS---
{truncate(block.code_section, 1400)}
---END CODE_AND_CHARTS---

Result interpretation excerpt:
---BEGIN RESULT---
{truncate(block.result_section, 900)}
---END RESULT---

Figure links seen in this case:
{figure_lines}

Case fallback excerpt:
---BEGIN CASE EXCERPT---
{truncate(block.case_excerpt, 1300)}
---END CASE EXCERPT---
""".strip()


def run_codex_exec(
    codex_bin: str,
    prompt: str,
    cwd: Path,
    timeout_sec: int,
    retries: int,
    backoff_sec: float,
    min_words: int,
    limiter: RateLimiter,
) -> str:
    cmd = [codex_bin, "exec", "--full-auto", prompt]
    last_error: Optional[str] = None

    for attempt in range(1, retries + 1):
        limiter.wait()
        logging.info("Codex attempt %d/%d", attempt, retries)
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
        except subprocess.TimeoutExpired:
            last_error = f"Timeout after {timeout_sec}s."
        except OSError as exc:
            last_error = f"OS error while invoking codex: {exc}"
        else:
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            if proc.returncode != 0:
                last_error = (
                    f"Codex exit code {proc.returncode}. "
                    f"stderr={stderr[:400]!r} stdout={stdout[:400]!r}"
                )
            else:
                rewritten = normalize_context_output(stdout)
                if not rewritten:
                    last_error = "Codex returned empty content after normalization."
                else:
                    approx_words = count_words_mixed(rewritten)
                    if approx_words < min_words:
                        last_error = (
                            f"Output too short ({approx_words} < {min_words} approx words)."
                        )
                    else:
                        return rewritten

        logging.warning("Codex attempt failed: %s", last_error)
        if attempt < retries:
            sleep_sec = backoff_sec * (2 ** (attempt - 1))
            sleep_sec += random.uniform(0.0, 1.0)
            time.sleep(sleep_sec)

    raise RuntimeError(last_error or "Codex rewrite failed without a captured error.")


def append_state_entry(state_file: Path, payload: Dict[str, object]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_success_ids(state_file: Path) -> Set[str]:
    done: Set[str] = set()
    if not state_file.exists():
        return done
    for line in state_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("status") == "success" and record.get("block_id"):
            done.add(str(record["block_id"]))
    return done


def collect_books_and_files(books_root: Path) -> Tuple[List[Path], List[Path]]:
    books = sorted(
        d for d in books_root.iterdir() if d.is_dir() and not d.name.startswith(".")
    )
    files: List[Path] = []
    for book in books:
        files.extend(sorted(book.glob("ch*.md")))
    return books, files


def write_summary(report_dir: Path, run_label: str, summary: Dict[str, object]) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    out_path = report_dir / f"context_enrichment_summary_{run_label}.json"
    atomic_write(out_path, json.dumps(summary, ensure_ascii=False, indent=2))
    return out_path


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overnight Context enrichment via Codex CLI + Gemini workshop persona."
    )
    parser.add_argument(
        "--books-root",
        type=Path,
        default=DEFAULT_BOOKS_ROOT,
        help=f"Books root directory (default: {DEFAULT_BOOKS_ROOT})",
    )
    parser.add_argument(
        "--expected-books",
        type=int,
        default=17,
        help="Expected book count for monitoring (default: 17).",
    )
    parser.add_argument(
        "--codex-bin",
        type=str,
        default="",
        help="Path to codex executable (fallback: CODEX_BIN env / PATH).",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help=f"Directory for reports (default: {DEFAULT_REPORT_DIR}).",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_FILE,
        help=f"JSONL state journal (default: {DEFAULT_STATE_FILE}).",
    )
    parser.add_argument(
        "--backup-suffix",
        type=str,
        default=".pre_context_enrich.bak",
        help="Backup suffix written once per changed file (default: .pre_context_enrich.bak).",
    )
    parser.add_argument(
        "--rewrite-all",
        action="store_true",
        help="Rewrite all Context blocks (ignore un-enriched filtering).",
    )
    parser.add_argument(
        "--repeat-threshold",
        type=int,
        default=2,
        help="Fingerprint repeat count to mark as un-enriched (default: 2).",
    )
    parser.add_argument(
        "--min-context-chars",
        type=int,
        default=160,
        help="If context is shorter than this, mark as un-enriched (default: 160).",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=100,
        help="Minimum approximate words in rewritten context (default: 100).",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=900,
        help="Timeout per codex call in seconds (default: 900).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=4,
        help="Retry count per block rewrite (default: 4).",
    )
    parser.add_argument(
        "--backoff-sec",
        type=float,
        default=6.0,
        help="Base exponential backoff in seconds (default: 6.0).",
    )
    parser.add_argument(
        "--min-call-interval-sec",
        type=float,
        default=10.0,
        help="Minimum delay between codex calls in seconds (default: 10).",
    )
    parser.add_argument(
        "--jitter-sec",
        type=float,
        default=1.0,
        help="Additional random jitter for each codex call (default: 1.0).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report targets without calling codex or writing files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)
    run_label = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats = RunStats()

    books_root = args.books_root.resolve()
    if not books_root.exists():
        logging.error("Books root does not exist: %s", books_root)
        return 2

    books, files = collect_books_and_files(books_root)
    stats.books_discovered = len(books)
    stats.files_discovered = len(files)
    if args.expected_books > 0 and stats.books_discovered != args.expected_books:
        logging.warning(
            "Expected %d books but found %d under %s. Continuing with discovered set.",
            args.expected_books,
            stats.books_discovered,
            books_root,
        )
    if not files:
        logging.error("No chapter files (ch*.md) found under %s", books_root)
        return 2

    all_blocks: List[ContextBlock] = []
    file_to_blocks: Dict[Path, List[ContextBlock]] = defaultdict(list)
    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = read_text_utf8(path)
        blocks = extract_context_blocks(path, rel, text)
        if blocks:
            all_blocks.extend(blocks)
            file_to_blocks[path].extend(blocks)

    stats.context_blocks_discovered = len(all_blocks)
    if not all_blocks:
        logging.warning("No case Context blocks found. Nothing to do.")
        return 0

    fingerprint_counts = Counter(block.fingerprint for block in all_blocks if block.fingerprint)
    target_ids_by_file: Dict[Path, List[str]] = defaultdict(list)
    for block in all_blocks:
        block_id = build_block_id(block)
        is_target = args.rewrite_all or looks_unenriched_context(
            block=block,
            duplicate_count=fingerprint_counts.get(block.fingerprint, 0),
            min_context_chars=args.min_context_chars,
            repeat_threshold=args.repeat_threshold,
        )
        if is_target:
            target_ids_by_file[block.file_path].append(block_id)

    stats.target_blocks = sum(len(v) for v in target_ids_by_file.values())
    if stats.target_blocks == 0:
        logging.info("No un-enriched Context blocks detected. Nothing to rewrite.")
        return 0

    logging.info(
        "Integrator/Rewriter (Codex-D) orchestration prepared | books=%d files=%d contexts=%d targets=%d",
        stats.books_discovered,
        stats.files_discovered,
        stats.context_blocks_discovered,
        stats.target_blocks,
    )

    completed_ids = load_success_ids(args.state_file.resolve())
    already_done = 0
    for ids in target_ids_by_file.values():
        for block_id in ids:
            if block_id in completed_ids:
                already_done += 1
    stats.skipped_already_done = already_done
    if already_done:
        logging.info("Resume mode: %d target blocks already marked success in state file.", already_done)

    codex_bin = ""
    if not args.dry_run:
        codex_bin = resolve_codex_bin(args.codex_bin)
        logging.info("Using codex binary: %s", codex_bin)

    limiter = RateLimiter(args.min_call_interval_sec, args.jitter_sec)
    run_failed_ids: Set[str] = set()

    for file_path in sorted(target_ids_by_file.keys()):
        rel = file_path.relative_to(REPO_ROOT).as_posix()
        logging.info("Processing file: %s", rel)

        while True:
            text = read_text_utf8(file_path)
            current_blocks = extract_context_blocks(file_path, rel, text)
            current_map = {build_block_id(block): block for block in current_blocks}

            next_block: Optional[ContextBlock] = None
            next_block_id: Optional[str] = None
            for block_id in target_ids_by_file[file_path]:
                if block_id in completed_ids or block_id in run_failed_ids:
                    continue
                candidate = current_map.get(block_id)
                if candidate:
                    next_block = candidate
                    next_block_id = block_id
                    break

            if not next_block or not next_block_id:
                break

            log_prefix = f"{rel} | {next_block.case_title} | {next_block_id}"
            if args.dry_run:
                logging.info("[DRY-RUN] would rewrite: %s", log_prefix)
                completed_ids.add(next_block_id)
                stats.rewritten_success += 1
                continue

            prompt = build_prompt(next_block, run_label=run_label)
            try:
                rewritten_body = run_codex_exec(
                    codex_bin=codex_bin,
                    prompt=prompt,
                    cwd=REPO_ROOT,
                    timeout_sec=args.timeout_sec,
                    retries=args.retries,
                    backoff_sec=args.backoff_sec,
                    min_words=args.min_words,
                    limiter=limiter,
                )
                updated_text = (
                    text[: next_block.context_body_start]
                    + rewritten_body.strip()
                    + "\n\n"
                    + text[next_block.context_body_end :]
                )
                ensure_backup(file_path, text, args.backup_suffix)
                atomic_write(file_path, updated_text)
                completed_ids.add(next_block_id)
                stats.rewritten_success += 1
                append_state_entry(
                    args.state_file.resolve(),
                    {
                        "ts": datetime.now().isoformat(timespec="seconds"),
                        "run_label": run_label,
                        "status": "success",
                        "persona": "Gemini图书出版工坊 Integrator/Rewriter (Codex-D)",
                        "block_id": next_block_id,
                        "file": rel,
                        "case_title": next_block.case_title,
                        "approx_words": count_words_mixed(rewritten_body),
                    },
                )
                logging.info("Rewrote context successfully: %s", log_prefix)
            except Exception as exc:
                stats.rewritten_failed += 1
                run_failed_ids.add(next_block_id)
                append_state_entry(
                    args.state_file.resolve(),
                    {
                        "ts": datetime.now().isoformat(timespec="seconds"),
                        "run_label": run_label,
                        "status": "failed",
                        "persona": "Gemini图书出版工坊 Integrator/Rewriter (Codex-D)",
                        "block_id": next_block_id,
                        "file": rel,
                        "case_title": next_block.case_title,
                        "error": str(exc),
                    },
                )
                logging.error("Failed to rewrite context: %s | error=%s", log_prefix, exc)

    summary = {
        "run_label": run_label,
        "persona": "Gemini图书出版工坊 Integrator/Rewriter (Codex-D)",
        "books_discovered": stats.books_discovered,
        "files_discovered": stats.files_discovered,
        "context_blocks_discovered": stats.context_blocks_discovered,
        "target_blocks": stats.target_blocks,
        "skipped_already_done": stats.skipped_already_done,
        "rewritten_success": stats.rewritten_success,
        "rewritten_failed": stats.rewritten_failed,
        "dry_run": bool(args.dry_run),
        "state_file": args.state_file.resolve().as_posix(),
    }
    summary_path = write_summary(args.report_dir.resolve(), run_label, summary)
    logging.info("Run summary written: %s", summary_path.as_posix())

    if stats.rewritten_failed > 0:
        logging.error(
            "Completed with failures: success=%d failed=%d",
            stats.rewritten_success,
            stats.rewritten_failed,
        )
        return 1

    logging.info("Completed successfully: rewritten=%d", stats.rewritten_success)
    return 0


if __name__ == "__main__":
    sys.exit(main())