#!/usr/bin/env bash
# Rejects commit and pull request commands that carry attribution trailers.
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
read_input
CMD="$(jget '.tool_input.command')"
[ -z "$CMD" ] && exit 0
printf '%s' "$CMD" | grep -Eiq -- '\bgit[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit\b|\bgh[[:space:]]+pr\b' || exit 0
printf '%s' "$CMD" | grep -Eiq -- 'co-authored-by|\bclaude\b|anthropic|generated with' && block "Attribution trailer found. Remove it; the owner is the sole author."
exit 0
