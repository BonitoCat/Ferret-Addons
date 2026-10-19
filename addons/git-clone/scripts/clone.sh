#!/usr/bin/env bash
set -u

case "${FE_LANGUAGE:-en}" in
    de|de-*)
        prompt='Repository-URL oder lokaler Repository-Pfad:'
        cancelled='Klonen abgebrochen.'
        missing_git='Git wurde nicht gefunden. Bitte installiere Git und versuche es erneut.'
        invalid_folder='Der Zielordner existiert nicht oder kann nicht geöffnet werden.'
        invalid_repository='Bitte gib eine Repository-URL oder einen lokalen Repository-Pfad ein.'
        success='Repository erfolgreich geklont.'
        cloning='Repository wird geklont…'
        ;;
    *)
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
    # Ferret opens its native input dialog and replies on stdin.
    # Cancel closes stdin; an empty answer also cancels this operation.
    printf 'fe:prompt %s\n' "$prompt"
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
# Ferret captures stdout as addon commands; keep all Git output on stderr.
# Credential helpers/askpass can still authenticate; fail instead of waiting
# for terminal input that does not exist in Ferret's background runner.
GIT_TERMINAL_PROMPT=0 git clone -- "$repository" </dev/null >&2
result=$?
if (( result != 0 )); then
    exit "$result"
fi

printf 'fe:refresh\nfe:status %s\n' "$success"
