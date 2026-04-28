<!-- 变更日志
v1 2026-04-28: 初稿，约1.2万字。Agent Fabric基础设施章——多Agent生命周期管理、通信协议、编排DSL。
-->

# 第9章 Agent Fabric：多智能体编排基础设施

---

> **知识依赖框：本章预设读者已了解……**
> 1. Agent统一定义：Agent五元组 (Perception, Decision, Action, Objective, Environment) 的完整定义见《水控》§2.6——本章不重定义Agent本身，只讨论Agent作为可部署计算单元的工程基础设施
> 2. HydroOS五层架构（第2章）：L0感知执行层、L1数据底座层、L2内核层、L3服务层、L4应用层的分工
> 3. Skill系统（第3章）：Skill作为水利算法标准化封装单元的定义、注册与调度机制
> 4. HydroClaw认知架构《水控》§14.2：Agent-Skill-Tool三层认知架构的基本概念
> 5. 多智能体系统（MAS）基本原理《认知》第 6—7 章：Agent间协同、协商与冲突消解的理论基础

> **学习目标：读完本章，你将能够……**
> 1. 阐述Agent Fabric作为HydroOS中管理多Agent生命周期的统一基础设施的设计动机与核心功能（Bloom: 理解）
> 2. 描述Agent的注册、发现、健康检查与生命周期状态迁移机制，并能绘制完整的状态机图（Bloom: 应用）
> 3. 解释Agent间通信协议的设计原则，包括消息格式、路由策略与QoS保证（Bloom: 理解）
> 4. 分析任务分配与负载均衡策略在异构Agent集群中的适用场景与工程取舍（Bloom: 分析）
> 5. 使用Agent编排DSL编写一个多Agent协同场景的声明式编排脚本（Bloom: 应用）
> 6. 评估Agent Fabric在WNAL L3+场景中的部署策略与降级方案（Bloom: 评价）

---

> **[管理层速览]**
>
> 如果说HydroOS是水网的操作系统，Skill是它的"能力单元"，那么Agent就是它的"执行者"，而Agent Fabric则是让多个执行者协同工作的组织架构。就像一家公司不能只有员工而没有管理体系和沟通机制，HydroOS不能让Agent各自为战。
>
> 本章回答的核心问题是：当水网中有数十甚至上百个Agent（每个负责不同的控制任务、监测任务或决策辅助任务），如何保证它们有序运行、及时通信、故障自愈？Agent Fabric提供的正是这个基础设施层——它不关心每个Agent内部用什么算法（那是《认知》和《算法》的领域），它关心的是Agent的"生老病死"（注册、激活、监控、退役）和"说话方式"（通信协议与消息路由）。

---

## 开篇故事：三条告警同时到来的一夜

[L1 所有读者]

2025年8月17日凌晨2:14，某流域调度中心的HydroOS平台同时触发三条来自不同Agent的告警。

Agent-A（负责上游来水预报）报告："未来6小时入库流量预测置信区间从±12%扩大到±35%，模型不确定性超阈值。" Agent-B（负责干渠水位调控）报告："7号节制闸响应延迟从正常值2.3秒增至9.7秒，疑似执行机构卡涩。" Agent-C（负责能耗优化）报告："泵站3号机组振动幅值从2.1mm/s升至5.8mm/s，需降功率运行。"

三个告警单独看都不致命。但调度内核需要判断：这三个事件是否关联？它们叠加后会产生什么系统性影响？应该让哪个Agent优先响应？如果让Agent-B独自处理水位调控、让Agent-C独自降功率，会不会因为泵站降功率导致水位进一步恶化，与Agent-B形成振荡？

