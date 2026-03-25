from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

class AssetType(Enum):
    NONE = 0
    PHOTO = 1
    VIDEO = 2


@dataclass
class StreamAsset:
    id: str | None = None
    creation_date: datetime | None = None
    derivatives: dict[str, StreamAssetDerivative] = field(default_factory=dict)
    preferred_derivative: str | None = None
    type: AssetType = AssetType.PHOTO
    exif: dict[str, any] = field(default_factory=dict)

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
    file_type: str | None = None
    downloaded: bool = False
    filepath: Path | None = None
    download: StreamAssetDownload = field(default_factory=StreamAssetDownload)

