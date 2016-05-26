import json
import logging
import threading
import socket
import os
import pickle
import hashlib


logging.basicConfig(filename='log.txt', filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s')


def get_hash(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def get_olo(method, args):
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

    def call(self, method_name, *args, **kargs):
        if method_name in self.__methods__.keys():
            self.__methods__[method_name](*args, **kargs)


class Users:
    def __init__(self):
        self.__users__ = []

    def add(self, ip):
        if ip not in self.__users__:
            self.__users__.append(ip)

    def remove(self, ip):
        if ip in self.__users__:
            self.__users__.remove(ip)

    def get_users(self):
        return self.__users__


class FileServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.sock.listen(10)
        self.__WORK__ = True
        self.__I__ = 0

    def start(self):
        super().start()
        logging.warning('File Server start...')
        if os.path.exists(os.getcwd() + '\\downloads\\') is False:
            os.mkdir(os.getcwd() + '\\downloads\\')

    def run(self):
        while self.__WORK__:
            try:
                conn, addr = self.sock.accept()
                conn.settimeout(60)
                while True:
                    data = conn.recv(1028)
                    head = data[:4]
                    if head == b'\x00\x00\x00\x01':
                        path = os.getcwd() + '\\downloads\\.part_' + str(self.__I__)
                        f = open(path, 'ab')
                        f.write(data[4:])
                        f.close()

                    if head == b'0002':
                        h, file_name = data.decode('utf-8').split(':')
                        path = os.getcwd() + '\\downloads\\'
                        if os.path.exists(path + '.part_' + str(self.__I__)) is True:
                            os.rename(path + '.part_' + str(self.__I__), path + file_name)

                    if not data:
                        break
                self.__I__ += 1
                conn.close()
            except Exception as error:
                logging.warning('----------------------------------------')
                logging.warning('Type: "%s"' % type(error))
                logging.warning('Exception: "%s"' % str(error))
                logging.warning('Exception args: "%s"' % str(error.args))
                logging.warning('----------------------------------------')

    def stop(self):
        self.__WORK__ = False
        self.sock.close()


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.__WORK__ = True
        self.__service__ = Service(self)
        self.__rooms__ = RoomManager()

    def start(self):
        super().start()
        logging.warning('Start Server...')
        print('Start Server...')
        self.__rooms__.load()

    def stop(self):
        self.__WORK__ = False
        self.send('stop...', ('127.0.0.1', 14801))
        self.sock.close()
        self.__rooms__.save()
        logging.warning('Server stopped!')
        print('Server stopped!')
        super()._stop()

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
        room_name, user_name, room_pass = args[1]
        users = Users()
        users.add(user_ip)
        self.__rooms__.add(room_name, {'users': users, 'pass': get_hash(room_pass), 'owner': user_name})
        olo = get_olo('con_to', [room_name])
        self.send(olo, user_ip)
        self.get_rooms(*args)

    @decorator
    def del_room(self, *args):
        room_name, user_name, input_pass = args[1]
        password = self.__rooms__[room_name]['pass']
        owner = self.__rooms__[room_name]['owner']
        if (get_hash(input_pass) == password) and (owner == user_name):
            self.__rooms__.remove(room_name)
            self.get_rooms(*args)

    @decorator
    def con_to(self, *args):
        user_ip = args[0]
        room_name, user_name, room_pass = args[1]
        password = self.__rooms__[room_name]['pass']
        if get_hash(room_pass) == password:
            message = '--- User "%s" connect to room ---' % user_name
            users = self.__rooms__[room_name]['users']
            users.add(user_ip)
            olo = get_olo('con_to', [room_name])
            self.send(olo, user_ip)
            self.__rooms__.broadcast(room_name, 'Server', message, user_ip, self)

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
        olo = get_olo('room_list', data)
        self.send(olo, user_ip)

    @decorator
    def disconnect_from(self, *args):
        user_ip = args[0]
        room_name = args[1][0]
        user_name = args[1][1]
        message = '--- User "%s" disconnect from room ---' % user_name
        self.__rooms__[room_name].remove(user_ip)
        self.__rooms__.broadcast(room_name, 'Server', message, user_ip, self)


class RoomManager:
    def __init__(self):
        self.__rooms__ = dict()

    def add(self, name, obj):
        if name not in self.__rooms__.keys():
            self.__rooms__[name] = obj

    def remove(self, name):
        if name in self.__rooms__.keys():
            del self.__rooms__[name]

    def __getitem__(self, item):
        if item in self.__rooms__.keys():
            return self.__rooms__[item]

    def broadcast(self, name, user, msg, input_ip, serv: Server):
        if name in self.__rooms__.keys():
            users = self.__rooms__[name]['users']
            for i in users.get_users():
                if i != input_ip:
                    olo = get_olo('push_message', [name, user, msg])
                    serv.send(olo, i)

    def save(self, path='rooms.data'):
        dump = pickle.dumps(self.__rooms__, protocol=0)
        f = open(path, 'wb')
        f.write(dump)
        f.close()

    def load(self, path='rooms.data'):
        if os.path.exists(path) is True:
            f = open(path, 'rb')
            data = f.read()
            f.close()
            self.__rooms__ = pickle.loads(data)
        else:
            logging.warning('File "%s" not found!' % path)

    def get_rooms(self):
        return json.dumps([i for i in self.__rooms__.keys()])


if __name__ == '__main__':
    files = FileServer()
    files.start()
    server = Server()
    server.start()
    while True:
        command = input('> ')
        if command == 'exit':
            server.stop()
            server.join()
            files.stop()
            files.join()
            break
        else:
            print('Unknown command "%s"' % command)
