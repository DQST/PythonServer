import socket
import os
import time
import sys
from threading import *


class Server:
	roomList = {}
	roomID = 0
	userList = {}
	sock = None
	last_time = 0
	_update_time = 1
	
	def __init__(self, port, time):
		print("Server running...")
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(("", port))
		self._update_time = time
	
	def cls(self):
		os.system('cls' if os.name=='nt' else 'clear')
	
	def ShowUserList(self):
		self.cls()
		print('Server running...')
		if len(self.userList) == 0:
			print('No connections to server...')
		for	i in self.userList:
			print('|\t' + i + '\t|\t' + self.userList[i][0] + '\t|\t' + str(round(self.userList[i][1])) + 'ms\t|')
		time.sleep(self._update_time)
	
	def UpdateUserList(self):
		for i in self.userList:
			last_time = self.userList[i][2]
			delta = (time.time() - last_time) * 100
			if delta >= 100:
				print(delta)
				self.userList.pop(i)
				if len(self.userList) > 0:
					continue
				else:
					break;
	
	def RunUpdate(self):
		while True:
			self.ShowUserList()
			self.UpdateUserList()
	
	def Recieve(self):
		while True:
			data = self.sock.recvfrom(1024)
			current_time = time.time()
			ping = (current_time - self.last_time) * 100
			self.last_time = current_time
			
			msg = data[0].decode("utf-8")
			addr = data[1]
			
			if msg:
				arr = msg.split(":")
				if arr[0] == "0042nop":
					self.userList[arr[1]] = [addr[0]+':'+str(addr[1]), ping, time.time()]
					continue
				elif arr[0] == "createroom":
					self.roomList[arr[1]]={'id':self.roomID,'host':addr[0],'port':int(addr[1])}
					self.roomID += 1;
					self.Send(bytes("Add new room:" + arr[1], 'utf-8'), addr)
					continue
				
				self.Send(b"Hello from UDP Python Server!", addr)
	
	def Send(self, msg, remoteAddr):
		self.sock.sendto(msg, remoteAddr)
	
	def Close(self):
		self.sock.close()

if __name__ == '__main__':
	inputData = sys.argv
	server = None
	if len(inputData) > 1:
		server = Server(int(inputData[1]), int(inputData[2]))
	else:
		server = Server(14801, 1)
	t = Thread(name='t1', target=server.RunUpdate)
	t.start()
	server.Recieve()
	server.Close()
	t.join()
