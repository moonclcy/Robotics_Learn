#!/usr/bin/env bash
# Link vault-hosted skills into the user-level Claude Code skills directory.
# Run once per device after cloning the vault.
set -euo pipefail

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME/.claude/skills"

mkdir -p "$TARGET_DIR"

for skill in note-capture paper-reading; do
  src="$VAULT/.claude/skills/$skill"
  dst="$TARGET_DIR/$skill"
  if [[ ! -d "$src" ]]; then
    echo "  skip: $src does not exist"
    continue
  fi
  ln -sfn "$src" "$dst"
  echo "  linked: $dst -> $src"
done

echo
echo "Done. Skills are now available in any directory when running 'claude'."
echo "Verify with: ls -la ~/.claude/skills/"
