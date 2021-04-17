from widget.widget import Widget
from sfml import sf


class Panel(Widget):
    def __init__(self, x, y, texture):
        self.texture = sf.Texture.from_file(texture)
        self.sprite = sf.Sprite(self.texture)
        self.sprite.position = (x, y)

    def draw(self, hwnd):
        hwnd.draw(self.sprite)

    def control(self, hwnd):
        pass
