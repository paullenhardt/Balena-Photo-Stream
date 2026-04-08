from enum import Enum
from collections.abc import Callable
from typing import Self
from dataclasses import dataclass, field
from pathlib import Path
from .StreamPost import StreamPost
from .StreamAsset import StreamAsset

class StreamType(Enum):
    NONE = 0
    ICLOUD_SHARED_STREAM = 1

@dataclass
class Stream:
    url: str | None = None
    # This may be unique to iphoto share streams
    id: str | None = None
    name: str | None = None
    owner: str | None = None
    enabled: bool = True
    type: StreamType = StreamType.ICLOUD_SHARED_STREAM
    posts: dict[str, StreamPost] = field(default_factory=dict)
    assets: dict[str, StreamAsset] = field(default_factory=dict)
    _dirty: bool = False
    _cloud_update: Callable[[Self], None] | None = None
    _cloud_download: Callable[[StreamAsset, Path], None] | None = None

    def cloud_update(self):
        if self._cloud_update:
            self._cloud_update(self)

    def set_cloud_update_func(self, update_func: Callable[[Self], None]):
        self._cloud_update = update_func

    def set_cloud_download_func(self, download_func: Callable[[StreamAsset, Path | None], None]):
        self._cloud_download = download_func

    def update_asset_cloud_download_func(self):
        if not self._cloud_download:
            return
        for asset in self.assets.values():
            asset.set_cloud_download_func(self._cloud_download)
    