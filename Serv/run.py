import json
import logging
import threading
import socket
import time


logging.basicConfig(filename='log.txt', filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s')


def oloprotocol(method, args):
    olo = {'ver': '0042', 'method': method, 'params': args}
    return json.dumps(olo)


def decorator(fun):
    fun.is_wrapped = True
    return fun


class Service:
    def __init__(self, obj):
        self.__methods__ = {}
        l = dir(obj)
        for i in l:
            ty = type(getattr(obj, i))
            try:
                if (str(ty) == "<class 'method'>") and (getattr(obj, i).is_wrapped is True):
                    self.__methods__[getattr(obj, i).__name__] = getattr(obj, i)
            except:
                pass

    def __str__(self):
        return [i for i in self.__methods__.keys()]

    def call(self, method_name, *args, **kargs):
        if method_name in self.__methods__.keys():
            self.__methods__[method_name](*args, **kargs)


class Users:
    def __init__(self):
        self.__users__ = []

    def add(self, ip):
        if not self.is_exists(ip):
            self.__users__.append(ip)

    def remove(self, ip):
        if self.is_exists(ip):
            self.__users__.remove(ip)

    def is_exists(self, ip):
        for i in self.__users__:
            if i == ip:
                return True
        return False

    def get_users(self):
        return self.__users__


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.__WORK__ = True
        self.__USER_CON__ = dict()
        self.__service__ = Service(self)
        self.__rooms__ = RoomManager()

    def start(self):
        super().start()
        logging.warning('Start Server...')
        print('Start Server...')

    def stop(self):
        self.__WORK__ = False
        self.send('stop...', ('127.0.0.1', 14801))
        self.sock.close()
        logging.warning('Server stopped!')

    def send(self, data, ip):
        self.sock.sendto(bytes(data, 'utf-8'), ip)

    def run(self):
        while self.__WORK__:
            try:
                data, ip = self.sock.recvfrom(1024)
                self.parse(data.decode('utf-8'), ip)
            except Exception as error:
                logging.warning('----------------------------------------')
                logging.warning('Type: "%s"' % type(error))
                logging.warning('Exception: "%s"' % str(error))
                logging.warning('Exception args: "%s"' % str(error.args))
                logging.warning('----------------------------------------')

    def parse(self, data, ip):
        pack = json.loads(data)
        if 'ver' in pack.keys() and pack['ver'] == '0042':
            method = pack['method']
            params = pack['params']
            self.__service__.call(method, ip, params)

    @decorator
    def add_room(self, *args):
        user_ip = args[0]
        room_name = args[1][0]
        users = Users()
        users.add(user_ip)
        self.__rooms__.add(room_name, users)
        olo = oloprotocol('con_to', [room_name])
        self.send(olo, user_ip)
        self.get_rooms(*args)

    @decorator
    def del_room(self, *args):
        room_name = args[1][0]
        self.__rooms__.remove(room_name)
        self.get_rooms(*args)

    @decorator
    def con_to(self, *args):
        user_ip = args[0]
        room_name = args[1][0]
        users = self.__rooms__[room_name]
        users.add(user_ip)
        olo = oloprotocol('con_to', [room_name])
        self.send(olo, user_ip)

    @decorator
    def broadcast_all_in_room(self, *args):
        user_ip = args[0]
        room_name = args[1][0]
        user_name = args[1][1]
        message = args[1][2]
        self.__rooms__.broadcast(room_name, user_name, message, user_ip, self)

    @decorator
    def get_rooms(self, *args):
        user_ip = args[0]
        data = self.__rooms__.get_rooms()
        olo = oloprotocol('room_list', data)
        self.send(olo, user_ip)

    @decorator
    def nop(self, *args):
        cur_time = time.time()
        user_name = args[1][0]
        if user_name in self.__USER_CON__.keys():
            last_time = self.__USER_CON__[user_name][0]
            if cur_time - last_time > 10.0:
                self.__USER_CON__[user_name][1] = False
        else:
            self.__USER_CON__[user_name] = [cur_time, True]


class RoomManager:
    def __init__(self):
        self.__rooms__ = dict()

    def add(self, name, users: Users):
        if name not in self.__rooms__.keys():
            self.__rooms__[name] = users

    def remove(self, name):
        if name in self.__rooms__.keys():
            del self.__rooms__[name]

    def __getitem__(self, item):
        if item in self.__rooms__.keys():
            return self.__rooms__[item]

    def broadcast(self, name, user, msg, input_ip, serv: Server):
        if name in self.__rooms__.keys():
            users = self.__rooms__[name]
            for i in users.get_users():
                if i != input_ip:
                    olo = oloprotocol('push_message', [name, user, msg])
                    serv.send(olo, i)

    def get_rooms(self):
        return json.dumps([i for i in self.__rooms__.keys()])


if __name__ == '__main__':
    server = Server()
    server.start()
    while True:
        command = input('> ')
        if command == 'exit':
            server.stop()
            server.join()
            break
        else:
            print('Unknown command "%s"' % command)
