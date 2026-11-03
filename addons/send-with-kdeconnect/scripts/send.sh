#!/usr/bin/env bash
set -u

fail() {
    printf 'fe:message $%s\n' "$1"
    exit 1
}

(( $# > 0 )) || fail NO_SELECTION

paths=()
for path in "$@"; do
    [[ -f "$path" && -r "$path" ]] || fail INVALID_PATH
    # Absolute paths keep leading dashes from becoming CLI options.
    [[ "$path" == /* ]] || path="$PWD/$path"
    paths+=("$path")
done

command -v kdeconnect-cli >/dev/null 2>&1 || fail NOT_INSTALLED

# This mode lists only paired, reachable devices, without localized status text.
if ! devices=$(kdeconnect-cli --list-available --id-name-only); then
    fail DISCOVERY_FAILED
fi

ids=()
labels=()
while IFS= read -r device; do
    [[ -n "$device" ]] || continue
    id=${device%% *}
    # Device IDs become CLI arguments; reject malformed discovery output.
    [[ "$id" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_-]*$ && "$device" == *' '* ]] || fail DISCOVERY_FAILED
    name=${device#* }
    # Ferret's line-based choice protocol has no escape for pipes/newlines.
    # Numeric choice values keep device names separate from the selected ID.
    name=${name//|/∣}
    name=${name//$'\r'/ }
    ids+=("$id")
    labels+=("$name ($id)")
done <<< "$devices"

(( ${#ids[@]} > 0 )) || fail NO_DEVICES

selected=0
if (( ${#ids[@]} > 1 )); then
    printf 'fe:choose $CHOOSE_DEVICE'
    for i in "${!ids[@]}"; do
        printf ' | %s=%s' "$i" "${labels[$i]}"
    done
    printf '\n'
    IFS= read -r reply || exit 0
    selected=-1
    for i in "${!ids[@]}"; do
        if [[ "$reply" == "$i" ]]; then
            selected=$i
            break
        fi
    done
    (( selected >= 0 )) || fail INVALID_DEVICE
fi

printf 'fe:status $SENDING\n'
# Keep KDE output off stdout: only Ferret protocol commands belong there.
if ! kdeconnect-cli --device "${ids[$selected]}" --share "${paths[@]}" >&2; then
    fail SEND_FAILED
fi
printf 'fe:status $TRANSFER_REQUESTED\n'
