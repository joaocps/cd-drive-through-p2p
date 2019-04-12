# coding: utf-8
import threading
import time
import pickle
import socket
import random
import logging
import argparse

# se o proximo id que quer fazer join é > id do no e menor que id do next node, entao faz join

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')


class Restaurant(threading.Thread):

    def __init__(self, address, ring_address=None):
        threading.Thread.__init__(self)
        self.name = "Restaurant"
        self.id = 0
        self.addr = address
        self.inside_ring = True

        if ring_address is None:
            self.successor_id = self.id
            self.successor_addr = address
        else:
            self.successor_id = None
            self.successor_addr = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = logging.getLogger("Node {}".format(self.id))

        self.grelhador = Grelhador()
        self.bebidas = Bebidas()
        self.fritadeira = Fritadeira()

    def send(self, address, o):
        p = pickle.dumps(o)
        self.socket.sendto(p, address)

    def recv(self):
        try:
            p, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None
        else:
            if len(p) == 0:
                return None, addr
            else:
                return p, addr

    def run(self):

        while not self.inside_ring:
            o = {'method': 'NODE_JOIN', 'args': {'addr':self.addr, 'id':self.id}}
            self.send(self.ring_address, o)
            p, addr = self.recv()

        self.socket.bind(self.addr)
        p, addr = self.recv()
        o = pickle.loads(p)
        self.logger.debug('O: %s', o)
        if o['method'] == 'ORDER':
            print(o['args'])
            print(addr)

    def __str__(self):
        return 'Node ID: {}; DHT: {}; Successor: {}' \
            .format(self.id, self.inside_ring, self.successor_id)

    def __repr__(self):
        return self.__str__()

class Grelhador(object):

    def __init__(self):
        self.avg_time = 3

    def grelhar(self, avg_time):

        f_time = random.gauss(self.avg_time,5)
        time.sleep(f_time)



class Bebidas(object):

    def __init__(self):
        self.avg_time = 1

    def prepBebida(self, avg_time):

        f_time = random.gauss(self.avg_time,5)
        time.sleep(f_time)


class Fritadeira(object):

    def __init__(self):
        self.avg_time = 5

    def fritar(self, avg_time):

        f_time = random.gauss(self.avg_time,5)
        time.sleep(f_time)


if __name__ == '__main__':
    Restaurant(('localhost', 5000)).run()


