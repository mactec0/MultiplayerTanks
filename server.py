#!/usr/bin/env python3
from socket import AF_INET, SOCK_STREAM
from request.request import REQUEST
from threading import Thread, Lock
from time import sleep, perf_counter
from argparse import ArgumentParser
from math import sin, cos, radians
from net.socket import GameSocket
from map.map import Map
import bson
import zlib
import os
from utils.utils import distance, schedule_task, normalize, \
    get_border_positions
from const.const import MAP_H, MAP_W, GRAVITY, MAX_ALLOWED_TURN_TIME


class GameServer:
    def __init__(self, addr):
        self.s = GameSocket(AF_INET, SOCK_STREAM)
        self.s.bind(addr)
        self.lobby = {
            2: [],
            3: [],
            4: [],
        }
        self.clients = []
        self.clients_lock = Lock()
        self.games = []
        self.game_players = {}

    def _handle_games(self):
        for game in self.games:
            try:
                game['mutex'].acquire()
                self._handle_game(game)
            except Exception as e:
                print(f'_handle_games exception {e}')
            finally:
                game['mutex'].release()

        self.games = [game for game in self.games if not game['finished']]

    def _handle_game(self, game):
        if game['finished']:
            active_clients = False
            for client in game['clients']:
                if client is None:
                    continue
                active_clients = True
            if not active_clients:
                del self.games[game]
            return

        alive_logged_count = 0
        alive_id = -1
        logged_count = 0
        i = 0
        for i in range(len(game['clients'])):
            if game['health'][i] > 0 and game['clients'][i] is not None:
                alive_logged_count += 1
                alive_id = i

            if game['clients'][i] is not None:
                logged_count += 1

        if alive_logged_count <= 1:
            schedule_task(self._send_winner_req,
                          (game, alive_id),
                          max(game['last_explode_time'] - perf_counter(), 0))
            game['finished'] = True
        elif logged_count > 1 and alive_logged_count == 0:
            schedule_task(self._send_winner_req,
                          (game, alive_id),
                          max(game['last_explode_time'] - perf_counter(), 0))
            game['finished'] = True
        elif game['clock'] <= perf_counter():
            self._next_turn(game)
            schedule_task(self._send_change_turn_req, game, 0)

    def _next_turn(self, game):
        anyone_live = False
        for hp in game['health']:
            if hp > 0:
                anyone_live = True
                break
        if not anyone_live:
            game['turn'] = -1
            return
        game['turn'] = (game['turn']+1) % game['num_of_players']
        while game['health'][game['turn']] <= 0 or \
                game['clients'][game['turn']] is None:
            game['turn'] = (game['turn']+1) % game['num_of_players']

    def keep_alive(self):
        while True:
            keep_alive_req = {
                'action': REQUEST.KEEP_ALIVE
            }

            self.clients_lock.acquire()
            for client in self.clients:
                try:
                    client.send(bson.dumps(keep_alive_req))
                except Exception as e:
                    print(f'keep_alive exception {e}')
                    self.clients.remove(client)
                    if client in self.game_players:
                        self._remove_user_from_game(client)
                        continue

                    for _, lobby in self.lobby.items():
                        if client not in lobby:
                            continue
                        lobby.remove(client)
                        client.close()
                        break
            self.clients_lock.release()
            sleep(5)

    def handle_new_connections(self):
        self.s.listen()
        while True:
            try:
                sock, addr = self.s.accept()
                sock = GameSocket.from_socket(sock)
                print(f'New connection from :{addr}')
                self.clients_lock.acquire()
                self.clients.append(sock)
                self.clients_lock.release()
                Thread(target=self._handle_client, args=(sock,)).start()
            except Exception as e:
                sock.close()
                print(f'Unkown exception: {e}')

    def main(self):
        while True:
            self._create_new_games()
            self._handle_games()

    def _create_game(self, num_of_players, clients):
        start_positions = {2: [], 3: [], 4: []}
        for key, arr in start_positions.items():
            arr.extend([int(i*(MAP_W/key)) for i in range(key)])

        game_map = Map(MAP_W, MAP_H, True)
        game = {
            'clients': [],
            'positions': start_positions[num_of_players],
            'positions_y': [],
            'mutex': Lock(),
            'num_of_players': num_of_players,
            'collision_map': game_map.collision_noise,
            'health': [100 for x in range(num_of_players)],
            'last_explode_time': 0.0,
            'map': game_map,
            'clock': 0.0,
            'finished': False,
            'turn': 0
        }

        for client in clients:
            game['clients'].append(client)
            join_game_req = {
                'action': REQUEST.JOIN_GAME,
                'map': zlib.compress(
                    bson.dumps({'data': game['collision_map']}), 7),
                'tank_id': clients.index(client),
                'start_x': start_positions[num_of_players]
            }

            client.send(bson.dumps(join_game_req))

        game['map'].create_map(game['collision_map'])
        client_invalid_request = False
        for client in clients:
            data = client.recv()
            if data['action'] != REQUEST.JOIN_GAME:
                client_invalid_request = True

        for pos_x in game['positions']:
            game['positions_y'].append(game['map'].get_height(pos_x))

        if client_invalid_request:
            for client in clients:
                self.clients_lock.acquire()
                self.clients.remove(client)
                self.clients_lock.release()
                client.close()
            return

        self.games.append(game)
        for x in range(num_of_players):
            self.game_players[clients[x]] = self.games[len(self.games) - 1]

        self._send_change_turn_req(game)

    def _send_change_turn_req(self, game):
        if game['turn'] == -1:
            return
        try:
            game['mutex'].acquire()
            game['clock'] = perf_counter() + MAX_ALLOWED_TURN_TIME
            change_turn_req = {
                'action': REQUEST.TURN_CHANGE,
                'tank_id': game['turn']
            }
            self._send_request_to_channel(game, change_turn_req)
        finally:
            game['mutex'].release()

    def _send_winner_req(self, args):
        game = args[0]
        alive_id = args[1]
        try:
            game['mutex'].acquire()
            announce_winner = {
                'action': REQUEST.WINNER_ANNOUNCEMENT,
                'winner': alive_id
            }
            self._send_request_to_channel(game, announce_winner)
        finally:
            game['mutex'].release()

    def _create_new_games(self):
        for key, lobby in self.lobby.items():
            if len(lobby) < key:
                continue
            clients = lobby[:key]
            self.lobby[key] = lobby[key:]

            try:
                self._create_game(key, clients)
            except Exception as e:
                print(f'_create_new_games failed: [{e}]')
                for client in clients:
                    self.clients_lock.acquire()
                    self.clients.remove(client)
                    self.clients_lock.release()
                    client.close()

    def _send_request_to_channel(self, game, data):
        for c in game['clients']:
            if c is None:
                continue
            c.send(bson.dumps(data))

    def _calc_trajectory(self, game, data):
        x = normalize(data['start_x'])
        y = data['start_y']
        dt = 1/240
        t = dt
        px, py = 0, 0
        while not game['map'].check_collision(int(px), int(py)):
            px = normalize(
                x + cos(radians(data['angle'])) * data['velocity'] * t)
            py = y + sin(radians(data['angle'])) * data['velocity'] * t + \
                (GRAVITY*t*t)/2
            t += dt

        if game['map'].check_collision(int(px), int(py)):
            game['map'].explode(int(px), int(py), data['r'])

        data['x'] = px
        data['y'] = py
        return data, t

    def _calc_damage(self, x, y, data):
        positions = get_border_positions(x, 50)
        dmg = []
        for x in positions:
            r = data['r']  # bomb radius
            r2 = 8  # tank radius
            dist = distance(x, y, data['x'], data['y']) + r2
            if dist > r*2:
                dmg.append(0)
                continue
            dmg.append(min(100, 100*(r*.4/dist)))
        dmg.sort(reverse=True)
        return dmg[0]

    def _send_missle(self, client, game, data):
        data, time = self._calc_trajectory(game, data)

        if game['clients'].index(client) != game['turn']:
            print('Invalid player sent missle')
            return

        self._send_request_to_channel(game, data)

        for i in range(game['num_of_players']):
            dmg = self._calc_damage(
                game['positions'][i], game['positions_y'][i], data)
            if dmg == 0:
                continue
            game['health'][i] = max(0, game['health'][i] - dmg)
            dmg_alert = {
                'action': REQUEST.DMG_ALERT,
                'tank_id': i,
                'health': game['health'][i]
            }
            self._send_request_to_channel(game, dmg_alert)

        game['clock'] = perf_counter() + MAX_ALLOWED_TURN_TIME
        game['last_explode_time'] = perf_counter() + time + 1
        self._next_turn(game)
        schedule_task(self._send_change_turn_req, game, time + 1)

    def _send_pos(self, client, game, data):
        game['positions'][game['clients'].index(client)] = data['x']
        game['positions_y'][game['clients'].index(client)] = data['y']
        for c in game['clients']:
            if client == c or c is None:
                continue
            c.send(bson.dumps(data))

    def _end_turn(self, client, game, data):
        self._next_turn(game)
        schedule_task(self._send_change_turn_req, game, 0)

    def _process_packet(self, client, data):
        pkt_callbacks = {
            REQUEST.SEND_POS: self._send_pos,
            REQUEST.SEND_MISSLE: self._send_missle,
            REQUEST.END_TURN: self._end_turn
        }

        if data['action'] not in pkt_callbacks:
            return

        game = self.game_players[client]
        try:
            game['mutex'].acquire()
            pkt_callbacks[data['action']](client, game, data)
        except Exception as e:
            print(f'pkt_callbacks exception [{e}]')
        finally:
            game['mutex'].release()

    def _handle_client(self, client):
        try:
            data = client.recv()
            if data['action'] != REQUEST.JOIN_LOBBY or \
                    data['num_of_players'] not in self.lobby:
                client.close()
                return

            self.lobby[data['num_of_players']].append(client)

            while client not in self.game_players:
                sleep(0.2)
                if client not in self.clients:
                    return

            while True:
                data = client.recv()
                self._process_packet(client, data)
        except Exception as e:
            print(f'Client disconnected: [{e}]')
            self.clients_lock.acquire()
            self._remove_user_from_game(client)
            self.clients_lock.release()

    def _remove_user_from_game(self, client):
        self.clients.remove(client)
        game = self.game_players[client]
        try:
            game['mutex'].acquire()
            game['clients'] = [c if c != client else None
                               for c in game['clients']]
            client.close()
        finally:
            game['mutex'].release()
        del self.game_players[client]


if __name__ == "__main__":
    parser = ArgumentParser(description="Game server")
    parser.add_argument(
        "-L", "--ip", help="Server ip addr", type=str, default='127.0.0.1')
    parser.add_argument(
        "-p", "--port", help="Port number to listen on",
        type=int, default=30203)
    argv = parser.parse_args()

    server = GameServer((argv.ip, argv.port))
    Thread(target=server.handle_new_connections).start()
    Thread(target=server.keep_alive).start()
    Thread(target=server.main).start()
    print('Server started succesfully')

    while True:
        try:
            x = input()
            if x == 'q':
                server.clients_lock.acquire()
                for c in server.clients:
                    c.close()
                server.clients_lock.release()
                server.s.close()
                os._exit(0)
        except Exception as e:
            print(f'[{e}]')
            server.s.close()
            os._exit(1)
