import socket
from socketserver import BaseRequestHandler,ThreadingTCPServer
import cv2
import numpy
import json
import hashlib
from PIL import ImageGrab
import os
import threading
import tkinter as tk
import inspect
import ctypes
from tkinter import messagebox
import tkinter.font as tkFont

class Handler(BaseRequestHandler):
    def handle(self):

        user_list = open('users.json')
        users = json.load(user_list)
        global client_count
        global desk
        
        while 1:
            try:
                user_name = self.request.recv(1024).decode()
                pwd = self.request.recv(1024).decode()
                if(users[user_name]== pwd):
                    user_list.close()
                    break
            except:
                break
        
        client_count += 1
        desk.status.update_client()

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
                client_count -= 1
                desk.status.update_client()
                #self.request.close()
                break

class basedesk():
    def __init__(self,master):
        self.root = master
        self.root.config()
        self.root.title('Base page')
        self.root.geometry('640x480')
        self.root.resizable(False, False)
        menubar = tk.Menu(self.root)
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=menu)
        menu.add_command(label='Status', command=self.change_to_status)
        menu.add_command(label='Users', command=self.change_to_user)
        self.root.config(menu=menubar)
        self.user = None
        self.status = Status(self.root)    

    def change_to_user(self,):
        if self.status!=None:
            self.status.delete()
        if self.user!=None:
            self.user.delete()
        self.user = Users(self.root)
    
    def change_to_status(self,):
        if self.status!=None:
            self.status.delete()
        if self.user!=None:
            self.user.delete()
        self.status = Status(self.root)  
                
class Status():
    def __init__(self,master):
        self.master = master
        self.master.config()
        self.Status = tk.Frame(self.master,)
        self.Status.grid()
        self.fontStyle = tkFont.Font(family="Lucida Grande", size=20)
        global client_count
        self.client_num = "Clients: "+ str(client_count)
        self.label_client = tk.Label(self.Status, width=15, height=5, text = self.client_num, font=self.fontStyle)
        self.label_client.grid(row=0, padx=200)
        
    def delete(self,):       
        self.Status.destroy()

    def update_client(self):
        global client_count
        self.client_num = "Clients: "+ str(client_count)
        self.label_client.configure(text=self.client_num)
              

class Users():
    def __init__(self,master):
        self.master = master
        self.master.config()
        self.Users = tk.Frame(self.master,)
        self.Users.grid()
        self.label_account = tk.Label(self.Users, width=10, height=5, text = "Account")
        self.label_password = tk.Label(self.Users, width=10, height=5, text = "Password")
        self.account = tk.Entry(self.Users, width=15, show=None, font=('Arial', 14))  
        self.password = tk.Entry(self.Users, width=15, show='*', font=('Arial', 14))
        self.label_account.grid(row=0,  column=1, padx=(160,5))
        self.account.grid(row=0,  column=2, padx=(5,160))
        self.label_password.grid(row=1, column=1, padx=(160,5))
        self.password.grid(row=1, column=2, padx=(5,160))
        self.btn = tk.Button(self.Users, height=3, width=10, text="Create", command=self.create_user)
        self.btn.grid(row=2, column=2, padx=(5,160))
    
    def delete(self):
        self.Users.destroy()
    
    class MessageWindow(tk.Toplevel):
        def __init__(self, title, message):
            super().__init__()
            self.details_expanded = False
            self.title(title)
            self.geometry("160x80+{}+{}".format(self.master.winfo_x()+240, self.master.winfo_y()+160))
            self.resizable(False, False)
            self.rowconfigure(0, weight=0)
            self.rowconfigure(1, weight=1)
            self.columnconfigure(0, weight=1)
            self.columnconfigure(1, weight=1)
            tk.Label(self, text=message, width=30, height=3).grid(row=0, padx=30)
            tk.Button(self, text="OK",width=5, height=1, command=self.destroy).grid(row=1, padx=30)
    
    def reset_Text(self):
        self.account.delete(0,"end")
        self.password.delete(0,"end")

    def create_user(self):
        try:
            with open('users.json') as data_file:    
                old_data = json.load(data_file)
        except:
            with open('users.json','w+').write("{ }") as data_file:
                old_data = json.load(data_file)
        name = self.account.get()
        pwd = self.password.get()
        if name=="" or pwd=="":
            self.reset_Text()
            self.MessageWindow("Error", "Please Fill Both!")
        else: 
            pwd_h = hashlib.sha1()
            pwd_h.update(pwd.encode())
            old_data[name]=pwd_h.hexdigest()
            with open('users.json', 'w+') as data_file:
                json.dump(old_data, data_file)
            self.reset_Text()
            self.MessageWindow("Create User", "Create User Finish!")


def serve():
    server = ThreadingTCPServer(ADDR,Handler)
    server.serve_forever()

def page():
    root = tk.Tk()
    global desk
    desk = basedesk(root)
    root.protocol('WM_DELETE_WINDOW', exit_function)
    root.mainloop()

def exit_function(): 
    exit() # exit gui thread and main will end

TCP_IP = "localhost"
TCP_PORT = 8002
client_count = 0
desk = None
ADDR=(TCP_IP,TCP_PORT)
service = threading.Thread(target = serve)
service.setDaemon(True)#if main end(gui terminate), this thread will terminate, too.
service.start()
gui = threading.Thread(target = page)
gui.start()






