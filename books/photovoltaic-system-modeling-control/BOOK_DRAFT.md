# Photovoltaic System Modeling Control - Independent Draft

## Generation Metadata
- generated_at_utc: 2026-03-05T09:04:09.198709+00:00
- engine_mode: placeholder
- chapter_count: 5
- case_count: 20

## Intro Seed
## 章节列表
- ch01: 光伏电池与阵列建模 (案例1-5)
- ch02: MPPT最大功率追踪 (案例6-10)
- ch03: 逆变器并网控制 (案例11-15)
- ch04: 微电网孤岛运行 (案例16-20)
- ch05: 水光互补与水面光伏(水能纽带) (新增)

## 代码与测试覆盖
- `code/core/water_energy_nexus.py`
- `tests/test_pv_water.py`

本书是 CHS-Books 遗留资产在 Wave 2/3 阶段并入的优质项目。
我们对底层计算接口（如生态基流、Saint-Venant 求解、HIL/SIL验证、水能枢纽等）进行了严格的 Pytest 补充测试，以符合 HydroDesktop 平台“代码即证据”的底线原则。

---

## Included File: `ch01.md`

---
title: "光伏电池与阵列建模"
sidebar_position: 2
---

# 光伏电池与阵列建模

## Reconstructed Theoretical Background
This chapter belongs to **Photovoltaic System Modeling Control** and frames a coherent learning arc for cases 01-05.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 章节概述
- 书籍: `photovoltaic-system-modeling-control`
- 内容范围: 案例1-5

## 核心机制
- 本章作为 光伏系统建模与控制 的关键组成部分，探讨了 光伏电池与阵列建模 在水务/能源联合调度中的数学机理与控制策略。
- 尤其针对此前缺乏测试的环节，我们在 `code/core` 下补充了核心函数，并在 `tests/` 目录下添加了验证用例。

## 代码与依赖参考
- `code/core/water_energy_nexus.py`
- `tests/test_pv_water.py`

> 💡 **提示**: 您可以在 HydroDesktop 的 Agent 中随时基于本章理论提问，获取跨域知识的融合解答。

## Expanded Case Set

### Case 01: 案例1: 光伏电池I-V特性建模

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 光伏电池与阵列建模** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_01_pv_cell_iv_characteristics` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 02: 案例2: 双二极管精确模型

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 光伏电池与阵列建模** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_02_double_diode_model` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 03: 案例3: 光伏组件建模

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 光伏电池与阵列建模** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_03_pv_module_modeling` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 04: 案例4: 光伏阵列配置

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 光伏电池与阵列建模** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_04_pv_array_configuration` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 05: 案例5: 遮挡分析与诊断

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 光伏电池与阵列建模** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_05_shading_analysis` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "MPPT最大功率追踪"
sidebar_position: 3
---

# MPPT最大功率追踪

## Reconstructed Theoretical Background
This chapter belongs to **Photovoltaic System Modeling Control** and frames a coherent learning arc for cases 06-10.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 章节概述
- 书籍: `photovoltaic-system-modeling-control`
- 内容范围: 案例6-10

## 核心机制
- 本章作为 光伏系统建模与控制 的关键组成部分，探讨了 MPPT最大功率追踪 在水务/能源联合调度中的数学机理与控制策略。
- 尤其针对此前缺乏测试的环节，我们在 `code/core` 下补充了核心函数，并在 `tests/` 目录下添加了验证用例。

## 代码与依赖参考
- `code/core/water_energy_nexus.py`
- `tests/test_pv_water.py`

> 💡 **提示**: 您可以在 HydroDesktop 的 Agent 中随时基于本章理论提问，获取跨域知识的融合解答。

## Expanded Case Set

### Case 06: 案例6: 参数辨识方法

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / MPPT最大功率追踪** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_06_parameter_identification` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 07: 案例7: P&O扰动观察法

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / MPPT最大功率追踪** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_07_perturb_observe` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 08: 案例8: 增量电导法

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / MPPT最大功率追踪** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_08_incremental_conductance` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 09: 案例9: 恒电压法

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / MPPT最大功率追踪** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_09_constant_voltage` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 10: 案例10: 模糊逻辑MPPT

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / MPPT最大功率追踪** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_10_fuzzy_logic` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "逆变器并网控制"
sidebar_position: 4
---

