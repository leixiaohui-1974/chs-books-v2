<!-- 变更日志
v1 2026-04-28: 初稿，约1.2万字。MCP与工具生态章——工具注册/发现/调用/权限、Skill与MCP的关系。
-->

# 第10章 MCP与工具生态：HydroOS的工具集成协议

---

> **知识依赖框：本章预设读者已了解……**
> 1. Agent统一定义《水控》§2.6：Agent五元组中Action元素的外部化——工具是Agent执行Action的手段
> 2. Skill系统（第3章）：Skill是水利算法的封装单元，但Skill的执行需要依赖底层工具（模型计算引擎、数据库查询接口、通信协议适配器）
> 3. HydroClaw认知架构《水控》§14.2：Agent-Skill-Tool三层架构中Tool层的定位
> 4. OPC-UA协议栈（第5章）：工业设备层的协议统一，本章讨论的是认知AI层的工具协议统一
> 5. Agent Fabric（第9章）：Agent间通信基础设施，本章的工具协议是其补充——Agent不仅需要彼此对话，还需要调用外部工具

> **学习目标：读完本章，你将能够……**
> 1. 阐述MCP（Model Context Protocol）在HydroOS中的定位——不是替代OPC-UA，而是在认知AI层建立统一的工具调用接口标准（Bloom: 理解）
> 2. 描述工具注册、发现、调用与权限控制的完整流程（Bloom: 应用）
> 3. 区分MCP工具与Skill的层次关系：Skill是编排单元，MCP工具是原子能力单元（Bloom: 分析）
> 4. 设计一个符合MCP规范的水利工具接口定义（Bloom: 创建）
> 5. 评估工具生态的安全性风险——工具调用的权限模型、审计要求和沙箱隔离（Bloom: 评价）

---

> **[管理层速览]**
>
> 本章讨论的是一个看似技术细节、实则关乎平台架构生命力的核心问题：HydroOS中的AI Agent如何"使用工具"。
>
> 在传统水利信息化系统中，工具是分散的——水文模型是一个EXE文件，数据库查询是一个SQL脚本，闸门控制是一个OPC-UA指令。Agent要调用这些工具，就需要为每一种工具写专门的适配代码。这就像每买一件家电就要重新装修一次房子的电路——不堪重负。
>
> MCP（Model Context Protocol）的价值在于为所有工具定义一个统一的插座标准。Agent不需要知道"这个模型是Fortran写的还是Python写的""这个数据库是MySQL还是PostgreSQL"，它只需要向MCP服务器发送一个标准的工具调用请求，MCP服务器负责把请求翻译为具体的底层调用并返回结果。这不仅降低了Agent的开发成本，更重要的是它让工具生态具备了可扩展性和可替换性——新工具只要实现了MCP接口，就能被所有Agent使用。

---

## 开篇故事：五个模型，五种调用方式

[L1 所有读者]

2023年，某省级水文局的信息化团队面临一个看似平常但极其折磨人的问题。

他们要为一个新的AI调度Agent接入五个模型：一个Fortran写的水文预报模型（通过命令行调用）、一个Python写的机器学习模型（通过HTTP API调用）、一个MATLAB编译的水质模拟模型（通过MATLAB Runtime调用）、一个用C#写的闸门优化模型（通过.NET Remoting调用），还有一个商业软件的水力仿真模型（通过该厂商的专有SDK调用，文档只有PDF格式的英文手册）。

团队安排了两位工程师全职做集成工作。两个月过去了，他们只完成了三个模型的接入。每个模型有自己独特的数据格式——这个用CSV，那个用NetCDF，第三个用HDF5，第四个用私有的二进制格式。每个模型的错误处理方式也不同——有的返回错误码，有的抛异常，有的悄悄写一个error.log文件。每次Agent调用一个模型，都要经过数据格式转换、参数映射、错误捕获、超时重试等层层适配。

最令团队沮丧的是，他们意识到这种集成工作没有尽头。明年可能换一个新的降雨预报模型，后年可能加一个基于大语言模型的调度建议生成工具，每一次变化都意味着重新做一遍适配。

这就是MCP要解决的根本问题：让工具提供方和工具使用方解耦。Agent只关心"我能调用什么功能"，工具提供方只关心"如何实现这个功能"，MCP作为中间层负责翻译和路由。

