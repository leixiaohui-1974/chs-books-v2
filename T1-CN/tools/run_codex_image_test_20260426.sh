#!/bin/bash
set -euo pipefail
SCRATCH_DIR="$HOME/codex_image_scratch"
REPO_OUT="$HOME/hydrosis-local/research/chs-books-v2/T1-CN/H/codex_min_image_test_20260426.png"
PROMPT_FILE="$SCRATCH_DIR/prompt.txt"
LAST_FILE="$SCRATCH_DIR/last.txt"
mkdir -p "$SCRATCH_DIR"
cat > "$PROMPT_FILE" <<'EOF'
只做一件事：使用你可用的 image_generation 能力，从零生成一张新的 PNG 图片并保存到指定路径。

输出路径：__OUTPUT_PATH__

图片要求：
- 白色背景
- 蓝色主调
- 中文标题“自主运行闭环”
- 四个节点“系统感知→系统决策→系统执行→系统学习”首尾闭环箭头连接
- 学术教材风格
- 扁平矢量
- 不要中英双语

限制：
1. 不要读取、转换、复制或修复任何现有图片；
2. 不要写代码说明文档代替图片；
3. 只需创建这个 PNG 文件，并最后简短说明是否成功。
EOF
python3 - <<'PY'
from pathlib import Path
p = Path.home() / 'codex_image_scratch' / 'prompt.txt'
text = p.read_text()
out = str(Path.home() / 'hydrosis-local' / 'research' / 'chs-books-v2' / 'T1-CN' / 'H' / 'codex_min_image_test_20260426.png')
p.write_text(text.replace('__OUTPUT_PATH__', out))
PY
cd "$SCRATCH_DIR"
codex exec --ignore-rules --ignore-user-config --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C "$SCRATCH_DIR" -o "$LAST_FILE" - < "$PROMPT_FILE"
if [ -f "$REPO_OUT" ]; then
  echo "[generated] $REPO_OUT"
  file "$REPO_OUT" || true
else
  echo "[missing] $REPO_OUT"
fi
if [ -f "$LAST_FILE" ]; then
  echo "[last-message]"
  sed -n '1,200p' "$LAST_FILE"
fi
