# 基于信息-物理-社会系统框架的国家水网全生命周期智能运行支撑体系

## 中文摘要

国家水网已由工程加速建设阶段转入“建设与智能运行并重”阶段，但规划静态化、设计碎片化、建设验证不足和运行经验驱动四类矛盾仍然并存。本文以水系统控制论（CHS）提出的信息-物理-社会系统（CPSS）为总框架，重构国家水网规划、设计、建设、运行全生命周期的智能运行支撑体系。首先，将Physical、Cyber、Social三空间与国家水网“纲、目、结”层级对应，进一步以六元组统一描述节点工程，明确可控可观性是智能运行的结构前提。其次，面向规划阶段提出基于可控可观性的拓扑优化、WNAL分级目标和ODD前置标定方法；面向设计阶段提出HDC分层分布式控制、数字孪生投影函数和闭环四预工程标准；面向建设阶段提出MIL、SIL、HIL、OIL递进验证、跨域安全包络和工作流分级建设；面向运行阶段提出闭环四预、四态机治理和L2至L3跃迁路径。以胶东调水工程为例，2024年3月水源切换实测表明，闭环四预将工况切换耗时由24 h压缩至6 h，水位控制精度提升至3 cm以内。研究表明，CPSS不是水网智能化的附属解释，而是国家水网智能运行的统一框架；闭环四预相较传统开环四预具有可验证、可落地、可复制的工程优势。

**关键词：** 国家水网；CPSS；闭环四预；WNAL；HDC；数字孪生；xIL；OIL

## Abstract

China's National Water Network is moving from rapid infrastructure expansion to a stage where construction and intelligent operation must advance together. However, four persistent contradictions still constrain performance: static planning, fragmented design, insufficient validation during construction, and experience-driven operation. This paper adopts the Cyber-Physical-Social Systems (CPSS) framework proposed by the Control Theory of Hydro-Systems (CHS) and reconstructs an intelligent operation support system for the full lifecycle of the National Water Network. First, the Physical, Cyber, and Social spaces are mapped to the hierarchical structure of the network, and a unified six-element model is used to describe node-level projects, highlighting controllability and observability as the structural prerequisites for intelligence. Second, for planning, a controllability-observability-based topology optimization method, WNAL grading targets, and front-loaded ODD calibration are proposed. For design, a hierarchical distributed control architecture, digital-twin projection function, and engineering standard for closed-loop four-prediction are established. For construction, progressive x-in-the-loop validation, cross-domain safety envelope design, and workflow grading are developed. For operation, closed-loop four-prediction, four-state governance, and an L2-to-L3 transition path are presented. Using the Jiaodong Water Diversion Project as a case study, field data from the March 2024 source-switching event show that the proposed closed-loop approach reduced transition time from 24 h to 6 h while keeping water-level error within 3 cm. The results indicate that CPSS should be treated as the unified framework for intelligent operation of the National Water Network, and that closed-loop four-prediction provides clear engineering advantages over the traditional open-loop paradigm.

**Keywords:** National Water Network; CPSS; closed-loop four-prediction; WNAL; HDC; digital twin; xIL; OIL

## 1 引言

国家水网正在从“重工程建设”走向“工程建设与运行智能并重”。这一转变并非简单的信息化升级，而是要求在规划、设计、建设、运行全链条中，把可感知、可计算、可调控、可治理作为同等重要的建设目标[1-5]。但现阶段仍存在四个突出矛盾。

其一，规划静态化。多数方案仍以设计水平年供需平衡和输配能力校核为主，对动态工况下网络可控可观性、测控冗余和运行边界缺少前置论证。规划阶段没有把“建成后能否稳定闭环运行”作为刚性指标，结果是一些工程直到投运后才暴露出测控先天不足。

其二，设计碎片化。水力、结构、机电、自控、通信、数字孪生往往按专业并行展开，接口靠后期协调，导致物理布置与信息架构错位。其直接后果不是单个子系统“不先进”，而是系统整体缺少统一反馈回路，最终难以形成真正可运行的智能控制体系。

其三，建设标准缺失。水利行业对控制算法、数字孪生和运行软件上线前的分级验证要求仍不完整，设计模型、施工模型、运行模型之间衔接松散。没有验证链条，就无法证明算法在故障、扰动、极端工况下仍满足安全与性能边界。

其四，运行经验驱动。传统“四预”多为预报、预警、预演、预案的串行组织，人工环节多、链路长、延迟大，误差沿流程单向积累[5]。当复杂扰动与多目标冲突叠加时，这种开环模式难以支撑分钟级、区段级乃至全网级的动态调控。

