# Task: 修改 T1-CN/ch14_final.md — 增加Cyber空间智能体谱系视角

## 概念背景

请先阅读 `.planning/phases/01-t1-cpss-restructure/CONTEXT.md`，这是你执行本任务所需的全部概念背景。

## 当前状态

ch14标题"物理AI与认知AI"，内容讲HydroCore（物理AI引擎，MPC/EKF）和HydroClaw（认知AI引擎，LLM/KG）的双引擎架构。

## 具体修改要求

### 修改1: 在导读之后、§14.1之前，新增一小节

标题："Cyber空间中的智能体谱系"

内容要点：

1. 从CPSS视角重新定位HydroCore和HydroClaw：
   - HydroCore = Physical↔Cyber界面的model-based agent（基于机理模型的决策）
   - HydroClaw = Cyber↔Social界面的general agent（基于语言的语义理解和策略解释）
   - 两者不是两个独立的AI系统，而是Cyber空间中不同层面的智能体

2. 智能体谱系的完整图景（简短段落）：
   - PLC硬逻辑 = Physical空间内的reactive agent（最快、最确定）
   - PID控制器 = Physical↔Cyber界面的reactive agent
   - MPC/EKF (HydroCore) = Cyber空间的model-based planning agent
   - RL策略网络 = Cyber空间的learning agent
   - LLM/KG (HydroClaw) = Cyber↔Social界面的general agent（最灵活、最不确定）
   - 从左到右：确定性递减、灵活性递增、决策复杂度递增

3. 关键结论：物理AI和认知AI不是两个独立领域，而是同一反馈原理在Cyber空间不同层面的实现。HydroCore的控制回路是确定性工作流，HydroClaw的语义理解是灵活工作流——两者通过"提议-验证-执行"闭环协同。

约600-800字。

### 修改2: 在现有HydroCore-HydroClaw协作机制部分

增加一段（约200字）论述确定性/灵活性工作流的区分：
- HydroCore的MPC控制回路 = 确定性工作流（每个步长严格执行感知-预测-优化-执行）
- HydroClaw的语义推理 = 灵活工作流（可以中断、改序、引入人类判断）
- 两者的协作本身也遵循确定性规则：HydroCore拥有安全否决权，这是一个硬约束

## 重要约束

- 不删除任何现有内容
- 风格与原文一致
- 不点名具体工程
- 文献引用格式 [14-xx]
- 总新增约800-1000字
