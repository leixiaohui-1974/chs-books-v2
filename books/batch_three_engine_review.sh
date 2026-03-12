#!/bin/bash
# 批量三引擎评审脚本
# 使用方法: bash batch_three_engine_review.sh <book_name>
# 示例: bash batch_three_engine_review.sh reservoir-operation-optimization

set -e

BOOK_NAME=$1
BASE_DIR="D:/cowork/教材/chs-books-v2/books"
BOOK_DIR="$BASE_DIR/$BOOK_NAME"

if [ -z "$BOOK_NAME" ]; then
    echo "使用方法: bash batch_three_engine_review.sh <book_name>"
    echo "示例: bash batch_three_engine_review.sh reservoir-operation-optimization"
    exit 1
fi

if [ ! -d "$BOOK_DIR" ]; then
    echo "错误: 书目录不存在: $BOOK_DIR"
    exit 1
fi

echo "=========================================="
echo "批量三引擎评审"
echo "书名: $BOOK_NAME"
echo "=========================================="

# 获取所有章节文件
cd "$BOOK_DIR"
CHAPTERS=$(ls ch[0-9][0-9].md 2>/dev/null | grep -v ch00 | sort)

if [ -z "$CHAPTERS" ]; then
    echo "错误: 未找到章节文件"
    exit 1
fi

TOTAL=$(echo "$CHAPTERS" | wc -l)
CURRENT=0

echo "找到 $TOTAL 个章节"
echo ""

for CHAPTER_FILE in $CHAPTERS; do
    CURRENT=$((CURRENT + 1))
    CHAPTER_NUM=$(echo "$CHAPTER_FILE" | sed 's/ch\([0-9][0-9]\).md/\1/')

    echo "[$CURRENT/$TOTAL] 评审 ch${CHAPTER_NUM}.md..."

    # 调用单章评审脚本
    cd "$BASE_DIR"
    bash three_engine_review.sh "$BOOK_NAME" "$CHAPTER_NUM"

    # 避免API限流
    if [ $CURRENT -lt $TOTAL ]; then
        echo "等待60秒避免API限流..."
        sleep 60
    fi

    echo ""
done

echo "=========================================="
echo "✓ 批量评审完成!"
echo "=========================================="
echo ""
echo "评审结果保存在: $BOOK_DIR/reviews/"
echo ""
echo "下一步:"
echo "1. 查看评审汇总: cat $BOOK_DIR/reviews/ch*_summary.md"
echo "2. 请Claude分析评审意见并生成修改方案"
echo ""