这四个矛盾的共同根源，是国家水网长期缺少一个能够同时解释物理过程、信息计算和治理约束的统一框架。学科脉络大致经历三步：首先，二元水循环理论把自然过程与社会用水过程纳入统一认识，为理解国家水网的“自然-社会”耦合奠定基础[22]；其次，控制论与系统科学将反馈、状态和决策引入工程系统，使水网从静态平衡对象转向动态调控对象[12,23]；进一步，CHS显式加入信息维度，形成CPSS框架，从而把水力过程、数字孪生、控制算法、规则体系和管理行为纳入同一分析语言[7-11]。因此，国家水网智能运行并不缺单点算法，缺的是统一框架。

前4篇CHS系列研究已分别完成理论框架、学科转向、WNAL架构与xIL验证体系的铺垫[8-11]。本文作为第5篇，不再展开PID、MPC、RL等具体方法谱系，而聚焦一个更直接的工程命题：CPSS如何转化为国家水网全生命周期的统一工程框架和闭环四预支撑体系。

本文创新点体现在3个方面：一是将CPSS从抽象概念压实为国家水网可执行的“三空间+六元组”统一表达，明确可控可观性是全部智能能力的结构前提；二是建立面向规划、设计、建设、运行的连续技术链条，使WNAL、ODD、HDC、xIL、四态机与闭环四预形成前后呼应的工程体系；三是以胶东调水2024年3月实测为证据，说明闭环四预并非概念升级，而是能显著缩短响应时滞、压制误差累积、提升运行稳定性的工程范式升级。

## 2 CPSS统一框架及其适用性

CPSS由Physical、Cyber、Social三空间组成。在国家水网中，Physical空间对应河湖水系、渠道、水库、泵站、闸门及其水力、水质、边坡、冰情等物理过程；Cyber空间对应传感、通信、数字孪生、状态估计、优化求解与控制执行；Social空间对应调度规程、管理权限、利益协调、供水目标与风险边界。三空间不是三套并列系统，而是通过感知、计算、执行、授权和约束构成连续耦合。

为避免概念化空转，本文将三空间进一步压缩为六元统一模型

$$
\Sigma = (P,\ A,\ S_e,\ D,\ C,\ O) \tag{1}
$$

式中，$P$为物理过程，$A$为执行器，$S_e$为传感器，$D$为数字孪生，$C$为控制与决策引擎，$O$为运行目标与边界。对于任一闸站、泵站、渠池或枢纽，六元组都能给出统一接口语言。其工程意义在于：不同专业不再围绕各自软件和图纸分头优化，而是围绕同一受控系统协同设计。

在国家水网场景中，三空间对应三重反馈回路。第一重是Physical与Cyber之间的秒至分钟级反馈，用于闸泵调节、水位控制和局地扰动抑制；第二重是Cyber与Social之间的小时至天级反馈，用于调度审批、约束更新和策略校正；第三重是Social与Physical之间的月年至多年级反馈，用于标准修编、工程改造和治理目标重构。三重回路与国家水网“结、目、纲”的层级高度契合：节点工程依赖快速闭环，区域水网依赖人机协同，骨干工程依赖长期适应。这也是图1所示全生命周期映射的理论基础。

![图1 CPSS三空间框架与国家水网全生命周期支撑映射](figures/fig1_cpss_lifecycle_mapping.png)

三空间与六元组合并后，可得到一个更直接的判断：国家水网的智能运行能力，不首先取决于算法是否先进，而首先取决于系统是否可控、可观。设线性化水网系统为

$$
\dot{\mathbf{x}}=\mathbf{A}\mathbf{x}+\mathbf{B}\mathbf{u},\quad \mathbf{y}=\mathbf{C}\mathbf{x} \tag{2}
$$

则可控与可观的基本判据为

$$
\operatorname{rank}\!\left[\mathbf{B}\ \mathbf{AB}\ \cdots\ \mathbf{A}^{n-1}\mathbf{B}\right]
=
\operatorname{rank}\!\left[\mathbf{C}^{\top}\ \mathbf{A}^{\top}\mathbf{C}^{\top}\ \cdots\ (\mathbf{A}^{\top})^{n-1}\mathbf{C}^{\top}\right]
= n \tag{3}
$$

