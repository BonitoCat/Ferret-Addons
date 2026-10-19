#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

OWNERS_FILE = "owners.yaml"
ADDONS_DIR = "addons"
API_URL = "https://api.github.com/"


def load_owners(repo):
    path = repo / OWNERS_FILE
    if not path.exists():
        return {}

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(addon_id): list(users or []) for addon_id, users in data.items()}


def save_owners(repo, owners):
    content = yaml.safe_dump(dict(sorted(owners.items(), key=lambda item: item[0].lower())), sort_keys=False, allow_unicode=True)
    path = repo / OWNERS_FILE
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return

    path.write_text(content, encoding="utf-8")


def owner_ids(owners, addon_id):
    return {int(owner["id"]) for owner in owners.get(addon_id, []) if isinstance(owner, dict) and "id" in owner}


def owner_names(owners, addon_id):
    return [str(owner.get("login", owner.get("id"))) if isinstance(owner, dict) else str(owner) for owner in owners.get(addon_id, [])]


def addon_of(path):
    parts = path.split("/")
    if len(parts) < 3 or parts[0] != ADDONS_DIR or not parts[1]:
        return None

    return parts[1]


def find_violations(repo, files, author_id):
    owners = load_owners(repo)
    paths = set()
    for file in files:
        paths.add(file["filename"])
        if file.get("previous_filename"):
            paths.add(file["previous_filename"])

    violations = []
    for path in sorted(paths):
        addon_id = addon_of(path)
        if addon_id is None:
            violations.append(f"`{path}` is outside of `{ADDONS_DIR}/<id>/`")
            continue

        if addon_id in owners and author_id not in owner_ids(owners, addon_id):
            violations.append(f"`{path}` belongs to `{addon_id}`, which is owned by {', '.join(owner_names(owners, addon_id))}")
            continue

        if addon_id not in owners and (repo / ADDONS_DIR / addon_id).exists():
            violations.append(f"`{path}` belongs to the existing addon `{addon_id}`")

    return violations


def check(args):
    if args.author_id == args.maintainer_id:
        print("pull request by the maintainer, ownership check skipped")
        return 0

    files = json.loads(Path(args.files).read_text(encoding="utf-8"))
    violations = find_violations(args.repo.resolve(), files, args.author_id)
    if not violations:
        print("all changed files belong to addons owned by the author")
        return 0

    lines = [
        "This pull request was closed automatically because it changes files you are not allowed to change.",
        "",
        f"Pull requests may only change files inside `{ADDONS_DIR}/<id>/`, and only for addons you own (or a new addon).",
        "",
    ]
    lines.extend(f"- {violation}" for violation in violations)
    report = "\n".join(lines) + "\n"

    print(report, file=sys.stderr)
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")

    return 1


def fetch_user(path):
    request = urllib.request.Request(API_URL + path, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(request, timeout=30) as response:
        user = json.load(response)
        return {"id": int(user["id"]), "login": str(user["login"])}


def refresh_owner(owner, cache):
    if not isinstance(owner, dict):
        return fetch_user("users/" + urllib.parse.quote(str(owner)))

    user_id = int(owner["id"])
    if user_id not in cache:
        try:
            cache[user_id] = fetch_user(f"user/{user_id}")
        except urllib.error.HTTPError as ex:
            if ex.code != 404:
                raise

            cache[user_id] = {"id": user_id, "login": str(owner.get("login", user_id))}

    return cache[user_id]


def refresh_owners(owners):
    cache = {}
    for addon_id, users in owners.items():
        refreshed = []
        for owner in users:
            user = refresh_owner(owner, cache)
            old_login = owner.get("login") if isinstance(owner, dict) else owner
            if old_login != user["login"]:
                print(f"owner of {addon_id}: {old_login} is now {user['login']}")

            refreshed.append(user)

        owners[addon_id] = refreshed


def update(args):
    repo = args.repo.resolve()
    owners = load_owners(repo)
    refresh_owners(owners)

    addons_dir = repo / ADDONS_DIR
    added = [p.name for p in sorted(addons_dir.iterdir()) if p.is_dir() and p.name not in owners] if addons_dir.exists() else []
    for addon_id in added:
        owners[addon_id] = [{"id": args.author_id, "login": args.author}]
        print(f"recorded {args.author} ({args.author_id}) as owner of {addon_id}")

    if owners:
        save_owners(repo, owners)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Addon ownership for the Ferret addon store")
    parser.add_argument("--repo", default=Path(__file__).resolve().parent.parent, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)

    check_parser = commands.add_parser("check", help="check that a pull request only changes addons its author owns")
    check_parser.add_argument("--files", required=True, help="JSON list of changed files from the GitHub API")
    check_parser.add_argument("--author-id", required=True, type=int)
    check_parser.add_argument("--maintainer-id", required=True, type=int)
    check_parser.add_argument("--report", help="write the violations as markdown to this file")

    update_parser = commands.add_parser("update", help="record the owner of newly added addons")
    update_parser.add_argument("--author", required=True, help="username, only stored as a readable label")
    update_parser.add_argument("--author-id", required=True, type=int)

    args = parser.parse_args()
    return check(args) if args.command == "check" else update(args)


if __name__ == "__main__":
    sys.exit(main())
