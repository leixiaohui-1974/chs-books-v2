# CHS 全系列术语统一规范

**适用范围**: T1理论卷、T2a技术卷上、T2b技术卷下、T3工程标准卷、T4平台卷、T5智能决策卷
**版本**: v2.0（CPSS统一框架修改后）
**最后更新**: 2026-03-31
**关联需求**: CROSS-01 全系列术语统一

---

## 一、CPSS框架术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 信息-物理-社会系统 | Cyber-Physical-Social Systems | CPSS | CHS全系列的统一屋顶框架，将水系统控制问题置于Physical、Cyber、Social三空间的耦合视角下分析。 | 全局 | T1 ch01 |
| Physical空间 | Physical Space | — | 水物理过程所在空间，包括河道、水库、管网、水文循环、闸门、泵站等实体及其物理行为。 | Physical | T1 ch01 |
| Cyber空间 | Cyber Space | — | 信息处理所在空间，包括数字孪生、模型、算法、控制器、AI等一切数字化组件。 | Cyber | T1 ch01 |
| Social空间 | Social Space | — | 人类社会决策所在空间，包括调度规程、法规、利益博弈、人类决策、社会需求等。 | Social | T1 ch01 |
| 三重反馈回路 | Triple Feedback Loop | — | CPSS三空间间的嵌套反馈结构：回路1（秒~分钟级）Physical↔Cyber，回路2（小时~天级）Cyber↔Social，回路3（月~年级）Social↔Physical。水系统复杂性的真正来源是三空间的耦合反馈。 | 全局 | T1 ch01 |

## 二、CHS基础术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 水系统控制论 | Cybernetics of Hydro Systems | CHS | 以控制论为核心方法论，研究水系统感知、决策、执行全过程的学科体系。全系列统一学科名称。 | 全局 | T1 ch01 |
| 六元受控系统 | Six-Element Controlled System | Σ | 水系统控制论的核心形式化表述Σ=(P,A,S,D,C,O)：P物理过程、A执行器、S传感器、D数字孪生、C控制器、O运行目标。 | 全局 | T1 ch01 |
| 物理过程 | Physical Process | P | 六元组第一元素，水物理过程（河道、水库、管网、水文循环）。 | Physical | T1 ch01 |
| 执行器 | Actuation | A | 六元组第二元素，C→P界面，将控制指令转化为物理动作（闸门、泵站）。 | C→P界面 | T1 ch01 |
| 传感器 | Sensing | S | 六元组第三元素，P→C界面，将物理状态转化为数字信号（遥测、监测）。 | P→C界面 | T1 ch01 |
| 数字孪生 | Digital Twin | D | 六元组第四元素，水物理过程在Cyber空间的模型映射（水文模型、水力模型）。 | Cyber | T1 ch01 |
| 控制器 | Controller | C | 六元组第五元素，决策引擎（PID/MPC/RL/LLM），接收感知信息并输出控制决策。 | Cyber | T1 ch01 |
| 运行目标 | Operation Objective | O | 六元组第六元素，目标约束（防洪标准、供水保证率）。关键洞察：O属于Social空间，目标不是技术决定的，而是社会协商的。 | Social | T1 ch01 |
| P→C投影函数 | P→C Projection | — | 物理空间向Cyber空间的映射过程，通过传感器和模型将物理实体转化为数字表征。 | P→C界面 | T1 ch03 |
| 八原理 | Eight Principles | P1-P8 | CHS方法论的八条核心原理，分四层：建模基础层(P1传递函数化、P2可控可观性)、架构组织层(P3分层分布式、P4安全包络)、验证保障层(P5在环验证)、协同智能层(P6认知增强、P7人机共融、P8全生命周期自主演进)。 | 全局 | T1 ch07 |
| 五个控制本质 | Five Control Essences | — | 水系统控制问题的五个核心特征：大时滞、强耦合、强约束、强不确定性、人机共治。全系列统一措辞，不使用"非线性""多约束"等替代说法。 | 全局 | T1 ch01 |

