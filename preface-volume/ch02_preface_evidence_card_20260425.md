# 章节证据卡

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 章节编号 | 总序卷第2章 |
| 章节标题 | CHS 与水系统运行对象 |
| 所属卷册 | 总序卷《自主运行水网导论：对象、层级、智能与治理》 |
| 目标读者 | 水利工程研究生、控制与自动化研究者、平台架构设计者、行业技术管理者 |
| 与前后章节关系 | 前承第1章“大水网时代与运行能力问题”，把问题提出升级为对象定义；后续为第3章或第4章关于 CPSS、复合运行对象、双引擎与治理边界提供统一对象语言。 |

## 2. 核心命题

| 序号 | 核心命题 | 命题类型 | 预期证据等级 | 当前状态 |
|---|---|---|---|---|
| 1 | CHS 研究的不是孤立水工设施，而是由物理水网、信息基础设施、认知执行网络与人类组织共同构成的水系统运行对象。 | 定义 | Tier 2 | 需升级 |
| 2 | 传统控制对象、数字化控制对象与复合运行对象之间的差异，不在“有没有数字化”，而在对象边界、动作集合和组织接口是否被纳入统一运行闭环。 | 理论 | Tier 2 | 需升级 |
| 3 | 若不先重构对象定义，后续关于物理 AI、认知 AI、Agent、WNAL、ODD 与平台架构的讨论都会失去共同落点。 | 理论 | Tier 3 | 待补 |
| 4 | 第2章应把运行对象表达为状态集合、控制集合、观测集合、扰动集合和约束集合，从而把 CHS 从纲领性语言推进为可教学语言。 | 方法 | Tier 2 | 需升级 |
| 5 | 水系统对象边界进入“物理—信息—社会/组织”耦合阶段后，运行能力问题天然具有 CPSS 或 CPHS 特征，但 CHS 仍需给出面向水系统运行的专门对象重构。 | 理论 | Tier 1-2 | 待补 |

## 3. 必引经典文献

| 序号 | 文献 | 作用 | 是否已纳入 |
|---|---|---|---|
| 1 | Norbert Wiener, *Cybernetics: Or Control and Communication in the Animal and the Machine*（MIT Press 页面） | 理论起点与“控制/通信”历史锚点 | 否 |
| 2 | *A Holistic Review of Cyber–Physical–Social Systems: New Directions and Opportunities* | 用于支持 CPSS 三空间边界与复杂系统特征 | 是 |
| 3 | *Cyber-physical systems in water management and governance* | 用于支撑水管理对象已具备 CPS 乃至更复杂基础设施属性 | 否 |
| 4 | *Evolution of cyber-physical-human water systems* | 用于支撑水务系统对象已进入 cyber-physical-human 耦合阶段 | 否 |
| 5 | `/home/ubuntu/hcogs_framework_and_restructuring.md` | 内部材料，用于统一总序卷与平台/对象层叙述 | 是 |
| 6 | `/mnt/desktop/desktop/hydrosis-local/research/chs-books-v2/CHS_术语规范_全系列.md` | 术语边界、命名一致性与对象语言约束 | 否 |

## 4. 证据来源计划

| 章节小节 | 关键论断 | 需要的来源类型 | 候选来源 | 风险备注 |
|---|---|---|---|---|
| 2.1 为什么必须重构对象 | 水系统控制对象已从单体设施扩展为网络化运行对象 | 官方文档、综述、内部材料 | 第1章已收集的国家水网来源；HCogS 总框架文档 | 需避免把“背景变化”直接等同于“对象定义完成” |
| 2.2 从传统对象到数字化对象 | 仅有 SCADA/模型/平台并不自动构成复合运行对象 | 综述、工程方法文献 | 开敞渠系建模控制综述、MPC 水资源系统综述 | 需防止章节滑向方法史综述 |
| 2.3 从 CPS/CPSS/CPHS 到 CHS 对象语言 | 水系统对象已跨越纯物理边界，但现有框架仍不足以直接替代 CHS 的专门对象定义 | 原始论文、综述 | CPSS 综述；water management and governance 的 CPS 文献；cyber-physical-human water systems 文献 | 需明确“借鉴”与“替代”的边界 |
| 2.4 运行对象的集合表达 | 需要给出状态、控制、观测、扰动、约束集合及其层次关系 | 原始论文、教材原典、内部方法文档 | Wiener 历史原典；控制系统标准表达；术语规范；总纲与章纲 | 公式需与后续章节兼容，不能写死过细工程细节 |
| 2.5 为什么对象定义决定后续全书结构 | 后续双引擎、治理和平台都依赖统一对象语言 | 内部材料、章纲、平台架构文档 | HCogS 总框架文档；正式章纲草案；HydroWriter 配置 | 需确保论证扎实，不仅是目录解释 |

## 5. 图表公式计划

| 元素编号 | 类型 | 主题 | 来源状态 | 预期来源/说明 |
|---|---|---|---|---|
| Fig-1 | 图 | 传统控制对象—数字化控制对象—复合运行对象三层对比图 | 自制 | 依据本章对象重构逻辑制作总图 |
| Tab-1 | 表 | 运行对象四层要素表（物理水网、信息基础设施、认知执行网络、人类组织） | 汇编 | 依据术语规范、章纲和本章定义整理 |
| Eq-1 | 公式 | 水系统运行对象的集合表达：状态、控制、观测、扰动、约束 | 推导 | 作为全书统一对象语言的第一版正式表达 |
| Fig-2 | 图 | 对象边界与闭环接口关系图 | 自制/改绘 | 用于说明感知、推理、执行、治理与人工接管接口 |
| Tab-2 | 表 | 传统对象、CPS/CPSS/CPHS、CHS 对象语言差异表 | 汇编 | 用于避免概念混用 |

## 6. 证据缺口

| 序号 | 问题 | 影响范围 | 解决动作 |
|---|---|---|---|
| 1 | Wiener 历史原典尚未补入可直接引用页面 | 第2章理论起点 | 下一步补检并摘录 MIT Press 或权威页面 |
| 2 | 水系统进入 CPHS/CPSS 阶段的专门综述尚未打开阅读全文 | 第2章边界论证 | 下一步打开候选论文，提取关键定义与边界表述 |
| 3 | 第2章公式语言尚未与全系列术语规范逐项对齐 | 公式与后续章节一致性 | 写作前重读术语规范并锁定变量命名 |
| 4 | 图表任务尚未细化为单独绘图提示卡 | 后续插图执行 | 在第2章初稿完成后同步生成图表任务文件 |

## 7. 审核结论

> 本章已经具备进入正式写作前的初步证据条件，但尚未具备最终定稿条件。当前结论为：**是，可以进入正式写作；但必须在写作过程中同步补齐 Wiener 历史锚点、水系统 CPHS/CPSS 文献摘录与变量命名一致性校核。**

## References

[1]: https://www.mdpi.com/1424-8220/23/17/7391 "A Holistic Review of Cyber–Physical–Social Systems: New Directions and Opportunities"
[2]: https://www.sciencedirect.com/science/article/pii/S1877343523000374 "Cyber-physical systems in water management and governance"
[3]: https://www.sciencedirect.com/science/article/pii/S0040162523002251 "Evolution of cyber-physical-human water systems"
[4]: file:///home/ubuntu/hcogs_framework_and_restructuring.md "水系统运行智治体系的总框架图、教材重构目录和平台命名分层表"
[5]: file:///home/ubuntu/chs_books_formal_outline_draft_20260425.md "chs-books-v2 正式书稿级章纲深化草案"
