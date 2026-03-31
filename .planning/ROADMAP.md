# Roadmap — CHS全系列书稿CPSS统一框架修改 v1.0

## Vision

以CPSS为统一屋顶、反馈为核心公理，建立CHS全系列书稿一致的理论层次感。

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | T1理论卷CPSS重构 | 建立全系列理论根基 | T1-01~08 | 8 |
| 2 | T2b技术卷下统一Agent+XIL | 统一agent概念，四预闭环工程化 | T2B-01~06 | 6 |
| 3 | T4平台卷闭环内核 | 闭环四预在HydroOS中落地 | T4-01~03 | 3 |
| 4 | T2a技术卷上闭环视角 | 控制方法增加闭环耦合和agent统一视角 | T2A-01~07 | 7 |
| 5 | T3工程标准卷+四预标准 | 工作流标准化+新增四预工程标准章 | T3-01~04 | 4 |
| 6 | T5智能决策卷agent回归 | 防止沦为AI手册，回归CHS统一视角 | T5-01~05 | 5 |
| 7 | 全系列贯穿统一 | 术语统一、定位图、导论定位段落 | CROSS-01~03 | 3 |

**Total: 7 phases | 33 requirements | 100% coverage**

---

## Phase Details

### Phase 1: T1理论卷CPSS重构

**Goal:** T1是全系列的理论根基，CPSS框架、智能体定义、闭环/开环区分、四预闭环都必须先在这里建立，其他卷才能引用。

**Requirements:** T1-01, T1-02, T1-03, T1-04, T1-05, T1-06, T1-07, T1-08

**Success criteria:**
1. ch02包含智能体统一定义表（PID/MPC/RL/LLM Agent五维对齐）
2. ch03包含CHS六元组→CPSS三空间映射图和说明
3. ch07包含反馈作为元原理的明确论述
4. ch08包含三重反馈回路（P↔C/C↔S/S↔P）、确定性/灵活性工作流谱系、闭环vs开环范式区分
5. ch08包含基于CHS的四预闭环体系完整论述（含宏观/实时双尺度）
6. ch10包含WNAL=Social→Cyber决策权让渡的CPSS解读
7. ch14以"Cyber空间智能体谱系"视角重构
8. ch15包含CHS作为CPSS水利实例化的学术定位声明

### Phase 2: T2b技术卷下统一Agent+XIL

**Goal:** T2b是AI与控制论统一的关键卷。重写导论叙事，建立RL-MPC对偶性，精确定位LLM Agent，把XIL升级为四预工程实现。

**Requirements:** T2B-01, T2B-02, T2B-03, T2B-04, T2B-05, T2B-06

**Success criteria:**
1. ch01导论以"Cyber空间决策机制扩展"为主线，不再暗示AI替代控制
2. ch05包含RL与MPC对偶性分析（Bellman方程共同根基）
3. ch06包含LLM Agent=Social↔Cyber翻译层的精确定位
4. ch07包含多智能体的CPSS三空间分布式耦合视角 + 确定性/灵活编排区分
5. ch08包含WNAL各等级的工作流特性对照表
6. ch10包含XIL=四预工程实现的完整论述（MIL/SIL/HIL/OIL→预演四层）+ 宏观/实时XIL区分

### Phase 3: T4平台卷闭环内核

**Goal:** T4-ch04步长级仿控耦合是全系列最关键的技术章节，需要扩展为闭环四预在HydroOS中的完整实现架构。

**Requirements:** T4-01, T4-02, T4-03

**Success criteria:**
1. ch01包含SCADA局限性分析（只有P↔C闭环，缺C↔S闭环）及HydroOS进化方向
2. ch04包含时间步内闭环四预实现架构（多模型耦合协议、确定性/灵活双引擎、开环降级机制）
3. ch05包含硬件层=确定性工作流物理保证的论述

### Phase 4: T2a技术卷上闭环视角

**Goal:** 在扎实的控制与优化方法基础上，增加闭环耦合视角和agent统一框架。

**Requirements:** T2A-01, T2A-02, T2A-03, T2A-04, T2A-05, T2A-06, T2A-07

**Success criteria:**
1. ch01包含本卷CPSS定位说明
2. ch05/ch06/ch07包含agent统一视角（PID=reactive, 状态反馈=model-based, MPC=planning agent）
3. ch07包含MPC闭环本质与四预对应关系
4. ch09包含可控可观性对AI Agent约束含义
5. ch12包含分层架构与CPSS时间尺度对应
6. ch13以P→C投影函数视角重构数字孪生，区分实时同步/离线仿真
7. ch14-15案例包含闭环/开环对比分析

### Phase 5: T3工程标准卷+四预标准

**Goal:** 把确定性/灵活性工作流区分落地为标准，新增四预工程标准章。

**Requirements:** T3-01, T3-02, T3-03, T3-04

**Success criteria:**
1. ch04包含各WNAL等级的工作流确定性要求
2. ch05包含ODD对工作流模式的约束定义
3. ch06包含四态机跳转触发工作流切换机制
4. 新增章节"四预工程标准"包含闭环四预工程实施标准（时间步长要求、模型耦合接口规范、闭环响应时间指标、开环降级条件）

### Phase 6: T5智能决策卷agent回归

**Goal:** 防止T5沦为AI技术手册，回归CHS统一视角，建立与控制论的有机联系。

**Requirements:** T5-01, T5-02, T5-03, T5-04, T5-05

**Success criteria:**
1. ch01包含水利AI特殊性=Physical空间约束优势的论述
2. ch02+ch05包含预报与调度模型闭环耦合问题
3. ch05包含RL与MPC时间尺度分工协作模式
4. ch06以Social空间知识Cyber化视角重构知识图谱
5. ch08案例包含闭环/开环实践对比（含效果数据）

### Phase 7: 全系列贯穿统一

**Goal:** 最后做全系列贯穿修改，确保术语一致、定位清晰。放在最后是因为前6个phase的修改可能会产生新的术语需要统一。

**Requirements:** CROSS-01, CROSS-02, CROSS-03

**Success criteria:**
1. 全系列术语表发布（含智能体、闭环控制、开环执行、确定性/灵活工作流等核心定义）
2. CPSS三空间定位图完成，各卷导论均包含该图并标注本卷覆盖区域
3. 六本书导论均包含"本卷在CPSS中的定位"段落

## Dependency Notes

- Phase 1（T1理论卷）必须最先完成，其他所有phase引用T1建立的概念框架
- Phase 2-6 可在Phase 1完成后并行执行，但建议按优先级顺序
- Phase 7 必须最后执行，收集前6个phase产生的所有新术语

## Current Phase

Phase 1 — T1理论卷CPSS重构

---
*Updated: 2026-03-31*
