import os
from pathlib import Path


ROOT_DIRECTORY = Path(os.environ.get("ROOT_DIRECTORY", Path(".")))
if os.path.exists("/photos"):
    PHOTO_PATH = Path("/photos")
else:
    PHOTO_PATH = ROOT_DIRECTORY / Path("images")