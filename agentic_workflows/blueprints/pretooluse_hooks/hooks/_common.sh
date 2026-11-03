#!/usr/bin/env bash
# Shared helpers. Needs jq. Contract: JSON on stdin, exit 0 allow, exit 2 block.
INPUT=""
read_input() { INPUT="$(cat)"; }
jget() { printf '%s' "$INPUT" | jq -r "$1 // empty" 2>/dev/null; }
has_match() { printf '%s' "$1" | grep -Eq ${3:+"$3"} -- "$2"; }
block() { echo "$1" >&2; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "jq is required" >&2; exit 0; }
