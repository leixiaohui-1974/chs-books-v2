#!/bin/bash
# ============================================================
# 三引擎协作评审脚本 (Claude + Codex + Gemini)
# 用法:
#   ./three_engine_review.sh ch01_final.md          # 评审单章
#   ./three_engine_review.sh all                     # 评审全部章节
#   ./three_engine_review.sh ch01_final.md --merge   # 仅合并已有评审
#   ./three_engine_review.sh ch01_final.md --fix     # 基于评审生成修复方案
# ============================================================

set -uo pipefail
# 注意：不使用 set -e，因为并行子进程失败不应终止整个脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$SCRIPT_DIR/reports/three_engine"
mkdir -p "$REPORT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ============================================================
# 评审提示词模板
# ============================================================

REVIEW_PROMPT_COMMON='你正在评审《水系统控制论：原理与架构》(T1-CN) 的一个章节。

评审维度（每项1-10分）：
1. **技术严谨性**：公式推导是否正确？符号是否与CHS体系一致（τ_d, A_s, τ_m等）？
2. **教学可读性**：是否有引导案例？概念是否循序渐进？读者能否跟上逻辑？
3. **CHS体系一致性**：是否正确引用八原理(P1-P8)？WNAL等级是否准确？与其他章节交叉引用是否正确？
4. **参考文献质量**：是否有僵尸引用（列出但未在正文引用）？自引率是否在15-25%范围？
5. **图表规范性**：图片路径是否正确（应为 ./H/fig_XX_YY_name.png）？图号是否与章号匹配？
6. **工程实用性**：案例数据是否真实可信？参数是否有工程依据？

输出格式要求：
```
## 评分
| 维度 | 分数 | 说明 |
|------|------|------|
| 技术严谨性 | X/10 | ... |
| 教学可读性 | X/10 | ... |
| CHS体系一致性 | X/10 | ... |
| 参考文献质量 | X/10 | ... |
| 图表规范性 | X/10 | ... |
| 工程实用性 | X/10 | ... |
| **综合** | **X/10** | |

## P0问题（必须立即修复）
- [ ] ...

## P1问题（重要但非阻塞）
- [ ] ...

## P2问题（建议改进）
- [ ] ...

## 亮点
- ...
```'

# Codex 特化：偏工程严谨性
CODEX_ROLE='你是一位资深水利工程CTO（Reviewer B），有20年SCADA系统和水利自动化经验。
重点关注：公式是否可实现、参数是否有工程依据、控制策略是否可落地、安全机制是否充分。
对任何"理论正确但工程不可行"的内容给出具体改进建议。'

# Gemini 特化：偏教学和交叉学科
GEMINI_ROLE='你是一位AI+水利交叉学科带头人（Reviewer C），Nature编委，关注创新性和教学效果。
重点关注：概念表述是否清晰、类比是否恰当、与AI/控制论前沿是否衔接、国际读者能否理解。
对任何"术语堆砌但缺乏直觉解释"的内容给出改写建议。'

# Claude 特化：偏理论严谨性
CLAUDE_ROLE='你是一位欧洲控制论教授（Reviewer A），擅长数学证明和理论体系构建。
重点关注：定理/引理的数学严谨性、符号一致性（以CHS P1a WRR论文为准）、传递函数推导、八原理映射的逻辑自洽性。
对任何公式错误或符号不一致给出精确修正。'

# ============================================================
# 核心函数
# ============================================================

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 获取章节编号
get_chapter_num() {
    local file="$1"
    echo "$file" | grep -oP 'ch\K\d+' || echo "00"
}

