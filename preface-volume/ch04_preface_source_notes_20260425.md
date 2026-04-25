# 总序卷第4章来源笔记

## 来源 1：Physics-informed machine learning

- 来源链接：<https://www.nature.com/articles/s42254-021-00314-5>
- 用途：作为第4章中“物理 AI”部分的理论锚点，用于支撑为什么现代智能系统不能脱离机理、约束与可验证性。

### 可直接支持的关键表述

> Physics-informed machine learning integrates seamlessly data and mathematical physics models, even in partially understood, uncertain and high-dimensional contexts.

> Such networks can be trained from additional information obtained by enforcing the physical laws.

> It may be possible to design specialized network architectures that automatically satisfy some of the physical invariants for better accuracy, faster training and improved generalization.

> There is a need for developing new frameworks and standardized benchmarks as well as new mathematics for scalable, robust and rigorous next-generation physics-informed learning machines.

### 本章写作含义

该综述可用于支撑本章关于“物理 AI 不是把 AI 用在物理问题上，而是把机理、边界、约束与不变量写回智能系统”的核心判断。它还能作为后文“物理 AI 负责守住可验证性、安全边界与约束一致性”的理论依据。

## 来源 2：The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey

- 来源链接：<https://arxiv.org/abs/2404.11584>
- 用途：作为第4章中“认知 AI”部分的理论锚点，用于支撑推理、规划、工具调用、执行与反思等能力如何构成认知执行链。

### 可直接支持的关键表述

> This survey paper examines the recent advancements in AI agent implementations, with a focus on their ability to achieve complex goals that require enhanced reasoning, planning, and tool execution capabilities.

> We achieve this by providing overviews of single-agent and multi-agent architectures, identifying key patterns and divergences in design choices, and evaluating their overall impact on accomplishing a provided goal.

> Our contribution outlines key themes when selecting an agentic architecture, the impact of leadership on agent systems, agent communication styles, and key phases for planning, execution, and reflection that enable robust AI agent systems.

### 本章写作含义

该综述可用于支撑本章关于“认知 AI 的核心不在于生成文本，而在于承担解释、推理、规划、工具调用与反思”的判断。它适合用于界定认知 AI 在 CHS 双引擎中的职责，即把规程、任务、上下文与多工具执行链组织成可消费的认知工作流。

## 当前可直接落稿的论证节点

| 论证节点 | 可支撑来源 | 用法 |
|---|---|---|
| 物理 AI 的价值在于把机理和物理约束嵌入学习与决策过程 | 来源 1 | 用于本章“物理 AI 的职责”段 |
| 物理 AI 需要面向 robust、rigorous、benchmarkable 的工程要求 | 来源 1 | 用于本章“为何不能只靠黑箱模型”段 |
| 认知 AI 的核心能力是 reasoning、planning、tool execution、reflection | 来源 2 | 用于本章“认知 AI 的职责”段 |
| 认知 AI 适合作为任务组织与工作流协调层 | 来源 2 | 用于本章“双引擎分工与接口”段 |
