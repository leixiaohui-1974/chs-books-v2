#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三引擎协作评审系统 (简化版)

使用方法:
    python three_engine_simple.py reservoir-operation-optimization 02
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_codex_review(book_name, chapter_num):
    """运行Codex评审"""
    print(f"\n[Codex] 评审 {book_name}/ch{chapter_num}.md...")

    base_dir = Path("D:/cowork/教材/chs-books-v2/books")
    book_dir = base_dir / book_name
    review_dir = book_dir / "reviews"
    review_dir.mkdir(exist_ok=True)

    output_file = review_dir / f"ch{chapter_num}_codex_review.txt"

    prompt = """请以控制理论专家的角度评审这一章节,重点关注:
1. 控制理论的应用是否准确
2. 优化算法描述的完整性
3. 动态规划推导的严谨性
4. 与现代控制理论的衔接
5. 技术细节的准确性(公式、符号、单位)

请给出:
- 高优先级问题(P1): 必须修复的技术错误
- 中优先级问题(P2): 建议改进的技术细节
- 低优先级问题(P3): 可选的优化建议"""

    # 使用Bash调用Codex
    cmd = f'cd "{book_dir}" && codex exec "{prompt}" --skip-git-repo-check --cd . -o "{output_file}"'

    print(f"执行命令: {cmd[:100]}...")
    ret = os.system(cmd)

    if ret == 0 and output_file.exists():
        print(f"[OK] Codex评审完成: {output_file}")
        return output_file
    else:
        print(f"[ERROR] Codex评审失败")
        return None


def run_gemini_review(book_name, chapter_num):
    """运行Gemini评审"""
    print(f"\n[Gemini] 评审 {book_name}/ch{chapter_num}.md...")

    base_dir = Path("D:/cowork/教材/chs-books-v2/books")
    book_dir = base_dir / book_name
    chapter_file = book_dir / f"ch{chapter_num}.md"
    review_dir = book_dir / "reviews"
    review_dir.mkdir(exist_ok=True)

    output_file = review_dir / f"ch{chapter_num}_gemini_review.txt"

    prompt = """请以水利水电工程专家的角度评审这一章节,重点关注:
1. 水利工程概念的准确性
2. 案例数据的真实性和合理性
3. 工程实践的可操作性
4. 术语使用的规范性

请给出:
- 工程可行性评分(1-10分)
- 案例真实性评分(1-10分)
- 主要问题列表
- 改进建议

请用中文回复。"""

    # 使用Bash调用Gemini
    cmd = f'cat "{chapter_file}" | gemini -p "{prompt}" > "{output_file}"'

    print(f"执行命令: {cmd[:100]}...")
    ret = os.system(cmd)

    if ret == 0 and output_file.exists():
        print(f"[OK] Gemini评审完成: {output_file}")
        return output_file
    else:
        print(f"[ERROR] Gemini评审失败")
        return None


def generate_summary(book_name, chapter_num, codex_file, gemini_file):
    """生成评审汇总"""
    print(f"\n[Claude] 生成评审汇总...")

    base_dir = Path("D:/cowork/教材/chs-books-v2/books")
    book_dir = base_dir / book_name
    review_dir = book_dir / "reviews"
    summary_file = review_dir / f"ch{chapter_num}_summary.md"

    codex_content = ""
    gemini_content = ""

    if codex_file and codex_file.exists():
        with open(codex_file, 'r', encoding='utf-8') as f:
            codex_content = f.read()

    if gemini_file and gemini_file.exists():
        with open(gemini_file, 'r', encoding='utf-8') as f:
            gemini_content = f.read()

    summary = f"""# ch{chapter_num} 三引擎评审汇总

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 章节: {book_name}/ch{chapter_num}.md

---

## 一、Codex评审 (控制理论专家)

{codex_content}

---

## 二、Gemini评审 (水利工程专家)

{gemini_content}

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

1. [OK] Codex技术评审完成
2. [OK] Gemini水利专家评审完成
3. [ ] Claude分析评审意见
4. [ ] 生成修改方案
5. [ ] 执行修改
6. [ ] 验证修改结果

"""

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"[OK] 评审汇总完成: {summary_file}")
    return summary_file


def main():
    if len(sys.argv) < 3:
        print("使用方法: python three_engine_simple.py <book_name> <chapter_num>")
        print("示例: python three_engine_simple.py reservoir-operation-optimization 02")
        sys.exit(1)

    book_name = sys.argv[1]
    chapter_num = sys.argv[2]

    print("="*60)
    print(f"三引擎协作评审: {book_name}/ch{chapter_num}.md")
    print("="*60)

    # 1. Codex评审
    codex_file = run_codex_review(book_name, chapter_num)

    # 2. Gemini评审
    gemini_file = run_gemini_review(book_name, chapter_num)

    # 3. 生成汇总
    summary_file = generate_summary(book_name, chapter_num, codex_file, gemini_file)

    print("\n" + "="*60)
    print("[OK] 评审完成!")
    print("="*60)
    print(f"\n生成的文件:")
    if codex_file:
        print(f"  1. Codex评审: {codex_file}")
    if gemini_file:
        print(f"  2. Gemini评审: {gemini_file}")
    if summary_file:
        print(f"  3. 评审汇总: {summary_file}")
    print(f"\n下一步: 请Claude分析评审意见并生成修改方案\n")


if __name__ == "__main__":
    main()
