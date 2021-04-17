from utils.sf_utils import get_mouse_pos
from widget.widget import Widget
from sfml import sf


class Button(Widget):
    def __init__(self, id, x, y, texture):
        super().__init__()
        self.id = id
        self.texture = sf.Texture.from_file(texture)
        self.sprite = sf.Sprite(self.texture)
        self.sprite.position = (x, y)
        self.x = x
        self.y = y
        self.w = self.sprite.local_bounds.width
        self.h = self.sprite.local_bounds.height
        self.clicked = False
        self.enabled = True

    def draw(self, hwnd):
        if self.clicked or not self.enabled:
            self.sprite.color = sf.Color(200, 200, 200)
        else:
            self.sprite.color = sf.Color(255, 255, 255)
        hwnd.draw(self.sprite)

    def control(self, hwnd):
        mx, my = get_mouse_pos(hwnd)
        if sf.Mouse.is_button_pressed(0) and \
                mx >= self.x and \
                my >= self.y and \
                mx < self.x + self.w and \
                my < self.y + self.h:
            self.clicked = True

        if not self.enabled and self.clicked:
            self.clicked = False
            return True
        elif not sf.Mouse.is_button_pressed(0):
            self.enabled = True

        return self.clicked

    def is_clicked(self):
        return self.clicked

    def disable(self):
        self.clicked = False
        self.enabled = False
