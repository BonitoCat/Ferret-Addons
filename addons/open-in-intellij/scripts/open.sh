#!/usr/bin/env bash
set -u

case "${FE_LANGUAGE:-en}" in
    de|de-*)
        invalid_folder='Wähle einen vorhandenen Ordner aus.'
        opening='Ordner wird in IntelliJ IDEA geöffnet…'
        not_installed='IntelliJ IDEA wurde nicht gefunden. Installiere IntelliJ IDEA oder füge den idea-Launcher zum PATH hinzu.'
        ;;
    *)
        invalid_folder='Select an existing folder.'
        opening='Opening folder in IntelliJ IDEA…'
        not_installed='IntelliJ IDEA was not found. Install IntelliJ IDEA or add its idea launcher to PATH.'
        ;;
esac

target="${1:-${FE_CURRENT_DIR:-}}"
if (( $# > 1 )) || [[ -z "$target" || ! -d "$target" ]]; then
    printf '%s\n' "$invalid_folder" >&2
    exit 1
fi
if [[ "$target" != /* ]]; then
    target="$PWD/$target"
fi

# Cover standalone/Toolbox launchers and current/older Snap package names.
# Explicit Snap paths also work when Ferret's desktop PATH omits /snap/bin.
for launcher in idea idea.sh intellij-idea intellij-idea-ultimate intellij-idea-community \
    "${XDG_DATA_HOME:-$HOME/.local/share}/JetBrains/Toolbox/scripts/idea" \
    /snap/bin/intellij-idea /snap/bin/intellij-idea-ultimate /snap/bin/intellij-idea-community; do
    if command -v "$launcher" >/dev/null 2>&1; then
        printf 'fe:status %s\n' "$opening"
        exec "$launcher" "$target" >&2
    fi
done

printf '%s\n' "$not_installed" >&2
exit 1
