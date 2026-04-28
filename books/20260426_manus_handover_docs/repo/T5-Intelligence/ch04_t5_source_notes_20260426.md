# T5 第4章来源笔记

## 来源 1：Reinforcement Learning: An Introduction

- 来源链接：<https://mitpress.mit.edu/9780262039246/reinforcement-learning/>
- 用途：支撑强化学习的基本问题定义、策略学习与价值优化的经典框架。

### 本章写作含义

该书是本章讨论 RL 的基础锚点。它有助于提醒读者：标准 RL 的出发点通常是假设环境可交互、回报可学习、探索可接受，但水利场景对这些假设都设定了更强约束，因此不能直接套用“探索—优化”的通用逻辑。

## 来源 2：A Comprehensive Survey on Safe Reinforcement Learning

- 来源链接：<https://jmlr.org/papers/v16/garcia15a.html>
- 用途：支撑安全强化学习的基本问题空间、风险约束与安全探索框架。

### 本章写作含义

该综述是本章最重要的安全 RL 外部锚点之一。它能够帮助本章说明：安全 RL 并非简单给奖励函数加惩罚，而是一整套关于安全探索、约束满足、风险意识和安全回退的框架性问题。

## 来源 3：Constrained Policy Optimization

- 来源链接：<https://proceedings.mlr.press/v70/achiam17a.html>
- 用途：支撑约束策略优化与在学习过程中显式控制约束违背的代表方法。

### 本章写作含义

该文适合用于本章“约束优化与策略学习必须共同设计”的论证。它可以作为代表性方法来源，说明可行域与约束条件并不是训练结束后再做检查，而应贯穿策略更新过程。

## 来源 4：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑高风险 AI 系统中的验证、监督、角色责任与风险管理。

### 可直接支持的关键表述

> Understanding and managing the risks of AI systems will help to enhance trustworthiness.

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

### 本章写作含义

该框架能把本章从“安全 RL 算法”推进到“高风险决策系统治理”。它特别适合支撑本章后半部分关于验证闸门、人工监督与部署条件的表述。

## 来源 5：xIL/HIL 验证来源（待补）

- 来源状态：待在第三轮精修前补充正式来源。
- 用途：支撑从仿真到现场之间的 xIL/HIL 验证链、代理环境质量评估和部署前闸门。

### 本章写作含义

本章要把 Sim-to-Real Gap 写成工程问题，就需要更明确的 xIL/HIL 来源支撑。第三轮精修时应补入至少一条可以直接支撑“仿真最优不等于可部署”的验证链来源。

## 小结

本章已经具备“RL 教材 + 安全 RL 综述 + 约束策略优化代表方法 + 高风险治理框架 + xIL/HIL 待补”的来源结构。第三轮精修时，应优先补足第 5 条来源，并把其与第6章部署闸门的证据链打通。

## References

[1]: https://mitpress.mit.edu/9780262039246/reinforcement-learning/ "Reinforcement Learning: An Introduction"
[2]: https://jmlr.org/papers/v16/garcia15a.html "A Comprehensive Survey on Safe Reinforcement Learning"
[3]: https://proceedings.mlr.press/v70/achiam17a.html "Constrained Policy Optimization"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
