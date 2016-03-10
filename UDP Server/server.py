import socket
import time

print("Server running...")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 14800))

last_time = 0

while True:
	data = sock.recvfrom(1024)
	current_time = time.time()
	ping = current_time - last_time
	last_time = current_time
	
	print("Ping: " + str(ping))
	
	msg = data[0].decode("utf-8")
	addr = data[1]
	
	if not msg:
		pass
	else:
		if msg == "nop":
			continue
		print("[" + addr[0] + ":" + str(addr[1]) + "] > " + msg)
		sock.sendto(b"Hello from UDP Python Server!", addr)

sock.close()
