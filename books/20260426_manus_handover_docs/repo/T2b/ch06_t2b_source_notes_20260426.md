# T2b 第6章来源笔记

## 来源 1：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑高风险 AI 系统必须可被自然人有效监督、理解边界、覆盖输出、停止系统与避免过度依赖等要求。

### 可直接支持的关键表述

> High-risk AI systems shall be designed and developed in such a way ... that they can be effectively overseen by natural persons during the period in which they are in use.

> Human oversight shall aim to prevent or minimise the risks to health, safety or fundamental rights.

> The oversight measures shall be commensurate with the risks, level of autonomy and context of use of the high-risk AI system.

> Natural persons ... are enabled ... to properly understand the relevant capacities and limitations of the high-risk AI system.

> Natural persons ... are enabled ... to decide ... not to use the high-risk AI system or to otherwise disregard, override or reverse the output of the high-risk AI system.

> Natural persons ... are enabled ... to intervene in the operation of the high-risk AI system or interrupt the system through a ‘stop’ button or a similar procedure.

### 本章写作含义

该条文是本章最硬的规范锚点。它几乎可以直接支撑“授权不是一次性开关”“人工接管必须被前置设计”“覆盖权与停止权属于正式治理能力而非临时补丁”等核心判断。

## 来源 2：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑 AI 风险管理、角色责任、监督、沟通链与治理结构设计。

### 可直接支持的关键表述

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

> AI risk management efforts should consider that humans may over-rely on AI outputs.

> Understanding and managing the risks of AI systems will help to enhance trustworthiness.

### 本章写作含义

该框架能帮助本章从“法规要求”进一步走向“治理机制设计”。它适合用来支撑覆盖权、停止权、回退权、审计权和追溯权的配置逻辑，也适合解释为什么越是高风险平台，越不能把责任藏在模型接口之后。

## 来源 3：Designing human-AI systems for complex settings

- 来源链接：<https://doi.org/10.1080/00140139.2023.2281898>
- 用途：支撑人工接管与监督应服务复杂社会技术系统，而非单次人机交互。

### 可直接支持的关键表述

> The demands of complex operational settings are met by multiple, distributed teams interwoven with a large array of artefacts and networked technologies, including automation.

> Current models of human-automation interaction ... tend to be dyadic in nature.

> Design frameworks informed by contemporary views of complex work performance are needed.

### 本章写作含义

这篇论文能直接帮助本章避免把“人工接管”写成单人点击按钮的孤立行为。对复杂运行平台而言，接管总是嵌在团队、制度、工具链和状态版本管理中，因此需要被设计成结构能力。

## 来源 4：The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey

- 来源链接：<https://arxiv.org/abs/2404.11584>
- 用途：支撑多代理结构、leadership、communication styles 与 planning/execution/reflection 相互耦合的架构背景。

### 可直接支持的关键表述

> Our contribution outlines key themes when selecting an agentic architecture, the impact of leadership on agent systems, agent communication styles, and key phases for planning, execution, and reflection.

> Multi-agent architectures ... each agent typically has their own persona.

### 本章写作含义

该综述能够帮助本章解释：多代理结构一旦引入 leadership、communication style 和多阶段执行，其授权与责任问题就会被放大。因此，授权边界不能只按单代理逻辑来设计。

## 来源 5：Institutionalised distrust and human oversight of artificial intelligence

- 来源链接：<https://link.springer.com/article/10.1007/s00146-023-01777-z>
- 用途：支撑 human oversight 的制度化理解，而不把其简化为个体是否“看着系统”。

### 可直接支持的关键表述

该文聚焦欧盟 AI 法案语境下的人类监督设计，适合作为本章从法规文本走向制度设计的桥接来源。它有助于说明 human oversight 并非一种心理感觉，而是一组被制度化配置的监督条件、权限与不信任设计。

### 本章写作含义

正式写作时，可用该文说明为什么本章强调“结构化不信任”与“制度化接管”：因为高风险系统并不假设人类永远正确，而是假设系统必须被设计成允许有权角色在适当条件下介入、覆盖、停止并追责。

## 小结

本章已经形成“法规条文 + 风险治理框架 + 复杂工作系统设计 + agent 架构综述 + 制度化监督研究”的五层来源结构。这一组合足以支撑授权边界、人工接管与平台治理收口的主要论证。下一步如需继续增强，可再补一条关于 auditability 或 accountability 的技术治理来源，用于加强审计链与责任追溯链的写法。

## References

[1]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[2]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[3]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
[4]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[5]: https://link.springer.com/article/10.1007/s00146-023-01777-z "Institutionalised distrust and human oversight of artificial intelligence"
