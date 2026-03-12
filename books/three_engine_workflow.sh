#!/bin/bash
# -*- coding: utf-8 -*-
# 三引擎协作评审与修改工作流
# 使用: bash three_engine_workflow.sh <book_name> <chapter_num>
# 示例: bash three_engine_workflow.sh reservoir-operation-optimization 01

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
echo "三引擎协作评审工作流"
echo "书名: $BOOK_NAME"
echo "章节: ch${CHAPTER_NUM}.md"
echo "=========================================="

# 检查章节文件是否存在
if [ ! -f "$CHAPTER_FILE" ]; then
    echo "错误: 章节文件不存在: $CHAPTER_FILE"
    exit 1
fi

# ==========================================
# 第一步: Codex CLI 技术评审
# ==========================================
echo ""
echo "[1/5] Codex CLI 技术评审中..."
echo "评审角度: 控制理论准确性、数学严谨性、工程可行性"

CODEX_PROMPT="请以控制理论专家的角度评审这一章节,重点关注:
1. 控制理论的应用是否准确
2. 优化算法描述的完整性
3. 动态规划推导的严谨性
4. 与现代控制理论的衔接
5. 技术细节的准确性(公式、符号、单位)
6. 工程实践的可行性

请给出:
- 高优先级问题(P1): 必须修复的技术错误
- 中优先级问题(P2): 建议改进的技术细节
- 低优先级问题(P3): 可选的优化建议

每个问题请标注具体行号或段落位置。"

codex exec "$CODEX_PROMPT" \
    --skip-git-repo-check \
    --cd "$BOOK_DIR" \
    -o "$REVIEW_DIR/ch${CHAPTER_NUM}_codex_review.txt"

echo "✓ Codex评审完成: $REVIEW_DIR/ch${CHAPTER_NUM}_codex_review.txt"

# ==========================================
# 第二步: Gemini CLI 水利专家评审
# ==========================================
echo ""
echo "[2/5] Gemini CLI 水利专家评审中..."
echo "评审角度: 水利工程实践、案例真实性、行业规范"

GEMINI_PROMPT="请以水利水电工程专家的角度评审这一章节,重点关注:
1. 水利工程概念的准确性
2. 案例数据的真实性和合理性
3. 工程实践的可操作性
4. 行业规范和标准的符合性
5. 术语使用的规范性
6. 与实际工程的契合度

请给出:
- 工程可行性评分(1-10分)
- 案例真实性评分(1-10分)
- 主要问题列表
- 改进建议

请用中文回复。"

cat "$CHAPTER_FILE" | gemini -p "$GEMINI_PROMPT" > "$REVIEW_DIR/ch${CHAPTER_NUM}_gemini_review.txt"

echo "✓ Gemini评审完成: $REVIEW_DIR/ch${CHAPTER_NUM}_gemini_review.txt"

# ==========================================
# 第三步: 汇总评审意见
# ==========================================
echo ""
echo "[3/5] 汇总评审意见中..."

cat > "$REVIEW_DIR/ch${CHAPTER_NUM}_summary.md" << EOF
# ch${CHAPTER_NUM} 三引擎评审汇总

> 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
> 章节: $BOOK_NAME/ch${CHAPTER_NUM}.md

---

## 一、Codex评审 (控制理论专家)

$(cat "$REVIEW_DIR/ch${CHAPTER_NUM}_codex_review.txt")

---

## 二、Gemini评审 (水利工程专家)

$(cat "$REVIEW_DIR/ch${CHAPTER_NUM}_gemini_review.txt")

---

## 三、Claude综合分析

### 3.1 问题优先级排序

**P0级问题** (必须立即修复):
- [ ] 待Claude分析Codex和Gemini的评审意见后填写

**P1级问题** (高优先级):
- [ ] 待填写

**P2级问题** (中优先级):
- [ ] 待填写

### 3.2 修改建议

待Claude根据两个引擎的评审意见生成具体修改方案。

---

## 四、下一步行动

1. Claude分析评审意见
2. 生成修改方案
3. 使用Codex/Gemini执行修改
4. 验证修改结果
5. 进行下一轮评审

EOF

echo "✓ 评审汇总完成: $REVIEW_DIR/ch${CHAPTER_NUM}_summary.md"

# ==========================================
# 第四步: 显示评审结果
# ==========================================
echo ""
echo "[4/5] 评审结果预览"
echo "=========================================="
echo ""
echo "--- Codex评审 (前30行) ---"
head -30 "$REVIEW_DIR/ch${CHAPTER_NUM}_codex_review.txt"
echo ""
echo "--- Gemini评审 (前30行) ---"
head -30 "$REVIEW_DIR/ch${CHAPTER_NUM}_gemini_review.txt"
echo ""
echo "=========================================="

# ==========================================
# 第五步: 生成修改任务清单
# ==========================================
echo ""
echo "[5/5] 生成修改任务清单..."

cat > "$REVIEW_DIR/ch${CHAPTER_NUM}_tasks.md" << EOF
# ch${CHAPTER_NUM} 修改任务清单

> 生成时间: $(date '+%Y-%m-%d %H:%M:%S')

## 待办任务

### 高优先级 (P1)
- [ ] 任务1: 待Claude分析后填写
- [ ] 任务2: 待填写

### 中优先级 (P2)
- [ ] 任务1: 待填写

### 低优先级 (P3)
- [ ] 任务1: 待填写

## 修改记录

| 时间 | 修改内容 | 负责引擎 | 状态 |
|------|---------|---------|------|
| - | - | - | - |

EOF

echo "✓ 任务清单生成: $REVIEW_DIR/ch${CHAPTER_NUM}_tasks.md"

# ==========================================
# 完成
# ==========================================
echo ""
echo "=========================================="
echo "✓ 三引擎评审完成!"
echo "=========================================="
echo ""
echo "生成的文件:"
echo "  1. Codex评审: $REVIEW_DIR/ch${CHAPTER_NUM}_codex_review.txt"
echo "  2. Gemini评审: $REVIEW_DIR/ch${CHAPTER_NUM}_gemini_review.txt"
echo "  3. 评审汇总: $REVIEW_DIR/ch${CHAPTER_NUM}_summary.md"
echo "  4. 任务清单: $REVIEW_DIR/ch${CHAPTER_NUM}_tasks.md"
echo ""
echo "下一步: 请Claude分析评审意见并生成修改方案"
echo ""
