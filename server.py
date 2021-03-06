import socket
from socketserver import BaseRequestHandler,ThreadingTCPServer
import cv2
import numpy
import json
import hashlib
from PIL import Image
import os
import sys 
import trace
import threading
import tkinter as tk
import inspect
import ctypes
from tkinter import messagebox
import tkinter.font as tkFont
from goto import with_goto
import queue
import time
from mss import mss

class thread_with_trace(threading.Thread): 
    def __init__(self, *args, **keywords): 
        threading.Thread.__init__(self, *args, **keywords)
        threading.Thread.setDaemon(self,True)
        self.killed = False
  
    def start(self): 
        self.__run_backup = self.run 
        self.run = self.__run       
        threading.Thread.start(self) 
  
    def __run(self): 
        sys.settrace(self.globaltrace) 
        self.__run_backup() 
        self.run = self.__run_backup 
  
    def globaltrace(self, frame, event, arg): 
        if event == 'call': 
            return self.localtrace 
        else: 
            return None
  
    def localtrace(self, frame, event, arg): 
        if self.killed: 
            if event == 'line': 
                raise SystemExit() 
        return self.localtrace 
  
    def kill(self): 
        self.killed = True

class Handler(BaseRequestHandler):
    @with_goto
    def handle(self):

        user_list = open('users.json')
        users = json.load(user_list)
        global client_count
        global desk

        login_time=0
        while(login_time<5):
            try:
                user_name = self.request.recv(1024).decode()
                #print(user_name)
            except:
                goto .end
            pwd = self.request.recv(1024).decode()
            if(user_name in users):
                if(users[user_name] ==pwd):
                    user_list.close()
                    self.request.send(b'AuthOK')
                    goto .begin
                else:
                    login_time += 1
                    self.request.send(b'AuthNN')
                    continue
            else:
                login_time += 1
                self.request.send(b'AuthNN')
                continue

        goto .end

        label .begin

        client_count += 1
        desk.status.update_client()

        encodert = thread_with_trace(target = encoder)
        encodert.start()

        global mutex
        global q

        while 1:
            try:
                mutex.acquire()
                if(q.empty()):
                    #print("empty")
                    mutex.release()
                    continue
                else:
                    #print("send")
                    stringData = q.get()
                    mutex.release()
                    self.request.send( str(len(stringData)).ljust(16).encode())
                    self.request.send( stringData )
            except:
                client_count -= 1
                desk.status.update_client()
                #self.request.close()
                break
        
        label .end
        encodert.kill()
        encodert.join()

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
            with open('users.json','r') as data_file:    
                old_data = json.load(data_file)
        except:
            open('users.json','w+').write("{ }")
        
        with open('users.json','r') as data_file:
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

def capture_screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        return Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
    
def encoder():
    global mutex
    global q
    while 1:
        mutex.acquire()
        if(q.full()):
            mutex.release()
            continue
        else:
            mutex.release()
            image = capture_screenshot()
            image = cv2.cvtColor(numpy.asarray(image),cv2.COLOR_RGB2BGR)
            result, imgencode = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY),70])
            data = numpy.array(imgencode)
            stringData = data.tostring()

            mutex.acquire()
            q.put(stringData)
            mutex.release()

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
    sys.exit() # exit gui thread and main will end

TCP_IP = ''
TCP_PORT = 8002
client_count = 0
desk = None
mutex = threading.Lock()
q = queue.Queue(maxsize=10)
ADDR=(TCP_IP,TCP_PORT)
service = threading.Thread(target = serve)
service.setDaemon(True)#if main end(gui terminate), this thread will terminate, too.
service.start()
gui = threading.Thread(target = page)
gui.start()






