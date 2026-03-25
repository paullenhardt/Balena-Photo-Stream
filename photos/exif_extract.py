# from PIL import Image
# from PIL.ExifTags import TAGS

# # path to the image or video
# imagename = "test.jpg"

# # read the image data using PIL
# image = Image.open(imagename)

# # extract EXIF data
# exifdata = image.getexif()

# # iterating over all EXIF data fields
# for tag_id in exifdata:
#     # get the tag name, instead of human unreadable tag id
#     tag = TAGS.get(tag_id, tag_id)
#     data = exifdata.get(tag_id)
#     # decode bytes
#     if isinstance(data, bytes):
#         data = data.decode()
#     print(f"{tag:25}: {data}")



from pprint import pprint
from PIL import Image
import piexif

codec = 'ISO-8859-1'  # or latin-1

def exif_to_tag(exif_dict):
    exif_tag_dict = {}
    thumbnail = exif_dict.pop('thumbnail')
    exif_tag_dict['thumbnail'] = thumbnail.decode(codec)

    for ifd in exif_dict:
        exif_tag_dict[ifd] = {}
        for tag in exif_dict[ifd]:
            try:
                element = exif_dict[ifd][tag].decode(codec)

            except AttributeError:
                element = exif_dict[ifd][tag]

            exif_tag_dict[ifd][piexif.TAGS[ifd][tag]["name"]] = element

    return exif_tag_dict

def main():
    filename = 'test.jpg'
    im = Image.open(filename)

    exif_dict = piexif.load(im.info.get('exif'))
    exif_dict = exif_to_tag(exif_dict)

    pprint(exif_dict['GPS'])

if __name__ == '__main__':
   main()
