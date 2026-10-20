# Send with LocalSend

Adds **Send with LocalSend** to Ferret's context menu for files and folders,
including multiple selections and mixed file/folder selections.

## Requirements

Linux, Bash, and the LocalSend desktop app. The addon detects `localsend` or
`localsend_app` on your `PATH`, then the Flatpak app
`org.localsend.localsend_app`. AppImage installations must expose a launcher
named `localsend` or `localsend_app` on your `PATH`.

## Install and use

Choose **Addons → Install Addon from Folder…** and select this folder, or
install the addon ZIP through **Addons → Install Addon from Zip…**.

Select files and/or folders, right-click, and choose **Send with LocalSend**.
LocalSend opens with your selection on its Send screen. Choose the receiving
device there to start the transfer. The addon does not choose a recipient or
send automatically. A running LocalSend instance can receive the selection.

Folders are collected recursively by LocalSend. Empty folders are not
transferred. Flatpak selections use filesystem path forwarding so filenames
with spaces and special characters remain intact. LocalSend's existing
Flatpak permissions still determine which files it can read.

Missing LocalSend installations and unavailable selected paths are reported
in Ferret's status bar. English and German menu text are included.

The integration follows [LocalSend's file and directory argument handling](https://github.com/localsend/localsend/blob/v1.18.2/app/lib/provider/selection/selected_sending_files_provider.dart)
and [Ferret's addon format](https://github.com/BonitoCat/Ferret-File-Explorer/blob/avalonia-upgrade/_docs/ADDONS.md).
