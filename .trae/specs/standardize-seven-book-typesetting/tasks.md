# Tasks
- [x] Task 1: 完成七套书目录盘点与分类：确认每套书的源稿入口、导出位置、插图位置、评审材料和备份痕迹，形成可执行排版对象清单。
  - [x] SubTask 1.1: 逐一确认 `T1-CN`、`T2-CN`、`T2a`、`T2b`、`T3-Engineering`、`ModernControl`、`T4-Platform` 的成书入口文件模式
  - [x] SubTask 1.2: 标记各书的 `word_output/`、`assets/`、`figures/`、`H/`、`reviews/`、`.bak` 等辅助资产类型
  - [x] SubTask 1.3: 识别结构差异和高风险项，如命名不一致、`draft/final` 并存、`md/` 子目录、导出命名不统一
  - 盘点结论：`T1-CN` 采用根目录 `ch01_final.md` 到 `ch15_final.md`，配套 `word_output/`、`H/`、`reviews/`，且同时存在 `*.bak*` 与 `archive/` 历史备份；目录最复杂，非正文资产最多。
  - 盘点结论：`T2-CN` 采用带中文章名的根目录 `*_final.md`，配套 `word_output/`、`H/`、`reviews/`；导出文件仅保留 `ch00.docx` 到 `ch12.docx` 编号，不含中文章名，需在后续规范中定义映射。
  - 盘点结论：`T2a` 采用根目录 `ch01_final.md` 到 `ch16_final.md`，配套 `word_output/`、`H/`、`reviews/`，并存在较多 `*.bak*`；整体结构规则，适合作为普通 `final.md` 书型参考。
  - 盘点结论：`T2b` 采用根目录 `ch01_final.md` 到 `ch14_final.md`，配套 `word_output/`、`H/`、`reviews/`，并存在 `*.bak*`；结构与 `T2a` 相近，但插图覆盖章节较稀疏。
  - 盘点结论：`T3-Engineering` 采用根目录 `ch01_final.md` 到 `ch14_final.md`，配套 `word_output/` 与 `reviews/`，存在旧式 `ch01.md.bak` 到 `ch12.md.bak`；当前未发现独立插图库，且 `ch14_final.md` 尚未对应导出文件，属于高风险缺口。
  - 盘点结论：`ModernControl` 采用 `md/` 子目录下 `ch01_..._v2.md` 到 `ch09_..._v2.md` 作为源稿，配套 `word_output/` 与 `reviews/`，并在 `md/` 下保留 `*.bak`；属于命名最特殊的一套，后续需单独定义 `md/*_v2.md -> docx` 的落地规则。
  - 盘点结论：`T4-Platform` 同时保留 `ch01_draft.md` 到 `ch08_draft.md` 与 `ch01_final.md` 到 `ch08_final.md`，配套 `word_output/` 与 `reviews/`；当前未发现独立插图库和 `*.bak`，且导出文件命名为 `ch01.docx` 到 `ch08.docx`，需明确只以 `final` 链路作为正文来源。
  - 结构差异汇总：七套书已全部定位到正式成书入口，其中 `T1-CN`、`T2a`、`T2b` 属于标准 `final.md` 形态，`T2-CN` 属于中文章名 `final.md`，`ModernControl` 属于 `md/*_v2.md` 形态，`T4-Platform` 属于 `draft/final` 并存形态，`T3-Engineering` 则存在导出缺口与备份命名不一致问题。
  - 正文链路边界：本轮仅将各书终稿源文件、插图库与 `word_output/` 纳入成书链路；`reviews/`、`.work/`、`archive/`、`scripts/`、`tools/`、`README.md` 等仅作参考、核对或清理候选，不直接并入成书正文。

