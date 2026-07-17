---
date: 2026-07-17
source: Claude Code
conversation_hash: b7c1
topics_touched: [note-capture]
---

# 仓库使用讲解

用户请求讲解 Robotics_Learn 仓库的使用方法,助手基于 README.md 做了简要总结。

## 用户请求

> 讲解一下这个仓库的使用方法

## 助手回答要点

基于 README.md 摘要:

### 两大 Skill
- `note-capture` — 主题聚合式笔记,同一主题合并到 topics/ 下对应文件
- `paper-reading` — 论文精读,产出中文笔记,维护 papers/

### 新设备装机 3 步
```bash
git clone <repo-url> ~/Note/Robotics_Learn
cd ~/Note/Robotics_Learn && bash setup.sh
ls -la ~/.claude/skills/
```

### 日常最常用的 4 个命令
```
Use $note-capture to save-chat: <主题提示>
Use $note-capture to save-inbox: <内容>
Use $note-capture to save-chat --dry-run
Use $paper-reading to read this paper slowly: <arxiv URL>
```

### 合并安全机制
- 合并前展示合并计划
- 冲突信息不删旧,只标注"更新于 YYYY-MM-DD"
- 主题笔记结尾有 `## 变更日志`
- 原始对话永久归档 chats/raw/

### note-capture vs paper-reading
- 工具/方法/经验 → note-capture → topics/
- 具体论文 → paper-reading → papers/
- 一闪而过想法 → save-inbox → inbox/

### 同步
Obsidian Git 插件 → Commit-and-sync(⟳);另一台设备 Pull。

## 后续对话

用户随后触发 `save-chat: 仓库使用`。助手判断本轮内容与已有 topics/note-capture.md 高度重复,提出合并计划(只增加"日常最常用的 4 个命令"速查小节)。用户回复"那就不动了",遂只做原文归档,不修改主题笔记。
