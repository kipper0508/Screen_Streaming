import socket
import cv2
import numpy
import hashlib

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

ip = input('IP:')
TCP_IP = ip
TCP_PORT = 8002

sock = socket.socket()
sock.connect((TCP_IP, TCP_PORT))

user_name = input('USER:')
sock.send( user_name.encode() );
pwd = input('PASSWORD:')
pwd_h = hashlib.sha1()
pwd_h.update(pwd.encode())
sock.send( pwd_h.hexdigest().encode() );

cv2.namedWindow("CLIENT2",0)

while 1:
    length = recvall(sock,16)
    stringData = recvall(sock, int(length))
    data = numpy.fromstring(stringData, dtype='uint8')
    decimg=cv2.imdecode(data,cv2.IMREAD_COLOR)
    
    cv2.imshow('CLIENT2',decimg)
    cv2.waitKey(1)

sock.close()
cv2.destroyAllWindows()
