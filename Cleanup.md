# Project Architecture
This project needs a refactoring.  I would like to remove the depence on Balena and switch to a basic minimal linux with docker containers.
The project should not be specific for hardware.  It should autodetect as much as possible or support YAML configuration for anything that cannot be detected or needs configuration.
The project is going to be four main modules.

**Modules**
 1. Manager module
    - This will be a service which supports updating and controlling everything.  It will be able to check for new versions of the apps and OS updates.  Depending on settings and schedule, it will update the apps and OS automatically while maintaining a working system (boot environments or similar).  This is a simplification and replication of what balena offers, but without fully relying on balena's services.
 2. Netbird or other networking VPN service
    - This supports allowing secure direct connections for monitoring, backups, control, etc.
 3. Photo Manager App
    - This app automatically downloads, monitors, and manages photos on the display.
 4. User Interface App
    - This app displays photos and runs the photo UI.  It is intended to provide a settings interface and potentially more custimizable widgets.
    - Kivy is the UI framework for now.  In order to avoid memory and performance bloat, no browser based solutions are evaluated.
    - Outstanding question on whether the UI APP is monolithic or whether it should be many apps with a custom X-Window manager/compositor like a bespoke QTile?
    - It will start as monolithic currently.

## Manager
This doesn't yet exist. Everything needs to be done.  As long as a VPN allows direct control, the manager is not *required*, however it will be difficult to go without for long.

## Netbird or VPN
This is a standalone service and is off-the-shelf.  This needs some instruction or automation for setting up a device, but should be hands off after that.

## Photos
 - Split into a Stream Object which just tracks a given stream and can save off the meta data and load meta data from file
    - This object is basically the in memory representation of the stream that we can query for photos by "id" or something
    - This should have a generic API such that we can support multiple stream types
 - Have a generic downloader which takes a list of photos to download and downloads them in the background, 
   runs assigned tasks on the photo (such as downscaling or updating a stream with a local file location)
 - Use a YAML file or something for setup (specifying streams, stream types, actions to take on local files, etc)
 - Needs to store full meta data for photos and support EXIF tag reading.

 ## Kivy
 The UI needs full rework.  Would like to be able to display photo info when desired on a photo.  The UI needs to support showing settings screen.  More direct control, such as setting wifi password through the UI as well.