若系统先天不可控或不可观，则更复杂的智能体只是在结构缺陷上叠加算力，无法从根本上提升运行能力。由此可见，CPSS对国家水网的价值不在于引入一个新名词，而在于把“物理约束、信息能力、治理边界”统一进一个可验证的闭环框架中。它既是国家水网智能运行的统一框架，也是全生命周期技术标准的上位逻辑。

## 3 CPSS对国家水网规划的支撑

规划阶段必须把MBD（Model-Based Design）前置。其核心不是“先建模型再做方案”，而是“在规划阶段就验证未来能否运行”，避免设计完成后才发现测控架构无法支撑闭环控制。对国家水网而言，MBD至少意味着：ODD前置定义、模型贯通设计、验证链条同步策划。

规划的首要任务是把可控可观性纳入拓扑比选。仅比较输水能力和投资成本，无法判断方案是否适于智能运行。对候选方案，应同时比较传感器布置、执行器配置、通信冗余及其对Gramian条件数的影响，并以“结构筛选+数值优化”的方式进行技术经济综合比选。工程上可将结论压缩为4类决策：完全可控且完全可观，可进入控制设计；完全可控但不完全可观，应优先补传感；不完全可控但完全可观，应优先补执行；两者均不足，则应返回拓扑重构。

WNAL是规划阶段连接“能力目标”和“投资配置”的关键语言。区段综合等级由最薄弱能力域决定，可表示为

$$
\mathrm{WNAL}_{\text{seg}}=\min_{d\in\mathcal{D}}\mathrm{WNAL}_d \tag{4}
$$

其中$\mathcal{D}$为感知、决策、执行、安全等能力域。该式意味着，国家水网不能以局部高配设备掩盖整体短板，等级提升必须围绕系统最薄弱环节展开。对于骨干输水干线，近期目标应是L3前的L2+到L3过渡；对于风险较低、工况较稳定区段，可采取分级达标而非一刀切高配。

ODD则把传统“设计工况”转化为可计算的运行边界。本文采用六维向量表示

$$
\mathbf{x}_{\mathrm{ODD}}=[H,\ I,\ E,\ R,\ C_a,\ M]^{\top} \tag{5}
$$

其中$H$为水文气象，$I$为基础设施状态，$E$为外部需求，$R$为风险边界，$C_a$为控制能力，$M$为通信条件。若当前工况满足自主运行准入，则至少应满足

$$
\lambda_{\min}(\mathbf{W}_c)\ge \lambda_c^{\mathrm{req}},\quad
\lambda_{\min}(\mathbf{W}_o)\ge \lambda_o^{\mathrm{req}} \tag{6}
$$

式(6)把ODD与可控可观性直接绑定，使自主运行不再依赖经验口径，而依赖可验证阈值。

在此基础上，WNAL可作为规划的目标语言，ODD可作为运行边界语言。前者回答“要达到什么等级”，后者回答“在什么条件下能够稳定达到”。两者共同构成规划阶段从静态水网走向可运行水网的关键支点。

## 4 CPSS对国家水网设计的支撑

设计阶段同样必须遵循MBD逻辑，即在图纸、模型、控制架构和验证需求之间形成闭环，而不是把智能化内容留给建成后的二次改造。设计阶段的核心任务，是把规划阶段的可控可观性目标、WNAL目标和ODD边界落到控制架构、数字孪生和工程标准上。

HDC（Hierarchical Distributed Control）是最适合国家水网的工程架构，其根本原因并不只是技术上“分层更稳”，而是它天然对齐现有组织管理体系。L0设备层负责本地保护与联锁，L1过程层负责站级或区段MPC，L2协调层负责全局优化与调度协调。三层时间尺度与CPSS三空间关系如图2所示。

![图2 HDC三层架构与CPSS三空间的时间尺度对应关系](figures/fig2_hdc_cpss_timescale.png)

HDC可概括为

$$
\mathcal{H}=\{L0_{\text{protect}},\ L1_{\text{process}},\ L2_{\text{coord}}\} \tag{7}
$$

其中L0解决毫秒至秒级安全，L1解决分钟级动态控制，L2解决小时级优化协调。其管理映射见表1。

**表1 HDC技术层与国家水网管理层映射**

| 管理层级 | HDC层级 | 时间尺度 | 主要职责 | 决策特征 |
|:--|:--|:--|:--|:--|
| 调度中心 | L2协调层 | 小时至天 | 全网优化、边界下发 | 规则与目标主导 |
| 分中心/管理处 | L1过程层 | 分钟至小时 | 区段控制、状态协调 | 模型驱动优化 |
| 现地站点 | L0设备层 | 毫秒至秒 | 联锁保护、就地执行 | 安全优先 |

