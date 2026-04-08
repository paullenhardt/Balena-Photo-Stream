from pprint import pprint
from PIL import Image
import piexif

codec = 'ISO-8859-1'  # or latin-1

def exif_to_tag(exif_dict):
    exif_tag_dict = {}
    thumbnail = exif_dict.pop('thumbnail')
    try:
        exif_tag_dict['thumbnail'] = thumbnail.decode(codec)
    except AttributeError:
        ...

    for ifd in exif_dict:
        exif_tag_dict[ifd] = {}
        for tag in exif_dict[ifd]:
            try:
                element = exif_dict[ifd][tag].decode(codec)

            except AttributeError:
                element = exif_dict[ifd][tag]

            exif_tag_dict[ifd][piexif.TAGS[ifd][tag]["name"]] = element

    return exif_tag_dict

def get_exif_data(image: Image) -> dict[str, any]:
    exif_dict = piexif.load(image.info.get('exif'))
    exif_dict = exif_to_tag(exif_dict)

    return exif_dict