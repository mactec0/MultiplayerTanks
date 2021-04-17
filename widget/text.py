from widget.widget import Widget
from sfml import sf


class Text(Widget):
    def __init__(self, id, x, y, text, font, color=[25, 25, 25], size=20):
        self.font = sf.Font.from_file(font)
        self.text = sf.Text()
        self.text.font = self.font
        self.text.string = text
        self.text.character_size = 20
        self.text.color = sf.Color(color[0], color[1], color[2])
        self.text.position = (x, y)

    def draw(self, hwnd):
        hwnd.draw(self.text)
        pass

    def control(self, hwnd):
        pass
