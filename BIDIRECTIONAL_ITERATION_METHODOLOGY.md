# 书稿与代码测试案例双向迭代机制
## Bidirectional Iteration Methodology

## 1. 目标与范围
本文定义 `CoupledTank`、`Alumina`、`Hydrology` 三本书与代码/测试资产的双向迭代机制，用于实现以下目标：

1. **书稿驱动代码与测试开发**：每章的理论、模型、约束、场景都落成可执行工件。
2. **代码与测试反哺书稿**：每个关键论断都对应可复现实验、可追溯测试与可引用结果。
3. **建立统一证据链**：章节内容 <-需求ID-> 模块 <-测试ID-> CI报告 <-图表/表格-> 书稿。

适用对象：教材作者、算法工程师、MCP 服务开发者、测试工程师、审稿人。

## 2. 双向迭代总体机制
### 2.1 A向：书稿 -> 代码/测试（Book-to-Code/Test）
1. **章节拆解**：从每章提取 `概念声明`、`数学声明`、`工程声明`、`案例声明`。
2. **需求编号**：为每个声明建立 `BOOK-<book>-CH<nn>-REQ<nn>`。
3. **工件映射**：为每个需求绑定 `Python Core Module`、`MCP Tool/Server`、`Pytest Case`。
4. **最小可验证交付**：每章至少具备 1 个可执行示例 + 1 组自动化测试。
5. **合入门槛**：章节对应测试在 CI 通过，且输出结果可被书稿引用。

### 2.2 B向：代码/测试 -> 书稿（Code/Test-to-Book）
1. **自动产出证据**：CI 输出关键指标（误差、超调、能耗、告警率、时延等）与图表。
2. **书稿引用规范**：在章内标注 `Test ID`、`数据版本`、`提交哈希`、`运行日期`。
3. **回归触发修订**：若测试失败或指标退化，自动生成书稿修订任务（章节、段落、图号）。
4. **审稿可复验**：审稿人按 `pytest -k <test_id>` 能重现实验证论。

## 3. 版本与节奏
### 3.1 迭代节奏（建议）
1. **周节奏**：每周一次“章节-代码-测试”闭环。
2. **里程碑节奏**：每完成 2 章，进行一次跨章回归（含 MCP 联调）。
3. **发布节奏**：每月一次 `Book Evidence Release`（书稿快照 + 测试快照）。

### 3.2 四道质量门（Gates）
1. `G1 章节需求冻结`：章节声明完成编号与映射。
2. `G2 模块可运行`：核心模块单测通过。
3. `G3 服务可调用`：MCP Server 合同测试通过。
4. `G4 书稿可引用`：图表/指标可追溯到测试证据。

## 4. 统一命名与追溯约定
### 4.1 模块命名（建议）
- `src/coupled_tank/*`
- `src/alumina/*`
- `src/hydrology/*`

### 4.2 MCP Server 命名（建议）
- `mcp/coupled_tank_server.py`
- `mcp/alumina_evap_server.py`
- `mcp/hydrology_server.py`

### 4.3 Pytest 命名（建议）
- `tests/<domain>/test_chXX_<topic>.py`
- 用例ID：`TC_<BOOK>_CH<nn>_<keyword>`

## 5. 三书映射矩阵（Chapter -> Module -> MCP -> Pytest）
说明：以下为实施结构与建议命名，可按实际代码库落地路径微调，但需保持可追溯。

