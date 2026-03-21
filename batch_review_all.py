"""批量评审脚本：扫描所有书稿章节，生成出版级评审提示词供外部引擎调用。"""

from __future__ import annotations
import argparse, logging, re, sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterator

ROOT_CHS = Path("Z:/research/chs-books-v2")
ROOT_HYDRO = Path("Z:/research/HydroBooks")
VALID_ENGINES = ("claude", "gpt", "gemini", "codex")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
logger = logging.getLogger(__name__)

@dataclass
class BookConfig:
    """单本书的配置信息。"""
    book_id: str
    display_name: str
    series: str
    glob_pattern: str
    src_dir: Path
    review_dir: Path
    level: str
    domain: str
    lang: str = "zh"
    extra_notes: str = ""

def _detect_pattern(book_dir: Path) -> str:
    """自动检测书目章节文件匹配模式。"""
    if list(book_dir.glob("ch*_final.md")):
        return "ch*_final.md"
    if list(book_dir.glob("ch*_draft.md")):
        return "ch*_draft.md"
    return "ch*.md"

def _build_registry() -> list[BookConfig]:
    """构建所有书目配置列表。"""
    configs: list[BookConfig] = []
    t_items = [
        ("T1-CN", "T1 中文版·水系统控制概论", "ch*_final.md",
         ROOT_CHS / "T1-CN", "graduate", "water-systems-control",
         "CHS 体系入门，应覆盖八原理与 WNAL 框架"),
        ("T2a", "T2a 水力学", "ch*_final.md",
         ROOT_CHS / "T2a", "graduate", "hydraulics",
         "重点检查明渠流、管道流公式推导与量纲一致性"),
        ("T2b", "T2b 水环境", "ch*_final.md",
         ROOT_CHS / "T2b", "graduate", "water-environment", ""),
        ("T2-CN", "T2 中文版·城市供水网络", "ch*_revised.md",
         ROOT_CHS / "T2-CN", "professional", "urban-water-distribution",
         "面向工程师；文件名含中文描述"),
        ("T3", "T3 工程数值方法", "ch*.md",
         ROOT_CHS / "T3-Engineering", "graduate", "numerical-methods",
         "重点检查数值稳定性分析与代码示例"),
        ("T4", "T4 数字孪生平台", "ch*_draft.md",
         ROOT_CHS / "T4-Platform", "graduate", "digital-twin",
         "草稿阶段，重点关注结构完整性与 P0 级缺失内容"),
        ("T5", "T5 水利智能化", "ch*_draft.md",
         ROOT_CHS / "T5-Intelligence", "graduate", "ai-for-water",
         "草稿阶段；检查 AI/ML 方法描述是否与最新文献一致"),
    ]
    for book_id, name, pattern, src, level, domain, notes in t_items:
        configs.append(BookConfig(
            book_id=book_id, display_name=name, series="CHS-T",
            glob_pattern=pattern, src_dir=src, review_dir=src / "reviews",
            level=level, domain=domain, extra_notes=notes,
        ))
    mc_src = ROOT_CHS / "ModernControl" / "md"
    configs.append(BookConfig(
        book_id="ModernControl", display_name="水系统现代控制理论",
        series="CHS-Graduate", glob_pattern="ch*.md", src_dir=mc_src,
        review_dir=ROOT_CHS / "ModernControl" / "reviews",
        level="graduate", domain="modern-control",
        extra_notes="重点检查状态空间、MPC、自适应控制、强化学习推导",
    ))
    books_root = ROOT_CHS / "books"
    if books_root.exists():
        for d in sorted(books_root.iterdir()):
            if not d.is_dir() or d.name.startswith(("_", ".")):
                continue
            configs.append(BookConfig(
                book_id=f"books/{d.name}",
                display_name=d.name.replace("-", " ").title(),
                series="CHS-Books", glob_pattern=_detect_pattern(d),
                src_dir=d, review_dir=d / "reviews",
                level="graduate", domain=d.name,
            ))
    hydro_root = ROOT_HYDRO / "books"
    hydro_en = {"hydromind-developer-guide", "hydromind-user-guide"}
    if hydro_root.exists():
        for d in sorted(hydro_root.iterdir()):
            if not d.is_dir() or d.name.startswith(("_", ".")):
                continue
            if not list(d.glob("ch*.md")):
                continue
            configs.append(BookConfig(
                book_id=f"HydroBooks/{d.name}",
                display_name=d.name.replace("-", " ").title(),
                series="HydroBooks", glob_pattern="ch*.md",
                src_dir=d, review_dir=d / "reviews",
                level="professional", domain=d.name,
                lang="en" if d.name in hydro_en else "zh",
            ))
    return configs

