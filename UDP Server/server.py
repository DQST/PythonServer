import os
import json
import logging
from threading import *
import socket
from sys import argv

logging.basicConfig(filename='log.txt', filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s')


'''Config class.'''


class Config:
    @staticmethod
    def save(obj, path):
        data = json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))
        f = open(path, 'w')
        f.write(data)
        f.close()

    @staticmethod
    def load(path):
        f = open(path)
        data = f.read()
        f.close()
        return json.loads(data)


'''Server class'''


class Server:
    """Server constructor"""

    def __init__(self, args=()):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(args)
        self.WORK = True
        self.UsersOnline = []

        if os.path.exists('table.json'):
            self.__ROOM_HASH__ = Config.load('table.json')

            '''Convert list to tuple'''
            for i in self.__ROOM_HASH__:
                ip_adr = self.__ROOM_HASH__[i][0]
                port = self.__ROOM_HASH__[i][1]
                self.__ROOM_HASH__[i] = (ip_adr, port)
        else:
            self.__ROOM_HASH__ = {}

        logging.warning('Server running...')

    def parse_data(self, input_data):
        data, input_adr = input_data
        message = data.decode('utf-8')

        ip_adr = str(input_adr[0]) + ':' + str(input_adr[1])

        strings = message.split(':')
        protocol_ver = strings[0][:4]
        command = strings[0][4:]

        if protocol_ver == '0042':
            if command == 'nop':
                pass
            elif command == 'newroom':
                if (strings[1] in self.__ROOM_HASH__.keys()) is True:
                    self.send_to('Error, room "%s" already exist!' % strings[1], input_adr)
                    logging.warning('[{0}] Error "{1}" already exist!'.format(ip_adr, strings[1]))
                else:
                    self.__ROOM_HASH__[strings[1]] = input_adr
                    self.send_to('Room "%s" has been create!' % strings[1], input_adr)
                    logging.warning('[{0}] Create room "{1}"'.format(ip_adr, strings[1]))
            elif command == 'contoroom':
                res = None
                if strings[1] in self.__ROOM_HASH__.keys():
                    res = self.__ROOM_HASH__[strings[1]]

                if res == input_adr:
                    self.send_to('You already connect to room: "%s"' % strings[1], input_adr)
                    logging.warning('Try connect [%s] with himself.' % ip_adr)
                    return

                '''Do something with this shit!!!!'''
                if res is not None:
                    user1 = res[0] + ':' + str(res[1])
                    user2 = input_adr[0] + ':' + str(input_adr[1])
                    self.send_to('tryconto$' + user1 + '$' + strings[1], input_adr)
                    self.send_to('tryconto$' + user2 + '$' + strings[1], res)
                    logging.warning('[{0}] connect to [{1}]'.format(input_adr, res))
                else:
                    self.send_to('Room "%s" not found!' % strings[1], input_adr)
            elif command == 'get_rooms':
                json_str = json.dumps(self.__ROOM_HASH__)
                self.send_to('rooms_list$%s' % json_str, input_adr)
            elif command == 'msg':
                self.send_to('Hello from Server!', input_adr)

    '''Send message here'''

    def send_to(self, msg, end_point):
        self.sock.sendto(bytes(msg, 'utf-8'), end_point)

    '''receive input message'''

    def receive(self):
        while self.WORK:
            try:
                input_data = self.sock.recvfrom(1024)

                '''Parse input data'''
                self.parse_data(input_data)
            except Exception as error:
                logging.warning('---------------------')
                logging.warning('Server Error!')
                logging.warning('Error type: "%s"' % type(error))
                logging.warning('Error args: "%s"' % str(error.args))
                logging.warning('Error args: "%s"' % str(error))
                logging.warning('---------------------')
        else:
            logging.warning('receive stopped.')

    '''stop server here'''

    def stop(self):
        self.WORK = False
        logging.warning('Server stopped!')
        self.send_to('Stop...', ('127.0.0.1', 14801))
        Config.save(self.__ROOM_HASH__, 'table.json')
        self.sock.close()


switch = {'rooms': lambda x: [print('"{0}" {1}'.format(i, x[i])) for i in x]}

if __name__ == '__main__':
    argsList = None

    if len(argv) > 1:
        argsList = (argv[1], argv[2])
    else:
        argsList = ('0.0.0.0', 14801)

    server = Server(argsList)
    receiveThread = Thread(name='receive', target=server.receive)
    receiveThread.start()

    try:
        print('Start server...')
        while True:
            arr = input('> ')

            '''stop server'''
            if arr == 'exit':
                server.stop()
                receiveThread.join()
                break
            else:
                if (arr in switch.keys()) is True:
                    switch[arr](server.__ROOM_HASH__)
                else:
                    print('Command "%s" not found!' % arr)
    except Exception as e:
        logging.warning('Server Error!')
        logging.warning('Error type: "%s"' % type(e))