> **AI解读：** 这个故事揭示了工具集成中的"N×M问题"：如果有N个Agent（或Skill）和M个工具，没有统一协议时需要N×M个适配器。MCP将这个问题降为N+M：每个工具实现一次MCP接口，每个Agent通过MCP调用一次。这种复杂度降级是MCP最直接但也最容易被低估的工程价值。

---

## 10.1 MCP在HydroOS中的定位 [L1]

### 10.1.1 协议分层：MCP、OPC-UA、Modbus的职责边界

HydroOS中的协议体系至少包含三个层次。理解它们的差异，是理解MCP定位的前提。

**表10-1：HydroOS协议分层与职责边界**

| 协议层 | 代表协议 | 操作对象 | 抽象层级 | 典型延迟 | 安全模型 |
|-------|---------|---------|---------|---------|---------|
| 设备层 | Modbus, DNP3, IEC 60870 | 寄存器、线圈、模拟量 | 物理信号 | <100ms | 无/弱 |
| 控制层 | OPC-UA | 变量、方法、事件 | 设备语义 | <50ms | 证书+签名+加密 |
| 认知层 | MCP | 工具（Tools）、资源（Resources）、提示（Prompts） | AI可理解的语义 | 100ms-10s | Token+Scope+审计 |

第5章已经详细讨论了设备层和控制层的协议统一问题——用OPC-UA统一Modbus、DNP3等异构协议。但OPC-UA解决的是"如何从闸门PLC读取开度值"这种物理设备和控制系统之间的通信问题。MCP解决的是另一个层次的问题："AI Agent如何告诉一个水文模型执行一次72小时预报"——它要处理更多样的数据格式、更复杂的错误语义、更细粒度的权限控制。

换句话说，OPC-UA让所有设备说同一种"设备语言"，MCP让所有AI工具说同一种"工具语言"。两者不是竞争关系，而是分层协作关系。

### 10.1.2 MCP的核心抽象

MCP协议的核心抽象有三种：

**工具（Tools）**：可以被Agent调用的函数。类似REST API中的POST端点，但带有结构化的输入参数schema和输出schema。Agent通过MCP发现可用工具、理解每个工具的功能描述和参数要求，然后发起调用。

示例工具定义（简化版）：
```json
{
  "name": "run_streamflow_forecast",
  "description": "运行指定流域未来72小时的径流预报模型",
  "inputSchema": {
    "type": "object",
    "properties": {
      "basin_id": {"type": "string", "description": "流域编码"},
      "forecast_hours": {"type": "integer", "min": 1, "max": 168},
      "model_version": {"type": "string"}
    },
    "required": ["basin_id", "forecast_hours"]
  }
}
```

**资源（Resources）**：可以被Agent读取的数据文件、数据库表、配置项。类似REST API中的GET端点。资源是只读的，Agent通过MCP获取资源内容。

**提示（Prompts）**：预定义的提示模板，用于引导Agent的下游LLM推理。这不是Agent调用工具，而是Agent从MCP获取"如何更好地使用这些工具"的指导信息。

> **AI解读：** MCP的三抽象设计（Tool / Resource / Prompt）对应了Agent与外部世界交互的三种基本模式：执行（Tool）、感知（Resource）、理解（Prompt）。这种分类不是学术上的整洁癖好，而是为Agent提供了一个稳定、可扩展、可理解的外部世界模型。Agent的推理引擎只需要理解这三种抽象，就能与任何MCP兼容的工具交互。

---

## 10.2 工具注册与发现机制 [L2]

### 10.2.1 工具注册流程

每个MCP Server在启动时向HydroOS的工具注册中心（Tool Registry）注册它所提供的工具列表。注册流程包含以下步骤：

**步骤1：Server身份认证**。Server使用X.509证书向注册中心证明身份。证书中包含Server所归属的管理域和信任级别。

**步骤2：能力声明**。Server提交其工具列表的JSON Schema定义，包括每个工具的输入参数、输出格式、执行时间估计、并发能力上限。

**步骤3：ODD声明**。Server声明每个工具的适用ODD范围。例如，一个针对淮河流域训练的洪水预报模型，应声明其ODD为`{region: "Huaihe", rainfall_range: [0, 200]mm/h}`。当Agent在ODD范围外调用该工具时，注册中心会返回警告。

**步骤4：健康检查注册**。Server提供一个heartbeat端点，注册中心每隔T_heartbeat秒探测。连续N次探测失败后，注册中心将该Server标记为unavailable，并将其工具从可用列表中移除。

