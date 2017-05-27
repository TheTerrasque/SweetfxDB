from PIL import Image
from PIL import ImageFile
import cStringIO
from django.core.files.uploadedfile import SimpleUploadedFile
import os.path

class BaseImage(object):
    
    save_options = {
        "format" :"JPEG",
        "quality": 65,
        "optimize": True, 
        "progressive": True,
    }
    
    def __init__(self, path):
        self.path = path
        self.image = self.open_image(path)
    
    def open_image(self, path):
        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img
    
    def change_image(self):
        pass
    
    def get_save_options(self):
        return self.save_options
    
    def store_image(self):
        res = cStringIO.StringIO()
        ImageFile.MAXBLOCK = 1024 * 1024
        options = self.get_save_options()
        self.image.save(res, **options)
        res.seek(0)
        return res
    
    def get_filename(self):
        return os.path.basename(self.path)
    
    def save_image(self):
        filename = self.get_filename()
        self.change_image()
        res = self.store_image()
        res = SimpleUploadedFile(filename, res.read())
        return (filename, res)

class ResizeImage(BaseImage):
   
    def change_image(self):
        cur_w, cur_h = self.image.size
        nw, nh = self.new_size
        ratio = min(float(nw)/cur_w, float(nh)/cur_h)
        new_size = (int(cur_w * ratio), int(cur_h * ratio))
        self.image = self.image.resize(new_size, Image.ANTIALIAS)

class CompressImage(BaseImage):
    
    save_options = {
        "format" :"PNG",
        "optimize": True,
    }

    def should_compress(self):
        if self.image.format in ["BMP"]:
            return True

    def get_filename(self):
        return os.path.basename(self.path) + ".png"
    
def resize_image(path, size=(1024, 1024), quality=65, format="JPEG"):
    handler = ResizeImage(path)
    handler.new_size = size
    handler.save_options["format"] = format
    handler.save_options["quality"] = quality
    return handler.save_image()