BOOK_REGISTRY: list[BookConfig] = _build_registry()
BOOK_INDEX: dict[str, BookConfig] = {b.book_id: b for b in BOOK_REGISTRY}

_EXCLUDE_TAGS = ("_codex_v", "_gemini_", "_gpt_", "_claude_", "_draft_v")

def extract_chapter_number(filename: str) -> str:
    """从文件名提取章节号，如 ch01_final.md -> 01。"""
    m = re.match(r"ch(\d+)", filename, re.IGNORECASE)
    return m.group(1) if m else "00"

def iter_chapters(book: BookConfig) -> Iterator[Path]:
    """按章节号顺序迭代书目中的主版本章节文件（排除中间文件）。"""
    if not book.src_dir.exists():
        return
    files = sorted(
        (f for f in book.src_dir.glob(book.glob_pattern)
         if not any(tag in f.stem.lower() for tag in _EXCLUDE_TAGS)),
        key=lambda p: extract_chapter_number(p.name),
    )
    yield from files

def get_reviewed_engines(review_dir: Path, chapter_num: str) -> list[str]:
    """返回该章节已完成评审的引擎列表。"""
    if not review_dir.exists():
        return []
    return [e for e in VALID_ENGINES
            if (review_dir / f"ch{chapter_num}_{e}_review.md").exists()]

def review_output_path(book: BookConfig, chapter_num: str, engine: str) -> Path:
    """返回评审结果文件的绝对路径。"""
    return book.review_dir / f"ch{chapter_num}_{engine}_review.md"

def prompt_tmp_path(book: BookConfig, chapter_num: str, engine: str) -> Path:
    """返回临时提示词文件的绝对路径（隐藏文件前缀）。"""
    return book.review_dir / f"._prompt_ch{chapter_num}_{engine}.txt"

_DOMAIN_NOTES: dict[str, str] = {
    "water-systems-control": (
        "本书属于 CHS 教材体系，请检查是否覆盖 CHS 八原理、WNAL 框架、"
        "物理 AI + 认知 AI 双引擎概念。"
    ),
    "hydraulics": (
        "重点验证明渠流（Manning、谢才公式）、管道流（Darcy-Weisbach）、"
        "水锤方程的推导与量纲一致性。"
    ),
    "water-environment": (
        "检查水质模型（BOD-DO、富营养化）参数单位；"
        "关注国标（GB）与 EPA 标准的引用规范。"
    ),
    "modern-control": (
        "深度检查状态空间建模、可控性/可观性证明、李雅普诺夫稳定性分析、"
        "MPC 滚动优化推导、强化学习收敛性讨论。"
    ),
    "numerical-methods": (
        "验证有限差分格式稳定性条件（CFL、von Neumann 分析）；"
        "检查示例代码边界条件处理与收敛性测试完整性。"
    ),
    "digital-twin": (
        "关注数字孪生五维框架完整定义；"
        "检查实时同步与数据融合方法的技术准确性。"
    ),
    "ai-for-water": (
        "检查 LSTM/GNN/Transformer 在水利场景的适用性论述；"
        "警惕泛化能力夸大、数据泄露问题未讨论等缺陷。"
    ),
    "urban-water-distribution": (
        "验证 Hazen-Williams 与 Darcy-Weisbach 管网水力模型；"
        "检查 EPANET/WaterGEMS 工具引用是否有具体参数说明。"
    ),
    "developer-guide": (
        "重点检查 API 接口描述准确性、代码示例可运行性、"
        "版本兼容性说明及错误处理示例完整性。"
    ),
}