### 5.1 CoupledTank 映射矩阵
| Chapter | Python Core Modules | MCP Servers / Tools | Pytest Test Cases |
|---|---|---|---|
| Ch1 水务液位控制痛点 | `src/coupled_tank/problem_model.py` | `coupled_tank_server.describe_pain_points` | `tests/coupled_tank/test_ch01_problem_baseline.py` |
| Ch2 双容水箱物理与数学模型 | `src/coupled_tank/dynamics.py`, `src/coupled_tank/ode_solver.py` | `coupled_tank_server.simulate_dynamics` | `tests/coupled_tank/test_ch02_mass_balance.py`, `test_ch02_ode_stability.py` |
| Ch3 PID 到 MPC | `src/coupled_tank/pid.py`, `src/coupled_tank/mpc.py` | `coupled_tank_server.compare_pid_mpc` | `tests/coupled_tank/test_ch03_pid_vs_mpc.py` |
| Ch4 L0-L4 全栈架构 | `src/coupled_tank/stack/l0_core.py`, `l1_gateway.py`, `l4_agent_adapter.py` | `coupled_tank_server.run_closed_loop` | `tests/coupled_tank/test_ch04_stack_contract.py` |
| Ch5 CC-Desktop 与决策助理 | `src/coupled_tank/nlu_intent.py`, `schema_template.py` | `coupled_tank_server.nl_to_control_json` | `tests/coupled_tank/test_ch05_intent_to_json.py` |      
| Ch6 典型控制场景 | `src/coupled_tank/scenarios.py` | `coupled_tank_server.run_scenario` | `tests/coupled_tank/test_ch06_scenario_fill_no_overflow.py`, `test_ch06_disturbance_rejection.py` |
| Ch7 结果与诊断分析 | `src/coupled_tank/diagnostics.py`, `kpi.py` | `coupled_tank_server.generate_diagnosis` | `tests/coupled_tank/test_ch07_kpi_consistency.py` |
| Ch8 从水箱到宏大水网 | `src/coupled_tank/scaling.py` | `coupled_tank_server.map_to_network` | `tests/coupled_tank/test_ch08_scaling_mapping.py` |

### 5.2 Alumina 映射矩阵
| Chapter | Python Core Modules | MCP Servers / Tools | Pytest Test Cases |
|---|---|---|---|
| Ch1 蒸发工序痛点 | `src/alumina/process_baseline.py` | `alumina_evap_server.describe_process_risks` | `tests/alumina/test_ch01_baseline_profile.py` |
| Ch2 物理机理与数学模型 | `src/alumina/thermo_balance.py`, `two_phase_flow.py` | `alumina_evap_server.solve_balance` | `tests/alumina/test_ch02_energy_mass_balance.py` |
| Ch3 智能协同控制架构 | `src/alumina/distributed_control.py`, `advanced_pid_mpc.py` | `alumina_evap_server.optimize_operating_point` | `tests/alumina/test_ch03_control_strategy_switch.py` |
| Ch4 核心算法实现 | `src/alumina/nonlinear_solver.py`, `sqp_optimizer.py` | `alumina_evap_server.run_optimization` | `tests/alumina/test_ch04_sqp_constraints.py`, `test_ch04_solver_convergence.py` |
| Ch5 知识映射与工作台 | `src/alumina/mbd_mapping.py`, `parameter_extractor.py` | `alumina_evap_server.extract_and_plan` | `tests/alumina/test_ch05_mapping_template.py` |
| Ch6 典型生产场景 | `src/alumina/scenarios.py` | `alumina_evap_server.run_production_scenario` | `tests/alumina/test_ch06_steam_drop_emergency.py`, `test_ch06_feed_disturbance.py` |    
| Ch7 结果导向分析 | `src/alumina/diagnostic_report.py`, `energy_kpi.py` | `alumina_evap_server.generate_report` | `tests/alumina/test_ch07_kpi_traceability.py` |
| Ch8 跨界融合展望 | `src/alumina/cross_domain_mapping.py` | `alumina_evap_server.map_to_water_network` | `tests/alumina/test_ch08_cross_domain_transfer.py` |

