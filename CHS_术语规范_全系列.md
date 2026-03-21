# CHS 教材体系术语统一规范

**适用范围**: T1-CN, T2a, T2b, T2-CN, T3, T4, T5 全系列
**最后更新**: 2026-03-22

---

## 一、核心术语

| 中文规范 | 英文规范 | 缩写 | 首次定义 | 说明 |
|---------|---------|------|---------|------|
| 水系统控制论 | Cybernetics of Hydro Systems | CHS | T1-CN ch01 | 学科名称，全系列统一 |
| 水网自主等级 | Water Network Autonomy Levels | WNAL | T1-CN ch01 | **全系列使用WNAL**（非WSAL） |
| 运行设计域 | Operational Design Domain | ODD | T1-CN ch04 | 首次使用须给全称 |
| 安全包络 | Safety Envelope | — | T1-CN ch11 | 以中文"安全包络"为主，英文辅助 |
| 分层分布式控制 | Hierarchical Distributed Control | HDC | T1-CN ch07 | 首次使用须给全称 |
| 模型预测控制 | Model Predictive Control | MPC | T1-CN ch04 | 首次使用须给全称 |
| 积分-延迟-零点模型 | Integrator-Delay-Zero | IDZ | T1-CN ch04 | CHS核心模型 |
| 最小风险条件/状态 | Minimum Risk Condition | MRC | T1-CN ch10 | 四态机核心概念 |
| 在环测试 | In-the-Loop Testing | xIL | T1-CN ch11 | 含MIL/SIL/HIL/PIL |
| 水网操作系统 | HydroOS | — | T2b ch09 | 软件平台名称 |
| 基于模型的设计 | Model-Based Design | MBD | T3 ch08 | **非Model-Based Definition** |

## 二、WNAL等级名称（全系列统一）

| 等级 | 中文名称 | 英文名称 |
|------|---------|---------|
| L0 | 手动运行 | Manual Operation |
| L1 | 规则自动化 | Rule-based Automation |
| L2 | 条件自动化 | Conditional Automation |
| L3 | 条件自主 | Conditional Autonomy |
| L4 | 高度自主 | High Autonomy |
| L5 | 完全自主 | Full Autonomy |

## 三、八原理编号（教学版，全系列统一）

| 编号 | 中文名称 | 层级 |
|------|---------|------|
| P1 | 传递函数化 | 建模基础层 |
| P2 | 可控可观性 | 建模基础层 |
| P3 | 分层分布式 | 架构组织层 |
| P4 | 安全包络 | 架构组织层 |
| P5 | 在环验证 | 验证保障层 |
| P6 | 认知增强 | 协同智能层 |
| P7 | 人机共融 | 协同智能层 |
| P8 | 全生命周期自主演进 | 演进能力层 |

> 注：CHS理论论文使用不同编号体系（双四元组），映射关系见T1-CN第七章注释框7-B。

## 四、HDC控制层级命名（避免与WNAL混淆）

| 层级 | 规范写法 | 避免写法 |
|------|---------|---------|
| 安全保护层 | 第0层（Layer 0） | ~~L0层~~ |
| 本地调节层 | 第1层（Layer 1） | ~~L1层~~ |
| 协调优化层 | 第2层（Layer 2） | ~~L2层~~ |
| 计划调度层 | 第3层（Layer 3） | ~~L3层~~ |

## 五、五个控制本质（全系列统一）

1. 大时滞
2. 强耦合
3. 强约束
4. 强不确定性
5. 人机共治

> 注：**不使用**"非线性""多约束""不确定性"等替代说法。

## 六、工程数据统一

| 数据项 | 统一值 | 说明 |
|--------|-------|------|
| 胶东调水全长 | 571.4 km | 胶东地区引黄调水工程（南水北调东线） |
| 引黄济青段 | ~300 km | 需注明"引黄济青段"或"引黄济青工程" |

## 七、各卷定位声明

每卷 ch01 须包含以下定位说明：

- **T1-CN**: 水系统控制论（本科教材）
- **T2a**: CHS教材体系·建模与控制（研究生上册）
- **T2b**: CHS教材体系·认知AI工程版（研究生下册）
- **T2-CN**: CHS科普读物·水网觉醒
- **T3**: CHS教材体系·智能化标准与工程治理
- **T4**: CHS教材体系·平台开发分册 ✅ 已添加
- **T5**: CHS教材体系·智能算法分册 ✅ 已添加