调度员李工看着屏幕上三个闪烁的告警图标，没有逐一处置，而是在Agent Fabric的编排面板上选择了一个名为"多告警联合研判"的预置工作流。三秒内，Fabric自动执行了以下动作：(1) 启动一个临时的协调Agent（Orchestrator），(2) 将三个告警消息路由到Orchestrator，(3) Orchestrator分别向Agent-A/B/C查询当前状态快照，(4) 运行一次多目标联合优化，(5) 输出一个包含功率下调优先级、闸门调整幅度和预案启动建议的综合报告。

这套机制的关键不在于每个Agent有多聪明，而在于有一个统一的基础设施让它们知道彼此的存在、能彼此对话、能按编排策略协同工作。这就是Agent Fabric的工程价值。

> **AI解读：** 这个故事揭示了Agent Fabric的三个核心能力。第一，Agent注册与发现——Orchestrator不需要硬编码其他Agent的地址。第二，消息路由——告警消息不是广播给所有Agent，而是按策略定向投递。第三，动态编排——根据告警的关联性自动生成联合研判流程。这三个能力构成了Agent Fabric区别于简单消息队列的本质特征。

---

## 9.1 为什么需要Agent Fabric [L1]

### 9.1.1 从单Agent到多Agent：组织复杂度跃升

《认知》第 6 章已经从理论层面论证了多智能体系统（MAS）在水网中的必要性：单个Agent无法同时处理空间分布式、时间多尺度、目标多冲突的水网控制问题。但从工程部署的角度看，《认知》的论证只回答了"为什么需要多Agent"——它没有回答"多Agent怎么组织、怎么运维、怎么保证可靠性"。

这正是《平台》与《认知》的分工边界：《认知》讲"多Agent为什么这样设计"（认知层面的架构论证），《平台》讲"Agent Fabric怎么部署运维"（平台层面的工程实现）。

在工程实践中，多Agent系统的组织复杂度体现在三个维度：

**数量复杂度**：一个中等规模的流域（如淮河流域），可能需要部署50-100个Agent——包括每个支流的预报Agent、每个闸群的调控Agent、每个泵站的优化Agent，以及全局的协调Agent、审计Agent、安全监控Agent。每个Agent都有自己的运行周期、计算资源需求和故障模式。

**关系复杂度**：Agent之间不是孤立的。上游预报Agent的输出是下游调控Agent的输入；能耗优化Agent的决策会约束水位调控Agent的行动空间；全局协调Agent需要等待多个子Agent的计算结果才能做综合决策。这些依赖关系构成了一个有向图，图的拓扑随工况动态变化。

**生命周期复杂度**：Agent会启动、会停止、会故障、会升级。在一次防汛应急中，可能需要临时启动一批预案Agent；在常规运行中，某些Agent可能长期休眠；当某个Agent的模型版本更新后，需要确保新旧版本之间不产生数据格式冲突。

这三个维度的复杂度叠加，使得"各自为战"的Agent部署模式不可持续。Agent Fabric就是为了解决这个组织问题而设计的基础设施层。

### 9.1.2 Agent Fabric在HydroOS五层架构中的位置

Agent Fabric位于HydroOS的L3服务层，与Skill注册中心、事件总线并列。它向上为L4应用层提供Agent管理界面和编排工具，向下通过L2内核层的调度引擎获取计算资源，向侧方与Skill注册中心交互（Agent调用Skill进行计算）。

**表9-1：Agent Fabric与HydroOS各层的接口**

| 层 | 接口内容 | 调用方向 |
|:---:|:---|:---:|
| L4 应用层 | Agent状态Dashboard、编排面板、告警订阅 | L4→L3 |
| L3 Skill注册中心 | Agent调用Skill进行模型计算 | L3↔L3 |
| L3 事件总线 | Agent间消息传递、告警发布 | L3→L3 |
| L2 内核层 | 计算资源申请、优先级调度 | L3→L2 |
| L1 数据底座 | Agent读取时序数据、写入执行日志 | L3→L1 |

