import socket
import threading
import time
import json


def log(msg, file='log.txt'):
    f = open(file, 'a')
    f.write(' | ' + msg + '\n')
    f.close()


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
            if key == 'msg':                        # if key in package = msg then send Hello message
                self.sendto(json.dumps({'msg': 'Hello from Server!'}), input_ip)
            elif key == 'add_room':
                name = json_package[key]
                if name not in self.__dht:
                    self.__dht.add(name, [input_ip])
                    self.sendto(json.dumps({'msg': 'Room "%s" has been created!' % name}), input_ip)
                else:
                    self.sendto(json.dumps({'msg': 'Room "%s" already exists!' % name}), input_ip)
            elif key == 'del_room':
                name = json_package[key]
                if name in self.__dht:
                    self.__dht.remove(name)
                    self.sendto(json.dumps({'msg': 'Delete room "%s".' % name}), input_ip)
                else:
                    self.sendto(json.dumps({'msg': 'Room "%s" not found!' % name}), input_ip)
            elif key == 'con_to':
                name = json_package[key]
                if name in self.__dht:
                    host_ip = self.__dht[name][0]
                    self.sendto(json.dumps({'con_to': host_ip}), input_ip)
                    self.sendto(json.dumps({'con_to': input_ip}), host_ip)
                else:
                    self.sendto(json.dumps({'msg': 'Room "%s" not found!'}), input_ip)

    def run(self):
        while self.__FLAG_WORK__:
            try:
                data, ip = self.sock.recvfrom(1024)                 # get receive data and input IP
                decode_data = data.decode('utf-8')                  # decode from bytes to string
                header = decode_data[:4]                            # get head of package
                body = decode_data[4:]                              # get body of package
                if header == '0042':                                # header = 0042
                    self.parse(body, ip)                            # ok, parse body
                else:
                    log('Unknown header: "%s"' % header)     # if no, then log
            except Exception as error:
                log('----------------------------------------')
                log('Type: "%s"' % type(error))
                log('Exception: "%s"' % str(error))
                log('Exception args: "%s"' % str(error.args))
                log('----------------------------------------')


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
