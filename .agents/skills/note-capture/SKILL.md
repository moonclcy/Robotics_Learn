---
name: note-capture
description: Merge Codex or Codex conversation content into a topic-aggregated knowledge base at ~/Note/Robotics_Learn. Instead of one-file-per-chat, each save-chat call intelligently merges new content into an existing topic note (or creates a new topic), keeping a growing knowledge base rather than a chat log. Use for explicit `$note-capture` commands or natural-language requests such as "整理笔记" and "save this chat". Paper-related requests are delegated to the paper-reading skill.
---

# Note Capture — Topic-Aggregated Knowledge Base

Merges Codex or Codex conversations into a living, topic-organized knowledge base. Unlike traditional per-chat archiving, this skill folds new content into existing topic notes so a subject grows more complete over time rather than fragmenting across many files.

Companion to the `paper-reading` skill (which handles academic papers).

## Vault layout

```
$HOME/Note/Robotics_Learn/
├── topics/              # one file per topic, canonical knowledge
│   ├── _index.md        # topic directory — MUST read before merging
│   └── <slug>.md
├── chats/raw/           # raw conversation archive (audit only)
├── inbox/               # quick captures not yet promoted to a topic
└── papers/              # managed by paper-reading skill (do not touch)
```

Root is fixed at `$HOME/Note/Robotics_Learn`. Always use absolute paths — this skill is invoked from arbitrary working directories.

## Topic note skeleton

Every `topics/<slug>.md` follows this structure so merges are idempotent:

```markdown
---
title: <human-readable, can be Chinese>
slug: <english-kebab>
tags: [topic, <domain-tag>, ...]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [chats/raw/2026-07-17-xxx-abcd.md]
related: [[other-topic-a]], [[other-topic-b]]
---

## 概念
## 关键结论
## 展开细节
## 命令 / 代码 / 配置
## 常见问题
## 后续行动
## 相关 [[]]
## 变更日志

<!-- 2026-07-17 -->
- 新增：xxx
- 更新：yyy
```

Skip sections with no content — do not leave empty headings. `## 变更日志` is append-only and records what changed in each merge.

## `topics/_index.md` — the directory

```markdown
# Topics Index

<!-- one line per topic. slug is the filename without .md. -->

- **obsidian-git** — Obsidian git sync, multi-device workflow. tags: tools, sync
- **ros2-humble-setup** — ROS2 Humble install & colcon gotchas. tags: robotics, ros2
```

Read this file before every merge. Update it whenever a topic is created, renamed, merged, or deleted.

## Commands

Invoke with `Use $note-capture to <command>: <args>`.

### `save-chat` — merge current conversation into a topic

```
Use $note-capture to save-chat: <optional topic hint>
Use $note-capture to save-chat --dry-run
Use $note-capture to save-chat --force-topic <slug>
```

Flow:
1. **Archive raw**: write full conversation to `chats/raw/YYYY-MM-DD-<slug>-<hash>.md`
2. **Read `topics/_index.md`**
3. **Match**: pick target topic
   - High confidence hit → merge into that topic
   - No match → create new topic (ask user to confirm the slug)
   - Ambiguous → present 2-3 candidates + "new topic" option, ask user
   - `--force-topic` skips matching
4. **Merge** (into existing topic):
   - Read `topics/<slug>.md`
   - Insert new content into the right sections; combine duplicates; mark conflicting info with "更新于 YYYY-MM-DD"
   - Update frontmatter: `updated`, append to `sources`, add new `related` links if applicable
   - Append a short block under `## 变更日志` describing what was added/changed (5-10 bullets max)
5. **Or create** (new topic):
   - Write `topics/<new-slug>.md` from the skeleton
   - Append a new line to `topics/_index.md`
6. **Cross-link**: if the merged content references other existing topics (by name), add `[[...]]` links in `## 相关` on both sides. Never link to non-existent topics.
7. **Output**: print the target file path, what was merged/created, and remind the user to Commit-and-sync

`--dry-run` runs steps 1-4/5 in simulation mode, prints the merge plan, and writes NOTHING to disk (raw archive included). Use for previewing.

### `save-inbox` — quick capture, bypass topic system

```
Use $note-capture to save-inbox: <content>
```

Writes near-verbatim to `inbox/YYYY-MM-DD-<slug>.md`. Use when the material isn't ready for a topic yet (e.g., an interesting URL to review later).

### `save-note` — write to an explicit path

```
Use $note-capture to save-note: <path relative to vault> <content>
```

Writes to `$HOME/Note/Robotics_Learn/<path>.md`. Creates parent dirs. Bypasses the topic system — use when you know exactly where content belongs.