> **AI解读：** Agent Fabric不是独立运行的应用，而是嵌入HydroOS L3层的横向基础设施。它不替代Skill系统、不替代L2调度引擎、不替代数据底座——它做的是Agent特有的组织性工作：注册、发现、通信、编排。这就像公司的人力资源部门不替代业务部门做事，但负责员工的入职、沟通、绩效和离职管理。

### 9.1.3 与《认知》的分工边界

为避免跨卷概念混淆，此处明确《认知》与《平台》在Agent主题上的分工：

| 维度 | 《认知》第 6—7 章（认知AI方法卷） | 《平台》第 9 章（平台开发卷） |
|------|-------------------------------|----------------------|
| Agent认知架构 | 讲Agent的推理链设计、知识表示、决策逻辑 | 不讲（引用《认知》） |
| 多Agent协同原理 | 讲协同模式（协商/拍卖/共识）、冲突消解算法 | 不讲（引用《认知》） |
| Agent注册与发现 | 不讲（属平台基础设施） | 讲注册表结构、发现协议、健康检查 |
| Agent通信协议 | 讲语义层面的消息内容设计 | 讲传输层面的消息格式、路由、QoS |
| Agent生命周期管理 | 不讲 | 讲启动/停止/升级/退役的工程流程 |
| Agent编排工具 | 不讲 | 讲编排DSL、工作流定义与执行引擎 |
| Agent部署运维 | 不讲 | 讲监控、告警、日志审计、降级策略 |

---

## 9.2 Agent生命周期管理 [L2]

### 9.2.1 Agent状态机

每个部署在HydroOS上的Agent实例都遵循一个精确定义的生命周期状态机。这个状态机是Agent Fabric对所有Agent进行统一管理的基础。

Agent的状态集合定义为：

$$\mathcal{S}_{\text{Agent}} = \{\text{Registered}, \text{Initialized}, \text{Running}, \text{Paused}, \text{Degraded}, \text{Stopped}, \text{Failed}\} \tag{9-1}$$

状态迁移条件如下：

- **Registered → Initialized**：Agent通过注册审核后，Fabric为其分配计算资源（CPU核、内存配额、网络端点），加载配置参数。这一步相当于操作系统中的"进程创建"。
- **Initialized → Running**：Agent完成自检（模型文件完整性校验、依赖Skill可用性检查、数据源连通性测试），通过后进入运行态，开始执行其核心任务循环。
- **Running → Paused**：Fabric发出暂停指令（通常用于系统维护或资源紧张时的优先级调度），Agent保存当前状态快照并挂起任务循环。
- **Paused → Running**：Fabric发出恢复指令，Agent从快照恢复并继续运行。
- **Running → Degraded**：Agent的健康检查连续N次未通过（如模型计算超时、数据源中断、内存使用超阈值），自动进入降级态。在降级态下，Agent可能只执行部分功能或降低计算频率。
- **Degraded → Running**：健康检查恢复通过，自动回归运行态。
- **Degraded → Stopped**：降级持续时间超过阈值T_timeout，或Fabric判定该Agent已无法提供有效服务，主动停止。
- **任何状态 → Failed**：Agent进程崩溃或遇到不可恢复的错误（如模型文件损坏、硬件故障）。
- **Failed → Registered**：经过人工或自动修复后，Agent重新注册。

[工程解释] 这个状态机的设计借鉴了Erlang/OTP的supervisor树模式和Kubernetes的Pod生命周期管理，但针对水网场景做了三项调整：第一，增加了Degraded态，因为在水利场景中"部分可用"比"完全不可用"更有价值——一个只能做简单水位预测的降级Agent，比完全死掉的Agent更有用；第二，状态迁移全部带时间戳记录，用于事后审计（这对符合《标治》合规要求至关重要）；第三，连接了ODD状态检查——当Agent的运行环境超出ODD范围时，强制进入Degraded态。

### 9.2.2 Agent注册表

Agent注册表（Agent Registry）是Agent Fabric的核心数据结构。每个Agent在注册时提交一个Agent描述文档（Agent Descriptor），包含以下字段：

