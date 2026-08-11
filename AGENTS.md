# AGENTS.md

这是一个 **Obsidian vault**，同时也是通过 git 在多台电脑间同步的机器人学习笔记库。任何在这个目录下工作的 Codex 会话都请遵守以下规则。

## Obsidian 图片路径规则

所有 Markdown 笔记里的图片引用必须使用相对路径或 Obsidian wiki 语法，禁止使用绝对路径（如 `/home/liushuo/Note/...`）或 `file://` 链接。

推荐写法（按优先级）：

1. Wiki 语法：`![[filename.png]]`
2. 相对路径：
   - 笔记在 `papers/notes/`：`../assets/<paper-slug>/xxx.png`
   - 笔记在 vault 根目录：`papers/assets/<paper-slug>/xxx.png`

## 笔记库结构

```text
Robotics_Learn/
├── papers/
│   ├── notes/
│   ├── metadata/
│   ├── pdfs/
│   ├── assets/<slug>/
│   └── navigation/
├── chats/
├── topics/
├── inbox/
└── 具身力控.md 等
```

## 常用 skill

- `Use $paper-reading to read this paper slowly: <arxiv URL>`：生成元数据、PDF、关键图和中文详细笔记。
- `Use $note-capture to <command>`：把对话内容合并进主题聚合知识库。