数字孪生在设计阶段不应只被理解为“可视化平台”，而应被定义为Physical向Cyber的投影函数

$$
\hat{\mathcal{X}}_{C}(t)=\Pi_{P\rightarrow C}\!\left(\mathcal{X}_{P}(t)\right)+\boldsymbol{\epsilon}(t) \tag{8}
$$

设计目标不是消除误差，而是在运行域内持续压制$\|\boldsymbol{\epsilon}(t)\|$。为支撑在线控制，投影函数应满足“同化-降阶-预测-消费”的实时链路；为支撑离线验证，则应支持更高精度但非实时的冻结孪生。二者关系如图3所示。

![图3 数字孪生作为Physical到Cyber投影函数的两种运行模式](figures/fig3_dt_projection.png)

在此基础上，闭环四预不再是四个部门串行协作，而是每个控制步长内完成的统一计算过程。其设计约束可写为

$$
\Delta t_{\text{forecast}}+\Delta t_{\text{warning}}+\Delta t_{\text{rehearsal}}+\Delta t_{\text{plan}}
\le \Delta t \tag{9}
$$

为保证实时性，还需满足计算预算比

$$
\eta=\frac{\Delta t_{\text{compute}}}{\Delta t}\le \eta_{\max} \tag{10}
$$

设计阶段的“四预”参数应统一纳入控制标准、通信标准和算力标准，而不能散落在不同子系统招标文件中。所谓“四预一体”，本质就是把预报、预警、预演、预案压缩到同一闭环内完成，这正是CPSS框架下国家水网设计的最大工程收益。

## 5 CPSS对国家水网建设的支撑

建设阶段的核心不是把既有设计“照图施工”，而是把未来运行能力逐级验证出来。xIL应采用MIL、SIL、HIL、OIL的递进体系。MIL用于场景穷举和控制逻辑验证；SIL用于把算法原型落到目标软件栈并验证实时性；HIL用于暴露真实闸泵、PLC、传感器噪声和通信接口带来的硬件效应；OIL则以真实工程影子运行方式验证算法在实网中的性能、稳健性与可接受性。这里必须强调，水网应使用OIL，而非PIL。

跨域安全包络是建设阶段必须前置的第二项任务。国家水网的水力、水质、边坡、冰情、机电、通信并不是六个平行专业，而是存在级联传导的多域系统。设域$i$到域$j$的风险传导为

$$
s_j(t+\tau_{ij})=\max\!\left(s_j(t),\ \Gamma_{ij}(s_i(t))\right) \tag{11}
$$

其中状态按Normal、Restricted、Degraded、Managed的严重度递增。该式要求工程建设时就编制跨域耦合清单、传导延时和阻断策略，而不是等运行中被动发现级联故障。

典型级联场景是“水质异常触发取水约束，进而抬升上游水位并向边坡安全传导”，其跨域关系如图4所示。该图所强调的不是单域告警，而是风险在不同专业边界间的时间延迟和状态升级路径。

![图4 跨域安全包络级联传导示意](figures/fig4_cross_domain_cascade.png)

第三项任务是工作流分级建设。实时保护、联锁切换、故障降级必须采用确定性工作流；调度会商、策略审批、应急协同则保留灵活工作流。国家水网建设不能把全部流程都做成死逻辑，也不能把关键安全功能交给临场裁量。其原则是：越接近Physical空间，越要求确定性；越接近Social空间，越允许灵活性。

## 6 CPSS对国家水网运行的支撑

运行阶段最关键的变化，是把传统开环四预改造成闭环四预。开环四预以部门串行和人工衔接为特征，预报结果先产生，预警再研判，预演多停留在桌面推演，预案最终表现为静态文档；一旦现场偏离预测，只能等待下一轮流程重启。闭环四预则在每个控制步长内同时完成状态感知、预测、风险评估、可行性筛选和控制下发，执行结果在下一步立即回流修正。其步长内耦合位置如图5所示。

![图5 闭环四预在CPSS三空间中的定位与步长内耦合循环](figures/fig5_closed_loop_four_prediction.png)

开环与闭环的差异，不是“自动化多一点”而是运行范式不同。前者误差沿链路单向累积，后者误差在每步被压制；前者的端到端延迟通常为小时级，后者是分钟级甚至更短；前者依赖调度员在流程间补洞，后者依赖模型、规则和执行器共同构成完整反馈回路。因此，闭环四预的优势不是概念优势，而是工程优势。

