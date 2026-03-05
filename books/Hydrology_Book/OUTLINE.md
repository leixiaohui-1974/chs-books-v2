# Hydrology Intelligence Engineering (《智能水文工程实战》)
## A Practical Book for Water Sector Professionals

## 核心规划
**字数目标**：5万字以上
**读者定位**：水文水资源工程师、给排水工程师、水务管理者、数字孪生集成商
**核心导向**：全面介绍智能水文体系，包括水文算法、API架构、MCP集成、工作流（Skills）、智能体（Agents）以及典型水务案例。

### 第一部分：领域基础与运行环境（Domain Foundations）
**第1章：2026年的智能水文为什么重要**
1.1 城市内涝、干旱压力与基础设施老化的挑战
1.2 传统被动响应模式向预测性调控的业务转变
1.3 什么是 Hydrology Intelligence（水文智能）

**第2章：数字水文核心概念**
2.1 流域、产汇流、入渗、基流与地下水-地表水交互
2.2 场次洪水模型 vs. 连续水文模型
2.3 站点观测、网格化气象与遥感数据的融合

### 第二部分：水文平台特性与数据模型（Platform & Data Model）
**第3章：核心水文能力（Features）**
3.1 降雨径流计算、河道汇流与洪水演进
3.2 实时遥测数据接入与事件检测
3.3 预报预警与 What-if 场景推演（Scenario Simulation）

**第4章：数字孪生对象与数据模型（MBD 映射）**
4.1 实体抽象：流域（Basin）、河段（Reach）、水库（Reservoir）、泵闸（Gate/Pump）
4.2 时间序列数据的语义、单位、质量标识（Quality Flags）
4.3 空间索引与拓扑约束网络

### 第三部分：算法与决策引擎（Algorithms & Decision Engines）
**第5章：预报与模拟算法（Forecasting）**
5.1 概念性水文模型与水动力学模型（1D/2D）
5.2 引入机器学习（Time-series ML）预测来水与水位
5.3 集合预报（Ensemble）与概率不确定性分析

**第6章：优化调控算法（Optimization）**
6.1 泵站、闸门、蓄水池的 MPC（模型预测控制）
6.2 多目标优化：防洪排涝、泵站节能、水质达标的权衡
6.3 约束处理与实时滚动优化

### 第四部分：开放互联协议 MCP 与 API（Integration & MCP）
**第7章：面向关键水务系统的 API 设计**
7.1 为什么水利系统需要 API-First 架构？
7.2 RESTful 资源模型：`/basins`, `/stations`, `/forecasts`, `/scenarios`
7.3 时空窗口查询与异步任务（Asynchronous Jobs）处理

**第8章：MCP：让大模型读懂水文世界**
8.1 MCP (Model Context Protocol) 核心机制：Tools, Resources, Prompts
8.2 封装水文能力：将 `run_forecast` 包装为 FastMCP Server
8.3 标准化 Schema：如何确保大模型稳定输出控制指令

### 第五部分：智能体与专业技能（Agents & Skills）
**第9章：定义水文领域的 Skills（工作流）**
9.1 什么是 Skill？将业务经验封装为可执行流
9.2 典型 Skill 范例：降雨预报复核、异经常归因分析、合规报告生成
9.3 Skill 的质量控制与测试验证

**第10章：Agent 在水务运营中的架构**
10.1 调度规划 Agent、数据分析 Agent、控制 Agent 的分工
10.2 大模型的“认知层”：如何从文字意图提取水文 API 参数
10.3 人机协同（Human-in-the-loop）与安全护栏（Guardrails）机制

### 第六部分：端到端水文与水务案例实战（Use Cases）
**第11章：城市内涝防洪预警与联合调度**
11.1 从气象接入、产流计算到街道级内涝告警的全链路
11.2 “库-河-网”联合调度降低溢流风险

**第12章：引调水工程与水库群优化运行**
11.1 水库放水计划与下游防洪风险的联合求解
11.2 枯水期的水资源供需平衡与限水策略推演
11.3 突发水污染事件（Water Quality Incident）的溯源与扩散追踪

### 第七部分：系统部署与未来展望
**第13章：HydroDesktop（工作台）部署与 SRE**
13.1 系统成熟度阶段与团队人员转型
13.2 平台可靠性工程（SRE）：水文服务的 SLI/SLO 设定
13.3 面向气候韧性的自主水务运行路线图（2030+）