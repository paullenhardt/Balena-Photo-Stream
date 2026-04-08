import os
import threading
import time
import json
from pathlib import Path
import photo_env
from PhotoStreamManager.DownloadManager import DownloadManager
from PhotoStreamManager import Stream, iCloudSharedPhotoStream

def main():
    input_url = photo_env.shared_url
    gallery_urls = os.environ.get("PHOTO_GALLERY_URL", input_url)
    download_interval = int(os.environ.get("PHOTO_DOWNLOAD_INTERVAL", str(60 * 60)))
    stopFlag = threading.Event()
    if os.path.exists("/photos"):
        photo_path = Path("/photos")
    else:
        photo_path = Path("./images")
    download_manager = DownloadManager(stopFlag, download_interval, photo_path, cloud_refresh=True, asset_download=True)

    # This should happen within the Download Manager or Persistence Manager
    # Load stream(s) from storage or Config
    stream = Stream.Stream(id=photo_env.stream_id)
    iCloudSharedPhotoStream.init_stream_as_icloud(stream)

    download_manager.add_stream(stream)

    download_manager.start()
    try:
        while 1:
            time.sleep(10)
    except KeyboardInterrupt:
        stopFlag.set()
    
    # # This should happen within the Download Manager
    # # Load stream(s) from storage or Config
    # stream = Stream.Stream()
    # stream.id_from_url(photo_env.shared_url)
    # stream.set_cloud_update_func(iCloudSharedPhotoStream.update_from_cloud)
    
    # # Refresh stream from cloud
    # stream.cloud_update()

    # # Mixin the icloud functions
    # for asset in stream.assets.values():
    #     asset.set_cloud_download_func(iCloudSharedPhotoStream.download_asset)

    # stream.assets['98CC62EE-759E-4A25-A8EE-F678AFF3A275'].cloud_download()
    # Persist changes to DB
    # Queue Assets to be downloaded
        # On each download persist Asset info to DB (filepath)
    ...

if __name__ == "__main__":
    main()

    

