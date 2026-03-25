from enum import Enum
from collections.abc import Callable
from typing import Self
from dataclasses import dataclass, field
from .StreamPost import StreamPost
from .StreamAsset import StreamAsset
from .CloudUpdateMixin import CloudUpdateMixin
from .CloudDownloadMixin import CloudDownloadMixin

class StreamType(Enum):
    NONE = 0
    ICLOUD_SHARED_STREAM = 1

@dataclass
class Stream(CloudUpdateMixin[Self], CloudDownloadMixin[StreamAsset]):
    url: str | None = None
    # This may be unique to iphoto share streams
    id: str | None = None
    name: str | None = None
    owner: str | None = None
    type: StreamType = StreamType.ICLOUD_SHARED_STREAM
    posts: dict[str, StreamPost] = field(default_factory=dict)
    assets: dict[str, StreamAsset] = field(default_factory=dict)
    _dirty: bool = False

    def id_from_url(self, url:str):
        self.url = url
        self.id = url.split("#")[-1] if url and len(url.split("#")) == 2 else None
    