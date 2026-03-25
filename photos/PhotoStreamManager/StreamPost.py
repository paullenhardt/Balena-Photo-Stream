from dataclasses import dataclass, field
from datetime import datetime
from .StreamAsset import *


@dataclass
class StreamPost:
    id: str | None = None
    asset_ids: set[str] = field(default_factory=set)
    post_date: datetime | None = None
    caption: str | None = None
    contributor: str | None = None
    _dirty: bool = False