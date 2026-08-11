#!/usr/bin/env bash
# Link vault-hosted skills into the user-level Claude Code and Codex skill directories.
# Run once per device after cloning the vault.
set -euo pipefail

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIRS=(
  "$HOME/.claude/skills"
  "$HOME/.agents/skills"
)

for target_dir in "${TARGET_DIRS[@]}"; do
  mkdir -p "$target_dir"
  for skill in note-capture paper-reading; do
    src="$VAULT/.claude/skills/$skill"
    dst="$target_dir/$skill"
    if [[ ! -d "$src" ]]; then
      echo "  skip: $src does not exist"
      continue
    fi
    ln -sfn "$src" "$dst"
    echo "  linked: $dst -> $src"
  done
done

echo
echo "Done. Skills are now available to Claude Code and Codex."
echo "Verify Claude Code: ls -la ~/.claude/skills/"
echo "Verify Codex:       ls -la ~/.agents/skills/"
