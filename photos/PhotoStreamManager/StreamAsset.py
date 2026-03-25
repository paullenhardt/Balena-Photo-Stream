from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Self
from .CloudDownloadMixin import CloudDownloadMixin

class AssetType(Enum):
    NONE = 0
    PHOTO = 1
    VIDEO = 2


@dataclass
class StreamAsset(CloudDownloadMixin[Self]):
    id: str | None = None
    creation_date: datetime | None = None
    derivatives: dict[str, StreamAssetDerivative] = field(default_factory=dict)
    preferred_derivative: str | None = None
    type: AssetType = AssetType.PHOTO
    exif: dict[str, any] = field(default_factory=dict)
    _dirty: bool = False

@dataclass
class StreamAssetDownload:
    url_location: str | None = None
    url_path: str | None = None
    url_expiry: datetime | None = None
    file_name: str | None = None

@dataclass
class StreamAssetDerivative:
    hash: str | None = None
    width: int = 0
    height: int = 0
    file_size: int = 0
    downloaded: bool = False
    filepath: Path | None = None
    _dirty: bool = False
    download: StreamAssetDownload = field(default_factory=StreamAssetDownload)

