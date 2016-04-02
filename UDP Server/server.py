import os
import json
from threading import *
from time import *
from socket import *
from sys import argv

'''Help class'''
class Help:
	@staticmethod
	def log(msg, file='log.txt'):
		f = open(file, 'a')
		f.write('{0} | {1}\n'.format(Help.ge_format_time(), msg))
		f.close()

	@staticmethod
	def ge_format_time():
		ti = localtime()
		return '{0}.{1}.{2} {3}:{4}:{5}'.format(ti[2], ti[1], ti[0], ti[3], ti[4], ti[5])

'''Config class.'''
class Config:
	@staticmethod
	def save(obj, path):
		data = json.dumps(obj, sort_keys=True, indent=4, separators=(',',': '))
		f = open(path, 'w')
		f.write(data)
		f.close()

	@staticmethod
	def load(path):
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
			self.__ROOM_HASH__ = Config.load('table.json')

			'''Convert list to tuple'''
			for i in self.__ROOM_HASH__:
				ip_adr = self.__ROOM_HASH__[i][0]
				port = self.__ROOM_HASH__[i][1]
				self.__ROOM_HASH__[i] = (ip_adr, port)
		else:
			self.__ROOM_HASH__ = {}
		
		Help.log('Server running...')

	def parse_data(self, inputData, ping, time):
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
				if (arr[1] in self.__ROOM_HASH__.keys()) is True:
					self.send_to('Error, room "%s" already exist!' % arr[1], addr)
					Help.log('[{0}] Error "{1}" already exist!'.format(ip_addr, arr[1]))
				else:
					self.__ROOM_HASH__[arr[1]] = addr
					self.send_to('Room "%s" has been create!' % arr[1], addr)
					Help.log('[{0}] Create room "{1}"'.format(ip_addr, arr[1]))
			elif command == 'contoroom':
				res = None
				if arr[1] in self.__ROOM_HASH__.keys():
					res = self.__ROOM_HASH__[arr[1]]

				if res == addr:
					self.send_to('You already connect to room: "%s"' % arr[1], addr)
					Help.log('Try connect [%s] with himself.' % ip_addr)
					return

				'''Do something with this shit!!!!'''
				if res is not None:
					user1 = res[0] + ':' + str(res[1])
					user2 = addr[0]+':'+str(addr[1])
					self.send_to('tryconto$' + user1 + '$' + arr[1], addr)
					self.send_to('tryconto$' + user2 + '$' + arr[1], res)
					Help.log('[{0}] connect to [{1}]'.format(addr, res))
				else:
					self.send_to('Room "%s" not found!' % arr[1])
			elif command == 'get_rooms':
				json_str = json.dumps(self.__ROOM_HASH__)
				self.send_to('rooms_list$%s' % json_str, addr)
			elif command == 'msg':
				self.send_to('Hello from Server!', addr)

	'''Send message here'''
	def send_to(self, msg, endPoint):
		self.sock.sendto(bytes(msg, 'utf-8'), endPoint)

	'''receive input message'''
	def receive(self):
		try:
			while self.WORK:
				inputData = self.sock.recvfrom(1024)
				curTime = time()
				PING = (curTime - self.lastTime) * 100
				self.lastTime = curTime

				'''Parse input data'''
				self.parse_data(inputData, PING, curTime)
			else:
				Help.log('receive stopped.')
		except Exception as e:
			Help.log('---------------------')
			Help.log('Server Error!')
			Help.log('Error type: "%s"' % type(e))
			Help.log('Error args: "%s"' % str(e.args))
			Help.log('Error args: "%s"' % str(e))
			Help.log('---------------------')

	def cls(self):
		os.system('cls' if os.name == 'nt' else 'clear')

	'''stop server here'''
	def stop(self):
		self.WORK = False
		Help.log('Server stopped!')
		self.send_to('Stop...', ('127.0.0.1', 14801))
		Config.save(self.__ROOM_HASH__, 'table.json')
		self.sock.close()

switch = {'rooms': lambda x: [print('"{0}" {1}'.format(i, x[i])) for i in x]}

if __name__ == '__main__':
	argsList = None

	if len(argv) > 1:
		argsList = (argv[1], argv[2])
	else:
		argsList = ('0.0.0.0', 14801)

	server = Server(argsList)
	receiveThread = Thread(name='receive', target=server.receive)
	receiveThread.start()

	try:
		while True:
			arr = input('> ')

			'''stop server'''
			if arr == 'exit':
				server.stop()
				receiveThread.join()
				break
			else:
				if (arr in switch.keys()) is True:
					switch[arr](server.__ROOM_HASH__)
				else:
					print('Command "%s" not found!' % arr)
	except Exception as e:
		Help.log('Server Error!')
		Help.log('Error type: "%s"' % type(e))
