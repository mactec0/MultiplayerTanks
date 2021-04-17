from enum import Enum
from sfml import sf


class TEXTURE(Enum):
    TANK_1 = 1
    TANK_2 = 2
    TANK_3 = 3
    TANK_4 = 4
    CROSSHAIR = 5
    BARREL = 6
    MISSLE = 7
    LAND_1 = 8
    LAND_2 = 9
    LAND_3 = 10
    LAND_4 = 11
    LAND_5 = 12
    BACKGROUND = 13
    LANDSCAPE = 14


class TextureManager:
    def __init__(self):
        self.textures = {}
        self.textures[TEXTURE.CROSSHAIR] = sf.Texture.from_file(
            './data/gfx/crosshair.png')
        self.textures[TEXTURE.BARREL] = sf.Texture.from_file(
            './data/gfx/barrel.png')
        self.textures[TEXTURE.MISSLE] = sf.Texture.from_file(
            './data/gfx/missle.png')
        self.textures[TEXTURE.BACKGROUND] = sf.Texture.from_file(
            './data/gfx/bg.png')
        self.textures[TEXTURE.LANDSCAPE] = sf.Texture.from_file(
            './data/gfx/landscape.png')

        self.textures.update({i:
                              sf.Texture.from_file(f'./data/gfx/tank{i}.png')
                              for i in range(1, 5)})
        self.textures.update({TEXTURE.LAND_1.value + i - 1:
                              sf.Texture.from_file(f'./data/gfx/land_{i}.png')
                              for i in range(1, 6)})


texture_manager = TextureManager()
