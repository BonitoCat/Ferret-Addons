#!/usr/bin/env bash
set -u

case "${FE_LANGUAGE:-en}" in
    de|de-*)
        title='Git-Repository klonen'
        prompt='Repository-URL oder lokaler Repository-Pfad:'
        cancelled='Klonen abgebrochen.'
        missing_git='Git wurde nicht gefunden. Bitte installiere Git und versuche es erneut.'
        invalid_folder='Der Zielordner existiert nicht oder kann nicht geöffnet werden.'
        invalid_repository='Bitte gib eine Repository-URL oder einen lokalen Repository-Pfad ein.'
        success='Repository erfolgreich geklont.'
        cloning='Repository wird geklont…'
        ;;
    *)
        title='Clone Git Repository'
        prompt='Repository URL or local repository path:'
        cancelled='Clone cancelled.'
        missing_git='Git was not found. Install Git and try again.'
        invalid_folder='The target folder does not exist or cannot be opened.'
        invalid_repository='Enter a repository URL or a local repository path.'
        success='Repository cloned successfully.'
        cloning='Cloning repository…'
        ;;
esac

if ! command -v git >/dev/null 2>&1; then
    printf '%s\n' "$missing_git" >&2
    exit 1
fi

target="${1:-${FE_CURRENT_DIR:-}}"
if [[ -z "$target" ]] || ! cd -- "$target"; then
    printf '%s\n' "$invalid_folder" >&2
    exit 1
fi

repository="${2:-}"
if [[ -z "$repository" ]]; then
    # Clipboard tools are optional. Bound reads so an unavailable display or
    # clipboard owner cannot prevent Ferret from opening the input form.
    clipboard=''
    if command -v timeout >/dev/null 2>&1; then
        if [[ -n "${WAYLAND_DISPLAY:-}" ]] && command -v wl-paste >/dev/null 2>&1; then
            clipboard=$(timeout 2 wl-paste --no-newline 2>/dev/null) || clipboard=''
        fi
        if [[ -z "$clipboard" && -n "${DISPLAY:-}" ]]; then
            if command -v xclip >/dev/null 2>&1; then
                clipboard=$(timeout 2 xclip -selection clipboard -o 2>/dev/null) || clipboard=''
            elif command -v xsel >/dev/null 2>&1; then
                clipboard=$(timeout 2 xsel --clipboard --output 2>/dev/null) || clipboard=''
            fi
        fi
    fi
    clipboard="${clipboard#"${clipboard%%[![:space:]]*}"}"
    clipboard="${clipboard%"${clipboard##*[![:space:]]}"}"
    # Only a single GitHub repository link may become a default. This also
    # excludes form separators, tabs and line breaks from clipboard input.
    if [[ ! "$clipboard" =~ ^https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$ &&
          ! "$clipboard" =~ ^git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ &&
          ! "$clipboard" =~ ^ssh://git@github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$ ]]; then
        clipboard=''
    fi

    # A native one-field form provides an editable clipboard default.
    # Cancel closes stdin; an empty answer also cancels this operation.
    printf 'fe:form %s\nfe:field repository | text | %s | %s\nfe:form-show\n' "$title" "$prompt" "$clipboard"
    if ! IFS= read -r repository || [[ -z "$repository" ]]; then
        printf 'fe:status %s\n' "$cancelled"
        exit 0
    fi
fi

# Accept one literal repository, never shell code or extra git options.
if [[ "$repository" == -* || "$repository" == *$'\n'* || "$repository" == *$'\r'* || ! "$repository" =~ [^[:space:]] ]]; then
    printf '%s\n' "$invalid_repository" >&2
    exit 1
fi

printf 'fe:status %s\n' "$cloning"
printf 'fe:progress-title %s\nfe:progress busy\nfe:progress-text %s\n' "$title" "$cloning"
trap 'printf "fe:progress done\nfe:status %s\n" "$cancelled"; exit 0' TERM INT

# Ferret captures stdout as addon commands; keep all Git output on stderr.
# Credential helpers/askpass can still authenticate; fail instead of waiting
# for terminal input that does not exist in Ferret's background runner.
# Git updates progress with carriage returns. Convert these to lines, then
# show the percentage for the current stage (receiving, resolving, checkout).
# Flush each converted line immediately so quiet clones do not look stuck.
LC_ALL=C GIT_TERMINAL_PROMPT=0 git clone --progress -- "$repository" </dev/null 2>&1 |
    stdbuf -oL tr '\r' '\n' |
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -n "$line" ]] || continue
        printf '%s\n' "$line" >&2
        if [[ "$line" =~ ^(remote:\ )?([^:]+):[[:space:]]+([0-9]{1,3})% ]]; then
            percent=$((10#${BASH_REMATCH[3]}))
            if (( percent <= 100 )); then
                printf 'fe:progress %s/100 %s\n' "$percent" "$line"
            fi
        fi
    done
result=${PIPESTATUS[0]}
if (( result != 0 )); then
    printf 'fe:progress done\n'
    exit "$result"
fi

printf 'fe:progress 100/100\nfe:progress done\nfe:refresh\nfe:status %s\n' "$success"
