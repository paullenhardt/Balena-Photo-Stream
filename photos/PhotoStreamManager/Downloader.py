from abc import ABC, abstractmethod
from pathlib import Path

class Downloader(ABC):
    @property
    @abstractmethod
    def share_url(self) -> str:
        pass

    @share_url.setter
    @abstractmethod
    def share_url(self, share_url: str) -> None:
        pass

    @property
    @abstractmethod
    def save_directory(self) -> Path:
        pass

    @save_directory.setter
    @abstractmethod
    def save_directory(self, save_directory: Path) -> None:
        pass

    @abstractmethod
    def download_photos(self) -> None:
        pass