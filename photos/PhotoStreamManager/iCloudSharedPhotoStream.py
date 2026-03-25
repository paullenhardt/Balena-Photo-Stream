import requests
import json
import re
from copy import deepcopy
from .Stream import Stream
from .StreamPost import StreamPost
from .StreamAsset import *

ICLOUD_API_URL_FORMAT = "https://p23-sharedstreams.icloud.com/{}/sharedstreams"

EXTENSION_MATCHER = re.compile(r"/[\w_\-\+\%\.]+\.(\w+)\?")


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
    process_stream(stream, stream_meta_data)

    # Clear all tmp lists
    stream._tmp_posts_order.clear()
    for post_key in stream.posts:
        stream.posts[post_key]._tmp_asset_ids.clear()
    
    # Need to track "dirty" flags for items to know what to update in the DB
    # Perhaps as each item is "updated" compare it against a previous deepcopy version and if different, flag as dirty
    # Process over every post and asset in the stream
    for item in stream_meta_data.get("photos", list()):
        post_item = process_post(stream, item)
        asset_item = process_asset(stream, item, post_item)
    
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
    for asset_id in stream.assets:
        for derivative_key in stream.assets[asset_id].derivatives:
            derivative = stream.assets[asset_id].derivatives[derivative_key]
            download_item = StreamAssetDownload()
            download_dict = photo_urls_dict.get(derivative.hash, {})
            download_item.url_location = download_dict.get("url_location", None)
            url_path = download_dict.get("url_path", None)
            if url_path:
                download_item.url_path = url_path
            url_expiry = download_dict.get("url_expiry", None)
            if url_expiry:
                download_item.url_expiry = datetime.fromisoformat(url_expiry)
            search = EXTENSION_MATCHER.search(url_path)
            if search:
                download_item.file_name = search.group(1)
            derivative.download = download_item

    # Check the stream for changes, propagate _tmp lists to permanent if different
    # Persist stream changes to DB
    ...


def process_stream(stream, stream_meta_data):
    if "streamName" in stream_meta_data:
        stream.name = stream_meta_data["streamName"]
    if "userFirstName" in stream_meta_data and "userLastName" in stream_meta_data:
        stream.owner = "{} {}".format(stream_meta_data["userFirstName"], stream_meta_data["userLastName"])

def process_post(stream: Stream, item: dict[str, any]):
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
        stream._tmp_posts_order.append(post_id)
    # Ensure the post is up-to-date with the cloud
    # Create function that takes in the item dict and the post_item and updates it
    batch_time = item.get("batchDateCreated", None)
    if batch_time and post_item:
        post_item.post_date = datetime.fromisoformat(batch_time)
    caption = item.get("caption", None)
    if caption and post_item:
        post_item.caption = caption
    contributor = item.get("contributorFullName", None)
    if contributor and post_item:
        post_item.contributor = contributor
    return post_item

def process_asset(stream, item, post_item):
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
            if post_item:
                post_item._tmp_asset_ids.append(asset_id)
    # Ensure the asset is up-to-date with the cloud
    # Create function that takes in the item dict and the asset_item and updates it along with updating the derivatives
    date_created = item.get("dateCreated", None)
    if date_created and asset_item:
        asset_item.creation_date = datetime.fromisoformat(date_created)
    asset_type = item.get("mediaAssetType", "photo")
    if asset_type and asset_item:
        asset_item.type = AssetType[asset_type.upper()]

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
        # Ensure the derivative is up-to-date with the cloud
        checksum = derivative.get("checksum", None)
        if checksum and derivative_item:
            derivative_item.hash = checksum
        width = derivative.get("width", None)
        if width and derivative_item:
            derivative_item.width = int(width)
        height = derivative.get("height", None)
        if height and derivative_item:
            derivative_item.height = int(height)
        filesize = derivative.get("fileSize", None)
        if filesize and derivative_item:
            derivative_item.file_size = int(filesize)
        
    return asset_item
