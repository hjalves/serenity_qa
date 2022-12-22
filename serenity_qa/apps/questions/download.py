from pathlib import Path

import yt_dlp


def youtube_dl_download(
    url,
    download_dir=None,
    info=True,
    skip_download=False,
    progress_hooks=None,
    only_audio=False,
    live_chat=False,
    subtitles=False,
    logger=None
):
    download_dir = Path(download_dir or "./media/")
    out_template = str((download_dir / "%(id)s.%(ext)s").resolve())

    ydl_opts = {
        "outtmpl": out_template,
        "logger": logger,
        "writeinfojson": info,
        "skip_download": skip_download,
        "writesubtitles": True,
        "subtitleslangs": ["en"],
        "writeautomaticsub": subtitles,
        "addmetadata": True,
    }
    if progress_hooks:
        ydl_opts["progress_hooks"] = progress_hooks
    if live_chat:
        ydl_opts["subtitleslangs"] += ["live_chat"]
    if only_audio:
        ydl_opts = {
            **ydl_opts,
            # "format": "251/bestaudio/best"
            "format": "251",
            "postprocessors": [{"key": "FFmpegExtractAudio"}],
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([url])
