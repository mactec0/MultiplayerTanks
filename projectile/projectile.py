from texture_manager.texture_manager import texture_manager, TEXTURE
from math import radians, sin, cos
from utils.utils import normalize
from const.const import GRAVITY
from sfml import sf


class Projectile:
    def __init__(self, map, x, y, angle, vel, final_pos=None):
        self.map = map
        self.texture = texture_manager.textures[TEXTURE.MISSLE]
        self.sprite = sf.Sprite(self.texture)
        self.sprite.origin = (2, 2)
        self.enemy_missle = True if final_pos is not None else False
        self.final_pos = final_pos
        self.start_x = normalize(x)
        self.start_y = y
        self.x = self.start_x
        self.y = y
        self.angle = radians(angle)
        self.vel = vel
        self.clock = None
        self.should_remove = False
        self.r = 24
        self.t = 0

    def control(self, dt):
        if self.should_remove:
            return

        if self.map.check_collision(int(self.x), int(self.y)):
            if self.final_pos is not None:
                self.x = self.final_pos[0]
                self.y = self.final_pos[1]
                self.final_pos = None
            self.map.explode(int(self.x), int(self.y), self.r)
            self.should_remove = True
            return

        self.t += dt
        self.x = normalize(self.start_x + cos(self.angle) * self.vel * self.t)
        self.y = self.start_y + sin(self.angle) * self.vel * self.t + \
            0.5*(GRAVITY*self.t*self.t)
        self.sprite.rotate(dt*180)

    def draw(self, hwnd, map_scroll):
        x = normalize(self.x + map_scroll)
        self.sprite.position = (x, self.y)
        hwnd.draw(self.sprite)
