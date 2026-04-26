# T2b 第3章来源笔记

## 来源 1：ReAct: Synergizing Reasoning and Acting in Language Models

- 来源链接：<https://openreview.net/forum?id=WE_vluYUL-X>
- 用途：支撑“推理—行动交替”“推理链不只是思考，而是与外部动作和工具调用耦合”的论断。

### 可直接支持的关键表述

> ReAct prompts LLMs to generate both verbal reasoning traces and task-specific actions in an interleaved manner.

> ReAct allows language models to interact with external environments and gather additional information.

### 本章写作含义

该文适合作为本章“快思考/慢思考”工程化讨论的重要方法来源。它表明认知系统的价值不在于单次回答，而在于把推理链与外部动作、信息获取和回路更新组织起来。这可直接支撑本章关于“快慢差别首先是工作流差别”的判断。

## 来源 2：The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey

- 来源链接：<https://arxiv.org/abs/2404.11584>
- 用途：支撑代理中的 planning、execution、reflection 与单/多代理架构框架。

### 可直接支持的关键表述

> Agentic systems have a notion of planning, loops, reflection and other control structures that heavily leverage the model’s inherent reasoning capabilities to accomplish a task end-to-end.

> Single agent architectures excel when problems are well-defined and feedback from other agent-personas or the user is not needed, while multi-agent architectures tend to thrive when collaboration and multiple distinct execution paths are required.

### 本章写作含义

该综述适合用来说明：认知引擎的“解释”不能脱离 planning、execution、reflection 这些控制结构而孤立理解。解释链若不能进入后续工作流，就只是语言表演，而不是运行支持能力。

## 来源 3：Designing human-AI systems for complex settings

- 来源链接：<https://doi.org/10.1080/00140139.2023.2281898>
- 用途：支撑“复杂运行环境中的人机协同不是 dyadic interaction，而是分布式团队与网络化技术共同构成的复杂工作系统”。

### 可直接支持的关键表述

> The demands of complex operational settings are met by multiple, distributed teams interwoven with a large array of artefacts and networked technologies, including automation.

> Current models of human-automation interaction ... tend to be dyadic in nature.

> Design frameworks informed by contemporary views of complex work performance are needed.

### 本章写作含义

这篇论文能够帮助本章把“解释服务对象”从抽象用户转回到实际工作系统。对于调度场景而言，解释是否可用，取决于它能否支持值班员、会商组织、审批角色和协同部门在共同约束下形成一致判断。

## 来源 4：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑过度依赖、监督责任、解释边界与治理结构前置等表述。

### 可直接支持的关键表述

> AI risk management efforts should consider that humans may over-rely on AI outputs.

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

### 本章写作含义

该框架可直接补强本章关于“说得流畅反而危险”的讨论。因为解释若强化了自动化偏置，而不是帮助人类更好地理解系统边界，那么解释反而会放大风险。

## 来源 5：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑自然人应能理解系统能力边界、覆盖输出、停止系统以及避免过度依赖的条文要求。

### 可直接支持的关键表述

> Natural persons ... are enabled ... to properly understand the relevant capacities and limitations of the high-risk AI system.

> Natural persons ... are enabled ... to correctly interpret the high-risk AI system’s output.

> Natural persons ... are enabled ... to decide ... not to use the high-risk AI system or to otherwise disregard, override or reverse the output of the high-risk AI system.

### 本章写作含义

这些条文非常适合支撑本章“运行解释不是把答案说清楚，而是把责任说清楚”的中心判断。解释若不能帮助人类理解边界、实施覆盖和停止，就不构成合格的高风险系统解释机制。

## 来源 6：Thinking, Fast and Slow

- 来源链接：<https://us.macmillan.com/books/9780374533557/thinkingfastandslow>
- 用途：作为“快思考/慢思考”概念源流，用于说明本章采用的是工程隐喻而非原义照搬。

### 本章写作含义

该书主要承担概念源流说明作用。正式写作时应明确指出，本章借用“快/慢思考”只是为了帮助读者理解两类认知工作流节奏差异，而非把心理学双系统理论直接翻译为软件架构。

## 小结

本章已经形成“reasoning/acting 原始论文 + 代理综述 + 复杂工作系统设计 + 风险治理规范 + 概念源流说明”的来源组合。下一步可再补一条高风险领域规程检索或知识治理来源，以进一步强化“规程理解不同于通用问答”的章节论断。

## References

[1]: https://openreview.net/forum?id=WE_vluYUL-X "ReAct: Synergizing Reasoning and Acting in Language Models"
[2]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[3]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[5]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[6]: https://us.macmillan.com/books/9780374533557/thinkingfastandslow "Thinking, Fast and Slow"
