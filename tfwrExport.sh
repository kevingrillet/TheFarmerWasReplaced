#!/bin/bash

set -e

DEFAULT_SRC="./Save0"
DEFAULT_DST="$HOME/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0"
DRYRUN=0

usage() {
    echo "Usage: $0 [-s source_path] [-d dest_path] [--dryrun]"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--source)
            SRC="$2"
            shift 2
            ;;
        -d|--dest)
            DST="$2"
            shift 2
            ;;
        --dryrun)
            DRYRUN=1
            shift
            ;;
        *)
            usage
            ;;
    esac
done

SRC="${SRC:-$DEFAULT_SRC}"
DST="${DST:-$DEFAULT_DST}"

# Find .py files except __builtins__.py
PY_FILES=()
while IFS= read -r -d '' file; do
    [[ "$(basename "$file")" == "__builtins__.py" ]] && continue
    PY_FILES+=("$file")
done < <(find "$SRC" -maxdepth 1 -type f -name "*.py" -print0)

if [[ $DRYRUN -eq 1 ]]; then
    echo "Dryrun mode enabled. The following files would be copied from:"
    echo "  $SRC"
    echo "To:"
    echo "  $DST"
    for f in "${PY_FILES[@]}"; do
        echo "  $(basename "$f")"
    done
    exit 0
fi

# Create destination folder if needed
if [[ ! -d "$DST" ]]; then
    mkdir -p "$DST"
fi

# Copy .py files except __builtins__.py
for f in "${PY_FILES[@]}"; do
    cp "$f" "$DST/"
done

echo "Files copied to $DST:"
for f in "${PY_FILES[@]}"; do
    echo "  $(basename "$f")"
done