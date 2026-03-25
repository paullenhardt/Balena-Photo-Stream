# Project Architecture
This project needs a refactoring.  I would like to remove the dependence on Balena and switch to a basic minimal linux with docker containers.
The project should not be specific for hardware.  It should autodetect as much as possible or support YAML configuration for anything that cannot be detected or needs configuration.
The project is going to be four main modules.

**Modules**
 1. Manager module (New component.  Python?)
    - This will be a service which supports updating and controlling everything.  It will be able to check for new versions of the apps and OS updates.  Depending on settings and schedule, it will update the apps and OS automatically while maintaining a working system (boot environments or similar).  This is a simplification and replication of what balena offers, but without fully relying on balena's services.
 2. Netbird or other networking VPN service (Off-the-shelf)
    - This supports allowing secure direct connections for monitoring, backups, control, etc.
 3. Photo Manager App (Python scripts)
    - This app automatically downloads, monitors, and manages photos on the display.
    - Note, this app does not display anything.
 4. User Interface App(s)
    - This app displays photos and runs the photo UI.  It is intended to provide a settings interface and potentially more customizable widgets.
    - Kivy is the original UI framework.  In order to avoid memory and performance bloat, no browser based solutions are evaluated.  We want the entire system to run in under 500 MB of ram.  Ideally less for possible expansion.
    - Evaluating possibility of switching to LVGL (with python? or c?). 
        - This is looking much better than KIVY with much lower level control but yet a better API for widgets and animations.
        - ~~Can multiple LVGL apps paint to frame buffers with one primary app compositing the framebuffers and passing around inputs?~~
            - Not worth investigation for now.
        - Micropython OS? Just came out.  Needs investigation.
    - ~~Outstanding question on whether the UI APP is monolithic or whether it should be many apps with a custom X-Window manager/compositor like a bespoke QTile?~~
        - It will start as monolithic currently (at least monolithic in the sense that it all runs in a single container).

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

 ## User Interface Apps
 The UI needs full rework.  Would like to be able to display photo info when desired on a photo.  The UI needs to support showing settings screen.  More direct control, such as setting wifi password through the UI as well.


## Getting LVGL Working
https://falb18.github.io/tinkering_at_night/archives/2025/rpi-lvgl-demo-drm.html
