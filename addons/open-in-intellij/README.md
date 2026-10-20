# Open in IntelliJ IDEA

Adds **Open in IntelliJ IDEA** to Ferret's context menu for a single folder
and for empty space inside the current folder. Requires Linux, Bash, and
IntelliJ IDEA.

## Install and use

Choose **Addons → Install Addon from Folder…** and select this folder, or
install the addon ZIP through **Addons → Install Addon from Zip…**.

Right-click a folder and choose **Open in IntelliJ IDEA** to open that
folder as a project. Right-click empty space to open the current folder.
The entry is hidden for files and multiple selections.

The addon checks `idea`, `idea.sh`, `intellij-idea`,
`intellij-idea-ultimate`, and `intellij-idea-community` on your `PATH`, then
the default JetBrains Toolbox `scripts/idea` launcher and Snap launchers
under `/snap/bin`. For a standalone installation, expose its launcher as
`idea` on your `PATH`. Missing launchers are reported in Ferret's status bar.

English and German menu text are included. Folder paths with spaces are
passed as a single argument.

See [JetBrains' command-line launcher documentation](https://www.jetbrains.com/help/idea/working-with-the-ide-features-from-command-line.html).
