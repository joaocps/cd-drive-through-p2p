# coding: utf-8

import time
import pickle
import socket
import random
import logging
import argparse
import threading


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Waiter')


class Waiter(threading.Thread):
    def __init__(self, port=5001, ide=1, ring_address = None):
        threading.Thread.__init__(self)
        self.name = "Waiter"
        self.id = ide
        self.port = port
        self.ring_address = ring_address

        if ring_address is None:
            self.successor_id = self.id
            self.successor_port = self.port
        else:
            self.successor_id = None
            self.successor_port = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = logging.getLogger("Node {}".format(self.id))

    def send(self, port, o):
        p = pickle.dumps(o)
        self.socket.sendto(p, port)

    def recv(self):
        try:
            p, port = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None
        else:
            if len(p) == 0:
                return None, port
            else:
                return p, port

    def node_join(self,args):
        pass

    def node_discovery(self):
        pass

    def __str__(self):
        return 'Node ID: {}; Ring Address: {}; Successor: {}; ' \
            .format(self.id, self.ring_address, self.successor_id)

    def __repr__(self):
        return self.__str__()

    def run(self):
        print("ID-1")
