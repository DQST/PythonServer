import socket
import threading
import time
import json


class Logger:
    @staticmethod
    def log(msg, file='log.txt'):
        f = open(file, 'a')
        f.write(' | ' + msg)
        f.close()


class Server(threading.Thread):
    def __init__(self, ver='0042'):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.__FLAG_WORK__ = True
        self.__HEADER__ = ver

    def sendto(self, msg, end_point):
        data = bytes(self.__HEADER__ + msg, 'utf-8')
        self.sock.sendto(data, end_point)

    def stop_server(self):
        self.__FLAG_WORK__ = False
        self.sendto('stop...', ('127.0.0.1', 14801))
        self.sock.close()

    @staticmethod
    def parse(data):
        json_package = json.loads(data)
        for i in json_package.keys():
            key = i
            if key == 'msg':
                pass

    def run(self):
        while self.__FLAG_WORK__:
            try:
                data, ip = self.sock.recvfrom(1024)
                decode_data = data.decode('utf-8')
                header = decode_data[:4]
                message = decode_data[4:]
                if header is '0042':
                    Server.parse(message)
                else:
                    Logger.log('Unknown header: "%s"' % header)
            except Exception as error:
                Logger.log('----------------------------------------')
                Logger.log('Type: "%s"' % type(error))
                Logger.log('Exception: "%s"' % str(error))
                Logger.log('Exception args: "%s"' % str(error.args))
                Logger.log('----------------------------------------')


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
