# 总序卷第6章来源笔记

## 来源 1：Designing human-in-the-loop autonomous Cyber-Physical Systems

- 来源链接：<https://www.sciencedirect.com/science/article/pii/S1071581919300461>
- 用途：作为第6章中“人机在环”“人工接管”“边界内自主而非无限自主”的理论锚点。

### 已获取的关键表述

根据页面正文可直接提炼出以下判断：

> an autonomous system cannot be fully automated and that human involvement is required to execute some tasks.

> humans are required for intimate collaboration with ACPSs in the execution of certain tasks that cannot be performed autonomously (“human-in-the-loop”).

> ACPSs are required to explain their behavior to humans, provide them with feedback, and to allow them to override system actions.

> Human integration into the ACPS must be natural, robust, and non-intrusive.

### 本章写作含义

该文献可用于支撑第6章的核心判断：高等级自主运行并不等于取消人工，而是必须把人工接管、反馈解释和越权覆盖写入系统边界与验证链之中。它也可直接支撑“xIL 与人工接管流程图”的理论前提。

## 来源 2：Testing, validation, and verification of robotic and autonomous systems: a systematic review

- 来源链接：<https://dl.acm.org/doi/10.1145/3542945>
- 用途：作为第6章中测试、验证、确认（V&V）以及 xIL 验证流程的候选综述来源。

### 当前状态

该页面遭遇验证码阻断，尚未获取有效正文摘录，因此当前只能将其记录为候选来源，不能作为已完成引文证据直接入稿。

### 本章写作含义

若后续需要补强第6章的验证方法综述，可考虑改找可直接访问的替代来源，或在必要时再请求用户协助完成验证码页面接管。

## 当前可直接落稿的论证节点

| 论证节点 | 可支撑来源 | 用法 |
|---|---|---|
| 高等级自主运行不等于取消人工介入 | 来源 1 | 用于第6章导言和运行等级边界段 |
| 人工接管应被视为设计要求而非失败补丁 | 来源 1 | 用于第6章“人机接管与回退机制”段 |
| 自主系统必须能向人解释行为并允许 override | 来源 1 | 用于第6章“xIL 与解释反馈”段 |
| V&V/xIL 需要再补一条可直接访问的综述来源 | 来源 2 当前不可直接使用 | 作为后续补强动作 |

## 来源 3：An Overview of Verification and Validation Challenges for Inspection Robots

- 来源链接：<https://www.mdpi.com/2218-6581/10/2/67>
- 用途：作为第6章中 testing、validation、verification、安全可靠性与部署前论证链的开放获取综述来源。

### 已获取的关键表述

根据摘要与引言部分可直接提炼出以下判断：

> we still need to carry out a range of verification and validation tasks to ensure that the systems to be deployed are as safe and reliable as possible.

> Without the latter, engineers, regulators, and users will have little confidence that these robotic solutions are indeed safe, reliable and effective.

### 本章写作含义

该综述可用于支撑第6章的一个核心结论：验证与确认不是部署后补充动作，而是部署前形成工程信任、监管信任和用户信任的前提。它适合作为 xIL 与整体验证链的外部方法论补充来源。

## 来源 4：PAS1883 ODD 规范

- 来源链接：<https://www.bsigroup.com/globalassets/localfiles/en-gb/cav/pas1883.pdf>
- 用途：作为第6章 ODD 定义与边界结构化表达的标准来源候选。

### 当前状态

浏览访问该 PDF 时返回错误页面，尚未取得正文内容，因此当前只能保留为候选标准来源，暂不能直接摘录入稿。

### 本章写作含义

如后续需要正式引入 ODD 的标准文本，需继续寻找可访问副本或替代开放来源；在当前阶段，可先用域无关 ODD 文献和本书内部对象语言完成章节成稿框架。
