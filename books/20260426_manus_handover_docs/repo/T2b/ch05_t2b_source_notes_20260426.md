# T2b 第5章来源笔记

## 来源 1：The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey

- 来源链接：<https://arxiv.org/abs/2404.11584>
- 用途：支撑单代理/多代理架构、纵向/横向组织、leadership 与 communication styles 等论断。

### 可直接支持的关键表述

> Single agent architectures excel when problems are well-defined and feedback from other agent-personas or the user is not needed.

> Multi-agent architectures tend to thrive more when collaboration and multiple distinct execution paths are required.

> Vertical architectures ... one agent acts as a leader and has other agents report directly to them.

> Horizontal architectures ... all the agents are treated as equals and are part of one group discussion about the task.

### 本章写作含义

该综述可以直接支撑本章关于“单代理边界”和“多代理组织模式”的基本判断。它尤其适合帮助本章把多代理从“多个模型”重新界定为一种组织结构选择。

## 来源 2：Cooperative Multi-Agent Planning: A Survey

- 来源链接：<https://dl.acm.org/doi/10.1145/3128584>
- 用途：支撑多代理规划、分布式任务求解、协调与通信的经典问题结构。

### 可直接支持的关键表述

该综述聚焦 cooperative multi-agent planning 的求解与协调问题，适合作为本章回接传统多代理系统研究脉络的经典锚点。它能帮助本章说明：多代理问题的核心一直不是“多几个智能体”，而是如何分解任务、协调局部视角并处理共享约束。

### 本章写作含义

正式写作时，可用该综述将本章的“串行/并行/主从/事件驱动”模式放回更广义的多代理协调传统中，从而降低本章仅依赖新近 LLM-agent 语汇的风险。

## 来源 3：Multiagent Systems: A Survey from a Machine Learning Perspective

- 来源链接：<https://www.cs.cmu.edu/~mmv/papers/MASsurvey.pdf>
- 用途：支撑多代理系统中的协同、竞争、通信与学习问题空间。

### 可直接支持的关键表述

该综述是多代理系统的经典综述来源之一，适合作为本章讨论状态共享、局部视图与协调难题的理论背景。它对于说明“接口比对话更重要”“局部决策与全局约束需要协调”尤其有用。

### 本章写作含义

本章可以借此把“状态传递”进一步提升为多代理系统中的共享知识与协调问题，而不是把它写成自然语言聊天记录的堆叠。

## 来源 4：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑角色责任、沟通链、监督机制与风险前置设计。

### 可直接支持的关键表述

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

> Understanding and managing the risks of AI systems will help to enhance trustworthiness.

### 本章写作含义

该框架能直接补强本章的冲突消解与状态治理部分。对多代理系统而言，风险并不只来自某个单体代理失误，也来自角色分工混乱、通信链断裂和监督责任不清。

## 来源 5：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑覆盖、停止、不过度依赖与监督措施应与 autonomy/context 对齐等要求。

### 可直接支持的关键表述

> The oversight measures shall be commensurate with the risks, level of autonomy and context of use of the high-risk AI system.

> Natural persons ... are enabled ... to decide ... not to use the high-risk AI system or to otherwise disregard, override or reverse the output.

### 本章写作含义

这些条文非常适合支撑本章“冲突消解不能只靠代理互相协商，还需要明确覆盖权与停止权”的判断。它们也为下一章授权与接管设计提供了规范接口。

## 来源 6：Designing human-AI systems for complex settings

- 来源链接：<https://doi.org/10.1080/00140139.2023.2281898>
- 用途：支撑多角色、分布式团队与复杂社会技术系统视角。

### 可直接支持的关键表述

> The demands of complex operational settings are met by multiple, distributed teams interwoven with a large array of artefacts and networked technologies, including automation.

### 本章写作含义

该文可帮助本章说明：多代理协同并不是人工智能世界里独立发生的，它总是嵌在复杂组织工作中。因此，状态传递、冲突消解和权限划分都必须服务于真实团队协作，而不是只服务于代理之间的“对话美感”。

## 小结

本章已经具备“新近 agent 综述 + 经典 MAS 综述 + 风险治理规范 + 复杂工作系统来源”的四层来源结构。下一步如需进一步强化学术严谨性，可再补一条关于共享状态或 belief/coordination 的更细粒度来源，用于支撑“事实状态与推断状态必须区分”的表述。

## References

[1]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[2]: https://dl.acm.org/doi/10.1145/3128584 "Cooperative Multi-Agent Planning: A Survey"
[3]: https://www.cs.cmu.edu/~mmv/papers/MASsurvey.pdf "Multiagent Systems: A Survey from a Machine Learning Perspective"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[5]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[6]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
