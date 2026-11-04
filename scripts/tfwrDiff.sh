#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
tfwr_load_config
SRC="$TFWR_REPO_SAVE_DIR"
DST="$TFWR_SAVE_DIR"
tfwr_parse_args "$@"
if [[ ! -d "$DST" ]]; then
    printf 'Destination directory not found: %s\n' "$DST" >&2
    exit 1
fi
command -v git > /dev/null || { printf 'git is required.\n' >&2; exit 1; }

printf 'Comparing .py files between:\n  %s\n  %s\n' "$SRC" "$DST"
declare -A seen=()
differences=0
shopt -s nullglob
for file in "$SRC"/*.py "$DST"/*.py; do
    [[ -f "$file" ]] || continue
    name="${file##*/}"
    [[ -n ${seen[$name]:-} ]] && continue
    seen["$name"]=1
    source_file="$SRC/$name"
    dest_file="$DST/$name"
    [[ -f "$source_file" ]] || source_file=/dev/null
    [[ -f "$dest_file" ]] || dest_file=/dev/null
    if git --no-pager diff --no-index -w --ignore-blank-lines -- "$source_file" "$dest_file"; then
        :
    else
        status=$?
        [[ "$status" -eq 1 ]] || exit "$status"
        differences=1
    fi
done
if [[ "$differences" == 0 ]]; then printf 'No differences in .py files.\n'; fi
# Differences are normal output for this interactive comparison task.
