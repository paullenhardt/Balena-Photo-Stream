import os
import requests
import json
import datetime
import re
import threading
import time
from PIL import Image
import io


class DownloadManager(threading.Thread):
    def __init__(self, event, delay=5 * 60):
        threading.Thread.__init__(self)
        self.stopped = event
        self.delay = delay
        self.downloaders = []

    def run(self):
        # Start initially by downloading
        for downloader in self.downloaders:
            print('Starting downloading for {}'.format(downloader.share_url))
            downloader.download_photos()

        # Wait to check again
        while not self.stopped.wait(self.delay):
            for downloader in self.downloaders:
                downloader.download_photos()

    def add_downloader(self, downloader=None):
        assert isinstance(downloader, Downloader)
        self.downloaders.append(downloader)


class Downloader(object):
    api_url_format = "https://p23-sharedstreams.icloud.com/{}/sharedstreams"

    def __init__(self, share_url='', save_directory='./images'):
        self.share_url = share_url
        self.save_directory = save_directory
        url_parts = share_url.split('#')
        if len(url_parts) == 2:
            self.album_guid = share_url.split('#')[1]
        else:
            raise ValueError
        # end if
        self.base_url = self.api_url_format.format(self.album_guid)
        self.photo_urls = dict()
        self.stream = dict()
        self.existing_files = dict()
        pass

    def download_photos(self):
        self.get_directory_info()
        self.get_stream_meta_data()

        photo_dict = dict()

        for photo in self.stream.get('photos', []):
            if photo.get('mediaAssetType', '').lower() != 'video':
                derivatives = photo.get('derivatives', dict())
                max_file_size = 0
                checksum = ''
                for derivative in derivatives.values():
                    file_size = int(derivative.get('fileSize', '0'))
                    if file_size > max_file_size:
                        max_file_size = file_size
                        checksum = derivative.get('checksum', '')
                    # end if
                # end for
                created_date = datetime.datetime.strptime(photo.get('batchDateCreated', ''), "%Y-%m-%dT%H:%M:%SZ")
                photo_dict[checksum] = {'date': created_date,
                                        'checksum': checksum,
                                        'fileSize': max_file_size,
                                        'caption': photo.get('caption', ''),
                                        'height': int(photo.get('height', '0')),
                                        'width': int(photo.get('width', '0'))}
                pass
            # end if
            pass
        # end for

        # Order photos by newest created date
        photo_list = sorted([x for x in photo_dict.values()], key=lambda d: d['date'], reverse=True)

        # Download photos that aren't already downloaded
        for photo in photo_list:
            if not photo.get('checksum', '') in self.existing_files:
                print('Trying to download {}'.format(photo))
                self.get_photo(photo)
            # end if
        # end for

    def get_stream_meta_data(self):
        r = requests.post(self.base_url + '/webstream', data='{"streamCtag":null}',
                          headers={'Content-Type': 'application/json'})
        if 300 <= r.status_code < 400:
            host = r.json().get('X-Apple-MMe-Host', None)
            if host:
                self.base_url = 'https://{}/{}/sharedstreams'.format(host, self.album_guid)
            # end if
        # end if
        r = requests.post(self.base_url + '/webstream', data='{"streamCtag":null}',
                          headers={'Content-Type': 'application/json'})
        stream = r.json()
        photo_guids = {'photoGuids': [x.get('photoGuid', '0') for x in stream.get('photos', [])]}
        photo_guids_json = json.dumps(photo_guids)
        r_photo_urls = requests.post(self.base_url + '/webasseturls', data=photo_guids_json,
                                     headers={'Content-Type': 'application/json'})
        self.photo_urls = r_photo_urls.json()
        self.stream = stream
        pass

    def get_photo(self, photo):
        chcksum = photo['checksum']
        item = self.photo_urls['items'][chcksum]
        ext = re.search('/[\w_\-\+\%\.]+\.(\w+)\?', item['url_path'])
        url = 'https://{}{}&{}'.format(item['url_location'], item['url_path'], chcksum)
        print('Downloading from: {}'.format(url))
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
            im.save(os.path.join(self.save_directory, '{}.{}'.format(chcksum, ext.group(1))))
            # with open(os.path.join(self.save_directory, '{}.{}'.format(chcksum, ext.group(1))), 'wb') as fid:
            #     fid.write(photo_req.content)
            # end with
        # end if
        pass

    def get_directory_info(self):
        file_list = dict()
        for (dir_path, dir_names, file_names) in os.walk(self.save_directory):
            for file_name in file_names:
                name, ext = os.path.splitext(file_name)
                if ext.lower() == '.jpg' or ext.lower() == '.mp4':
                    file_list[name] = os.path.join(dir_path, file_name)
                # end if
            # end for
        # end for
        self.existing_files = file_list
        pass


if __name__ == '__main__':
    input_url = ""
    gallery_url = os.environ.get('PHOTO_GALLERY_URL', input_url)
    download_interval = int(os.environ.get('PHOTO_DOWNLOAD_INTERVAL', str(60 * 60)))
    stopFlag = threading.Event()
    download_manager = DownloadManager(stopFlag, download_interval)
    if os.path.exists('/photos'):
        photo_path = '/photos'
    else:
        photo_path = './images'
    for url in gallery_url.split(', '):
        downloader = Downloader(share_url=url, save_directory=photo_path)
        download_manager.add_downloader(downloader)
        print('Add downloader for: {}'.format(url))
    download_manager.start()
    try:
        while 1:
            time.sleep(10)
    except KeyboardInterrupt:
        stopFlag.set()
