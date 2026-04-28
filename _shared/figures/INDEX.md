# CHS 共享根图索引

> **版本**：v1, 2026-04-26  
> **用途**：本目录列出所有"跨多卷复用的根图"。每个核心概念只有一张权威图，其他卷用路径引用而非重画。  
> **与 `FIGURES_MASTER_PROMPTS.md` 的关系**：本文件列已存在的根图；提示词文档列待新生的图。

---

## 〇、引用规则

各卷在使用本目录列出的共享根图时——

1. **路径引用**：直接引用 T1-CN 现有图的相对路径，**不在自己的 assets/ 下重复存**
2. **图题简化**：在引用卷使用 "图 X-Y　[主题]（同 T1-CN [图]，详见 T1-CN 第 X 章）"
3. **修订同步**：如根图需要更新，**只在 T1-CN 一处修改**，所有引用卷自动同步
4. **不强制改科普版**：T2-CN 已有的 100+ 张科普风格图保留自己的版本，**不强制改用共享根图**

---

## 一、共享根图清单（按概念）

### 1.1 八原理与 WNAL 体系

| 概念 | 权威路径 | 适用引用卷 |
|---|---|---|
| **八原理与 WNAL 映射** | `T1-CN/H/fig_08_principles_wnal_mapping.png` | T1 ch07/ch10/ch15 自用；T2b ch01 / T3 ch04 引用 |
| **八原理覆盖热力图** | `T1-CN/H/fig_15_02_principles_heatmap.png` | T1 ch15 自用；T2b ch01 引用 |
| **WNAL L0—L5 阶梯图** | `T1-CN/H/fig_08_wnal_ladder.png` | T2-CN ch05 / T2b ch08 / T3 ch04 |
| **WNAL 与原理映射** | `T1-CN/H/fig_10_03_principles_wnal_mapping.png` | T2b ch08 / T3 ch04 |
| **WNAL 评估雷达**（待生） | `T1-CN/H/fig_10_04_wnal_radar.png`（计划新生） | T1 ch10 自用 |

### 1.2 ODD / 安全包络 / xIL 验证

| 概念 | 权威路径 | 适用引用卷 |
|---|---|---|
| **ODD 与安全包络** | `T2a/assets/ch01/fig_01_05_odd_safety_envelope.png` | T1 ch10 / T2b ch08 / T3 ch05 / T5 ch06 |
| **xIL 与 WNAL（角度一）** | `T1-CN/H/fig_07_04_xil_wnal.png` | T1 ch07 自用；T2b ch09 / T3 ch08 引用 |
| **xIL 与 WNAL（角度二）** | `T1-CN/H/fig_09_02_xil_wnal.png` | T1 ch09 自用 |
| **xIL 与 WNAL（角度三）** | `T1-CN/H/fig_10_02_xil_wnal.png` | T1 ch10 自用；T5 ch06 引用 |

> 注：T1 内部 xIL 主题有 3 张图，可能存在冗余。建议作者拍板**一张作为权威版**，其余加 `_archive` 后缀归档。

### 1.3 CPSS / MBD / HDC 框架

| 概念 | 权威路径 | 适用引用卷 |
|---|---|---|
| **CPSS 三空间架构** | `T1-CN/H/fig_08_01_cpss_architecture.png` | T2-CN ch03 / T2b ch01 / T4 ch02 |
| **MBD 全生命周期框架** | `T1-CN/H/fig_03_10_mbd_framework.png`（含新 codex 版 `_codex_20260426.png`） | T2b ch09 / T3 ch04 / T3 ch08 / T4 ch01 |
| **HDC 三层架构（角度一）** | `T1-CN/H/fig_07_02_hdc_architecture.png` | T1 ch07 自用；T2b ch05 / T4 ch03 引用 |
| **HDC 信息流** | `T2a/assets/ch12/fig_12_01_hdc_info_flow.png` | T2a ch12 自用；T4 ch03 引用 |

### 1.4 物理 AI / 认知 AI 双引擎

| 概念 | 权威路径 | 适用引用卷 |
|---|---|---|
| **物理 AI / 认知 AI 工作流** | `T1-CN/H/fig_13_01_pai_cai_workflow.png` | T1 ch13 自用；T2-CN ch08 / T2b ch01/ch06 / T5 ch01 引用 |
| **AI 与控制映射** | `T2b/assets/ch01/fig_01_02b_ai_control_mapping.png` | T2b ch01 自用 |

### 1.5 五代演进

| 概念 | 权威路径 | 适用引用卷 |
|---|---|---|
| **五代演进图** | `T1-CN/H/fig_01_01_codex_20260426.png` | T1 ch01 自用；T2-CN ch01 引用 |

### 1.6 HydroOS 架构

| 概念 | 权威路径 | 适用引用卷 |
|---|---|---|
| **HydroOS 整体架构** | `T1-CN/H/fig_13_01_hydroos_overview.png` | T1 ch13 自用；T4 ch02 引用 |
| **HydroOS 详细架构** | `T1-CN/H/fig_13_02_hydroos_architecture.png` | T1 ch13 自用；T4 ch02 引用 |
| **HydroOS 五层（T4 工程版）** | `T4-Platform/assets/ch02/fig_02_01_hydroos_kernel.png`（待生） | T4 ch02 自用 |

> 注：T1 ch13 与 T4 ch02 都讲 HydroOS 架构，但 T1 是理论视角、T4 是工程实现视角。两套图并存合理，但应明确分工。

---

## 二、待生的共享根图（详见 FIGURES_MASTER_PROMPTS.md §二）

| 概念 | 计划路径 | 状态 |
|---|---|---|
| 二元水循环 | `_shared/figures/dualistic_water_cycle.png` | ❌ 真缺，待生 |
| 控制论经典反馈闭环 | `_shared/figures/cybernetics_feedback_loop.png` | ❌ 真缺，待生 |
| Agent 统一架构 | `_shared/figures/agent_unified_architecture.png` | ⚠️ 待核查 T1 ch02 现有 12 张图后决定 |
| CHS 八原理总览（环形） | `_shared/figures/chs_eight_principles_overview.png` | ⚠️ 待作者拍板是否需要"入口型总览图" |

---

## 三、各卷专属图清单（不进入共享）

各卷专属图（不被其他卷引用）放在各书自己的 `assets/<chXX>/` 下，不进入本索引。专属图清单见 `FIGURES_MASTER_PROMPTS.md` §四—§九。

---

## 四、维护规则

1. **新增共享图**：必须先在本索引登记，再在 `FIGURES_MASTER_PROMPTS.md` 写提示词
2. **修改共享图**：只能修改 T1-CN 权威路径，引用卷自动同步
3. **退役共享图**：在本索引标注 `[已退役]`，并指向替代图

---

*本索引 v1 由 Claude 在 2026-04-26 撰写，配合 FIGURES_MASTER_PROMPTS.md v3 使用。*