**表9-2：Agent描述文档核心字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| agent_id | UUID | 全局唯一标识符 |
| agent_type | Enum | 类型分类：ForecastAgent / ControlAgent / OptimizeAgent / MonitorAgent / Orchestrator |
| name | String | 人类可读名称 |
| version | SemVer | 语义化版本号 |
| capabilities | [Capability] | 能力列表，每项包含输入/输出类型、WNAL适用等级、ODD约束 |
| dependencies | [agent_id] | 依赖的其他Agent列表（形成Agent依赖图） |
| resource_requirements | ResourceSpec | CPU/内存/存储/网络需求 |
| schedule_policy | Enum | Cron / EventDriven / Continuous / OnDemand |
| health_check_endpoint | URI | Fabric定期探测的健康检查端点 |
| owner_team | String | 负责运维的团队标识 |

注册表本身采用分布式一致性存储（基于Raft协议的多副本同步），确保在网络分区情况下仍能提供一致的Agent状态视图。

### 9.2.3 Agent发现机制

Agent发现（Service Discovery）解决的是"Agent A如何找到Agent B的地址"这个问题。在水网场景中，Agent的部署拓扑可能随防汛应急、系统扩容、节点故障而动态变化，硬编码的IP:Port不可行。

Agent Fabric采用**基于能力标签的发现机制**：每个Agent在注册时声明自己的capabilities，其他Agent通过查询"谁提供XXXX能力"来发现目标。这类似于DNS的服务发现或Kubernetes的Label Selector，但增加了版本兼容性检查和ODD适用性过滤。

具体流程：
1. Agent-A向Fabric发起发现请求：`discover(required_capability="StreamflowForecast", region="Huaihe_Upstream")`
2. Fabric在注册表中匹配所有具备该能力且ODD覆盖该区域的Agent
3. Fabric对候选Agent进行健康检查过滤（排除Degraded和Stopped态的Agent）
4. Fabric返回排序后的Agent列表（按负载、网络延迟加权排序）
5. Agent-A从中选择一个Agent-B建立通信会话

[工程解释] 发现机制的实现需要在"实时性"和"一致性"之间做取舍。对于控制类Agent（对延迟敏感），Fabric维护一个本地缓存，每隔T_refresh秒异步刷新——这样发现延迟可控制在毫秒级，代价是可能短暂出现"缓存指向的Agent已下线"的情况（需要重试机制兜底）。对于数据类Agent（对一致性敏感），Fabric每次都从注册表实时查询——延迟更高但保证准确性。

---

## 9.3 Agent间通信协议 [L2]

### 9.3.1 消息格式规范

Agent间的所有通信都遵循统一的JSON消息格式。该格式在设计上借鉴了FIPA ACL（Agent Communication Language）的消息结构，但针对水网工程场景做了简化和约束。

基本消息格式：

```json
{
  "header": {
    "msg_id": "uuid",
    "correlation_id": "uuid",
    "sender_id": "agent_uuid",
    "receiver_id": "agent_uuid | broadcast | multicast_group",
    "timestamp": "ISO8601",
    "msg_type": "Request | Response | Notification | Heartbeat",
    "priority": "P0 | P1 | P2 | P3",
    "ttl_seconds": 30
  },
  "performative": "query | inform | request | propose | refuse | confirm | cancel",
  "content": {
    "capability": "string",
    "payload": {},
    "constraints": {},
    "deadline": "ISO8601"
  }
}
```

关键字段的工程含义：

- **priority**：P0为安全相关消息（如ODD越界告警、安全联锁触发），必须在100ms内送达；P1为实时控制消息（如MPC协调请求），时效要求1秒；P2为常规业务消息；P3为统计/日志类消息。
- **ttl_seconds**：消息生存时间，超时未送达则丢弃。这是防止消息积压的关键机制——在水网的恶劣通信条件下，一个卡在拥塞队列里的旧调度指令比没有指令更危险。
- **performative**：消息的"言语行为"类型，沿用FIPA标准。对于水网场景，最常用的是query（查询状态）、inform（传递信息）、request（请求执行）和propose（建议方案）。

