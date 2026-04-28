# 章节证据卡

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 章节编号 | T5-Intelligence 第2章 |
| 章节标题 | 机理嵌入不是装饰：为什么物理信息学习是水利 AI 的必要条件 |
| 所属卷册 | T5《水网智能决策：算法、视觉与安全》 |
| 目标读者 | 水利 AI 算法研发人员、机理模型研究者、研究生 |
| 与前后章节关系 | 本章承接第1章提出的 PIA 导论，进一步说明为什么物理信息学习不是锦上添花，而是水利 AI 可部署性的基本前提；后续第3章会从 PINNs 扩展到更完整的混合建模选择树。 |

## 2. 核心命题

| 序号 | 核心命题 | 命题类型 | 预期证据等级 | 当前状态 |
|---|---|---|---|---|
| 1 | 在水利场景中，机理嵌入的价值不在于提升论文精度，而在于防止模型在边界工况下脱离物理世界。 | 方法/工程 | Tier 2-3 | 待补 |
| 2 | 物理信息学习可以在数据、结构、损失与后处理多个层面嵌入，而不是只有 PINNs 一种形态。 | 方法论 | Tier 2-3 | 待补 |
| 3 | 守恒关系、拓扑约束、设备边界与规程限制共同构成水利 AI 的多层物理—工程约束。 | 定义/工程 | Tier 2-3 | 待补 |
| 4 | 机理嵌入是提高 OOD 稳定性、解释性与审计能力的必要条件，但不是自动保证正确的充分条件。 | 方法/治理 | Tier 2-3 | 待补 |
| 5 | 第2章的关键任务是把“为什么需要物理信息学习”说清，而不是直接进入算法细节堆砌。 | 结构 | Tier 3 | 待补 |

## 3. 必引经典文献

| 序号 | 文献 | 作用 | 是否已纳入 |
|---|---|---|---|
| 1 | Karniadakis et al., *Physics-informed machine learning* | 支撑 PIML 的总体框架与方法族 | 是 |
| 2 | Raissi et al., *Physics-informed neural networks* | 支撑 PDE 约束嵌入学习的典型代表 | 是 |
| 3 | Willard et al., *Integrating physics-based modeling with machine learning* | 支撑物理—数据融合的更广义方法视角 | 否 |
| 4 | NIST AI RMF 1.0 | 支撑物理一致性与部署风险之间的治理关系 | 否 |
| 5 | Saint-Venant 方程相关教材/水力学来源 | 支撑水位、流量与过程一致性的领域基础 | 否 |

## 4. 证据来源计划

| 章节小节 | 关键论断 | 需要的来源类型 | 候选来源 | 风险备注 |
|---|---|---|---|---|
| 2.1 为什么机理嵌入不是装饰 | 机理缺失会导致 OOD 崩溃和不可执行输出 | PIML 综述/PINNs/工程失效案例 | Karniadakis et al.; Raissi et al. | 需避免只停留在抽象原则层 |
| 2.2 机理嵌入的多层方式 | 数据、结构、损失、后处理均可嵌入机理 | PIML 综述/融合建模综述 | Karniadakis et al.; Willard et al. | 需与第1章 PIA 四层框架术语对齐 |
| 2.3 多层约束来源 | 守恒、拓扑、设备、规程共同构成边界 | 水力学/工程约束/平台实践 | Saint-Venant 基础来源；运行规程；平台经验 | 需明确哪些是作者归纳 |
| 2.4 机理嵌入的边界 | 物理约束是必要条件但不是充分条件 | PIML 来源/治理框架 | Karniadakis et al.; NIST AI RMF | 需防止把物理信息学习神化 |

## 5. 图表公式计划

| 元素编号 | 类型 | 主题 | 来源状态 | 预期来源/说明 |
|---|---|---|---|---|
| Fig-1 | 图 | 机理嵌入四层方式图 | 自制 | 与第1章 PIA 总图呼应，但聚焦机理嵌入 |
| Tab-1 | 表 | 物理约束、工程约束、制度约束对照表 | 汇编 | 作为本章最重要的教材表 |
| Fig-2 | 图 | 无机理/弱机理/强机理模型对照图 | 自制 | 用于说明边界工况下的差异 |
| Box-1 | 案例框 | “高分但物理无效”的预测案例 | 自制/待核 | 强调机理嵌入的必要性 |

## 6. 证据缺口

| 序号 | 问题 | 影响范围 | 解决动作 |
|---|---|---|---|
| 1 | 当前仍缺一条更广义的物理—数据融合综述来源 | 2.2 | 补纳入 Willard et al. 等综述 |
| 2 | 水力学基础方程与工程约束的领域来源尚未正式纳入 | 2.3 | 第三轮精修时补充水力学教材或权威水文水力来源 |
| 3 | 本章需要防止“机理嵌入万能化”表述 | 2.4 | 在来源笔记中显式写出必要但不充分 |

## 7. 审核结论

> 本章承担的是整卷方法论转向的关键一步：把“需要物理信息学习”从口号变成结构性判断。当前支撑框架已具雏形，但第三轮精修仍需补入更广义的融合建模综述与更硬的领域基础来源，以提高这一章的教材硬度和跨学科说服力。

## 8. 第三轮精修前置建议

第三轮精修时，本章应优先完成三项工作。第一，稳定“机理嵌入四层方式图”，使其与第1章 PIA 总图无缝衔接。第二，把物理约束、工程约束、制度约束三层边界清晰区分。第三，为“必要但不充分”这一判断增加更显式的失败案例或对照表述。

## References

[1]: https://www.nature.com/articles/s42254-021-00314-5 "Physics-informed machine learning"
[2]: https://www.sciencedirect.com/science/article/pii/S0021999118307125 "Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations"
[3]: https://www.nature.com/articles/s42256-020-00287-8 "Integrating physics-based modeling with machine learning"
[4]: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf "Artificial Intelligence Risk Management Framework (AI RMF 1.0)"
