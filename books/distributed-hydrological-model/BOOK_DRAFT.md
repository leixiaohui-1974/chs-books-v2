# Distributed Hydrological Model - Independent Draft

## Generation Metadata
- generated_at_utc: 2026-03-05T09:04:09.094984+00:00
- engine_mode: placeholder
- chapter_count: 13
- case_count: 24

## Intro Seed
## 章节列表
- ch01: 分布式水文模型概论 (案例1-2)
- ch02: 流域空间离散化 (案例1-3)
- ch03: 降雨空间插值 (案例2-3)
- ch04: 产流模拟 (案例4-6)
- ch05: 坡面汇流 (案例7)
- ch06: 河道汇流 (案例8,10)
- ch07: 蒸散发模拟 (案例4-6)
- ch08: 参数率定与不确定性 (案例11-12)
- ch09: 在线辨识与同化 (案例13,21)
- ch10: 水文水动力耦合 (案例15,23)
- ch11: 人类活动影响 (案例16,19)
- ch12: 流域智能管理 (案例17-22,25)
- ch13: 综合应用案例 (案例14,23-25)

## 代码与实战参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

本书是 CHS-Books 遗留资产中的优质项目。所有相关源码及工程案例均可用于深入学习与推演。

---

## Included File: `ch01.md`

---
title: "分布式水文模型概论"
sidebar_position: 2
---

# 分布式水文模型概论

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 01-02.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例1-2

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例1-2。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 01: 案例1：DEM分析与河网提取

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 分布式水文模型概论** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_01_dem_analysis` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 02: 案例2：Thiessen多边形降雨插值

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 分布式水文模型概论** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_02_thiessen` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "流域空间离散化"
sidebar_position: 3
---

# 流域空间离散化

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 03-03.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例1-3

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例1-3。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 03: 案例3：IDW与Kriging空间插值对比

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 流域空间离散化** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_03_idw_kriging` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "降雨空间插值"
sidebar_position: 4
---

# 降雨空间插值

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases none.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例2-3

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例2-3。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

---

## Included File: `ch04.md`

---
title: "产流模拟"
sidebar_position: 5
---

# 产流模拟

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 04-06.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例4-6

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例4-6。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 04: 案例4：新安江模型产流计算

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 产流模拟** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_04_xaj_model` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 05: 案例5：Green-Ampt超渗产流模型

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 产流模拟** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_05_green_ampt` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 06: 案例6：分布式产流网格模型

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 产流模拟** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_06_distributed_runoff` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "坡面汇流"
sidebar_position: 6
---

# 坡面汇流

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 07-07.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例7

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例7。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 07: 案例7：坡面运动波汇流

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 坡面汇流** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_07_slope_routing` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "河道汇流"
sidebar_position: 7
---

# 河道汇流

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 08-08.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例8,10

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例8,10。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 08: 案例8：单元线法河道汇流

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 河道汇流** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_08_unit_hydrograph` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "蒸散发模拟"
sidebar_position: 8
---

# 蒸散发模拟

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases none.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例4-6

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例4-6。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

---

## Included File: `ch08.md`

---
title: "参数率定与不确定性"
sidebar_position: 9
---

# 参数率定与不确定性

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 11-12.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例11-12

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例11-12。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 11: 案例11：SCE-UA参数率定算法

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 参数率定与不确定性** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_11_sce_calibration` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 12: 案例12: GLUE不确定性分析

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 参数率定与不确定性** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_12_glue_uncertainty` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "在线辨识与同化"
sidebar_position: 10
---

# 在线辨识与同化

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases none.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例13,21

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例13,21。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

---

## Included File: `ch10.md`

---
title: "水文水动力耦合"
sidebar_position: 11
---

# 水文水动力耦合

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 15-15.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例15,23

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例15,23。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 15: 案例15：水文-水动力耦合模拟

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 水文水动力耦合** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_15_hydro_dynamic_coupling` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "人类活动影响"
sidebar_position: 12
---

# 人类活动影响

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 16-16.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例16,19

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例16,19。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 16: 案例16：人类活动对产汇流影响评估

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 人类活动影响** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_16_human_impact` 目录。基于 CHS-Books-Old 资产迁移。
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

