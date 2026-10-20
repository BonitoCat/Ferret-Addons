# Ferret-Addons

A public list of all officially verified addons for [Ferret](https://github.com/BonitoCat/Ferret-File-Explorer). Everything in this repository shows up in Ferret's built-in addon store (Addons → Browse Addon Store).

## Layout

```
addons/<id>/  one folder per addon, plain source files (reviewed before merging)
dist/         generated: one .zip per addon
icons/        generated: icons copied from the addons
index.yaml    generated: the list the addon store reads
owners.yaml   generated: who may change which addon
scripts/      build_index.py and owners.py, used by the GitHub Action
```

## Submitting an addon

1. Add your addon folder as `addons/<id>/`, with `addon.yaml` directly inside it. Don't zip it.
2. Your `addon.yaml` needs an `id` that matches the folder name (letters, digits, `.`, `_`, `-`) and a `version`. Optional store fields: `author`, `website`, `icon` (`.png`, `.svg`, `.jpg`), `donate`.
   `donate` only accepts links to Ko-fi, PayPal, Patreon, GitHub Sponsors, Buy Me a Coffee, Liberapay and Open Collective, in the forms listed in Ferret's [addon docs](https://github.com/BonitoCat/Ferret-File-Explorer/blob/main/_docs/ADDONS.md#donation-links). Pull requests with any other donation link fail the check.
3. Open a pull request. A reviewer will check your addons and accept it, if it meets the criteria.
4. Once it has been reviewed and merged, the Action builds the zip and updates the index. The addon appears in the store within a few minutes.

Whoever's pull request first adds an addon becomes its owner. After that, only the owner can change or delete it. Pull requests that change files outside `addons/<id>/`, or in an addon owned by someone else, are closed automatically.

To publish an update, change your files in a new pull request and raise `version` in `addon.yaml`. Ferret then offers the update to everyone who has the addon installed.
