# CCG 三引擎评审合成报告 — CHS全系列CPSS统一框架修改

- Date: 2026-03-31
- Engines: Claude Opus (18 files, 64 tool calls) | Gemini 2.5-pro (9 files) | Codex default (6 files, 76k tokens)
- Scope: 34 requirements across 6 volumes

## Agreed Recommendations (all engines concur)

1. **术语跨卷治理是当前最大风险** — 三引擎一致认为术语不一致是主要问题，不是单段逻辑
2. **新增内容思想主线正确** — CPSS三空间、智能体统一、闭环/开环区分的核心框架在各卷贯彻良好
3. **高亮段落质量优秀** — ch09智能体约束表、ch13投影函数、ch06跨域级联、AI↔XIL映射获三引擎一致肯定

## Conflicting Recommendations

| 维度 | Claude | Gemini | Codex | 裁决 |
|------|--------|--------|-------|------|
| 术语表质量 | "14分节完整" | "严重滞后" | "D/DT重复、缺知识图谱" | **Gemini+Codex更准确**：结构好但内容有缺 |
| 投影函数公式 | 未提 | P2"增加比喻" | P1"数学不够干净" | **Codex更深入**：应修正公式+补观测算子 |
| 四态机命名 | P2"英文名统一" | 未提 | P0"四套名称混用" | **Codex严重度更合理**：升级为P0 |

## Chosen Final Direction

### 已修复（本轮闭环 7/7）
- P0: ODD维度五维→六维
- P0: ch14表编号重复
- P1: HDC/WNAL命名歧义注释
- P1: T3 ch14回溯引用
- P1: RL时间尺度偏差
- P1: T5 ch05 LaTeX (33处\eft + 15个断行公式)
- P1: T5 ch06 公式符号 (22处乱码 + 23处\\frac)

### 需作者决策后修复
- **xIL第四级**: OIL(Operator-in-Loop) vs PIL(Plant-in-Loop) — 需确定全系列标准
- **四态机末态**: Managed vs Override vs Manual vs 接管 — 需确定唯一标准名

### 下一轮技术修复（不需作者决策）
- 投影函数公式加入观测算子y(t)
- LQR/Kalman改用stabilizable/detectable表述
- ch14闭环对比注明基线来源"历史开环基线"
- 多域行为矩阵补通信/算力域
- 术语表D/DT关系厘清
- 术语表补充：活孪生/冻结孪生、知识图谱、P→C投影函数、多域行为矩阵

## Action Checklist

- [x] P0-1: ODD维度统一 (CHS_术语规范_全系列.md)
- [x] P0-2: ch14表编号 (T2a/ch14_final.md)
- [x] P1-1: LaTeX修复 (T5/ch05_final.md, T5/ch06_final.md)
- [x] P1-2: HDC命名注释 (T2a/ch12_final.md)
- [x] P1-3: T3回溯引用 (T3/ch14.md)
- [x] P1-5: RL时间尺度 (T5/ch05_final.md)
- [ ] P0-new: xIL OIL/PIL统一 (需作者决策)
- [ ] P0-new: 四态机末态统一 (需作者决策)
- [ ] P1: 投影函数公式精化 (T2a/ch13_final.md)
- [ ] P1: LQR/Kalman表述修正 (T2a/ch09_final.md)
- [ ] P1: 闭环对比基线标注 (T2a/ch14_final.md)
- [ ] P1: 多域矩阵补通信域 (T3/ch06.md)
- [ ] P1: 术语表D/DT合并 (CHS_术语规范_全系列.md)
- [ ] P1: 术语表补充新概念 (CHS_术语规范_全系列.md)
