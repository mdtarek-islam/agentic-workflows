#!/usr/bin/env bash
# Refuses deletion commands. The agent must archive instead.
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
read_input
CMD="$(jget '.tool_input.command')"
[ -z "$CMD" ] && exit 0
RE='(^|[;&|][[:space:]]*|[[:space:]])(rm|rmdir|unlink)[[:space:]]|git[[:space:]]+(rm|clean)\b|git[[:space:]]+reset[[:space:]]+--hard|git[[:space:]]+branch[[:space:]]+-D\b'
printf '%s' "$CMD" | grep -Eq -- "$RE" && block "Deletion refused. Move the file to .dump/<repo>/<file>.<YYYYMMDD-HHMMSS>.bak instead."
exit 0
