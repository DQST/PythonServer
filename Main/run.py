import json
import logging
import threading
import socket
import os


logging.basicConfig(filename='log.txt', filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s')


def easydecorator(fun):
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


class DHT(object):
    def __init__(self):
        self.__dht = {}

    def __getitem__(self, item):
        return self.__dht[item]

    def __contains__(self, item):
        return item in self.__dht

    @staticmethod
    def __convert(dump):
        for i in dump:
            adr, port = dump[i][0]
            dump[i][0] = (adr, port)
        return dump

    def only_keys(self):
        return json.dumps([i for i in self.__dht.keys()])

    def __str__(self):
        return str(self.__dht)

    def add(self, key, data):
        self.__dht[key] = data

    def remove(self, key):
        self.__dht.pop(key)

    def get_json(self):
        return json.dumps(self.__dht)

    def save(self, path='rooms.json'):
        f = open(path, 'w')
        f.write(self.get_json())
        f.close()

    def load(self, path='rooms.json'):
        if os.path.exists(path) is True:
            f = open(path, 'r')
            s = f.read()
            f.close()
            self.__dht = self.__convert(json.loads(s))
        else:
            logging.warning('File "%s" not found!' % path)


class Package(DHT):
    def __init__(self):
        DHT.__init__(self)

    def add(self, key, data):
        super().add(key, data)
        return self


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.__is_work__ = True
        self.__service__ = Service(self)
        self.__room_table__ = DHT()
        self.__room_table__.load('rooms.json')

    def start(self):
        print('Server running...')
        logging.warning('Start Server...')
        super().start()

    @easydecorator
    def add_room(self, *args):
        input_ip = args[0]
        room_name = args[1][0]
        room_pass = args[1][1]
        if room_name not in self.__room_table__:
            self.__room_table__.add(room_name, [input_ip, room_pass])
        self.get_rooms(args[0], args[1])

    @easydecorator
    def del_room(self, *args):
        name = args[1][0]  # get name
        if name in self.__room_table__:
            self.__room_table__.remove(name)
        self.get_rooms(args[0], args[1])

    @easydecorator
    def con_to(self, *args):
        input_adr, input_port = args[0]
        room_name = args[1][0]
        room_pass = args[1][1]
        # TODO: room connection
        if room_name in self.__room_table__:
            room = self.__room_table__[room_name]

            if room[1] == room_pass:
                host_adr, host_port = room[0]

                if (input_adr, input_port) != (host_adr, host_port):
                    user_pack = Package().add('ver', '0042').add('method', 'con_to')\
                        .add('params', [room_name, host_adr + ':' + str(host_port)])
                    host_pack = Package().add('ver', '0042').add('method', 'con_to')\
                        .add('params', [room_name, input_adr + ':' + str(input_port)])
                    self.send(user_pack.get_json(), (input_adr, input_port))
                    self.send(host_pack.get_json(), (host_adr, host_port))

    @easydecorator
    def get_rooms(self, *args):
        input_ip = args[0]
        pack = Package().add('ver', '0042').add('method', 'room_list') \
            .add('params', self.__room_table__.only_keys())
        self.send(pack.get_json(), input_ip)

    def parse(self, pack, input_ip):
        pack = json.loads(pack)
        if 'ver' in pack.keys() and pack['ver'] == '0042':
            method = pack['method']
            params = pack['params']
            self.__service__.call(method, input_ip, params)

    def send(self, data, ip):
        self.sock.sendto(bytes(data, 'utf-8'), ip)

    def run(self):
        while self.__is_work__:
            try:
                data, ip = self.sock.recvfrom(1024)
                self.parse(data.decode('utf-8'), ip)
            except Exception as error:
                logging.warning('----------------------------------------')
                logging.warning('Type: "%s"' % type(error))
                logging.warning('Exception: "%s"' % str(error))
                logging.warning('Exception args: "%s"' % str(error.args))
                logging.warning('----------------------------------------')

    def stop(self):
        self.__room_table__.save('rooms.json')
        self.__is_work__ = False
        self.send('stop...', ('127.0.0.1', 14801))
        self.sock.close()
        logging.warning('Server stopped!')

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
