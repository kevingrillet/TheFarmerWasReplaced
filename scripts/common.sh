#!/usr/bin/env bash
# Shared paths with %USERPROFILE% support. The .env file is never sourced.

tfwr_resolve_path() {
    local value="$1" base="${2:-$TFWR_REPO_ROOT}" profile="${USERPROFILE:-$HOME}"
    value="${value//%USERPROFILE%/"$profile"}"
    value="${value//\\//}"
    case "$value" in
        /*|[A-Za-z]:/*) ;;
        *) value="$base/$value" ;;
    esac
    if command -v cygpath > /dev/null 2>&1; then
        cygpath -u -- "$value"
    else
        printf '%s\n' "$value"
    fi
}

tfwr_load_config() {
    TFWR_REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
    local env_file line key value first last line_number=0
    env_file="$(tfwr_resolve_path "${TFWR_ENV_FILE:-$TFWR_REPO_ROOT/.env}")"
    if [[ -n ${TFWR_ENV_FILE:-} && ! -f "$env_file" ]]; then
        printf 'Configuration file not found: %s\n' "$env_file" >&2
        return 1
    fi
    if [[ -f "$env_file" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            line_number=$((line_number + 1))
            line="${line%$'\r'}"
            line="${line#"${line%%[![:space:]]*}"}"
            line="${line%"${line##*[![:space:]]}"}"
            [[ -z "$line" || "$line" == \#* ]] && continue
            if [[ ! "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
                printf 'Invalid assignment at %s:%s\n' "$env_file" "$line_number" >&2
                return 1
            fi
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            case "$key" in TFWR_GAME_DIR|TFWR_SAVE_DIR|TFWR_REPO_SAVE_DIR) ;; *) continue ;; esac
            first="${value:0:1}"
            last="${value: -1}"
            if [[ "$first" == \" || "$first" == "'" ]]; then
                if [[ ${#value} -lt 2 || "$last" != "$first" ]]; then
                    printf 'Unclosed quote at %s:%s\n' "$env_file" "$line_number" >&2
                    return 1
                fi
                value="${value:1:${#value}-2}"
            fi
            if [[ -z ${!key:-} ]]; then
                printf -v "$key" '%s' "$value"
            fi
        done < "$env_file"
    fi
    : "${TFWR_GAME_DIR:=C:/Program Files (x86)/Steam/steamapps/common/The Farmer Was Replaced}"
    : "${TFWR_SAVE_DIR:=${USERPROFILE:-$HOME}/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0}"
    : "${TFWR_REPO_SAVE_DIR:=Save0}"
    TFWR_GAME_DIR="$(tfwr_resolve_path "$TFWR_GAME_DIR")"
    TFWR_SAVE_DIR="$(tfwr_resolve_path "$TFWR_SAVE_DIR")"
    TFWR_REPO_SAVE_DIR="$(tfwr_resolve_path "$TFWR_REPO_SAVE_DIR")"
}

tfwr_usage() {
    printf 'Usage: %s [-s source_path] [-d dest_path] [--dryrun]\n' "$0"
}

tfwr_parse_args() {
    DRYRUN=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -s|--source|-d|--dest)
                if [[ $# -lt 2 || -z "$2" || "$2" == --* || "$2" == -s || "$2" == -d ]]; then
                    tfwr_usage >&2
                    return 2
                fi
                case "$1" in -s|--source) SRC="$2" ;; *) DST="$2" ;; esac
                shift 2
                ;;
            --dryrun) DRYRUN=1; shift ;;
            -h|--help) tfwr_usage; exit 0 ;;
            *) tfwr_usage >&2; return 2 ;;
        esac
    done
    SRC="$(tfwr_resolve_path "$SRC" "$PWD")"
    DST="$(tfwr_resolve_path "$DST" "$PWD")"
    if [[ ! -d "$SRC" ]]; then
        printf 'Source directory not found: %s\n' "$SRC" >&2
        return 1
    fi
    if [[ -d "$DST" && "$SRC" -ef "$DST" ]]; then
        printf 'Source and destination must be different directories.\n' >&2
        return 1
    fi
}

tfwr_copy_files() {
    local direction="$1" include_builtins="$2" file matching=0 answer
    local -a files=() candidates=()
    shopt -s nullglob
    candidates=("$SRC"/*.py)
    if [[ "$direction" == Import && -f "$SRC/save.json" ]]; then
        candidates+=("$SRC/save.json")
    fi
    for file in "${candidates[@]}"; do
        [[ -f "$file" ]] || continue
        [[ "$include_builtins" == 0 && "${file##*/}" == __builtins__.py ]] && continue
        files+=("$file")
        [[ -e "$DST/${file##*/}" ]] && matching=$((matching + 1))
    done
    printf '%s files from:\n  %s\nTo:\n  %s\n' "$direction" "$SRC" "$DST"
    if [[ ${#files[@]} -eq 0 ]]; then
        printf 'No files to copy.\n'
        return 0
    fi
    for file in "${files[@]}"; do printf '  %s\n' "${file##*/}"; done
    [[ "$DRYRUN" == 1 ]] && { printf 'Dry run: no files changed.\n'; return 0; }
    if [[ "$direction" == Import && "$matching" -gt 0 ]]; then
        read -r -p "Replace $matching existing files? Other files are kept. (y/N) " answer || answer=""
        answer="${answer%$'\r'}"
        if [[ ! "$answer" =~ ^[Yy]$ ]]; then
            printf 'Operation cancelled.\n'
            return 0
        fi
    fi
    mkdir -p -- "$DST"
    for file in "${files[@]}"; do cp -- "$file" "$DST/${file##*/}"; done
    printf 'Copied %s files.\n' "${#files[@]}"
}
