#!/usr/bin/env python3
"""YouTube downloads through yt-dlp, with Ferret forms and live progress."""
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
PROGRESS = '__FERRET_DOWNLOAD__'
POSTPROCESS = '__FERRET_POSTPROCESS__'


def strings():
    language = os.environ.get('FE_LANGUAGE', 'en').split('-')[0]
    path = ROOT / 'translations' / f'{language}.json'
    if not path.is_file():
        path = ROOT / 'translations/en.json'
    return json.loads(path.read_text(encoding='utf-8'))


def clean(value):
    return ' '.join(str(value).split())


def emit(command, value=''):
    print(f'fe:{command}' + (f' {clean(value)}' if value != '' else ''), flush=True)


def youtube_url(value):
    if not value or any(character.isspace() or character == '|' for character in value):
        return False
    try:
        url = urlsplit(value)
        return (url.scheme in ('https', 'http') and not url.username and not url.password
                and url.port in (None, 80, 443)
                and url.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com',
                                     'music.youtube.com', 'youtu.be', 'www.youtu.be')
                and url.path not in ('', '/'))
    except ValueError:
        return False


def clipboard_url():
    commands = []
    if os.environ.get('WAYLAND_DISPLAY'):
        commands.append(['wl-paste', '--no-newline'])
    if os.environ.get('DISPLAY'):
        commands.extend([['xclip', '-selection', 'clipboard', '-o'],
                         ['xsel', '--clipboard', '--output']])
    for command in commands:
        if not shutil.which(command[0]):
            continue
        try:
            result = subprocess.run(command, capture_output=True, text=True,
                                    timeout=2, errors='replace')
            value = result.stdout.strip()
            if result.returncode == 0 and youtube_url(value):
                return value
        except (OSError, subprocess.TimeoutExpired):
            pass
    return ''


def program(name):
    # GUI apps may retain an older PATH after a user-local tool is installed.
    local = Path.home() / '.local/bin' / name
    if local.is_file() and os.access(local, os.X_OK):
        return str(local)
    return shutil.which(name)


def javascript_runtime():
    deno = program('deno')
    if deno:
        return ['--js-runtimes', f'deno:{deno}']
    node = program('node')
    if node:
        try:
            version = subprocess.run([node, '--version'], capture_output=True,
                                     text=True, timeout=3, check=True).stdout.strip()
            if int(version.lstrip('v').split('.')[0]) >= 22:
                return ['--js-runtimes', f'node:{node}']
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    return []


