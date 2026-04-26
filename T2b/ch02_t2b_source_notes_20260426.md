# T2b 第2章来源笔记

## 来源 1：The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey

- 来源链接：<https://arxiv.org/abs/2404.11584>
- 用途：支撑“代理具备规划、行动、工具调用与迭代执行能力”“单代理与多代理架构差异”“工具是可调用函数而不是抽象能力”等论断。

### 可直接支持的关键表述

> AI agents are language model-powered entities able to plan and take actions to execute goals over multiple iterations.

> Agents allow for more complex interaction and orchestration. In particular, agentic systems have a notion of planning, loops, reflection and other control structures that heavily leverage the model’s inherent reasoning capabilities to accomplish a task end-to-end.

> Tools. In the context of AI agents, tools represent any functions that the model can call.

> Single Agent Architectures. These architectures are powered by one language model and will perform all the reasoning, planning, and tool execution on their own.

> Multi-Agent Architectures. These architectures involve two or more agents ... Each agent typically has their own persona.

### 本章写作含义

该文可作为本章“机器学习与认知工作流的关系”之统一外部锚点。它尤其适合支撑“输出并非终局动作，而是进入规划、执行、反思与工具链的一个节点”这一判断，也可为后文的 Skill 编排与多代理协同预先埋下术语基础。

## 来源 2：Designing human-AI systems for complex settings

- 来源链接：<https://doi.org/10.1080/00140139.2023.2281898>
- 用途：支撑“复杂运行工作不是单个人—单台机器之间的 dyadic interaction”“解释、监督、接管应服务于复杂社会技术系统”这一论断。

### 可直接支持的关键表述

> Real-world events ... remind us that the demands of complex operational settings are met by multiple, distributed teams interwoven with a large array of artefacts and networked technologies, including automation.

> Current models of human-automation interaction ... tend to be dyadic in nature, assuming individual humans interacting with individual machines.

> We show how ideas of distributed cognition, joint cognitive systems, and self-organisation lead to specific concepts for designing human-AI systems.

> Design frameworks informed by contemporary views of complex work performance are needed. We discuss cognitive work analysis as an example.

### 本章写作含义

这篇论文适合用来解释为什么本章不能只谈“模型输入输出”，而必须进一步讨论对象映射、任务边界与责任角色。因为在复杂运行场景中，模型输出面对的不是抽象用户，而是分布式团队、网络化工具链与制度化流程。

## 来源 3：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑高风险 AI 的人类监督、角色配置、风险管理与责任前置等表述。

### 可直接支持的关键表述

> Understanding and managing the risks of AI systems will help to enhance trustworthiness, and in turn, cultivate public trust.

> AI risk management efforts should consider that humans may assume that AI systems work as intended, and may not override the system when needed.

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

### 本章写作含义

该框架可作为本章“五问法”中门禁、回退与责任链三项问题的规范锚点。它特别适合支撑“先定义责任，再训练模型”的治理顺序，因为模型一旦进入高后果工作流，其风险已经不再只是精度问题。

## 来源 4：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑“推荐不等于授权”“人类应能理解能力边界、拒绝使用、覆盖输出、停止系统”这类部署约束。

### 可直接支持的关键表述

> Human oversight shall aim to prevent or minimise the risks to health, safety or fundamental rights that may emerge when a high-risk AI system is used.

> The oversight measures shall be commensurate with the risks, level of autonomy and context of use of the high-risk AI system.

> Natural persons ... are enabled ... to properly understand the relevant capacities and limitations of the high-risk AI system.

> Natural persons ... are enabled ... to decide ... not to use the high-risk AI system or to otherwise disregard, override or reverse the output of the high-risk AI system.

> Natural persons ... are enabled ... to intervene in the operation of the high-risk AI system or interrupt the system through a ‘stop’ button or a similar procedure.

### 本章写作含义

该条文可直接补强本章有关“建议不能被自动滑移为命令”的治理表述。它还为后续第6章的人工接管和授权分层提供了规范语言，因此本章可先以“推荐不等于授权”的方式引用其治理精神。

## 来源 5：Cybernetics: Or Control and Communication in the Animal and the Machine

- 来源链接：<https://mitpress.mit.edu/9780262730099/cybernetics/>
- 用途：作为控制论经典来源，支撑“控制回路并不天然等于认知工作流”这一历史对照。

### 可直接支持的关键表述

本书是控制与通信统一视角的奠基性来源，适合用于说明 T2b 并不是抛弃控制，而是在控制论底座之上引入认知层扩展。考虑到本章的主要任务不是展开控制史，正式写作中宜将其作为理论源流锚点，而不宜过度延伸。

### 本章写作含义

该来源主要承担“历史锚点”作用，用于将 T2a 的控制底座与 T2b 的认知扩展区分开来，防止读者误以为机器学习章节意在替代控制论框架。

## 小结

本章目前已经具备“代理综述 + 复杂工作系统设计 + 风险治理规范 + 控制论源流”四层来源结构。下一步如需进一步增强学术完整性，可再补一条经典 AI/ML 教材来源，用以支撑七类任务拆解的教材化表述。

## References

[1]: https://arxiv.org/abs/2404.11584 "The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey"
[2]: https://doi.org/10.1080/00140139.2023.2281898 "Designing human-AI systems for complex settings"
[3]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[4]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
[5]: https://mitpress.mit.edu/9780262730099/cybernetics/ "Cybernetics: Or Control and Communication in the Animal and the Machine"