# 运行单个引擎评审
run_engine_review() {
    local engine="$1"    # claude / codex / gemini
    local chapter="$2"   # ch01_final.md
    local ch_num
    ch_num=$(get_chapter_num "$chapter")
    local outfile="$REPORT_DIR/ch${ch_num}_${engine}_review.md"
    local chapter_path="$SCRIPT_DIR/$chapter"

    if [[ ! -f "$chapter_path" ]]; then
        log_error "文件不存在: $chapter_path"
        return 1
    fi

    # 如果评审文件已存在且不为空，跳过（除非 --force）
    if [[ -f "$outfile" && -s "$outfile" && "${FORCE:-}" != "1" ]]; then
        log_warn "$engine 评审已存在: $outfile（跳过，用 --force 强制重新评审）"
        return 0
    fi

    local content
    content=$(cat "$chapter_path")
    local prompt role timestamp

    case "$engine" in
        claude)
            role="$CLAUDE_ROLE"
            ;;
        codex)
            role="$CODEX_ROLE"
            ;;
        gemini)
            role="$GEMINI_ROLE"
            ;;
        *)
            log_error "未知引擎: $engine"
            return 1
            ;;
    esac

    prompt="${role}

${REVIEW_PROMPT_COMMON}

以下是待评审章节内容：

${content}"

    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    log_info "[$timestamp] 启动 $engine 评审 $chapter ..."

    # 将 prompt 写入临时文件（避免命令行长度限制和特殊字符问题）
    local tmpfile
    tmpfile=$(mktemp)
    echo "$prompt" > "$tmpfile"

    case "$engine" in
        claude)
            # 取消 CLAUDECODE 环境变量以允许嵌套调用
            env -u CLAUDECODE claude -p --allowedTools "" \
                --max-budget-usd 1.0 \
                < "$tmpfile" \
                > "$outfile" 2>/dev/null || {
                log_error "Claude 评审失败: $chapter"
                rm -f "$tmpfile"
                return 1
            }
            ;;
        codex)
            codex exec - \
                < "$tmpfile" \
                > "$outfile" 2>/dev/null || {
                log_error "Codex 评审失败: $chapter"
                rm -f "$tmpfile"
                return 1
            }
            ;;
        gemini)
            gemini -p "" \
                < "$tmpfile" \
                > "$outfile" 2>/dev/null || {
                log_error "Gemini 评审失败: $chapter"
                rm -f "$tmpfile"
                return 1
            }
            ;;
    esac
    rm -f "$tmpfile"

    if [[ -s "$outfile" ]]; then
        log_ok "$engine 评审完成: $outfile"
    else
        log_error "$engine 评审输出为空: $outfile"
        rm -f "$outfile"
        return 1
    fi
}

# 三引擎并行评审单章
review_chapter() {
    local chapter="$1"
    local ch_num
    ch_num=$(get_chapter_num "$chapter")

    echo ""
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}  三引擎评审: 第${ch_num}章 ($chapter)${NC}"
    echo -e "${PURPLE}========================================${NC}"

    # 并行启动三个引擎
    local pids=()

    run_engine_review "claude" "$chapter" &
    pids+=($!)

    run_engine_review "codex" "$chapter" &
    pids+=($!)

    run_engine_review "gemini" "$chapter" &
    pids+=($!)

    # 等待所有引擎完成
    local failed=0
    for pid in "${pids[@]}"; do
        wait "$pid" || failed=$((failed + 1))
    done

    if [[ $failed -gt 0 ]]; then
        log_warn "$failed 个引擎评审失败"
    fi

    # 自动合并
    merge_reviews "$chapter"
}

