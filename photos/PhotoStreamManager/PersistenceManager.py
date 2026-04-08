from pathlib import Path
import sqlite3
import json
from zoneinfo import ZoneInfo
from . import iCloudSharedPhotoStream
from .Stream import Stream, StreamType
from .StreamPost import StreamPost
from .StreamAsset import *
from . import ROOT_DIRECTORY, PHOTO_PATH

""" Upsert 

cursor.execute('''
    INSERT INTO users (id, name) VALUES (?, ?)
    ON CONFLICT(id) DO UPDATE SET name = excluded.name;
''', (1, 'Bob'))

"""
UTC_TZ = ZoneInfo("utc")
STREAM_TYPE_MAP = {
    StreamType.ICLOUD_SHARED_STREAM: iCloudSharedPhotoStream.init_stream_as_icloud
}


# Future TODO: Abstract class for other options beyond SQLite?
class PersistenceManager:
    def __init__(self):
        self._db_path: Path = PHOTO_PATH / Path("photos.db")
        self._cursor = None
        # Initialize DB Schema if required
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self._db_path) as connection:
            self._cursor = connection.cursor()
            self._cursor.execute("PRAGMA journal_mode = WAL")
            self._cursor.execute("PRAGMA foreign_keys = ON")
            self._create_stream_table()
            self._create_stream_props_table()
            self._create_posts_table()
            self._create_assets_table()
            self._create_asset_derivatives_table()
            connection.commit()
            self._cursor = None
        ...

    def _create_stream_table(self):
        query = """
                CREATE TABLE IF NOT EXISTS streams (
                    stream_id TEXT PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    owner TEXT,
                    enabled INT,
                    url TEXT
                );
                """
        self._cursor.execute(query)
        ...

    def _create_stream_props_table(self):
        query = """
                CREATE TABLE IF NOT EXISTS stream_properties (
                    prop_id INT PRIMARY KEY,
                    stream_id TEXT NOT NULL,
                    key TEXT,
                    value TEXT,
                    FOREIGN KEY(stream_id) REFERENCES streams(stream_id)
                );
                """
        self._cursor.execute(query)
        ...

    def _create_posts_table(self):
        query = """
                CREATE TABLE IF NOT EXISTS posts (
                    post_id TEXT NOT NULL,
                    stream_id TEXT NOT NULL,
                    date TEXT,
                    contributor TEXT,
                    PRIMARY KEY (post_id, stream_id),
                    FOREIGN KEY(stream_id) REFERENCES streams(stream_id)
                );
                """
        self._cursor.execute(query)
        ...

    def _create_assets_table(self):
        query = """
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT NOT NULL,
                    stream_id TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    creation_date TEXT,
                    caption TEXT,
                    preferred_derivative TEXT,
                    type TEXT, -- Enumeration
                    exif TEXT, -- JSON Dict
                    PRIMARY KEY (asset_id, stream_id, post_id),
                    FOREIGN KEY(stream_id) REFERENCES streams(stream_id),
                    FOREIGN KEY(post_id, stream_id) REFERENCES posts(post_id, stream_id)
                );
                """
        self._cursor.execute(query)
        ...

    def _create_asset_derivatives_table(self):
        query = """
                CREATE TABLE IF NOT EXISTS derivatives (
                    derivative_id TEXT NOT NULL, -- This is the HASH as well
                    name TEXT NOT NULL, -- This is the key for an asset to find based on preferred derivative
                    asset_id TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    stream_id TEXT NOT NULL,
                    width INT,
                    height INT,
                    file_size INT,
                    downloaded INT, -- BOOL
                    filepath TEXT,
                    -- url_location TEXT,
                    -- url_path TEXT,
                    -- url_expiry TEXT,
                    file_name TEXT,
                    PRIMARY KEY (derivative_id, name, asset_id),
                    FOREIGN KEY(asset_id, stream_id, post_id) REFERENCES assets(asset_id, stream_id, post_id)
                );
                """
        self._cursor.execute(query)
        ...

    def persist_stream(
        self, stream: Stream, connection_input: sqlite3.Connection | None = None
    ):
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()

        # Update the stream if it is dirty
        if stream._dirty:
            query = """
                        INSERT INTO streams (stream_id, name, type, owner, enabled, url) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(stream_id) 
                        DO UPDATE SET 
                        name = excluded.name, 
                        type = excluded.type,
                        owner = excluded.owner,
                        enabled = excluded.enabled,
                        url = excluded.url
                    """
            cursor.execute(
                query,
                (
                    stream.id,
                    stream.name,
                    stream.type.name,
                    stream.owner,
                    stream.enabled,
                    stream.url,
                ),
            )
            connection.commit()
            stream._dirty = False
        # Persist posts and assets of the stream
        for post in stream.posts.values():
            self.persist_post(post, stream, connection_input=connection)
        for asset in stream.assets.values():
            self.persist_asset(asset, stream, connection_input=connection)
        # Close connection if we opened it
        if connection_input is None:
            connection.close()
        ...

    def persist_post(
        self,
        post: StreamPost,
        stream: Stream,
        connection_input: sqlite3.Connection | None = None,
    ):
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()

        if post._dirty:
            query = """
                        INSERT INTO posts (post_id, stream_id, date, contributor) VALUES (?, ?, datetime(?), ?)
                        ON CONFLICT(post_id, stream_id) 
                        DO UPDATE SET 
                        date = excluded.date,
                        contributor = excluded.contributor
                    """
            cursor.execute(
                query,
                (
                    post.id,
                    stream.id,
                    post.post_date.replace(tzinfo=UTC_TZ).isoformat(),
                    post.contributor,
                ),
            )
            connection.commit()
            post._dirty = False
        # Close connection if we opened it
        if connection_input is None:
            connection.close()

    def persist_asset(
        self,
        asset: StreamAsset,
        stream: Stream,
        connection_input: sqlite3.Connection | None = None,
    ):
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()

        if asset._dirty:
            query = """
                        INSERT INTO assets (asset_id, stream_id, post_id, creation_date, caption, preferred_derivative, type, exif) 
                        VALUES (?, ?, ?, datetime(?), ?, ?, ?, ?)
                        ON CONFLICT(asset_id, stream_id, post_id) 
                        DO UPDATE SET
                        creation_date = excluded.creation_date, 
                        caption = excluded.caption,
                        preferred_derivative = excluded.preferred_derivative, 
                        type = excluded.type, 
                        exif = excluded.exif
                    """
            cursor.execute(
                query,
                (
                    asset.id,
                    stream.id,
                    asset.post_id,
                    asset.creation_date.replace(tzinfo=UTC_TZ).isoformat(),
                    asset.caption,
                    asset.preferred_derivative,
                    asset.type.name,
                    json.dumps(asset.exif),
                ),
            )
            connection.commit()
            asset._dirty = False
        # Persist any derivatives of the asset
        for key, derivative in asset.derivatives.items():
            self.persist_derivative(
                derivative, asset, key, stream, connection_input=connection
            )
        # Close connection if we opened it
        if connection_input is None:
            connection.close()

    def persist_derivative(
        self,
        derivative: StreamAssetDerivative,
        asset: StreamAsset,
        derivative_key: str,
        stream: Stream,
        connection_input: sqlite3.Connection | None = None,
    ):
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()

        if derivative._dirty:
            query = """
                        INSERT INTO derivatives (derivative_id, name, asset_id, post_id, stream_id, 
                            width, height, file_size, downloaded, filepath, file_name) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(derivative_id, name, asset_id)
                        DO UPDATE SET 
                        post_id = excluded.post_id,
                        stream_id = excluded.stream_id,
                        width = excluded.width,
                        height = excluded.height,
                        file_size = excluded.file_size,
                        downloaded = excluded.downloaded,
                        filepath = excluded.filepath,
                        file_name = excluded.file_name
                    """
            cursor.execute(
                query,
                (
                    derivative.hash,
                    derivative_key,
                    asset.id,
                    asset.post_id,
                    stream.id,
                    derivative.width,
                    derivative.height,
                    derivative.file_size,
                    derivative.downloaded,
                    derivative.filepath.as_posix() if derivative.filepath else derivative.filepath,
                    derivative.download.file_name,
                ),
            )
            connection.commit()
            derivative._dirty = False
        # Close connection if we opened it
        if connection_input is None:
            connection.close()

    def load_streams(
        self, connection_input: sqlite3.Connection | None = None
    ) -> dict[str, Stream]:
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
        streams = {}
        # Select ALL Streams from the streams table
        query = """
                SELECT
                    streams.stream_id,
                    streams.name,
                    streams.type,
                    streams.owner,
                    streams.enabled,
                    streams.url
                FROM
                    streams;
                """
        cursor.execute(query)
        results = cursor.fetchall()
        for stream_data in results:
            stream = Stream(
                id=stream_data[0],
                name=stream_data[1],
                type=StreamType[stream_data[2]],
                owner=stream_data[3],
                enabled=bool(stream_data[4]),
                url=stream_data[5],
            )
            streams[stream.id] = stream
            # At some point we may need to load stream properties as well
            stream.assets.update(
                self._load_assets_for_stream(stream, connection_input=connection)
            )
            stream.posts.update(
                self._load_posts_for_stream(stream, connection_input=connection)
            )
            # Initialize the stream as the proper type
            STREAM_TYPE_MAP[stream.type](stream)

        if connection_input is None:
            connection.close()
        return streams

    def _load_assets_for_stream(
        self, stream: Stream, connection_input: sqlite3.Connection | None = None
    ) -> dict[str, StreamAsset]:
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
        assets = {}
        # Select ALL assets from the assets table for our particular stream
        query = """
                SELECT
                    assets.asset_id,
                    assets.post_id,
                    assets.creation_date,
                    assets.caption,
                    assets.preferred_derivative,
                    assets.type,
                    assets.exif
                FROM
                    assets
                WHERE
                    assets.stream_id = ?;
                """
        cursor.execute(query, (stream.id,))
        results = cursor.fetchall()
        for asset_data in results:
            asset = StreamAsset(
                id=asset_data[0],
                post_id=asset_data[1],
                creation_date=datetime.fromisoformat(asset_data[2]).replace(
                    tzinfo=UTC_TZ
                ),
                caption=asset_data[3],
                preferred_derivative=asset_data[4],
                type=AssetType[asset_data[5]],
                exif=json.loads(asset_data[6]),
            )
            assets[asset.id] = asset
            asset.derivatives.update(
                self._load_derivatives_for_asset(
                    stream, asset, connection_input=connection
                )
            )
        if connection_input is None:
            connection.close()
        return assets

    def _load_posts_for_stream(
        self, stream: Stream, connection_input: sqlite3.Connection | None = None
    ) -> dict[str, StreamPost]:
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
        posts = {}
        # Select ALL posts from the posts table for our particular stream
        query = """
                SELECT
                    posts.post_id,
                    posts.date,
                    posts.contributor
                FROM
                    posts
                WHERE
                    posts.stream_id = ?;
                """
        cursor.execute(query, (stream.id,))
        results = cursor.fetchall()
        for post_id, post_date, contributor in results:
            post = StreamPost(
                id=post_id,
                post_date=datetime.fromisoformat(post_date).replace(tzinfo=UTC_TZ),
                contributor=contributor,
            )
            posts[post.id] = post
        if connection_input is None:
            connection.close()
        return posts

    def _load_derivatives_for_asset(
        self,
        stream: Stream,
        asset: StreamAsset,
        connection_input: sqlite3.Connection | None = None,
    ) -> dict[str, StreamAssetDerivative]:
        if connection_input:
            connection = connection_input
            cursor = connection_input.cursor()
        else:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
        derivatives = {}
        # Select ALL posts from the posts table for our particular stream
        query = """
                SELECT
                    derivative_id,
                    name,
                    width,
                    height,
                    file_size,
                    downloaded,
                    filepath,
                    file_name
                FROM
                    derivatives
                WHERE
                    derivatives.asset_id = ?;
                """
        cursor.execute(query, (asset.id,))
        results = cursor.fetchall()
        for (
            derivative_id,
            name,
            width,
            height,
            file_size,
            downloaded,
            filepath,
            file_name,
        ) in results:
            derivative = StreamAssetDerivative(
                hash=derivative_id,
                width=width,
                height=height,
                file_size=file_size,
                downloaded=bool(downloaded),
                filepath=filepath,
            )
            derivative.download.file_name = file_name
            derivatives[name] = derivative
        if connection_input is None:
            connection.close()
        return derivatives
