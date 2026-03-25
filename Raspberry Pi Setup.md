# Steps to setup the Raspberry Pi 5
The following doc explains how to setup a Raspberry Pi 5 as a photo-frame using a [WaveShare 10.1 DSI Touch Screen](https://www.waveshare.com/wiki/10.1-DSI-TOUCH-A).  In addition to configuring the hardware correctly, this doc will explain how to modify the startup process and add a custom boot screen before building and deploying the photo-frame software.

## WaveShare 10.1 DSI Touch A Setup
Follow the normal steps on <https://www.waveshare.com/wiki/10.1-DSI-TOUCH-A>.  Some points to note, the DSI-1 port is not well labeled on the wiki.  The instructions to rotate the image from portrait to landscape are wrong (the wiki states the command to add to command.txt file is `video=DSI-2:720x1280,rotate=90` when it should be `video=DSI-2:800x1280,rotate=270`).

## Setup Plymouth Splash Screen
Add instructions here

## Install Netbird
```bash
#!/bin/bash
curl -fsSL https://pkgs.netbird.io/install.sh | sh

sudo netbird up --setup-key <YOUR_SETUP_KEY>
```

## Setup Cross Compile on macOS

```bash
#!/bin/bash
brew tap messense/macos-cross-toolchains
brew install aarch64-unknown-linux-gnu
```