## Included File: `ch12.md`

---
title: "流域智能管理"
sidebar_position: 13
---

# 流域智能管理

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 17-22.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例17-22,25

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例17-22,25。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 17: 案例17：水库优化调度（基于规则）

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 流域智能管理** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_17_reservoir_operation` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 18: 案例18：实时洪水预报调度系统

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 流域智能管理** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_18_forecast_operation` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 19: 案例19: 气候变化对水文过程影响评估

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 流域智能管理** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_19_climate_change` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 20: 案例20：多水库梯级联合调度

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 流域智能管理** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_20_cascade_reservoirs` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 21: 案例21：实时校正模型

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 流域智能管理** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_21_realtime_correction` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 22: 案例22：GIS集成应用

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 流域智能管理** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_22_gis_integration` 目录。基于 CHS-Books-Old 资产迁移。
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
title: "综合应用案例"
sidebar_position: 14
---

# 综合应用案例

## Reconstructed Theoretical Background
This chapter belongs to **Distributed Hydrological Model** and frames a coherent learning arc for cases 09-25.
It reconstructs first-principles theory, links those principles to real constraints, and
connects model-based reasoning with deployable decisions.

Learning progression:
1. Understand dominant mechanisms
2. Build quantitative formulations
3. Validate and decide under constraints

## Original Chapter Seed
## 内容来源
- 书籍: `distributed-hydrological-model`
- 覆盖范围: 案例14,23-25

## 本章摘要
- 本章由Wave 1从目录与案例说明自动生成。该书籍代码与测试用例在 `CHS-Books` 仓库中已获得验证。
- 对应案例范围: 案例14,23-25。

## 代码与依赖参考
- `code/core/interpolation/thiessen.py`
- `code/core/interpolation/idw.py`
- `code/core/interpolation/kriging.py`
- `code/core/runoff_generation/xaj_model.py`
- `code/core/runoff_generation/green_ampt.py`
- `code/core/slope_routing/kinematic_wave.py`
- `code/core/channel_routing/muskingum.py`
- `code/core/calibration/sce_ua.py`
- `code/core/calibration/glue.py`
- `code/core/assimilation/enkf.py`
- `code/core/coupling/saint_venant.py`
- `code/core/reservoir/optimization.py`

> 💡 **提示**: 本章节的核心机理均可通过 HydroDesktop 的认知大模型基于 RAG 服务自动溯源。

## Expanded Case Set

### Case 09: 案例9：参数敏感性分析

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 综合应用案例** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_09_sensitivity_analysis` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 10: 案例10：Muskingum-Cunge河道洪水演进方法

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 综合应用案例** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_10_muskingum_cunge` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 14: 案例14：完整流域分布式水文模型

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 综合应用案例** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_14_integrated_watershed` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 23: 案例23：分布式水文-水动力全耦合

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 综合应用案例** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_23_full_coupling` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 24: 案例24：流域数字孪生系统

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 综合应用案例** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_24_digital_twin` 目录。基于 CHS-Books-Old 资产迁移。
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

### Case 25: 案例25：智能水文预报平台

### 🌟 案例背景 (Context)
        This case in **Distributed Hydrological Model / 综合应用案例** should be grounded in dynamic systems,
        uncertainty, and physically consistent constraints.

        ### 🎯 问题描述 (Problem)
        Interpret the scenario as an operational context with safety, efficiency, and robustness trade-offs.

        ### 💡 解题思路 (Solution Approach)
        State assumptions explicitly, define operating ranges, and include failure triggers for invalid assumptions.

        ### 💻 代码执行与图表 (Code & Charts)
        Build a reproducible pipeline: data conditioning, baseline model, improved method, stress validation.
        ## 2.1 案例问题描述 (Case Problem Description)
- **业务/领域上下文**:
  提取自 `case_25_intelligent_forecast` 目录。基于 CHS-Books-Old 资产迁移。
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