## 三、智能体术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 智能体统一定义 | Unified Agent Definition | Agent | Agent=(Perception, Decision, Action, Objective, Environment)。PID/MPC/RL/LLM Agent都是同一范式的不同实现，差异仅在决策机制复杂度，反馈原理不变。 | Cyber | T1 ch01 |
| 反应式智能体 | Reactive Agent | — | 仅基于当前感知直接映射到动作的智能体，无内部状态模型。典型实例：PID控制器（感知偏差e(t)→输出控制量）。 | Cyber | T1 ch05 |
| 基于模型的智能体 | Model-based Agent | — | 维护内部环境模型，基于模型预测进行决策的智能体。典型实例：MPC控制器（基于IDZ模型滚动优化）。 | Cyber | T1 ch04 |
| 规划型智能体 | Planning Agent | — | 具备多步前瞻规划能力的智能体，可生成行动序列并评估长期收益。典型实例：RL智能体（通过策略网络π(s)选择动作以最大化累计奖励）。 | Cyber | T2a ch07 |
| LLM智能体 | LLM Agent | — | 以大语言模型为决策引擎的智能体，感知文本/工具返回值，通过LLM推理+规划完成指令，动作为调用工具。 | Cyber | T2b ch09 |

## 四、控制范式术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 闭环控制 | Closed-loop Control | — | 系统输出经传感器反馈至控制器，控制器根据反馈偏差调整输入的控制方式。反馈是闭环的本质特征。 | Cyber↔Physical | T1 ch02 |
| 开环执行 | Open-loop Execution | — | 控制指令按预定方案顺序执行，执行过程中不利用输出反馈修正的方式。误差单向累积，无自我纠偏能力。 | Cyber→Physical | T1 ch02 |
| 时间步内闭环 | Intra-step Closed-loop | — | 在每个时间步内，多模型（预报↔水力↔优化）耦合迭代至收敛后再推进下一步，每步都有可执行决策。这是四预应有的正确形态。 | Cyber | T1 ch03 |
| 开环串行 | Open-loop Sequential | — | 模型A跑完全部时间步后传结果给模型B，模型间无反馈，误差单向累积。当前水利行业四预的主流做法，应改为时间步内闭环。 | Cyber | T1 ch03 |
| 反馈 | Feedback | — | 将系统输出信息返回输入端以修正控制决策的机制。反馈是控制论的核心概念，贯穿CPSS三空间。 | 全局 | T1 ch02 |

## 五、工作流术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 确定性工作流 | DAG Workflow | DAG | 步骤预先固定、执行路径在运行前完全确定的工作流。Physical空间的物理因果律要求严格确定性工作流。 | Physical为主 | T1 ch01 |
| 灵活工作流 | Dynamic Routing Workflow | — | 运行时根据当前状态动态选择执行路径的工作流。Social空间的人类决策情境依赖性要求高度灵活工作流。 | Social为主 | T1 ch01 |
| 工作流谱系 | Workflow Spectrum | — | 从严格确定性到高度灵活的连续谱系：Physical空间严格确定性、Cyber空间混合（算法流程确定+策略可自适应）、Social空间高度灵活。 | 全局 | T1 ch01 |