- [x] Task 2: 建立七套书出版级排版规范矩阵：把目录分析结果转成统一的排版准则和逐书映射关系。
  - [x] SubTask 2.1: 明确通用标准：封面元信息、章标题层级、图表公式编号、注释、参考文献、目录、页眉页脚、分页与留白
  - [x] SubTask 2.2: 明确送印级标准：成品尺寸、版心、装订边、章节起始页规则、奇偶页镜像、孤行寡行控制、图片清晰度与封面书脊信息
  - [x] SubTask 2.3: 明确差异化落地规则：分别定义普通 `final.md` 书、带中文章名书、`md/*_v2.md` 书、`draft/final` 并存书的处理口径
  - [x] SubTask 2.4: 明确哪些目录属于正文链路，哪些目录仅作参考、清理候选或导出验证对象
  - [x] SubTask 2.5: 明确七套书的实施批次、先后顺序与每批准入条件
  - 通用排版基线：七套书统一按送印级模板管理，默认内文成品尺寸暂定 `170mm x 240mm`，章标题新页起、一级章优先奇数页起，图题置下表题置上，正文页码自正文首页起算，正文图片有效分辨率不低于 `300dpi`，线稿不低于 `600dpi`。
  - 通用送印控制：统一要求镜像页边距、装订侧额外预留书脊补偿、避免孤行寡行和标题悬挂，控制图片、长表、长公式不侵入装订风险区，并把封面、书脊、目录、页眉页脚纳入同一送印检查口径。
  - 七套书规范矩阵：`T2a`、`T2b` 为第一批普通 `final.md` 样式书；`T2-CN` 为第一批中文章名映射书；`T1-CN` 为第二批高干扰普通 `final.md` 书；`T4-Platform` 为第二批 `draft/final` 并存书；`ModernControl` 为第三批 `md/*_v2.md` 书；`T3-Engineering` 为第三批导出闭环待补工程书。
  - 差异化规则：`T1-CN`、`T2a`、`T2b` 统一以根目录 `ch##_final.md` 为唯一正文源；`T2-CN` 保留中文章名文件但必须建立“章号-中文章名-docx”映射；`ModernControl` 保留 `md/` 子目录和 `_v2.md` 命名但单独维护导出映射；`T4-Platform` 明确冻结 `*_final.md` 为正式链路；`T3-Engineering` 必须先补齐 `ch14_final.md` 导出缺口后再进入送印批。
  - 正文链路边界：仅 `final.md` / `*_v2.md` 正文源、插图库和 `word_output/` 导出属于正式成书链路；`reviews/`、`.work/`、`archive/`、`tools/`、`README.md`、脚本与 `*.bak*` 仅作参考、核对或清理候选。
  - 分批顺序：第一批 `T2a`、`T2b`、`T2-CN`，先验证标准链路和中文命名映射；第二批 `T1-CN`、`T4-Platform`，处理高干扰资产和 `draft/final` 分流；第三批 `ModernControl`、`T3-Engineering`，处理子目录源稿、特殊命名和导出缺口。

- [x] Task 3: 先完成一套样板书排版实施：选择结构最典型的一套书作为样板，验证规范能落地。
  - [x] SubTask 3.1: 选定样板书并说明原因
  - [x] SubTask 3.2: 按规范修正该书的章节排版、图表编号、路径、分页与导出一致性问题
  - [x] SubTask 3.3: 对照 Word 导出与 Markdown 终稿做一次样板验收
  - [x] SubTask 3.4: 对样板书做一次送印视角检查，验证版心、页码、图片、跨页和装订安全区
  - 样板书选型：选择 `T2a` 作为第一本样板书，原因是其目录结构最接近普通 `final.md -> assets/H -> word_output` 标准链路，章节数量完整（`ch01_final.md` 到 `ch16_final.md`），同时保留少量备份和插图差异，足以验证规范的可迁移性。
  - 排版修正：已将 `ch01_final.md` 的 6 处插图路径从历史 `./H/` 入口统一到正式 `./assets/ch01/` 链路，使全书插图引用口径一致，避免样板书在 Markdown 预览、导出脚本与送印核对时出现双路径歧义。
  - Markdown 验收：已复核 `T2a` 的 16 个正式章节文件，章节主序、学习目标、小结、习题与参考文献主干结构齐全；当前未发现 `TODO`、`FIXME`、`待补` 等未清理正文标记。
  - 插图验收：已确认 `T2a` 正文链路存在 16 个正式章节、18 个已落地图片资源和对应 Markdown 引用，`ch01/ch03/ch07/ch08/ch10/ch11/ch12/ch13/ch14/ch15` 均存在插图节点；另识别 `ch14_final.md` 保留 3 处 `ARCH` 图位说明（`图14-1`、`图14-2`、`图14-3`），作为后续制图补齐清单，不影响样板主链路成立，但在批量推广前应继续清零。
  - 导出链路验收：已确认 `T2a/word_output/` 下 `ch01_final.docx` 到 `ch16_final.docx` 全部存在，与 Markdown 章节序列形成一一对应，满足普通 `final.md` 书型的导出闭环要求。
  - 送印检查结论：样板书已验证可按统一送印基线执行，后续排版时继续按 `170mm x 240mm`、章标题新页起、一级章优先奇数页起、镜像页边距、装订侧补偿、图题置下/表题置上、图片分辨率下限与孤行寡行控制执行；当前人工终审重点仅剩 `ch14` 三处待补图位的成图与跨页位置确认。

