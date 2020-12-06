import socket
from socketserver import BaseRequestHandler,ThreadingTCPServer
import cv2
import numpy
import json
import hashlib
from PIL import ImageGrab
import os
import threading

def create_user():
        with open('users.json') as data_file:    
            old_data = json.load(data_file)
        name = input("name")
        pwd = input("password")
        pwd_h = hashlib.sha1()
        pwd_h.update(pwd.encode())
        old_data[name]=pwd_h.hexdigest()
        with open('users.json', 'w') as data_file:
            json.dump(old_data, data_file)
        print("finish")

class Handler(BaseRequestHandler):
    def handle(self):

        user_list = open('users.json')
        users = json.load(user_list)
        
        while 1:
            try:
                user_name = self.request.recv(1024).decode()
                pwd = self.request.recv(1024).decode()
                if(users[user_name]== pwd):
                    user_list.close()
                    break
            except:
                break

        while 1:
            image = ImageGrab.grab()
            image = cv2.cvtColor(numpy.asarray(image),cv2.COLOR_RGB2BGR)
            result, imgencode = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY),100])
            data = numpy.array(imgencode)
            stringData = data.tostring()
            try:
                self.request.send( str(len(stringData)).ljust(16).encode())
                self.request.send( stringData )
            except:
                #self.request.close()
                break

TCP_IP = "localhost"
TCP_PORT = 8002
ADDR=(TCP_IP,TCP_PORT)
#create user section
m = input("mode: 1 2\n")
if(m == '2'):
    print("12")
    create_user()
    exit()
else:
    server = ThreadingTCPServer(ADDR,Handler)
    server.serve_forever()
