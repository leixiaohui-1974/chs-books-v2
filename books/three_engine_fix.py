#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三引擎协作修改执行系统

功能:
1. 读取Codex和Gemini的评审意见
2. Claude分析并生成修改方案
3. 使用Codex/Gemini执行具体修改
4. 验证修改结果

使用方法:
    python three_engine_fix.py --book reservoir-operation-optimization --chapter 02
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class ThreeEngineFix:
    def __init__(self, base_dir="D:/cowork/教材/chs-books-v2/books"):
        self.base_dir = Path(base_dir)

    def read_reviews(self, book_name, chapter_num):
        """读取评审意见"""
        book_dir = self.base_dir / book_name
        review_dir = book_dir / "reviews"

        codex_file = review_dir / f"ch{chapter_num}_codex_review.txt"
        gemini_file = review_dir / f"ch{chapter_num}_gemini_review.txt"

        codex_review = ""
        gemini_review = ""

        if codex_file.exists():
            with open(codex_file, 'r', encoding='utf-8') as f:
                codex_review = f.read()

        if gemini_file.exists():
            with open(gemini_file, 'r', encoding='utf-8') as f:
                gemini_review = f.read()

        return codex_review, gemini_review

    def generate_fix_plan(self, book_name, chapter_num, codex_review, gemini_review):
        """生成修改方案 (由Claude完成)"""
        print(f"\n[Claude] 分析评审意见并生成修改方案...")

        # 这里返回一个模板,实际修改方案需要Claude在对话中生成
        plan_template = f"""# ch{chapter_num} 修改方案

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 书名: {book_name}

---

## 一、Codex评审问题汇总

{codex_review[:500]}...

## 二、Gemini评审问题汇总

{gemini_review[:500]}...

## 三、Claude综合分析

### 3.1 问题分类

**P0级问题** (必须立即修复):
1. 待Claude分析后填写

**P1级问题** (高优先级):
1. 待填写

**P2级问题** (中优先级):
1. 待填写

### 3.2 修改策略

#### 策略1: 技术准确性修复 (使用Codex)
- 问题:
- 修改方案:
- 执行引擎: Codex

#### 策略2: 工程实践优化 (使用Gemini)
- 问题:
- 修改方案:
- 执行引擎: Gemini

#### 策略3: 内容扩充 (使用Gemini)
- 问题:
- 修改方案:
- 执行引擎: Gemini

---

## 四、修改执行计划

| 序号 | 问题 | 修改方案 | 负责引擎 | 优先级 | 状态 |
|------|------|---------|---------|--------|------|
| 1 | 待填写 | 待填写 | Codex/Gemini | P0/P1/P2 | ⏳ |

---

## 五、验证清单

- [ ] 技术准确性验证
- [ ] 公式符号一致性检查
- [ ] 参考文献格式检查
- [ ] 代码可运行性验证
- [ ] CHS关联自然性检查

"""

        return plan_template

    def execute_fix_with_codex(self, book_name, chapter_num, fix_instruction):
        """使用Codex执行修改"""
        print(f"\n[Codex] 执行修改...")

        book_dir = self.base_dir / book_name
        chapter_file = book_dir / f"ch{chapter_num}.md"
        backup_file = book_dir / f"ch{chapter_num}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        # 备份原文件
        import shutil
        shutil.copy(chapter_file, backup_file)
        print(f"✓ 已备份原文件: {backup_file}")

        prompt = f"""请根据以下修改指令修改章节内容:

{fix_instruction}

要求:
1. 保持原有结构和格式
2. 只修改指定的问题
3. 确保修改后的内容技术准确
4. 保持参考文献格式规范
5. 输出完整的修改后的章节内容

请直接输出修改后的完整Markdown内容,不要添加任何解释。"""

        try:
            # 读取原文件
            with open(chapter_file, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 调用Codex
            cmd = ["codex", "exec", prompt, "--skip-git-repo-check", "--cd", str(book_dir)]

            result = subprocess.run(
                cmd,
                input=original_content,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300
            )

            if result.returncode == 0:
                # 保存修改后的内容
                modified_content = result.stdout

                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)

                print(f"✓ Codex修改完成")
                return True
            else:
                print(f"✗ Codex修改失败: {result.stderr}")
                # 恢复备份
                shutil.copy(backup_file, chapter_file)
                return False

        except Exception as e:
            print(f"✗ Codex修改异常: {str(e)}")
            # 恢复备份
            import shutil
            shutil.copy(backup_file, chapter_file)
            return False

    def execute_fix_with_gemini(self, book_name, chapter_num, fix_instruction):
        """使用Gemini执行修改"""
        print(f"\n[Gemini] 执行修改...")

        book_dir = self.base_dir / book_name
        chapter_file = book_dir / f"ch{chapter_num}.md"
        backup_file = book_dir / f"ch{chapter_num}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        # 备份原文件
        import shutil
        shutil.copy(chapter_file, backup_file)
        print(f"✓ 已备份原文件: {backup_file}")

        prompt = f"""请根据以下修改指令修改章节内容:

{fix_instruction}

要求:
1. 保持原有结构和格式
2. 只修改指定的问题
3. 确保修改后的内容符合水利工程实践
4. 保持参考文献格式规范
5. 输出完整的修改后的章节内容

请直接输出修改后的完整Markdown内容,不要添加任何解释。请用中文回复。"""

        try:
            # 读取原文件
            with open(chapter_file, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 调用Gemini
            cmd = ["gemini", "-p", prompt]

            result = subprocess.run(
                cmd,
                input=original_content,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300
            )

            if result.returncode == 0:
                # 保存修改后的内容
                modified_content = result.stdout

                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)

                print(f"✓ Gemini修改完成")
                return True
            else:
                print(f"✗ Gemini修改失败: {result.stderr}")
                # 恢复备份
                shutil.copy(backup_file, chapter_file)
                return False

        except Exception as e:
            print(f"✗ Gemini修改异常: {str(e)}")
            # 恢复备份
            import shutil
            shutil.copy(backup_file, chapter_file)
            return False

    def verify_fix(self, book_name, chapter_num):
        """验证修改结果"""
        print(f"\n[验证] 检查修改结果...")

        book_dir = self.base_dir / book_name
        chapter_file = book_dir / f"ch{chapter_num}.md"

        # 基本检查
        checks = {
            '文件存在': chapter_file.exists(),
            '文件非空': chapter_file.stat().st_size > 0 if chapter_file.exists() else False,
            '包含参考文献': False,
            '包含代码块': False,
            '包含CHS关联': False
        }

        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()

            checks['包含参考文献'] = '## 参考文献' in content
            checks['包含代码块'] = '```python' in content
            checks['包含CHS关联'] = '水系统控制论' in content or 'CHS' in content

        print("\n验证结果:")
        for check, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}")

        all_passed = all(checks.values())
        if all_passed:
            print("\n✓ 所有检查通过!")
        else:
            print("\n⚠️ 部分检查未通过,请人工审核")

        return all_passed


