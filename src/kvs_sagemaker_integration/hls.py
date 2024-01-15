import os
from pathlib import Path, PurePath

import ffmpeg
import numpy as np

from logger import Logger

logger = Logger(__name__).get()


class Writer:
    def __init__(self, **kwargs):
        self._out_dir = str(kwargs.get('out_dir')) if kwargs.get('out_dir') else str(Path.home()) + "/desktop" if os.path.isdir(str(Path.home()) + '/desktop') else str(Path.home())
        self._fps = int(kwargs.get('fps')) if kwargs.get('fps') else 30
        self._width = int(kwargs.get('width')) if kwargs.get('width') else None
        self._height = int(kwargs.get('height')) if kwargs.get('height') else None
        self._hls_time = int(kwargs.get('hls_time')) if kwargs.get('hls_time') else 2
        self._hls_list_size = int(kwargs.get('hls_list_size')) if kwargs.get('hls_list_size') else 10
        self._fragment_counter = 0
        self._manifest = ""

    @property
    def out_dir(self):
        return self._out_dir

    @property
    def fps(self):
        return self._fps

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def hls_time(self):
        return self._hls_time

    @property
    def hls_list_size(self):
        return self._hls_list_size

    @property
    def manifest(self):
        return self._manifest

    def write_video(self, images: list[np.ndarray], **kwargs) -> PurePath:
        fps = kwargs.get("fps") or self._fps
        width = kwargs.get("width") or self._width
        height = kwargs.get("height") or self._height
        out_dir = kwargs.get("out_dir") or self._out_dir
        hls_time = kwargs.get("hls_time") or self._hls_time
        hls_list_size = kwargs.get("hls_list_size") or self._hls_list_size

        if not height:
            height, _, _ = images[-1].shape

        if not width:
            _, width, _ = images[-1].shape

        self._manifest = f"{out_dir}/manifest.m3u8"

        input_kwargs = dict(
            format='rawvideo',
            pix_fmt='rgb24',
            r=fps,
            s='{}x{}'.format(width, height),
            an=None
        )

        output_kwargs = dict(
            format='hls',
            hls_time=hls_time,
            hls_list_size=hls_list_size,
            hls_delete_threshold=hls_list_size,
            hls_segment_filename=f"{out_dir}/%03d.ts",
            hls_flags='append_list+omit_endlist+delete_segments',
            loglevel="error"
        )

        process = (
            ffmpeg
            .input('pipe:', **input_kwargs)
            .output(self._manifest, **output_kwargs)
            .run_async(pipe_stdin=True)
        )

        for frame in images:
            process.stdin.write(
                frame
                .astype(np.uint8)
                .tobytes()
            )
        process.stdin.close()

        process.wait()

        fname = str(self._fragment_counter).zfill(3) + '.ts'
        out_path = f"{out_dir}/{fname}"

        self._fragment_counter += 1

        return PurePath(out_path)