_LEVEL_NOTES: dict[str, str] = {
    "graduate": (
        "本书定位为研究生教材，评审以学术严谨性为首要标准：\n"
        "- 要求公式推导完整，关键步骤不可跳过\n"
        "- 要求引用高质量期刊论文（SCI/EI，近五年文献 >=30%）\n"
        "- 习题应包含推导题、编程仿真题，难度达到研究生入学考试水平"
    ),
    "undergraduate": (
        "本书定位为本科生教材，评审侧重教学适用性：\n"
        "- 概念引入须有直觉解释（工程实例、类比）\n"
        "- 公式推导须详细，避免跳步\n"
        "- 习题应有充足例题与解答过程"
    ),
    "professional": (
        "本书定位为工程技术人员参考书，评审侧重实用性：\n"
        "- 工程案例须有完整参数、来源说明\n"
        "- 规范引用须对应现行版本（如 GB/T 标准年号）\n"
        "- 操作流程须清晰，可直接指导实践"
    ),
}

_ENGINE_INTRO: dict[str, str] = {
    "claude": "你是 Claude（Anthropic），擅长严谨的学术评审与中文技术写作",
    "gpt":    "你是 GPT-4o（OpenAI），擅长技术准确性核查与结构化分析",
    "gemini": "你是 Gemini（Google DeepMind），擅长多模态理解与跨文献核查",
    "codex":  "你是 Codex（OpenAI），擅长代码正确性验证与算法逻辑分析",
}

def _read_preview(chapter_path: Path, chars: int = 800) -> str:
    """读取章节前 chars 字符作为上下文预览。"""
    try:
        return chapter_path.read_text(encoding="utf-8", errors="replace")[:chars].strip()
    except OSError as exc:
        logger.warning(f"无法读取 {chapter_path}: {exc}")
        return "（文件读取失败）"

def _chapter_stats(text: str) -> dict[str, object]:
    """统计章节基本指标。"""
    return {
        "总行数": len(text.splitlines()),
        "总字符数": f"{len(text):,}",
        "图引用数": len(re.findall(r"图\s*\d+[\-\u2013]\d+|图\s*\d+", text)),
        "表引用数": len(re.findall(r"表\s*\d+[\-\u2013]\d+|表\s*\d+", text)),
        "块公式数": len(re.findall(
            r"\$\$[\s\S]+?\$\$|\\[[\s\S]+?\\]|\begin\{equation", text
        )),
        "行内公式数": len(re.findall(r"\$[^$\n]+\$", text)),
        "代码块数":   len(re.findall(r"```", text)) // 2,
        "参考文献数": len(re.findall(r"^\s*\[\d+\]", text, re.MULTILINE)),
        "二级标题数": len(re.findall(r"^##\s", text, re.MULTILINE)),
        "三级标题数": len(re.findall(r"^###\s", text, re.MULTILINE)),
    }

def _stats_table(stats: dict[str, object]) -> str:
    """将统计信息格式化为 Markdown 表格。"""
    rows = "".join(f"| {k} | {v} |\n" for k, v in stats.items())
    return (
        "\n**章节基本统计（自动扫描）**\n\n"
        "| 指标 | 数量 |\n|------|------|\n"
        + rows
    )

def _prompt_header(book: BookConfig, chapter_path: Path, engine: str, today: str) -> str:
    """构建提示词头部元信息块。"""
    ch_num = extract_chapter_number(chapter_path.name)
    intro = _ENGINE_INTRO.get(engine, "你是专业学术评审 AI")
    rpath = review_output_path(book, ch_num, engine)
    return (
        f"# 书稿评审任务\n\n"
        f"**评审引擎**: {engine.upper()}（{intro}）\n"
        f"**评审日期**: {today}\n"
        f"**书目 ID**: {book.book_id}\n"
        f"**书目名称**: {book.display_name}\n"
        f"**系列**: {book.series}\n"
        f"**章节文件**: {chapter_path.name}（第 {ch_num} 章）\n"
        f"**章节路径**: {chapter_path}\n"
        f"**输出路径**: {rpath}\n"
        f"**教材层级**: {book.level}  **领域**: {book.domain}  **语言**: {book.lang}\n"
    )

