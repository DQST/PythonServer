import os
import json
from threading import *
from time import *
from socket import *
from sys import argv

'''Help class'''
class Help:
	@staticmethod
	def Log(msg, file='log.txt'):
		f = open(file, 'a')
		f.write('{0} | {1}\n'.format(Help.GetFormatTime(), msg))
		f.close()

	@staticmethod
	def GetFormatTime():
		ti = localtime()
		return '{0}.{1}.{2} {3}:{4}:{5}'.format(ti[2], ti[1], ti[0], ti[3], ti[4], ti[5])

'''Config class.'''
class Config:
	@staticmethod
	def Save(obj, path):
		data = json.dumps(obj, sort_keys=True, indent=4, separators=(',',': '))
		f = open(path, 'w')
		f.write(data)
		f.close()

	@staticmethod
	def Load(path):
		f = open(path)
		data = f.read()
		f.close()
		return json.loads(data)

'''Server class'''
class Server:
	'''Server constructor'''
	def __init__(self, args=()):
		self.sock = socket(AF_INET, SOCK_DGRAM)
		self.sock.bind(args)
		self.lastTime = 0
		self.WORK = True
		self.UsersOnline = []

		if os.path.exists('table.json'):
			self.__ROOM_HASH__ = Config.Load('table.json')

			'''Convert list to tuple'''
			for i in self.__ROOM_HASH__:
				IP_ADR = self.__ROOM_HASH__[i][0]
				PORT = self.__ROOM_HASH__[i][1]
				self.__ROOM_HASH__[i] = (IP_ADR, PORT)
		else:
			self.__ROOM_HASH__ = {}
		
		Help.Log('Server running...')

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
				if arr[1] in self.__ROOM_HASH__.keys():
					self.SendTo('Error, room "%s" already exist!' % arr[1], addr)
					Help.Log('[{0}] Error "{1}" already exist!'.format(ip_addr, arr[1]))
				else:
					self.__ROOM_HASH__[arr[1]] = addr
					self.SendTo('Room "%s" has been create!' % arr[1], addr)
					Help.Log('[{0}] Create room "{1}"'.format(ip_addr, arr[1]))
			elif command == 'contoroom':
				res = None
				if arr[1] in self.__ROOM_HASH__.keys():
					res = self.__ROOM_HASH__[arr[1]]

				if res == addr:
					self.SendTo('You already connect to room: "%s"' % arr[1], addr)
					Help.Log('Try connect [%s] with himself.' % ip_addr)
					return

				if res != None:
					newAdr = res[0] + ':' + str(res[1])
					self.SendTo('tryconto:' + newAdr, addr)
					self.SendTo('tryconto:' + addr[0]+':'+str(addr[1]), res)
					Help.Log('[{0}] connect to [{1}]'.format(addr, res))
				else:
					self.SendTo('Room "%s" not found!' % arr[1])
			elif command == 'msg':
				self.SendTo('Hello from Server!', addr)

	'''Send message here'''
	def SendTo(self, msg, endPoint):
		self.sock.sendto(bytes(msg, 'utf-8'), endPoint)

	'''Recieve input message'''
	def Recieve(self):
		try:	
			while self.WORK:
				inputData = self.sock.recvfrom(1024)
				curTime = time()
				PING = (curTime - self.lastTime) * 100
				self.lastTime = curTime

				'''Parse input data'''
				self.ParseData(inputData, PING, curTime)
			else:
				Help.Log('Recieve stoped.')
		except Exception as e:
			Help.Log('Server Error!')
			Help.Log('Error type: "%s"' % type(e))
			Help.Log('Error args: "%s"' % e.args)

	def cls(self):
		os.system('cls' if os.name == 'nt' else 'clear')

	'''Stop server here'''
	def Stop(self):
		self.WORK = False
		Help.Log('Server stoped!')
		self.SendTo('Stop...', ('127.0.0.1', 14801))
		Config.Save(self.__ROOM_HASH__, 'table.json')
		self.sock.close()

switch = {'rooms': lambda x: [print('"{0}" {1}'.format(i,x[i])) for i in x]}

if __name__ == '__main__':
	argsList = None

	if len(argv) > 1:
		argsList = (argv[1], argv[2])
	else:
		argsList = ('0.0.0.0',14801)
	
	server = Server(argsList)
	recieveT = Thread(name='recieve', target=server.Recieve)
	recieveT.start()

	try:
		while True:
			arr = input('> ')

			'''Stop server'''
			if arr == 'exit':
				server.Stop()
				recieveT.join()
				break
			else:
				if (arr in switch.keys()) == True:
					switch[arr](server.__ROOM_HASH__)
				else:
					print('Command "%s" not found!' % arr)
	except Exception as e:
		Help.Log('Server Error!')
		Help.Log('Error type: "%s"' % type(e))
