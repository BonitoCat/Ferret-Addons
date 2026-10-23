"""File naming, serialization, and race-safe conflict handling."""
from datetime import datetime
import io
import json
from pathlib import Path
import re


TEXT_EXTENSIONS = ('.txt', '.json', '.md', '.log')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.webp')
INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
RESERVED = re.compile(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', re.I)


class InvalidName(ValueError):
    pass


class InvalidJSON(ValueError):
    pass


def parse_json(text):
    def reject_constant(_value):
        raise ValueError('non-JSON numeric constant')
    return json.loads(text, parse_constant=reject_constant)


def suggestion(content, now=None):
    stamp = (now or datetime.now()).strftime('%Y%m%d_%H%M%S')
    if content.kind == 'image':
        return f'clipboard_{stamp}.png', IMAGE_EXTENSIONS, '.png'
    extension = '.txt'
    try:
        parse_json(content.data.decode('utf-8'))
        extension = '.json'
    except (ValueError, UnicodeError, RecursionError):
        pass
    return f'snippet_{stamp}{extension}', TEXT_EXTENSIONS, extension


def filename(value, extension):
    if not value or value != value.strip() or value in ('.', '..') or INVALID.search(value):
        raise InvalidName()
    if value.endswith(('.', ' ')) or RESERVED.match(value):
        raise InvalidName()
    # The extension dropdown determines the output format. Replace an existing
    # supported suffix, otherwise append the selected extension to the name.
    if Path(value).suffix.lower() in (*TEXT_EXTENSIONS, *IMAGE_EXTENSIONS, '.jpeg'):
        value = str(Path(value).with_suffix(extension))
    else:
        value += extension
    if len(value.encode('utf-8')) > 240:
        raise InvalidName()
    return value


def serialize(content, extension):
    if content.kind == 'text':
        if extension not in TEXT_EXTENSIONS:
            raise InvalidName()
        if extension == '.json':
            try:
                value = parse_json(content.data.decode('utf-8'))
                return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            except (ValueError, UnicodeError, RecursionError) as error:
                raise InvalidJSON() from error
        return content.data  # Preserve whitespace, CRLF, and final newlines.
    if extension not in IMAGE_EXTENSIONS:
        raise InvalidName()
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(content.data)) as source:
        source.load()
        image = ImageOps.exif_transpose(source)
        if extension == '.jpg':
            rgba = image.convert('RGBA')
            image = Image.new('RGB', rgba.size, 'white')
            image.paste(rgba, mask=rgba.getchannel('A'))
        elif extension == '.webp':
            image = image.convert('RGBA')
        elif image.mode not in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA', 'I', 'I;16'):
            image = image.convert('RGBA')
        output = io.BytesIO()
        image.save(output, format={'.png': 'PNG', '.jpg': 'JPEG', '.webp': 'WEBP'}[extension])
        return output.getvalue()


def save_unique(directory, name, data):
    directory = Path(directory)
    stem, suffix = Path(name).stem, Path(name).suffix
    counter = 0
    while True:
        candidate = directory / (name if counter == 0 else f'{stem}_{counter}{suffix}')
        try:
            handle = candidate.open('xb')  # Never replace files or follow symlinks.
        except FileExistsError:
            counter += 1
            continue
        try:
            with handle:
                handle.write(data)
                handle.flush()
            return candidate
        except BaseException:
            candidate.unlink(missing_ok=True)
            raise