### 5.3 Hydrology 映射矩阵
| Chapter | Python Core Modules | MCP Servers / Tools | Pytest Test Cases |
|---|---|---|---|
| Ch1 智能水文背景 | `src/hydrology/domain_context.py` | `hydrology_server.describe_context` | `tests/hydrology/test_ch01_context_assumptions.py` |
| Ch2 数字水文概念 | `src/hydrology/concepts.py`, `hydro_entities.py` | `hydrology_server.validate_hydro_entities` | `tests/hydrology/test_ch02_entities_schema.py` |
| Ch3 核心水文能力 | `src/hydrology/rainfall_runoff.py`, `routing.py` | `hydrology_server.run_core_features` | `tests/hydrology/test_ch03_runoff_routing.py` |
| Ch4 数字孪生对象与MBD | `src/hydrology/mbd_schema.py`, `topology_index.py` | `hydrology_server.export_mbd_objects` | `tests/hydrology/test_ch04_mbd_schema_contract.py` |
| Ch5 预报与模拟算法 | `src/hydrology/forecast/conceptual_model.py`, `ml_forecast.py` | `hydrology_server.run_forecast` | `tests/hydrology/test_ch05_forecast_accuracy.py` |
| Ch6 优化调控算法 | `src/hydrology/optimization/mpc_dispatch.py` | `hydrology_server.optimize_dispatch` | `tests/hydrology/test_ch06_mpc_constraints.py` |
| Ch7 API 设计 | `src/hydrology/api/resources.py`, `jobs.py` | `hydrology_server.query_resources` | `tests/hydrology/test_ch07_api_resource_contract.py`, `test_ch07_async_jobs.py` |     
| Ch8 MCP 协议集成 | `src/hydrology/mcp/schema.py`, `prompt_contract.py` | `hydrology_server.mcp_toolkit` | `tests/hydrology/test_ch08_mcp_schema_stability.py` |
| Ch9 Skills 工作流 | `src/hydrology/skills/review_forecast.py`, `compliance_report.py` | `hydrology_server.run_skill` | `tests/hydrology/test_ch09_skill_workflow.py` |
| Ch10 Agent 架构 | `src/hydrology/agents/dispatcher.py`, `analyzer.py`, `controller.py` | `hydrology_server.route_agent_task` | `tests/hydrology/test_ch10_agent_role_boundary.py` |     
| Ch11 城市内涝案例 | `src/hydrology/use_cases/urban_flood.py` | `hydrology_server.run_urban_flood_case` | `tests/hydrology/test_ch11_end_to_end_urban_flood.py` |
| Ch12 引调水与水库群案例 | `src/hydrology/use_cases/reservoir_system.py`, `water_quality_incident.py` | `hydrology_server.run_reservoir_case` | `tests/hydrology/test_ch12_reservoir_multiobjective.py`, `test_ch12_wq_incident_trace.py` |
| Ch13 部署与SRE | `src/hydrology/sre/sli_slo.py`, `reliability_checks.py` | `hydrology_server.health_and_slo` | `tests/hydrology/test_ch13_sli_slo_compliance.py` |

## 6. 双向迭代执行清单（每章）
1. 从章节提取 3-8 条“可验证声明”并编号。
2. 完成模块实现或更新，确保声明有对应可执行逻辑。
3. 完成最少 1 个单元测试 + 1 个场景测试（或合同测试）。
4. 在 MCP Server 暴露对应能力，补齐输入输出 Schema。
5. CI 生成图表/指标并归档到章节证据目录。
6. 书稿更新引用：插入 Test ID、结果摘要、版本哈希。

## 7. 验收标准（Definition of Done）
对任一章节，只有同时满足以下条件才算完成：

1. `章节声明覆盖率` >= 90%（声明有映射模块+测试）。
2. 对应 `pytest` 全绿，且关键阈值（精度/稳定性/时延）达标。
3. MCP 调用链可复现章节中的至少一个核心图表或结论。
4. 书稿可追溯到具体测试与代码版本（含日期与提交哈希）。

---

该机制确保三本书不是“先写完再补代码”，也不是“先写代码再补叙述”，而是通过同一证据链持续双向迭代，形成可验证、可教学、可工程复用的统一资产。