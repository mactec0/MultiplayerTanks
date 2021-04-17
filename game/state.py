from enum import Enum


class STATE(Enum):
    IN_MENU = 0
    WAIT_FOR_START = 1
    IN_GAME = 2
    RESULT = 3
