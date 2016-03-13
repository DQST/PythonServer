import socket
import time


class Server:
	roomList = {}
	roomID = 0
	sock = None
	last_time = 0
	
	def __init__(self, port):
		print("Server running...")
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(("", port))

	def Recieve(self):
		while True:
			data = self.sock.recvfrom(1024)
			current_time = time.time()
			ping = current_time - self.last_time
			self.last_time = current_time
			
			# print("Ping: " + str(ping))
			
			msg = data[0].decode("utf-8")
			addr = data[1]
			
			if not msg:
				pass
			else:
				arr = msg.split(":")
				if arr[0] == "nop":
					continue
				elif arr[0] == "createroom":
					self.roomList[arr[1]]={'id':self.roomID,'host':addr[0],'port':int(addr[1])}
					self.roomID += 1;
					self.Send(bytes("Add new room:" + arr[1], 'utf-8'), addr)
					continue
				
				# print("[" + addr[0] + ":" + str(addr[1]) + "] > " + msg)
				self.Send(b"Hello from UDP Python Server!", addr)
	
	def Send(self, msg, remoteAddr):
		self.sock.sendto(msg, remoteAddr)
	
	def Close(self):
		self.sock.close()

server = Server(14801)
server.Recieve()
server.Close()
