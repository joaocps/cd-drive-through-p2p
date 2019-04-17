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

def contains_successor(identification, successor, node):
    if identification < node <= successor:
        return True
    elif successor < identification and (node > identification or node < successor):
        return True
    return False

class Waiter(threading.Thread):
    def __init__(self, port=5001, ide=1, ring_address = 5000):
        threading.Thread.__init__(self)
        self.name = "Waiter"
        self.id = ide
        self.port = port
        self.ring_address = ring_address
        self.ring_ids_dict = {'RESTAURANT': None, 'WAITER': self.id, 'CHEF': None, 'CLERK': None}

        if ring_address is None:
            self.successor_id = self.id
            self.successor_port = self.port
            self.inside_ring = True
        else:
            self.successor_id = None
            self.successor_port = None
            self.inside_ring = False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = logging.getLogger("Node {}".format(self.id))

    def send(self, port, o):
        p = pickle.dumps(o)
        self.socket.sendto(p, ('localhost', port))

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
        self.logger.debug('Node join: %s', args)

        port = args['addr']
        identification = args['id']

        if self.id == self.successor_id:
            self.successor_id = identification
            self.successor_port = port
            args = {'successor_id': self.id, 'successor_port': self.port}
            self.send(port, {'method': 'JOIN_REP', 'args': args})

        elif contains_successor(self.id, self.successor_id, identification):
            args = {'successor_id': self.successor_id, 'successor_port': self.successor_port}
            self.successor_id = identification
            self.successor_port = port
            self.send(port, {'method': 'JOIN_REP', 'args': args})
        else:
            self.logger.debug('Find Successor(%d)', args['id'])
            self.send(self.successor_port, {'method': 'JOIN_RING', 'args':args})
        self.logger.info(self)

    def node_discovery(self):
        pass

    def __str__(self):
        return 'Node ID: {}; Ring Address: {}; Successor_id: {}; Successor_port: {};' \
            .format(self.id, self.ring_address, self.successor_id, self.successor_port)

    def __repr__(self):
        return self.__str__()

    def run(self):
        self.socket.bind(('localhost', self.port))
        while not self.inside_ring:
            o = {'method': 'JOIN_RING', 'args': {'addr': self.port, 'id': self.id}}
            self.send(self.ring_address, o)
            p, addr = self.recv()
            if p is not None:
                o = pickle.loads(p)
                self.logger.debug('O: %s', o)
                if o['method'] == 'JOIN_REP':
                    args = o['args']
                    self.successor_id = args['successor_id']
                    self.successor_port = args['successor_port']
                    self.inside_ring = True
                    self.logger.info(self)

        done = False
        while not done:
            p, addr = self.recv()
            if p is not None:
                o = pickle.loads(p)
                self.logger.info('O: %s', o)
                if o['method'] == 'JOIN_RING':
                    self.node_join(o['args'])



