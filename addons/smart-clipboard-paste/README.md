# Smart Clipboard Paste

Save clipboard text or images as a new file in the currently open folder.
The addon uses Ferret's native Paste command, clipboard access, and dialogs.

## Features

- **Smart Paste:** Ctrl+V or Paste opens a save dialog for text and images.
  Copied or cut files continue through Ferret's normal paste operation.
- **Automatic suggestions:** timestamped filenames, with `.json` suggested
  for valid JSON and `.png` for images.
- **Text formats:** `.txt`, `.json`, `.md`, and `.log`.
- **Image formats:** `.png`, `.jpg`, and `.webp`.
- **Live filename updates:** choosing an extension updates the name
  immediately while keeping your custom basename.
- **No overwrites:** existing names get `_1`, `_2`, etc.
- **Automatic selection:** the newly saved file is selected in Ferret.
- **English and German UI.**

## Requirements

- A Ferret version supporting native addon paste handlers, typed clipboard
  access, and live forms.
- Python 3, declared in `addon.yaml`.
- Python Pillow for image conversion: `python3-pil` on Debian/Ubuntu/Mint,
  `python3-pillow` on Fedora, or `python-pillow` on Arch.

Ferret can check the declared Python executable dependency. Pillow is a
Python module and must be installed separately; the addon reports when it
is missing. Text works without Pillow. No external clipboard utilities are
required.

## Install

Install this folder through **Addons → Install Addon from Folder…**, or
install the addon ZIP. Choose **Addons → Reload Addons** after an update.

## Use

Press **Ctrl+V** in an explorer file list, or use Ferret's normal **Paste**
command. The native handler works with Ferret's configured Paste shortcut
and leaves text inputs such as the path bar and search box alone.

- **Copied or cut files:** Ferret's normal copy/move behavior and conflict
  handling are preserved. File lists take priority
  over accompanying text or images.
- **Text:** opens a filename dialog with `snippet_YYYYMMDD_HHMMSS.txt`, or
  `.json` if the content is valid JSON.
- **Images:** opens the same dialog with `clipboard_YYYYMMDD_HHMMSS.png`.
- **Unsupported/empty clipboard:** no file is written.

The separate context-menu and Addons-menu entry **Paste clipboard as file…**
is also available. It always saves in the current folder, regardless of the
selected item. If files were copied, it points you to the normal Paste
command instead.

## Live filename dialog

The name is initially selected without its extension. Choose `.txt`,
`.json`, `.md`, `.log`, or, for images, `.png`, `.jpg`, `.webp`.

Changing the extension updates the filename immediately; custom names and
additional dots are preserved. Typing in the filename does not trigger a
programmatic rewrite.
Enter saves and Esc cancels. Cancel never passes the raw clipboard to
another handler or creates a file.

The selected extension determines the saved format. JSON is formatted with
two spaces; other text formats preserve the original UTF-8 text, including
tabs, backslashes, CRLF, and trailing newlines. Images are exported by Ferret
as PNG and converted locally if needed. JPEG transparency is flattened on
white. Clipboard data is exported before the dialog opens, so subsequent
clipboard changes do not alter the file being saved. Temporary exports are
deleted after being read.

## Naming and error handling

Existing files, directories, and symlinks are never replaced. Name conflicts
append `_1`, `_2`, etc.; exclusive creation also protects concurrent saves.
After saving, Ferret refreshes the folder and selects the exact new file.

Names containing `< > : " / \ | ? *`, control characters, reserved names,
or trailing spaces/dots are rejected and the dialog reopens. Names are
limited to 240 UTF-8 bytes. Folder paths with `|` or newlines are rejected
before writing because Ferret's reveal protocol cannot represent them
unambiguously. Clipboard export failures, invalid JSON, conversion errors,
and filesystem errors are reported in Ferret.

All addon UI messages are in `translations/en.json` and
`translations/de.json`, with regional-language fallback.

API reference: [Ferret addon documentation](https://github.com/BonitoCat/Ferret-File-Explorer/blob/HEAD/_docs/ADDONS.md).
