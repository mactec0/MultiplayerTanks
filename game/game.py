#!/usr/bin/env python3
from request.callbacks import update_pos_callback, \
    recv_missle_callback, turn_change_callback, \
    dmg_alert_callback, winner_announcement_callback
from threading import Thread
from texture_manager.texture_manager import texture_manager, TEXTURE
from utils.utils import normalize
from utils.sf_utils import create_rect
from const.const import SCREEN_H, SCREEN_W, GRAVITY, MAP_W, MAP_H, \
    SCREEN_CENTER
from map.gamemap import GameMap
from tank.tank import NetworkPlayerTank, PlayerTank
from background.background import Background
from request.request import REQUEST
from net.socket import GameSocket
from turn.turn import GameTurn
from game.state import STATE
from gui.gui import GUI

from socket import AF_INET, SOCK_STREAM
from math import radians, sin, cos
from time import sleep
from sfml import sf
import bson
import zlib
import yaml
import os


class Game:
    def __init__(self):
        self.s = None
        self.width = SCREEN_W
        self.height = SCREEN_H
        self.hwnd_context = sf.ContextSettings()
        self.hwnd_context.antialiasing_level = 4
        self.hwnd = sf.RenderWindow(sf.VideoMode(
            self.width, self.height), "Tankz2D", sf.Style.DEFAULT,
            self.hwnd_context)
        self.hwnd.framerate_limit = 60
        self.hwnd.vertical_synchronization = True
        self.state = STATE.IN_MENU
        self.turn = GameTurn()
        self.tank_sprites = [0]*4
        self.winner = -1
        self.map_scroll = 0
        for x in range(4):
            self.tank_sprites[x] = sf.Sprite(texture_manager.textures[x+1])
            self.tank_sprites[x].origin = (11, 6)
            self.tank_sprites[x].position = (SCREEN_W/2, SCREEN_H/2)
            self.tank_sprites[x].scale((16, 16))

        try:
            with open('./data/cfg.yaml', 'r') as stream:
                self.cfg = yaml.safe_load(stream)
        except Exception as e:
            print(f'reading config failed: [{e}]')
            os._exit(-1)

        self.ui = GUI(self.cfg['ui'])
        self.ui.set_scene('main_menu')

        self.map = None
        self.map = GameMap(MAP_W, MAP_H)
        self.tanks = []
        self.tank_id = 0
        self.timer = sf.Clock()
        self.timer.restart()

        self.finished = False

        self.bg = Background(texture_manager.textures[TEXTURE.BACKGROUND])
        self.landscape = sf.Sprite(texture_manager.textures[TEXTURE.LANDSCAPE])

        self.think_callbacks = {
            STATE.IN_MENU: self.menu_callback,
            STATE.WAIT_FOR_START: self.wait_for_start_callback,
            STATE.IN_GAME: self.ingame_callback,
            STATE.RESULT: self.results_callback,
        }
        self.render_callbacks = {
            STATE.IN_MENU: self.menu_render_callback,
            STATE.WAIT_FOR_START: self.wait_for_start_render_callback,
            STATE.IN_GAME: self.ingame_render_callback,
            STATE.RESULT: self.results_render_callback
        }

        self.projectiles = []

        self.cheat_active = False

    def loop(self):
        clock = sf.Clock()
        while self.hwnd.is_open:
            dt = clock.restart()
            self._think(dt.seconds)

            self.hwnd.clear(sf.Color(18, 176, 255))

            self._render()

            self.hwnd.display()

    def _think(self, dt):
        if sf.Keyboard.is_key_pressed(sf.Keyboard.ESCAPE) \
                and self.hwnd.has_focus():
            self.state = STATE.IN_MENU
            self.timer.restart()
            self.s.close()
            self.ui.set_scene('main_menu')
            self.state = STATE.IN_MENU
            self.finished = True
            return

        for event in self.hwnd.events:
            if event == sf.Event.CLOSED:
                self.hwnd.close()
                os._exit(-1)

        if self.state in self.think_callbacks:
            self.think_callbacks[self.state](dt)

    def _render(self):
        self.hwnd.clear(sf.Color(18, 176, 255))

        if self.state in self.render_callbacks:
            self.render_callbacks[self.state](())

        self.ui.draw(self.hwnd)

    def _handle_connection(self, num_of_players):
        try:
            self.s = GameSocket(AF_INET, SOCK_STREAM)
            self.s.connect((self.cfg['server']['ip'], self.cfg['server']['port']))
            self.ui.get_widget('status_text').text.string = 'Joining lobby...'
            join_lobby_req = {
                'action': REQUEST.JOIN_LOBBY,
                'num_of_players': num_of_players
            }
            self.s.send(bson.dumps(join_lobby_req))
            self.ui.get_widget(
                'status_text').text.string = 'Waiting for players...'

            data = self.s.recv()
            if data['action'] != REQUEST.JOIN_GAME:
                self.s.close()
                self.ui.set_scene('main_menu')
                self.state = STATE.IN_MENU
                return

            data['map'] = bson.loads(zlib.decompress(data['map']))['data']

            self.ui.get_widget(
                'status_text').text.string = 'Reconstructing map...'
            self.map.create_map(data['map'])
            self.tank_id = data['tank_id']

            self.tanks = [PlayerTank(x+1, self.map, data['start_x'][x])
                          if x == self.tank_id else
                          NetworkPlayerTank(x+1, self.map, data['start_x'][x])
                          for x in range(num_of_players)]

            join_game_req = {
                'action': REQUEST.JOIN_GAME
            }
            self.projectiles = []
            self.s.send(bson.dumps(join_game_req))
            self.turn = GameTurn()
            self.ui.set_scene('in_game')
            self.state = STATE.IN_GAME
            self.finished = False
            self.timer.restart()

            while not self.finished:
                data = self.s.recv()
                self._process_packet(data)

        except Exception as e:
            print(f'connecting to server failed {e}')
            self.s.close()
            self.ui.set_scene('main_menu')
            self.state = STATE.IN_MENU

    def _send_position(self):
        if self.tanks[self.tank_id].moved():
            w = self.ui.get_widget('fuel_bar')
            w.value = self.tanks[self.tank_id].move_limit/100
            w.reset()
            send_pos_req = {
                'action': REQUEST.SEND_POS,
                'x': self.tanks[self.tank_id].x,
                'y': self.tanks[self.tank_id].y,
                'aim_angle': self.tanks[self.tank_id].aim_angle,
                'tank_id': self.tank_id
            }
            self.s.send(bson.dumps(send_pos_req))

    def _process_packet(self, data):
        pkt_callbacks = {
            REQUEST.SEND_POS: update_pos_callback,
            REQUEST.SEND_MISSLE: recv_missle_callback,
            REQUEST.TURN_CHANGE: turn_change_callback,
            REQUEST.DMG_ALERT: dmg_alert_callback,
            REQUEST.WINNER_ANNOUNCEMENT: winner_announcement_callback
        }

        if data['action'] not in pkt_callbacks:
            return
        pkt_callbacks[data['action']](self, data)

    """ Callbacks """

    def menu_callback(self, dt):
        if self.hwnd.has_focus():
            self.ui.control(self.hwnd)

        self.bg.control(dt)

        if self.ui.get_widget('quit_button').is_clicked():
            os._exit(0)

        num_of_players = None
        start_buttons = [
            (self.ui.get_widget('players_2_button'), 2),
            (self.ui.get_widget('players_3_button'), 3),
            (self.ui.get_widget('players_4_button'), 4),
        ]

        for w, n in start_buttons:
            if not w.is_clicked():
                continue
            w.disable()
            num_of_players = n
            break

        if num_of_players is None:
            return

        Thread(target=self._handle_connection, args=(num_of_players,)).start()
        self.ui.set_scene('in_lobby')
        self.state = STATE.WAIT_FOR_START
        self.ui.get_widget(
            'status_text').text.string = 'Connecting to server..'

    def menu_render_callback(self, args):
        self.bg.draw(self.hwnd)

    def wait_for_start_callback(self, dt):
        self.bg.control(dt)
        if self.hwnd.has_focus():
            self.ui.control(self.hwnd)

    def wait_for_start_render_callback(self, dt):
        self.bg.draw(self.hwnd)

    def ingame_callback(self, dt):
        self.map_scroll = SCREEN_CENTER - self.tanks[self.tank_id].x
        if self.hwnd.has_focus() and self.turn.my_turn:
            self.ui.control(self.hwnd)

        if self.turn.finished():
            end_turn_req = {
                'action': REQUEST.END_TURN
            }
            self.s.send(bson.dumps(end_turn_req))

        w = self.ui.get_widget('angle_slider')
        if w.value_changed():
            self.tanks[self.tank_id].aim_angle = w.get_value()*360 - 270

        if self.hwnd.has_focus() and self.turn.my_turn:
            self.tanks[self.tank_id].move(dt)

        for tank in self.tanks:
            tank.control(dt)

        w = self.ui.get_widget('fire_button')
        if w.is_clicked():
            self.turn.end(self.ui)
            w.disable()
            w = self.ui.get_widget('power_slider')
            send_missle_req = {
                'action': REQUEST.SEND_MISSLE,
                'start_x': self.tanks[self.tank_id].x,
                'start_y': self.tanks[self.tank_id].y - 11,
                'angle': self.tanks[self.tank_id].aim_angle,
                'velocity': w.get_value()*540,
                'r': 24
            }
            self.s.send(bson.dumps(send_missle_req))

        for projectile in self.projectiles:
            projectile.control(dt)

        self.turn.control(self.ui)

        self.projectiles = [p for p in self.projectiles if not p.should_remove]

        if self.timer.elapsed_time.seconds > 0.166:
            self._send_position()
            self.timer.restart()

    def ingame_render_callback(self, args):
        start_x = self.map_scroll if self.map_scroll < 0 \
            else self.map_scroll - MAP_W
        for _ in range(2):
            self.landscape.position = (start_x, 0)
            self.hwnd.draw(self.landscape)
            start_x += MAP_W
        self.map.draw(self.hwnd, self.map_scroll)
        for tank in self.tanks:
            tank.draw(self.hwnd, self.map_scroll)

        self._show_trajectory()

        for projectile in self.projectiles:
            projectile.draw(self.hwnd, self.map_scroll)

    def results_callback(self, dt):
        self.bg.control(dt)
        if self.timer.elapsed_time.seconds > 5:
            self.ui.set_scene('main_menu')
            self.state = STATE.IN_MENU

    def results_render_callback(self, args):
        self.bg.draw(self.hwnd)
        if self.winner != -1:
            self.hwnd.draw(self.tank_sprites[self.winner])

    """ CHEATS """

    def _calc_trajectory(self, x, y, fps=60, draw=False):
        rect = create_rect(0, 0, 2, 2, sf.Color(0, 0, 0, 50))

        x = normalize(x)
        y = y
        px, py = 0, 0
        dt = 1/fps
        t = dt
        angle = self.tanks[self.tank_id].aim_angle
        w = self.ui.get_widget('power_slider')
        if w is None:
            return
        velocity = w.get_value()*540
        while not self.map.check_collision(int(px), int(py)):
            px = normalize(x + cos(radians(angle)) * velocity * t)
            py = y + sin(radians(angle)) * velocity * t + \
                0.5*(GRAVITY*t*t)

            t += dt
            if draw:
                rect.position = (normalize(px+self.map_scroll)-1, py-1)
                self.hwnd.draw(rect)
        return (px, py)

    def _show_trajectory(self):
        if sf.Keyboard.is_key_pressed(sf.Keyboard.M) and \
                self.hwnd.has_focus():
            self.cheat_active = not self.cheat_active
            sleep(0.5)

        if self.cheat_active:
            x, y = self._calc_trajectory(
                self.tanks[self.tank_id].x,
                self.tanks[self.tank_id].y-11,
                60, True)
            x = normalize(x + self.map_scroll)
            rect = create_rect(x-2, y-2, 4, 4, sf.Color.CYAN)
            self.hwnd.draw(rect)
