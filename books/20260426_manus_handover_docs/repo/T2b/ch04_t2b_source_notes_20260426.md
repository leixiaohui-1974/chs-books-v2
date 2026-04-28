# T2b 第4章来源笔记

## 来源 1：The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey

- 来源链接：<https://arxiv.org/abs/2404.11584>
- 用途：支撑任务编排中 planning、execution、reflection、single-agent / multi-agent 架构与 communication style 等概念。

### 可直接支持的关键表述

> Agents allow for more complex interaction and orchestration.

> Agentic systems have a notion of planning, loops, reflection and other control structures that heavily leverage the model’s inherent reasoning capabilities to accomplish a task end-to-end.

> Our contribution outlines key themes when selecting an agentic architecture, the impact of leadership on agent systems, agent communication styles, and key phases for planning, execution, and reflection.

### 本章写作含义

该综述可作为本章的总外部锚点，帮助把任务编排从“工具串联”提升为“规划、执行、反思与组织控制结构”的工程问题。它尤其适合支撑“解释之后必须进入任务编排”的核心判断。

## 来源 2：ReAct: Synergizing Reasoning and Acting in Language Models

- 来源链接：<https://openreview.net/forum?id=WE_vluYUL-X>
- 用途：支撑 reasoning 与 acting 交替、行动前后信息更新与回路收敛的基本机制。

### 可直接支持的关键表述

> ReAct prompts LLMs to generate both verbal reasoning traces and task-specific actions in an interleaved manner.

> ReAct allows language models to interact with external environments and gather additional information.

### 本章写作含义

该文可直接支撑本章关于任务编排必须包含行动、反馈与再判断的观点。它说明工作流闭环不是额外包装，而是认知系统走向可执行性的基本条件。

## 来源 3：Language Models Can Teach Themselves to Use Tools

- 来源链接：<https://arxiv.org/abs/2302.04761>
- 用途：支撑工具调用是模型可组织、可学习的能力，而非简单外挂接口。

### 可直接支持的关键表述

> We introduce Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results.

> We show that LMs can teach themselves to use external tools via simple APIs and achieve the best of both worlds.

### 本章写作含义

该来源可用来说明为什么本章需要在“工具”之上再引入 Skill 与工作流层。因为真正困难的不在于是否接上工具，而在于何时调用、以何参数调用、如何解释结果、何时停止或回退。

## 来源 4：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑治理结构、角色责任、监控与留痕等高风险系统要求。

### 可直接支持的关键表述

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

> Understanding and managing the risks of AI systems will help to enhance trustworthiness.

### 本章写作含义

该框架适合用来支撑“结果留痕必须服务责任和复盘”的判断。对本章而言，日志不是技术附属物，而是责任链和回退链的一部分。

## 来源 5：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑工作流中的覆盖、停止、不过度依赖和解释边界要求。

### 可直接支持的关键表述

> The oversight measures shall be commensurate with the risks, level of autonomy and context of use of the high-risk AI system.

> Natural persons ... are enabled ... to decide ... not to use the high-risk AI system or to otherwise disregard, override or reverse the output.

> Natural persons ... are enabled ... to intervene in the operation of the high-risk AI system or interrupt the system through a ‘stop’ button.

### 本章写作含义

该条文可直接补强本章的异常回退与人工覆盖节点设计。也就是说，一个完整的工作流并不只定义“如何调用”，还必须定义“何时停、谁能停、停后如何安全收口”。

## 来源 6：Designing human-AI systems for complex settings

- 来源链接：<https://doi.org/10.1080/00140139.2023.2281898>
- 用途：支撑工作流设计应面向分布式团队与复杂社会技术系统，而非单个用户体验。

### 可直接支持的关键表述

> The demands of complex operational settings are met by multiple, distributed teams interwoven with a large array of artefacts and networked technologies, including automation.

> Design frameworks informed by contemporary views of complex work performance are needed.

### 本章写作含义

这篇论文能帮助本章把 Skill、工作流与工作代理的层级关系落回真实组织语境。因为工作流的终点不是“模型完成任务”，而是让分布式团队在可监督、可回退的条件下完成工作。

## 小结

本章已经具备“代理综述 + reasoning/acting 原始论文 + 工具调用论文 + 风险治理规范 + 复杂工作系统设计”五层来源结构。下一步如需进一步强化学术纵深，可再补一条关于代理脆弱性或工作流失败模式的来源，以支撑第4.4节的风险分类。

## References

[1]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[2]: https://openreview.net/forum?id=WE_vluYUL-X "ReAct: Synergizing Reasoning and Acting in Language Models"
[3]: https://arxiv.org/abs/2302.04761 "Language Models Can Teach Themselves to Use Tools"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[5]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[6]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
