#!/bin/bash
# Gemini + Codex 联合评审脚本
# 用途: 对已修复的ch01进行二次评审

BOOK_DIR="D:/cowork/教材/chs-books-v2/books/reservoir-operation-optimization"
CHAPTER_FILE="$BOOK_DIR/ch01.md"
REVIEW_DIR="$BOOK_DIR/reviews"

echo "========================================="
echo "Gemini + Codex 联合评审 - ch01 (已修复P1)"
echo "========================================="

# 1. Gemini评审 (水利工程实践角度)
echo ""
echo "[1/2] 启动Gemini评审..."
gemini -p "请以水利工程专家的角度评审这个水库调度章节。重点关注:
1. 工程案例的真实性和代表性
2. 与现行规范(SL706-2015等)的符合性
3. 动态防洪限制水位调整的工程可行性
4. 公式中的工程参数是否合理
5. 是否存在工程实践中的风险点

请列出3-5个主要问题,并给出7个维度的评分(1-10分)。

章节内容:
$(cat "$CHAPTER_FILE")
" > "$REVIEW_DIR/ch01_gemini_review_v2.txt" 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Gemini评审完成: ch01_gemini_review_v2.txt"
else
    echo "✗ Gemini评审失败,请检查认证状态"
fi

# 2. Codex评审 (控制理论角度)
echo ""
echo "[2/2] 启动Codex评审..."
codex exec "请以控制理论专家的角度评审这个章节。重点关注:
1. 逆向水量平衡方程的数学正确性(已修复,请验证)
2. 动态规划算法的完整性
3. 状态转移方程的严谨性
4. 符号使用的一致性
5. 是否需要补充算法伪代码

请列出3-5个技术问题,并给出评分。" \
--cd "$BOOK_DIR" \
--skip-git-repo-check \
-o "$REVIEW_DIR/ch01_codex_review_v2.txt" 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Codex评审完成: ch01_codex_review_v2.txt"
else
    echo "✗ Codex评审失败"
fi

# 3. 生成综合报告
echo ""
echo "[3/3] 生成综合报告..."
echo "# ch01二次评审综合报告 (P1修复后)" > "$REVIEW_DIR/ch01_v2_summary.md"
echo "" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo "**评审日期**: $(date +%Y-%m-%d)" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo "**修复内容**: P1-1逆向公式, P1-3动态防洪约束" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo "" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo "## Gemini评审结果" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo '```' >> "$REVIEW_DIR/ch01_v2_summary.md"
cat "$REVIEW_DIR/ch01_gemini_review_v2.txt" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo '```' >> "$REVIEW_DIR/ch01_v2_summary.md"
echo "" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo "## Codex评审结果" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo '```' >> "$REVIEW_DIR/ch01_v2_summary.md"
cat "$REVIEW_DIR/ch01_codex_review_v2.txt" >> "$REVIEW_DIR/ch01_v2_summary.md"
echo '```' >> "$REVIEW_DIR/ch01_v2_summary.md"

echo "✓ 综合报告生成: ch01_v2_summary.md"
echo ""
echo "========================================="
echo "评审完成! 请查看reviews目录下的文件"
echo "========================================="