def _prompt_background(book: BookConfig) -> str:
    """构建评审背景说明块。"""
    level_note = _LEVEL_NOTES.get(book.level, _LEVEL_NOTES["graduate"])
    domain_note = _DOMAIN_NOTES.get(book.domain, "")
    parts = [
        "## 任务背景\n\n",
        "你正在为一本出版级中文学术教材进行同行评审，"
        "须达到**出版社技术编辑**的专业标准。\n",
        "发现的每个问题须给出**具体位置**（节标题或行号）、"
        "**问题描述**和**修改建议**。\n\n",
        f"{level_note}\n",
    ]
    if domain_note:
        parts.append(f"\n**领域专项要求**：{domain_note}\n")
    if book.extra_notes:
        parts.append(f"\n**额外说明**：{book.extra_notes}\n")
    return "".join(parts)

def _prompt_dimensions() -> str:
    """构建七维度评审框架文本。"""
    return (
        "## 评审框架（七个维度，出版级标准）\n\n"
        "对以下七个维度逐一评审，每个维度给出 **0-10 分**评分"
        "（0=完全不合格，10=出版就绪）。\n\n"
        "---\n\n"
        "### D1  技术准确性与逻辑连贯性（权重 25%）\n\n"
        "1. 概念定义是否精确、前后一致？是否存在混用或歧义？\n"
        "2. 公式推导步骤是否完整？是否有无根据跳步？\n"
        "3. 论证链条是否严密？因果关系是否清晰？\n"
        "4. 核心公式、参数是否与引用文献吻合？\n"
        "5. 同一符号在不同节中含义是否统一？\n"
        "6. 是否符合领域主流框架与国际标准？\n\n"
        "输出：列出所有技术错误（位置 | 错误 | 正确应为），给出 D1 评分。\n\n"
        "---\n\n"
        "### D2  图表完整性（权重 15%）\n\n"
        "1. 图引用编号是否连续（不跳号）？\n"
        "2. 哪些内容应有图但无图（系统架构图、算法流程图、实验结果对比图）？\n"
        "3. 正文引用与图注标题是否一致？\n"
        "4. 表格是否有表号、表题、数据来源说明？\n\n"
        "输出：列出缺失/问题图表（编号 | 问题 | 建议），给出 D2 评分。\n\n"
        "---\n\n"
        "### D3  公式正确性（权重 20%）\n\n"
        "1. LaTeX 语法：$...$、$$...$$、\begin{equation} 是否正确闭合？\n"
        "2. 公式编号是否连续，有无跳号/重复？\n"
        "3. 符号是否在首次出现时有定义？\n"
        "4. 等式两边量纲是否一致？单位是否标注？\n"
        "5. 核心公式是否与引用文献一致？\n"
        "6. 向量/矩阵记法是否统一（粗体或特定记号）？\n\n"
        "输出：逐一列出公式问题（位置 | 错误类型 | 正确写法），给出 D3 评分。\n\n"
        "---\n\n"
        "### D4  参考文献规范性（权重 15%）\n\n"
        "1. 是否符合 GB/T 7714-2015 格式？\n"
        "   期刊格式：作者. 题名[J]. 刊名, 年, 卷(期): 起止页.\n"
        "   著作格式：作者. 书名[M]. 版次. 出版地: 出版者, 年.\n"
        "2. 文献是否真实可查？警惕 AI 幻觉假文献。\n"
        "3. 英文期刊文献占比是否 >= 30%？\n"
        "4. 近五年（2020年后）文献占比是否 >= 25%？\n"
        "5. 领域重要文献是否有明显遗漏？\n"
        "6. 自引率是否 < 20%？\n\n"
        "输出：格式错误+疑似假文献列表；统计（总/中文/英文/近五年/自引）；给出 D4 评分。\n\n"
        "---\n\n"
        "### D5  编号连续性（权重 10%）\n\n"
        "1. 章节编号 x.y.z 是否连续、不跳号、不重复？\n"
        "2. 图编号、表编号、公式编号是否全章连续？\n"
        "3. 正文交叉引用与实际编号是否一致？\n\n"
        "输出：列出所有编号问题，给出 D5 评分。\n\n"
        "---\n\n"
        "### D6  教材体例（权重 10%）\n\n"
        "章首：[ ] 学习目标（3-5 条可量化成果）  [ ] 知识体系图（建议有）\n"
        "正文：[ ] 定义/定理高亮框  [ ] 例题（>=2 题含完整解答）  [ ] 工程案例（>=1 个）\n"
        "章末：[ ] 本章小结（200-500 字）  [ ] 关键术语（中英对照）\n"
        "      [ ] 习题（思考题>=3，计算/推导题>=3，编程/仿真题>=1）  [ ] 拓展阅读\n\n"
        "输出：逐项列出缺失要素及对教学效果的影响，给出 D6 评分。\n\n"
        "---\n\n"
        "### D7  代码示例可运行性（权重 5%）\n\n"
        "1. Python/MATLAB 语法是否正确？\n"
        "2. 是否有完整 import 语句并注明库版本？\n"
        "3. 代码变量名与正文公式符号是否对应？\n"
        "4. 是否给出具体输入数据使代码可直接运行？\n"
        "5. 是否给出预期输出？关键步骤是否有注释？\n\n"
        "若无代码块，标注 N/A 并不计入加权。给出 D7 评分。\n"
    )

