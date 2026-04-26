# 章节证据卡

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 章节编号 | T2b 第5章 |
| 章节标题 | 从单代理到多代理：协同、状态传递与冲突消解 |
| 所属卷册 | T2b《从控制到认知：水系统运行智能的方法链与工作代理》 |
| 目标读者 | 平台架构师、运行调度管理者、协同系统设计者、研究生 |
| 与前后章节关系 | 本章承接第4章工作流与工作代理的层级结构，把单代理推进为多代理协同结构；后续第6章进一步讨论授权边界、人工接管与平台治理收口。 |

## 2. 核心命题

| 序号 | 核心命题 | 命题类型 | 预期证据等级 | 当前状态 |
|---|---|---|---|---|
| 1 | 单代理的边界并不只来自上下文窗口，更来自任务节奏差异、角色分工需求与组织现实的多角色结构。 | 方法/工程 | Tier 2-3 | 待补 |
| 2 | 多代理不是“多个机器人并排工作”，而是责任可分解、接口可定义、冲突可治理的工作结构。 | 定义/架构 | Tier 2-3 | 待补 |
| 3 | 多代理协同至少存在串行、并行、主从和事件驱动四类基本模式，不同模式对应不同的冲突类型与治理要求。 | 架构/方法 | Tier 2-3 | 待补 |
| 4 | 状态传递并非简单消息转发，而是工作世界局部快照的受控共享，必须区分事实状态与推断状态。 | 工程/治理 | Tier 2-3 | 待补 |
| 5 | 冲突消解的关键不在于让代理“谈拢”，而在于明确仲裁权、版本权、覆盖权和回退权。 | 治理/工程 | Tier 1-2 | 待补 |

## 3. 必引经典文献

| 序号 | 文献 | 作用 | 是否已纳入 |
|---|---|---|---|
| 1 | Masterman et al., *The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey* | 支撑单代理/多代理、纵向/横向架构与 communication styles | 是 |
| 2 | Torreño et al., *Cooperative Multi-Agent Planning: A Survey* | 支撑多代理规划、协同与分布式任务求解的经典综述锚点 | 否 |
| 3 | Stone & Veloso, *Multiagent Systems: A Survey from a Machine Learning Perspective* | 支撑 MAS 的经典问题空间与协调维度 | 否 |
| 4 | NIST AI RMF / EU AI Act Article 14 | 支撑监督、覆盖、回退与责任分配 | 是 |
| 5 | Naikar et al., *Designing human-AI systems for complex settings* | 支撑多角色、分布式团队与复杂工作系统视角 | 是 |

## 4. 证据来源计划

| 章节小节 | 关键论断 | 需要的来源类型 | 候选来源 | 风险备注 |
|---|---|---|---|---|
| 5.1 单代理边界 | 上下文、节奏与角色现实共同构成单代理边界 | 代理综述/复杂工作系统论文 | Masterman et al.; Naikar et al. | 需避免把多代理必要性只归因于模型上下文长度 |
| 5.2 多代理的定义 | 多代理本质是责任可分解的工作结构 | MAS 综述/代理架构综述/内部平台框架 | Torreño et al.; Stone & Veloso；Masterman et al. | 需把经典 MAS 与 LLM-agent 语境区别写清 |
| 5.3 四类协同模式 | 串行、并行、主从、事件驱动模式各有适用边界 | MAS 规划综述/代理架构论文/内部经验 | Torreño et al.; Masterman et al. | 模式分类有作者归纳成分，需说明 |
| 5.4 状态传递 | 共享的是受控状态快照而非自然语言闲聊 | MAS 文献/治理规范/内部对象模型 | Stone & Veloso；NIST AI RMF；内部平台状态模型 | 需补事实状态与推断状态的外部桥接 |
| 5.5 冲突消解 | 仲裁权、版本权、覆盖权、回退权必须前置设计 | 治理规范/复杂工作系统来源 | NIST AI RMF；EU AI Act；Naikar et al. | 需避免把冲突消解写成“对话商量” |

## 5. 图表公式计划

| 元素编号 | 类型 | 主题 | 来源状态 | 预期来源/说明 |
|---|---|---|---|---|
| Fig-1 | 图 | 单代理与多代理边界对照图 | 自制 | 用于说明边界变化来自工作结构而非仅来自模型能力 |
| Fig-2 | 图 | 四类协同模式示意图 | 自制 | 应明确串行、并行、主从、事件驱动的接口差异 |
| Tab-1 | 表 | 状态传递中的事实状态/推断状态/授权状态对照表 | 汇编 | 依据本章正文整理，是多代理治理核心表 |
| Fig-3 | 图 | 冲突消解权限图 | 自制 | 应标出仲裁权、版本权、覆盖权、回退权四种权力 |
| Box-1 | 案例框 | “协同良好但责任不清”的联合处置案例 | 自制/待核 | 用于说明多代理成功协同不等于责任正确收口 |

## 6. 证据缺口

| 序号 | 问题 | 影响范围 | 解决动作 |
|---|---|---|---|
| 1 | 经典 MAS 综述尚未正式补入，当前多代理讨论偏重新近 agent 综述 | 5.2-5.4 | 补引 Cooperative Multi-Agent Planning 与 Stone & Veloso 等经典来源 |
| 2 | 事实状态/推断状态的分层语言主要来自章节内部组织，需更强外部桥接 | 5.4 | 补检索共享状态、belief state、coordination 相关来源 |
| 3 | 四类协同模式与冲突权力结构尚未绑定更明确的图示与来源说明 | 5.3-5.5 | 在图表治理文件中补来源映射与权限标注 |
| 4 | 本章若不尽快形成协同模式图，将影响第6章授权与接管层级的表达 | 全章图表 | 优先固化 Fig-2 与 Fig-3 |

## 7. 审核结论

> 本章已具备把“多代理”从热词拆解为工作结构的良好基础。当前最需要补强的是两条证据线：一条是经典 MAS/多代理规划文献，用于稳住多代理概念的学术底盘；另一条是治理规范与复杂工作系统来源，用于把状态传递与冲突消解写成责任结构而非仅写成消息机制。

## 8. 第三轮精修前置建议

第三轮精修时，本章应优先完成三项收口。第一，把四类协同模式与第6章授权分层明确对齐，形成跨章一致的“模式—权限—回退”框架。第二，将“状态传递”统一改写为“状态快照受控共享”，避免读者误解为普通多轮对话。第三，为经典 MAS 来源增补一段简短桥接文字，说明本章如何从传统多代理系统转入 LLM 驱动的工作代理平台。

## References

[1]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[2]: https://dl.acm.org/doi/10.1145/3128584 "Cooperative Multi-Agent Planning: A Survey"
[3]: https://www.cs.cmu.edu/~mmv/papers/MASsurvey.pdf "Multiagent Systems: A Survey from a Machine Learning Perspective"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[5]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[6]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
