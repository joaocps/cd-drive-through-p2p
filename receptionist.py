# coding: utf-8
import threading
import time
import pickle
import socket
import random
import logging
import argparse

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')


class Receptionist(threading.Thread):

    def __init__(self, address, ring_address=None):
        threading.Thread.__init__(self)
        self.name = "Receptionist"
        self.id = 1
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

        self.socket.bind(self.addr)
        p, addr = self.recv()
        o = pickle.loads(p)
        self.logger.debug('O: %s', o)
        if o['method'] == 'ORDER':
            print(o['args'])

    def __str__(self):
        return 'Node ID: {}; DHT: {}; Successor: {}' \
            .format(self.id, self.inside_ring, self.successor_id)

    def __repr__(self):
        return self.__str__()

if __name__ == '__main__':
    Receptionist(('localhost', 5001)).run()