这一运行范式还需要四态机治理托底。Normal对应正常闭环；Restricted对应边界收紧与功能限制；Degraded对应局部自治和性能降级；Managed对应人工接管与最小风险控制。与“Override”不同，本文统一使用Managed，强调其不是随意接管，而是有边界、有终态、有规则的管理状态。四态机的作用，是把异常处置从经验判断转为状态驱动执行，使跨域风险能够按规则传播、阻断与恢复。

L2向L3的跃迁则是国家水网运行升级的真正门槛。L2意味着常态工况自动运行但异常仍依赖人工；L3意味着在ODD内系统可自主识别、降级和恢复，只有超域时才要求人工介入。其瓶颈不只在算法精度，更在于3点：一是xIL标准和场景库不足，无法证明异常工况下的可靠性；二是可控可观性在线监控不足，ODD无法动态管理；三是行业信任与管理授权尚未完成。换言之，L3不是“再上一个优化器”就能实现，而是控制、验证和治理共同成熟的结果。

## 7 工程案例：胶东调水

胶东调水工程是典型的长距离、多水源、多层级、多目标调水系统。对本文而言，案例的意义不在于重复工程概况，而在于验证CPSS统一框架和闭环四预是否具有可测量的工程效益。工程具备多源切换、梯级泵站耦合、供水与能耗冲突、冰期与汛期叠加、三级管理协同等典型特征，因此能够代表国家水网骨干工程的复杂性。

在CPSS框架下，胶东调水将SCADA、数字孪生、边缘MPC和全局协调优化纳入统一闭环。L0层实现联锁保护，L1层以5 min为采样周期执行区段MPC，L2层执行小时级协调优化；同时通过双冗余通信和边缘盒子保障断网自治。其本质不是“在传统SCADA上叠加一个算法模块”，而是把原本松散的感知、预测、优化、执行和管理流程闭合起来。

2024年3月水源切换事件为本文提供了关键实测证据。同类工况下，传统开环模式通常需要24 h左右完成方案编制、逐级审批、站点执行和偏差修正；闭环模式下，L2一次性生成全流程目标轨迹，L1每5 min按实测状态滚动修正。实测结果表明，工况切换总耗时压缩至6 h，响应时滞由4~6 h降至约5 min，水位控制精度由±15~20 cm提升至3 cm以内，流量偏差控制在1.6%以内。这里最重要的不是某个单项指标改善，而是两个工程事实同时成立：一方面，误差不再跨环节积累；另一方面，扰动可在预测窗口内被前瞻性对冲。

基于现有证据，可将胶东调水评定为WNAL L2+，并可分维度理解其水平：感知能力已接近L3，局部达到L4；执行能力和决策能力稳定处于L2+；安全保障仍主要停留在L2，因为标准化SIL、HIL和跨域级联标定尚不完整。这说明“木桶短板”依然存在，系统综合等级不由最强模块决定，而由最弱能力域决定。图6给出了其WNAL多维评级表达。

![图6 胶东调水工程WNAL多维评级](figures/fig6_jiaodong_wnal_radar.png)

极端工况讨论更能说明问题。若出现大面积断电、广域通信中断、上游突发来水叠加冰期阻水，系统即使拥有较强的常态控制能力，也会迅速逼近ODD边界。此时若没有四态机驱动的降级逻辑、预烧录的Managed终态和经xIL验证的跨域阻断策略，所谓“智能运行”会立刻退化为人工抢险。因此，胶东调水案例的真正启示不是“闭环已经完全成熟”，而是：CPSS框架能够准确定位其成熟部分与短板部分，闭环四预已经证明工程有效，而L3跃迁仍取决于验证、授权和极端工况治理能力的补齐。

## 8 结论与展望

本文得到3点主要结论。第一，CPSS能够把Physical、Cyber、Social三空间及其反馈回路压缩为国家水网统一的工程语言，因此它不是智能水网的辅助解释，而是国家水网智能运行的统一框架。第二，规划、设计、建设、运行四阶段并非彼此分离的专业环节，而是以可控可观性、WNAL、ODD、HDC、xIL和四态机为主线的连续技术链条，闭环四预是该链条在运行阶段的集中体现。第三，胶东调水2024年3月实测说明，闭环四预相较传统开环四预具有明确工程优势，能够显著压缩时滞、抑制误差累积、提升调控精度与运行稳定性。

