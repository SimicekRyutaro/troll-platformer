"""
File with the Clouds class
"""
import random

class Cloud:
    """Class representing a single cloud"""
    def __init__(self, pos, img, speed):
        self.pos = list(pos)
        self.img = img
        self.speed = speed

    def update(self):
        """Updates cloud position"""
        self.pos[0] += self.speed

    def render(self, surf):
        """Renders cloud on surf"""
        surf.blit(self.img, (self.pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(), self.pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height()))

class Clouds:
    """Class representing multiple clouds"""
    def __init__(self, cloud_images, disp_width, disp_height, count=10):
        self.clouds = []
        for _ in range(count):
            self.clouds.append(
                Cloud(
                    pos = (random.random() * disp_width, random.random() * disp_height),
                    img = random.choice(cloud_images),
                    speed = random.random() * 0.05 + 0.05
                )
            )
        self.clouds.sort(key=lambda x: x.speed)

    def update(self):
        """Updates the position of all clouds"""
        for cloud in self.clouds:
            cloud.update()

    def render(self, surf):
        """Renders all clouds on surf"""
        for cloud in self.clouds:
            cloud.render(surf)
