# 三引擎评审合并报告: ch01
生成时间: 2026-03-06 15:03
---

## Reviewer B (Gemini — 工程实践型)
## 八维度评分
1. **工程真实性 (Engineering Authenticity)**: 9/10（高位水塔注水、非线性泄流及系统状态截断等场景非常契合水务工程底层实战）
2. **代码可复现性 (Code Reproducibility)**: 6/10（代码逻辑过关，但文中所声明的源码文件在项目目录中实际处于丢失状态）
3. **数值准确性 (Numerical Accuracy)**: 10/10（ODE 积分逻辑正确，稳态极限值计算 $0.566m$ 完全符合 $Q_{in}=Q_{out}$ 的物理定律方程推导）
4. **工业指导价值 (Industrial Guidance Value)**: 9/10（明确指出了纯滞后引发水锤、传感器高频噪声需滤波、求解器溢出等工业现场级痛点）
5. **难度梯度与教学性 (Difficulty Gradient & Teachability)**: 8/10（从物理质量守恒到泰勒展开，再到计算机数值仿真，知识链条递进合理）
6. **习题与配套资源 (Exercises & Supporting Resources)**: 2/10（作为教材，本章完全没有提供课后习题和思考题）
7. **学术文风严谨度 (Academic Writing Rigor)**: 3/10（大量使用 Emoji 和网络化口语，违背学术出版标准）
8. **图表与公式规范性 (Chart & Formula Standardization)**: 7/10（公式标准，但图表缺乏全局统一的学术编号）

## 工程问题清单（Critical/Major/Minor）

- **Critical (致命问题)**
  - **学术参考文献完全缺失**：全章未列出任何参考文献。控制论基础（PID、拉普拉斯变换）、数值积分方法及托里拆利定律等，均需引用权威教材（如 Ogata《现代控制工程》）以支撑理论依据。
  - **教学闭环缺失（无习题）**：作为教材，本章末尾缺少供学生进行理论推导或上机仿真的课后习题。

- **Major (严重问题)**
  - **文风轻浮（非学术化）**：正文充斥大量 Emoji（🌟、🎯、💡、💻、📊、🚀），并使用了“防崩溃护栏”、“白话解释”等博客式的网络口语。学术教材须保持客观严谨，必须剔除所有表情符号并将相关标题规范化（例如改为“1.4.1 案例背景”）。
  - **内部源文件引用失效（幽灵文件）**：代码块下方标注 `Source: assets/ch01/ch01_tank_sim.py`，但查阅当前工作区目录树发现，`assets/ch01/` 目录下仅有图片文件，该 Python 脚本缺失。

- **Minor (次要问题)**
  - **缺乏图表编号与交叉引用**：文中的图（如物理概化图、波形图）和表格均缺少“图 1-1”、“表 1-1”这样的学术编号及详尽图题。正文中也未使用编号进行标准指引。
  - **数学符号与变量命名未统一**：正文推导中进水流量使用小写 $q_{in}$，而在 Mermaid 图与代码段中混用了 $Q_{in}$ 和 `Q_in`。为了防止初学者概念混淆，建议将宏观绝对流量统一为大写 $Q$，小写 $q$ 仅用于表示线性化后的偏差量。

## 参考文献审查（缺失/格式错误/疑似虚构）
- **外部文献缺失**：无任何外部参考文献，不符合学术教材规范。
- **内部引用虚构/失效**：引用的 `assets/ch01/ch01_tank_sim.py` 疑似虚构或未提交代码库。

## 综合评分: 6.8/10

**CTO 评审总结**：
技术底子扎实。对系统纯滞后、工业传感器去噪以及防积分器溢出宕机的工程论述切中要害，体现了真实的工业现场经验。但是，这作为一本**学术教材**在规范性上是不及格的。请立刻剔除所有的“网红博客文风”（清理 Emoji 和口语词汇），补齐缺失的代码文件、图表编号、课后习题以及学术参考目录。技术的硬核不能作为排版和行文随意的借口。