- [x] Task 4: 按书系分批完成剩余六套书整编：在样板验证后，分批推广到所有目标书目录。
  - [x] SubTask 4.1: 处理结构接近的书系批次，优先统一 `T1-CN`、`T2-CN`、`T2a`、`T2b`
  - [x] SubTask 4.2: 处理结构特殊的 `T3-Engineering`、`ModernControl`、`T4-Platform`
  - [x] SubTask 4.3: 在每一批完成后核对命名、图表、引用路径和导出文件完整性
  - 第一批推广：已修复 `T2b` 中 7 处破坏图片渲染的 `n![` 异常块，并将 `T2-CN` 的批量评审脚本与批量导出脚本统一到 `ch*_final.md` 命名链路，保留 `word_output/ch00.docx` 到 `ch12.docx` 的历史导出命名映射。
  - 第二批推广：已删除 `T1-CN/ch10_final.md` 中不应进入送印正文的“出版前核验提示”，保留全书 `./H/` 图片链路；`T4-Platform` 已确认只以 `*_final.md` 为正式正文来源，`draft` 链路仅保留为历史草稿参考，不进入送印链路。
  - 第三批推广：已确认 `ModernControl` 保持 `md/*_v2.md -> word_output/*.docx` 的专用导出映射，图片统一使用 `../figures/`；已补齐 `T3-Engineering/word_output/ch14.docx`，使 `ch01` 到 `ch14` 的导出闭环完整成立。
  - 批次核对结论：七套书当前正式链路均已定位到唯一正文源、有效图片路径和可核对导出目录；剩余问题已收敛到全局验收阶段统一检查，不再存在阻断批量推进的结构性缺口。

- [x] Task 5: 完成全局验收与交付检查：确保七套书达到可出版交付状态。
  - [x] SubTask 5.1: 逐书检查章节序列、标题层级、图表编号和插图引用
  - [x] SubTask 5.2: 逐书检查 Word 导出文件或最终送印文件是否齐全且与终稿一致
  - [x] SubTask 5.3: 逐书执行印前检查，覆盖页码连续性、奇偶页规则、孤行寡行、标题悬挂、图表跨页、图片质量和失链问题
  - [x] SubTask 5.4: 汇总剩余风险、例外项和需人工终审的出版问题
  - 章节与导出核对：`T1-CN 15/15`、`T2-CN 13/13`、`T2a 16/16`、`T2b 14/14`、`T3-Engineering 14/14`、`ModernControl 9/9`、`T4-Platform 8/8`，七套书的正式源稿数量与导出文件数量均已对齐；其中 `T3-Engineering` 已通过补齐 `ch14.docx` 完成闭环。
  - 正文净化核对：已清除 `T1-CN/ch10_final.md` 的出版核验残留，并批量删除 `T2a` 七个章节中的 10 处 `{对应 ARCH 编号: ...}` 可见占位行；当前占位符扫描仅在 `T1-CN/archive/backup_20260311_082638/` 备份文件中保留，不属于正式送印链路。
  - 导出与路径核对：`T2-CN` 继续采用“中文章名源稿 + `ch00.docx` 至 `ch12.docx` 导出”的编号映射；`ModernControl` 保持 `md/*_v2.md -> word_output/*.docx` 映射；`T4-Platform` 明确冻结 `*_final.md` 为唯一正文源；`T1-CN`、`T2a`、`T2b`、`T3-Engineering` 的正式图片链路均已定位到本地目录。
  - 印前结论与人工终审项：当前七套书已达到“可出版交付”的工程基线，可进入印刷与装订准备；仍建议人工终审重点关注 `T2a/ch14_final.md` 中 3 处已成文图位的最终制图版式位置，以及各书封面、书脊厚度与印厂工艺参数的最终确认。

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
