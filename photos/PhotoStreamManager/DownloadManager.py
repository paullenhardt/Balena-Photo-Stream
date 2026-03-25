from .Downloader import Downloader
from threading import Thread, Event
import time
from collections.abc import Callable
from queue import Queue, Empty
from .Stream import Stream
from .StreamAsset import *


class DownloadManager(Thread):
    def __init__(
        self,
        event: Event,
        delay: int = 60 * 60,
        download_path: Path = Path("/photos"),
        cloud_refresh: bool = True,
        asset_download: bool = False,
    ) -> None:
        Thread.__init__(self)
        self.stopped = event
        self.delay = delay
        self.download_path: Path = download_path
        self.cloud_refresh: bool = cloud_refresh
        self.asset_download: bool = asset_download
        self._streams: list[Stream] = []
        self._asset_queue: Queue[StreamAsset] = Queue()

    def add_stream(self, stream: Stream) -> None:
        self._streams.append(stream)

    def run(self) -> None:
        # Delay between all subsequent checks
        while not self.stopped.is_set():
            self._process_stream_updates() if self.cloud_refresh else ()
            self._persist_stream_changes()
            self._queue_assets_for_download() if self.asset_download else ()

            while not self._asset_queue.empty() and not self.stopped.is_set():
                try:
                    asset = self._asset_queue.get_nowait()
                except Empty as exp:
                    ...
                else:
                    # download asset
                    asset.cloud_download(data_dir=self.download_path)

                    # persist asset changes to storage
                    ...

            # Delay until the stopped flag is raised or until we hit the delay time
            self.stopped.wait(self.delay)

    def _process_stream_updates(self):
        for stream in self._streams:
            stream.cloud_update()
            # I do not like this... There should be an easier way to setup the calls
            for asset in stream.assets.values():
                asset.set_cloud_download_func(stream._cloud_download)

    def _persist_stream_changes(self):
        # Persist stream changes to storage
        ...

    def _queue_assets_for_download(self):
        # Find and add all assets from stream that need to be downloaded to queue
        for stream in self._streams:
            for asset in stream.assets.values():
                if (
                    asset.preferred_derivative
                    and asset.preferred_derivative in asset.derivatives
                ):
                    derivative = asset.derivatives[asset.preferred_derivative]
                    if not derivative.downloaded:
                        self._asset_queue.put(asset)
        ...
