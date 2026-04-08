import requests
import json
import re
import io
import os
from pathlib import Path
from PIL import Image
from datetime import datetime
from zoneinfo import ZoneInfo
from copy import deepcopy
from .PhotoUtilities import get_exif_data
from .Stream import Stream
from .StreamPost import StreamPost
from .StreamAsset import *

ICLOUD_API_URL_FORMAT = "https://p23-sharedstreams.icloud.com/{}/sharedstreams"

EXTENSION_MATCHER = re.compile(r"/([\w_\-\+\%\.]+\.(\w+))\?")

POSTER_FRAME = "PosterFrame"

UTC_TZ = ZoneInfo("utc")

def init_stream_as_icloud(stream: Stream):
    stream.set_cloud_update_func(update_from_cloud)
    stream.set_cloud_download_func(download_asset)
    stream.update_asset_cloud_download_func()

def update_from_cloud(stream: Stream):
    # If the stream doesn't have an ID, return
    if not stream.id:
        return

    base_url = ICLOUD_API_URL_FORMAT.format(stream.id)

    response = requests.post(
        base_url + "/webstream",
        data='{"streamCtag":null}',
        headers={"Content-Type": "application/json"},
    )
    # Handle Redirects to different servers.
    if 300 <= response.status_code < 400:
        host = response.json().get("X-Apple-MMe-Host", None)
        if host:
            base_url = "https://{}/{}/sharedstreams".format(host, stream.id)
        # Retry the request with the new URL
        response = requests.post(
            base_url + "/webstream",
            data='{"streamCtag":null}',
            headers={"Content-Type": "application/json"},
        )

    stream_meta_data = response.json()
    # Process the Stream meta data and update the stream object (Currently it blindly updates)
    _process_stream(stream, stream_meta_data)
    
    # Need to track "dirty" flags for items to know what to update in the DB
    # Perhaps as each item is "updated" compare it against a previous deepcopy version and if different, flag as dirty
    # Process over every post and asset in the stream
    for item in stream_meta_data.get("photos", list()):
        post_item = _process_post(stream, item)
        asset_item = _process_asset(stream, item, post_item)
    
    # Currently this pulls URLs for EVERY photo in the stream, this may not be needed
    photo_guids = {
        "photoGuids": [
            x.get("photoGuid", "0") for x in stream_meta_data.get("photos", [])
        ]
    }
    photo_guids_json = json.dumps(photo_guids)
    response = requests.post(
        base_url + "/webasseturls",
        data=photo_guids_json,
        headers={"Content-Type": "application/json"},
    )
    photo_urls = response.json()
    photo_urls_dict = photo_urls.get("items", {})

    # Iterate over all assets and update derivatives with download links
    for asset_id in stream.assets:
        for derivative_key in stream.assets[asset_id].derivatives:
            derivative = stream.assets[asset_id].derivatives[derivative_key]
            download_item = StreamAssetDownload()
            download_dict = photo_urls_dict.get(derivative.hash, {})
            url_location = download_dict.get("url_location", None)
            if url_location:
                download_item.url_location = url_location
            url_path = download_dict.get("url_path", None)
            if url_path:
                download_item.url_path = url_path
            url_expiry = download_dict.get("url_expiry", None)
            if url_expiry:
                download_item.url_expiry = datetime.fromisoformat(url_expiry).replace(tzinfo=UTC_TZ)
            search = EXTENSION_MATCHER.search(url_path)
            if search:
                download_item.file_name = search.group(1).lower()
            if derivative.download and derivative.download.file_name != download_item.file_name:
                derivative._dirty = True
            # Update regardless of dirty as we don't track all items such as download URLs which expire
            derivative.download = download_item

    # Propagate any functions as needed.
    stream.update_asset_cloud_download_func()

def _process_stream(stream: Stream, stream_meta_data):
    if "streamName" in stream_meta_data and stream_meta_data["streamName"] != stream.name:
        stream.name = stream_meta_data["streamName"]
        stream._dirty = True
    if "userFirstName" in stream_meta_data and "userLastName" in stream_meta_data:
        owner = "{} {}".format(stream_meta_data["userFirstName"], stream_meta_data["userLastName"])
        if stream.owner != owner:
            stream.owner = owner
            stream._dirty = True

def _process_post(stream: Stream, item: dict[str, any]):
    post_item: StreamPost | None = None
    post_id = item.get("batchGuid", None)
    # Check if the post is already part of the stream
    if post_id:
        if post_id in stream.posts:
            # grab the post
            post_item = stream.posts[post_id]
        else:
            # create a new post and add it to the stream
            post_item = StreamPost()
            stream.posts[post_id] = post_item
            post_item.id = post_id
            stream._dirty = True
    # Ensure the post is up-to-date with the cloud
    # Grab times and convert
    batch_time = item.get("batchDateCreated", None)
    try:
        post_date = datetime.fromisoformat(batch_time).replace(tzinfo=UTC_TZ)
    except:
        post_date = None
    if post_date and post_item and (post_item.post_date != post_date):
        post_item.post_date = post_date
        post_item._dirty = True
    contributor = item.get("contributorFullName", None)
    if contributor and post_item and (post_item.contributor != contributor):
        post_item.contributor = contributor
        post_item._dirty = True
    return post_item

