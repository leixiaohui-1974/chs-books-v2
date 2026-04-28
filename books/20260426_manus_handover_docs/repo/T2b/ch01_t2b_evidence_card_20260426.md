# 章节证据卡

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 章节编号 | T2b 第1章 |
| 章节标题 | 从控制到认知：为什么水系统运行智能需要第二条主线 |
| 所属卷册 | T2b《从控制到认知：水系统运行智能的方法链与工作代理》 |
| 目标读者 | 水利工程师、运行管理者、研究生、平台架构设计者 |
| 与前后章节关系 | 本章作为 T2b 卷导论章，负责解释为什么在 T2a 的物理 AI 主线之外，还必须建立认知主线；第2章起进一步把机器学习、解释、编排、协同与治理逐章展开。 |

## 2. 核心命题

| 序号 | 核心命题 | 命题类型 | 预期证据等级 | 当前状态 |
|---|---|---|---|---|
| 1 | 水系统运行智能若只停留在控制与优化层，会在解释、协同、规程理解和责任组织方面暴露系统性缺口。 | 定义/结构 | Tier 2-3 | 待补 |
| 2 | T2b 的认知主线不是替代 T2a 的物理 AI 引擎，而是为其提供解释、编排、协同与治理层能力。 | 架构/方法 | Tier 2-3 | 待补 |
| 3 | 运行智能的升级不只是模型升级，而是工作世界组织方式的升级。 | 理论/工程 | Tier 2-3 | 待补 |
| 4 | 认知系统一旦进入运行平台，就必须同时面对对象边界、任务边界与责任边界。 | 工程/治理 | Tier 2-3 | 待补 |
| 5 | 前半卷的真正目标，是为后续方法链建立从对象、解释、编排、协同到授权治理的连续结构。 | 结构 | Tier 3 | 待补 |

## 3. 必引经典文献

| 序号 | 文献 | 作用 | 是否已纳入 |
|---|---|---|---|
| 1 | Masterman et al., *The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey* | 作为 agentic systems、planning、tool calling 与单/多代理的总锚点 | 是 |
| 2 | Naikar et al., *Designing human-AI systems for complex settings* | 作为复杂工作系统、人机协同与认知工作分析的总锚点 | 是 |
| 3 | Wiener, *Cybernetics* | 作为控制论底座与 T2a/T2b 分工的历史锚点 | 否 |
| 4 | NIST AI RMF 1.0 | 作为风险治理与监督结构的前置锚点 | 是 |
| 5 | EU AI Act Article 14 | 作为 human oversight 与高风险系统边界设计的规范锚点 | 是 |

## 4. 证据来源计划

| 章节小节 | 关键论断 | 需要的来源类型 | 候选来源 | 风险备注 |
|---|---|---|---|---|
| 1.1 为什么需要第二条主线 | 控制与优化之外仍存在解释、协同、规程与责任缺口 | agent 综述/复杂工作系统来源/控制论经典 | Masterman et al.; Naikar et al.; Wiener | 需避免简单贬低控制主线 |
| 1.2 T2a 与 T2b 的关系 | 物理引擎与认知引擎是分工而非替代 | 控制论/架构综述/本书内部结构 | Wiener；Masterman et al. | 需明确哪些表述是本书结构设计 |
| 1.3 运行智能升级 | 升级发生在工作世界组织而非单一模型性能 | 复杂工作系统来源/治理框架 | Naikar et al.; NIST AI RMF | 需补强“工作世界”概念桥接 |
| 1.4 前半卷结构预告 | 对象、解释、编排、协同、治理构成连续方法链 | 本书内部结构+外部总锚点 | Masterman et al.; Naikar et al. | 应明确为作者组织框架 |

## 5. 图表公式计划

| 元素编号 | 类型 | 主题 | 来源状态 | 预期来源/说明 |
|---|---|---|---|---|
| Fig-1 | 图 | T2a 物理 AI 与 T2b 认知主线双轨关系图 | 自制 | 作为整卷总图，应显示两条主线的分工与接口 |
| Tab-1 | 表 | 控制主线与认知主线能力对照表 | 汇编 | 依据本章正文整理，为后续章节提供术语入口 |
| Fig-2 | 图 | 前半卷方法链总览图 | 自制 | 展示对象、解释、编排、协同、治理五级递进 |
| Box-1 | 案例框 | “控制很好但解释断裂”的运行案例 | 自制/待核 | 用于说明第二条主线的必要性 |

## 6. 证据缺口

| 序号 | 问题 | 影响范围 | 解决动作 |
|---|---|---|---|
| 1 | “工作世界升级”仍偏作者归纳，需更强复杂工作系统文献绑定 | 1.3 | 在来源笔记中强化 Naikar 等来源的桥接解释 |
| 2 | T2a/T2b 双轨关系总图尚未独立固化 | 全章图表 | 在图表治理文件中补成整卷接口图任务 |
| 3 | 控制论经典与认知代理综述之间的桥接语仍需更细化 | 1.1-1.2 | 第三轮精修时补一段源流过渡说明 |

## 7. 审核结论

> 本章作为导论章，其主要任务不是提供大量新事实，而是完成结构性定标：为什么在物理 AI 主线之外，必须建立认知主线。当前支撑已经足够形成章节级证据治理，但第三轮精修时仍需进一步强化“控制—认知—治理”之间的桥接语言，避免导论过于依赖内部术语自洽。

## 8. 第三轮精修前置建议

第三轮精修时，本章应优先稳定三项内容。第一，完成 T2a/T2b 双轨关系图。第二，把“工作世界”与“复杂社会技术系统”的关系解释得更清楚。第三，为后续五章预设跨章共享术语表，使导论真正承担起方法链入口功能。

## References

[1]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[2]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
[3]: https://mitpress.mit.edu/9780262730099/cybernetics/ "Cybernetics: Or Control and Communication in the Animal and the Machine"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[5]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
