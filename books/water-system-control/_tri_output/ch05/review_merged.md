# 三引擎评审合并报告: ch05
生成时间: 2026-03-06 15:12
---

## Reviewer B (Gemini — 工程实践型)
## 八维度评分（每项1-10）
1. **工程真实性: 9/10**（雷达液位计受水波纹及飞鸟干扰、PID微分项对噪声的敏感放大，这些都是极其真实的工业现场痛点。使用EKF及残差剔除作为软测量手段，是标准的工业级解决方案）
2. **理论准确性: 8/10**（EKF的雅可比矩阵推导正确，Predict和Update两步逻辑清晰；但在单变量（1D）系统中，误差协方差 $P$ 严谨来说应称为“方差”）
3. **代码可运行性: 7/10**（Python代码逻辑无误且能成功过滤飞鸟干扰。但**未固定随机种子**，导致读者运行的噪声序列每次不同，无法复现教材表格中的精确数值）
4. **图表专业性: 7/10**（仿真图能直观反映滤波效果，圈出被拒绝的脉冲点极具教学意义。但“Nano-Banana-Pro”生成的场景图可能不符合学术教材的严谨工程制图规范）
5. **表述规范性: 3/10**（严重失格。大量使用“疯狂抽搐”、“斩杀脉冲”、“惊险时刻”、“没事人一样”、“降维打击”等极其口语化和网络化的词汇，并滥用Emoji，完全脱离了学术教材的严肃性）
6. **教学启发性: 9/10**（以“飞鸟导致2米跳变”这种极端且形象的案例，完美解释了为什么“要依靠物理底座盲飞”，比纯数学推导有效得多）
7. **完整度: 4/10**（没有参考文献，没有课后习题，结构虎头蛇尾）
8. **前沿性: 8/10**（延伸到污水处理厂总磷总氮的虚拟传感器（Virtual Sensor）软测量，非常贴近现代工业CTO的关注点）

## 工程问题清单
### Critical (致命问题)
1. **文风极度不规范（需全面重写）**：必须删去所有段落标题的Emoji（🌟、🎯等）。将网络梗和口语替换为工程术语，例如：
   - “疯狂抽搐” -> “执行机构高频震荡 / 加剧阀门磨损”
   - “斩杀脉冲” -> “有效抑制脉冲干扰 / 异常值剔除”
   - “降维打击” -> “具备显著的技术优势”
2. **代码缺乏可复现性**：`assets/ch05/ch05_kalman_filter.py` 中生成 `w_proc` 和 `v_meas` 时使用了 `np.random.normal`，但未在脚本开头设置 `np.random.seed(42)`。如果不加种子，读者自己跑出来的表格数据永远对不上教材里的数据。

### Major (主要问题)
1. **数学符号上下文不一致**：问题描述中微分方程使用的是液位 $h$ （$dh/dt$），但在后文解题思路和代码中突然变成了状态变量 $x$（$x_{pred}$, $x_{est}$）。应在建立状态空间时明确说明“令状态变量 $x = h$”。
2. **异常值判定逻辑过于硬编码（Hardcoded）**：代码中使用 `if abs(y) > 0.5:` 作为剔除标准，这在工业上不够鲁棒。教材作为范例，应引入**基于新息协方差的卡方检验（Chi-Square Test）**：即计算残差协方差 $S = H P_{pred} H^T + R$，当 $y^2/S > \gamma$ 时判定为异常，这才是正统的软测量逻辑。

### Minor (次要问题)
1. **排版格式**：非线性的雅可比矩阵偏导公式 $F = 1 - \frac{C \Delta t}{2 A \sqrt{x}}$ 建议做成居中的块级（Block）公式，挤在行内不仅难看，也不利于学生抄写和推导。
2. **缺少习题**：建议增加一道工程计算题，例如让学生推导不同采样周期 $\Delta t$ 或不同测量噪声协方差 $R$ 对卡尔曼增益 $K$ 收敛值的影响。

## 参考文献审查
- **严重缺失**：本章末尾**完全没有列出任何参考文献**。对于状态估计和软测量的章节，这是不可接受的。
- **修改建议**：必须补充：
  1. 卡尔曼的奠基性论文：Kalman, R. E. (1960). *A New Approach to Linear Filtering and Prediction Problems*. Journal of Basic Engineering.
  2. 工业软测量的经典著作或教材，例如 Dan Simon 的 *Optimal State Estimation*。

