from .Downloader import Downloader
from pathlib import Path
from PIL import Image
import requests
import datetime
import json
import re
import io
import os

class SharedPhotoStreamDownloader(Downloader):
    api_url_format = "https://p23-sharedstreams.icloud.com/{}/sharedstreams"

    def __init__(self, share_url: str="", save_directory: Path=Path("./images")) -> None:
        super().__init__()
        self._share_url = "" 
        self.share_url = share_url
        self._save_directory = Path()
        self.save_directory = save_directory
        url_parts = share_url.split("#")
        if len(url_parts) == 2:
            self.album_guid = share_url.split("#")[1]
        else:
            raise ValueError
        # end if
        self.base_url = self.api_url_format.format(self.album_guid)
        self.photo_urls = dict()
        self.stream = dict()
        self.existing_files = dict()
        pass

    @property
    def share_url(self) -> str:
        return self.share_url

    @share_url.setter
    def share_url(self, share_url: str) -> None:
        assert(isinstance(share_url, str))
        self._share_url = share_url

    @property
    def save_directory(self) -> Path:
        return self._save_directory

    @save_directory.setter
    def save_directory(self, save_directory: Path) -> None:
        assert(isinstance(save_directory, Path))
        self._save_directory = save_directory

    def download_photos(self) -> None:
        self.get_directory_info()
        self.get_stream_meta_data()

        photo_dict = dict()

        for photo in self.stream.get("photos", []):
            # If the mediaAssetType is video, we can grab the "PosterFrame" derivative 
            # (and maybe overlay a "video camera" icon to indicate it is a video poster?)
            if photo.get("mediaAssetType", "").lower() != "video":
                derivatives = photo.get("derivatives", dict())
                max_file_size = 0
                checksum = ""
                for derivative in derivatives.values():
                    file_size = int(derivative.get("fileSize", "0"))
                    if file_size > max_file_size:
                        max_file_size = file_size
                        checksum = derivative.get("checksum", "")
                    # end if
                # end for
                created_date = datetime.datetime.strptime(
                    photo.get("batchDateCreated", ""), "%Y-%m-%dT%H:%M:%SZ"
                )
                photo_dict[checksum] = {
                    "date": created_date,
                    "checksum": checksum,
                    "fileSize": max_file_size,
                    "caption": photo.get("caption", ""),
                    "height": int(photo.get("height", "0")),
                    "width": int(photo.get("width", "0")),
                }
                pass
            # end if
            pass
        # end for

        # Order photos by newest created date
        photo_list = sorted(
            [x for x in photo_dict.values()], key=lambda d: d["date"], reverse=True
        )

        # Download photos that aren't already downloaded
        for photo in photo_list:
            if not photo.get("checksum", "") in self.existing_files:
                print("Trying to download {}".format(photo))
                self.get_photo(photo)
            # end if
        # end for

    def get_stream_meta_data(self):
        response = requests.post(
            self.base_url + "/webstream",
            data='{"streamCtag":null}',
            headers={"Content-Type": "application/json"},
        )
        # Handle Redirects to different servers.
        if 300 <= response.status_code < 400:
            host = response.json().get("X-Apple-MMe-Host", None)
            if host:
                self.base_url = "https://{}/{}/sharedstreams".format(
                    host, self.album_guid
                )
            # end if
        # end if
        response = requests.post(
            self.base_url + "/webstream",
            data='{"streamCtag":null}',
            headers={"Content-Type": "application/json"},
        )
        stream = response.json()
        photo_guids = {
            "photoGuids": [x.get("photoGuid", "0") for x in stream.get("photos", [])]
        }
        photo_guids_json = json.dumps(photo_guids)
        response = requests.post(
            self.base_url + "/webasseturls",
            data=photo_guids_json,
            headers={"Content-Type": "application/json"},
        )
        self.photo_urls = response.json()
        self.stream = stream
        pass

    def get_photo(self, photo):
        chcksum = photo["checksum"]
        item = self.photo_urls["items"][chcksum]
        ext = re.search(r"/[\w_\-\+\%\.]+\.(\w+)\?", item["url_path"])
        url = "https://{}{}&{}".format(item["url_location"], item["url_path"], chcksum)
        print("Downloading from: {}".format(url))
        photo_req = requests.get(url)
        if photo_req.status_code == 200:
            byte_file = io.BytesIO(photo_req.content)
            im = Image.open(byte_file)
            max_size = 800
            height, width = im.size
            if max(height, width) % 2 > 0:
                size = min(max(height, width) - 1, max_size)
            else:
                size = max_size
            size = size, size
            im.thumbnail(size)
            im.save(
                os.path.join(self.save_directory, "{}.{}".format(chcksum, ext.group(1)))
            )
            # with open(os.path.join(self.save_directory, '{}.{}'.format(chcksum, ext.group(1))), 'wb') as fid:
            #     fid.write(photo_req.content)
            # end with
        # end if
        pass

    def get_directory_info(self):
        file_list = dict()
        for dir_path, dir_names, file_names in os.walk(self.save_directory):
            for file_name in file_names:
                name, ext = os.path.splitext(file_name)
                if ext.lower() == ".jpg" or ext.lower() == ".mp4":
                    file_list[name] = os.path.join(dir_path, file_name)
                # end if
            # end for
        # end for
        self.existing_files = file_list
        pass