### 9.3.2 消息路由策略

Agent Fabric的消息路由引擎支持三种路由模式：

**点对点路由（Point-to-Point）**：发送方指定receiver_id，Fabric直接投递。用于确知目标Agent身份的场景，如预报Agent将预测结果直发给对应的调控Agent。

**话题路由（Topic-Based）**：发送方将消息发布到一个话题（Topic），所有订阅该话题的Agent接收。用于广播场景，如ODD状态变化告警、系统时钟同步信号。话题按命名空间组织：`hydroos/region/huaihe/alerts/odd`。

**内容路由（Content-Based）**：发送方不指定接收方，只描述消息内容特征。Fabric根据Agent的能力注册信息自动匹配接收方。这是最灵活但也最消耗资源的路由模式，仅用于需要动态发现目标的场景。

**表9-3：三种路由模式的适用场景与QoS约束**

| 路由模式 | 延迟目标 | 可靠性 | 适用场景 |
|---------|---------|--------|---------|
| 点对点 | <10ms (P0) / <100ms (P1) | 至少一次 | 预报→调控的数据管道 |
| 话题路由 | <50ms | 至多一次 | ODD告警广播、时钟同步 |
| 内容路由 | <500ms | 至少一次 | 应急态势的动态协同 |

### 9.3.3 QoS保证与拥塞控制

水网的通信条件差异极大：控制专网（光纤）的带宽和延迟稳定，而偏远站点的4G/NB-IoT链路可能出现秒级延迟和间歇性断线。Agent Fabric在消息层实现了适配性的QoS机制：

- **优先级抢占**：P0安全消息始终排在发送队列最前。当链路拥塞时，先丢弃P3日志消息，再丢弃P2业务消息，确保P0/P1消息的送达。
- **断线缓存**：当接收方Agent的通信链路中断时，Fabric在发送方缓存消息（按FIFO + 优先级排序），链路恢复后批量重传。缓存大小有上限（默认1000条），超出则丢弃最旧的P3级消息。
- **消息去重**：基于msg_id实现幂等性——接收方对相同msg_id的消息只处理一次，防止重传导致重复执行。

> **AI解读：** Agent间通信协议的设计有一个常被忽视的原则：**通信机制本身不应成为系统脆弱性的来源**。这意味着消息格式必须是确定的、可审计的（所有消息落盘日志），消息投递必须是可追踪的（每条消息有全局唯一的correlation_id用于端到端追踪），协议升级必须是向后兼容的（版本号在header中声明，接收方按最低版本解释）。这些原则在互联网分布式系统中是常识，但在工业控制系统向AI Agent系统过渡的过程中，往往因为"先跑通再说"的心态被忽略，直到出事后才回头补课。

---

## 9.4 任务分配与负载均衡 [L2]

### 9.4.1 任务分配问题的形式化

在Agent Fabric中，"任务"是触发Agent执行某项计算的工作单元。任务分配问题可以形式化为：

给定m个任务 $\{T_1, T_2, \ldots, T_m\}$ 和n个Agent $\{A_1, A_2, \ldots, A_n\}$，每个任务$T_i$对Agent的能力有约束$C_i$，每个Agent$A_j$有当前负载$L_j$和计算能力$K_j$。寻找分配矩阵$X_{m \times n}$，使得：

$$\min \sum_{i=1}^{m} \sum_{j=1}^{n} x_{ij} \cdot \text{cost}(T_i, A_j) \tag{9-2}$$

满足：
- 每个任务只分配一次：$\sum_j x_{ij} = 1, \forall i$
- 能力匹配：$x_{ij} = 1 \Rightarrow C_i \subseteq \text{capabilities}(A_j)$
- 负载上限：$\sum_i x_{ij} \cdot w_i \leq K_j, \forall j$（$w_i$为任务$T_i$的计算权重）