## 综合评分: 6.8/10
**CTO 寄语**：
这个章节的工程切入点非常漂亮，把晦涩的协方差更新讲成了“我不信传感器只信混合体”，非常接地气，工业应用（虚拟传感器）的拓展也很有前瞻性。但是，**教材不是微信公众号推文**。你的文字太跳脱了，代码的严谨性（随机种子、卡方检验）也有所欠缺。请立刻收起那些花哨的Emoji和网络流行语，用工程师该有的严谨把文字和公式重新梳理一遍。把文献补齐，把代码里的随机数种子钉死。

## Reviewer C (Codex — 代码验证型)
*执行失败: OpenAI Codex v0.107.0 (research preview)
--------
workdir: D:\cowork\教材\chs-books-v2\books\water-system-control
model: gpt-5.4
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: high
reasoning summaries: none
session id: 019cc1fb-bc85-7353-8214-7483601a961f
--------
user
请阅读文件 C:\Users\lxh\AppData\Local\Temp\tri_tlptyv4w.md 的全部内容，按其中的要求完成任务，输出完整结果。
mcp: figma starting
mcp: notion starting
2026-03-06T07:10:29.783174Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer realm=\"OAuth\", error=\"invalid_token\", error_description=\"Missing or invalid access token\"" })
mcp: notion failed: The notion MCP server is not logged in. Run `codex mcp login notion`.
2026-03-06T07:10:30.348609Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer resource_metadata=\"https://mcp.figma.com/.well-known/oauth-protected-resource\",scope=\"mcp:connect\",authorization_uri=\"https://api.figma.com/.well-known/oauth-authorization-server\"" })
mcp: figma failed: The figma MCP server is not logged in. Run `codex mcp login figma`.
mcp startup: failed: notion, figma
2026-03-06T07:10:31.204253Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}", url: wss://chatgpt.com/backend-api/codex/responses
2026-03-06T07:10:31.949607Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}", url: wss://chatgpt.com/backend-api/codex/responses
2026-03-06T07:10:33.417674Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}", url: wss://chatgpt.com/backend-api/codex/responses
Reconnecting... 2/5 (stream disconnected before completion: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}")
2026-03-06T07:10:34.614609Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}", url: wss://chatgpt.com/backend-api/codex/responses
Reconnecting... 3/5 (stream disconnected before completion: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}")
2026-03-06T07:10:36.022348Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}", url: wss://chatgpt.com/backend-api/codex/responses
Reconnecting... 4/5 (stream disconnected before completion: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}")
2026-03-06T07:10:38.279778Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}", url: wss://chatgpt.com/backend-api/codex/responses
Reconnecting... 5/5 (stream disconnected before completion: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}")
2026-03-06T07:10:41.810222Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}", url: wss://chatgpt.com/backend-api/codex/responses
warning: Falling back from WebSockets to HTTPS transport. stream disconnected before completion: UTF-8 encoding error: failed to convert header to a str for header name 'x-codex-turn-metadata' with value: "{\"turn_id\":\"019cc1fb-c49d-7090-9547-3464bb36be78\",\"workspaces\":{\"D:\\cowork\\\xe6\x95\x99\xe6\x9d\x90\\chs-books-v2\":{\"associated_remote_urls\":{\"origin\":\"https://github.com/leixiaohui-1974/chs-books-v2.git\"},\"latest_git_commit_hash\":\"3e8742f9f66d54028bb076a207a55122e8eed2d4\",\"has_changes\":true}},\"sandbox\":\"none\"}"
ERROR: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Mar 12th, 2026 5:38 AM.
Warning: no last agent message; wrote empty content to _tri_output\ch05\review_codex.md
*

## Reviewer A (Claude — 理论严谨型)
*等待Claude Code会话中执行*

---
## 综合处理建议
请在Claude Code中执行以下操作：
1. 阅读三引擎评审意见
2. Claude补充理论评审（如尚未执行）
3. 合并Critical+Major问题，生成修改清单
4. 调用 `python tri_engine.py revise` 执行修改
