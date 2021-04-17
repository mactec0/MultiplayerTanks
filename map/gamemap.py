from texture_manager.texture_manager import texture_manager, TEXTURE
from const.const import MAP_W, MAP_H
from utils.utils import distance, get_border_positions
from map.map import Map
from sfml import sf


class GameMap(Map):
    def __init__(self, w, h):
        super().__init__(w, h)

    def draw(self, hwnd, map_scroll):
        start_x = map_scroll if map_scroll < 0 else map_scroll - MAP_W
        for x in range(2):
            self.map_sprite.position = (start_x, 0)
            hwnd.draw(self.map_sprite)
            start_x += MAP_W

    def create_map(self, collision_map):
        self.map_img = sf.Image.create(
            self.width, self.height, sf.Color(0, 0, 0, 0))
        self.map_pixels = list(self.map_img.pixels)
        self.map_tex = sf.Texture.from_image(self.map_img)
        self.map_sprite = sf.Sprite(self.map_tex)

        land_img = []
        land_px = []
        for i in range(5):
            land_img.append(
                texture_manager.
                textures[TEXTURE.LAND_1.value+i].copy_to_image())
            land_px.append(list(land_img[i].pixels))

        self.collision_map = [
            [False for x in range(MAP_W)] for y in range(MAP_H)]

        for x in range(MAP_W):
            for y in range(collision_map[x], MAP_H):
                self.collision_map[y][x] = True
                depth = y - collision_map[x] + 1
                depth = 0 if depth < 11 else int(depth/28)+1
                depth = min(depth, 4)

                if y - collision_map[x] < 2:
                    self.map_pixels[(y*MAP_W + x)*4 + 0] = b'\x0f'
                    self.map_pixels[(y*MAP_W + x)*4 + 1] = b'\x0f'
                    self.map_pixels[(y*MAP_W + x)*4 + 2] = b'\x0f'
                    self.map_pixels[(y*MAP_W + x)*4 + 3] = b'\xA0'
                else:
                    self.map_pixels[(y*MAP_W + x)*4 +
                                    0] = land_px[depth][(y*MAP_W + x)*4 + 0]
                    self.map_pixels[(y*MAP_W + x)*4 +
                                    1] = land_px[depth][(y*MAP_W + x)*4 + 1]
                    self.map_pixels[(y*MAP_W + x)*4 +
                                    2] = land_px[depth][(y*MAP_W + x)*4 + 2]
                    self.map_pixels[(y*MAP_W + x)*4 + 3] = b'\xff'

        self.map_img = sf.Image.from_pixels(
            MAP_W, MAP_H, b''.join(self.map_pixels))
        self.map_tex = sf.Texture.from_image(self.map_img)
        self.map_sprite.texture = self.map_tex

    def explode(self, x, y, r):
        positions = get_border_positions(x, 50)
        for x in positions:
            for py in range(max(y - r, 0), min(y + r, MAP_H)):
                for px in range(max(x - r, 0), min(x + r, MAP_W)):
                    if distance(x, y, px, py) >= r:
                        continue
                    self.collision_map[py][px] = False
                    self.map_pixels[(py*MAP_W + px)*4 + 3] = b'\x00'

        self.map_img = sf.Image.from_pixels(
            MAP_W, MAP_H, b''.join(self.map_pixels))
        self.map_tex = sf.Texture.from_image(self.map_img)
        self.map_sprite.texture = self.map_tex