def main():
    parser = argparse.ArgumentParser(description='三引擎协作修改系统')
    parser.add_argument('--book', required=True, help='书名')
    parser.add_argument('--chapter', required=True, help='章节号')
    parser.add_argument('--engine', choices=['codex', 'gemini', 'auto'], default='auto',
                       help='执行修改的引擎')
    parser.add_argument('--instruction', help='修改指令文件路径')

    args = parser.parse_args()

    system = ThreeEngineFix()

    # 1. 读取评审意见
    codex_review, gemini_review = system.read_reviews(args.book, args.chapter)

    if not codex_review and not gemini_review:
        print("错误: 未找到评审意见,请先运行three_engine_system.py进行评审")
        sys.exit(1)

    # 2. 生成修改方案
    fix_plan = system.generate_fix_plan(args.book, args.chapter, codex_review, gemini_review)

    # 保存修改方案
    book_dir = system.base_dir / args.book
    review_dir = book_dir / "reviews"
    plan_file = review_dir / f"ch{args.chapter}_fix_plan.md"

    with open(plan_file, 'w', encoding='utf-8') as f:
        f.write(fix_plan)

    print(f"\n修改方案已生成: {plan_file}")
    print("\n请Claude分析评审意见并完善修改方案,然后使用--instruction参数执行修改")

    # 如果提供了修改指令,执行修改
    if args.instruction:
        with open(args.instruction, 'r', encoding='utf-8') as f:
            instruction = f.read()

        if args.engine == 'codex':
            success = system.execute_fix_with_codex(args.book, args.chapter, instruction)
        elif args.engine == 'gemini':
            success = system.execute_fix_with_gemini(args.book, args.chapter, instruction)
        else:
            # 自动选择
            print("\n自动模式: 先使用Codex修复技术问题,再使用Gemini优化工程实践")
            success = system.execute_fix_with_codex(args.book, args.chapter, instruction)

        if success:
            # 验证修改
            system.verify_fix(args.book, args.chapter)


if __name__ == "__main__":
    main()
