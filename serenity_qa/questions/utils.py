import datetime
import tempfile
from pathlib import Path

import ffmpeg
from django.core.cache import cache


def serializer_format_to_mimetype(format):
    mimetypes = {
        "json": "application/json",
        "jsonl": "application/jsonlines",
        "xml": "application/xml",
        "yaml": "text/yaml",
        "kdl": "text/kdl",
    }
    return mimetypes.get(format, "text/plain")


def trim_audio_file(input_file, start_second, duration, output_file=None):
    if not output_file:
        output_file = tempfile.mktemp(suffix=".opus")
    stream = ffmpeg.input(input_file, ss=start_second, t=duration)
    output = stream.output(output_file, acodec="copy")
    ffmpeg.overwrite_output(output).run()
    return Path(output_file)


def get_or_set_tag_colors_version(force_set=False):
    cache_func = cache.set if force_set else cache.get_or_set
    default_value = datetime.datetime.utcnow().strftime("%y%m%d%H%M%S")
    value = cache_func("tag-colors-version", default_value, timeout=None)
    return default_value if force_set else value
