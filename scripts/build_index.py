#!/usr/bin/env python3
import argparse
import hashlib
import io
import json
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

INDEX_VERSION = 1
MANIFEST = "addon.yaml"
FALLBACK_LANGUAGE = "en"
TRANSLATION_DIRS = ("translations", "translation")
ICON_EXTENSIONS = (".png", ".svg", ".jpg", ".jpeg")
IGNORED_NAMES = {".DS_Store", "Thumbs.db", "__pycache__"}
MAX_ADDON_BYTES = 100 * 1024 * 1024
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
DONATION_NAME = r"[a-z0-9_.-]{1,64}"
DONATION_PROVIDERS = {
    "Ko-fi": [r"https://(www\.)?ko-fi\.com/[a-z0-9_]{1,64}/?"],
    "PayPal": [
        rf"https://(www\.)?paypal\.me/{DONATION_NAME}/?",
        rf"https://(www\.)?paypal\.com/paypalme/{DONATION_NAME}/?",
        r"https://(www\.)?paypal\.com/donate/?\?hosted_button_id=[a-z0-9]{1,32}",
    ],
    "Patreon": [r"https://(www\.)?patreon\.com/(c/)?[a-z0-9_-]{1,64}/?"],
    "GitHub Sponsors": [r"https://github\.com/sponsors/[a-z0-9-]{1,39}/?"],
    "Buy Me a Coffee": [rf"https://(www\.)?buymeacoffee\.com/{DONATION_NAME}/?"],
    "Liberapay": [rf"https://(www\.)?liberapay\.com/{DONATION_NAME}/?"],
    "Open Collective": [r"https://(www\.)?opencollective\.com/[a-z0-9-]{1,64}/?"],
}
DONATION_PATTERNS = [re.compile(p, re.IGNORECASE | re.ASCII) for patterns in DONATION_PROVIDERS.values() for p in patterns]


class AddonError(Exception):
    pass


def collect_files(folder):
    files = []
    total = 0
    for path in sorted(folder.rglob("*"), key=lambda p: p.relative_to(folder).as_posix()):
        relative = path.relative_to(folder)
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue

        if path.is_symlink():
            raise AddonError(f"symlinks are not allowed: {relative.as_posix()}")

        if not path.is_file():
            continue

        total += path.stat().st_size
        if total > MAX_ADDON_BYTES:
            raise AddonError(f"addon is larger than {MAX_ADDON_BYTES} bytes")

        files.append(path)

    return files


def build_zip(folder, files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(folder).as_posix(), ZIP_TIMESTAMP)
            executable = path.stat().st_mode & stat.S_IXUSR
            info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compresslevel=9)

    return buffer.getvalue()


def load_manifest(folder):
    manifest_path = folder / MANIFEST
    if not manifest_path.is_file():
        raise AddonError(f"{MANIFEST} is missing")

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8-sig")) or {}
    except (yaml.YAMLError, UnicodeDecodeError) as ex:
        raise AddonError(f"invalid {MANIFEST}: {ex}")

    if not isinstance(manifest, dict):
        raise AddonError(f"invalid {MANIFEST}: expected a mapping")

    return manifest


def load_translations(folder):
    translations = {}
    for directory in TRANSLATION_DIRS:
        for path in sorted((folder / directory).glob("*.json")):
            try:
                strings = json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError, UnicodeDecodeError) as ex:
                raise AddonError(f"invalid translation file {directory}/{path.name}: {ex}")

            if not isinstance(strings, dict):
                raise AddonError(f"invalid translation file {directory}/{path.name}: expected an object")

            translations.setdefault(path.stem, {}).update({k: v for k, v in strings.items() if isinstance(v, str) and v})

    return translations


def localize(value, translations):
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()
    if not value.startswith("$") or len(value) == 1:
        return {FALLBACK_LANGUAGE: value}

    key = value[1:]
    result = {}
    for language, strings in sorted(translations.items()):
        if key in strings:
            result[language] = strings[key]

    return result or {FALLBACK_LANGUAGE: value}


def find_icon(folder, icon):
    if not isinstance(icon, str) or not icon.strip():
        return None

    path = (folder / icon.strip()).resolve()
    if path.suffix.lower() not in ICON_EXTENSIONS or not path.is_file() or folder.resolve() not in path.parents:
        return None

    return path


