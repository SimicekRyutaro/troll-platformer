"""
File with utilities - image loading, animations
"""
import os
import pygame

BASE_IMG_PATH = "data/images/"

def load_image(path, alpha=True):
    """Loads image from path"""
    if alpha:
        img = pygame.image.load(BASE_IMG_PATH + path).convert_alpha()
    else:
        img = pygame.image.load(BASE_IMG_PATH + path).convert()
        img.set_colorkey((0, 0, 0))
    return img

def load_images(path, alpha=True):
    """Loads all images from directory path"""
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + img_name, alpha=alpha))
    return images

class Animation:
    """Class with animations for entities"""
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        """Returns a copy of self"""
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        """Increases frame of the animation"""
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        """Returns the image of current frame of the animation"""
        return self.images[int(self.frame / self.img_duration)]
