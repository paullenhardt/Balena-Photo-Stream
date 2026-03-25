from collections.abc import Callable
from typing import TypeVar, Generic
from pathlib import Path

T = TypeVar('T')

class CloudDownloadMixin(Generic[T]):
    def cloud_download(self, data_dir: Path | None = None):
        self._cloud_download(self, data_dir)

    def set_cloud_download_func(self, download_func: Callable[[T, Path | None], None]):
        self._cloud_download = download_func