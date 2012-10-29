import socket

csocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

csocket.connect(('localhost', 2727))
csocket.send ('record[/home/sio2/Desktop/123.wav]')
a=csocket.recv(4096)

sound = a[a.find("[")+1:a.find("]")]
frec = a[a.find("(")+1:a.find(")")]

print(sound)
print(frec)

csocket.send("showplots")

csocket.close()



