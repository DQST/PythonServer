import json
import logging
import socket
import threading
import os

logging.basicConfig(filename='log.txt', filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s')

"""DHT table to save data about rooms"""


class DHT(object):
    def __init__(self):
        self.__dht = {}

    def __getitem__(self, item):
        return self.__dht[item]

    def __contains__(self, item):
        return item in self.__dht

    def __str__(self):
        return str(self.__dht)

    def add(self, key, data):
        self.__dht[key] = data

    def remove(self, key):
        self.__dht.pop(key)

    def get_json(self):
        return json.dumps(self.__dht)


class Package(DHT):
    def __init__(self):
        DHT.__init__(self)

    def add(self, key, data):
        super().add(key, data)
        return self


class Serialize:
    @staticmethod
    def save(file, obj):
        f = open(file, 'w')
        f.write(obj)
        f.close()

    @staticmethod
    def load(file):
        if os.path.exists(file):
            f = open(file, 'r')
            s = f.read()
            f.close()
            return json.loads(s)
        else:
            raise FileNotFoundError('File "%s" not found!' % file)


class Server(threading.Thread):
    def __init__(self, ver='0042'):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.__FLAG_WORK__ = True
        self.__HEADER__ = ver
        self.__METHODS__ = {'message': self.message, 'get_rooms': self.get_rooms}
        try:
            pack = Package()
            load = Serialize.load('rooms.json')
            for i in load.keys():
                pack.add(i, (load[i][0], load[i][1]))
            self.__dht = pack
        except FileNotFoundError as error:
            self.__dht = DHT()
            logging.warning(error.args)

    def __str__(self):
        return self.__dht.__str__()

    def sendto(self, msg, end_point):
        data = bytes(self.__HEADER__ + msg, 'utf-8')
        self.sock.sendto(data, end_point)

    def stop_server(self):
        Serialize.save('rooms.json', self.__dht.get_json())
        self.__FLAG_WORK__ = False
        self.sendto('stop...', ('127.0.0.1', 14801))
        self.sock.close()

    def message(self, *args):
        input_ip = args[0]
        input_id = args[1]
        pack = Package().add('jsonrpc', '2.0').add('method', 'pushMessage')\
            .add('params', ['Server', 'Server', 'Hello from Server!']).add('id', input_id)
        self.sendto(pack.get_json(), input_ip)

    def get_rooms(self, *args):
        input_ip = args[0]
        input_id = args[1]
        pack = Package().add('jsonrpc', '2.0').add('result', self.__dht.get_json()).add('id', input_id)
        self.sendto(pack.get_json(), input_ip)

    def parse(self, data, input_ip):
        json_package = json.loads(data)
        if 'jsonrpc' in json_package.keys() and json_package['jsonrpc'] == '2.0':
            method = json_package['method']
            input_id = json_package['id']
            params = json_package['params']
            if method in self.__METHODS__.keys():
                self.__METHODS__[method](input_ip, input_id, params)
            else:
                pack = Package().add('jsonrpc', '2.0').\
                    add('error', {'code': -32601, 'message': 'Procedure not found.'}).add('id', input_id)
                self.sendto(pack.get_json(), input_ip)
        # json_package = json.loads(data)  # convert input data from json to dict
        # for i in json_package.keys():
        #     key = i  # get key
        #     if key == 'msg':  # if key in package = msg then send "Hello" message
        #         pack = Package().add('msg', 'Hello from Server!').add('sender', 'Server').add('in_room', 'Server')
        #         self.sendto(pack.get_json(), input_ip)
        #     elif key == 'add_room':
        #         name = json_package[key]
        #         if name not in self.__dht:
        #             self.__dht.add(name, input_ip)
        #             pack = Package().add('msg', 'Room "%s" has been created!' % name).add('sender', 'Server').add(
        #                 'in_room', 'Server')
        #             self.sendto(pack.get_json(), input_ip)
        #         else:
        #             pack = Package().add('msg', 'Room "%s" already exists!' % name).add('sender', 'Server').add(
        #                 'in_room', 'Server')
        #             self.sendto(pack.get_json(), input_ip)
        #     elif key == 'del_room':
        #         name = json_package[key]
        #         if name in self.__dht:
        #             self.__dht.remove(name)
        #             pack = Package().add('msg', 'Delete room "%s".' % name).add('sender', 'Server').add('in_room',
        #                                                                                                 'Server')
        #             self.sendto(pack.get_json(), input_ip)
        #         else:
        #             pack = Package().add('msg', 'Room "%s" not found!' % name).add('sender', 'Server').add('in_room',
        #                                                                                                    'Server')
        #             self.sendto(pack.get_json(), input_ip)
        #     elif key == 'con_to':
        #         name = json_package[key]
        #         if name in self.__dht:
        #             host_ip = self.__dht[name]
        #             host = Package().add('con_to', host_ip).add('in_room', 'Server')
        #             user = Package().add('con_to', input_ip).add('in_room', 'Server')
        #             self.sendto(host.get_json(), input_ip)
        #             self.sendto(user.get_json(), host_ip)
        #         else:
        #             pack = Package().add('msg', 'Room "%s" not found!' % name).add('sender', 'Server').add('in_room',
        #                                                                                                    'Server')
        #             self.sendto(pack.get_json(), input_ip)
        #     elif key == 'get_rooms':
        #         pack = Package().add('rooms_list', self.__dht.get_json()).add('in_room', 'Server')
        #         self.sendto(pack.get_json(), input_ip)

    def run(self):
        while self.__FLAG_WORK__:
            try:
                data, ip = self.sock.recvfrom(1024)  # get receive data and input IP
                decode_data = data.decode('utf-8')  # decode from bytes to string
                header = decode_data[:4]  # get head of package
                body = decode_data[4:]  # get body of package
                if header == '0042':  # header = 0042
                    self.parse(body, ip)  # ok, parse body
                else:
                    logging.warning('Unknown header: "%s"' % header)  # if no, then logging.warning
            except Exception as error:
                logging.warning('----------------------------------------')
                logging.warning('Type: "%s"' % type(error))
                logging.warning('Exception: "%s"' % str(error))
                logging.warning('Exception args: "%s"' % str(error.args))
                logging.warning('----------------------------------------')


if __name__ == '__main__':
    server = Server()
    server.start()
    while True:
        inp = input('> ')
        if inp == 'exit':
            server.stop_server()
            server.join()
            break
        elif inp == 'rooms':
            print(server)
        else:
            print('Unknown command "%s"' % inp)
