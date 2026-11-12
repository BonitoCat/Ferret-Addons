# Send with KDE Connect

Adds **Send with KDE Connect** (**Mit KDE Connect versenden** in German) to
Ferret's file context menu, including multiple selections.

## Requirements

Linux, Bash, and KDE Connect with `kdeconnect-cli` on your `PATH`. Pair your
receiving device in KDE Connect first, enable its sharing plugin, and make
sure it is reachable.

## Install and use

Choose **Addons → Install Addon from Folder…** and select this folder, or
install a packaged ZIP through **Addons → Install Addon from Zip…**.

Select one or more files, right-click, and choose **Send with KDE Connect**.
If one paired device is reachable, the addon requests a transfer to it
immediately. If several devices are available, Ferret asks you to choose one;
Cancel sends nothing. Device IDs are displayed alongside names to distinguish
devices with the same name. No device name or ID is hard-coded.

The context-menu title is fixed: Ferret's addon format does not support
generating menu entries or titles from discovered devices. The device picker
provides the recipient selection from the screenshot when needed.

Only readable regular files are accepted. Archive folders before sending.
Paths with spaces, quotes, Unicode, and leading dashes remain separate arguments.
KDE Connect owns the asynchronous transfer: the addon's final status means the
request was submitted, not that the recipient has received the files. Check
KDE Connect for progress or delivery errors.

The integration uses KDE Connect's [`--list-available --id-name-only` and
`--device … --share …` CLI options](https://invent.kde.org/network/kdeconnect-kde/-/blob/master/cli/kdeconnect-cli.cpp)
and [Ferret's addon protocol](https://github.com/BonitoCat/Ferret-File-Explorer/blob/avalonia-upgrade/_docs/ADDONS.md).
