from .Downloader import Downloader
from threading import Thread, Event
import time
from collections.abc import Callable
from queue import Queue, Empty
from .Stream import Stream
from .StreamAsset import *
from .PersistenceManager import PersistenceManager


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
        self._streams: dict[str, Stream] = {}
        self._asset_queue: Queue[StreamAsset] = Queue()
        self._persistence_manager: PersistenceManager | None = None

    def add_stream(self, stream: Stream) -> None:
        if stream.id not in self._streams:
            self._streams[stream.id] = stream

    def run(self) -> None:
        # Create Persistence Manager on the run thread.
        self._persistence_manager = PersistenceManager()
        start = time.time()
        self._streams.update(self._persistence_manager.load_streams())
        stop = time.time()
        print(f'Loading from DB took {stop-start} seconds.')
        # Delay between all subsequent checks
        while not self.stopped.is_set():
            start = time.time()
            self._process_stream_updates() if self.cloud_refresh else ()
            stop = time.time()
            print(f'Loading stream updates took {stop-start} seconds.')

            start = time.time()
            self._persist_stream_changes()
            stop = time.time()
            print(f'Persisting stream changes took {stop-start} seconds.')

            start = time.time()
            self._queue_assets_for_download() if self.asset_download else ()
            stop = time.time()
            print(f'Queuing assets for download took {stop-start} seconds.')

            while not self._asset_queue.empty() and not self.stopped.is_set():
                try:
                    asset = self._asset_queue.get_nowait()
                except Empty as exp:
                    ...
                else:
                    # download asset
                    asset.cloud_download(data_dir=self.download_path)

                    # persist asset changes to storage
                    if asset._dirty:
                        self._persist_stream_changes()
                    ...

            # Delay until the stopped flag is raised or until we hit the delay time
            self.stopped.wait(self.delay)

    def _process_stream_updates(self):
        for stream in self._streams.values():
            stream.cloud_update()
            stream.update_asset_cloud_download_func()

    def _persist_stream_changes(self):
        # Persist stream changes to storage
        for stream in self._streams.values():
            self._persistence_manager.persist_stream(stream)
        ...

    def _queue_assets_for_download(self):
        # Find and add all assets from stream that need to be downloaded to queue
        for stream in self._streams.values():
            for asset in stream.assets.values():
                if (
                    asset.preferred_derivative
                    and asset.preferred_derivative in asset.derivatives
                ):
                    derivative = asset.derivatives[asset.preferred_derivative]
                    if not derivative.downloaded:
                        self._asset_queue.put(asset)
        ...
