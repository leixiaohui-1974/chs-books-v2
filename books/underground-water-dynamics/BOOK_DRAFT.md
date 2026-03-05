# Underground Water Dynamics - Independent Draft

## Generation Metadata
- generated_at_utc: 2026-03-05T09:04:09.215248+00:00
- engine_mode: placeholder
- chapter_count: 5
- case_count: 20

## Intro Seed
## 章节列表
- ch01: 基础理论与数值方法 (案例1-5)
- ch02: 参数率定与不确定性分析 (案例6-10)
- ch03: 地表地下水耦合系统 (案例11-15)
- ch04: 人类活动影响评估 (案例16-18)
- ch05: 智能化与数字孪生 (案例19-20)

## 代码与实战参考
- `gwflow/grid/structured.py`
- `gwflow/solvers/steady_state.py`
- `gwflow/solvers/transient.py`
- `gwflow/calibration/pest.py`
- `gwflow/coupling/river_package.py`
- `gwflow/pumping/optimization.py`
- `gwflow/subsidence/subsidence_model.py`
- `gwflow/transport/advection_dispersion.py`
- `gwflow/digital_twin/digital_twin.py`
- `gwflow/optimization/multi_objective.py`

本书是 CHS-Books 遗留资产中的优质项目。所有相关源码及工程案例均可用于深入学习与推演。

---

## Included File: `ch01.md`

---
title: "基础理论与数值方法"
sidebar_position: 2
---

# 基础理论与数值方法

## Reconstructed Theoretical Background
This chapter belongs to **Underground Water Dynamics** and frames a coherent learning arc for cases 01-05.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `underground-water-dynamics`
- 覆盖范围: 案例1-5

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例1-5。

## 代码与依赖参考
- `gwflow/grid/structured.py`
- `gwflow/solvers/steady_state.py`
- `gwflow/solvers/transient.py`
- `gwflow/calibration/pest.py`
- `gwflow/coupling/river_package.py`
- `gwflow/pumping/optimization.py`
- `gwflow/subsidence/subsidence_model.py`
- `gwflow/transport/advection_dispersion.py`
- `gwflow/digital_twin/digital_twin.py`
- `gwflow/optimization/multi_objective.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 01: 案例1：一维稳态地下水流动

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 基础理论与数值方法** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_01` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 02: 案例2：二维稳态地下水流动与网格剖分

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 基础理论与数值方法** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_02` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 03: 案例3：非均质含水层模拟

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 基础理论与数值方法** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_03` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 04: 案例4：瞬态地下水流动

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 基础理论与数值方法** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_04` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 05: 案例5：有限元方法基础

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 基础理论与数值方法** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_05` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

---

## Included File: `ch02.md`

---
title: "参数率定与不确定性分析"
sidebar_position: 3
---

# 参数率定与不确定性分析

## Reconstructed Theoretical Background
This chapter belongs to **Underground Water Dynamics** and frames a coherent learning arc for cases 06-10.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `underground-water-dynamics`
- 覆盖范围: 案例6-10

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例6-10。

## 代码与依赖参考
- `gwflow/grid/structured.py`
- `gwflow/solvers/steady_state.py`
- `gwflow/solvers/transient.py`
- `gwflow/calibration/pest.py`
- `gwflow/coupling/river_package.py`
- `gwflow/pumping/optimization.py`
- `gwflow/subsidence/subsidence_model.py`
- `gwflow/transport/advection_dispersion.py`
- `gwflow/digital_twin/digital_twin.py`
- `gwflow/optimization/multi_objective.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 06: 案例6：参数率定基础（优化方法）

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 参数率定与不确定性分析** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_06` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 07: 案例7：PEST方法实现

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 参数率定与不确定性分析** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_07` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 08: 案例8：贝叶斯推断与MCMC

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 参数率定与不确定性分析** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_08` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 09: 案例9：敏感性分析深入

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 参数率定与不确定性分析** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_09` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 10: 案例10：不确定性量化

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 参数率定与不确定性分析** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_10` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

---

## Included File: `ch03.md`

---
title: "地表地下水耦合系统"
sidebar_position: 4
---

# 地表地下水耦合系统

