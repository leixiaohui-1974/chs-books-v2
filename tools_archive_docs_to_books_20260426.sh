#!/bin/bash
set -euo pipefail
ROOT=/Users/rainfields/hydrosis-local/research/chs-books-v2
TARGET="$ROOT/books/20260426_manus_handover_docs"
mkdir -p "$TARGET/repo" "$TARGET/workspace" "$TARGET/skills"

find "$ROOT" \( \
  -path "$ROOT/T1-CN/tools/*20260426*.md" -o \
  -path "$ROOT/T1-CN/tools/*20260426*.txt" -o \
  -path "$ROOT/T2b/*20260425*.md" -o \
  -path "$ROOT/T2b/*20260426*.md" -o \
  -path "$ROOT/T5-Intelligence/*20260425*.md" -o \
  -path "$ROOT/T5-Intelligence/*20260426*.md" -o \
  -path "$ROOT/t2b_t5_front_half_progress_20260425.md" -o \
  -path "$ROOT/t2b_t5_round3_refinement_checklist_20260426.md" -o \
  -path "$ROOT/t2b_t5_sample_expansion_progress_20260425.md" \
\) -type f | while IFS= read -r f; do
  rel=${f#"$ROOT/"}
  mkdir -p "$TARGET/repo/$(dirname "$rel")"
  cp -f "$f" "$TARGET/repo/$rel"
done

find /mnt/desktop /home/ubuntu \( \
  -name 'book_*20260426.md' -o \
  -name 't1_*20260426.md' -o \
  -name 't2b_*20260425.md' -o \
  -name 't2b_*20260426.md' -o \
  -name 't5_*20260426.md' \
\) -type f 2>/dev/null | while IFS= read -r f; do
  base=$(basename "$f")
  mkdir -p "$TARGET/workspace"
  cp -f "$f" "$TARGET/workspace/$base"
done

SK=/mnt/desktop/home/ubuntu/skills/codex-cli-chinese-textbook-illustration
if [ ! -d "$SK" ]; then
  SK=/home/ubuntu/skills/codex-cli-chinese-textbook-illustration
fi
if [ -d "$SK" ]; then
  find "$SK" -type f | while IFS= read -r f; do
    rel=${f#"$SK/"}
    mkdir -p "$TARGET/skills/codex-cli-chinese-textbook-illustration/$(dirname "$rel")"
    cp -f "$f" "$TARGET/skills/codex-cli-chinese-textbook-illustration/$rel"
  done
fi

cat > "$TARGET/README.md" <<'EOF'
# 2026-04-26 Manus handover docs

此目录汇总本轮已形成的主要文档，便于后续 Claude 与 Codex 接续。

- `repo/`：已回写到 `chs-books-v2` 仓库内的文档
- `workspace/`：本轮在工作区形成的研究、检查点与批次记录
- `skills/`：新沉淀的 Codex CLI 中文教材插图 Skill
EOF

echo "[TARGET]"
echo "$TARGET"
echo
echo "[COUNTS]"
find "$TARGET" -type f | wc -l
echo
echo "[SAMPLE]"
find "$TARGET" -type f | sort | sed -n '1,120p'
