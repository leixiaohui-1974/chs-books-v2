# T5-Intelligence 卷核心参考文献标准库（2026-04-26 草案）

> **用途**：供 T5-Intelligence 前六章第三轮精修统一调用。凡涉及物理信息学习、方法选择树、安全强化学习、xIL/HIL、ODD、safety case、safety envelope、部署分级与运行资格等命题时，应优先使用本库中的标准条目与固定表述。
>
> **适用原则**：本文件为卷级 canonical references，不等同于最终文后参考文献。各章可调整编号，但条目元数据、题名译法与用途说明应保持一致。

---

## T5-L1 — AI 风险治理母框架

Tabassi, E. *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*. NIST AI 100-1. National Institute of Standards and Technology, 2023. DOI: 10.6028/NIST.AI.100-1.

**建议中文指称**：NIST《人工智能风险管理框架（AI RMF 1.0）》。

**主要用途**：支撑 T5 第1章、第5章、第6章关于可信 AI、风险治理、部署责任和运行期管理的框架性叙述。

## T5-L2 — ODD 风险边界框架

Cho, H. *Operational Design Domain (ODD) Framework for Driver-Automation Integrated Systems*. Massachusetts Institute of Technology, 2020.

**建议中文指称**：ODD（运行设计域）框架研究。

**主要用途**：支撑 T5 第1章和第6章关于 ODD 的正式定义、边界条件、风险阈值与 ODD 管理。

**正文优先引用要点**：

1. ODD 定义了自动化系统被设计为发挥功能的条件；
2. ODD 可被写成与风险阈值相关的条件超空间边界；
3. ODD 一经定义，仍需通过系统或人工进行管理，防止超域运行。

## T5-L3 — XIL / HIL 验证链

Abboush, M., Knieke, C., & Rausch, A. *A Virtual Testing Framework for Real-Time Validation of Automotive Software Systems Based on Hardware in the Loop and Fault Injection*. Sensors, 2024, 24(12): 3733. DOI: 10.3390/s24123733.

**建议中文指称**：基于 HIL 与故障注入的实时验证框架。

**主要用途**：支撑 T5 第4章至第6章关于 MiL、SiL、PiL、HiL、ViL 组成的 xIL 验证链，以及部署前 assurance 的获取方式。

**正文优先引用要点**：

1. 安全相关软件在 V-model 各阶段开展 XIL 测试；
2. MiL、SiL、PiL、HiL、ViL 共同组成分阶段验证链；
3. HIL 与 fault injection 适合在低成本条件下检验关键异常工况与系统响应。

## T5-L4 — Safety Case 模板

Bloomfield, R., Fletcher, G., Khlaaf, H., Hinde, L., & Ryan, P. *Safety Case Templates for Autonomous Systems*. arXiv, 2021. DOI: 10.48550/arXiv.2102.02625.

**建议中文指称**：自主系统 safety case 模板。

**主要用途**：支撑 T5 第5章和第6章关于部署闸门、安全论证、危险分析、安全监控架构、随时间变化适配等内容。

## T5-L5 — Safe RL / CPO 经典条目

Achiam, J., Held, D., Tamar, A., & Abbeel, P. *Constrained Policy Optimization*. arXiv, 2017. DOI: 10.48550/arXiv.1705.10528.

**建议中文指称**：约束策略优化（CPO）。

**主要用途**：支撑 T5 第4章“安全约束进入优化过程”的核心命题。

**正文优先引用要点**：

1. 强化学习很多场景需要同时指定 reward 与 constraints；
2. 与人或环境发生物理交互的系统应满足安全约束；
3. CPO 旨在每次迭代中实现近似约束满足。

## T5-L6 — Safety Envelope / RSS 扩展

Bernhard, J., Hart, P., Sahu, A., Schöller, C., & Guzman Cancimance, M. *Risk-Based Safety Envelopes for Autonomous Vehicles Under Perception Uncertainty*. arXiv, 2021. DOI: 10.48550/arXiv.2107.09918.

