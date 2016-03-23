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
		

class Rooms:
	def __init__(self):
		self.ROOM_HASH = {}
		self.__ROOM_ID__ = 0

	def Add(self, name, host):
		if [name, host] in self.ROOM_HASH.values() == False or len(self.ROOM_HASH) <= 0:
			self.ROOM_HASH[self.__ROOM_ID__] = [name, host]
			self.__ROOM_ID__ += 1
			return True
		return False

	def GetHostByName(self, name):
		for i in self.ROOM_HASH:
			if self.ROOM_HASH[i][0] == name:
				return self.ROOM_HASH[i][1]
		return None

	def RemoveHost(self, name):
		for i in self.ROOM_HASH:
			if self.ROOM_HASH[i][0] == name:
				del self.ROOM_HASH[i]
				break

class Server:
	rooms = Rooms()

	'''Server constructor'''
	def __init__(self, args=()):
		self.sock = socket(AF_INET, SOCK_DGRAM)
		self.sock.bind(args)
		self.lastTime = 0
		self.WORK = True

	def ParseData(self, inputData, ping, time):
		data, addr = inputData
		message = data.decode('utf-8')

		ip_addr = str(addr[0]) + ':' + str(addr[1])

		arr = message.split(':')
		protocol_ver = arr[0][:4]
		command = arr[0][4:]

		if protocol_ver == '0042':
			if command == 'nop':
				pass
			elif command == 'newroom':
				res = self.rooms.Add(arr[1], ip_addr)
				if res == False:
					self.SendTo('Error, room "%s" already exist!' % arr[1], addr)
				else:
					self.SendTo('Room "%s" has been create!' % arr[1], addr)
			elif command == 'contoroom':
				res = self.rooms.GetHostByName(arr[1])
				if res != None:
					self.SendTo('tryconto:' + res, addr)
					args = res.split(':')
					self.SendTo('tryconto:' + addr[0]+':'+str(addr[1]), (args[0], int(args[1])))
				else:
					self.SendTo('Room %s not found!' % arr[1], addr)
			elif command == 'msg':
				self.SendTo('Hello from Server!', addr)

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

	'''Stop server here'''
	def Stop(self):
		self.WORK = False


if __name__ == '__main__':
	argsList = None

	if len(argv) > 1:
		argsList = (argv[1], argv[2])
	else:
		argsList = ('0.0.0.0',14801)
	
	server = Server(argsList)

	# updateT = Thread(name='update', target=server.Update)
	recieveT = Thread(name='recieve', target=server.Recieve)
	# updateT.start()
	recieveT.start()
	while True:
		arr = input('> ')

		'''Stop server'''
		if arr == 'exit':
			server.Stop()
			# updateT.join()
			recieveT.join()
			break
