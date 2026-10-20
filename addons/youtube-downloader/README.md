# YouTube Downloader

Download YouTube videos or audio into a folder using Ferret's native forms,
progress bars, and Cancel button. English and German are included.

## Requirements

- Linux, Python 3, and a Ferret build supporting addon forms and progress
  bars (introduced on `avalonia-upgrade`).
- A current [yt-dlp](https://github.com/yt-dlp/yt-dlp#installation) and
  FFmpeg available on `PATH`. YouTube changes often; old distribution
  packages of yt-dlp may fail. Follow yt-dlp's installation/update guidance.
- Deno (recommended) or Node.js 22 or newer for YouTube's JavaScript
  challenges. The addon explicitly enables the detected runtime. Use an
  official yt-dlp executable (includes the EJS solver scripts) or install
  `yt-dlp[default]` through the official Python instructions.
- Clipboard prefill optionally uses `wl-paste` on Wayland or `xclip`/`xsel`
  on X11. Missing tools do not prevent downloads.

The manifest declares Python 3, yt-dlp, FFmpeg, FFprobe, and Deno using
Ferret's `dependencies` field. Ferret can offer to install missing system
packages. Deno has no universal package mapping and is shown for manual
installation when missing. Deno is the declared runtime; the script also
supports Node.js 22+ as an alternative, although Ferret will still list
Deno as missing on a Node-only setup. Clipboard tools remain optional.
Ferret checks command presence, so runtime checks still verify yt-dlp
support and JavaScript runtime availability.

The addon prefers tools in `~/.local/bin` over `PATH`, so desktop Ferret
sessions do not accidentally keep using an older system yt-dlp. It detects
old downloader versions before starting a download and explains missing
JavaScript runtimes. See [yt-dlp's YouTube runtime setup](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

## Install and use

Choose **Addons → Install Addon from Folder…** and select this folder, or
install the addon ZIP through **Addons → Install Addon from Zip…**.

- Right-click a folder or empty folder space → **Download from YouTube…**.
- Use the **Addons** menu to download into the current folder.
- Enter `youtube`, `yt`, or `youtube <URL>` in the path bar.

The form lets you edit the URL, choose best video/1080p/720p/MP3, and enable
playlists. A YouTube link in the clipboard prefills the URL. An explicit
path-bar URL takes precedence. Confirm the form before any download starts.

Playlists are off by default. A video link with a playlist parameter
downloads just that video; a playlist-only link downloads its first entry.
Enable **Download entire playlist** to download all entries. Video quality
is limited to what the source offers. Merging separate video/audio streams
uses MKV; existing combined streams retain their source container. MP3 mode
extracts and converts the audio with FFmpeg.

Progress is per stream/video, so it can restart for audio or the next
playlist item. Unknown totals and merging/conversion show an activity bar.
Cancel stops the operation. Partial files remain and can resume when you
retry with the same URL/options. Existing downloads are not overwritten.
The folder refreshes after completion, failure, or cancellation.

Downloads are named with the video title and ID. The addon ignores yt-dlp
configuration files so unrelated local flags do not change its behavior.
Downloader errors appear in Ferret's status bar and addon logs. This addon
does not configure browser cookies, account login, or DRM decryption.

The implementation uses [yt-dlp's documented options](https://github.com/yt-dlp/yt-dlp#usage-and-options)
and [Ferret's addon APIs](https://github.com/BonitoCat/Ferret-File-Explorer/blob/avalonia-upgrade/_docs/ADDONS.md).