# 合并三引擎评审结果
merge_reviews() {
    local chapter="$1"
    local ch_num
    ch_num=$(get_chapter_num "$chapter")
    local merged="$REPORT_DIR/ch${ch_num}_merged_review.md"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$merged" << HEADER
---
title: "第${ch_num}章 三引擎协作评审汇总"
chapter: ${chapter}
date: ${timestamp}
engines: [Claude (Reviewer A), Codex (Reviewer B), Gemini (Reviewer C)]
---

# 第${ch_num}章 三引擎协作评审汇总

> 生成时间: ${timestamp}
> 评审文件: ${chapter}

---

HEADER

    # 逐引擎追加
    for engine in claude codex gemini; do
        local review_file="$REPORT_DIR/ch${ch_num}_${engine}_review.md"
        local engine_label

        case "$engine" in
            claude) engine_label="Claude (Reviewer A — 理论严谨型)" ;;
            codex)  engine_label="Codex (Reviewer B — 工程实践型)" ;;
            gemini) engine_label="Gemini (Reviewer C — 学科交叉型)" ;;
        esac

        echo "## $engine_label" >> "$merged"
        echo "" >> "$merged"

        if [[ -f "$review_file" && -s "$review_file" ]]; then
            cat "$review_file" >> "$merged"
        else
            echo "> ⚠️ 该引擎评审未完成或为空" >> "$merged"
        fi

        echo "" >> "$merged"
        echo "---" >> "$merged"
        echo "" >> "$merged"
    done

    # 追加汇总统计区（占位，由后续 --fix 流程填充）
    cat >> "$merged" << 'FOOTER'
## 三引擎共识分析

> 以下由 Claude 主引擎基于三方评审自动生成

### P0 共识问题（至少2个引擎同时标记）

（待生成）

### 分歧点

（待生成）

### 修复优先级排序

（待生成）
FOOTER

    log_ok "评审汇总: $merged"
}