def _process_asset(stream: Stream, item: dict[str, any], post_item: StreamPost):
    asset_item: StreamAsset | None = None
    asset_id = item.get("photoGuid", None)
    # Check if the asset is already part of the stream
    if asset_id:
        if asset_id in stream.assets:
            # grab the asset
            asset_item = stream.assets[asset_id]
        else:
            # create a new asset and add it to the stream
            asset_item = StreamAsset()
            stream.assets[asset_id] = asset_item
            asset_item.id = asset_id
            stream._dirty = True
            if post_item and (not asset_id in post_item.asset_ids):
                post_item.asset_ids.add(asset_id)
                # Not dirty as we don't persist the asset ids with the post
                # post_item._dirty = True
    # Ensure the asset is up-to-date with the cloud
    post_id = post_item.id
    if post_id and (asset_item.post_id != post_id):
        asset_item.post_id = post_id
        asset_item._dirty = True
    # Check caption for changes
    caption = item.get("caption", None)
    if caption and asset_item and (asset_item.caption != caption):
        asset_item.caption = caption
        asset_item._dirty = True
    date_created = item.get("dateCreated", None)
    try:
        creation_date = datetime.fromisoformat(date_created).replace(tzinfo=UTC_TZ)
    except:
        creation_date = None
    if creation_date and asset_item and (asset_item.creation_date != creation_date):
        asset_item.creation_date = creation_date
        asset_item._dirty = True
    try:
        asset_type = AssetType[item.get("mediaAssetType", "photo").upper()]
    except:
        asset_type = AssetType.NONE
    if (asset_type != AssetType.NONE) and asset_item and (asset_item.type != asset_type):
        asset_item.type = asset_type
        asset_item._dirty = True

    # Process any derivatives for the asset
    for key in item.get("derivatives", dict()):
        derivative = item["derivatives"][key]
        derivative_item: StreamAssetDerivative | None = None
        if key in asset_item.derivatives:
            derivative_item = asset_item.derivatives[key]
        else:
            # Create a new derivate and add it to the asset_item
            derivative_item = StreamAssetDerivative()
            asset_item.derivatives[key] = derivative_item
            asset_item._dirty = True
        # Ensure the derivative is up-to-date with the cloud
        checksum = derivative.get("checksum", None)
        if checksum and derivative_item and (derivative_item.hash != checksum):
            derivative_item.hash = checksum
            derivative_item._dirty = True
        width = int(derivative.get("width", None))
        if width and derivative_item and (derivative_item.width != width):
            derivative_item.width = width
            derivative_item._dirty = True
        height = int(derivative.get("height", None))
        if height and derivative_item and (derivative_item.height != height):
            derivative_item.height = height
            derivative_item._dirty = True
        filesize = int(derivative.get("fileSize", None))
        if filesize and derivative_item and (derivative_item.file_size != filesize):
            derivative_item.file_size = filesize
            derivative_item._dirty = True
    
    # Choose a preferred asset
    # if asset is a photo, prefer the largest size
    if asset_item.type == AssetType.PHOTO:
        preferred_derivative = None
        max_file_size = 0
        for derivative_key in asset_item.derivatives:
            derivative = asset_item.derivatives[derivative_key]
            if derivative.file_size > max_file_size:
                max_file_size = derivative.file_size
                preferred_derivative = derivative_key
        if preferred_derivative and (asset_item.preferred_derivative != preferred_derivative):
            asset_item.preferred_derivative = preferred_derivative
            asset_item._dirty = True
    else:
        # If it is not a Photo and a PosterFrame is available, use that
        if POSTER_FRAME in asset_item.derivatives and (asset_item.preferred_derivative != POSTER_FRAME):
            asset_item.preferred_derivative = POSTER_FRAME
        
    return asset_item

def download_asset(asset: StreamAsset, data_dir: Path | None = None):
    # TODO: Check for previous download by verifying the hash?
    # Use a default if no data_dir is passed
    if not data_dir:
        data_dir = Path(os.path.dirname(os.path.dirname(__file__)))
    # if the preferred derivative isn't set or available, return
    if not (asset.preferred_derivative and (asset.preferred_derivative in asset.derivatives)):
        return
    # Grab the preferred derivative
    derivative = asset.derivatives[asset.preferred_derivative]
    derivative_url = "https://{}{}&{}".format(derivative.download.url_location, derivative.download.url_path, derivative.hash)
    print("Downloading from: {}".format(derivative_url))
    download_request = requests.get(derivative_url)
    if download_request.status_code == 200:
        byte_file = io.BytesIO(download_request.content)
        asset_dir = data_dir / Path(derivative.hash[-2:])
        asset_save_path = asset_dir / Path(derivative.hash + "." + derivative.download.file_name.lower())
        if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)
        with open(asset_save_path, "wb") as fid:
            fid.write(download_request.content)
        derivative.filepath = asset_save_path
        derivative.downloaded = True
        derivative._dirty = True
        im = Image.open(byte_file)
        exif_data = get_exif_data(im)
        if exif_data and (asset.exif != exif_data):
            asset.exif = exif_data
            asset._dirty = True
        # max_size = 1280
        # height, width = im.size
        # if max(height, width) % 2 > 0:
        #     size = min(max(height, width) - 1, max_size)
        # else:
        #     size = max_size
        # size = size, size
        # im.thumbnail(size)
        # im.save(
        #     os.path.join(self.save_directory, "{}.{}".format(chcksum, ext.group(1)))
        # )
    ...

