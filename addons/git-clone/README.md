# Git Clone

Clone repositories from Ferret's folder context menu and path bar.
Requires Linux, Bash, and Git on your `PATH`. The URL popup requires a Ferret
build with native addon input prompts (`fe:prompt`), introduced on the
`avalonia-upgrade` branch. No external dialog tool or terminal emulator is
required.

## Install

In Ferret, choose **Addons → Install Addon from Folder…** and select this
`git-clone` folder. Alternatively, copy it into the folder opened by
**Addons → Open Addons Folder**, then choose **Addons → Reload Addons**.

## Use

- Right-click empty space in a folder and choose **Clone Git Repository…**.
- Right-click a single folder to clone inside that folder.
- Press **Ctrl+L**, type `clone`, and press Enter to enter the repository URL
  in Ferret's native popup.
- Or type `clone https://github.com/BonitoCat/Ferret-File-Explorer.git` to
  start cloning directly into the folder currently open in Ferret. Selected
  items do not change this destination.

Ferret's status bar shows when cloning starts, completes, or fails. The
folder refreshes automatically on success. Cancel or submit an empty URL
dialog to stop before cloning. Git uses your existing credential helpers,
askpass tools, and SSH configuration. Repositories that require terminal
authentication must have credentials/SSH access configured beforehand.
Cloning runs in the background; no terminal window opens.

HTTPS URLs, SSH URLs such as `git@github.com:owner/repo.git`, and local
repository paths are supported. The entire text after `clone` is treated as
one literal repository URL/path, so paths containing spaces work without
quotes. Extra Git options and custom destination names are not accepted.
Git creates its usual repository-named subfolder and reports a failure if
that destination already contains files. After a failure or interruption,
inspect any partial clone before retrying. Refresh Ferret if the new folder
does not appear automatically.

The addon follows [Ferret's addon documentation on avalonia-upgrade](https://github.com/BonitoCat/Ferret-File-Explorer/blob/avalonia-upgrade/_docs/ADDONS.md).
English and German menu text and prompts are included.
