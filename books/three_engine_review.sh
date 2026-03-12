#!/bin/bash
# 三引擎协作评审脚本 (直接使用Bash,避免Python subprocess问题)
# 使用方法: bash three_engine_review.sh <book_name> <chapter_num>

set -e

BOOK_NAME=$1
CHAPTER_NUM=$2
BASE_DIR="D:/cowork/教材/chs-books-v2/books"
BOOK_DIR="$BASE_DIR/$BOOK_NAME"
CHAPTER_FILE="$BOOK_DIR/ch${CHAPTER_NUM}.md"
REVIEW_DIR="$BOOK_DIR/reviews"

# 创建评审目录
mkdir -p "$REVIEW_DIR"

echo "=========================================="
echo "三引擎协作评审"
echo "书名: $BOOK_NAME"
echo "章节: ch${CHAPTER_NUM}.md"
echo "=========================================="

# 检查章节文件
if [ ! -f "$CHAPTER_FILE" ]; then
    echo "错误: 章节文件不存在: $CHAPTER_FILE"
    exit 1
fi

# ==========================================
# Codex评审
# ==========================================
echo ""
echo "[1/3] Codex CLI 技术评审中..."

CODEX_OUTPUT="$REVIEW_DIR/ch${CHAPTER_NUM}_codex_review.txt"

CODEX_PROMPT="请以控制理论专家的角度评审这一章节,重点关注:
1. 控制理论的应用是否准确
2. 优化算法描述的完整性
3. 动态规划推导的严谨性
4. 与现代控制理论的衔接
5. 技术细节的准确性(公式、符号、单位)

请给出:
- 高优先级问题(P1): 必须修复的技术错误
- 中优先级问题(P2): 建议改进的技术细节
- 低优先级问题(P3): 可选的优化建议

每个问题请标注具体行号或段落位置。"

cd "$BOOK_DIR"
codex exec "$CODEX_PROMPT" --skip-git-repo-check --cd . -o "$CODEX_OUTPUT" 2>&1

if [ -f "$CODEX_OUTPUT" ]; then
    echo "✓ Codex评审完成: $CODEX_OUTPUT"
else
    echo "✗ Codex评审失败"
fi

# ==========================================
# Gemini评审
# ==========================================
echo ""
echo "[2/3] Gemini CLI 水利专家评审中..."

GEMINI_OUTPUT="$REVIEW_DIR/ch${CHAPTER_NUM}_gemini_review.txt"

GEMINI_PROMPT="请以水利水电工程专家的角度评审这一章节,重点关注:
1. 水利工程概念的准确性
2. 案例数据的真实性和合理性
3. 工程实践的可操作性
4. 术语使用的规范性

请给出:
- 工程可行性评分(1-10分)
- 案例真实性评分(1-10分)
- 主要问题列表
- 改进建议

请用中文回复。"

cat "$CHAPTER_FILE" | gemini -p "$GEMINI_PROMPT" > "$GEMINI_OUTPUT" 2>&1

if [ -f "$GEMINI_OUTPUT" ]; then
    echo "✓ Gemini评审完成: $GEMINI_OUTPUT"
else
    echo "✗ Gemini评审失败"
fi

# ==========================================
# 生成汇总
# ==========================================
echo ""
echo "[3/3] 生成评审汇总..."

SUMMARY_FILE="$REVIEW_DIR/ch${CHAPTER_NUM}_summary.md"

cat > "$SUMMARY_FILE" << EOF
# ch${CHAPTER_NUM} 三引擎评审汇总

> 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
> 章节: $BOOK_NAME/ch${CHAPTER_NUM}.md

---

## 一、Codex评审 (控制理论专家)

$(cat "$CODEX_OUTPUT" 2>/dev/null || echo "评审失败")

---

## 二、Gemini评审 (水利工程专家)

$(cat "$GEMINI_OUTPUT" 2>/dev/null || echo "评审失败")

---

## 三、Claude综合分析

### 3.1 问题优先级排序

**P0级问题** (必须立即修复):
- [ ] 待Claude分析后填写

**P1级问题** (高优先级):
- [ ] 待填写

**P2级问题** (中优先级):
- [ ] 待填写

### 3.2 修改建议

待Claude根据两个引擎的评审意见生成具体修改方案。

---

## 四、下一步行动

1. ✓ Codex技术评审完成
2. ✓ Gemini水利专家评审完成
3. ⏳ Claude分析评审意见
4. ⏳ 生成修改方案
5. ⏳ 执行修改
6. ⏳ 验证修改结果

EOF

echo "✓ 评审汇总完成: $SUMMARY_FILE"

# ==========================================
# 显示结果
# ==========================================
echo ""
echo "=========================================="
echo "✓ 三引擎评审完成!"
echo "=========================================="
echo ""
echo "生成的文件:"
echo "  1. Codex评审: $CODEX_OUTPUT"
echo "  2. Gemini评审: $GEMINI_OUTPUT"
echo "  3. 评审汇总: $SUMMARY_FILE"
echo ""
echo "下一步: 请Claude分析评审意见并生成修改方案"
echo ""

# 显示评审结果预览
echo "--- Codex评审预览 (前20行) ---"
head -20 "$CODEX_OUTPUT" 2>/dev/null || echo "无内容"
echo ""
echo "--- Gemini评审预览 (前20行) ---"
head -20 "$GEMINI_OUTPUT" 2>/dev/null || echo "无内容"
echo ""
