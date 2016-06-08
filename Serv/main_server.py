import json
import logging
import threading
import socket
import os
import hashlib
import sqlite3
import datetime


logging.basicConfig(filename='log.txt', filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s')


def get_hash(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def get_olo(method, args):
    olo = {'ver': '0042', 'method': method, 'params': args}
    return json.dumps(olo)


def get_datetime():
    date_now = datetime.datetime.now()
    return date_now.strftime('%d.%m.%y %H:%M')


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
        logging.warning('Запуск сервера...')
        logging.warning('Проверка рабочих директорий...')
        print('Запуск сервера...')
        print('Проверка рабочих директорий...')
        path = os.getcwd() + '/downloads/'
        if os.path.exists(path) is False:
            logging.warning('Создание директорий...')
            print('Создание директорий...')
            os.mkdir(path)

        con = sqlite3.connect('base.db')

        logging.warning('Проверка базы...')
        print('Проверка базы...')
        try:
            con.execute('SELECT * FROM Users')
            logging.warning('База статус: ОК')
            print('База статус: ОК')
        except sqlite3.OperationalError:
            logging.warning('Создание базы...')
            print('Создание базы...')
            con.executescript('''
                CREATE TABLE Users (
                    user_id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                    user_login	TEXT NOT NULL,
                    user_pass	TEXT NOT NULL,
                    user_name	TEXT NOT NULL,
                    user_ip     TEXT NOT NULL
                );
                CREATE TABLE Rooms (
                    room_id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                    room_name	TEXT NOT NULL,
                    room_pass	TEXT NOT NULL,
                    owner_id	INTEGER NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES Users(user_id)
                );
                CREATE TABLE Users_Rooms (
                    id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                    user_id	INTEGER,
                    room_id	INTEGER,
                    FOREIGN KEY(user_id) REFERENCES Users(user_id),
                    FOREIGN KEY(room_id) REFERENCES Rooms(room_id)
                );
                CREATE TABLE History (
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
        logging.warning('Остановка сервера!')
        print('Остановка сервера!')

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
        room_name, user_name, room_pass = args[1]
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT room_id FROM Rooms WHERE room_name = ?', (room_name,))
        l = rez.fetchall()
        if len(l) == 0:
            rez = con.execute('SELECT user_id FROM Users WHERE user_name = "%s"' % user_name)
            l = rez.fetchall()
            if len(l) > 0:
                _id = l[0][0]
                con.execute('INSERT INTO Rooms(room_name, room_pass, owner_id) values("%s", "%s", %d)' %
                            (room_name, get_hash(room_pass), _id))
                con.commit()
        else:
            olo = get_olo('error', ('Комната "%s" уже существует!' % room_name,))
            self.send(olo, args[0])
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
        cur = con.execute('SELECT room_id FROM Rooms WHERE room_name = ? and room_pass = ?',
                          (room_name, get_hash(room_pass)))
        l = cur.fetchall()
        if len(l) > 0:
            room_id = l[0][0]
            rez = con.execute('SELECT user_id FROM Users WHERE user_name = ?', (user_name,))
            user_id = rez.fetchall()[0][0]
            rez = con.execute('SELECT user_id FROM Users_Rooms WHERE user_id = ? AND room_id = ?', (user_id, room_id))
            if len(rez.fetchall()) == 0:
                con.execute('INSERT INTO Users_Rooms(user_id, room_id) VALUES(?, ?)', (user_id, room_id))
                con.commit()
                olo = get_olo('con_to', [room_name])
                self.send(olo, args[0])
                self.broadcast_all_in_room(args[0], (room_name, 'Сервер', 'Пользователь %s присоеденился к комнате' %
                                                     user_name))
            else:
                olo = get_olo('error', ['Вы уже подключены к этой комнате!'])
                self.send(olo, args[0])
        else:
            olo = get_olo('error', ['Неверный пароль!'])
            self.send(olo, args[0])
        con.close()
        users = self.get_users(room_name)
        self.broadcast_all_in_room(args[0], (room_name, 'Сервер', users), method='push_users')

    @decorator
    def change_nickname(self, *args):
        user_id, user_name = args[1]
        con = sqlite3.connect('base.db')
        con.execute('UPDATE Users SET user_name = ? WHERE user_id = ?', (user_name, user_id))
        con.commit()
        con.close()
        olo = get_olo('set_nickname', [user_name])
        self.send(olo, args[0])

    @decorator
    def broadcast_all_in_room(self, *args, method='push_message'):
        room_name, user_name, message = args[1]
        con = sqlite3.connect('base.db')
        cur = con.execute('SELECT room_id FROM Rooms WHERE room_name = "%s"' % room_name)
        l = cur.fetchall()
        if len(l) > 0:
            room_id = l[0][0]
            id_list = []
            rez = con.execute('SELECT DISTINCT user_id FROM Users_Rooms WHERE room_id = %d' % room_id)
            for i in rez.fetchall():
                id_list.append(i[0])

            user_ip_list = []
            for i in id_list:
                rez = con.execute('SELECT DISTINCT user_ip FROM Users WHERE user_id = %d' % i)
                for j in rez.fetchall():
                    user_ip_list.append(j)
            if method != 'push_users':
                con.execute('INSERT INTO History(room_id, send_date, sender, message) VALUES(?, ?, ?, ?)',
                            (room_id, get_datetime(), user_name, message))
                con.commit()
            if len(user_ip_list) > 0:
                for i in user_ip_list:
                    ip, port = i[0].split(':')
                    time = get_datetime().split(' ')[1]
                    olo = get_olo(method, (room_name, '{0} {1}'.format(time, user_name), message))
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
        self.broadcast_all_in_room(args[0], (room_name, 'Сервер', 'Пользователь %s отключился от комнаты' % user_name))
        users = self.get_users(room_name)
        self.broadcast_all_in_room(args[0], (room_name, 'Сервер', users), method='push_users')

    @decorator
    def get_history(self, *args):
        room_name = args[1][0]
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT room_id FROM Rooms WHERE room_name = "%s"' % room_name)
        room_id = rez.fetchall()[0][0]
        rez = con.execute('SELECT send_date, sender, message FROM History WHERE room_id = %d AND NOT sender = "Сервер"'
                          % room_id)
        l = rez.fetchall()
        current_date, current_time = get_datetime().split(' ')
        if len(l) > 0:
            for i in l:
                date, time = i[0].split(' ')
                sender = i[1]
                message = i[2]
                if date == current_date:
                    date_time_str = time
                else:
                    date_time_str = '{0} {1}'.format(date, time)
                olo = get_olo('push_message', [room_name, '{0} {1}'.format(date_time_str, sender), message])
                self.send(olo, args[0])
        con.close()

    @staticmethod
    def get_users(room_name):
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT room_id FROM Rooms WHERE room_name = "%s"' % room_name)
        room_id = rez.fetchall()[0][0]
        rez = con.execute('SELECT user_id FROM Users_Rooms WHERE room_id = %d' % room_id)
        user_id_list = []
        for i in rez.fetchall():
            user_id_list.append(i[0])
        users = []
        for i in user_id_list:
            rez = con.execute('SELECT user_name FROM Users WHERE user_id = %d' % i)
            rez = rez.fetchall()
            users.append(rez[0][0])
        con.close()
        return users

    @decorator
    def file_load(self, *args):
        self.broadcast_all_in_room(*args, method='push_file')

    @decorator
    def login(self, *args):
        _ip, _port = args[0]
        input_login = args[1][0]
        input_pass = get_hash(args[1][1])
        con = sqlite3.connect('base.db')
        rez = con.execute('SELECT user_id, user_name FROM Users WHERE user_login = "%s" AND user_pass = "%s"' %
                          (input_login, input_pass))
        l = rez.fetchall()
        if len(l) > 0:
            con.execute('UPDATE Users SET user_ip = "%s" WHERE user_login = "%s"' %
                        (_ip + ':' + str(_port), input_login))
            con.commit()
            olo = get_olo('enter', ('Добро пожаловать %s!' % l[0][1], l[0][1], l[0][0]))
        else:
            olo = get_olo('error', ('Ошибка, неверный логин или пароль.',))
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
