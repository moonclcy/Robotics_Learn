# Merge Plan Preview

<!-- Used by save-chat to show what will be merged before writing. -->

## Target
- Topic: `<slug>` (existing | new)
- File: `topics/<slug>.md`
- Confidence: high | medium | low
- Alternative candidates considered: <slug-a>, <slug-b>

## Raw archive
- Will write: `chats/raw/YYYY-MM-DD-<slug>-<hash>.md`

## Changes to topic

### Section: 概念
- (add) ...
- (update) 原："..." → 新："..." (更新于 YYYY-MM-DD)

### Section: 命令 / 代码 / 配置
- (add) ...

### Section: 关键结论
- (add) ...

## Frontmatter updates
- `updated`: → YYYY-MM-DD
- `sources`: += chats/raw/xxx.md
- `related`: += [[other-topic]]

## Cross-links to add
- In `topics/other-topic.md` — add `[[<this-slug>]]` under 相关

## 变更日志 entry
```
<!-- 2026-07-17 -->
- 新增：xxx
- 更新：yyy
```
