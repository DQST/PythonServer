import socket

print("Server running...")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 14800))

while True:
	data = sock.recvfrom(1024)
	msg = data[0].decode("utf-8")
	addr = data[1]
	
	if not msg:
		pass
	else:
		print("[" + addr[0] + ":" + str(addr[1]) + "] > " + msg)
		sock.sendto(b"Hello from UDP Python Server!", addr)

sock.close()
