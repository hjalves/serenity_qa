import logging
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)


def my_hook(d):
    pass
    # print(d["status"])
    # print(d["downloaded_bytes"], d["total_bytes"])
    # logger.debug("hook: %s", d)
    # if d["status"] == "finished":
    #    print(d)


def youtube_dl_download(
    url,
    download_dir=None,
    info=True,
    skip_download=False,
    progress_hooks=None,
    only_audio=False,
):
    download_dir = Path(download_dir or "./media/")
    progress_hooks = progress_hooks or [my_hook]
    out_template = str((download_dir / "%(id)s.%(ext)s").resolve())
    ydl_opts = {
        "outtmpl": out_template,
        "logger": logger,
        "writeinfojson": info,
        "progress_hooks": progress_hooks,
        "skip_download": skip_download,
        "writeautomaticsub": True,
        "addmetadata": True,
    }
    if only_audio:
        ydl_opts = {
            **ydl_opts,
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio"}],
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([url])
