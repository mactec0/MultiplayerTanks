from projectile.projectile import Projectile
from game.state import STATE


def update_pos_callback(game, data):
    game.tanks[data['tank_id']].final_x = data['x']
    game.tanks[data['tank_id']].aim_angle = data['aim_angle']


def recv_missle_callback(game, data):
    game.projectiles.append(Projectile(
        game.map, data['start_x'], data['start_y'], data['angle'],
        data['velocity'], (data['x'], data['y'])))


def turn_change_callback(game, data):
    if data['tank_id'] == game.tank_id:
        game.tanks[game.tank_id].move_limit = 100
        w = game.ui.get_widget('fuel_bar')
        w.value = game.tanks[game.tank_id].move_limit/100
        w.reset()
        game.turn.restart()


def dmg_alert_callback(game, data):
    game.tanks[data['tank_id']].health = data['health']
    game.tanks[data['tank_id']]._redraw_healthbar()


def winner_announcement_callback(game, data):
    game.winner = data['winner']
    game.ui.set_scene('results')
    game.state = STATE.RESULT
    game.timer.restart()
    game.s.close()
    if data['winner'] != -1:
        game.ui.get_widget(
            'results_text').text.string = f'Player {data["winner"] + 1} won!'
    else:
        game.ui.get_widget('results_text').text.string = 'No one won'

    game.finished = True
