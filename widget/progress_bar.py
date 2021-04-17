from utils.sf_utils import create_rect
from widget.widget import Widget
from sfml import sf


class ProgressBar(Widget):
    def __init__(self, id, x, y, w, h, value=1.0):
        super().__init__()
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.value = value
        self.reset()

    def reset(self):
        self.rect_1 = create_rect(self.x - 2, self.y - 2,
                                  self.w + 4, self.h + 4,
                                  sf.Color(100, 100, 100))

        bar_len = self.h*self.value
        self.rect_2 = create_rect(self.x, self.y + self.h - bar_len,
                                  self.w, bar_len, sf.Color(5, 102, 17))

    def draw(self, hwnd):
        hwnd.draw(self.rect_1)
        hwnd.draw(self.rect_2)

    def control(self, hwnd):
        pass
