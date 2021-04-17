from utils.utils import clamp, distance, normalize, get_border_positions
from perlin_noise import PerlinNoise
from const.const import MAP_W, MAP_H
from random import uniform


class Map:
    def __init__(self, w, h, generate_map=False):
        self.width = w
        self.height = h
        self.gnoise = [[uniform(0, 1) for x in range(255)] for y in range(255)]
        if generate_map:
            self._generate_map()

    def create_map(self, collision_noise):
        self.collision_map = [
            [False for x in range(MAP_W)] for y in range(MAP_H)]

        for x in range(MAP_W):
            for y in range(collision_noise[x], MAP_H):
                self.collision_map[y][x] = True

    def get_height(self, x, sy=0):
        x = normalize(x)
        h = sy
        for y in range(sy, MAP_H):
            if self.collision_map[y][x]:
                return h
            h += 1
        return h

    def check_collision(self, x, y):
        if x < 0 or \
                y < 0 or \
                x >= self.width or \
                y >= self.height:
            return False

        return self.collision_map[y][x]

    def explode(self, x, y, r):
        positions = get_border_positions(x, 50)
        for x in positions:
            for py in range(max(y - r, 0), min(y + r, MAP_H)):
                for px in range(max(x - r, 0), min(x + r, MAP_W)):
                    if distance(x, y, px, py) >= r:
                        continue
                    self.collision_map[py][px] = False

    def _generate_map(self):
        map_margin = 32
        mid_y = int(MAP_H/2)
        noise1 = PerlinNoise(octaves=4)
        noise2 = PerlinNoise(octaves=12)
        noise3 = PerlinNoise(octaves=16)
        self.collision_noise = [0 for x in range(MAP_W)]

        for x in range(MAP_W):
            n = noise1([0, x/MAP_W]) + \
                0.5 * noise2([0, x/MAP_W]) + \
                0.25 * noise3([0, x/MAP_W])

            y2 = clamp(mid_y+n*200, map_margin, MAP_H - map_margin)
            self.collision_noise[x] = int(y2)
