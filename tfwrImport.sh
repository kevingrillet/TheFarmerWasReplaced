#!/bin/bash

set -e

# Default values
DEFAULT_SRC="$HOME/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0"
DEFAULT_DST="./Save0"
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

# Find .py files safely (handles spaces)
mapfile -d '' PY_FILES < <(find "$SRC" -maxdepth 1 -type f -name "*.py" -print0)

if [[ $DRYRUN -eq 1 ]]; then
    echo "Dryrun mode enabled. The following files would be copied from:"
    echo "  $SRC"
    echo "To:"
    echo "  $DST"
    for f in "${PY_FILES[@]}"; do
        [[ -z "$f" ]] && continue
        echo "  $(basename "$f")"
    done
    exit 0
fi

# Create destination folder if needed
if [[ ! -d "$DST" ]]; then
    mkdir -p "$DST"
fi

# If destination folder is not empty, ask for confirmation to empty it
if [ "$(find "$DST" -mindepth 1 -print -quit 2>/dev/null)" ]; then
    read -r -p "The destination folder is not empty. Do you want to empty it? (y/N) " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf -- "${DST:?}"/*
    else
        echo "Operation cancelled."
        exit 1
    fi
fi

# Copy files
for f in "${PY_FILES[@]}"; do
    [[ -z "$f" ]] && continue
    cp -- "$f" "$DST/"
done

echo "Files copied to $DST:"
ls "$DST"