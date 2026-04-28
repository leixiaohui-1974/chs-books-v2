# T5 第5章来源笔记

## 来源 1：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑高风险 AI 的验证、监督、角色责任、沟通链和风险管理结构。

### 可直接支持的关键表述

> Understanding and managing the risks of AI systems will help to enhance trustworthiness.

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

### 本章写作含义

该框架是本章“运行资格”概念最重要的治理锚点。它可直接支撑“模型有效不等于运行可信”“不同风险等级需要不同验证强度与监督密度”这类核心判断。

## 来源 2：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑高风险系统中的覆盖、停止、理解边界与不过度依赖等要求。

### 可直接支持的关键表述

> The oversight measures shall be commensurate with the risks, level of autonomy and context of use of the high-risk AI system.

> Natural persons ... are enabled ... to decide ... not to use the high-risk AI system or to otherwise disregard, override or reverse the output.

### 本章写作含义

该条文非常适合作为本章“部署分级”部分的法规锚点。它能帮助本章把不同运行资格与不同监督要求、停止能力和覆盖能力明确对应起来。

## 来源 3：模型治理 / MLOps 生命周期来源（待补）

- 来源状态：待第三轮精修前补入正式来源。
- 用途：支撑模型生命周期管理、监控、版本控制和上线审批治理。

### 本章写作含义

本章在讨论“运行资格”时，不能只依赖 AI 治理框架，还需要更贴近模型生命周期管理的来源。第三轮精修时应补入至少一条 MLOps 或 model governance 来源，以支撑版本治理、再训练、监控和回滚等具体治理动作。

## 来源 4：xIL/HIL 验证链来源（待补）

- 来源状态：待第三轮精修前补入正式来源。
- 用途：支撑在环验证、软硬件联调、部署前闸门和运行前审查。

### 本章写作含义

本章需要把验证闭环具体化，而不是抽象地说“多做测试”。因此，xIL/HIL 相关来源对说明“为何离线高分不足以获得运行资格”具有关键作用。

## 来源 5：代理模型/数字孪生治理来源（待补）

- 来源状态：待第三轮精修前补入正式来源。
- 用途：支撑 surrogate model、twin、快速替代求解器在验证链中的风险传播与治理需求。

### 本章写作含义

本章提出“代理模型也要被治理”，这是非常关键但当前外部锚点仍偏弱的一点。第三轮精修时应补入更具体的工程来源，以证明 surrogate/twin 并非中性工具，而会显著影响验证链的可信度。

## 小结

本章当前已经形成“风险治理框架 + human oversight 法规 + 模型治理待补 + xIL/HIL 待补 + 代理模型治理待补”的来源结构。下一步第三轮精修时，应优先补齐后三类来源，以便把“运行资格”概念从治理直觉提升为证据更完整的部署框架。

## References

[1]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[2]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
