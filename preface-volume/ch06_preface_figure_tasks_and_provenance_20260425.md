# 图表公式来源追踪表

| 编号 | 元素类型 | 所属章节 | 标题/主题 | 来源状态 | 原始来源 | 改绘/汇编说明 | 中文标注是否统一 | 科学性复核状态 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| Fig-1 | 图 | 总序卷第6章 | WNAL、ODD、xIL 与安全包络关系图 | 自制 | 第6章正文、第6章证据卡、CHS术语规范、人机在环自主 CPS 设计文献、机器人系统验证综述[1] [2] [3] [4] | 自制主图，展示自主等级、适用边界、验证链和运行授权之间的逻辑顺序。 | 是 | 通过 | 本图是第6章总图，应与第4章双引擎图和第5章工作代理闭环图保持接口一致。 |
| Fig-2 | 图 | 总序卷第6章 | 从 MIL/SIL/HIL/OIL 到在线运行的验证递进图 | 自制 | 第6章正文、CHS术语规范、xIL/V&V 综述[1] [4] | 以时间轴与保真度双维展示验证层级递进关系，并标出人工接管和回退节点。 | 是 | 通过 | 可复用于 T3 工程标准卷。 |
| Tab-1 | 表 | 总序卷第6章 | WNAL L0-L5 与执行权、监督权、接管权对照表 | 汇编 | 第6章正文、CHS术语规范、第6章证据卡 | 汇编本书统一等级语言，明确各等级的社会—网络决策权分配。 | 是 | 通过 | 用于支撑第6章核心表。 |
| Tab-2 | 表 | 总序卷第6章 | ODD 六维边界与典型失配触发条件表 | 汇编 | CHS术语规范、PAS1883 ODD 规范页面、第6章来源笔记[2] [5] | 依据六维 ODD 定义整理触发条件，统一“边界—监测—动作”三列结构。 | 是 | 通过 | 需在定稿前再次核对标准化措辞。 |
| Eq-1 | 公式 | 总序卷第6章 | 授权等级—边界满足度—验证充分性联合判据 | 推导 | 第6章正文、术语规范、第6章证据卡 | 用结构式表达“等级授权不是能力宣称，而是边界满足与证据充分性的联合结果”。 | 不适用 | 通过 | 可作为后续案例评估体系公式入口。 |

## 图表任务说明

| 任务编号 | 对应元素 | 任务内容 | 执行优先级 | 当前状态 |
|---|---|---|---|---|
| T6-F1 | Fig-1 | 绘制 WNAL、ODD、xIL 与安全包络逻辑关系图，明确“边界定义—验证递进—等级授权—越界回退”的主链。 | 高 | 待绘制 |
| T6-F2 | Fig-2 | 绘制 MIL/SIL/HIL/OIL 到在线运行的验证递进图，并标出人工接管、降级与最小风险状态的触发点。 | 高 | 待绘制 |
| T6-T1 | Tab-1 | 汇编 WNAL L0-L5 权责对照表，统一社会监督、网络决策与人工接管的术语表达。 | 高 | 待排版 |
| T6-T2 | Tab-2 | 整理 ODD 六维边界与失配条件表，形成边界治理的最小标准表。 | 高 | 待排版 |
| T6-E1 | Eq-1 | 整理授权等级—边界满足度—验证充分性联合判据，用于衔接后续工程评估与认证表达。 | 中 | 待精修 |

## 参考来源

[1]: https://www.sciencedirect.com/science/article/pii/S1071581919300461 "Human-in-the-loop autonomous CPS design paper"
[2]: https://hal.science/hal-04613329v1/document "ODD risk-oriented definition document"
[3]: file:///mnt/desktop/desktop/hydrosis-local/research/chs-books-v2/CHS_术语规范_全系列.md "CHS 全系列术语统一规范"
[4]: https://www.mdpi.com/2218-6581/10/2/67 "A Review of Verification and Validation for Intelligent and Autonomous Robot Systems"
[5]: https://www.bsigroup.com/globalassets/localfiles/en-gb/cav/pas1883.pdf "PAS1883 Operational Design Domain standard PDF"
[6]: file:///home/ubuntu/chs_books_preface_ch06_evidence_card_20260425.md "总序卷第6章证据卡"