这是一个NP-难问题。在工程实践中，Fabric不追求全局最优分配，而是使用贪心+局部优化的近似策略。

### 9.4.2 调度策略

Agent Fabric支持三种任务调度策略，按场景选择：

**轮询调度（Round-Robin）**：适用于同构Agent池（多个Agent提供完全相同的能力），任务按FIFO队列轮询分配。优点是简单、公平，缺点是不感知Agent的实际负载差异。

**最少连接调度（Least-Connection）**：任务分配给当前负载最低的Agent。适用于Agent计算能力同构但负载不均的场景。Fabric通过健康检查端点获取每个Agent的实时负载（活跃任务数、CPU/内存使用率）。

**优先级感知调度（Priority-Aware）**：结合任务优先级和Agent能力画像的综合调度。P0任务优先分配，关键Agent（如全局协调Agent）预留资源余量避免过载。这是水网场景中的默认策略。

### 9.4.3 负载均衡与故障转移

当某个Agent进入Degraded或Failed状态时，Fabric自动触发故障转移（Failover）：将该Agent的待处理任务队列迁移到具备相同能力的健康Agent上。故障转移的时间窗口取决于健康检查的检测延迟和任务队列的迁移开销——正常情况下，Agent Fabric将故障转移的总耗时控制在3秒以内（P0任务）或15秒以内（P1任务）。

负载均衡与故障转移共享同一套底层机制：保持Agent池的能力冗余（任何关键能力至少由2个Agent提供），这是保证高可用的基本前提。

---

## 9.5 Agent编排DSL [L2]

### 9.5.1 设计理念

Agent编排DSL（Domain-Specific Language）是一种声明式语言，用于定义多Agent协同工作流。它的设计遵循三个原则：

**声明式而非命令式**：用户描述"要达成什么"，而非"每一步怎么做"。Fabric的执行引擎负责将声明式的编排描述转换为具体的Agent调用序列。

**可审计**：每个编排实例的执行过程——包括触发了哪些Agent、每个Agent的输入输出、分支决策点——都完整记录在审计日志中。这对应《标治》第 12 章的RACI审计要求。

**可中断与可恢复**：编排工作流可能在任意步骤暂停（等待人工审批、等待外部数据），并在条件满足后从中断点继续执行。这适配了水网中"人机协同"的决策流程。

### 9.5.2 编排脚本示例

以下是一个"多条告警联合研判"场景的编排DSL脚本：

```yaml
workflow: multi_alert_joint_assessment
version: "1.2.0"
description: "当多个Agent同时发出告警时，启动联合研判"

trigger:
  type: event_pattern
  condition:
    - alert_count >= 3 within 60s
    - alerts.from_different_agents == true

steps:
  - id: create_orchestrator
    action: spawn_agent
    agent_type: Orchestrator
    ttl: 3600  # 1小时后自动销毁

  - id: collect_snapshots
    action: parallel
    fan_out:
      - query:
          agent: "{alert.source_agents}"
          capability: "StateSnapshot"
          timeout: 10s
    aggregate: merge_by_timestamp

  - id: check_correlation
    action: call_skill
    skill_id: "correlation_analysis_v2"
    input:
      snapshots: "{collect_snapshots.output}"
      alerts: "{trigger.alerts}"
    condition:
      - correlation_score > 0.3

  - id: run_joint_optimization
    action: call_agent
    agent_type: OptimizeAgent
    capability: "MultiObjectiveJointOptimization"
    input:
      correlated_alerts: "{check_correlation.output}"
    deadline: 30s

  - id: human_review
    action: wait_for_approval
    input: "{run_joint_optimization.output}"
    approver_role: "SeniorDispatcher"
    timeout: 300s  # 5分钟无人审批则自动降级到默认预案

  - id: execute_plan
    action: parallel
    fan_out: "{run_joint_optimization.output.action_items}"
    rollback_on_failure: true
```

