#!/usr/bin/env bash
set -euo pipefail

usage() {
    printf 'Usage: %s SOURCE TARGET [--discard-empty]\n' "$0" >&2
}

if (( $# < 2 )); then
    usage
    exit 2
fi

readonly source="$1"
readonly target="$2"
shift 2

discard_empty_file=false

while (( $# > 0 )); do
    case "$1" in
        --discard-empty)
            discard_empty_file=true
            shift
            ;;
        *)
            printf 'Unknown argument: %s\n' "$1" >&2
            usage
            exit 2
            ;;
    esac
done

next_backup_path() {
    local base="${target}.backup-$(date +%Y%m%d-%H%M%S)"
    local candidate="$base"
    local suffix=1

    while [[ -e "$candidate" || -L "$candidate" ]]; do
        candidate="${base}-${suffix}"
        ((suffix += 1))
    done

    printf '%s\n' "$candidate"
}

if [[ ! -e "$source" ]]; then
    printf 'Source does not exist: %s\n' "$source" >&2
    exit 1
fi

if [[ -L "$target" && "$target" -ef "$source" ]]; then
    printf 'Already linked: %s -> %s\n' "$target" "$source"
    exit 0
fi

mkdir -p "$(dirname "$target")"

backup_path=""
if [[ -e "$target" || -L "$target" ]]; then
    if [[ "$discard_empty_file" == true && ! -L "$target" && -f "$target" && ! -s "$target" ]]; then
        rm "$target"
        printf 'Removed empty file: %s\n' "$target"
    else
        backup_path="$(next_backup_path)"
        mv "$target" "$backup_path"
        printf 'Backed up: %s -> %s\n' "$target" "$backup_path"
    fi
fi

if ! ln -s "$source" "$target"; then
    if [[ -n "$backup_path" ]]; then
        mv "$backup_path" "$target"
        printf 'Restored after link failure: %s\n' "$target" >&2
    fi
    exit 1
fi

printf 'Linked: %s -> %s\n' "$target" "$source"
