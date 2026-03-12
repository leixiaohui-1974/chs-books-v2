#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三引擎协作评审与修改系统

功能:
1. Codex CLI: 控制理论技术评审
2. Gemini CLI: 水利工程专家评审
3. Claude: 综合分析与修改方案生成

使用方法:
    python three_engine_system.py --book reservoir-operation-optimization --chapter 01
    python three_engine_system.py --book all --chapter all  # 批量处理
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class ThreeEngineSystem:
    def __init__(self, base_dir="D:/cowork/教材/chs-books-v2/books"):
        self.base_dir = Path(base_dir)

    def run_codex_review(self, book_name, chapter_num):
        """运行Codex技术评审"""
        print(f"\n[Codex] 评审 {book_name}/ch{chapter_num}.md...")

        book_dir = self.base_dir / book_name
        chapter_file = book_dir / f"ch{chapter_num}.md"
        review_dir = book_dir / "reviews"
        review_dir.mkdir(exist_ok=True)

        output_file = review_dir / f"ch{chapter_num}_codex_review.txt"

        prompt = """请以控制理论专家的角度评审这一章节,重点关注:
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

每个问题请标注具体行号或段落位置。"""

        try:
            cmd = [
                "codex", "exec", prompt,
                "--skip-git-repo-check",
                "--cd", str(book_dir),
                "-o", str(output_file)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300
            )

            if result.returncode == 0:
                print(f"✓ Codex评审完成: {output_file}")
                return output_file
            else:
                print(f"✗ Codex评审失败: {result.stderr}")
                return None

        except Exception as e:
            print(f"✗ Codex评审异常: {str(e)}")
            return None

    def run_gemini_review(self, book_name, chapter_num):
        """运行Gemini水利专家评审"""
        print(f"\n[Gemini] 评审 {book_name}/ch{chapter_num}.md...")

        book_dir = self.base_dir / book_name
        chapter_file = book_dir / f"ch{chapter_num}.md"
        review_dir = book_dir / "reviews"
        review_dir.mkdir(exist_ok=True)

        output_file = review_dir / f"ch{chapter_num}_gemini_review.txt"

        prompt = """请以水利水电工程专家的角度评审这一章节,重点关注:
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

请用中文回复。"""

        try:
            # 读取章节内容
            with open(chapter_file, 'r', encoding='utf-8') as f:
                chapter_content = f.read()

            # 调用Gemini CLI
            cmd = ["gemini", "-p", prompt]

            result = subprocess.run(
                cmd,
                input=chapter_content,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300
            )

            if result.returncode == 0:
                # 保存评审结果
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                print(f"✓ Gemini评审完成: {output_file}")
                return output_file
            else:
                print(f"✗ Gemini评审失败: {result.stderr}")
                return None

        except Exception as e:
            print(f"✗ Gemini评审异常: {str(e)}")
            return None

    def generate_summary(self, book_name, chapter_num, codex_file, gemini_file):
        """生成评审汇总"""
        print(f"\n[Claude] 生成评审汇总...")

        book_dir = self.base_dir / book_name
        review_dir = book_dir / "reviews"
        summary_file = review_dir / f"ch{chapter_num}_summary.md"

        # 读取评审结果
        codex_content = ""
        gemini_content = ""

        if codex_file and codex_file.exists():
            with open(codex_file, 'r', encoding='utf-8') as f:
                codex_content = f.read()

        if gemini_file and gemini_file.exists():
            with open(gemini_file, 'r', encoding='utf-8') as f:
                gemini_content = f.read()

        # 生成汇总
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

1. ✓ Codex技术评审完成
2. ✓ Gemini水利专家评审完成
3. ⏳ Claude分析评审意见
4. ⏳ 生成修改方案
5. ⏳ 执行修改
6. ⏳ 验证修改结果

"""

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"✓ 评审汇总完成: {summary_file}")
        return summary_file

    def review_chapter(self, book_name, chapter_num):
        """评审单个章节"""
        print(f"\n{'='*60}")
        print(f"三引擎协作评审: {book_name}/ch{chapter_num}.md")
        print(f"{'='*60}")

        # 1. Codex评审
        codex_file = self.run_codex_review(book_name, chapter_num)

        # 2. Gemini评审
        gemini_file = self.run_gemini_review(book_name, chapter_num)

        # 3. 生成汇总
        summary_file = self.generate_summary(book_name, chapter_num, codex_file, gemini_file)

        print(f"\n{'='*60}")
        print(f"✓ 评审完成!")
        print(f"{'='*60}")
        print(f"\n生成的文件:")
        if codex_file:
            print(f"  1. Codex评审: {codex_file}")
        if gemini_file:
            print(f"  2. Gemini评审: {gemini_file}")
        if summary_file:
            print(f"  3. 评审汇总: {summary_file}")
        print(f"\n下一步: 请Claude分析评审意见并生成修改方案\n")

        return {
            'codex': codex_file,
            'gemini': gemini_file,
            'summary': summary_file
        }

    def batch_review(self, book_name=None):
        """批量评审"""
        books = []

        if book_name and book_name != "all":
            books = [book_name]
        else:
            # 获取所有书目
            books = [
                "reservoir-operation-optimization",
                "flood-forecasting-control",
                "dam-safety-monitoring",
                "river-sediment-dynamics",
                "inland-waterway-navigation",
                "ship-lock-automation",
                "water-energy-food-nexus",
                "digital-twin-river-basin",
                "ai-for-water-engineering",
            ]

        results = []

        for book in books:
            book_dir = self.base_dir / book
            if not book_dir.exists():
                continue

            # 获取所有章节
            chapters = sorted(book_dir.glob("ch*.md"))
            chapters = [f for f in chapters if not f.name.startswith('ch00')
                       and 'codex' not in f.name.lower()
                       and 'gemini' not in f.name.lower()]

            for chapter_file in chapters:
                chapter_num = chapter_file.stem.replace('ch', '')
                result = self.review_chapter(book, chapter_num)
                results.append({
                    'book': book,
                    'chapter': chapter_num,
                    'files': result
                })

        return results


def main():
    parser = argparse.ArgumentParser(description='三引擎协作评审系统')
    parser.add_argument('--book', required=True, help='书名或"all"')
    parser.add_argument('--chapter', required=True, help='章节号或"all"')

    args = parser.parse_args()

    system = ThreeEngineSystem()

    if args.chapter == "all":
        # 批量评审
        results = system.batch_review(args.book)
        print(f"\n批量评审完成! 共评审 {len(results)} 个章节")
    else:
        # 单章评审
        system.review_chapter(args.book, args.chapter)


if __name__ == "__main__":
    main()
