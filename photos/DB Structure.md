# Database Structure

## Streams Table
This table stores each stream, the name and type of the stream, and whether it is enabled or not.
 - Stream ID
 - Stream Name
 - Stream Type
 - Stream Enabled
 - Stream URL


## Streams Properties
This table stores extra key-value pairs for a stream
 - Property ID
 - Stream ID
 - Key
 - Value

 ## Asset Table
This table stores asset information
 - Asset Internal ID
 - Stream ID
 - Asset External ID
 - Asset Batch/Group ID
 - Asset RemoteURL? Do we need this, it invalidates over time?
 - Asset StoredFilePath
 - Asset IsDownloaded
 - Asset Analyzed?
 - Asset Resized?
 - Asset Type
 - Asset Width
 - Asset Height
 - Asset DateTime
 - Asset Location
 - Asset EXIF_Data
 - Asset isFavorite
 - Asset SlideShowVisibility
 - Asset Comments?


# Software Stream Download Manager
This software manages all the different streams the display is "subscribed" to.  It checks for assets that are available but not cached locally and then attempts to download them.  Currently the assets are then transformed to match the dimensions of the screen to prevent storing assets at too high of a resolution wasting storage space and wasting processing power downscaling the image for the screen.

The download manager starts up streams based on the stream type, adds them to an array and loops through them having them download data.  When no new assets are available, it should wait until the next polling period and have each stream check for new assets, downloading them as necessary.

The streams themselves have access to meta data about the stream and extra meta data about the asset.  This extra meta data is who uploaded the assets, when they were uploaded (different from when the asset was created), comments for the assets, groupings of the assets.  How much flexibility is needed beyond supporting just the SharedPhotoStream from icloud?

SharedPhotoStream has owner and name for meta data and is composed of an array of "posts" (or groups).  The post has comments and specific meta data for itself.  Each post has an array of assets.  The assets themselves have EXIF data, size/resolution, creation time/date.

## Software Startup Sequence
Download Manager runs and "loads" data.  The Data is loaded from sqlite.  If an sqlite db is not present, one is created and initialized.  The stream data is compared against stream info from the config file (not sure what to do if a stream is in the db, but not in the config) and if a new stream is found, it is added to the db. 

Stream objects are created for each stream in DB.  Then post objects are created for each stream post.  And lastly Asset objects are created for each asset.  The download manager should have all streams, posts, and assets loaded into memory (meta data at least).  It can then have the each stream object update itself by checking each post and if a post is new creating a post object.  The streams will have each post update themselves and for each asset in the post, an asset object will be created if it is new otherwise the download URL can be updated (if it changed).  From there, all assets which need downloading will be queued up.  Any changed or added post/asset objects will persist themselves to the db by a trigger from the download manager down the chain.

For simplicity, post/asset/stream objects will inherit from a generic post or asset or stream object.  The subclassed items can add specificity for a given type (if needed) and mixin some sqlite creation/update queries based on their type such that an object can be passed to a "Persistence" class which can ask the object for a unique query to update or create it.

## Asset Downloading
When an asset is queued for download, the asset should have a method to provide a URL to download itself from.  The asset should also have a series of operations which should be applied once downloaded (such as resize, extract EXIF, etc).  The asset should also have a filepath to save the actual file to.  The methods to download, save, and process operations should be built into the base asset class.  Likewise the stream objects should have methods to pull stream updates.