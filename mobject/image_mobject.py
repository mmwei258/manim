import numpy as np
import itertools as it
import os
from PIL import Image
from random import random

from tex_utils import *
from mobject import *

class ImageMobject(Mobject):
    """
    Automatically filters out black pixels
    """
    DEFAULT_CONFIG = {
        "filter_color" : "black",
        "invert" : True,
        "use_cache" : True,
        "should_buffer_points" : False,
        "scale_value" : 1.0
    }
    def __init__(self, image_file, **kwargs):
        digest_config(self, ImageMobject, kwargs, locals())
        Mobject.__init__(self, **kwargs)
        self.filter_rgb = 255 * np.array(Color(self.filter_color).get_rgb()).astype('uint8')
        self.name = to_cammel_case(
            os.path.split(image_file)[-1].split(".")[0]
        )
        possible_paths = [
            image_file,
            os.path.join(IMAGE_DIR, image_file),
            os.path.join(IMAGE_DIR, image_file + ".jpg"),
            os.path.join(IMAGE_DIR, image_file + ".png"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                self.generate_points_from_file(path)
                self.scale(self.scale_value)
                self.center()
                return
        raise IOError("File not Found")
                
    def generate_points_from_file(self, path):
        if self.use_cache and self.read_in_cached_attrs(path):
            return
        image = Image.open(path).convert('RGB')
        if self.invert:
            image = invert_image(image)
        self.generate_points_from_image_array(np.array(image))
        self.cache_attrs(path)

    def get_cached_attr_files(self, path, attrs):
        #Hash should be unique to (path, invert) pair
        unique_hash = str(hash(path+str(self.invert)))
        return [
            os.path.join(IMAGE_MOBJECT_DIR, unique_hash)+"."+attr
            for attr in attrs
        ]

    def read_in_cached_attrs(self, path, 
                             attrs = ("points", "rgbs"), 
                             dtype = "float64"):
        cached_attr_files = self.get_cached_attr_files(path, attrs)
        if all(map(os.path.exists, cached_attr_files)):
            for attr, cache_file in zip(attrs, cached_attr_files):
                arr = np.fromfile(cache_file, dtype = dtype)
                arr = arr.reshape(arr.size/self.DIM, self.DIM)
                setattr(self, attr, arr)
            return True
        return False

    def cache_attrs(self, path, 
                    attrs = ("points", "rgbs"),
                    dtype = "float64"):
        cached_attr_files = self.get_cached_attr_files(path, attrs)
        for attr, cache_file in zip(attrs, cached_attr_files): 
            getattr(self, attr).astype(dtype).tofile(cache_file)


    def generate_points_from_image_array(self, image_array):
        height, width = image_array.shape[:2]
        #Flatten array, and find indices where rgb is not filter_rgb
        array = image_array.reshape((height * width, 3))
        bools = array == self.filter_rgb
        bools = bools[:,0]*bools[:,1]*bools[:,2]
        indices = np.arange(height * width, dtype = 'int')[~bools]
        rgbs = array[indices, :].astype('float') / 255.0

        points = np.zeros((indices.size, 3), dtype = 'float64')
        points[:,0] =  indices%width - width/2
        points[:,1] = -indices/width + height/2

        height, width = map(float, (height, width))
        if height / width > float(DEFAULT_HEIGHT) / DEFAULT_WIDTH:
            points *= 2 * SPACE_HEIGHT / height
        else:
            points *= 2 * SPACE_WIDTH / width
        self.add_points(points, rgbs = rgbs)

    def should_buffer_points(self):
        # potentially changed in subclasses
        return False

class Face(ImageMobject):
    DEFAULT_CONFIG = {
        "mode" : "simple",
        "scale_value" : 0.5
    }
    def __init__(self, **kwargs):
        """
        Mode can be "simple", "talking", "straight"
        """
        digest_config(self, Face, kwargs)
        ImageMobject.__init__(self, self.mode + "_face", **kwargs)

class VideoIcon(ImageMobject):
    DEFAULT_CONFIG = {
        "scale_value" : 0.3
    }
    def __init__(self, **kwargs):
        digest_config(self, VideoIcon, kwargs)
        ImageMobject.__init__(self, "video_icon", **kwargs)

#TODO, Make both of these proper mobject classes
def text_mobject(text, size = None):
    size = size or "\\Large" #TODO, auto-adjust?
    return tex_mobject(text, size, TEMPLATE_TEXT_FILE)

def tex_mobject(expression, 
                size = None, 
                template_tex_file = TEMPLATE_TEX_FILE):
    if size == None:
        if len("".join(expression)) < MAX_LEN_FOR_HUGE_TEX_FONT:
            size = "\\Huge"
        else:
            size = "\\large"
        #Todo, make this more sophisticated.
    image_files = tex_to_image(expression, size, template_tex_file)
    if isinstance(image_files, list):
        #TODO, is checking listiness really the best here?
        result = CompoundMobject(*map(ImageMobject, image_files))
    else:
        result = ImageMobject(image_files, should_buffer_points = True)
    return result.highlight("white")





