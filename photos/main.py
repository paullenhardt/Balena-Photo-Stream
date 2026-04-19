import os
import threading
import time
import json
from pathlib import Path
import photo_env
from PhotoStreamManager.DownloadManager import DownloadManager
from PhotoStreamManager.PersistenceManager import PersistenceManager
from PhotoStreamManager import Stream, iCloudSharedPhotoStream

def main():
    input_url = photo_env.shared_url
    gallery_urls = os.environ.get("PHOTO_GALLERY_URL", input_url)
    persistence_manager = PersistenceManager()
    for stream_id in photo_env.icloud_stream_ids:
        stream = Stream.Stream(id=stream_id)
        stream._dirty = True
        persistence_manager.persist_stream(stream=stream)

    download_interval = int(os.environ.get("PHOTO_DOWNLOAD_INTERVAL", str(60 * 60)))
    stopFlag = threading.Event()
    if os.path.exists("/photos"):
        photo_path = Path("/photos")
    else:
        photo_path = Path("./images")
    download_manager = DownloadManager(stopFlag, download_interval, photo_path, cloud_refresh=True, asset_download=True)

    # This should happen within the Download Manager or Persistence Manager
    # Load stream(s) from storage or Config
    # stream = Stream.Stream(id=photo_env.stream_id)
    # iCloudSharedPhotoStream.init_stream_as_icloud(stream)
    # download_manager.add_stream(stream)

    download_manager.start()
    try:
        while 1:
            time.sleep(10)
    except KeyboardInterrupt:
        stopFlag.set()
    ...

if __name__ == "__main__":
    main()

    

