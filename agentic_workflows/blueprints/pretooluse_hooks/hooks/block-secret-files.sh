#!/usr/bin/env bash
# Blocks .env files, keys and secrets folders. Example files stay readable.
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
read_input
TARGET="$(printf '%s' "$INPUT" | jq -r '[.tool_input.file_path, .tool_input.path, .tool_input.pattern, .tool_input.glob, .tool_input.command] | map(select(. != null)) | join("\n")' 2>/dev/null)"
[ -z "$TARGET" ] && exit 0
CLEAN="$(printf '%s' "$TARGET" | sed -E 's#[^[:space:]"/\\]*\.example##g')"
RE='(^|[/\\[:space:]"=])(\.env(\.[A-Za-z0-9_-]+)?|[^/\\[:space:]"]*\.(pem|key)|id_rsa[^/\\[:space:]"]*|id_ed25519[^/\\[:space:]"]*)($|[[:space:];|&"])|[/\\]secrets[/\\]'
printf '%s' "$CLEAN" | grep -Eiq -- "$RE" && block "Secret file access refused. Use the .example file."
exit 0