**步骤5：权限策略配置**。Server为每个工具声明默认的访问控制策略——哪些角色/Agent可以调用、是否需要人工审批、调用频率上限。

### 10.2.2 工具发现查询

Agent通过以下查询接口发现工具：

```
list_tools(
  capability_description: str,    // 自然语言描述所需功能
  required_inputs: [str],         // 必须兼容的输入参数类型
  odd_constraints: {region, ...}, // ODD约束过滤
  max_latency_ms: int             // 最大延迟约束
) -> [ToolDescriptor]
```

查询结果按匹配度排序，返回每个工具的名称、描述、输入schema、ODD范围、历史平均执行时间。Agent根据这些信息选择最合适的工具。

[工程解释] 工具发现的查询接口采用了"语义匹配"而非"精确关键字匹配"。Agent可以用自然语言描述需求（如"我需要一个能预测未来降雨的工具"），注册中心通过嵌入向量相似度匹配找到相关工具。这是MCP区别于传统服务发现（如DNS、Consul）的关键特征——Agent不是人，它需要一种机器可理解的服务描述方式，而自然语言描述+schema约束是目前实践中效果最好的折中方案。

---

## 10.3 工具调用与权限控制 [L2]

### 10.3.1 同步调用与异步调用

MCP支持两种调用模式：

**同步调用**：Agent发起请求后阻塞等待结果。适用于执行时间短（<5秒）、需要立即使用结果的计算任务，如读取实时水位数据、查询历史统计值。

**异步调用**：Agent发起请求后立即返回task_id，后续通过轮询或回调获取结果。适用于执行时间长（数分钟）的计算任务，如运行72小时水文预报模型、执行多目标优化求解。异步调用是水网场景的默认模式——大多数水利模型的计算时长以分钟计，不能让Agent线程一直阻塞等待。

异步调用的任务状态机：
```
PENDING → QUEUED → RUNNING → COMPLETED
                         ↘ FAILED
                         ↘ CANCELLED
```

### 10.3.2 权限模型

MCP的权限控制采用**基于属性的访问控制（ABAC）**模型，比传统RBAC更灵活。每个工具调用请求需要满足以下条件：

- **主体属性**：调用方的Agent类型、WNAL等级、所属管理域
- **客体属性**：工具的安全等级（Safety Level）、影响的物理范围
- **环境属性**：当前ODD状态、系统运行模式（正常/应急/维护）
- **动作属性**：读操作还是写操作、是否涉及物理设备控制

权限裁决在MCP Server的请求拦截器中执行，而非在Agent侧。这确保了权限控制不会被Agent绕过——即使Agent被攻破或设计有缺陷，工具层仍然有独立的防护。

### 10.3.3 写操作的"双人原则"

对于涉及物理控制的写操作（如"开启3号闸门到50%开度"、"启动应急泵组"），MCP强制执行"双人原则"（Two-Person Rule）：

1. Agent发起写操作请求后，MCP生成一个操作预授权单（Operation Pre-Authorization Ticket）
2. 该预授权单必须经由人类操作员在L4应用层的Dashboard上点击确认
3. 确认后的操作才被MCP转发到OPC-UA协议层执行
4. 预授权单有timeout（默认60秒），超时未确认则自动失效

这是CHS"人机共治"原则在工具层的工程体现——AI可以建议，但不能替代人类对关键物理操作的最终授权。

---

## 10.4 Skill与MCP的层次关系 [L2]

### 10.4.1 为什么Skill≠MCP Tool

这是最容易被混淆的概念，需要明确区分。

**MCP Tool是原子能力单元**——它做一件具体的事，如"读取数据库中的今日水位"、"执行一次水文模型预报"、"发送一条HTTP请求"。Tool不包含业务逻辑编排。

**Skill是编排单元**——它组合多个Tool（以及可能多个其他Skill）完成一个有业务含义的工作。Skill包含编排逻辑、前置条件校验、异常处理、结果验证。

以"防汛预警生成"为例：
- **MCP Tool层**：有三个原子工具——`get_rainfall_forecast`（获取降雨预报）、`run_hydrological_model`（运行水文模型）、`query_reservoir_status`（查询水库状态）
- **Skill层**：有一个"防汛预警生成"Skill，它编排这三个Tool的调用顺序、传递中间结果、校验每个Tool的输出、处理可能的失败，最终生成一份结构化的预警报告

