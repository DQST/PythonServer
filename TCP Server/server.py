import socket

print("Server running...")
sock = socket.socket()
sock.bind(("0.0.0.0", 14800))	
sock.listen(10)

conn, addr = sock.accept()

while True:
	data = conn.recv(1024)
	if not data:
		pass
	else:
		msg = data.decode("utf-8")
		print(addr[0] + ':' + str(addr[1]) + ' > ' + msg)
		conn.send(b"Hello from my Python Server!")

conn.close()