## 六、四预术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 四预闭环 | Four-Prediction Closed Loop | 四预 | 预报、预警、预演、预案的闭环耦合体系。四预不是四个串行环节，而是CPSS三空间在每个时间步内的闭环耦合。 | 全局 | T1 ch03 |
| 预报 | Forecasting | — | Sensing+Digital Twin的前向推演，将当前状态向未来投射。 | Cyber | T1 ch03 |
| 预警 | Warning/Alerting | — | ODD状态评估，实时判断系统状态是否接近运行边界。 | Cyber↔Social | T1 ch03 |
| 预演 | Rehearsal/Simulation | — | XIL验证，在不同保真度层级（MIL/SIL/HIL/OIL）上预先验证决策方案的可行性。 | Cyber | T1 ch03 |
| 预案 | Response Planning | — | Control的实时决策输出。预案不是静态文档，而是活的动态决策。 | Cyber→Social | T1 ch03 |
| 宏观四预 | Macro-level Four-Prediction | Skill级 | 天~周尺度的四预，以开环优化+滚动修正为主，工作流灵活（Social主导），形态为方案比选。 | Social主导 | T1 ch03 |
| 实时四预 | Real-time Four-Prediction | 步长级 | 分钟~小时尺度的四预，严格闭环、时间步内耦合，工作流确定性（Physical主导），每步输出可执行决策。 | Physical主导 | T1 ch03 |
| 在环测试 | X-in-the-Loop Testing | XIL | 预演的四层验证体系，按保真度递增：MIL（模型在环）、SIL（软件在环）、HIL（硬件在环）、OIL（运行在环/人在环）。 | Cyber | T1 ch11 |
| 模型在环 | Model-in-the-Loop | MIL | XIL第一层，纯模型仿真验证，保真度最低、迭代最快。 | Cyber | T1 ch11 |
| 软件在环 | Software-in-the-Loop | SIL | XIL第二层，将控制算法部署到目标软件环境中测试。 | Cyber | T1 ch11 |
| 硬件在环 | Hardware-in-the-Loop | HIL | XIL第三层，接入物理硬件（PLC、RTU）进行实时测试。 | Cyber↔Physical | T1 ch11 |
| 运行在环 | Operator-in-the-Loop | OIL | XIL第四层，含人类操作员的全系统联调，保真度最高。对应AI领域的Human-in-the-Loop。 | Cyber↔Social | T1 ch11 |

## 七、等级与安全术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 水网自主等级 | Water Network Autonomy Levels | WNAL | Social空间向Cyber空间的决策权渐进让渡等级（L0-L5）。全系列使用WNAL（非WSAL）。L3为质变点：Cyber在ODD内自主，Social设定边界。 | Social→Cyber | T1 ch01 |
| L0 手动运行 | Manual Operation | L0 | Social完全控制，Cyber不参与决策。 | Social | T1 ch01 |
| L1 规则自动化 | Rule-based Automation | L1 | Social设定规则，Cyber按规则执行。 | Social主导 | T1 ch01 |
| L2 条件自动化 | Conditional Automation | L2 | Cyber决策，Social监督。 | Social监督 | T1 ch01 |
| L3 条件自主 | Conditional Autonomy | L3 | Cyber在ODD内自主，Social设定边界。WNAL的质变点。 | Cyber主导 | T1 ch01 |
| L4 高度自主 | High Autonomy | L4 | Cyber主导决策，Social仅在极端情况下介入。 | Cyber主导 | T1 ch01 |
| L5 完全自主 | Full Autonomy | L5 | Cyber完全自主运行。 | Cyber | T1 ch01 |
| 运行设计域 | Operational Design Domain | ODD | 系统可安全自主运行的条件边界集合。CHS采用六维定义：H水文（Hydrological Limits）/P工程物理（Physical Infrastructure）/D数据质量（Data Quality）/E环境气象（Environmental Conditions）/C网络算力（Cyber-Infrastructure）/G治理规则（Governance & Rules）。ODD空间为六维子空间之交集 $X_{ODD}=H\cap P\cap D\cap E\cap C\cap G$。首次使用须给全称。 | Cyber↔Physical | T3 ch05 |
| 安全包络 | Safety Envelope | — | 系统运行的多维安全边界，超出即触发降级或保护动作。以中文"安全包络"为主，英文辅助。跨域安全包络存在耦合（如水质红→关闸→水位涨→边坡黄）。 | 全局 | T1 ch11 |
| 四态机 | Four-State Machine | — | 系统运行状态的四档划分：Normal（正常）、Restricted（受限）、Degraded（降级）、Managed（管控）。各域在不同状态下有具体行为定义。 | 全局 | T1 ch10 |
| 最小风险状态 | Minimum Risk Condition | MRC | 四态机的兜底安全目标，当系统无法维持正常运行时应退回的最低安全状态。 | Physical | T1 ch10 |