**建议中文指称**：感知不确定性下的风险型安全包络。

**主要用途**：支撑 T5 第6章关于 safety envelope、RSS、感知不确定性、风险阈值与运行边界的正式表述。

**正文优先引用要点**：

1. safety envelope 可在感知不确定性下用概率方法计算；
2. 该包络以 risk threshold 为基础；
3. 该方法将非概率型 RSS 扩展到不确定性情景。

## T5-L7 — Human Oversight 的法规约束

European Union. *Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act), Article 14: Human Oversight*. Official Journal of the European Union, 2024. Online text: https://artificialintelligenceact.eu/article/14/ .

**建议中文指称**：欧盟《人工智能法案》第14条：人工监督。

**主要用途**：支撑 T5 第5章和第6章关于部署分级、人工确认、override / reverse / stop 与安全状态回退的制度要求。

---

## 推荐映射关系（按章节）

| 章节 | 建议优先 canonical refs | 备注 |
|---|---|---|
| ch01 | T5-L1, T5-L2 | 建立卷入口的风险治理与运行边界框架 |
| ch02 | T5-L1 | 物理信息学习的可信与治理前提 |
| ch03 | T5-L1 | 方法树的选择与治理视角 |
| ch04 | T5-L3, T5-L5 | 安全强化学习与验证链 |
| ch05 | T5-L1, T5-L4, T5-L7 | 验证闭环、部署分级、治理收口 |
| ch06 | T5-L2, T5-L3, T5-L4, T5-L6, T5-L7 | 形成 ODD—xIL—safety case—safety envelope—human oversight 的五层引用链 |

---

## 常见错误模式（当前应避免）

| 错误模式 | 风险 | 纠正方式 |
|---|---|---|
| 将 ODD 写成业务清单或场景目录 | 丢失运行边界与风险阈值含义 | 按 T5-L2 统一改写为条件集合与边界管理 |
| 将 xIL 仅写成测试术语罗列 | 无法形成 assurance chain | 用 T5-L3 回写 MiL→SiL→PiL→HiL→ViL 的递进链 |
| 将 safety case 写成“安全说明” | 无法体现论证结构 | 明确其为要求、危害分析、监控架构、证据可信度的组织框架 |
| 将 safe RL 简化为“更安全的 RL” | 学理强度不足 | 通过 T5-L5 明确约束进入优化过程 |
| 将 safety envelope 写成模糊安全边界 | 缺乏形式化基础 | 通过 T5-L6 补入 risk threshold、RSS 与不确定性感知表述 |

---

## 第三轮精修待办

1. 为 ch04、ch05、ch06 回填 3—6 处正文显式引用。
2. 按 T5-L2 至 T5-L7 的链条重写第6章的收口结构，使其更像教材化专著章节而非扩展长文。
3. 形成卷级 `references_t5_front_half.md` 或等效文后参考文献文件。
4. 把图表治理文件中的关键图件与本标准库逐一绑定，补充图注来源说明。

---

## References

[1]: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10 "Artificial Intelligence Risk Management Framework (AI RMF 1.0) | NIST"
[2]: https://dspace.mit.edu/handle/1721.1/129156 "Operational Design Domain (ODD) framework for driver-automation integrated systems"
[3]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11207294/ "A Virtual Testing Framework for Real-Time Validation of Automotive Software Systems Based on Hardware in the Loop and Fault Injection"
[4]: https://arxiv.org/abs/2102.02625 "Safety Case Templates for Autonomous Systems"
[5]: https://arxiv.org/abs/1705.10528 "Constrained Policy Optimization"
[6]: https://arxiv.org/abs/2107.09918 "Risk-Based Safety Envelopes for Autonomous Vehicles Under Perception Uncertainty"
[7]: https://artificialintelligenceact.eu/article/14/ "Article 14: Human Oversight | EU Artificial Intelligence Act"
