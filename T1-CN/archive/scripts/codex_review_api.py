#!/usr/bin/env python
"""
Codex 评审 API 调用脚本（使用 OpenAI Responses API）
用法: python codex_review_api.py <chapter_file> <output_file>
"""
import sys
import os
from openai import OpenAI

API_KEY = "sk-a7f21d06c28c0affa5f75b920f639733b7de77800776065be80ffaaaf3a49139"
BASE_URL = "https://aicode.cat/v1/"
MODEL = "gpt-5.4"

CODEX_ROLE = """你是一位资深水利工程CTO（Reviewer B），有20年SCADA系统和水利自动化经验。
重点关注：公式是否可实现、参数是否有工程依据、控制策略是否可落地、安全机制是否充分。
对任何"理论正确但工程不可行"的内容给出具体改进建议。"""

REVIEW_PROMPT = """评审维度（每项1-10分）：
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
```"""


def review_chapter(chapter_path: str, output_path: str):
    with open(chapter_path, "r", encoding="utf-8") as f:
        content = f.read()

    prompt = f"{CODEX_ROLE}\n\n{REVIEW_PROMPT}\n\n以下是待评审章节内容：\n\n{content}"

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print(f"[Codex API] 正在评审 {os.path.basename(chapter_path)} ...", file=sys.stderr)

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    # 提取文本输出
    result_text = ""
    for item in response.output:
        if item.type == "message":
            for content_block in item.content:
                if content_block.type == "output_text":
                    result_text += content_block.text

    if not result_text:
        print(f"[Codex API] 警告：响应为空", file=sys.stderr)
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result_text)

    print(f"[Codex API] 完成: {output_path} ({len(result_text)} 字符)", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"用法: python {sys.argv[0]} <chapter.md> <output.md>")
        sys.exit(1)

    review_chapter(sys.argv[1], sys.argv[2])
