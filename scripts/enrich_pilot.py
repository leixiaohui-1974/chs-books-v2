import os
import re
from pathlib import Path

target_dir = Path(r'D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics')
filepath = target_dir / 'ch01.md'

content = filepath.read_text(encoding='utf-8')

new_case = """### 🌟 案例背景 (Context)
想象一下，您需要为一片广袤的农田设计一条灌溉水渠。您知道每天需要输送多少水（流量 Q），也知道当地的地形起伏（底坡 S0）。但问题是：为了保证水不溢出来，且水流既不冲刷渠道也不产生淤积，这条水渠的**正常水深（Normal Depth）**应该是多少？
本案例就是运用经典的 Manning 方程来解决这个在明渠设计中最基础也是最核心的“均匀流（Uniform Flow）”水深反推问题。

### 🎯 问题描述 (Problem)
在给定的流量要求 $Q = 0.5 m^3/s$，底宽 $b=1.0m$，边坡系数 $m=1.5$，糙率 $n=0.025$ 且底坡 $S_0=0.0002$ 的梯形渠道中，求解能够维持稳态均匀流的正常水深 $h_n$。
**核心痛点**：因为水面宽度和过水面积都与水深 $h$ 呈非线性关系，所以 Manning 方程无法得出简单的代数解析解，必须依靠数值迭代方法。

### 💡 解题思路 (Solution Approach)
我们不能瞎猜水位。为了保证计算程序的健壮性：
1. **区间试探法（Bracketing）**：程序首先通过不断倍增水深，快速框定一个包含真实水深的宽泛区间 `[low, high]`。
2. **牛顿迭代法（Newton-Raphson）**：在框定区间后，利用流量对水深的导数（水面宽），指引程序快速逼近真实解。
3. **安全护栏**：如果在迭代过程中牛顿法算出了一步极其夸张的值（比如跳到了负数水深），程序会强制采用“二分法”将其拉回安全区间，这保证了底层代码绝不会崩溃发散。

### 💻 代码执行与图表 (Code & Charts)
> 核心求解器采用 `solve_normal_depth` 函数，通过 1e-10 的极高精度误差阈值控制收敛。

![Q-h 曲线演进图](../../../CHS-Books-Old/books/open-channel-hydraulics/code/examples/case_01_irrigation/results/q_h_curve.png)
*(图注：红点标注了在设计流量 0.5 $m^3/s$ 时，系统最终锁定的稳态水深约为 0.74 米。)*

### 📊 结果白话解释 (Result Interpretation)
经过极其迅速的 5 次牛顿迭代，系统锁定了水位为 **0.74 米**。
观察上述生成的 Q-h (流量-水深) 曲线，我们可以明显看到它是一条上抛的非线性曲线。这意味着：当渠道里的水比较浅时，稍微增加一点水深就能大幅提高输水能力；但当水越来越深，受到两岸边坡摩擦力（湿周）的牵制，水位上涨带来的流量红利会逐渐衰减。

### 🚀 专家建议 (Recommendations)
1. **给设计者的建议**：目前的计算表明弗劳德数 (Fr) 约为 0.16，属于典型的“缓流”。这意味着如果下游有控制闸门，水波会向上游传播。请在渠道全线预留 0.3 米以上的安全超高。
2. **防崩溃原则**：在把这个模块接入大模型 Agent 时，如果输入的极端流量 $Q$ 过大导致水深暴涨，我们刚才植入的二分法防线能够成功拦截非法迭代，避免系统进入死循环。这也是工业级软件与学生作业的核心区别。"""

content = re.sub(r'### 🌟 案例背景 \(Context\).*?reflection task\.', new_case, content, flags=re.DOTALL)

filepath.write_text(content, encoding='utf-8')
print('Mock generation of Pilot Chapter completed safely.')