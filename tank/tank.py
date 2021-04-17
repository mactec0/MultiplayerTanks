from math import atan2, degrees, radians, sin, cos
from const.const import MAP_W, MAP_H
from utils.utils import lerp, normalize, get_border_positions
from utils.sf_utils import create_rect
from texture_manager.texture_manager import texture_manager, TEXTURE
from enum import Enum
from sfml import sf


class TANK_TYPE(Enum):
    TANK_1 = 1
    TANK_2 = 2
    TANK_3 = 3
    TANK_4 = 4


class Tank:
    VELOCITY = 65

    def __init__(self, tank_type, map, start_x=100):
        self.type = tank_type
        self.crosshair_tex = texture_manager.textures[TEXTURE.CROSSHAIR]
        self.crosshair_sprite = sf.Sprite(self.crosshair_tex)
        self.crosshair_sprite.origin = (7, 7)
        self.barrel_tex = texture_manager.textures[TEXTURE.BARREL]
        self.barrel_sprite = sf.Sprite(self.barrel_tex)
        self.barrel_sprite.origin = (1, 6)
        self.texture = texture_manager.textures[tank_type]
        self.sprite = sf.Sprite(self.texture)
        self.sprite.origin = (11, 4)
        self.aim_angle = -90
        self.last_aim_angle = self.aim_angle
        self.map = map
        self.x = start_x
        self.last_x = 0
        self.y = map.get_height(self.x)
        self.final_x = -1
        self.health = 100
        self._redraw_healthbar()

    def _redraw_healthbar(self):
        self.bar_green_len = int(10*max(self.health, 0)/100)
        self.bar_green = create_rect(
            0, 0, self.bar_green_len, 2, sf.Color(0, 140, 0))
        self.bar_red = create_rect(
            self.bar_green_len, 0, 10-self.bar_green_len, 2,
            sf.Color(130, 0, 0))
        if self.health == 0:
            self.sprite.color = sf.Color(100, 100, 100, 150)

    def control(self, dt):
        self.crosshair_sprite.rotate(dt*45)

        if self.aim_angle != self.last_aim_angle:
            self.barrel_sprite.rotate(
                self.aim_angle - self.barrel_sprite.rotation + 90)
            self.changed_pos = True
            self.last_aim_angle = self.aim_angle

        if self.x != self.last_x:
            self.changed_pos = True
            self.new_y = -1
            for y in range(max(self.y - 5, 0), MAP_H):
                if not self.map.collision_map[y-1][int(self.x)] and \
                        self.map.collision_map[y][int(self.x)]:
                    self.new_y = y
                    break

            if self.new_y == -1 and self.final_x == -1:
                self.x = self.last_x
                return

            self.y = self.new_y

            p1 = (self.x - 4, self.map.get_height(normalize(int(self.x) - 4),
                                                  normalize(int(self.y - 5))))
            p2 = (self.x + 4, self.map.get_height(normalize(int(self.x) + 4),
                                                  normalize(int(self.y - 5))))

            angle = degrees(atan2(p2[1] - p1[1], p2[0] - p1[0]))
            self.sprite.rotate(angle - self.sprite.rotation)
        else:
            self.new_y = -1
            for y in range(max(self.y - 5, 0), MAP_H):
                if not self.map.collision_map[y-1][int(self.x)] and \
                        self.map.collision_map[y][int(self.x)]:
                    self.new_y = y
                    break

            if self.new_y != self.y:
                self.y = self.new_y
                p1 = (self.x - 4, self.map.get_height(int(self.x) - 4,
                                                      int(self.y - 5)))
                p2 = (self.x + 4, self.map.get_height(int(self.x) + 4,
                                                      int(self.y - 5)))

                angle = degrees(atan2(p2[1] - p1[1], p2[0] - p1[0]))
                self.sprite.rotate(angle - self.sprite.rotation)

        self.last_x = self.x

    def draw(self, hwnd, map_scroll):
        x = normalize(self.x + map_scroll)
        positions = get_border_positions(x, 50)

        for x in positions:
            self.bar_green.position = (x-5, self.y-22)
            self.bar_red.position = (x-5+self.bar_green_len, self.y-22)
            self.barrel_sprite.position = (x, self.y-10)
            self.sprite.position = (x, self.y-8)
            self.crosshair_sprite.position = (
                x + 35*cos(radians(self.aim_angle)),
                self.y - 12 + 35*sin(radians(self.aim_angle)))
            hwnd.draw(self.barrel_sprite)
            hwnd.draw(self.sprite)
            hwnd.draw(self.bar_green)
            hwnd.draw(self.bar_red)

            self.rect = create_rect(
                x-1, self.y-1, 2, 2, sf.Color(255, 255, 255))
            hwnd.draw(self.rect)


class NetworkPlayerTank(Tank):
    def __init__(self, tank_type, map, start_x):
        super().__init__(tank_type, map, start_x)
        self.final_x = self.x

    def control(self, dt):
        if self.final_x > self.x + 500:
            self.final_x -= MAP_W
        if self.x > self.final_x + 500:
            self.final_x += MAP_W

        if self.x != self.final_x:
            self.x = normalize(lerp(self.x, self.final_x, dt*7))
        super().control(dt)


class PlayerTank(Tank):
    def __init__(self, tank_type, map, start_x):
        super().__init__(tank_type, map, start_x)
        self.move_limit = 100.0
        self.changed_pos = False
        self.angle = 0

    def moved(self):
        ret = self.changed_pos
        self.changed_pos = False
        return ret

    def move(self, dt):
        if self.move_limit <= 0:
            return

        move_amount = dt*Tank.VELOCITY

        if sf.Keyboard.is_key_pressed(sf.Keyboard.A):
            self.x -= move_amount
            self.move_limit -= abs(move_amount)

        if sf.Keyboard.is_key_pressed(sf.Keyboard.D):
            self.x += move_amount
            self.move_limit -= abs(move_amount)

        self.x = normalize(self.x)

    def control(self, dt):
        super().control(dt)

    def draw(self, hwnd, map_scroll):
        super().draw(hwnd, map_scroll)
        hwnd.draw(self.crosshair_sprite)