未来可从两个方向继续推进。其一，突破在线可控可观性评估、网络级降阶建模和跨域级联标定，使ODD动态管理和L3自主运行具备坚实技术基础。其二，正视行业阻力，尤其是管理授权、责任划分、标准审查和调度信任问题；国家水网从L2走向L3，最大的障碍未必是算法，而可能是验证规范不足与组织接受度滞后。只有把技术成熟与治理成熟同步推进，CPSS框架和闭环四预的工程价值才能在国家水网中规模化释放。

## 参考文献

[1] 中共中央, 国务院. 国家水网建设规划纲要[R]. 北京, 2023.

[2] 李国英. 加快构建国家水网 全面提升水安全保障能力[J]. 水利学报, 2022, 53(8): 895-903.

[3] 邓铭江, 王忠静, 黄介生, 等. 跨流域调水工程优化调度研究进展与展望[J]. 水利学报, 2019, 50(12): 1437-1450.

[4] 王浩, 雷晓辉, 蒋云钟. 水利智能化技术发展方向与关键问题[J]. 水利学报, 2022, 53(10): 1153-1164.

[5] 程晓陶, 李帅杰, 刘志雨, 等. 新时期流域防洪“四预”体系建设的关键技术问题[J]. 水利学报, 2023, 54(8): 887-897.

[6] Liu B, Recalde-Camacho L, Thomas I M, et al. Observability and controllability analysis of water distribution systems[J]. Journal of Water Resources Planning and Management, 2022, 148(2): 04021095.

[7] Wang F Y. Parallel control and management for intelligent transportation systems: concepts, architectures, and applications[J]. IEEE Transactions on Intelligent Transportation Systems, 2010, 11(3): 630-638.

[8] 雷晓辉, 蒋云钟, 王浩. 水系统控制论: 背景、技术框架与研究范式[J]. 南水北调与水利科技(中英文), 2025, 23(1): 1-15.

[9] 雷晓辉, 蒋云钟, 王浩. 水资源系统分析学科展望: 从静态平衡到动态控制[J]. 南水北调与水利科技(中英文), 2025, 23(2): 201-218.

[10] 雷晓辉, 蒋云钟, 王浩. 基于无人驾驶理念的下一代自主运行智慧水网架构与关键技术[J]. 南水北调与水利科技(中英文), 2025, 23(3): 401-420.

[11] 雷晓辉, 蒋云钟, 王浩. 自主运行智能水网的在环测试体系[J]. 南水北调与水利科技(中英文), 2025, 23(4): 601-618.

[12] Kalman R E. Mathematical description of linear dynamical systems[J]. Journal of the Society for Industrial and Applied Mathematics, Series A: Control, 1963, 1(2): 152-192.

[13] Chen C T. Linear System Theory and Design[M]. 3rd ed. New York: Oxford University Press, 1999.

[14] SAE International. J3016: Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles[S]. Warrendale: SAE, 2021.

[15] Negenborn R R, van Overloop P J, Keviczky T, et al. Distributed model predictive control of irrigation canals[J]. Networks and Heterogeneous Media, 2009, 4(2): 359-380.

[16] Boyd S, Parikh N, Chu E, et al. Distributed optimization and statistical learning via the alternating direction method of multipliers[J]. Foundations and Trends in Machine Learning, 2011, 3(1): 1-122.

[17] Tao F, Zhang H, Liu A, et al. Digital twin in industry: state-of-the-art[J]. IEEE Transactions on Industrial Informatics, 2019, 15(4): 2405-2415.

[18] Schuurmans J, Clemmens A J, Dijkstra S, et al. Modeling of irrigation and drainage canals for controller design[J]. Journal of Irrigation and Drainage Engineering, 1999, 125(6): 338-344.

[19] Clemmens A J, Schuurmans J. Simple optimal downstream feedback canal controllers: theory[J]. Journal of Irrigation and Drainage Engineering, 2004, 130(1): 26-34.

[20] Moore B C. Principal component analysis in linear systems: controllability, observability, and model reduction[J]. IEEE Transactions on Automatic Control, 1981, 26(1): 17-32.

[21] Kong L, Lei X, Wang H, et al. A model predictive control based distributed coordination for multi-reach canal systems[J]. Journal of Hydrology, 2019, 577: 123937.

[22] 王浩, 王建华, 秦大庸, 等. 基于二元水循环模式的水资源评价理论方法[J]. 水利学报, 2006, 37(12): 1496-1502.

[23] Wiener N. Cybernetics: Or Control and Communication in the Animal and the Machine[M]. Cambridge: MIT Press, 1948.