# 逆变器并网控制

## Reconstructed Theoretical Background
This chapter belongs to **Photovoltaic System Modeling Control** and frames a coherent learning arc for cases 11-15.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 章节概述
- 书籍: `photovoltaic-system-modeling-control`
- 内容范围: 案例11-15

## 核心机制
- 本章作为 光伏系统建模与控制 的关键组成部分，探讨了 逆变器并网控制 在水务/能源联合调度中的数学机理与控制策略。
- 尤其针对此前缺乏测试的环节，我们在 `code/core` 下补充了核心函数，并在 `tests/` 目录下添加了验证用例。

## 代码与依赖参考
- `code/core/water_energy_nexus.py`
- `tests/test_pv_water.py`

> 💡 **提示**: 您可以在 HydroDesktop 的 Agent 中随时基于本章理论提问，获取跨域知识的融合解答。

## Expanded Case Set

### Case 11: 案例11: 粒子群优化MPPT

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 逆变器并网控制** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_11_pso_mppt` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 12: 案例12: 多峰MPPT算法

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 逆变器并网控制** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_12_multi_peak_mppt` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 13: 案例13: PWM调制技术

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 逆变器并网控制** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_13_pwm_modulation` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 14: 案例14: 电流控制

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 逆变器并网控制** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_14_current_control` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 15: 案例15: 电压控制

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 逆变器并网控制** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_15_voltage_control` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "微电网孤岛运行"
sidebar_position: 5
---

# 微电网孤岛运行

## Reconstructed Theoretical Background
This chapter belongs to **Photovoltaic System Modeling Control** and frames a coherent learning arc for cases 16-20.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 章节概述
- 书籍: `photovoltaic-system-modeling-control`
- 内容范围: 案例16-20

## 核心机制
- 本章作为 光伏系统建模与控制 的关键组成部分，探讨了 微电网孤岛运行 在水务/能源联合调度中的数学机理与控制策略。
- 尤其针对此前缺乏测试的环节，我们在 `code/core` 下补充了核心函数，并在 `tests/` 目录下添加了验证用例。

## 代码与依赖参考
- `code/core/water_energy_nexus.py`
- `tests/test_pv_water.py`

> 💡 **提示**: 您可以在 HydroDesktop 的 Agent 中随时基于本章理论提问，获取跨域知识的融合解答。

## Expanded Case Set

### Case 16: 案例16: 并网同步控制 - 锁相环(PLL)设计

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 微电网孤岛运行** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_16_grid_synchronization` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 17: 案例17: 功率因数控制

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 微电网孤岛运行** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_17_power_factor_control` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 18: 案例18: 谐波抑制

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 微电网孤岛运行** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_18_harmonic_suppression` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 19: 案例19: DC/DC变换器建模

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 微电网孤岛运行** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_19_dcdc_converter` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 20: 案例20: 直流母线电压控制

### 🌟 案例背景 (Context)
        This case in **Photovoltaic System Modeling Control / 微电网孤岛运行** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_20_dc_bus_control` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "水光互补与水面光伏(水能纽带)"
sidebar_position: 6
---

# 水光互补与水面光伏(水能纽带)

## Reconstructed Theoretical Background
This chapter belongs to **Photovoltaic System Modeling Control** and frames a coherent learning arc for cases none.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 章节概述
- 书籍: `photovoltaic-system-modeling-control`
- 内容范围: 新增

## 核心机制
- 本章作为 光伏系统建模与控制 的关键组成部分，探讨了 水光互补与水面光伏(水能纽带) 在水务/能源联合调度中的数学机理与控制策略。
- 尤其针对此前缺乏测试的环节，我们在 `code/core` 下补充了核心函数，并在 `tests/` 目录下添加了验证用例。

## 代码与依赖参考
- `code/core/water_energy_nexus.py`
- `tests/test_pv_water.py`

> 💡 **提示**: 您可以在 HydroDesktop 的 Agent 中随时基于本章理论提问，获取跨域知识的融合解答。

## Expanded Case Set

---
