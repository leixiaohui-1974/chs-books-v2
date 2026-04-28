# T2b 卷核心参考文献标准库（2026-04-26 草案）

> **用途**：供 T2b 前六章第三轮精修统一调用。凡涉及工作代理、工具调用、多代理治理、平台责任链、human oversight、风险治理等核心命题时，应优先使用本库中的标准条目与一致表述。
>
> **适用原则**：本文件不是最终文后参考文献，而是卷级 canonical references。后续各章可按章内编号重排，但作者、题名、年份、出处、DOI/URL 与中英文标题译法应尽量保持一致。

---

## T2b-L1 — Agent 综述与能力边界

Xi, Z., Chen, W., Guo, X., et al. *The Rise and Potential of Large Language Model Based Agents: A Survey*. arXiv, 2024. DOI: 10.48550/arXiv.2404.11584.

**建议中文指称**：基于大语言模型的智能体综述 / LLM Agents 综述。

**主要用途**：支撑 T2b 第2章和第5章中关于单代理、多代理、规划、记忆、工具使用与协作模式的概念总览。

## T2b-L2 — Human Oversight 的正式法规依据

European Union. *Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act), Article 14: Human Oversight*. Official Journal of the European Union, 2024. Online text: https://artificialintelligenceact.eu/article/14/ .

**建议中文指称**：欧盟《人工智能法案》第14条：人工监督。

**主要用途**：支撑 T2b 第6章关于人工监督、override / reverse / stop、automation bias、风险相称监督与人工接管的制度化表述。

**正文优先引用要点**：

1. human oversight 应与风险、自治水平和使用情境相称；
2. 监督人应能理解系统能力与限制；
3. 监督人应能决定不使用、忽略、覆盖或逆转系统输出；
4. 监督人应能通过停止程序让系统进入安全状态。

## T2b-L3 — AI 风险治理母框架

Tabassi, E. *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*. NIST AI 100-1. National Institute of Standards and Technology, 2023. DOI: 10.6028/NIST.AI.100-1.

**建议中文指称**：NIST《人工智能风险管理框架（AI RMF 1.0）》。

**主要用途**：支撑 T2b 第6章关于平台治理、生命周期风险治理、可信与负责的 AI、组织级部署责任分配等内容。

**正文优先引用要点**：

1. AI RMF 面向设计、开发、部署与使用 AI 系统的组织；
2. 目标是管理 AI 的多重风险并促进 trustworthy and responsible AI；
3. 该框架具有跨行业、跨场景、可操作化特征，适合作为平台治理母框架。

## T2b-L4 — 复杂社会技术系统与认知工作分析

Bisantz, A. M., et al. *Cognitive Work Analysis in Complex Sociotechnical Systems: Concepts, Methodology and Use*（以当前可访问的人机协同与认知工作分析论文为准，后续需在最终文后参考文献中统一到实际采用篇目）.

**状态**：占位型 canonical 条目，需在下一轮完成实际最终篇名、卷期页核定。

**主要用途**：支撑 T2b 第3章和第6章关于复杂工作系统分析、监督负荷、人机协同接管与任务分配边界。

**说明**：本条已在来源笔记中存在，但尚未完成正式元数据统一；在正式入稿前必须完成替换，不能保持占位状态。

## T2b-L5 — 平台治理与责任链的卷内自有来源

雷晓辉团队内部书稿材料与当前项目支撑件（如 `ch06_t2b_evidence_card_20260426.md`、`ch06_t2b_source_notes_20260426.md`、`ch06_t2b_figure_tasks_and_provenance_20260426.md`）。

**状态**：内部/自制来源，不得与外部文献混同。

**主要用途**：仅用于说明本卷提出的平台治理框架、责任链结构、图表设计与自制案例边界；不能替代外部法规与学术依据。

---

## 推荐映射关系（按章节）

| 章节 | 建议优先 canonical refs | 备注 |
|---|---|---|
| ch01 | T2b-L1 | 作为卷入口综述来源 |
| ch02 | T2b-L1 | 支撑 agent 基本能力架构 |
| ch03 | T2b-L4 | 支撑认知负荷、解释与监督边界 |
| ch04 | T2b-L1, T2b-L5 | 工具调用、编排、责任留痕需兼顾外部与内部来源 |
| ch05 | T2b-L1, T2b-L5 | 多代理协同与平台状态传递 |
| ch06 | T2b-L2, T2b-L3, T2b-L4, T2b-L5 | 形成法规—治理—人机系统—平台自制框架的四层引用链 |

---

## 常见错误模式（当前应避免）

| 错误模式 | 风险 | 纠正方式 |
|---|---|---|
| 只在 source notes 出现来源，但正文未显式引用 | 读者无法追溯证据 | 在第三轮精修中把关键命题回填到正文引文 |
| 将内部平台框架当成外部文献引用 | 混淆外部依据与自创结构 | 明确标注“内部/自制来源” |
| 用弱网页文章替代法规与标准来源 | 论证权威性不足 | 优先使用 EU AI Act、NIST AI RMF 等正式文本 |
| human oversight 只写“人工参与” | 丢失制度细节 | 明确补入 override、reverse、stop、automation bias 等条款语义 |

---

## 第三轮精修待办

1. 将 T2b-L4 占位条目替换为已核定的人机协同/认知工作分析正式文献。
2. 为 ch02、ch05、ch06 回填至少 2—4 处正文显式引用。
3. 在卷末形成正式 `references_t2b_front_half.md` 或等效文后参考文献文件。
4. 将本标准库与各章 source notes 去重，并统一作者名、年份和题名译法。

---

## References

[1]: https://arxiv.org/abs/2404.11584 "The Rise and Potential of Large Language Model Based Agents: A Survey"
[2]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[3]: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10 "Artificial Intelligence Risk Management Framework (AI RMF 1.0) | NIST"
