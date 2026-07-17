---
title: Obsidian Git — 多设备同步与 vault 内 git 管理
slug: obsidian-git
tags: [topic, tools, obsidian, git, sync]
created: 2026-07-17
updated: 2026-07-17
sources: [chats/raw/2026-07-17-note-capture-v2-a3f2.md]
related: [[note-capture]]
---

## 概念

- **Obsidian Git** 是 Obsidian 的 community plugin，让你在 Obsidian 内部直接跑 git 操作（提交、拉取、推送、同步）
- 用来做**多设备 Obsidian vault 同步**：所有设备指向同一个 git 仓库，改动通过 commit + push/pull 分发
- 核心约束：**vault 根目录必须等于 `.git` 所在目录**

## 关键结论

- **Obsidian Git 插件在 vault 根目录找 `.git`**。如果 `.git` 在子目录，插件会报"不是 git 仓库"
- **切 vault 用 "Open folder as vault"**（File → Open another vault → Open folder as vault），选到 `.git` 所在目录
- **右下角状态栏的分支名 + ⟳ 图标**能直接触发 Commit-and-sync，不用打开完整 git 面板
- **不要用 `git commit --amend` 修补 Obsidian Git 提交**：插件依赖 commit 是 append-only 追加式的
- **不要 `--no-verify` 跳 hook**：如果有 hook 报错先排查根因

## 展开细节

### 排查"不是 git 仓库"
1. 打开终端到疑似 vault 根：`cd ~/Note/Robotics_Learn`
2. `git status` — 如果正常显示分支和状态，则 git 仓库本身没问题
3. `ls ~/Note/` — 找到 `.obsidian/` 所在位置，这就是 vault 根
4. 对比：`.obsidian/` 和 `.git/` 是否在同一层？不同则插件找不到

### 两种修复方案
**A. 把 git 仓库迁到 vault 根**（想同步整个 vault）：
```bash
mv ~/Note/Robotics_Learn/.git ~/Note/.git
cd ~/Note && git add -A && git status
```

**B. 把 Obsidian vault 切到子目录**（只同步子文件夹）：
- File → Open another vault → Open folder as vault → 选 `~/Note/Robotics_Learn/`
- 新 vault 是独立配置，需要重新装 Obsidian Git 插件
- 或先复制配置：`cp -r ~/Note/.obsidian/plugins ~/Note/Robotics_Learn/.obsidian/`

### 右侧栏 git 视图
- 状态栏（右下）总是显示分支名和同步图标 ⟳，随时可点
- 完整视图：Ctrl+P → `Git: Open source control view`（改动列表 + 暂存 + 提交）
- 历史视图：Ctrl+P → `Git: Open history view`
- 打开后拖到侧栏可固定住

### 常用图标
| 图标 | 含义 |
|---|---|
| ↑ | Push |
| ✓ | Commit |
| ➕ | Stage all |
| ➖ | Unstage all |
| ⬇ | Pull |
| ⟳ | Commit-and-sync（提交+拉+推 一键） |

## 命令 / 代码 / 配置

### Commit message 模板
在插件设置里配置，支持占位符：
- `{{date}}` — 当前日期
- `{{hostname}}` — 主机名
- `{{numFiles}}` — 改动文件数
- `{{files}}` — 改动文件列表

示例：`vault backup: {{date}} ({{hostname}})`

### 代理配置（大陆网络）
```bash
git config --global http.proxy http://127.0.0.1:7897
git config --global https.proxy http://127.0.0.1:7897
```
port 视 clash/v2rayN 设置调整。

### 常用命令面板动作
- `Git: Commit-and-sync` — 一键完整同步
- `Git: Pull` / `Git: Push` / `Git: Fetch`
- `Git: Commit` / `Git: Amend staged`（谨慎用）
- `Git: Open diff view` — 看具体改了啥
- `Git: Edit .gitignore` — 编辑忽略规则
- `Git: Create new branch` / `Git: Switch branch`

## 常见问题

**Q: 插件启用后一直说 "not a git repository"？**
- 99% 是 vault 根 ≠ `.git` 所在目录。见"排查"和"修复"段落

**Q: 想同步但不想每次都手动点？**
- 插件设置 → Auto backup after X minutes / Auto pull on load
- 缺点：可能覆盖你正在改的 conflict；建议保持手动，养成 Commit-and-sync 习惯

**Q: `.obsidian/workspace.json` 一直改，diff 很吵？**
- 在 `.gitignore` 加：`.obsidian/workspace*` — 排除工作区状态，只同步真正的插件配置和笔记

**Q: 冲突了怎么办？**
- Obsidian Git 会在冲突文件里插入标记 `<<<<<<< HEAD` — 手动打开修，改完再 commit
- 或用 IDE 打开 vault 目录，用图形化 merge 工具

**Q: PDF/大文件让仓库变重？**
- 考虑 git-lfs（跟踪 `*.pdf`）
- 或 `.gitignore` 排除特定目录（例如 `papers/pdfs/` 不追踪，只在本地留）

**Q: 大陆网络推 GitHub 慢/失败？**
- 见"代理配置"段落
- 或换 gitee/coding.net 作为镜像仓库

## 后续行动

- [ ] 在插件设置里配置合适的 commit message 模板（默认 `vault backup: {{date}}`）
- [ ] 考虑加 `.obsidian/workspace*` 到 `.gitignore` 减少无意义 diff
- [ ] 每台设备统一 hostname，方便看 commit 是从哪台机器来的

## 相关

- `[[note-capture]]` — 依赖 obsidian-git 的同步机制分发到多设备

## 变更日志

<!-- 2026-07-17 -->
- 新增：从零建立 obsidian-git 主题笔记，覆盖多设备同步、vault 根排查、代理配置、图标含义、命令面板动作
- 关联：初次提及 [[note-capture]]（同批创建，note-capture 的分发依赖此主题）
