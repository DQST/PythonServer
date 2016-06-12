import socket

i = 0


def start():
    global i
    s = socket.socket()
    s.bind(('', 14801))
    s.listen(10)

    while True:
        sc, address = s.accept()
        print('input connection: {0}'.format(address))

        with open('file_%d.vf' % i, 'w+b') as file:
            while True:
                l = sc.recv(1024)
                while l:
                    file.write(l)
                    l = sc.recv(1024)

        sc.close()

    s.close()

start()
