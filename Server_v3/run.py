import socket
import threading
import time
import json
import logging


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


class Server(threading.Thread):
    def __init__(self, ver='0042'):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.__FLAG_WORK__ = True
        self.__HEADER__ = ver
        self.__dht = DHT()

    def sendto(self, msg, end_point):
        data = bytes(self.__HEADER__ + msg, 'utf-8')
        self.sock.sendto(data, end_point)

    def stop_server(self):
        self.__FLAG_WORK__ = False
        self.sendto('stop...', ('127.0.0.1', 14801))
        self.sock.close()

    def parse(self, data, input_ip):
        json_package = json.loads(data)             # convert input data from json to dict
        for i in json_package.keys():
            key = i                                 # get key
            if key == 'msg':                        # if key in package = msg then send "Hello" message
                pack = Package().add('msg', 'Hello from Server!').add('sender', 'Server').add('in_room', 'Server')
                self.sendto(pack.get_json(), input_ip)
            elif key == 'add_room':
                name = json_package[key]
                if name not in self.__dht:
                    self.__dht.add(name, input_ip)
                    pack = Package().add('msg', 'Room "%s" has been created!' % name).add('sender', 'Server').add('in_room', 'Server')
                    self.sendto(pack.get_json(), input_ip)
                else:
                    pack = Package().add('msg', 'Room "%s" already exists!' % name).add('sender', 'Server').add('in_room', 'Server')
                    self.sendto(pack.get_json(), input_ip)
            elif key == 'del_room':
                name = json_package[key]
                if name in self.__dht:
                    self.__dht.remove(name)
                    pack = Package().add('msg', 'Delete room "%s".' % name).add('sender', 'Server').add('in_room', 'Server')
                    self.sendto(pack.get_json(), input_ip)
                else:
                    pack = Package().add('msg', 'Room "%s" not found!' % name).add('sender', 'Server').add('in_room', 'Server')
                    self.sendto(pack.get_json(), input_ip)
            elif key == 'con_to':
                name = json_package[key]
                if name in self.__dht:
                    host_ip = self.__dht[name]
                    host = Package().add('con_to', host_ip).add('in_room', 'Server')
                    user = Package().add('con_to', input_ip).add('in_room', 'Server')
                    self.sendto(host.get_json(), input_ip)
                    self.sendto(user.get_json(), host_ip)
                else:
                    pack = Package().add('msg', 'Room "%s" not found!' % name).add('sender', 'Server').add('in_room', 'Server')
                    self.sendto(pack.get_json(), input_ip)
            elif key == 'get_rooms':
                pack = Package().add('rooms_list', self.__dht.get_json()).add('in_room', 'Server')
                self.sendto(pack.get_json(), input_ip)

    def run(self):
        while self.__FLAG_WORK__:
            try:
                data, ip = self.sock.recvfrom(1024)                     # get receive data and input IP
                decode_data = data.decode('utf-8')                      # decode from bytes to string
                header = decode_data[:4]                                # get head of package
                body = decode_data[4:]                                  # get body of package
                if header == '0042':                                    # header = 0042
                    self.parse(body, ip)                                # ok, parse body
                else:
                    logging.warning('Unknown header: "%s"' % header)    # if no, then logging.warning
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
        else:
            print('Unknown command "%s"' % inp)
