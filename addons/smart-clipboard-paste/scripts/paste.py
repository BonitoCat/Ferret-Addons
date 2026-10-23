#!/usr/bin/env python3
"""Ferret native dialog frontend for Smart Clipboard Paste."""
import json
import os
from pathlib import Path
import sys

from clipboard import ClipboardError, snapshot
from storage import InvalidJSON, InvalidName, filename, save_unique, serialize, suggestion


ROOT = Path(__file__).resolve().parent.parent


def translations():
    language = os.environ.get('FE_LANGUAGE', 'en').replace('_', '-')
    values = {}
    for code in dict.fromkeys(('en', language.split('-')[0], language)):
        path = ROOT / 'translations' / f'{code}.json'
        if path.is_file():
            values.update(json.loads(path.read_text(encoding='utf-8')))
    return values


def emit(command, value=''):
    # Protocol arguments may contain spaces, but never newlines.
    print('fe:' + command + (' ' + str(value).replace('\r', ' ').replace('\n', ' ') if value else ''), flush=True)


def main():
    text = translations()
    paste_handler = '--paste-handler' in sys.argv[2:]
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('FE_CURRENT_DIR', '.'))
    # fe:reveal uses | as a path separator, so reject unrepresentable paths
    # before writing rather than selecting a different file by accident.
    directory = directory.resolve()
    if not directory.is_dir() or any(char in str(directory) for char in '|\r\n'):
        print(text['INVALID_DIRECTORY'], file=sys.stderr)
        return 1
    try:
        content = snapshot()
    except (ClipboardError, UnicodeError):
        print(text['CLIPBOARD_ERROR'], file=sys.stderr)
        return 1
    if content.kind == 'files':
        if paste_handler:
            emit('pass')
        else:
            emit('status', text['USE_NATIVE_PASTE'])
        return 0
    if content.kind == 'empty':
        emit('status', text['EMPTY_CLIPBOARD'])
        return 0
    if content.kind == 'image':
        try:
            import PIL.Image  # noqa: F401
        except ImportError:
            print(text['PILLOW_REQUIRED'], file=sys.stderr)
            return 1
    proposed, extensions, selected = suggestion(content)
    while True:
        emit('form', text['SAVE_CLIPBOARD'])
        emit('field', f'name | text | {text["FILENAME"]} | {proposed}')
        choices = ','.join(('*' if item == selected else '') + item for item in extensions)
        emit('field', f'extension | choice | {text["FILETYPE"]} | {choices}')
        emit('field-select', 'name | name')
        emit('form-show', 'live')
        while True:
            answer = sys.stdin.readline()
            if not answer:
                emit('status', text['CANCELLED'])
                return 0
            values = answer.rstrip('\r\n').split('\t')
            if values[0] == 'change' and len(values) == 4 and values[3] in extensions:
                if values[1] == 'extension' and values[2]:
                    try:
                        updated = filename(values[2], values[3])
                    except InvalidName:
                        # Never put | or other invalid input into field-set.
                        continue
                    emit('field-set', f'name | {updated}')
                continue
            if values[0] == 'submit' and len(values) == 3 and values[2] in extensions:
                fields = values[1:]
                break
            print(text['INVALID_REPLY'], file=sys.stderr)
            return 1
        entered, selected = fields
        try:
            name = filename(entered, selected)
            payload = serialize(content, selected)
        except InvalidName:
            emit('message', text['INVALID_FILENAME'])
            # Keep only a safe default in the next form's | delimited protocol.
            continue
        except InvalidJSON:
            proposed = entered
            emit('message', text['INVALID_JSON'])
            continue
        except (OSError, ValueError, ImportError) as error:
            print(text['CONVERSION_ERROR'].format(error=error), file=sys.stderr)
            return 1
        try:
            path = save_unique(directory, name, payload)
        except OSError as error:
            print(text['SAVE_ERROR'].format(error=error), file=sys.stderr)
            return 1
        emit('reveal', str(path))
        emit('status', text['SAVED'].format(name=path.name))
        return 0


if __name__ == '__main__':
    sys.exit(main())
