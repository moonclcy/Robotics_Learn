---
title: note-capture — 主题聚合式知识库 skill
slug: note-capture
tags: [topic, tools, claude-code, obsidian, knowledge-base]
created: 2026-07-17
updated: 2026-07-17
sources: [chats/raw/2026-07-17-note-capture-v2-a3f2.md]
related: [[paper-reading]], [[obsidian-git]]
---

## 概念

- `note-capture` 是一个 Claude Code skill，把 Claude Code 对话**聚合到主题笔记**而不是每次生成新文件
- 与 `paper-reading` skill 并列：note-capture 管**跨切面主题**（工具、方法、经验、概念），paper-reading 管**具体论文**
- 物理位置：`~/Note/Robotics_Learn/.claude/skills/note-capture/`
- 通过 `~/.claude/skills/` 下的 symlink 暴露到全局，任意目录 `claude` 都能调用
- 单一事实源在 vault 内，跟已有的 Obsidian Git 同步机制走多设备分发

## 关键结论

- **把 skill 放 vault 内**（而非各设备各存一份的 `~/.claude/skills/`）是关键选择——跟已有 git 同步走，多设备零漂移、无额外机制
- **`paper-reading` 直接 vendor 自 `~/下载/paper-reading-main`**，不改源码；用环境变量 `PAPER_READING_VAULT=~/Note/Robotics_Learn` 或 `--vault` 参数指向 vault
- **主题聚合优于时间序**：一主题一文件，反复讨论合并进已有笔记，笔记随时间增值而非碎片化
- 合并可控性依赖三个机制：`chats/raw/` 原文永久留存 + `## 变更日志` 段落 + `--dry-run` 预览
- **文件名严格英文 kebab-case**（跨平台 git 安全）；文件正文和 `title` frontmatter 可用中文

## 展开细节

### v1 → v2 演进
- v1（时间序）：每次对话生成 `chats/YYYY-MM-DD-*.md`
- v2（主题聚合）：`topics/<slug>.md` 一主题一文件，反复讨论合并到同一文件
- v2 保留 `save-inbox` `save-note` 作为绕过主题机制的逃生舱

### 智能合并流程
1. 提取当前对话有价值内容
2. 归档原文到 `chats/raw/YYYY-MM-DD-<slug>-<hash>.md`
3. 读 `topics/_index.md` 判断该归入哪个主题
4. 高置信匹配 → 合并；无匹配 → 建新主题；模糊 → 让用户确认
5. 更新 frontmatter (`updated`, `sources`, `related`) + 在对应 section 插入新内容
6. 追加 `## 变更日志` 一段人类可读的 diff 摘要

### 主题笔记固定骨架
```
概念 / 关键结论 / 展开细节 / 命令 / 常见问题 / 后续行动 / 相关 / 变更日志
```
骨架稳定 → LLM 幂等合并；空 section 跳过不留空标题。

### 冲突处理
不删除旧内容，标注"更新于 YYYY-MM-DD：新说法 ..."。用户可回溯所有历史结论。

### 双链保守
只在目标主题存在时才加 `[[...]]`，双向同步。宁可欠链也不留 dangling link。

## 命令 / 代码 / 配置

### 新设备装机
```bash
git clone <vault-url> ~/Note/Robotics_Learn
cd ~/Note/Robotics_Learn && bash setup.sh
ls -la ~/.claude/skills/   # 应看到两个 symlink
```

### setup.sh 核心
```bash
ln -sfn "$VAULT/.claude/skills/note-capture" ~/.claude/skills/note-capture
ln -sfn "$VAULT/.claude/skills/paper-reading" ~/.claude/skills/paper-reading
```

### 完整命令集
`Use $note-capture to <command>: <args>`

**捕获**：
- `save-chat: <hint>` — 智能合并当前对话到主题
- `save-chat --dry-run` — 预览合并计划不写盘
- `save-chat --force-topic <slug>` — 跳过匹配指定主题
- `save-inbox: <content>` — 快速捕获，绕过主题
- `save-note: <path> <content>` — 写到指定路径

**主题管理**：
- `topic new: <name>` / `topic list` / `topic show: <slug>`
- `topic merge: <old> to <new>` / `topic rename: <old> to <new>`

**查询与维护**：
- `list [raw|inbox|topics]`
- `find: <query>`
- `promote: <inbox-file> to topic:<slug>`

### paper-reading 交接
论文相关内容（arXiv 引用、PDF 精读）自动转给 `paper-reading` skill；note-capture 只归档对话到 `chats/raw/`，论文笔记落在 `papers/notes/`。

## 常见问题

**Q: skill 触发不成功？**
- 检查 `readlink ~/.claude/skills/note-capture` 指向 vault 内正确路径
- 确认 Claude Code 是新会话（skill 只在启动时扫描；中途创建的 skill 需要重启会话才被正式加载）

**Q: Obsidian 里看不到 `.claude/`？**
- 正常。Obsidian 默认忽略点开头目录（不显示在文件树），但 Git 仍会追踪
- 想在 Obsidian 里也能看：Settings → Files & Links → Detect all file extensions（不推荐）

**Q: `chats/raw/` 会越来越大吗？**
- 每次对话一份原文，一年也就几百个文件、几十 MB，Git 完全能承受
- 长期太大：归档旧的到 `chats/raw/archive/YYYY/` 或直接 gzip

**Q: 主题分裂了怎么办？**
- 事后用 `topic merge: <old> to <new>` 合并
- 命令会自动重写 vault 内所有 `[[old]]` 引用为 `[[new]]`

**Q: Windows 设备 symlink 不通用？**
- 目前只在 Linux 验证过；Windows 场景之后用 wrapper skill 补（简单文件转发）

## 后续行动

- [ ] 端到端跑一次真实的 `save-chat`（不带 `--dry-run`），验证首篇主题笔记
- [ ] 观察前 5-10 个主题是否分类合理；不合理用 `topic merge` 归整
- [ ] （远期）v3：周汇总、孤儿主题扫描、语义搜索接入
- [ ] 重启 Claude Code 会话，验证 skill 走 Skill 工具而非模拟执行

## 相关

- `[[paper-reading]]` — 姊妹 skill，管具体论文；note-capture 把论文任务转给它
- `[[obsidian-git]]` — 跨设备同步机制的载体，note-capture 的分发依赖它

## 变更日志

<!-- 2026-07-17 -->
- 新增：从零建立 note-capture 主题笔记，覆盖 v2 主题聚合式知识库的设计、命令集、装机方法
- 关联：初次提及 [[paper-reading]]、[[obsidian-git]]（同批创建）