## 八、架构术语

| 中文名 | 英文名 | 缩写 | 标准定义 | 所属CPSS空间 | 首次出现 |
|--------|--------|------|----------|-------------|---------|
| 分层分布式控制 | Hierarchical Distributed Control | HDC | CHS核心架构模式，分四层：第0层安全保护层、第1层本地调节层、第2层协调优化层、第3层计划调度层。层级用"第N层"表述，避免与WNAL的LN混淆。首次使用须给全称。 | Cyber | T1 ch07 |
| 数字孪生 | Digital Twin | DT | Physical空间在Cyber空间的数字映像，支撑预报、预演和控制决策。注：DT作为工程实现对象，是六元组中D（数字孪生元素）的具体系统化实现。D强调概念角色（Cyber空间中物理过程的模型映射），DT强调工程实体（包含机理模型、数据驱动模型、实时数据流和控制接口的完整平台）。 | Cyber | T1 ch03 |
| 活孪生 | Live Twin | — | 通过数据同化实时更新参数的数字孪生，反映Physical空间当前状态（如IDZ参数在线辨识）。与"冻结孪生"相对。 | Cyber | T1 ch06 |
| 冻结孪生 | Frozen Twin | — | 参数固化、不随实时数据更新的数字孪生，用于离线分析和方案比选。与"活孪生"相对。 | Cyber | T1 ch06 |
| 积分-延迟-零点模型 | Integrator-Delay-Zero | IDZ | CHS核心简化模型，将复杂水力过程降阶为可在线消费的控制导向模型。活孪生的典型载体。 | Cyber | T1 ch04 |
| 模型预测控制 | Model Predictive Control | MPC | 基于模型滚动预测+在线优化的控制方法。CHS中典型实现为分层分布式MPC：协调层（小时级全线优化）+执行层（分钟级现地跟踪）。首次使用须给全称。 | Cyber | T1 ch04 |
| 基于模型的设计 | Model-Based Design | MBD | 以模型为核心贯穿设计、仿真、验证、部署全流程的工程方法。注意：非Model-Based Definition。 | Cyber | T3 ch08 |
| 水网操作系统 | HydroOS | — | CHS软件平台的统一名称，承载HDC架构的运行时环境。 | Cyber | T2b ch09 |
| 多域融合 | Multi-domain Fusion | — | 打破专业竖井（水力/水质/边坡/冰期/机电/视频），建立统一状态空间 $x=[h,Q,C,F_s,T_{ice},\delta_{mech},\ldots]$ 的架构思想。 | Cyber | T4 ch07 |
| 知识图谱 | Knowledge Graph | KG | Social空间隐性知识（规程、经验、规范）向Cyber空间的显式结构化表示，由实体-关系-属性三元组构成。 | Social→Cyber | T5 ch06 |
| 多域行为矩阵 | Multi-Domain Behavior Matrix | — | 四态机在各运行域（水力/水质/边坡/冰期/机电/通信等）下具体行为的矩阵化描述，用于跨域耦合分析。 | 全局 | T3 ch06 |

## 九、AI与控制论映射术语

本节建立AI/LLM领域概念与CHS控制论概念的对应关系，确保全系列在交叉引用时术语一致。

| AI/LLM概念 | CHS控制论对应 | 映射本质 | 首次出现 |
|-----------|-------------|---------|---------|
| Sequential Chain | 开环串行 | 模块间无反馈，输出单向传递。 | T1 ch01 |
| Agent Loop (ReAct) | 时间步内闭环 | 感知-决策-执行-反馈的循环，每步都可修正。 | T1 ch01 |
| Tool Use | 执行器(A)+传感器(S) | 工具调用=向环境施加动作并获取观测。 | T2b ch09 |
| Human-in-the-Loop | OIL（运行在环） | Social↔Cyber界面，人类参与决策回路。 | T1 ch11 |
| Multi-Agent System | 分层分布式控制(HDC) | 多个智能体按层级协调，局部自治+全局协同。 | T1 ch07 |
| Retry/Fallback | 降级/四态机 | 异常处理的系统化机制，从Normal逐级退守至MRC。 | T1 ch10 |
| DAG Workflow | 确定性工作流 | 步骤预先固定，执行路径不依赖运行时状态。 | T1 ch01 |
| Dynamic Routing | 灵活工作流 | 运行时根据状态动态选择路径。 | T1 ch01 |
| Prompt/Context | 目标约束(O) | 为智能体提供任务目标和上下文边界。 | T2b ch09 |
| Memory/RAG | 数字孪生(D) | 智能体的知识库=环境的数字化模型。 | T2b ch09 |

