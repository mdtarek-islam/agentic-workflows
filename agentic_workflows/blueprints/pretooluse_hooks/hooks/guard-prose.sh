#!/usr/bin/env bash
# Blocks dashes, emoji and banned words in .md, .svg and .html writes.
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
read_input
FILE="$(jget '.tool_input.file_path')"
case "$FILE" in *.md|*.svg|*.html) ;; *) exit 0 ;; esac
TEXT="$(printf '%s' "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty' 2>/dev/null)"
[ -z "$TEXT" ] && exit 0
# Byte-level matching keeps the check independent of the locale.
printf '%s' "$TEXT" | LC_ALL=C grep -Pq '\xE2\x80[\x93\x94]' && block "Dash characters found. Use a comma, colon, full stop or the word 'to'."
printf '%s' "$TEXT" | LC_ALL=C grep -Pq '\xF0\x9F|\xE2[\x98-\x9E]' && block "Emoji found. Remove it."
WORDS='delve|leverage|tapestry|testament|seamless|seamlessly|cutting-edge|game-changer|unlock|unleash|elevate|foster|realm|paradigm|beacon|underscore|pivotal|meticulous|embark|symphony|robust'
HIT="$(printf '%s' "$TEXT" | grep -Eioh -- "(^|[^[:alnum:]_-])($WORDS)($|[^[:alnum:]_-])" | head -n1)"
[ -n "$HIT" ] && block "Banned word found: $(printf '%s' "$HIT" | tr -d '[:space:][:punct:]' ). Rewrite the sentence."
exit 0
