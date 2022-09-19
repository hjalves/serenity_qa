import tempfile
from pathlib import Path

import ffmpeg


def trim_audio_file(input_file, start_second, duration, output_file=None):
    if not output_file:
        output_file = tempfile.mktemp(suffix='.opus')
    stream = ffmpeg.input(input_file, ss=start_second, t=duration)
    output = stream.output(output_file, acodec='copy')
    ffmpeg.overwrite_output(output).run()
    return Path(output_file)