def check_donations(value):
    if value is None:
        return

    links = value if isinstance(value, list) else [value]
    allowed = ", ".join(DONATION_PROVIDERS)
    for link in links:
        if not isinstance(link, str) or not link.strip().isascii() or not any(p.fullmatch(link.strip()) for p in DONATION_PATTERNS):
            raise AddonError(f"unsupported donation link '{link}' (allowed: links to {allowed})")


def write_if_changed(path, data):
    if path.exists() and path.read_bytes() == data:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def build_entry(folder, dist_dir, icons_dir):
    manifest = load_manifest(folder)

    addon_id = str(manifest.get("id") or "").strip()
    if not ID_PATTERN.match(addon_id) or addon_id in (".", ".."):
        raise AddonError(f"missing or invalid id '{addon_id}' (allowed: letters, digits, '.', '_', '-')")

    if addon_id != folder.name:
        raise AddonError(f"folder name must match the addon id '{addon_id}'")

    version = str(manifest.get("version") or "").strip()
    if not version:
        raise AddonError("missing version")

    check_donations(manifest.get("donate"))
    translations = load_translations(folder)
    data = build_zip(folder, collect_files(folder))
    write_if_changed(dist_dir / f"{addon_id}.zip", data)

    entry = {"id": addon_id, "version": version}
    for field in ("author", "website"):
        value = manifest.get(field)
        if isinstance(value, str) and value.strip():
            entry[field] = value.strip()

    icon = find_icon(folder, manifest.get("icon"))
    if icon is not None:
        icon_name = f"{addon_id}{icon.suffix.lower()}"
        write_if_changed(icons_dir / icon_name, icon.read_bytes())
        entry["icon"] = f"icons/{icon_name}"

    entry["download"] = f"dist/{addon_id}.zip"
    entry["sha256"] = hashlib.sha256(data).hexdigest()
    entry["size"] = len(data)
    entry["name"] = localize(manifest.get("name"), translations) or {FALLBACK_LANGUAGE: addon_id}

    description = localize(manifest.get("description"), translations)
    if description:
        entry["description"] = description

    return entry


def remove_stale(directory, ids):
    if not directory.exists():
        return

    for path in directory.iterdir():
        if path.is_file() and path.stem not in ids:
            path.unlink()


def build(repo, output, check):
    addons_dir = repo / "addons"
    dist_dir = output / "dist"
    icons_dir = output / "icons"

    entries = []
    errors = []
    for folder in sorted(p for p in addons_dir.iterdir() if p.is_dir() and p.name not in IGNORED_NAMES):
        try:
            entries.append(build_entry(folder, dist_dir, icons_dir))
        except (AddonError, OSError) as ex:
            errors.append(f"{folder.name}: {ex}")

    stray = sorted(p.name for p in addons_dir.iterdir() if p.is_file())
    for name in stray:
        errors.append(f"{name}: only addon folders belong in addons/, zips are built automatically")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)

        return 1

    if check:
        print(f"all {len(entries)} addons are valid")
        return 0

    ids = {entry["id"] for entry in entries}
    remove_stale(dist_dir, ids)
    remove_stale(icons_dir, ids)

    entries.sort(key=lambda e: e["id"].lower())
    content = yaml.safe_dump({"version": INDEX_VERSION, "addons": entries}, sort_keys=False, allow_unicode=True, width=1000)
    write_if_changed(output / "index.yaml", content.encode("utf-8"))

    print(f"wrote index.yaml with {len(entries)} addons")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Build the Ferret addon store: zips, icons and index.yaml")
    parser.add_argument("--repo", default=Path(__file__).resolve().parent.parent, type=Path)
    parser.add_argument("--check", action="store_true", help="only validate the addons, do not write anything")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / "addons").is_dir():
        print("error: addons/ folder not found", file=sys.stderr)
        return 1

    if args.check:
        with tempfile.TemporaryDirectory() as temp:
            return build(repo, Path(temp), True)

    return build(repo, repo, False)


if __name__ == "__main__":
    sys.exit(main())