def _prompt_output_template(
    book: BookConfig, chapter_path: Path, engine: str, today: str
) -> str:
    """构建要求 AI 输出的 Markdown 报告模板说明。"""
    ch_num = extract_chapter_number(chapter_path.name)
    rpath = review_output_path(book, ch_num, engine)
    lines = [
        f"## 输出格式要求（严格遵守）\n",
        f"将评审报告保存到：`{rpath}`\n\n",
        "报告结构如下：\n\n",
        "```\n",
        f"# 第 {ch_num} 章 [章节标题] — {engine.upper()} 评审报告\n\n",
        f"**评审日期**: {today}  **书目**: {book.display_name}  **引擎**: {engine.upper()}\n\n",
        "---\n\n",
        "## 综合评分: X.X/10\n\n",
        "| 维度 | 权重 | 得分 | 说明 |\n",
        "|------|------|------|------|\n",
        "| D1 技术准确性与逻辑连贯性 | 25% | X/10 | ... |\n",
        "| D2 图表完整性 | 15% | X/10 | ... |\n",
        "| D3 公式正确性 | 20% | X/10 | ... |\n",
        "| D4 参考文献规范性 | 15% | X/10 | ... |\n",
        "| D5 编号连续性 | 10% | X/10 | ... |\n",
        "| D6 教材体例 | 10% | X/10 | ... |\n",
        "| D7 代码示例可运行性 | 5% | X/10 | ... |\n",
        "| **加权综合** | 100% | **X.X/10** | |\n\n",
        "---\n\n",
        "## P0 级问题（致命缺陷，出版前必须修正）\n\n",
        "### P0-1: [问题标题]\n",
        "- **位置**: [节标题 / 行号]\n",
        "- **问题**: [详细描述]\n",
        "- **修改建议**: [具体建议]\n\n",
        "## P1 级问题（重要，定稿前修改）\n\n[P1-1 及以下...]\n\n",
        "## P2 级问题（建议改进，下版修订）\n\n[P2-1 及以下...]\n\n",
        "## 各维度详细评审\n\n",
        "### D1 技术准确性与逻辑连贯性（X/10）\n[详细内容]\n\n",
        "...（D2-D7 同结构）\n\n",
        "## 修改优先级清单\n\n",
        "| 优先级 | 问题编号 | 简要描述 | 预计工作量 |\n",
        "|--------|----------|----------|------------|\n",
        "| P0 | P0-1 | ... | 大/中/小 |\n\n",
        "## 总体评价\n\n",
        "[2-4 段：主要贡献、主要问题、修改方向、是否可进入下一审校环节]\n",
        "```\n\n",
        "注意事项：\n",
        "- 评审须基于实际章节内容，不得凭空编造问题\n",
        "- 若某维度无内容（如无代码），D7 标注 N/A 并不计入加权\n",
        "- 加权综合分须按权重严格计算\n",
        "- 所有问题定位须精确到节标题或行号区间\n",
        "- 若章节全文未在本提示中提供，请要求用户提供完整文件后再开始\n",
    ]
    return "".join(lines)


