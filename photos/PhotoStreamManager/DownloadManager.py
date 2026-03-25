from .Downloader import Downloader
from threading import Thread, Event
from typing import Optional

class DownloadManager(Thread):
    def __init__(self, event: Event, delay: int=5 * 60) -> None:
        Thread.__init__(self)
        self.stopped = event
        self.delay = delay
        self.downloaders: list[Downloader] = []

    def run(self) -> None:
        # Start initially by downloading
        for downloader in self.downloaders:
            print("Starting downloading for {}".format(downloader.share_url))
            downloader.download_photos()

        # Wait to check again
        while not self.stopped.wait(self.delay):
            for downloader in self.downloaders:
                downloader.download_photos()

    def add_downloader(self, downloader: Optional[Downloader]=None) -> None:
        assert isinstance(downloader, Downloader)
        self.downloaders.append(downloader)
