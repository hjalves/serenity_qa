import logging
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)


def my_hook(d):
    # print(d)
    # logger.debug("hook: %s", d)
    if d["status"] == "finished":
        print(d)


def youtube_dl_download(
    url, download_dir=None, info=True, skip_download=False, progress_hooks=None
):
    download_dir = Path(download_dir or "./media/")
    progress_hooks = progress_hooks or [my_hook]
    out_template = '%(id)s.%(ext)s'
    outtmpl = str((download_dir / out_template).resolve())
    ydl_opts = {
        "outtmpl": outtmpl,
        "logger": logger,
        "writeinfojson": info,
        "progress_hooks": progress_hooks,
        "skip_download": skip_download,
        "writeautomaticsub": True,
        "addmetadata": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([url])
