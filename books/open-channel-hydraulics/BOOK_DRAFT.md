# Open Channel Hydraulics - Independent Draft

## Generation Metadata
- generated_at_utc: 2026-03-05T09:04:09.170889+00:00
- engine_mode: placeholder
- chapter_count: 13
- case_count: 31

## Intro Seed
## 章节列表
- ch01: 明渠水力学基础 (案例1-3)
- ch02: 均匀流与临界流 (案例1-3)
- ch03: 水工建筑物 (案例4-7)
- ch04: 非均匀流 (案例8-9)
- ch05: 复杂系统水力计算 (案例10-12)
- ch06: 非恒定流理论 (案例13-15)
- ch07: 数值算法详解 (案例16-17)
- ch08: 高级应用 (案例18-20)
- ch09: 有压流稳态 (案例21-24)
- ch10: 有压流瞬态 (案例25-28)
- ch11: 管网计算 (案例22-23,28)
- ch12: 混合系统 (案例29)
- ch13: 综合应用 (案例30)

## 代码与实战参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

本书是 CHS-Books 遗留资产中的优质项目。所有相关源码及工程案例均可用于深入学习与推演。

---

## Included File: `ch01.md`

---
title: "明渠水力学基础"
sidebar_position: 2
---

# 明渠水力学基础

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 01-03.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例1-3

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例1-3。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 01: 案例1：农村灌溉渠流量计算

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 明渠水力学基础** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_01_irrigation` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 02: 案例2：城市雨水排水渠设计

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 明渠水力学基础** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_02_drainage` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 03: 案例3：景观水渠水流状态分析

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 明渠水力学基础** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_03_landscape` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "均匀流与临界流"
sidebar_position: 3
---

# 均匀流与临界流

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases none.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例1-3

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例1-3。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

---

## Included File: `ch03.md`

---
title: "水工建筑物"
sidebar_position: 4
---

# 水工建筑物

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 04-07.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例4-7

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例4-7。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 04: 案例4：灌区量水堰流量测量

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 水工建筑物** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_04_weir` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 05: 案例5：渠道闸门出流计算

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 水工建筑物** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_05_gate` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 06: 案例6：跌水消能设计

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 水工建筑物** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_06_drop` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 07: 案例7：渠道水面曲线计算

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 水工建筑物** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_07_profile` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "非均匀流"
sidebar_position: 5
---

# 非均匀流

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 08-09.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例8-9

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例8-9。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 08: 案例8：桥梁壅水分析

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 非均匀流** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_08_bridge` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 09: 案例9：河道糙率率定

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 非均匀流** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_09_roughness` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "复杂系统水力计算"
sidebar_position: 6
---

# 复杂系统水力计算

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 10-12.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例10-12

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例10-12。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 10: 案例10：复式断面河道

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 复杂系统水力计算** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_10_compound` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 11: 案例11：渠道变宽与收缩

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 复杂系统水力计算** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_11_transition` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 12: 案例12：涵洞过流

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 复杂系统水力计算** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_12_culvert` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch06.md`

---
title: "非恒定流理论"
sidebar_position: 7
---

# 非恒定流理论

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 13-15.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例13-15

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例13-15。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 13: 案例13：明渠非恒定流基础

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 非恒定流理论** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_13_unsteady` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 14: 案例14：洪水演进计算

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 非恒定流理论** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_14_flood_routing` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 15: 案例15：溃坝波计算

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 非恒定流理论** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_15_dam_break` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch07.md`

---
title: "数值算法详解"
sidebar_position: 8
---

# 数值算法详解

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 16-17.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例16-17

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例16-17。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 16: 案例16：渠道非恒定流调度

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 数值算法详解** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_16_canal_operation` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 17: 案例17：潮汐河口非恒定流

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 数值算法详解** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_17_tidal_river` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch08.md`

---
title: "高级应用"
sidebar_position: 9
---

# 高级应用

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 18-20.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例18-20

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例18-20。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 18: 案例18：明渠波动与反射

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 高级应用** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_18_wave_reflection` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 19: 案例19：多闸门渠系动态调度优化

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 高级应用** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_19_dynamic_scheduling` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 20: 案例20：二维明渠水流模拟

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 高级应用** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_20_2d_flow` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch09.md`

---
title: "有压流稳态"
sidebar_position: 10
---

# 有压流稳态

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 21-24.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例21-24

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例21-24。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 21: 案例21：城市供水管道水力计算

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流稳态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_21_pipe_flow` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 22: 案例22：管网平衡计算

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流稳态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_22_pipe_network` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 23: 案例23：长距离输水管道设计

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流稳态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_23_long_distance` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 24: 案例24：虹吸与倒虹吸设计

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流稳态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_24_siphon` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch10.md`

---
title: "有压流瞬态"
sidebar_position: 11
---

# 有压流瞬态

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 25-28.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例25-28

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例25-28。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 25: 案例25：水锤基础

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流瞬态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_25_water_hammer` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 26: 案例26：特征线法MOC

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流瞬态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_26_moc` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 27: 案例27：泵站瞬变过程

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流瞬态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_27_pump_transients` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 28: 案例28：调压井

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 有压流瞬态** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_28_surge_tank` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch11.md`

---
title: "管网计算"
sidebar_position: 12
---

# 管网计算

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases none.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例22-23,28

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例22-23,28。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

---

## Included File: `ch12.md`

---
title: "混合系统"
sidebar_position: 13
---

# 混合系统

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 29-29.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例29

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例29。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 29: 案例29：渠道-管道耦合系统

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 混合系统** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_29_channel_pipe` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch13.md`

---
title: "综合应用"
sidebar_position: 14
---

# 综合应用

## Reconstructed Theoretical Background
This chapter belongs to **Open Channel Hydraulics** and frames a coherent learning arc for cases 30-30.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `open-channel-hydraulics`
- 覆盖范围: 案例30

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例30。

## 代码与依赖参考
- `code/models/channel.py`
- `code/models/structures.py`
- `code/solvers/steady/uniform_flow.py`
- `code/solvers/steady/profile.py`
- `code/solvers/saint_venant.py`
- `code/examples/run_all_examples.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 30: 案例30：泵站-渠道-管道综合系统

### 🌟 案例背景 (Context)
        This case in **Open Channel Hydraulics / 综合应用** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_30_comprehensive` 目录。基于 CHS-Books-Old 资产迁移。
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