[工程解释] 这个DSL脚本展示了几项关键设计。`parallel`步骤将多个独立查询并行化，缩短了总执行时间。`human_review`是一个同步等待点——当决策涉及重大工程影响时（如泄洪操作），编排自动引入人工审批环节，而不是让Agent全自动执行。`execute_plan`的`rollback_on_failure: true`确保一旦任何执行步骤失败，Fabric会自动执行补偿操作（如恢复闸门到执行前状态）。

### 9.5.3 编排执行引擎

编排引擎将DSL脚本解释为有向无环图（DAG），按拓扑排序执行。执行引擎的关键能力：

- **并行动态扇出**：`fan_out`步骤中的子任务数量可以在运行时根据实际数据动态确定（例如告警涉及3个Agent就创建3个子任务）
- **条件分支**：步骤的`condition`字段控制执行路径分叉
- **超时控制**：每个步骤都有独立的deadline，超时触发降级逻辑
- **补偿事务**：`rollback_on_failure`触发时，按执行的逆序调用每个Agent的compensate方法

---

## 9.6 部署策略与降级方案 [L2]

### 9.6.1 WNAL等级对应的Agent Fabric部署策略

Agent Fabric的部署深度应与目标系统的WNAL等级匹配：

| WNAL等级 | Fabric部署策略 | 说明 |
|:---:|:---|:---|
| L0-L1 | 无需Fabric | 单一或少量的确定性规则Agent，点对点通信即可 |
| L2 | 轻量Fabric | Agent注册表+基本健康检查+点对点消息路由 |
| L3 | 全功能Fabric | 完整的状态机+三种路由模式+编排DSL+故障转移 |
| L4-L5 | 增强Fabric | 在L3基础上增加分布式Fabric集群+跨区域消息路由+安全沙箱隔离 |

### 9.6.2 Agent Fabric自身的降级

Agent Fabric不能成为单点故障。其降级设计遵循"Fail-Standalone"原则：当Fabric不可用时，Agent退化为独立运行模式。

具体降级策略：
1. Fabric主节点故障 → Raft自动选举新Leader（<2秒）
2. Fabric集群整体不可用 → Agent使用本地缓存的通信对端地址继续运行，但失去动态发现和编排能力
3. 编排引擎故障 → 正在执行的编排工作流进入安全暂停，已执行步骤的结果保留，等待引擎恢复后从中断点继续

> **本章前置阅读**：《水控》§2.6.6（Agent统一定义）、《水控》§14.2（HydroClaw认知架构）、《认知》第 6—7 章（多智能体系统原理）
>
> **本章后续进阶**：《算法》第 6 章（Agent模型选型与推理部署的具体工程方法）、《标治》第 5 章（ODD拓扑声明——Agent部署时的ODD边界定义规范）

---

## 参考文献

[9-1] Wooldridge, M. (2009). *An Introduction to MultiAgent Systems* (2nd ed.). Wiley.
[9-2] FIPA. (2002). *FIPA ACL Message Structure Specification*. SC00061G.
[9-3] Kubernetes. (2024). *Pod Lifecycle*. https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
[9-4] Armstrong, J. (2007). *Programming Erlang: Software for a Concurrent World*. Pragmatic Bookshelf.
[9-5] Ongaro, D., & Ousterhout, J. (2014). In search of an understandable consensus algorithm. *USENIX ATC*.
[9-6] Lei, X. et al. (2025c). 水系统控制论：WNAL架构. *南水北调与水利科技*.
[9-7] Bernstein, P. A., & Newcomer, E. (2009). *Principles of Transaction Processing* (2nd ed.). Morgan Kaufmann.
[9-8] Hohpe, G., & Woolf, B. (2003). *Enterprise Integration Patterns*. Addison-Wesley.
