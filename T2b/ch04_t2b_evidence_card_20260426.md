# 章节证据卡

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 章节编号 | T2b 第4章 |
| 章节标题 | 从认知解释到任务编排：Skill、工具链与工作流闭环 |
| 所属卷册 | T2b《从控制到认知：水系统运行智能的方法链与工作代理》 |
| 目标读者 | 平台架构师、运行智能系统设计者、水利数字化团队、研究生 |
| 与前后章节关系 | 本章承接第3章对解释链与快慢工作流的讨论，把认知能力进一步推进为任务编排、工具调用与工作代理；后续第5章进入多代理协同，第6章进入授权与接管治理。 |

## 2. 核心命题

| 序号 | 核心命题 | 命题类型 | 预期证据等级 | 当前状态 |
|---|---|---|---|---|
| 1 | 运行问题天然是多步问题，认知解释若不能进入任务编排，就无法形成可工作的闭环。 | 方法/工程 | Tier 2-3 | 待补 |
| 2 | 工具、Skill、工作流与工作代理并非同义词，而是从执行单元到高层组织体的分层结构。 | 定义/架构 | Tier 2-3 | 待补 |
| 3 | 高质量的任务编排必须显式包含意图识别、子任务分解、证据绑定、工具调用、异常回退与结果留痕。 | 工程/治理 | Tier 2-3 | 待补 |
| 4 | Skill 的价值不在于包装工具，而在于将经验性工作步骤、约束条件与门禁接口模板化。 | 方法/工程 | Tier 2-3 | 待补 |
| 5 | 工作流闭环的核心不只是自动化程度，而是责任能否被追踪、回退能否被执行、留痕能否支持复盘。 | 治理/工程 | Tier 1-2 | 待补 |

## 3. 必引经典文献

| 序号 | 文献 | 作用 | 是否已纳入 |
|---|---|---|---|
| 1 | Masterman et al., *The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey* | 支撑 planning、execution、reflection 与单/多代理组织结构 | 是 |
| 2 | Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models* | 支撑 reasoning 与 acting 交替的闭环视角 | 是 |
| 3 | Schick et al., *Toolformer: Language Models Can Teach Themselves to Use Tools* | 支撑工具调用是可学习、可组织的能力，而非外挂噱头 | 否 |
| 4 | NIST AI RMF / EU AI Act Article 14 | 支撑高风险 AI 工作流中的监督、覆盖、停止与日志治理 | 是 |
| 5 | Naikar et al., *Designing human-AI systems for complex settings* | 支撑工作流必须服务分布式团队与复杂社会技术系统 | 是 |

## 4. 证据来源计划

| 章节小节 | 关键论断 | 需要的来源类型 | 候选来源 | 风险备注 |
|---|---|---|---|---|
| 4.1 为什么解释之后必须进入任务编排 | 运行问题天然是多步、多角色、多工具的问题 | 代理综述/复杂工作系统来源 | Masterman et al.; Naikar et al. | 需避免把工作流写成通用办公自动化套路 |
| 4.2 Skill、工具、工作流与工作代理的层级关系 | 这些概念是分层架构，不可混写 | 代理架构论文/工具调用论文/内部平台框架 | Masterman et al.; Toolformer；内部平台设计文档 | Skill 的定义有较强作者归纳色彩，需明确原创部分 |
| 4.3 完整任务编排链 | 编排链至少包括意图识别、分解、证据绑定、工具调用、异常回退、结果留痕 | 工作流论文/治理框架/内部编排规范 | ReAct；NIST AI RMF；内部工作流文档 | 需把“留痕”从普通日志区分为责任留痕 |
| 4.4 Skill 调用链风险 | 风险来自链条结构与授权接口，而非仅来自单模型错误 | 风险治理框架/代理综述/内部复盘案例 | NIST AI RMF；EU AI Act；Masterman et al. | 需补强风险分类的外部锚点 |
| 4.5 本章收口 | 闭环能力的核心是责任、回退和复盘可执行 | 风险治理/复杂工作系统来源 | NIST AI RMF；Naikar et al. | 需与第5-6章协同、授权术语统一 |

## 5. 图表公式计划

| 元素编号 | 类型 | 主题 | 来源状态 | 预期来源/说明 |
|---|---|---|---|---|
| Fig-1 | 图 | 工具—Skill—工作流—工作代理四层结构图 | 自制 | 作为本章核心总图，需明确层级边界与接口 |
| Fig-2 | 图 | 完整任务编排链流程图 | 自制 | 应突出证据绑定、异常回退和结果留痕三个关键节点 |
| Tab-1 | 表 | 各层实体的输入、输出、责任与门禁对照表 | 汇编 | 依据正文提炼，便于与后续多代理协同章节接口 |
| Box-1 | 案例框 | “会解释但不会收口”的认知系统案例 | 自制/待核 | 强调没有编排就没有闭环 |
| Fig-3 | 图 | Skill 调用链四类风险定位图 | 自制 | 用于第三轮精修时强化风险可视化 |

## 6. 证据缺口

| 序号 | 问题 | 影响范围 | 解决动作 |
|---|---|---|---|
| 1 | Skill 的定义和边界目前主要来自章节内部语言，尚需更多外部代理/工具调用文献支撑 | 4.2 | 补入 Toolformer 或其他 tool-use 论文作为锚点 |
| 2 | 任务编排链中的“证据绑定”“结果留痕”还缺规范性来源支撑 | 4.3 | 补引 NIST AI RMF 与日志/治理要求文本 |
| 3 | 风险分类目前仍偏作者归纳，外部桥接不足 | 4.4 | 在来源笔记中补入代理失效/脆弱性相关来源 |
| 4 | 四层结构图和编排链流程图尚未正式定稿，将影响第5章与第6章接口理解 | 全章图表 | 在图表治理文件中补绘图约束和跨章术语一致性要求 |

## 7. 审核结论

> 本章已形成较强的工程主线，能够把认知能力从“会解释”推进到“能组织工作”。当前最关键的补强方向有二：其一，是通过 Toolformer 等来源补强 Skill/工具调用的外部方法锚点；其二，是通过治理规范把证据绑定、异常回退、结果留痕与责任闭环写得更硬。

## 8. 第三轮精修前置建议

第三轮精修时，本章应优先完成三项工作。第一，把四层结构图和完整任务编排链流程图稳定下来，因为它们会成为第5章与第6章的接口底图。第二，把“结果留痕”统一改写为“责任留痕与复盘留痕”，以避免降格为普通日志。第三，为 Skill 的定义增加更明确的外部论文桥接，降低章节完全依赖内部平台语汇的风险。

## References

[1]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[2]: https://openreview.net/forum?id=WE_vluYUL-X "ReAct: Synergizing Reasoning and Acting in Language Models"
[3]: https://arxiv.org/abs/2302.04761 "Language Models Can Teach Themselves to Use Tools"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[5]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[6]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
