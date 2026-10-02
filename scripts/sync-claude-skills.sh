#!/usr/bin/env bash
set -euo pipefail

src="$HOME/.config/opencode/skills"
dst="$HOME/.claude/skills"

mkdir -p "$dst"

# Remove stale or broken symlinks that point into the opencode skills dir
# (retired skills, renamed dirs, broken targets). Real dirs like `synced` are untouched.
for link in "$dst"/*; do
    [ -L "$link" ] || continue
    target="$(readlink "$link")"
    case "$target" in
        "$src"/*)
            if [ ! -e "$target" ]; then
                rm -f "$link"
                echo "removed stale: $(basename "$link")"
            fi
            ;;
    esac
done

linked=0
skipped=0
for dir in "$src"/*/; do
    name="$(basename "$dir")"
    file="$dir/SKILL.md"
    [ -f "$file" ] || continue
    if ! head -1 "$file" | grep -q '^---' \
        || ! grep -q '^name:' "$file" \
        || ! grep -q '^description:' "$file"; then
        echo "skip (need '---', 'name:', 'description:' frontmatter): $name"
        skipped=$((skipped + 1))
        continue
    fi
    ln -sfn "$dir" "$dst/$name"
    linked=$((linked + 1))
done

echo "linked $linked skill(s), skipped $skipped"