def build_review_prompt(book: BookConfig, chapter_path: Path, engine: str) -> str:
    """构建完整的出版级评审提示词。"""
    today = date.today().isoformat()
    preview = _read_preview(chapter_path)
    full_text = ""
    try:
        full_text = chapter_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    stats_block = _stats_table(_chapter_stats(full_text)) if full_text else ""
    sections = [
        _prompt_header(book, chapter_path, engine, today),
        "---",
        _prompt_background(book),
        "---",
        f"## 章节内容预览（前 800 字）\n\n```\n{preview}\n```\n{stats_block}",
        "---",
        _prompt_dimensions(),
        "---",
        _prompt_output_template(book, chapter_path, engine, today),
    ]
    return "\n\n".join(sections)

def cmd_list(args: argparse.Namespace) -> None:
    """列出所有（或指定书目的）章节及评审状态。"""
    books = _filter_books(args)
    total, reviewed = 0, 0
    for book in books:
        chapters = list(iter_chapters(book))
        if not chapters:
            continue
        print(f"\n[{book.book_id}]  {book.display_name}  ({book.level} | {book.domain})")
        for ch_path in chapters:
            ch_num = extract_chapter_number(ch_path.name)
            done = get_reviewed_engines(book.review_dir, ch_num)
            done_str = ",".join(done)
            status = f"[已评审: {done_str}]" if done else "[未评审]"
            print(f"  ch{ch_num}  {ch_path.name}  {status}")
            total += 1
            if done:
                reviewed += 1
    print(f"\n总计: {total} 章节，已评审: {reviewed}，待评审: {total - reviewed}")


def cmd_status(args: argparse.Namespace) -> None:
    """显示各引擎评审覆盖率统计。"""
    counts: dict[str, dict[str, int]] = {e: {"done": 0, "total": 0} for e in VALID_ENGINES}
    grand_total, grand_done = 0, 0
    for book in BOOK_REGISTRY:
        for ch_path in iter_chapters(book):
            grand_total += 1
            ch_num = extract_chapter_number(ch_path.name)
            done = get_reviewed_engines(book.review_dir, ch_num)
            if done:
                grand_done += 1
            for e in VALID_ENGINES:
                counts[e]["total"] += 1
                if e in done:
                    counts[e]["done"] += 1
    sep = "=" * 52
    print(f"\n{sep}")
    print(f"  评审覆盖率统计（总章节: {grand_total}）")
    print(sep)
    for eng, cnt in counts.items():
        d = cnt["done"]
        t = cnt["total"]
        pct = d / t * 100 if t else 0
        bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
        print(f"  {eng:8s}  [{bar}] {pct:5.1f}%  ({d}/{t})")
    print(sep)
    pct_total = grand_done / grand_total * 100 if grand_total else 0
    print(f"  任意引擎已评审: {grand_done}/{grand_total}  ({pct_total:.1f}%)")


def _chapters_to_process(
    book: BookConfig, chapter_arg: str | None, engine: str, force: bool,
) -> list[tuple[BookConfig, Path]]:
    """筛选需要处理的章节列表。"""
    result: list[tuple[BookConfig, Path]] = []
    for ch_path in iter_chapters(book):
        ch_num = extract_chapter_number(ch_path.name)
        if chapter_arg:
            normalized = re.sub(r"^ch", "", chapter_arg, flags=re.IGNORECASE).zfill(2)
            if ch_num != normalized:
                continue
        if review_output_path(book, ch_num, engine).exists() and not force:
            logger.info(f"跳过（已评审）: ch{ch_num} [{book.book_id}]")
            continue
        result.append((book, ch_path))
    return result


def _write_prompt(book: BookConfig, ch_path: Path, engine: str, dry_run: bool) -> None:
    """生成并写入（或打印）单章提示词。"""
    ch_num = extract_chapter_number(ch_path.name)
    prompt = build_review_prompt(book, ch_path, engine)
    if dry_run:
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"[DRY-RUN] {book.book_id} / ch{ch_num} / {engine}")
        print(sep)
        print(prompt[:3000])
        print(f"\n... [提示词共 {len(prompt)} 字符]")
    else:
        book.review_dir.mkdir(parents=True, exist_ok=True)
        tmp = prompt_tmp_path(book, ch_num, engine)
        tmp.write_text(prompt, encoding="utf-8")
        print(str(tmp.resolve()))
        logger.info(f"已写入: {tmp}")


