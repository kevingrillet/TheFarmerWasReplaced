#!/bin/bash
# Compares two folders (default: ./Save0 and game save folder) using git diff for .py files

DEFAULT_SRC="./Save0"
DEFAULT_DST="$HOME/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0"

usage() {
    echo "Usage: $0 [-s source_path] [-d dest_path]"
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
        *)
            usage
            ;;
    esac
done

SRC="${SRC:-$DEFAULT_SRC}"
DST="${DST:-$DEFAULT_DST}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "git is required for this script."
    exit 1
fi

# Compare .py files in both directories
echo "Comparing .py files between:"
echo "  $SRC"
echo "  $DST"
echo

git --no-pager diff --no-index "$SRC" "$DST" -- '*.py'