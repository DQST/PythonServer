from os import *
from threading import *
from time import *
from socket import *
from sys import argv

class UserData:
	"""docstring for User"""
	def __init__(self, ip, ping, time):
		self.IPAddr = ip
		self.Ping = ping
		self.Time = time

	def ToString(self):
		return '|\t{0}\t|\t{1}ms\t|'.format(self.IPAddr, round(self.Ping, 2))
		

class Server:
	'''Server constructor'''
	def __init__(self, args=()):
		self.sock = socket(AF_INET, SOCK_DGRAM)
		self.sock.bind(args)
		self.lastTime = 0
		self.WORK = True

		self.UserList = {}
		self.ROOM_HASH = {}

	def ParseData(self, inputData, ping, time):
		data, addr = inputData
		message = data.decode('utf-8')

		ip_addr = str(addr[0]) + ':' + str(addr[1])

		arr = message.split(':')
		protocol_ver = arr[0][:4]
		command = arr[0][4:]

		if protocol_ver == '0042':
			if command == 'nop':
				name = arr[1]
				self.UserList[name] = UserData(ip_addr, ping, time)
			else:
				self.SendTo("Hello from Server!", addr)

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
			self.ParseData(inputData, PING, curTime)
		else:
			print('Recieve stoped.')

	def cls(self):
		system('cls' if name == 'nt' else 'clear')

	def ShowUserList(self):
		if len(self.UserList) <= 0:
			print('*********** No connecting ***********')

		for i in self.UserList:
			print('|\t%s\t%s' % (i, self.UserList[i].ToString()))

	'''At this must be show data about clients'''
	def Update(self):
		while  self.WORK:
			print('Connecting to server:')
			self.ShowUserList()
			for i in self.UserList:
				delta = (time() - self.UserList[i].Time) * 100
				if delta >= 100:
			 		del self.UserList[i]
			 		if len(self.UserList) > 0:
			 			continue
			 		else:
			 			break

			sleep(1)
			self.cls()

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
		arr = input('> ')

		'''Stop server'''
		if arr == 'exit':
			server.Stop()
			updateT.join()
			recieveT.join()
			break
