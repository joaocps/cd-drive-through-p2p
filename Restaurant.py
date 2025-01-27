# coding: utf-8

import time
import pickle
import socket
import random
import logging
import argparse
import threading
import queue

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Restaurant')


def contains_successor(identification, successor, node):
    if identification < node <= successor:
        return True
    elif successor < identification and (node > identification or node < successor):
        return True
    return False


class Restaurant(threading.Thread):
    def __init__(self, port=5000, ide=0, ring_address = None, timeout = 3):
        threading.Thread.__init__(self)
        self.name = "RESTAURANT"
        self.id = ide
        self.port = port
        self.ring_address = ring_address
        self.ring_completed = False
        self.ring_ids_dict = {'RESTAURANT': self.id,'WAITER': None,'CHEF': None,'CLERK': None}
        self.done = False
        self.work = False
        self.orders = queue.Queue()

        if ring_address is None:
            self.successor_id = self.id
            self.successor_port = self.port
            self.inside_ring = True
        else:
            self.successor_id = None
            self.successor_port = None
            self.inside_ring = False

        self.grelhador = Grelhador(30)
        self.bebidas = Bebidas(10)
        self.fritadeira = Fritadeira(50)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
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

    def node_join(self, args):
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
            self.send(self.successor_port, {'method': 'JOIN_RING', 'args': args})
        self.logger.info(self)

    def check_ring_completed(self):
        if self.successor_id == 0:
            return True
        return False

    def node_discovery(self, args):

        if self.ring_ids_dict['WAITER'] is None and args['WAITER'] is not None:
            self.ring_ids_dict['WAITER'] = args['WAITER']

        if self.ring_ids_dict['CHEF'] is None and args['CHEF'] is not None:
            self.ring_ids_dict['CHEF'] = args['CHEF']

        if self.ring_ids_dict['CLERK'] is None and args['CLERK'] is not None:
            self.ring_ids_dict['CLERK'] = args['CLERK']

        if all(value is not None for value in self.ring_ids_dict.values()):
            self.ring_completed = True
            self.send(self.successor_port, {'method': 'NODE_DISCOVERY', 'args': self.ring_ids_dict})
            return

        self.send(self.successor_port, {'method': 'NODE_DISCOVERY', 'args': self.ring_ids_dict})

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
                elif o['method'] == 'NODE_DISCOVERY' and not self.ring_completed:
                    self.node_discovery(o['args'])

                elif o['method'] == 'ORDER':
                    self.send(self.successor_port, o)

                elif o['method'] == 'COOKED' or o['method'] == 'START':
                    self.send(self.successor_port, o)

                #cliente pergunta se está pronto e o pedido já esta pronto
                elif o['method'] == 'PICKUP' and self.done == True:
                    #print("pickup done")
                    self.send(self.successor_port, o)

                #cliente pergunta se está pronto e o pedido ainda não está esta pronto
                elif o['method'] == 'PICKUP' and self.done == False:
                    #print("pickup not done")
                    pass

                #pedido está pronto
                elif o['method'] == 'DONE':
                    self.done = True
                    self.send(self.successor_port, {'method': 'PICKUP', 'args': o['args']})

                #recebe o ticket e envia o feedback ao client e passa o ao sucessor
                elif o['method'] == 'TICKET':
                    self.send(5004, {"args": {'number': o["args"]['number']}})
                    self.orders.put(o['args'])
                    self.send(self.successor_port, {'method': 'START', 'args': o['args']})

                    #code to use queue orders
                    #if self.work == False:
                    #    self.work = True

                #entrega
                elif o['method'] == 'DELIVER':
                    self.done = False
                    self.send(5004, o)

                    #code to use queue orders
                    #self.work = False
                    #self.orders.get(o['args'])
                    #for elem in list(self.orders.queue):
                    #    print(elem)
                    #if len(self.orders.queue) == 0:
                    #    self.send(self.successor_port, {'method': 'WAITING', 'args': 'no orders'})
                    #else:
                    #    self.send(self.successor_port, {'method': 'START', 'args': self.orders.get()})

                #code to use queue orders
                #elif o['method'] == 'WAITING' and len(self.orders.queue) == 0:
                #    self.send(self.successor_port, o)
                #elif o['method'] == 'WAITING' and len(self.orders.queue) != 0:
                #    self.send(self.successor_port, {'method': 'START','args' : self.orders.get()})

                #recebe o que tem de cozinhar
                elif o['method'] == 'COOK':

                    if o['args']['args']['hamburger'] != 0:
                        nr = o['args']['args']['hamburger']
                        for i in range(nr):
                            Grelhador(3).grelhar()

                    elif o['args']['args']['drink'] != 0:
                        nr = o['args']['args']['drink']
                        for i in range(nr):
                            Bebidas(1).prepBebida()

                    elif o['args']['args']['fries'] != 0:
                        nr = o['args']['args']['fries']
                        for i in range(nr):
                            #print(nr)
                            Fritadeira(5).fritar()

                    self.send(self.successor_port,{'method': 'COOKED', 'args': o['args']})
            else:
                if not self.ring_completed:
                    o = {'method': 'NODE_DISCOVERY', 'args': self.ring_ids_dict}
                    self.send(self.successor_port, o)
                


class Grelhador(object):
    def __init__(self, time):
        self.avg_time = time

    def grelhar(self):
        time.sleep(random.gauss(self.avg_time, 0.5))



class Bebidas(object):
    def __init__(self, time):
        self.avg_time = time

    def prepBebida(self):
        time.sleep(random.gauss(self.avg_time, 0.5))


class Fritadeira(object):
    def __init__(self, time):
        self.avg_time = time

    def fritar(self):
        time.sleep(random.gauss(self.avg_time, 0.5))