## 十、HDC控制层级命名规范

层级使用"第N层（Layer N）"表述，**严禁**使用"LN层"以避免与WNAL等级混淆。

| 层级 | 规范写法 | 功能 | 避免写法 |
|------|---------|------|---------|
| 安全保护层 | 第0层（Layer 0） | 硬件联锁、紧急保护 | ~~L0层~~ |
| 本地调节层 | 第1层（Layer 1） | 单体PID/现地控制 | ~~L1层~~ |
| 协调优化层 | 第2层（Layer 2） | 多体协调MPC | ~~L2层~~ |
| 计划调度层 | 第3层（Layer 3） | 全局调度优化 | ~~L3层~~ |

## 十一、八原理编号体系

教学版（全系列统一）：

| 编号 | 中文名称 | 层级 |
|------|---------|------|
| P1 | 传递函数化 | 建模基础层 |
| P2 | 可控可观性 | 建模基础层 |
| P3 | 分层分布式 | 架构组织层 |
| P4 | 安全包络 | 架构组织层 |
| P5 | 在环验证 | 验证保障层 |
| P6 | 认知增强 | 协同智能层 |
| P7 | 人机共融 | 协同智能层 |
| P8 | 全生命周期自主演进 | 演进能力层 |

> 注：CHS理论论文使用不同编号体系（双四元组），映射关系见T1第七章注释框7-B。

## 十二、各卷定位声明

每卷ch01须包含以下定位说明：

| 卷号 | 定位 | 说明 |
|------|------|------|
| T1 | 水系统控制论（本科教材） | 理论卷，建立CPSS统一框架 |
| T2a | CHS教材体系·建模与控制（研究生上册） | 技术卷上，经典控制方法 |
| T2b | CHS教材体系·认知AI工程版（研究生下册） | 技术卷下，AI与智能控制 |
| T3 | CHS教材体系·智能化标准与工程治理 | 工程标准卷 |
| T4 | CHS教材体系·平台开发分册 | 平台卷 |
| T5 | CHS教材体系·智能算法分册 | 智能决策卷 |

## 十三、工程数据统一

| 数据项 | 统一值 | 说明 |
|--------|-------|------|
| 胶东调水全长 | 571.4 km | 胶东地区引黄调水工程（南水北调东线） |
| 引黄济青段 | ~300 km | 需注明"引黄济青段"或"引黄济青工程" |

## 十四、写作规范

1. **首次出现规则**：所有缩写术语首次出现时须给出"中文全称（English Full Name, ABBR）"格式。
2. **中文优先**：正文以中文术语为主，英文/缩写作为辅助标注。
3. **CPSS空间标注**：讨论概念时应明确其所属CPSS空间归属，避免空间错位。
4. **六元组引用**：引用Σ=(P,A,S,D,C,O)时使用单字母缩写，首次引用须展开全部六个元素名称。
5. **避免混淆**：HDC层级用"第N层"，WNAL等级用"LN"，二者严格区分。
6. **工程案例**：不点名具体工程名称，以"某长距离调水干线""某梯级水电站"等通用描述。
7. **公式格式**：使用LaTeX格式（`$ $`），行间公式用`$$ $$`。
8. **文献引用**：格式为`[章-编号]`，如`[8-1]`、`[8-2]`。

---

> 本文件为CHS全系列六卷的术语统一基准。所有章节修改、新增内容须以本文件为准。如需新增术语，须经审核后更新本表。