### `topic new: <name>` — create an empty topic

```
Use $note-capture to topic new: reinforcement-learning
```

Creates `topics/reinforcement-learning.md` with skeleton, adds a line to `_index.md`. Prompts for the human title, tags, and one-line description for the index.

### `topic list` — print the topic index

```
Use $note-capture to topic list
```

Reads `topics/_index.md` and displays it.

### `topic show: <slug>` — print a topic note

```
Use $note-capture to topic show: obsidian-git
```

Prints `topics/<slug>.md`. Read-only.

### `topic merge: <old> to <new>` — combine two topics

```
Use $note-capture to topic merge: obsidian-git to note-sync
```

- Read both files
- Intelligently merge `old` content into `new` (same rules as save-chat merge)
- Delete `topics/<old>.md`
- Update `_index.md` (remove old line, adjust new description if needed)
- Scan the vault for `[[old]]` wikilinks and rewrite them to `[[new]]`
- Log the merge in `new`'s `## 变更日志`

### `topic rename: <old> to <new>` — rename without content merge

```
Use $note-capture to topic rename: obsidian-git to obsidian-sync
```

Same as merge but the destination doesn't pre-exist. Renames file, updates index, rewrites all `[[old]]` references.

### `list` — recent activity

```
Use $note-capture to list                    # topics by updated time
Use $note-capture to list raw                # recent chats/raw/
Use $note-capture to list inbox
```

### `find: <query>` — grep

```
Use $note-capture to find: obsidian git
```

Searches `topics/` first, then `inbox/`. Read-only.

### `promote: <inbox-file> to <dest>` — move inbox item

```
Use $note-capture to promote: 2026-07-17-ros2-note to topic:ros2-humble-setup
Use $note-capture to promote: 2026-07-17-quick-thought to inbox   # (no-op, just an example)
```

If dest is `topic:<slug>`, merges the inbox content into that topic (same flow as save-chat merge). Otherwise moves the file to the given folder path.

## Paper handoff

If the conversation is primarily about a specific paper (heavy references to arXiv id/title, or the user asks to "read this paper"):

> This looks like paper content — I'll:
> 1. Archive this conversation to `chats/raw/`
> 2. Suggest invoking `paper-reading` skill for the paper note itself.

Do NOT create a topic note for individual papers (they belong in `papers/notes/`). Topics are for cross-cutting subjects (a method, a tool, a workflow).

## Filename & slug rules

- Slug: 2-4 English words, lowercase, hyphen-separated. **No Chinese** (git cross-platform hazard).
- Topic file: `topics/<slug>.md`
- Raw archive: `chats/raw/YYYY-MM-DD-<slug>-<4-char-hash>.md`
- Inbox: `inbox/YYYY-MM-DD-<slug>.md`
- Slug collision: append `-2`, `-3`; never silently overwrite

## Frontmatter contracts

**Topic** (all fields required):
```yaml
title, slug, tags, created, updated, sources, related
```

**Raw archive**:
```yaml
date, source: Codex | Codex, conversation_hash, topics_touched: [<slugs>]
```

Set `source` to the client currently running the skill. Do not label Codex conversations as Codex.

**Inbox** (minimal):
```yaml
date, tags: [inbox], source
```

## Cross-linking rules

- Only insert `[[<slug>]]` when `topics/<slug>.md` exists. Check with:
  ```bash
  test -f "$HOME/Note/Robotics_Learn/topics/<slug>.md"
  ```
- When adding a link to topic A pointing at topic B, also add A back into B's `related` (bidirectional)
- Never fabricate links

## Merge quality guardrails

1. Read `topics/_index.md` and the target topic file **completely** before merging
2. Present a short "merge plan" in the chat output before writing (unless `--dry-run` is off and user already approved)
3. When conflicting info appears (e.g., user's old note says X, new content says Y):
   - Do NOT delete the old statement
   - Add "更新于 YYYY-MM-DD：新说法 ..." next to it
4. `## 变更日志` entry must be human-readable and concrete: "新增：git 代理配置命令" not "更新了内容"
5. Never modify sections outside the standard skeleton (user may have added custom sections manually — leave them)
6. Never `git commit` / `git push` from this skill

## Post-write output

Always print:
- Absolute path of file(s) written
- Which topic was merged into or created
- Which raw archive file was created
- A reminder: `Run Commit-and-sync in Obsidian to propagate.`

## Templates

- `templates/topic.md` — new-topic skeleton
- `templates/chat.md` — merge-plan preview format
- `templates/inbox.md` — minimal inbox capture
