import socket
import os
from threading import Thread


I = 0


class ClientThread(Thread):
    def __init__(self, sock):
        Thread.__init__(self)
        self.sock = sock

    def run(self):
        global I
        while True:
            data = self.sock.recv(1028)

            head = data[:4]
            if head == b'0001':
                path = os.getcwd() + '/downloads/.part_' + str(I)
                f = open(path, 'ab')
                f.write(data[4:])
                f.close()

            if head == b'0002':
                h, file_name = data.decode('utf-8').split(':')
                path = os.getcwd() + '/downloads/'
                if os.path.exists(path + '.part_' + str(I)) is True:
                    os.rename(path + '.part_' + str(I), path + file_name)
                    I += 1

            if head == b'0003':
                h, file_name = data.decode('utf-8').split(':')
                path = os.getcwd() + '/downloads/' + file_name
                if os.path.exists(path) is True:
                    f = open(path, 'rb')
                    buf = b'0001'
                    buf += f.read(1024)
                    while True:
                        self.sock.send(buf)
                        buf = b'0001' + f.read(1024)
                        if buf == b'0001':
                            break
                    f.close()
                    buf = b'0002:' + file_name.encode('utf-8') + b':'
                    self.sock.send(buf)
                    data = None
                    os.remove(path)

            if not data:
                self.sock.close()
                break

tcpsock = socket.socket()
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpsock.bind(('0.0.0.0', 14801))
tcpsock.listen(10)
threads = []

while True:
    conn, ip = tcpsock.accept()
    new_thread = ClientThread(conn)
    new_thread.start()
    threads.append(new_thread)

for i in threads:
    i.join()
