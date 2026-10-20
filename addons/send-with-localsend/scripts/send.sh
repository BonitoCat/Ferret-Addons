#!/usr/bin/env bash
set -u

case "${FE_LANGUAGE:-en}" in
    de|de-*)
        no_selection='Wähle mindestens eine Datei oder einen Ordner aus.'
        invalid_path='Eine ausgewählte Datei oder ein Ordner ist nicht mehr verfügbar.'
        opening='Auswahl wird in LocalSend geöffnet…'
        not_installed='LocalSend wurde nicht gefunden. Installiere LocalSend oder die Flatpak-App org.localsend.localsend_app.'
        ;;
    *)
        no_selection='Select at least one file or folder.'
        invalid_path='A selected file or folder is no longer available.'
        opening='Opening selection in LocalSend…'
        not_installed='LocalSend was not found. Install LocalSend or the Flatpak app org.localsend.localsend_app.'
        ;;
esac

if (( $# == 0 )); then
    printf '%s\n' "$no_selection" >&2
    exit 1
fi

paths=()
for path in "$@"; do
    if [[ ! -f "$path" && ! -d "$path" ]]; then
        printf '%s\n' "$invalid_path" >&2
        exit 1
    fi
    # Absolute paths also protect names beginning with '-' or Flatpak's '@@'.
    if [[ "$path" != /* ]]; then
        path="$PWD/$path"
    fi
    paths+=("$path")
done

for launcher in localsend localsend_app; do
    if command -v "$launcher" >/dev/null 2>&1; then
        printf 'fe:status %s\n' "$opening"
        exec "$launcher" "${paths[@]}" >&2
    fi
done

if command -v flatpak >/dev/null 2>&1 && flatpak info org.localsend.localsend_app >/dev/null 2>&1; then
    printf 'fe:status %s\n' "$opening"
    # Forward paths, not file:// URIs: LocalSend expects filesystem paths.
    exec flatpak run --file-forwarding org.localsend.localsend_app @@ "${paths[@]}" @@ >&2
fi

printf '%s\n' "$not_installed" >&2
exit 1