def options(url, target, mode, playlist):
    template = (PROGRESS + '{"downloaded":%(progress.downloaded_bytes|0)j,'
                '"total":%(progress.total_bytes,progress.total_bytes_estimate|0)j,'
                '"speed":%(progress.speed|0)j,"eta":%(progress.eta|0)j}')
    args = ['--ignore-config', '--no-simulate', '--newline', '--no-color', '--progress',
            '--progress-delta', '0.3', '--progress-template', 'download:' + template,
            '--progress-template', 'postprocess:' + POSTPROCESS + '%(progress.status)s',
            '--no-overwrites', '--continue', '--paths', str(target),
            '--output', '%(title).180B [%(id)s].%(ext)s']
    if playlist:
        args += ['--yes-playlist']
    else:
        args += ['--no-playlist', '--playlist-items', '1']
    if mode == 'mp3':
        args += ['--format', 'ba/b', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0']
    else:
        cap = {'best': '', '1080': '[height<=1080]', '720': '[height<=720]'}[mode]
        args += ['--format', f'bv*{cap}+ba/b{cap}', '--merge-output-format', 'mkv']
    return [*args, '--', url]


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else 0
    except (TypeError, ValueError):
        return 0


def report(line, text):
    if line.startswith(PROGRESS):
        try:
            data = json.loads(line[len(PROGRESS):])
            if not isinstance(data, dict):
                return
        except ValueError:
            return
        total = number(data.get('total'))
        if total:
            percentage = min(100, number(data.get('downloaded')) / total * 100)
            emit('progress', f'{percentage:.1f}/100')
        else:
            emit('progress', 'busy')
        emit('progress-text', text['DOWNLOADING'])
        speed, eta = number(data.get('speed')), number(data.get('eta'))
        emit('progress-status', f'{speed / 1048576:.1f} MiB/s · ETA {int(eta)} s')
    elif line.startswith(POSTPROCESS):
        emit('progress', 'busy')
        emit('progress-text', text['PROCESSING'])
        emit('progress-status')
    else:
        # Never let downloader output become arbitrary Ferret commands.
        print(line, file=sys.stderr, flush=True)
        if line.startswith('[download] Destination:') or line.startswith('[Merger]'):
            emit('progress-item', line)


class Cancelled(Exception):
    pass


def cancel(_signal, _frame):
    raise Cancelled()


def main():
    text = strings()
    target = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('FE_CURRENT_DIR', '.')).expanduser().resolve()
    if not target.is_dir():
        print(text['INVALID_FOLDER'], file=sys.stderr)
        return 1
    downloader = program('yt-dlp')
    if not downloader or not shutil.which('ffmpeg'):
        print(text['DEPENDENCIES'], file=sys.stderr)
        return 1
    try:
        help_result = subprocess.run([downloader, '--help'], capture_output=True,
                                     text=True, timeout=10, errors='replace')
        if help_result.returncode or '--js-runtimes' not in help_result.stdout:
            print(text['OUTDATED_DOWNLOADER'], file=sys.stderr)
            return 1
    except (OSError, subprocess.SubprocessError) as error:
        print(clean(error), file=sys.stderr)
        return 1
    runtime = javascript_runtime()
    if not runtime:
        print(text['JS_RUNTIME'], file=sys.stderr)
        return 1
    initial = sys.argv[2].strip() if len(sys.argv) > 2 else clipboard_url()
    if initial and not youtube_url(initial):
        print(text['INVALID_URL'], file=sys.stderr)
        return 1
    modes = [text[key] for key in ('BEST', 'VIDEO_1080', 'VIDEO_720', 'MP3')]
    emit('form', text['DOWNLOAD_YOUTUBE'])
    emit('field', f'url | text | {text["URL"]} | {initial}')
    emit('field', f'format | choice | {text["FORMAT"]} | ' + ','.join(modes))
    emit('field', f'playlist | bool | {text["PLAYLIST"]} | false')
    emit('form-show')
    answer = sys.stdin.readline()
    if not answer:
        emit('status', text['CANCELLED'])
        return 0
    fields = answer.rstrip('\r\n').split('\t')
    if len(fields) != 3 or fields[1] not in modes or fields[2] not in ('true', 'false'):
        print(text['INVALID_OPTIONS'], file=sys.stderr)
        return 1
    url = fields[0].strip()
    if not url:
        emit('status', text['CANCELLED'])
        return 0
    if not youtube_url(url):
        print(text['INVALID_URL'], file=sys.stderr)
        return 1
    mode = ('best', '1080', '720', 'mp3')[modes.index(fields[1])]
    command = [downloader, *runtime, *options(url, target, mode, fields[2] == 'true')]
    emit('progress-title', text['DOWNLOAD_YOUTUBE'])
    emit('progress', 'busy')
    emit('progress-text', text['PREPARING'])
    process = None
    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                                   bufsize=1, cwd=target)
        for line in process.stdout:
            report(line.rstrip('\r\n'), text)
        result = process.wait()
        if result:
            # Refresh partial outputs too; yt-dlp's final error stays on stderr.
            emit('refresh')
            return result if result > 0 else 1
        emit('refresh')
        emit('status', text['COMPLETE'])
        return 0
    except Cancelled:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        emit('refresh')
        emit('status', text['CANCELLED'])
        return 0
    except OSError as error:
        print(clean(error), file=sys.stderr)
        return 1
    finally:
        emit('progress', 'done')


if __name__ == '__main__':
    sys.exit(main())
