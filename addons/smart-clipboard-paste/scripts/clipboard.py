"""Read clipboard snapshots through Ferret's stdin/stdout addon protocol."""
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import tempfile


class ClipboardError(Exception):
    pass


@dataclass(frozen=True)
class Content:
    kind: str  # files, image, text, empty
    data: bytes = b''


def request(command):
    print('fe:' + command, flush=True)
    reply = sys.stdin.readline()
    if not reply:
        raise ClipboardError()
    return reply.rstrip('\r\n')


def snapshot():
    # Paste handlers receive the types captured by Ferret when Paste was
    # invoked. Menu actions query them explicitly using the same native API.
    types = os.environ.get('FE_CLIPBOARD')
    if types is None:
        types = request('clipboard-types')
    types = set(types.split())
    if 'files' in types:
        return Content('files')
    kind = 'image' if 'image' in types else 'text' if 'text' in types else 'empty'
    if kind == 'empty':
        return Content(kind)
    # Freeze the clipboard before showing the dialog. File-based exports
    # preserve exact text (including trailing newlines) and binary PNG data.
    try:
        with tempfile.TemporaryDirectory(prefix='smart-paste-', dir=os.environ.get('FE_TEMP_DIR')) as directory:
            path = Path(directory) / ('clipboard.png' if kind == 'image' else 'clipboard.txt')
            if request(f'clipboard-{kind} {path}') != 'yes':
                raise ClipboardError()
            data = path.read_bytes()
    except (OSError, ValueError) as error:
        raise ClipboardError() from error
    if kind == 'text':
        data.decode('utf-8')
    return Content(kind, data) if data else Content('empty')
