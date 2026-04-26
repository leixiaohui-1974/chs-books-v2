# T5 第6章来源笔记

## 来源 1：Artificial Intelligence Risk Management Framework (AI RMF 1.0)

- 来源链接：<https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf>
- 用途：支撑高风险 AI 的部署前治理、风险分级、监督设计与可信性管理。

### 可直接支持的关键表述

> Understanding and managing the risks of AI systems will help to enhance trustworthiness.

> Governance structures are needed to define roles, responsibilities, and lines of communication for human-AI configurations and oversight of AI systems.

### 本章写作含义

该框架适合作为本章部署闸门的总体治理锚点。它能帮助本章说明：所谓“运行可信”并不是单一技术属性，而是风险分级、监督设计、验证证据和责任结构共同作用的结果。

## 来源 2：Article 14: Human Oversight | EU Artificial Intelligence Act

- 来源链接：<https://artificialintelligenceact.eu/article/14/>
- 用途：支撑 human oversight、覆盖输出、停止系统与按风险和 autonomy 配置监督措施等要求。

### 可直接支持的关键表述

> The oversight measures shall be commensurate with the risks, level of autonomy and context of use of the high-risk AI system.

> Natural persons ... are enabled ... to decide ... not to use the high-risk AI system or to otherwise disregard, override or reverse the output.

> Natural persons ... are enabled ... to intervene in the operation of the high-risk AI system or interrupt the system.

### 本章写作含义

这些条文非常适合支撑本章的部署闸门逻辑：部署不是“装上系统”，而是确认系统在既定上下文、既定 autonomy 和既定监督条件下可以被放行，并且一旦越界能够被覆盖、停止和回退。

## 来源 3：ODD 相关正式来源（待补）

- 来源状态：待第三轮精修前补入正式来源。
- 用途：支撑 Operational Design Domain 的正式定义，以及运行域并非应用标签、而是边界条件集合这一判断。

### 本章写作含义

ODD 是本章最关键而当前外部来源最薄弱的部分之一。第三轮精修时应优先补入自动驾驶或其他安全关键系统中的 ODD 正式来源，用于支撑“对象、工况、传感、组织条件共同定义运行域”的表述。

## 来源 4：xIL/HIL 验证来源（待补）

- 来源状态：待第三轮精修前补入正式来源。
- 用途：支撑在环验证、接口一致性验证、软硬件联调与部署前闸门。

### 本章写作含义

本章要把“从方法有效到运行可信”的闸门讲清楚，就必须解释 xIL/HIL 在验证链中的位置。第三轮精修时应补入至少一条能说明为什么离线通过不代表现场可放行的 xIL/HIL 来源。

## 来源 5：安全包络 / safety envelope / safety case 相关来源（待补）

- 来源状态：待第三轮精修前补入正式来源。
- 用途：支撑安全包络如何定义动作边界、状态边界、时间边界和授权边界，以及如何形成安全论证。

### 本章写作含义

本章提出“安全包络不是事后加的保险层”，这一判断需要更强的外部锚点。第三轮精修时应补入 safety envelope 或 safety case 相关来源，以增强“包络是运行结构的一部分”这一论证。

## 小结

本章当前已经形成“高风险 AI 治理框架 + human oversight 法规 + ODD 待补 + xIL/HIL 待补 + 安全包络待补”的来源结构。下一步第三轮精修时，应将后三类来源优先补齐，因为它们决定本章能否从内部平台语言提升为更具规范硬度的部署方法论。

## References

[1]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[2]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
