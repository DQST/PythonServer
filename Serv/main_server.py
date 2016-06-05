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


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 14801))
        self.__WORK__ = True
        self.__service__ = Service(self)

    def start(self):
        super().start()
        logging.warning('Start Server...')
        print('Start Server...')
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
                    room_pass	TEXT NOT NULL,
                    owner_id	INTEGER NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES Users(user_id)
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

    @decorator
    def add_room(self, *args):
        ip, port = args[0]
        room_name, user_name, room_pass = args[1]
        con = sqlite3.connect('base.db')
        zap = con.execute('SELECT user_id FROM Users WHERE user_name = "%s"' % user_name)
        l = zap.fetchall()
        if len(l) > 0:
            _id = l[0][0]
            con.execute('INSERT INTO Rooms(room_name, room_pass, owner_id) values("%s", "%s", %d)' %
                        (room_name, get_hash(room_pass), _id))
            con.commit()
        else:
            pass    # TODO: This must be message if room exists
        con.close()
        self.get_rooms(*args)

    @decorator
    def del_room(self, *args):
        room_name, user_name = args[1]
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT user_id FROM Users WHERE user_name = "%s"' % user_name)
        user_id = rez.fetchall()[0][0]
        con.execute('DELETE FROM Rooms WHERE owner_id = %d and room_name = "%s"' % (user_id, room_name))
        con.commit()
        con.close()
        self.get_rooms(*args)

    @decorator
    def get_rooms(self, *args):
        con = sqlite3.connect('base.db')
        cur = con.execute('SELECT room_name FROM Rooms')
        arr = []
        for i in cur:
            arr.append(i[0])
        con.close()
        olo = get_olo('room_list', json.dumps(arr))
        self.send(olo, args[0])

    @decorator
    def con_to(self, *args):
        room_name, user_name, room_pass = args[1]
        con = sqlite3.connect('base.db')
        cur = con.execute('SELECT room_id FROM Rooms WHERE room_name = "%s" and room_pass = "%s"' %
                          (room_name, get_hash(room_pass)))
        l = cur.fetchall()
        if len(l) > 0:
            room_id = l[0][0]
            rez = con.execute('SELECT user_id FROM Users WHERE user_name = "%s"' % user_name)
            user_id = rez.fetchall()[0][0]
            con.execute('INSERT INTO Users_Rooms(user_id, room_id) VALUES(%d, %d)' % (user_id, room_id))
            con.commit()
            olo = get_olo('con_to', [room_name])
            self.send(olo, args[0])
            self.broadcast_all_in_room(args[0], (room_name, 'Сервер', 'Пользователь "%s" присоеденился к комнате' %
                                                 user_name))
        else:
            pass    # TODO: This must be message about incorrect password
        con.close()

    @decorator
    def broadcast_all_in_room(self, *args):     # TODO: Save history of message in table!
        room_name, user_name, message = args[1]
        con = sqlite3.connect('base.db')
        cur = con.execute('SELECT room_id FROM Rooms WHERE room_name = "%s"' % room_name)
        l = cur.fetchall()
        if len(l) > 0:
            room_id = l[0][0]
            rez = con.execute('''
                SELECT user_ip FROM Users as us WHERE EXISTS
                (SELECT user_id FROM Users_Rooms as us_ro WHERE us.user_id = us_ro.user_id AND room_id = %d)
            ''' % room_id)
            l = rez.fetchall()
            if len(l) > 0:
                for i in l:
                    ip, port = i[0].split(':')
                    olo = get_olo('push_message', [room_name, user_name, message])
                    self.send(olo, (ip, int(port)))
        con.close()

    @decorator
    def disconnect_from(self, *args):
        room_name, user_name = args[1]
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT user_id FROM Users WHERE user_name = "%s"' % user_name)
        user_id = rez.fetchall()[0][0]
        rez = con.execute('SELECT room_id FROM Rooms WHERE room_name = "%s"' % room_name)
        room_id = rez.fetchall()[0][0]
        con.execute('DELETE FROM Users_Rooms WHERE user_id = %d and room_id = %d' % (user_id, room_id))
        con.commit()
        con.close()
        self.broadcast_all_in_room(args[0], (room_name, 'Сервер', 'Пользователь "%s" отключился от комнаты' %
                                             user_name))

    @decorator
    def file_load(self, *args):
        user_ip = args[0]
        room_name = args[1][0]
        user_name = args[1][1]
        message = args[1][2]
        # self.__rooms__.broadcast(room_name, user_name, message, user_ip, self, 'push_file')

    @decorator
    def login(self, *args):
        _ip, _port = args[0]
        input_login = args[1][0]
        input_pass = get_hash(args[1][1])
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT user_id, user_name FROM Users WHERE user_login = "%s" AND user_pass = "%s"' %
                          (input_login, input_pass))
        olo = None
        l = rez.fetchall()
        if len(l) > 0:
            con.execute('UPDATE Users SET user_ip = "%s" WHERE user_login = "%s"' %
                        (_ip + ':' + str(_port), input_login))
            con.commit()
            olo = get_olo('enter', ['Добро пожаловать %s!' % l[0][1], l[0][1]])
        else:
            olo = get_olo('error', ['Ошибка, неверный логин или пароль.'])
        self.send(olo, args[0])
        con.close()

    @decorator
    def register(self, *args):
        _ip, _port = args[0]
        new_login = args[1][0]
        new_nickname = args[1][1]
        new_pass = args[1][2]
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT user_id FROM Users WHERE user_login = "%s"' % new_login)
        if len(rez.fetchall()) > 0:
            olo = get_olo('error', ['Ошибка, такой аккаунт уже зарегестрирован!'])
            self.send(olo, args[0])
        else:
            con.execute('INSERT INTO users(user_login, user_pass, user_name, user_ip) VALUES("%s", "%s", "%s", "%s")' %
                        (new_login, get_hash(new_pass), new_nickname, _ip + ':' + str(_port)))
            con.commit()
            olo = get_olo('reg_ok', ['Регистрация прошла успешно!'])
            self.send(olo, args[0])
        con.close()

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
