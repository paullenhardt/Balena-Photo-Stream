import os

from kivy.app import App
from kivy.uix.carousel import Carousel
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.properties import NumericProperty, BooleanProperty, ObjectProperty
import time
import datetime

import random

from kivy.config import Config
# Config.read('config.ini')
# Config.set("graphics", "show_cursor", 0)
# Config.set("graphics", "borderless", 1)
# Config.set("kivy", "log_level", "debug")
# Config.set('graphics', 'width', '800')
# Config.set('graphics', 'height', '480')
# Config.set('kivy', 'keyboard_mode', 'systemanddock')
# Config.set('input', 'mtdev_%(name)s', 'probesysfs,provider=mtdev,param=invert_x=1,param=invert_y=1')
# Config.set('input', 'hid_%(name)s', 'probesysfs,provider=hidinput,param=invert_x=1,param=invert_y=1')


class PhotoLoader(object):
    def __init__(self, photo_path='/photos' if os.path.exists('/photos') else './images'):
        self.image_list = dict()
        self.shown_images = set()
        self.photo_path = photo_path
        self.load_images()
        Clock.schedule_interval(self.load_images,
                                int(os.environ.get('KIVY_REFRESH_IMAGE_INTERVAL', str(10 * 60))))

    def load_images(self, dt=0):
        file_list = dict()
        for (dir_path, dir_names, file_names) in os.walk(self.photo_path):
            for file_name in file_names:
                name, ext = os.path.splitext(file_name)
                if ext.lower() == '.jpg':
                    file_list[name] = os.path.join(dir_path, file_name)
                # end if
            # end for
        # end for
        self.image_list = file_list

    def get_next_image(self):
        photo_path = ''
        if self.image_list:
            not_shown = dict(self.image_list.items())
            for key in self.shown_images:
                not_shown.pop(key, '')
            # end for
            if not not_shown:
                not_shown = self.image_list
                self.shown_images = set()
            # end if
            photos = [key for key in not_shown.keys()]
            next_photo = random.choice(photos)
            self.shown_images.add(next_photo)
            photo_path = self.image_list[next_photo]
        # end if
        return photo_path


class PhotoSlideShow(Carousel):
    last_slide_time = ObjectProperty(datetime.datetime.now())
    current_slide_delay = NumericProperty(int(os.environ.get('KIVY_SLIDE_SHOW_INTERVAL', str(10))))
    paused = BooleanProperty(False)

    def __init__(self, photo_loader=PhotoLoader(), **kwargs):
        super(PhotoSlideShow, self).__init__(**kwargs)
        self.photo_loader = photo_loader
        num_slides = max(int(os.environ.get('KIVY_NUM_SLIDES', str(10))), 3)
        for i in range(num_slides):
            image = AsyncImage(source=self.photo_loader.get_next_image(), fit_mode="contain")
            self.add_widget(image)
        # self.start_slides()
        Clock.schedule_interval(self.run_slide_show, 1)
        self.old_index = self.index
        self.last_loaded_slide = num_slides - 1
        super(PhotoSlideShow, self).bind(next_slide=self.load_new_slide)

    def on_touch_down(self, touch):
        # print('Touch Down, {} : {}, {}'.format(touch.device, touch.pos))
        self.direction = 'right'
        self.paused = True
        return super(PhotoSlideShow, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        print('Touch Move, {} : {} - {}'.format(touch.device, touch.pos, touch.dpos))
        return super(PhotoSlideShow, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        # print('Touch Up, {} : {}'.format(touch.device, touch.pos))
        self.paused = False
        self.current_slide_delay = int(os.environ.get('KIVY_SLIDE_SHOW_TOUCH_PAUSE_INTERVAL', str(30)))
        return super(PhotoSlideShow, self).on_touch_up(touch)

    def load_new_slide(self, slide_show=None, slide=None):
        # Add new image
        forward = (self.index - (self.old_index + 1) % len(self.slides) == 0)
        print('Current index {}, old index {}, forward {}'.format(self.index, self.old_index, forward))
        if slide is not None and forward and self.index == self.last_loaded_slide % len(self.slides):
            print('Loading new slide, last loaded slide {}'.format(self.last_loaded_slide))
            slide.source = self.photo_loader.get_next_image()
            self.last_loaded_slide = (self.index + 1) % len(self.slides)
        # end if
        self.old_index = self.index

    def change_image(self, dt=0):
        self.current_slide_delay = int(os.environ.get('KIVY_SLIDE_SHOW_INTERVAL', str(10)))
        self.last_slide_time = datetime.datetime.now()
        direction = random.choice(['right', 'left', 'top', 'bottom'])
        self.direction = direction
        self.load_next()

    def run_slide_show(self, dt=0):
        print('.', end=' ')
        if self.paused:
            self.last_slide_time = datetime.datetime.now()
            print('Paused {}'.format(self.last_slide_time))
        current_time = datetime.datetime.now()
        if not self.paused \
                and current_time - self.last_slide_time > datetime.timedelta(seconds=self.current_slide_delay):
            self.change_image()


class CarouselApp(App):
    def build(self):
        float_layout = FloatLayout()
        carousel = PhotoSlideShow(direction='right', loop=True)
        float_layout.add_widget(carousel)
        # button = Button(text='Config')
        # button.size_hint = (.1, .1)
        # button.pos_hint = {'x': 0.0, 'y': 0.9}
        # float_layout.add_widget(button)
        # anim = Animation(opacity=0.0)
        # anim.start(button)
        return float_layout


if __name__ == '__main__':
    from kivy.core.window import Window
    Window.maximize()
    Window.fullscreen = True
    print(f"Starting with window size: {Window.size}")
    app = CarouselApp()
    app.run()
