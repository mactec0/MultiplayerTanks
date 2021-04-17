from utils.utils import clamp
from utils.sf_utils import create_rect, get_mouse_pos
from widget.widget import Widget
from sfml import sf


class Slider(Widget):
    def __init__(self, id, x, y, w, default=50):
        super().__init__()
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.slider_x = x + int(w*(default/100.0))
        self.last_slider_x = self.slider_x

        self.rect_1 = create_rect(
            self.x, self.y + 4, self.w, 4, sf.Color(25, 25, 25))
        self.rect_2 = create_rect(
            self.x, self.y, 3, 12, sf.Color(200, 200, 200))
        self.rect_2.origin = (1, 0)
        self.clicked = False

    def value_changed(self):
        if self.slider_x != self.last_slider_x:
            self.last_slider_x = self.slider_x
            return True
        return False

    def get_value(self):
        return (self.slider_x - self.x) / self.w

    def set_value(self, v):
        self.slider_x = self.w*v

    def draw(self, hwnd):
        self.rect_1.position = (self.x, self.y+4)
        self.rect_2.position = (self.slider_x, self.y)
        hwnd.draw(self.rect_1)
        hwnd.draw(self.rect_2)

    def control(self, hwnd):
        mx, my = get_mouse_pos(hwnd)
        if sf.Mouse.is_button_pressed(0) and \
                mx >= self.x and \
                my >= self.y and \
                mx < self.x + self.w and \
                my < self.y + 12:
            self.clicked = True

        if not sf.Mouse.is_button_pressed(0):
            self.clicked = False

        if self.clicked:
            self.slider_x = clamp(mx, self.x, self.x + self.w - 1)

        return self.clicked
