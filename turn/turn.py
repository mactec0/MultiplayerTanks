from sfml import sf


class GameTurn:
    def __init__(self):
        self.timer = sf.Clock()
        self.my_turn = False
        self.last_turn = False
        self.time_limit = 45

    def restart(self):
        self.my_turn = True
        self.last_turn = True
        self.timer.restart()

    def finished(self):
        if not self.my_turn and self.last_turn:
            self.last_turn = False
            return True
        return False

    def end(self, ui):
        self.my_turn = False
        self.last_turn = False
        ui.get_widget('turn_text').text.string = ' '

    def control(self, ui):
        if not self.my_turn:
            ui.get_widget('turn_text').text.string = ' '
            return

        left = self.time_left()
        if left <= 0:
            ui.get_widget('turn_text').text.string = ' '
            self.my_turn = False
            return

        ui.get_widget('turn_text').text.string = \
            f'Your turn, time left: {left:.1f}s'

    def time_left(self):
        if not self.my_turn:
            return 0
        return self.time_limit - min(self.timer.elapsed_time.seconds,
                                     self.time_limit)
