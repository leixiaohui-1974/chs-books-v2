# T5 第1章来源笔记

## 来源 1：Physics-informed machine learning

- 来源链接：<https://www.nature.com/articles/s42254-021-00314-5>
- 用途：支撑物理约束驱动 AI、物理与数据融合学习、守恒约束与结构先验等总体论断。

### 可直接支持的关键表述

该综述系统讨论了物理约束、机理知识与数据驱动学习的融合方式，是本章提出 PIA 方法论的最重要外部锚点之一。它能够支撑“物理知识不应只在训练后做校验，而应被前移到模型设计与学习过程中”这一中心判断。

### 本章写作含义

本章可以借此说明：水利 AI 与通用 AI 的关键分界，不在于是否使用神经网络，而在于是否把对象世界的刚性约束纳入模型生命周期。PIA 的四层框架可据此建立外部桥接基础。

## 来源 2：Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations

- 来源链接：<https://www.sciencedirect.com/science/article/pii/S0021999118307125>
- 用途：支撑 PDE 约束、物理残差、守恒和方程嵌入学习结构等表述。

### 可直接支持的关键表述

该文是 PINNs 的代表性来源，适合作为本章在讨论 Saint-Venant 方程、过程一致性与物理残差时的典型方法锚点。它有助于说明为什么“方程不是建议，而是可进入损失函数与网络结构的硬约束来源”。

### 本章写作含义

本章可借此把物理约束性从原则性表述进一步落到方法层面，为后续物理 AI、约束学习和安全学习章节预先建立技术入口。

## 来源 3：Human-AI interaction in safety-critical network infrastructures

- 来源链接：待补精确链接（当前依据书稿既有文献条目，后续需在第三轮精修前补齐正式 URL）
- 用途：支撑安全关键网络基础设施中的人机协同、接管设计与责任要求。

### 本章写作含义

该来源在本章中主要承担“从算法问题过渡到安全关键系统问题”的桥接作用。尤其在讨论后果不对称性、可解释性作为责任要求以及人机协同边界时，该来源可帮助把水利 AI 放回关键基础设施语境，而不是把其视为一般数字产品。

## 来源 4：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑高风险 AI 风险管理、角色责任、监督与过度依赖防范。

### 可直接支持的关键表述

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

> AI risk management efforts should consider that humans may over-rely on AI outputs.

### 本章写作含义

该框架非常适合支撑本章“高分模型不等于可部署系统”的判断。它可以把本章关于安全可靠性、接管、验证门禁和离线生存的讨论，从工程直觉提升到治理框架层面。

## 来源 5：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑 human oversight、能力边界理解、覆盖输出、停止系统与不过度依赖的法规要求。

### 可直接支持的关键表述

> Human oversight shall aim to prevent or minimise the risks to health, safety or fundamental rights.

> Natural persons ... are enabled ... to properly understand the relevant capacities and limitations of the high-risk AI system.

> Natural persons ... are enabled ... to intervene in the operation of the high-risk AI system or interrupt the system.

### 本章写作含义

该条文能够把本章导论中的“人机协同与接管边界”写成硬约束，而不是主张式建议。它特别适合为后续卷中 ODD、验证门禁和授权治理章节预置规范语言。

## 小结

T5 第1章当前已经形成“PIML 总述 + PINNs 方法代表 + 安全关键基础设施人机协同 + 风险治理框架 + human oversight 法规”五层来源结构。第三轮精修前，应补齐来源 3 的正式链接，并进一步增补一条水文 OOD 或极值统计来源，以增强数据特殊性部分的证据密度。

## References

[1]: https://www.nature.com/articles/s42254-021-00314-5 "Physics-informed machine learning"
[2]: https://www.sciencedirect.com/science/article/pii/S0021999118307125 "Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations"
[3]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[4]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
