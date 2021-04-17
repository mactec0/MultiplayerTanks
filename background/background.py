from sfml import sf
from const.const import SCREEN_H, SCREEN_W


class Background:
    scroll_speed = 30

    def __init__(self, texture):
        self.bg = sf.Sprite(texture)
        self.size = self.bg.local_bounds.width
        self.scroll = 0

    def control(self, dt):
        self.scroll += dt * self.scroll_speed
        while self.scroll >= self.size:
            self.scroll -= self.size

    def draw(self, hwnd):
        y = -self.scroll
        while y < SCREEN_H:
            x = -self.scroll
            while x < SCREEN_W:
                self.bg.position = (x, y)
                hwnd.draw(self.bg)
                x += self.size
            y += self.size