def cmd_generate(args: argparse.Namespace) -> None:
    """生成指定章节（或书目全部章节）的评审提示词。"""
    engine = args.engine or "claude"
    items: list[tuple[BookConfig, Path]] = []
    for book in _filter_books(args):
        items.extend(_chapters_to_process(book, args.chapter, engine, args.force))
    if not items:
        print("没有待处理的章节（使用 --force 覆盖，或检查 --book/--chapter 参数）")
        return
    for book, ch_path in items:
        _write_prompt(book, ch_path, engine, args.dry_run)


def cmd_all(args: argparse.Namespace) -> None:
    """批量对所有未评审章节生成提示词。"""
    engine = args.engine or "claude"
    generated = 0
    for book in BOOK_REGISTRY:
        for book_, ch_path in _chapters_to_process(book, None, engine, args.force):
            _write_prompt(book_, ch_path, engine, args.dry_run)
            generated += 1
    logger.info(f"批量完成：共生成 {generated} 个提示词")


def _filter_books(args: argparse.Namespace) -> list[BookConfig]:
    """根据 --book 参数过滤书目。"""
    book_arg: str | None = getattr(args, "book", None)
    if not book_arg:
        return BOOK_REGISTRY
    if book_arg in BOOK_INDEX:
        return [BOOK_INDEX[book_arg]]
    matches = [b for b in BOOK_REGISTRY if book_arg.lower() in b.book_id.lower()]
    if not matches:
        logger.error(f"未找到书目 {book_arg!r}。使用 --list-books 查看所有书目 ID。")
        sys.exit(1)
    if len(matches) > 1:
        logger.warning(f"模糊匹配到多个书目: {[b.book_id for b in matches]}，将全部处理")
    return matches

def build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器。"""
    p = argparse.ArgumentParser(
        prog="batch_review_all.py",
        description="批量书稿评审脚本：扫描 CHS/HydroBooks 章节，生成出版级评审提示词。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用示例:\n"
            "  python batch_review_all.py                         # 列出所有待评审章节\n"
            "  python batch_review_all.py --status                # 覆盖率统计\n"
            "  python batch_review_all.py --list-books            # 列出所有书目 ID\n"
            "  python batch_review_all.py --book T1-CN            # 列出 T1-CN 章节\n"
            "  python batch_review_all.py --book T1-CN --chapter ch01 --engine claude\n"
            "  python batch_review_all.py --book T1-CN --chapter ch01 --dry-run\n"
            "  python batch_review_all.py --all --engine gpt      # 批量生成所有未评审章节\n"
            "  python batch_review_all.py --all --engine gemini --force\n"
        ),
    )
    p.add_argument("--book",    metavar="BOOK_ID", help="书目 ID（支持模糊匹配）")
    p.add_argument("--chapter", metavar="CHAPTER", help="章节，如 ch01 或 01")
    p.add_argument(
        "--engine", metavar="ENGINE", choices=VALID_ENGINES, default="claude",
        help=f"评审引擎 {list(VALID_ENGINES)}（默认: claude）",
    )
    p.add_argument("--all",        action="store_true", help="批量处理所有未评审章节")
    p.add_argument("--status",     action="store_true", help="显示评审覆盖率统计")
    p.add_argument("--force",      action="store_true", help="强制覆盖已有提示词/评审")
    p.add_argument("--dry-run",    action="store_true", help="打印提示词内容，不写文件")
    p.add_argument("--list-books", action="store_true", help="列出所有已注册书目 ID")
    p.add_argument("--verbose", "-v", action="store_true", help="输出详细日志")
    return p


def main() -> None:
    """主入口。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list_books:
        print(f"已注册书目（共 {len(BOOK_REGISTRY)} 本）:\n")
        for book in BOOK_REGISTRY:
            n = sum(1 for _ in iter_chapters(book))
            print(f"  {book.book_id:<48s}  {book.display_name}  ({n} 章)")
        return

    if args.status:
        cmd_status(args)
        return

    if args.all:
        cmd_all(args)
        return

    if args.chapter:
        cmd_generate(args)
        return

    cmd_list(args)


if __name__ == "__main__":
    main()
