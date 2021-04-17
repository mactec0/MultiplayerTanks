from socket import socket
from const.const import MAX_PKT_SIZE
from request.request import REQUEST
from threading import Lock
import bson


class BrokenSocket(Exception):
    def __init__(self):
        super().__init__("broken socket")


class GameSocket:
    def __init__(self, family=-1, type=-1, s=None):
        self.send_lock = Lock()
        if s is not None:
            self.s = s
            return
        self.s = socket(family, type)

    def __del__(self):
        if not self.send_lock.acquire(False):
            self.send_lock.release()

    @classmethod
    def from_socket(cls, s):
        return cls(-1, -1, s)

    def connect(self, addr):
        return self.s.connect(addr)

    def accept(self):
        return self.s.accept()

    def listen(self):
        self.s.listen()

    def bind(self, addr):
        self.s.bind(addr)

    def close(self):
        self.s.close()

    def recv(self):
        while True:
            pkt_size = int().from_bytes(self.s.recv(4), 'little')
            if pkt_size > MAX_PKT_SIZE:
                raise BrokenSocket()
            pkt_buff = bytes()
            bytes_read = 0
            while bytes_read < pkt_size:
                pkt_buff += self.s.recv(pkt_size - bytes_read)
                bytes_read = len(pkt_buff)
            data = bson.loads(pkt_buff)
            if data['action'] != REQUEST.KEEP_ALIVE:
                return data

    def send(self, data):
        self.send_lock.acquire()
        self.s.send(int(len(data)).to_bytes(4, 'little') + data)
        self.send_lock.release()
