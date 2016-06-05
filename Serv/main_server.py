import json
import logging
import threading
import socket
import os
import pickle
import hashlib
import sqlite3


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
        path = os.getcwd() + '/downloads/'
        if os.path.exists(path) is False:
            os.mkdir(path)

        con = sqlite3.connect('base.db')

        try:
            con.execute('SELECT * FROM Users')
        except sqlite3.OperationalError:
            print('Создание таблиц...')
            con.execute('''
                CREATE TABLE Users (
                    user_id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                    user_login	TEXT NOT NULL,
                    user_pass	TEXT NOT NULL,
                    user_name	TEXT NOT NULL,
                    user_ip     TEXT NOT NULL
                )
            ''')
            con.execute('''
                CREATE TABLE Rooms (
                    room_id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                    room_name	TEXT NOT NULL,
                    room_pass	TEXT NOT NULL
                )
            ''')
            con.execute('''
                CREATE TABLE Users_Rooms (
                    id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                    user_id	INTEGER,
                    room_id	INTEGER,
                    FOREIGN KEY(user_id) REFERENCES Users(user_id),
                    FOREIGN KEY(room_id) REFERENCES Rooms(room_id)
                )
            ''')
            con.execute('''
                CREATE TABLE "History" (
                    hist_id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                    room_id	INTEGER,
                    send_date	TEXT,
                    sender	INTEGER,
                    message	TEXT,
                    FOREIGN KEY(room_id) REFERENCES Rooms(room_id),
                    FOREIGN KEY(sender) REFERENCES Users(user_id)
                )
            ''')
            con.commit()
        con.close()

    def stop(self):
        self.__WORK__ = False
        self.send('stop...', ('127.0.0.1', 14801))
        self.sock.close()
        self.__rooms__.save()
        logging.warning('Server stopped!')
        print('Server stopped!')

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

    # @decorator
    # def add_room(self, *args):
    #     user_ip = args[0]
    #     room_name, user_name, room_pass = args[1]
    #     users = Users()
    #     users.add(user_ip)
    #     self.__rooms__.add(room_name, {'users': users, 'pass': get_hash(room_pass), 'owner': user_name})
    #     olo = get_olo('con_to', [room_name])
    #     self.send(olo, user_ip)
    #     self.get_rooms(*args)
    #
    # @decorator
    # def del_room(self, *args):
    #     room_name, user_key = args[1]
    #     owner = self.__rooms__[room_name]['owner']
    #     if owner == user_key:
    #         self.__rooms__.remove(room_name)
    #         self.get_rooms(*args)
    #
    # @decorator
    # def con_to(self, *args):
    #     user_ip = args[0]
    #     room_name, user_name, room_pass = args[1]
    #     password = self.__rooms__[room_name]['pass']
    #     if get_hash(room_pass) == password:
    #         message = '--- Пользователь "%s" присоеденился ---' % user_name
    #         users = self.__rooms__[room_name]['users']
    #         users.add(user_ip)
    #         olo = get_olo('con_to', [room_name])
    #         self.send(olo, user_ip)
    #         self.__rooms__.broadcast(room_name, 'Сервер', message, user_ip, self)
    #
    # @decorator
    # def broadcast_all_in_room(self, *args):
    #     user_ip = args[0]
    #     room_name = args[1][0]
    #     user_name = args[1][1]
    #     message = args[1][2]
    #     self.__rooms__.broadcast(room_name, user_name, message, user_ip, self)
    #
    # @decorator
    # def get_rooms(self, *args):
    #     user_ip = args[0]
    #     data = self.__rooms__.get_rooms()
    #     olo = get_olo('room_list', data)
    #     self.send(olo, user_ip)
    #
    # @decorator
    # def disconnect_from(self, *args):
    #     user_ip = args[0]
    #     room_name = args[1][0]
    #     user_name = args[1][1]
    #     message = '--- Пользователь "%s" отсоеденился ---' % user_name
    #     self.__rooms__[room_name]['users'].remove(user_ip)
    #     self.__rooms__.broadcast(room_name, 'Сервер', message, user_ip, self)

    @decorator
    def file_load(self, *args):
        user_ip = args[0]
        room_name = args[1][0]
        user_name = args[1][1]
        message = args[1][2]
        self.__rooms__.broadcast(room_name, user_name, message, user_ip, self, 'push_file')

    @decorator
    def login(self, *args):
        input_login = args[1][0]
        input_pass = get_hash(args[1][1])
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT user_id, user_name FROM Users WHERE user_login = "%s" AND user_pass = "%s"' %
                          (input_login, input_pass))
        olo = None
        l = rez.fetchall()
        if len(l) > 0:
            olo = get_olo('enter', ['Добро пожаловать %s!' % l[0][1], l[0][1]])
        else:
            olo = get_olo('error', ['Ошибка, неверный логин или пароль.'])
        self.send(olo, args[0])
        con.close()

    @decorator
    def register(self, *args):
        new_login = args[1][0]
        new_nickname = args[1][1]
        new_pass = args[1][2]
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT user_id FROM Users WHERE user_login = "%s"' % new_login)
        if len(rez.fetchall()) > 0:
            olo = get_olo('error', ['Ошибка, такой аккаунт уже зарегестрирован!'])
            self.send(olo, args[0])
        else:
            con.execute('INSERT INTO users(user_login, user_pass, user_name) VALUES("%s", "%s", "%s")' %
                        (new_login, get_hash(new_pass), new_nickname))
            con.commit()
            olo = get_olo('reg_ok', ['Регистрация прошла успешно!'])
            self.send(olo, args[0])
        con.close()


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

    def broadcast(self, name, user, msg, input_ip, serv: Server, method='push_message'):
        if name in self.__rooms__.keys():
            users = self.__rooms__[name]['users']
            for i in users.get_users():
                if i != input_ip:
                    olo = get_olo(method, [name, user, msg])
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
