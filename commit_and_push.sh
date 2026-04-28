#!/usr/bin/env bash
# CHS-books-v2 一键提交与推送脚本
# 用法：cd /Users/rainfields/hydrosis-local/research/chs-books-v2
#       bash commit_and_push.sh
# 由 Claude 生成于 2026-04-28，覆盖阶段一至五全工程整改成果

set -e

REPO=/Users/rainfields/hydrosis-local/research/chs-books-v2
cd "$REPO"

echo "==========================================="
echo "  CHS-books-v2 提交与推送"
echo "==========================================="
echo

# === Step 1: 解除遗留 index.lock ===
if [ -f .git/index.lock ]; then
  echo "[1/7] 检测到 .git/index.lock，正在解除..."
  rm -f .git/index.lock
  echo "    ✅ 已解除"
else
  echo "[1/7] .git/index.lock 不存在，跳过"
fi
echo

# === Step 2: 检查 git 用户身份 ===
USER_NAME=$(git config user.name || echo "")
USER_EMAIL=$(git config user.email || echo "")
echo "[2/7] git 用户身份："
echo "    user.name  = $USER_NAME"
echo "    user.email = $USER_EMAIL"
if [ -z "$USER_NAME" ] || [ -z "$USER_EMAIL" ]; then
  echo "    ⚠️  缺少身份配置，请手动跑："
  echo "        git config user.name 'Lei Xiaohui'"
  echo "        git config user.email '你的邮箱@example.com'"
  echo "    然后重跑本脚本。"
  exit 1
fi
echo

# === Step 3: 看一眼变更规模 ===
echo "[3/7] 变更文件统计："
TOTAL=$(git status --short | wc -l | tr -d ' ')
MODIFIED=$(git status --short | grep -c '^ M' || true)
DELETED=$(git status --short | grep -c '^ D' || true)
ADDED=$(git status --short | grep -c '^??' || true)
echo "    总变更 : $TOTAL"
echo "    修改   : $MODIFIED"
echo "    删除   : $DELETED"
echo "    新增   : $ADDED"
echo

# === Step 4: 确认是否继续 ===
read -p "[4/7] 准备 git add -A + commit + push origin main，是否继续？(y/N) " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  echo "    用户取消，退出"
  exit 0
fi
echo

# === Step 5: 添加所有变更 ===
echo "[5/7] 执行 git add -A ..."
git add -A
STAGED=$(git diff --cached --name-only | wc -l | tr -d ' ')
echo "    ✅ 已暂存 $STAGED 个文件"
echo

# === Step 6: 提交 ===
echo "[6/7] 执行 git commit ..."
git commit -m "feat(chs-books-v2): 阶段一至五全工程整改完成

阶段一: 硬错误清零
- T1-CN ch14 胶东数据 500→571km，case_data 同步补全 95 闸/47 节制闸/46 阀
- concept_authority 升级 v2.1，11 处权威位置反向校正（CHS=§1.5、CPSS=§8.2、
  WNAL=§10.3、闭环四预=§8.1、四态机=§2.7（理论）/§13.4.2（HydroOS）、
  HDC=§7.4、MBD=§12.1-§12.10、五个控制本质=§2.3、Agent=§2.6 等）
- xIL 从 4 级修正为 3 级（OIL 在 T1-CN 实然未定义）
- T3-Engineering 8 处死引用清理（ch09-14），改引现有章节或 Lei et al. 2025 论文

阶段二: 术语与格式统一
- MRC 中文统一为'最小风险状态'
- 四态机双版本并存（CHS 理论版 ch02 §2.7：正常/受限/降级/接管Takeover；
  HydroOS 工程版 ch13 §13.4.2：正常/降级/应急/检修），全系列 Managed→Takeover
- '自治等级'→'自主等级'、'操作设计域'→'运行设计域'
- T5 ch01 '水利系统控制论'→'水系统控制论'
- T1-CN ch03 六元组排序统一 (P,A,S,D,C,O)
- 全系列 826 处公式编号统一为 \\tag{X-Y} 连字符格式
- 附带修复 54 处 TAB+ag 渲染 bug（T4 ch07/ch03、T5 ch04/ch07）

阶段三: 内容补完与格式刷齐
- T5-Intelligence 8 章变更日志补齐
- T4-Platform 8 章变更日志补齐（ch01-ch08，ch09-ch12 此前已有）
- T3-Engineering ch10 表 10-1 编号补全
- ModernControl/casebook.md 增加变更日志、学习目标、案例集与 T1-CN/T2a 关系说明
- 新建 T5-Intelligence/ch09《MLOps 与模型部署》（约 1.0 万字，10 节 + 4 公式
  + 5 表 + 10 习题 + 15 参考文献），先 brief 后正文，明确与 T2b ch10/T4 ch03/
  T4 ch12 的边界
- ModernControl 9 章理论_v2 同步归档至 archived_v2/

阶段四: 出版准备
- T2-CN ch11 闸站数据按 case_data 加注精确口径
- T1-CN ch00 §0.4.4 增加'CHS 书系核心概念—权威定义导航'小表（17 概念）
- 新建 _shared/publication_checklist.md（出版社匹配 + 自检清单 + 阻塞项 + 时间线）
- 新建 _shared/CLAUDE_TOTAL_ENGAGEMENT_SUMMARY.md（全工程总结）

阶段五: 内部代号→正式简称替换
- 八卷正式书名与简称约定（《水控》《觉醒》《建模》《认知》《标治》《平台》
  《算法》《案例》），落地到 _shared/series_naming_convention.md
- Perl 脚本批处理 95 个 _final.md 文件，约 700 处跨卷引用替换
- 处理'代号+全名'双书名（T1-CN《水系统控制论》→《水系统控制论》（简称《水控》））
- ch 范围引用自动合并（[T1-CN ch00-ch03]→《水控》第 0-3 章）
- 新建 _shared/series_preamble_template.md（投稿稿'本书系导读'页模板）
- 变更日志 HTML 注释中的历史代号引用保留作内部档案

详见 _shared/CLAUDE_TOTAL_ENGAGEMENT_SUMMARY.md 与 phase1-5_completion_report.md
"
echo "    ✅ commit 完成"
echo

# === Step 7: 推送 ===
echo "[7/7] 执行 git push origin main ..."
echo "    （首次 push 时 macOS Keychain 可能弹窗要求 GitHub 凭据）"
echo "    （用户名 leixiaohui-1974，密码必须用 Personal Access Token，不是登录密码）"
echo
git push origin main
echo
echo "==========================================="
echo "  ✅ 已推送到 GitHub origin/main"
echo "==========================================="
echo
echo "可选：同步到 GitLab 镜像"
echo "    git push gitlab main"
echo

# === 显示远程状态 ===
echo "远程对照："
git log --oneline -3
echo "..."
git remote -v
