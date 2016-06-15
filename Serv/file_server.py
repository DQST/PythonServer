import socket
import os
import time

path = 'downloads/'
state = ''
select_file = ''


def start():
    global state
    global select_file
    s = socket.socket()
    s.bind(('', 14801))
    s.listen(10)

    while True:
        try:
            sc, address = s.accept()
            print('input connection: {0}'.format(address))

            while True:
                try:
                    command = sc.recv(1024).decode('utf-8')
                except:
                    sc.close()
                    break

                if command == 'create':
                    state = 'CREATE_FILE'
                elif command == 'loadfile':
                    state = 'LOAD_FILE'
                elif command == 'writeinselectfile':
                    state = 'WRITE_IN_SELECT_FILE'

                if state == 'CREATE_FILE':
                    file = sc.recv(1024).decode('utf-8')
                    select_file = path + file
                    open(select_file, 'w+b').close()
                elif state == 'LOAD_FILE':
                    file = sc.recv(1024).decode('utf-8')
                    if os.path.exists(path + file):
                        size = os.path.getsize(path + file)
                        rez = '%d' % size
                        byte_array = rez.encode('utf-8')
                        sc.send(byte_array)
                        time.sleep(1)
                        with open(path + file, 'r+b') as file:
                            data = file.read(1024)
                            while data:
                                sc.send(data)
                                com = sc.recv(1024).decode('utf-8')
                                if com == 'NEXT':
                                    data = file.read(1024)
                    sc.close()
                elif state == 'WRITE_IN_SELECT_FILE':
                    with open(select_file, 'w+b') as file:
                        l = sc.recv(1024)
                        sc.send(b'NEXT')
                        while l:
                            file.write(l)
                            sc.send(b'NEXT')
                            l = sc.recv(1024)
                    sc.close()
        except Exception as error:
            print(error)
    s.close()

if __name__ == '__main__':
    start()
