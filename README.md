# Robotics_Learn Vault

Obsidian 笔记 + Claude Code/Codex skills 的一体化知识库。配套两个 skill：

- **`note-capture`** — 把 Claude Code 或 Codex 对话**聚合到主题笔记**，形成活的知识库（不是流水账）
- **`paper-reading`** — 论文精读、笔记、vault 维护

跨设备通过 Obsidian Git 插件同步。

---

## 目录结构

```
Robotics_Learn/
├── .claude/skills/
│   ├── note-capture/       # 主题聚合式对话归档
│   └── paper-reading/      # 论文精读
├── topics/                 # 主题聚合知识库 — 一主题一文件
│   └── _index.md           # 主题目录（每次合并前必读）
├── chats/raw/              # 原始对话审计存档
├── inbox/                  # 快速捕获，未归主题
├── papers/                 # 论文（notes / metadata / pdfs / assets / navigation）
├── setup.sh                # 新设备一键 symlink 脚本
└── ...（你自己的笔记）
```

---

## 新设备装机

```bash
# 1. 克隆 vault
git clone <your-repo-url> ~/Note/Robotics_Learn

# 2. 把 vault 内的 skills 暴露给 Claude Code 和 Codex
cd ~/Note/Robotics_Learn
bash setup.sh

# 3. 验证
ls -la ~/.claude/skills/
ls -la ~/.agents/skills/
```

之后在任意目录启动 Claude Code 或 Codex，两个 skill 都可用。如果当前会话未刷新 skill 列表，请重启客户端。

---

## note-capture — 主题聚合知识库

**核心理念**：同一主题反复讨论 → 内容不断补充到 `topics/<slug>.md`，笔记越来越充实；不同主题之间自动交叉引用。**不是**每次对话都新建文件。

调用格式：`Use $note-capture to <command>: <args>`

### 捕获

| 命令 | 用途 |
|---|---|
| `save-chat: <hint>` | 智能合并当前对话到已有主题（或建新主题）。原文归档到 `chats/raw/` |
| `save-chat --dry-run` | 预览合并计划，不写盘 |
| `save-chat --force-topic <slug>` | 跳过匹配，直接合并到指定主题 |
| `save-inbox: <content>` | 快速捕获到 `inbox/`（未归主题） |
| `save-note: <path> <content>` | 写到指定路径（绕过主题系统） |

### 主题管理

| 命令 | 用途 |
|---|---|
| `topic new: <name>` | 建空主题 + 索引条目 |
| `topic list` | 打印主题索引 |
| `topic show: <slug>` | 打印主题笔记 |
| `topic merge: <old> to <new>` | 合并两个主题，重写 `[[old]]` 引用为 `[[new]]` |
| `topic rename: <old> to <new>` | 重命名主题 + 更新索引 + 重写引用 |

### 查询与维护

| 命令 | 用途 |
|---|---|
| `list [raw\|inbox\|topics]` | 按修改时间列出 |
| `find: <query>` | grep 搜索 topics + inbox |
| `promote: <inbox-file> to topic:<slug>` | 把 inbox 项目合并到主题 |

### 典型工作流

```
# 第一次讨论 obsidian git
> Use $note-capture to save-chat: obsidian git 与多设备同步
# → 建 topics/obsidian-git.md，索引加一行，原文存 chats/raw/

# 过几天再讨论相关话题
> Use $note-capture to save-chat: gitignore 配置
# → 自动识别为 obsidian-git 主题，合并进对应段落，追加变更日志

# 想预览合并结果不写盘
> Use $note-capture to save-chat --dry-run

# 主题识别错了？强制指定
> Use $note-capture to save-chat --force-topic ros2-humble-setup

# 想手工加个主题
> Use $note-capture to topic new: reinforcement-learning

# 事后发现主题重了，合并
> Use $note-capture to topic merge: obs-git to obsidian-git
```

### 合并的可控性

- 每次合并前先看**合并计划**（然后再问要不要写）
- 冲突的信息**不删除**旧内容，只加"更新于 YYYY-MM-DD"标注
- 主题笔记结尾有 `## 变更日志`，每次合并追加一段人类可读的 diff
- 原始对话永久留 `chats/raw/`，需要时可回溯重做

---

## paper-reading — 论文精读与 vault 维护

调用格式：`Use $paper-reading to <action>`

### 常用调用

| 场景 | 示例 |
|---|---|
| 精读 arXiv 论文 | `Use $paper-reading to read this paper slowly: https://arxiv.org/abs/2401.xxxxx` |
| 精读本地 PDF | `Use $paper-reading to read this local PDF slowly: /path/to/paper.pdf` |
| 转成中文详细笔记（带图） | `Use $paper-reading to turn this paper into a detailed Chinese Markdown note: <URL>` |
| 论文推荐 | `Use $paper-reading to recommend papers for <research question>` |
| 论文发现 | `Use $paper-reading to find recent papers related to <direction>` |
| 单篇入库 | `Use $paper-reading to maintain my paper vault for this paper: <URL>` |
| vault 整体维护 | `Use $paper-reading to organize my paper vault` |

### 辅助脚本

脚本可通过 `~/.claude/skills/paper-reading/scripts/` 或 `~/.agents/skills/paper-reading/scripts/` 访问：

```bash
export PAPER_READING_VAULT=~/Note/Robotics_Learn
python3 ~/.claude/skills/paper-reading/scripts/doctor.py --vault "$PAPER_READING_VAULT"
```

| 脚本 | 用途 |
|---|---|
| `doctor.py` | 检查环境和 vault 就绪状态 |
| `ingest_paper.py` | 提取论文元数据 |
| `extract_tex_source.py` | 抓 arXiv 源码 + 图片 |
| `extract_figures.py` | 从 PDF 提取候选插图 |
| `maintain_library.py` | 单篇入库 |
| `organize_library.py` | 全 vault 重建导航 |

### 参考文档

`~/.claude/skills/paper-reading/references/{paper-discovery,note-style,vault-organization,failure-cases}.md`

---

## 日常工作流

**捕获**（任意目录）：
```bash
claude
> Use $note-capture to save-chat: <topic hint>          # 主题式知识库
> Use $note-capture to save-inbox: <quick thought>      # 快速捕获
> Use $paper-reading to read this paper slowly: <URL>   # 论文
```

**同步**：Obsidian → 侧栏 Git → **Commit-and-sync**（⟳）

**另一台设备**：Obsidian 自动 Pull（或手动点 Pull），然后就能看到最新内容。

---

## note-capture vs paper-reading — 用哪个？

| 场景 | 用哪个 |
|---|---|
| 讨论某个工具/方法/概念 | `note-capture` → topics/ |
| 讨论某具体论文 | `paper-reading` → papers/ |
| 快速记一下想法 | `note-capture save-inbox` |
| 长时间项目笔记 | 手工在 vault 里维护，或用 `save-note` 到具体路径 |

**关键区分**：`topics/` 是**跨切面主题**（一个工具、一种方法、一类经验），一个主题可以引用多篇论文；`papers/` 是**具体作品**，一篇论文一条记录。

---

## 相关

- 原始设计计划：`~/.claude/plans/skills-nested-garden.md`
- Claude Code 全局 skills 目录：`~/.claude/skills/`
- Codex 全局 skills 目录：`~/.agents/skills/`
- Obsidian Git 插件：Obsidian → Settings → Community plugins → Git