**表10-2：Skill与MCP Tool的对比**

| 维度 | Skill | MCP Tool |
|------|-------|---------|
| 抽象层级 | 业务编排层 | 能力原子层 |
| 是否包含业务逻辑 | 是（编排、校验、处理） | 否（纯功能执行） |
| 是否可被Agent直接调用 | 是（Agent通过Skill注册中心调用） | 是（但通常通过Skill间接调用） |
| 是否可被其他Skill调用 | 是（链式组合） | 是（作为原子能力被Skill使用） |
| 版本管理 | Skill版本（含编排逻辑） | Tool版本（含实现逻辑） |
| 定义位置 | 《平台》第 3 章 Skill系统 | 《平台》第 10 章 MCP工具生态 |

简单记忆法：**Skill定义"做什么、按什么顺序做"，MCP Tool定义"每个步骤用什么工具做"**。Skill是乐谱，Tool是乐器。

### 10.4.2 MCP与HydroMind Skill体系的接口

在HydroClaw认知架构中，Agent通过HydroMind的Skill体系表达任务意图。当Skill需要执行具体操作时，通过MCP调用底层Tool。完整的调用链是：

```
Agent → 选择Skill → Skill->执行计划 → Skill步骤调用MCP Tool → MCP Server执行 → 返回结果
```

MCP为HydroMind的Skill提供了统一的工具接口——Skill开发者不需要关心底层工具的实现细节，只需要通过MCP标准的接口调用工具。这使得Skill可以跨不同的底层工具实现而保持可移植性。

> **本章前置阅读**：《平台》第 3 章（Skill系统）、《平台》第 5 章（硬件集成层——OPC-UA协议栈）、《水控》§14.2（HydroClaw认知架构中Tool层的定位）
>
> **本章后续进阶**：《算法》第 7 章（Skill的算法实现与Tool调用优化——如何选择最优Tool组合、如何优化Tool调用延迟）

---

## 10.5 工具安全性：沙箱隔离与审计 [L2]

### 10.5.1 工具执行的沙箱模型

由于MCP工具本质上允许Agent（可能由LLM驱动）执行任意代码，安全性是MCP设计的核心约束。MCP工具执行采用"三级沙箱"模型：

**Level 1 — 只读沙箱**：工具只能读取数据（数据库查询、文件读取、API GET），不能写入或修改任何东西。这是大多数分析类工具的默认安全级别。

**Level 2 — 受限写沙箱**：工具可以在指定的受限范围内写入（如在特定数据库表中插入记录、在指定目录写入日志文件），但不能修改生产配置或控制物理设备。

**Level 3 — 全权限**：工具可以执行任何操作，包括物理设备控制。仅当同时满足以下条件时才启用：(a) 操作获得人类操作员授权、(b) 系统运行在Normal或Restricted态、(c) ODD未越界。

### 10.5.2 工具调用审计

每个MCP工具调用都产生一条审计记录，包含：调用时间戳、调用方Agent ID、工具名称、输入参数（脱敏处理后的摘要）、输出结果摘要、执行耗时、是否成功。审计记录写入防篡改日志存储，满足《标治》第 10 章的合规审计要求。

> **AI解读：** 工具安全性在AI Agent系统中是一个容易被低估的风险。一个看似无害的"查询数据库"工具，可能在LLM产生幻觉时被生成恶意的SQL注入——这是AI与传统软件安全问题的交叉地带。MCP的沙箱+权限+审计三重防护，不是在信任Agent的基础上"加把锁"，而是在假设Agent"可能犯任何错误"的前提下设计的安全边界。

---

## 参考文献

[10-1] Anthropic. (2024). *Model Context Protocol Specification*. https://modelcontextprotocol.io
[10-2] IEC 62541-1. (2020). *OPC Unified Architecture - Part 1: Overview and Concepts*.
[10-3] Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proceedings of the IEEE*, 63(9), 1278-1308.
[10-4] Hu, V. C., et al. (2014). Guide to attribute based access control (ABAC) definition and considerations. *NIST Special Publication*, 800-162.
[10-5] Fielding, R. T. (2000). *Architectural Styles and the Design of Network-based Software Architectures*. PhD Thesis, UC Irvine.
[10-6] Lei, X. et al. (2025b). 水系统控制论：学科转向. *南水北调与水利科技*.
[10-7] Newman, S. (2021). *Building Microservices* (2nd ed.). O'Reilly Media.