# 基于合并评审生成修复方案
generate_fix_plan() {
    local chapter="$1"
    local ch_num
    ch_num=$(get_chapter_num "$chapter")
    local merged="$REPORT_DIR/ch${ch_num}_merged_review.md"
    local fix_plan="$REPORT_DIR/ch${ch_num}_fix_plan.md"

    if [[ ! -f "$merged" ]]; then
        log_error "合并评审不存在: $merged（请先运行评审）"
        return 1
    fi

    log_info "生成第${ch_num}章修复方案 ..."

    local prompt="你是《水系统控制论》的主编雷晓辉教授的AI助手。

以下是第${ch_num}章的三引擎评审汇总报告。请分析三方评审意见，生成修复方案。

要求：
1. 找出三方共识的P0问题（至少2个引擎同时标记的严重问题）
2. 识别分歧点（一方认为有问题但其他方未提及）
3. 按修复优先级排序：P0 > P1 > P2
4. 对每个P0/P1问题，给出具体修复操作（精确到行号或段落）
5. 标注自引率计算结果和图表路径检查结果

输出格式：
\`\`\`markdown
# 第${ch_num}章修复方案

## 共识问题（P0，必须修复）
1. [问题描述] — 修复操作: [具体指令]

## 重要问题（P1，建议修复）
1. [问题描述] — 修复操作: [具体指令]

## 建议改进（P2，可选）
1. [问题描述]

## 统计
- 自引率: X%（目标15-25%）
- 图表路径检查: X/Y 正确
- 交叉引用检查: [结果]
\`\`\`

三引擎评审报告：

$(cat "$merged")"

    echo "$prompt" | env -u CLAUDECODE claude -p --allowedTools "" \
        --max-budget-usd 1.0 \
        > "$fix_plan" 2>/dev/null

    if [[ -s "$fix_plan" ]]; then
        log_ok "修复方案: $fix_plan"
    else
        log_error "修复方案生成失败"
    fi
}

# ============================================================
# 批量模式
# ============================================================

review_all() {
    local chapters=()
    for f in "$SCRIPT_DIR"/ch*_final.md; do
        [[ -f "$f" ]] && chapters+=("$(basename "$f")")
    done

    if [[ ${#chapters[@]} -eq 0 ]]; then
        log_error "未找到 ch*_final.md 文件"
        exit 1
    fi

    log_info "找到 ${#chapters[@]} 个章节，开始批量三引擎评审..."
    echo ""

    local total=${#chapters[@]}
    local current=0

    for chapter in "${chapters[@]}"; do
        ((current++))
        echo -e "${YELLOW}[$current/$total]${NC} 处理 $chapter"
        review_chapter "$chapter"
        echo ""
    done

    # 生成全书汇总
    generate_summary
}

# 全书汇总报告
generate_summary() {
    local summary="$REPORT_DIR/全书三引擎评审汇总.md"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$summary" << HEADER
---
title: "《水系统控制论》全书三引擎协作评审汇总"
date: ${timestamp}
---

# 全书三引擎协作评审汇总

> 生成时间: ${timestamp}

## 各章评审状态

| 章节 | Claude | Codex | Gemini | 合并 | 修复方案 |
|------|--------|-------|--------|------|----------|
HEADER

    for f in "$SCRIPT_DIR"/ch*_final.md; do
        [[ -f "$f" ]] || continue
        local ch
        ch=$(basename "$f")
        local ch_num
        ch_num=$(get_chapter_num "$ch")

        local claude_status="❌"
        local codex_status="❌"
        local gemini_status="❌"
        local merged_status="❌"
        local fix_status="❌"

        [[ -s "$REPORT_DIR/ch${ch_num}_claude_review.md" ]] && claude_status="✅"
        [[ -s "$REPORT_DIR/ch${ch_num}_codex_review.md" ]] && codex_status="✅"
        [[ -s "$REPORT_DIR/ch${ch_num}_gemini_review.md" ]] && gemini_status="✅"
        [[ -s "$REPORT_DIR/ch${ch_num}_merged_review.md" ]] && merged_status="✅"
        [[ -s "$REPORT_DIR/ch${ch_num}_fix_plan.md" ]] && fix_status="✅"

        echo "| 第${ch_num}章 | ${claude_status} | ${codex_status} | ${gemini_status} | ${merged_status} | ${fix_status} |" >> "$summary"
    done

    echo "" >> "$summary"
    echo "## 使用说明" >> "$summary"
    cat >> "$summary" << 'USAGE'

```bash
# 评审单章
./three_engine_review.sh ch01_final.md

# 评审全部
./three_engine_review.sh all

# 强制重新评审（覆盖已有结果）
FORCE=1 ./three_engine_review.sh ch01_final.md

# 仅合并已有评审
./three_engine_review.sh ch01_final.md --merge

# 生成修复方案
./three_engine_review.sh ch01_final.md --fix

# 全部章节生成修复方案
./three_engine_review.sh all --fix
```
USAGE

    log_ok "全书汇总: $summary"
}

# ============================================================
# 主入口
# ============================================================

main() {
    local target="${1:-}"
    local action="${2:-review}"  # review / --merge / --fix

    if [[ -z "$target" ]]; then
        echo "用法:"
        echo "  $0 <chapter.md>          评审单章"
        echo "  $0 all                    评审全部章节"
        echo "  $0 <chapter.md> --merge   仅合并已有评审"
        echo "  $0 <chapter.md> --fix     基于评审生成修复方案"
        echo "  $0 all --fix              全部章节生成修复方案"
        echo ""
        echo "环境变量:"
        echo "  FORCE=1                   强制重新评审（覆盖已有结果）"
        exit 0
    fi

    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════╗"
    echo "║   三引擎协作评审系统 v1.0                ║"
    echo "║   Claude × Codex × Gemini               ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"

    case "$action" in
        --merge)
            if [[ "$target" == "all" ]]; then
                for f in "$SCRIPT_DIR"/ch*_final.md; do
                    merge_reviews "$(basename "$f")"
                done
            else
                merge_reviews "$target"
            fi
            ;;
        --fix)
            if [[ "$target" == "all" ]]; then
                for f in "$SCRIPT_DIR"/ch*_final.md; do
                    generate_fix_plan "$(basename "$f")"
                done
            else
                generate_fix_plan "$target"
            fi
            ;;
        *)
            if [[ "$target" == "all" ]]; then
                review_all
            else
                review_chapter "$target"
            fi
            ;;
    esac

    echo ""
    log_ok "全部任务完成！评审报告目录: $REPORT_DIR"
}

main "$@"
