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

		self.UserList = {}
		self.ROOM_HASH = {}

	def ParseData(self, inputData, ping):
		data, addr = inputData
		message = data.decode('utf-8')

		ip_addr = str(addr[0]) + ':' + str(addr[1])

		# command = message.split(':')
		# if command[0] == '0042nop':
		# 	self.UserList = [command[1], ip, ping]
		# elif command[0] == '0042mkroom':
		# 	self.ROOM_HASH[command[1]] = ip
		# elif command[0] == '0042delroom':
		# 	del self.ROOM_HASH[command[1]]
		# elif command[0] == '0042conto':
		# 	room_ip = self.ROOM_HASH[command[1]]
		# 	self.SendTo('0042roomip:' + command[1] + ':' + room_ip, addr)

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

			'''Parse input data'''
			self.ParseData(inputData)
		else:
			print('Recieve be stoped.')

	'''At this must be show data about clients'''
	def Update(self):
		for i in self.UserList:
			ping = (time() - self.UserList[i][2]) * 100
			if ping >= 100:
				del self.UserList[i]

		for i in self.UserList:
			print('|\t' + i + '\t|\t' + self.UserList[i][1] +
				'\t|\t' + self.UserList[i][2]+ '\t|')

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
