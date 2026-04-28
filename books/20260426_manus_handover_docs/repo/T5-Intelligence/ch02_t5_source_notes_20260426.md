# T5 第2章来源笔记

## 来源 1：Physics-informed machine learning

- 来源链接：<https://www.nature.com/articles/s42254-021-00314-5>
- 用途：支撑物理约束、机理知识与机器学习在数据、结构、损失和推断层的融合思路。

### 本章写作含义

该综述是本章的核心外部锚点。它能够帮助本章说明：机理嵌入不是一个额外插件，而是一种贯穿模型生命周期的设计原则。尤其适合支撑“机理嵌入可发生在多个层面，而不是只有 PINNs 一种形态”的判断。

## 来源 2：Physics-informed neural networks

- 来源链接：<https://www.sciencedirect.com/science/article/pii/S0021999118307125>
- 用途：支撑把 PDE 残差、边界条件与物理规律并入神经网络训练目标的典型方法路径。

### 本章写作含义

该文适合用来说明为什么 Saint-Venant 方程、守恒残差和边界条件可以成为学习结构的一部分，而不是训练后的外部检查项。它可为本章后续通向第3章的 PINNs 方法树建立直接入口。

## 来源 3：Integrating physics-based modeling with machine learning

- 来源链接：<https://www.nature.com/articles/s42256-020-00287-8>
- 用途：支撑更广义的物理模型与机器学习融合框架，而不把问题简化为单一 PINNs 路线。

### 本章写作含义

这篇综述能够帮助本章避免把“物理信息学习”等同于某一类神经网络结构。它适合支撑本章对数据层、结构层、损失层和部署层多种嵌入路径的归纳，并为后续混合建模选择树提供综述背景。

## 来源 4：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑物理一致性与可部署性之间的治理联系，说明模型即便“更合理”也仍需风险管理、监督与验证。

### 可直接支持的关键表述

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

### 本章写作含义

该框架有助于本章强调：机理嵌入是必要条件，但不是充分条件。即便一个模型在物理上更一致，也仍需要经过监督、验证、责任配置与部署门禁，才能成为关键基础设施中的可信系统。

## 来源 5：Saint-Venant / 水力学基础来源（待补具体教材条目）

- 来源状态：待在第三轮精修前补入正式教材或权威课程来源。
- 用途：支撑水位、流量、坡降和过程一致性的领域基础，避免章节过度依赖 AI 文献而缺失领域底盘。

### 本章写作含义

本章在讨论“方程不是建议”时，需要有足够明确的领域基础来源支撑。第三轮精修前应补入水力学教材或权威课程材料，使本章既有 AI 方法来源，也有水利领域原理来源。

## 小结

本章目前已经具备“PIML 总述 + PINNs 代表方法 + 更广义融合综述 + 风险治理框架 + 领域基础待补”的来源结构。下一步第三轮精修时，应优先补齐第 5 条的正式领域来源，并增加一段对“必要但不充分”判断的明确来源归属说明。

## References

[1]: https://www.nature.com/articles/s42254-021-00314-5 "Physics-informed machine learning"
[2]: https://www.sciencedirect.com/science/article/pii/S0021999118307125 "Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations"
[3]: https://www.nature.com/articles/s42256-020-00287-8 "Integrating physics-based modeling with machine learning"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
