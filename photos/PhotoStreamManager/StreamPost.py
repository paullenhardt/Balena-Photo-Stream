from dataclasses import dataclass, field
from datetime import datetime
from .StreamAsset import *


@dataclass
class StreamPost:
    id: str | None = None
    asset_ids: list[str] = field(default_factory=list)
    _tmp_asset_ids: list[str] = field(default_factory=list)
    post_date: datetime | None = None
    caption: str | None = None
    contributor: str | None = None