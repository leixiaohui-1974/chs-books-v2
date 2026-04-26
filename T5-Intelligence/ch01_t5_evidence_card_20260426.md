# 章节证据卡

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 章节编号 | T5-Intelligence 第1章 |
| 章节标题 | 水利AI的特殊性：为什么通用算法在水网中失效 |
| 所属卷册 | T5《水网智能决策：算法、视觉与安全》 |
| 目标读者 | 水利 AI 算法研发人员、系统架构师、研究生、运行智能平台建设者 |
| 与前后章节关系 | 本章作为整卷导论，负责解释为什么水利 AI 不能简单照搬通用算法范式，并提出 PIA（物理约束驱动 AI）的四层方法论；后续章节将分别展开物理约束学习、安全强化学习、视觉感知、多模态融合与验证治理。 |

## 2. 核心命题

| 序号 | 核心命题 | 命题类型 | 预期证据等级 | 当前状态 |
|---|---|---|---|---|
| 1 | 水利 AI 面临数据统计特殊性、物理硬约束与关键基础设施安全属性三类根本挑战，因此评价逻辑不同于通用 AI。 | 定义/结构 | Tier 2-3 | 待补 |
| 2 | 通用算法在水网中的失败并非偶发 bug，而是训练分布、物理边界和安全责任错位的系统结果。 | 方法/失效分析 | Tier 2-3 | 待补 |
| 3 | PIA 不是单一算法，而是从数据、结构、损失到部署的全链条物理约束嵌入方法论。 | 方法论 | Tier 2-3 | 待补 |
| 4 | 水利 AI 的第一任务不是更聪明，而是更守边界；高分模型不等于可部署系统。 | 治理/工程 | Tier 1-2 | 待补 |
| 5 | ODD、安全包络、人机协同、验证门禁与离线生存能力必须从导论开始进入算法评价框架。 | 治理/工程 | Tier 1-2 | 待补 |

## 3. 必引经典文献

| 序号 | 文献 | 作用 | 是否已纳入 |
|---|---|---|---|
| 1 | Karniadakis et al., *Physics-informed machine learning* | 作为 PIA/PIML 总体方法论锚点 | 是 |
| 2 | Raissi et al., *Physics-informed neural networks* | 作为将 PDE 与神经网络耦合的代表性方法锚点 | 是 |
| 3 | NIST AI RMF 1.0 | 作为高风险 AI 风险治理、监督与责任结构锚点 | 否 |
| 4 | EU AI Act Article 14 | 作为 human oversight 与高风险系统边界控制的规范锚点 | 否 |
| 5 | Mussi et al., *Human-AI interaction in safety-critical network infrastructures* | 作为安全关键网络基础设施中人机协同与接管设计的桥接来源 | 是 |

## 4. 证据来源计划

| 章节小节 | 关键论断 | 需要的来源类型 | 候选来源 | 风险备注 |
|---|---|---|---|---|
| 1.1 水利 AI 的特殊性 | 三类挑战共同重写 AI 的问题定义 | PIML 综述/安全关键系统来源/治理框架 | Karniadakis et al.; Mussi et al.; NIST AI RMF | 需避免把“行业特殊”写成空泛口号 |
| 1.2 数据特殊性 | 极端事件稀缺、时空耦合、传感器失效与非平稳性破坏 i.i.d. 假设 | 水文学/水利数据建模/PIML 综述 | Karniadakis et al.; 水文 OOD 与极值理论来源 | 需在第三轮精修时增加更直接的水文统计来源 |
| 1.3 物理约束性 | Saint-Venant、守恒关系、设备边界和生态约束是硬边界而非软偏好 | PINNs/PDE 约束来源/工程约束来源 | Raissi et al.; Karniadakis et al. | 需区分 PDE 约束与工程运行约束的层次 |
| 1.4 安全可靠性 | 关键基础设施不能沿用互联网式试错容忍逻辑 | 安全关键基础设施/治理框架/法规 | Mussi et al.; NIST AI RMF；EU AI Act | 需补强离线生存与边缘生存的工程来源 |
| 1.5 三类失效链 | 失效链是问题定义错位的结果 | 案例综述/安全学习来源/视觉鲁棒性来源 | OOD 水文建模来源；DRL sim-to-real 来源；视觉测流鲁棒性来源 | 失效链中有较强作者归纳成分，需明确 |
| 1.6 PIA 四层方法论 | PIA 是数据、结构、损失、部署四层嵌入框架 | PIML 总述/作者归纳 | Karniadakis et al.; Raissi et al. | 四层划分需标明为作者组织框架 |

## 5. 图表公式计划

| 元素编号 | 类型 | 主题 | 来源状态 | 预期来源/说明 |
|---|---|---|---|---|
| Fig-1 | 图 | 通用 AI 与水利 AI 问题定义差异图 | 自制 | 用于导论章建立“更守边界”总判断 |
| Tab-1 | 表 | 三类根本挑战与对应工程后果对照表 | 汇编 | 依据本章正文整理，为全卷提供入口表 |
| Fig-2 | 图 | 三类失效链总览图 | 自制 | 应并列展示 OOD、Sim-to-Real 和视觉假设崩溃 |
| Fig-3 | 图 | PIA 四层方法论图 | 自制 | 将成为全卷算法主线总图 |
| Box-1 | 案例框 | “智能之眼失灵”导入案例 | 自制/待核 | 用于说明通用算法失效不是偶发误差 |

## 6. 证据缺口

| 序号 | 问题 | 影响范围 | 解决动作 |
|---|---|---|---|
| 1 | 数据特殊性部分当前更多依赖导论性叙述，缺少更直接的水文 OOD 与极值建模来源 | 1.2 | 后续补检索水文极端事件、OOD hydrology、sensor failure 来源 |
| 2 | 安全可靠性部分需要更硬的治理规范锚点 | 1.4 | 补纳入 NIST AI RMF 与 EU AI Act Article 14 |
| 3 | PIA 四层框架是整卷核心结构，但其作者归纳属性尚需与外部来源边界写清 | 1.6 | 在来源笔记中区分“直接来源”与“章节归纳” |
| 4 | PIA 总图与失效链总图尚未固化，将影响后续章节接口 | 全章图表 | 优先完成图表治理任务卡 |

## 7. 审核结论

> 本章已经具备成为整卷问题定义总开关的条件。其核心价值不在于提出若干新算法，而在于重写算法评价逻辑：从平均分数转向边界守护、从纯预测转向物理一致、从模型能力转向高风险部署能力。第三轮精修时，应继续补强水文 OOD、边缘生存和治理规范三类外部来源，以提高导论章的证据硬度。

## 8. 第三轮精修前置建议

第三轮精修时，本章应优先完成三项工作。第一，把 PIA 四层方法论图稳定下来，因为它将贯穿全卷。第二，把三类失效链由案例化语言进一步压缩成可教学的结构图。第三，在安全可靠性部分把 NIST AI RMF、EU AI Act 与 Mussi 等人机协同来源显式并列，从一开始就树立“算法—治理一体化”的评价框架。

## References

[1]: https://www.nature.com/articles/s42254-021-00314-5 "Physics-informed machine learning"
[2]: https://www.sciencedirect.com/science/article/pii/S0021999118307125 "Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations"
[3]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
[4]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