## Reviewer C (Codex — 代码验证型)
综合评分：6.8/10

1. 位置：[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):45、[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):46、[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):48  
问题类型：公式错误 / 量纲错误  
严重程度：Critical  
修正建议：这里把状态方程里的输入系数 `1/A` 误写成了“系统增益”。由
\[
\frac{d\tilde h}{dt}=-\frac{k}{2A\sqrt{h_0}}\tilde h+\frac{1}{A}\tilde q_{in}
\]
拉氏变换可得
\[
G(s)=\frac{\tilde H(s)}{\tilde Q_{in}(s)}=\frac{1/A}{s+k/(2A\sqrt{h_0})}
=\frac{2\sqrt{h_0}/k}{(2A\sqrt{h_0}/k)s+1}.
\]
如果坚持写成标准形式 `K/(τs+1)`，则应为 `K = 2√h0 / k`，不是 `1/A`。`1/A` 的量纲是 `m^-2`，而传递函数静态增益量纲应为 `s/m^2`。

2. 位置：[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):94、[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):131  
问题类型：公式错误 / 物理建模不一致  
严重程度：Major  
修正建议：正文写的是“水泵恒定功率注水”，但代码实际施加的是恒定流量 `Q_in_step = 0.1 m^3/s`。恒功率泵与恒流量泵不是同一模型，扬程变化时流量一般不会保持常数。应二选一：
- 把文字改为“恒定流量注水”；
- 或补充泵特性/功率关系，改写 `Q_in(h)` 模型。

3. 位置：[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):107、[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):136  
问题类型：代码 bug / 可复现性问题  
严重程度：Major  
修正建议：文中声称“亲自运行了底层 Python 求解器，并呈现表格与双轴图”，但给出的代码只算出了 `h_sim`，并没有：
- 计算整段 `Q_out(t)`；
- 生成表格；
- 绘图或保存 `tank_simulation.png`。  
另外，引用的源码 `assets/ch01/ch01_tank_sim.py` 在当前仓库中不存在。应补齐完整脚本，或修正为实际存在的源文件路径。

4. 位置：[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):140  
问题类型：数值错误 / 表格精度表述  
严重程度：Minor  
修正建议：表中时间写成 `20.0, 40.0, 60.1, 100.2`，但 `np.linspace(0, 200, 500)` 的实际采样点是 `20.0401, 40.0802, 60.1202, 100.2004` 等，只有 `0` 和 `200` 是精确节点。当前水深/流量数值与“最近采样点”是匹配的，但时间列不是严格对应的仿真节点。应改成“约 20.04 s”等，或用插值后再列精确时刻。

已核对通过的项：
- [ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):29、[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):32、[ch01.md](D:/cowork/教材/chs-books-v2/books/water-system-control/ch01.md):33 的质量守恒方程、托里拆利出流形式、`g = 9.81 m/s^2` 都正确。
- 我复算了代码对应数值，表中水深和排流率与模型一致，保留 3 位小数后可得到 `0.378/0.081`、`0.492/0.093`、`0.536/0.097`、`0.561/0.099`、`0.566/0.100`。
- 稳态水位解析值为 \(h_{ss}=(Q_{in}/(C_d a\sqrt{2g}))^2 \approx 0.5663\ \text{m}\)，与文中最终数值一致。

结论：核心非线性水箱模型本身是对的，数据表也基本正确；主要问题集中在线性化后的“系统增益/传递函数”写错，以及案例文字与代码假设、代码与可复现实物之间不一致。

## Reviewer A (Claude — 理论严谨型)
*等待Claude Code会话中执行*

---
## 综合处理建议
请在Claude Code中执行以下操作：
1. 阅读三引擎评审意见
2. Claude补充理论评审（如尚未执行）
3. 合并Critical+Major问题，生成修改清单
4. 调用 `python tri_engine.py revise` 执行修改
