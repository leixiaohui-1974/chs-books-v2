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