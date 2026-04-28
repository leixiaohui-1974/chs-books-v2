# T5 第3章来源笔记

## 来源 1：Physics-informed neural networks

- 来源链接：<https://www.sciencedirect.com/science/article/pii/S0021999118307125>
- 用途：支撑 PINNs 的基本思想、PDE 约束嵌入与典型适用场景。

### 本章写作含义

该文是本章讨论 PINNs 时的第一锚点。它适合用来说明 PINNs 如何通过连续性方程、边界条件和残差项把机理直接纳入学习过程，同时也有助于提醒读者：这是一条强约束路线，但不必然适合所有水利任务。

## 来源 2：Physics-informed machine learning

- 来源链接：<https://www.nature.com/articles/s42254-021-00314-5>
- 用途：支撑 PINNs 之外更广的 PIML 方法族与问题结构视角。

### 本章写作含义

该综述可帮助本章把“方法选择树”建立在更高层的框架上。它说明水利物理 AI 并不是单点方法，而是一组围绕机理强度、数据可得性和目标任务特点展开的设计空间。

## 来源 3：Integrating physics-based modeling with machine learning

- 来源链接：<https://www.nature.com/articles/s42256-020-00287-8>
- 用途：支撑混合建模、残差学习、代理模型与机理—数据耦合路径的广义综述背景。

### 本章写作含义

这篇综述是本章讨论“混合建模不是 PINNs 的附属品”的关键桥接来源。它可用来支撑本章的方法树，把数据同化、机理校正、残差补偿、代理模型等多种路线组织成系统化选择空间。

## 来源 4：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑方法选型不能只看精度，还需看验证、监督与风险管理条件。

### 可直接支持的关键表述

> Understanding and managing the risks of AI systems will help to enhance trustworthiness.

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

### 本章写作含义

该框架可帮助本章把“选型”从算法比较提升到部署治理比较。也就是说，一个方法即便在离线精度上更优，若验证成本过高、监督接口不足或部署风险不可控，也未必是更好的工程选择。

## 来源 5：代理模型/数字孪生相关领域来源（待补）

- 来源状态：待在第三轮精修前补充正式来源。
- 用途：支撑代理模型、快速替代求解器与数字孪生中的混合建模角色。

### 本章写作含义

本章在讨论方法选择树时，需要把代理模型与工程应用更紧密地连接起来。第三轮精修时应补入至少一条领域来源，以增强“部署成本”和“在线推理约束”维度的说服力。

## 小结

本章当前已具备“PINNs 代表方法 + PIML 总述 + 混合建模综述 + 风险治理框架 + 代理模型待补”的来源结构。下一步第三轮精修时，应重点补足代理模型来源，并把这些来源与选型指标表逐项对齐。

## References

[1]: https://www.sciencedirect.com/science/article/pii/S0021999118307125 "Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations"
[2]: https://www.nature.com/articles/s42254-021-00314-5 "Physics-informed machine learning"
[3]: https://www.nature.com/articles/s42256-020-00287-8 "Integrating physics-based modeling with machine learning"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
