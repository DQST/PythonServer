import os
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
		self.__ROOM_HASH__ = {}
		self.Log('%s | Server running...' % self.GetFormatTime())

	def Log(self, msg, logFile='log.txt'):
		f = open(logFile, 'a')
		f.write(msg + '\n')
		f.close()

	def GetFormatTime(self):
		ti = localtime()
		return '{0}.{1}.{2} {3}:{4}:{5}'.format(ti[2], ti[1], ti[0], ti[3], ti[4], ti[5])

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
					self.Log('{2} | [{0}] Error "{1}" already exist!'.format(ip_addr, arr[1], self.GetFormatTime()))
				else:
					self.__ROOM_HASH__[arr[1]] = addr
					self.SendTo('Room "%s" has been create!' % arr[1], addr)
					self.Log('{2} | [{0}] Create room "{1}"'.format(ip_addr, arr[1], self.GetFormatTime()))
			elif command == 'contoroom':
				res = None
				if arr[1] in self.__ROOM_HASH__.keys():
					res = self.__ROOM_HASH__[arr[1]]
				
				if res != None:
					newAdr = res[0] + ':' + str(res[1])
					self.SendTo('tryconto:' + newAdr, addr)
					self.SendTo('tryconto:' + addr[0]+':'+str(addr[1]), res)
				else:
					self.SendTo('Room "%s" not found!' % arr[1])
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
			self.Log('{0} | Recieve stoped.'.format(self.GetFormatTime()))

	def cls(self):
		os.system('cls' if os.name == 'nt' else 'clear')

	'''Stop server here'''
	def Stop(self):
		self.WORK = False
		self.Log('%s | Server stoped!' % self.GetFormatTime())
		self.SendTo('Stop...', ('127.0.0.1', 14801))
		self.sock.close()


if __name__ == '__main__':
	argsList = None

	if len(argv) > 1:
		argsList = (argv[1], argv[2])
	else:
		argsList = ('0.0.0.0',14801)
	
	server = Server(argsList)
	recieveT = Thread(name='recieve', target=server.Recieve)
	recieveT.start()
	while True:
		arr = input('> ')

		'''Stop server'''
		if arr == 'exit':
			server.Stop()
			recieveT.join()
			break
