#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
tfwr_load_config
SRC="$TFWR_SAVE_DIR"
DST="$TFWR_REPO_SAVE_DIR"
tfwr_parse_args "$@"
tfwr_copy_files Import 1
