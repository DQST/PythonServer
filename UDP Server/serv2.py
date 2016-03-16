from os import *
from threading import *
from time import *
from socket import *
from sys import argv


class Server:
	'''Server constructor'''
	def __init__(self, args=()):
		self.sock = socket(AF_INET, SOCK_DGRAM)
		self.sock.bind(args)
		self.lastTime = 0
		self.WORK = True

	'''Send message here'''
	def SendTo(self, msg, endPoint):
		self.sock.sendto(bytes(msg, 'utf-8'), endPoint)

	'''Recieve input message'''
	def Recieve(self):
		while self.WORK:
			inputData = self.sock.recvfrom(1024)
			curTime = time()
			PING = (curTime - self.lastTime) * 100
			self.lastTime = curTime

			data, addr = inputData
			message = data.decode('utf-8')
			
			print('Addr: ' + str(addr) + ', message: ' + message)
			self.SendTo("Hello!", addr)
		else:
			print('Recieve be stoped.')

	'''At this must be show data about clients'''
	def Update(self):
		pass

	'''Stop server here'''
	def Stop(self):
		self.WORK = False


if __name__ == '__main__':
	argsList = None

	if len(argv) > 1:
		argsList = (argv[1], argv[2])
	else:
		argsList = ('127.0.0.1',14801)
	
	server = Server(argsList)

	updateT = Thread(name='update', target=server.Update)
	recieveT = Thread(name='recieve', target=server.Recieve)
	updateT.start()
	recieveT.start()
	while True:
		command = input('> ')

		'''Stop server'''
		if command == 'exit':
			server.Stop()
			updateT.join()
			recieveT.join()
			break