## Reconstructed Theoretical Background
This chapter belongs to **Underground Water Dynamics** and frames a coherent learning arc for cases 11-15.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `underground-water-dynamics`
- 覆盖范围: 案例11-15

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例11-15。

## 代码与依赖参考
- `gwflow/grid/structured.py`
- `gwflow/solvers/steady_state.py`
- `gwflow/solvers/transient.py`
- `gwflow/calibration/pest.py`
- `gwflow/coupling/river_package.py`
- `gwflow/pumping/optimization.py`
- `gwflow/subsidence/subsidence_model.py`
- `gwflow/transport/advection_dispersion.py`
- `gwflow/digital_twin/digital_twin.py`
- `gwflow/optimization/multi_objective.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 11: 案例11：地表地下水耦合基础

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 地表地下水耦合系统** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_11` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 12: 案例12：MODFLOW River包实现

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 地表地下水耦合系统** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_12` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 13: 案例13：渗漏与越流模拟

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 地表地下水耦合系统** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_13` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 14: 案例14：耦合模型率定

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 地表地下水耦合系统** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_14` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 15: 案例15：耦合系统不确定性分析

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 地表地下水耦合系统** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_15` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

---

## Included File: `ch04.md`

---
title: "人类活动影响评估"
sidebar_position: 5
---

# 人类活动影响评估

## Reconstructed Theoretical Background
This chapter belongs to **Underground Water Dynamics** and frames a coherent learning arc for cases 16-18.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `underground-water-dynamics`
- 覆盖范围: 案例16-18

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例16-18。

## 代码与依赖参考
- `gwflow/grid/structured.py`
- `gwflow/solvers/steady_state.py`
- `gwflow/solvers/transient.py`
- `gwflow/calibration/pest.py`
- `gwflow/coupling/river_package.py`
- `gwflow/pumping/optimization.py`
- `gwflow/subsidence/subsidence_model.py`
- `gwflow/transport/advection_dispersion.py`
- `gwflow/digital_twin/digital_twin.py`
- `gwflow/optimization/multi_objective.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 16: 案例16：地下水开采优化

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 人类活动影响评估** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_16` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 17: 案例17：地面沉降模拟

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 人类活动影响评估** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_17` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 18: 案例18：污染物运移模拟

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 人类活动影响评估** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_18` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

---

## Included File: `ch05.md`

---
title: "智能化与数字孪生"
sidebar_position: 6
---

# 智能化与数字孪生

## Reconstructed Theoretical Background
This chapter belongs to **Underground Water Dynamics** and frames a coherent learning arc for cases 19-20.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `underground-water-dynamics`
- 覆盖范围: 案例19-20

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例19-20。

## 代码与依赖参考
- `gwflow/grid/structured.py`
- `gwflow/solvers/steady_state.py`
- `gwflow/solvers/transient.py`
- `gwflow/calibration/pest.py`
- `gwflow/coupling/river_package.py`
- `gwflow/pumping/optimization.py`
- `gwflow/subsidence/subsidence_model.py`
- `gwflow/transport/advection_dispersion.py`
- `gwflow/digital_twin/digital_twin.py`
- `gwflow/optimization/multi_objective.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 19: 案例19：地下水数字孪生架构

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 智能化与数字孪生** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_19` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

### Case 20: 案例20：智能决策支持系统

### 🌟 案例背景 (Context)
        This case in **Underground Water Dynamics / 智能化与数字孪生** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_20` 目录。基于 CHS-Books-Old 资产迁移。
- **输入数据概述**: 从 `README.md` 或入口脚本自动扫描提取约束边界。
## 2.2 解题思路 (Solution Approach)
- **算法/模型选择**: 遵循水力学/能量/质量守恒物理约束求解。
- **核心步骤**: 初始化 -> 数据注入 -> 核心求解器(如 Newton/SQP) -> 收敛性验证。
## 2.3 代码逻辑与执行 (Code Logic/Execution)
...

        ### 📊 结果白话解释 (Result Interpretation)
        Evaluate numerical performance, mechanism-level explanation, and transferability to neighboring conditions.

        ### 🚀 专家建议 (Recommendations)
        Include one conceptual question, one derivation task, one coding lab, and one reflection task.

---
