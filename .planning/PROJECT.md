# CHS 全系列书稿 CPSS 统一框架修改

## What This Is

对 `chs-books-v2/` 中的 5 本水系统控制论系列书稿进行系统性概念架构升级。不是重写内容，而是在现有扎实章节基础上，以 CPSS（信息-物理-社会系统）为统一屋顶、反馈为核心公理，建立全系列一致的理论层次感。

书稿清单：
- `T1-CN/`（15章）：理论卷 — 水系统控制论原理
- `T2a/`（16章）：技术卷上 — 经典/现代控制、MPC、优化
- `T2b/`（14章）：技术卷下 — AI/RL/多智能体、HydroOS
- `T3-Engineering/`（13章）：工程标准卷
- `T4-Platform/`（8章）：平台卷 — HydroOS
- `T5-Intelligence/`（8章）：智能决策卷 — AI算法

## Core Value

**概念层统一性优先于内容增量。** 五本书的技术内容已经扎实，缺的是"屋顶"——CPSS作为统一框架、反馈作为核心公理、智能体作为统一概念的全系列贯穿。

## Current Milestone: v1.0 CPSS统一框架修改

**Goal:** 以CPSS为统一屋顶，对5本书稿进行系统性概念架构升级

**Target features:**
- CPSS三空间框架作为全系列主线（不再是T1-ch08的单章话题）
- 智能体统一定义贯穿（PID/MPC/RL/LLM Agent同属感知-决策-行动-反馈范式）
- 闭环/开环范式显式区分（时间步内耦合 vs 模型串行）
- 确定性/灵活性工作流谱系（Physical确定→Social灵活）
- 四预闭环重构（预报预警预演预案的CHS闭环解读）
- 宏观/实时双尺度分层
- 全系列术语统一和CPSS定位图
- XIL作为四预工程实现的显式关联

## Context

### 核心概念共识（来自讨论）

1. **CPSS是屋顶，CHS是承重结构：**
   - P/A → Physical空间，S/D/C → Cyber空间，O → Social空间
   - 三重嵌套反馈：P↔C（秒级）、C↔S（小时级）、S↔P（年级）

2. **智能体统一定义：**
   - Agent = (Perception, Decision, Action, Objective, Environment)
   - PID=reactive agent, MPC=planning agent, RL=learning agent, LLM=general agent
   - 差异仅在决策机制复杂度，反馈原理不变

3. **闭环vs开环：**
   - 闭环：每个时间步内多模型耦合迭代（控制）
   - 开环：模型A跑完全时段再传给模型B（仿真）
   - 当前四预实践大多是开环串行，应为时间步内闭环

4. **工作流谱系：**
   - Physical空间 → 确定性工作流（物理因果律不可违）
   - Social空间 → 灵活性工作流（人类决策情境依赖）
   - Cyber空间 → 混合

5. **四预闭环重构：**
   - 预报=S+D前向推演，预警=ODD状态评估
   - 预演=XIL验证，预案=C的实时决策输出
   - 区分宏观尺度（灵活，Social主导）和实时尺度（确定性，Physical主导）

6. **WNAL的CPSS本质：**
   - Social空间向Cyber空间的决策权渐进让渡

### 修改优先级

1. T1-ch08 CPSS重构 — 理论根基，影响全系列叙事
2. T2b-ch01导论重写 + ch10 XIL扩展 — 统一agent概念 + 四预闭环
3. T4-ch04步长级仿控耦合扩展 — 闭环引擎是平台灵魂
4. T2a-ch07 MPC与四预关联 — 理论-实践桥梁
5. T3工作流标准化 — 确定性/灵活性区分落地为标准
6. T5回归agent统一视角 — 防止沦为AI技术手册
7. 全系列术语统一 + 定位图

## Constraints

- **只改概念架构层**：不动现有技术内容的正确性
- **增量式修改**：在现有章节中增加/扩展段落和小节，不重写整章
- **保持书稿风格一致**：修改内容的语言风格与原书一致

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 在chs-books-v2内建独立.planning | 不影响research根目录的其他项目 | Accepted |
| CPSS作为全系列屋顶而非单章 | CPSS应贯穿而非孤立介绍 | Accepted |
| 按书分phase执行 | 每本书的修改相对独立，可并行 | Accepted |
| 优先T1理论卷 | 理论根基影响全系列叙事 | Accepted |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-03-31 — Milestone v1.0 initialized*
