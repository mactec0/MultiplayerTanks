from utils.utils import get_random_string
from widget.progress_bar import ProgressBar
from widget.button import Button
from widget.slider import Slider
from widget.panel import Panel
from widget.text import Text


class GUI:
    def __init__(self, config):
        self.scenes = {}
        self.init_scenes(config['scenes'])
        self.scene = 'main_menu'
        self.scene_active_widget = None

    def init_widget(self, cfg):
        widgets = {
            'progres_bar': ProgressBar,
            'button': Button,
            'slider': Slider,
            'panel': Panel,
            'text': Text,
        }
        widget_type = next(iter(cfg))

        if widget_type not in widgets:
            return None

        return widgets[widget_type](**cfg[widget_type])

    def control(self, hwnd):
        for key, widget in self.scenes[self.scene].items():
            if self.scene_active_widget is not None \
                    and self.scene_active_widget != key:
                continue

            if widget.control(hwnd):
                self.scene_active_widget = key
                break

            self.scene_active_widget = None

    def draw(self, hwnd):
        for _, widget in self.scenes[self.scene].items():
            widget.draw(hwnd)

    def set_scene(self, scene):
        self.scene = scene
        self.scene_active_widget = None

    def init_scenes(self, config):
        for key, _ in config.items():
            self.scenes[key] = {}
            for widget in config[key]:
                w = self.init_widget(widget)
                if w is None:
                    continue
                widget_type = list(widget.keys())[0]
                widget_id = widget[widget_type]['id'] \
                    if 'id' in widget[widget_type] else get_random_string()
                self.scenes[key][widget_id] = w

    def get_widget(self, id):
        if id not in self.scenes[self.scene]:
            return None

        return self.scenes[self.scene][id]
