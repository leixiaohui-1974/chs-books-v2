# 章节证据卡

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 章节编号 | 总序卷第3章 |
| 章节标题 | CHS 与更上位框架：从 CPSS/CPHS 到水系统运行对象语言 |
| 所属卷册 | 总序卷《自主运行水网导论：对象、层级、智能与治理》 |
| 目标读者 | 水利工程研究生、控制与自动化研究者、平台架构设计者、行业技术管理者 |
| 与前后章节关系 | 前承第2章“CHS 与水系统运行对象”，把对象定义推进为边界解释；后续为第4章“物理 AI 与认知 AI 双引擎”、第5章“Agent、Skill 与工作代理”等章节提供统一的上位框架定位。 |

## 2. 核心命题

| 序号 | 核心命题 | 命题类型 | 预期证据等级 | 当前状态 |
|---|---|---|---|---|
| 1 | CPS、CPSS、CPHS 等框架揭示了现代水系统边界扩张的事实，但并不自动等于面向运行闭环的水系统对象语言。 | 理论 | Tier 1-2 | 需升级 |
| 2 | CPSS 适合作为总序卷的三空间屋顶视角，用于解释 Physical、Cyber、Social 的耦合关系。 | 定义 | Tier 2 | 需升级 |
| 3 | CPHS/CPH 视角提醒我们 human-social interactions 已经进入现代水系统对象内部，但其方法表达仍存在向工程闭环转译的缺口。 | 理论 | Tier 1-2 | 需升级 |
| 4 | CHS 的角色不是替代更上位框架，而是把这些上位框架转写为适用于水系统运行对象、控制闭环与治理边界的专门对象语言。 | 理论 | Tier 2-3 | 待补 |
| 5 | 若不在本章完成框架层级辨析，后续双引擎、Agent、WNAL、ODD 与平台章节将出现术语错位与边界混淆。 | 方法 | Tier 3 | 待补 |

## 3. 必引经典文献

| 序号 | 文献 | 作用 | 是否已纳入 |
|---|---|---|---|
| 1 | *A Holistic Review of Cyber–Physical–Social Systems: New Directions and Opportunities* | 作为 CPSS 屋顶框架与三空间复杂性来源的理论锚点 | 是 |
| 2 | *Evolution of cyber-physical-human water systems: Challenges and gaps* | 作为水系统进入 CPHS 阶段及其方法缺口的直接证据 | 是 |
| 3 | *Cyber-physical systems in water management and governance* | 作为从 CPS 过渡到社会/生态维度扩展的水管理证据 | 是 |
| 4 | 《自主运行水网的学科底座：水利-控制-AI 三方交叉与水系统控制论》 | 作为 CHS 在全书中的学科定位与边界转译依据 | 是 |
| 5 | `/mnt/desktop/desktop/hydrosis-local/research/chs-books-v2/CHS_术语规范_全系列.md` | 作为术语归口与本书内部框架一致性约束 | 否 |

## 4. 证据来源计划

| 章节小节 | 关键论断 | 需要的来源类型 | 候选来源 | 风险备注 |
|---|---|---|---|---|
| 3.1 为什么需要上位框架 | 水系统已超出传统受控物理对象，需要上位框架描述多空间耦合 | 综述、内部材料 | CPSS 综述、CPHS 水系统综述、学科篇内部材料 | 需避免把上位框架写成口号化总论 |
| 3.2 CPS 到 CPSS/CPHS 的边界变化 | social/human 进入对象边界并改变系统复杂性来源 | 原始论文、综述 | 水管理 CPS 论文、CPHS 水系统综述 | 需区分 social 与 human 的不同强调点 |
| 3.3 为什么 CHS 仍然必要 | 上位框架不能直接替代水系统运行对象语言 | 内部材料、术语规范、章节逻辑 | 学科篇内部材料、CHS 术语规范、第2章对象语言 | 需避免沦为自我宣示，必须给出清楚的“不能替代”的原因 |
| 3.4 框架分层表述 | 本书采用“CPSS 为上位视角、CHS 为专门对象语言”的层次关系 | 综述、内部材料、术语规范 | CPSS 综述、术语规范、HCogS 总框架 | 需确保后续章节可复用该表达 |
| 3.5 对后续全书的约束 | 双引擎、Agent、治理与平台章节都依赖框架层次辨析 | 内部材料、章纲 | 正式章纲、学科篇材料、HydroWriter 配置 | 风险在于可能写成目录解释，需保持论证性 |

## 5. 图表公式计划

| 元素编号 | 类型 | 主题 | 来源状态 | 预期来源/说明 |
|---|---|---|---|---|
| Fig-1 | 图 | 框架层级图：CPS/CPSS/CPHS/CHS 在水系统中的关系 | 自制 | 重点展示“上位观察框架”与“专门对象语言”的层次差异 |
| Tab-1 | 表 | 传统控制对象—数字化控制对象—复合运行对象比较表 | 汇编 | 承接第2章并在第3章作为关键总表复用 |
| Tab-2 | 表 | CPS、CPSS、CPHS、CHS 四类框架的边界、目标与适用问题比较 | 汇编 | 用于本章核心辨析 |
| Eq-1 | 公式/结构表达 | 三空间—专门对象语言的映射关系表达 | 推导 | 公式需求较轻，可用结构式而非复杂数学式 |
| Fig-2 | 图 | Agent/工作代理/人类组织在边界中的位置示意图 | 自制 | 为第5章铺垫 |

## 6. 证据缺口

| 序号 | 问题 | 影响范围 | 解决动作 |
|---|---|---|---|
| 1 | 尚未再次重读术语规范中 CPSS 与 CHS 的关键定义条目 | 第3章术语一致性 | 写作前补读术语规范相关段落 |
| 2 | CPSS 综述的核心定义尚未本轮重新摘录入源笔记 | 第3章引用精度 | 如需定稿前精修，可再补充摘录 |
| 3 | 第3章框架层级图尚未形成独立绘图提示卡 | 后续插图执行 | 在样章完成后补建图表任务与来源追踪文件 |

## 7. 审核结论

> 本章已经具备进入正式写作的证据条件。当前结论为：**是，可以进入正式写作；但须在写作过程中继续保持术语规范一致，并把“上位框架”与“专门对象语言”的层级关系说清。**

## References

[1]: https://www.mdpi.com/1424-8220/23/17/7391 "A Holistic Review of Cyber–Physical–Social Systems: New Directions and Opportunities"
[2]: https://www.sciencedirect.com/science/article/pii/S0040162523002251 "Evolution of cyber-physical-human water systems: Challenges and gaps"
[3]: https://www.sciencedirect.com/science/article/pii/S1877343523000374 "Cyber-physical systems in water management and governance"
[4]: file:///mnt/desktop/desktop/hydrosis-local/research/ppt/发布会26.4/14_学科篇_三方交叉与水系统控制论的正反思辨.md "自主运行水网的学科底座：水利-控制-AI 三方交叉与水系统控制论"
[5]: file:///mnt/desktop/desktop/hydrosis-local/research/chs-books-v2/CHS_术语规范_全系列.md "CHS 全系列术语统一规范"
