# note-capture

Merges Claude Code conversations into a **topic-aggregated knowledge base** at `~/Note/Robotics_Learn`. Instead of one file per chat, each save-chat call folds new content into an existing topic note (or creates a new one), so subjects grow more complete rather than fragmenting.

Companion to `paper-reading` (which handles papers).

## Vault layout

```
~/Note/Robotics_Learn/
├── topics/              # one file per topic — the canonical knowledge base
│   ├── _index.md        # directory of all topics
│   └── <slug>.md
├── chats/raw/           # raw conversation archive (audit only)
├── inbox/               # quick captures not yet promoted
└── papers/              # managed by paper-reading skill
```

## Invocation

Prefix with `Use $note-capture to <command>: <args>` for explicit invocation.

## Commands

### Capture

| Command | Purpose |
|---|---|
| `save-chat: <hint>` | Merge current conversation into a matching topic (or create new). Archives raw to `chats/raw/`. |
| `save-chat --dry-run` | Preview merge plan without writing anything |
| `save-chat --force-topic <slug>` | Skip topic matching, merge into a specified topic |
| `save-inbox: <content>` | Quick verbatim capture to `inbox/` |
| `save-note: <path> <content>` | Write to an explicit vault-relative path |

### Topic management

| Command | Purpose |
|---|---|
| `topic new: <name>` | Create an empty topic + index entry |
| `topic list` | Print the topic index |
| `topic show: <slug>` | Print a topic note |
| `topic merge: <old> to <new>` | Merge `old` content into `new`, delete `old`, rewrite `[[old]]` references |
| `topic rename: <old> to <new>` | Rename topic file + update index + rewrite references |

### Query & maintenance

| Command | Purpose |
|---|---|
| `list [raw\|inbox\|topics]` | Recent activity in target folder |
| `find: <query>` | grep across topics and inbox |
| `promote: <inbox-file> to topic:<slug>` | Merge inbox item into a topic |
| `promote: <inbox-file> to <folder>` | Move inbox item to a folder |

## Examples

```
# First-time discussion of a subject
Use $note-capture to save-chat: obsidian git 与多设备同步
# → creates topics/obsidian-git.md, adds line to _index.md, archives raw

# Later discussion on the same subject
Use $note-capture to save-chat: gitignore 配置
# → merges into topics/obsidian-git.md, appends to 变更日志

# Preview before merging
Use $note-capture to save-chat --dry-run

# Force target if auto-match is wrong
Use $note-capture to save-chat --force-topic ros2-humble-setup

# Manual topic
Use $note-capture to topic new: reinforcement-learning
Use $note-capture to topic list
Use $note-capture to topic show: obsidian-git

# Cleanup
Use $note-capture to topic merge: obs-git to obsidian-git
Use $note-capture to topic rename: obsidian-git to note-sync

# Search
Use $note-capture to find: rsync
```

## Merge behavior

Before writing, the skill:
1. Archives the full raw conversation to `chats/raw/`
2. Reads `topics/_index.md`
3. Picks the target topic (or asks if ambiguous)
4. Reads that topic file, plans changes section-by-section
5. Presents the merge plan
6. Writes: updates frontmatter (`updated`, `sources`, `related`), inserts new content into the right sections, appends a **variable log** entry describing what changed
7. Optionally adds bidirectional `[[wikilinks]]` if related topics exist

Conflicting info is never deleted — old statement is kept with an "更新于 YYYY-MM-DD: <new claim>" annotation.

## Filenames

- Topic: `topics/<english-kebab-slug>.md`
- Raw: `chats/raw/YYYY-MM-DD-<slug>-<hash>.md`
- Inbox: `inbox/YYYY-MM-DD-<slug>.md`
- **No Chinese in filenames.** File bodies can be Chinese; titles in frontmatter can be Chinese.

## What NOT to do

- Do not use this skill for papers — use `paper-reading` instead
- Do not `git commit` from this skill — you review in Obsidian and Commit-and-sync manually
- Do not create a topic per paper — topics are cross-cutting subjects; individual papers live in `papers/notes/`

## Cross-device

Skill lives inside vault (`.claude/skills/note-capture/`). Sync via Obsidian Git. New devices: `bash setup.sh` at vault root to symlink into `~/.claude/skills/`.
