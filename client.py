import socket
import cv2
import numpy
import hashlib
import sys 
import trace
import threading
import tkinter as tk
import inspect
import ctypes
from tkinter import messagebox
import tkinter.font as tkFont
import time
import queue

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

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def reciver():
    global q
    global mutex
    while 1:
        mutex.acquire()
        if(q.full()):
            mutex.release()
            continue
        else:
            mutex.release()
            length = recvall(sock,16)
            stringData = recvall(sock, int(length))
            mutex.acquire()
            q.put(length)
            q.put(stringData)
            mutex.release()
    
def video_catch():
    cv2.namedWindow("CLIENT2",0)
    global sock
    global q
    global mutex

    recivert = thread_with_trace(target = reciver)
    recivert.start()

    while 1:
        mutex.acquire()
        if(q.empty()):
            mutex.release()
            continue
        else:
            length = q.get()
            stringData = q.get()
            mutex.release()
            data = numpy.fromstring(stringData, dtype='uint8')
            decimg=cv2.imdecode(data,cv2.IMREAD_COLOR)
        
            cv2.imshow('CLIENT2',decimg)
            cv2.waitKey(1)

    sock.close()
    recivert.kill()
    recivert.join()
    cv2.destroyAllWindows()

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

class basedesk():
    def __init__(self,master):
        self.root = master
        self.root.config()
        self.root.title('Screen Streaming Client')
        self.root.geometry('640x480')
        self.root.resizable(False, False)   
        Connect(self.root)
                
class Connect():
    def __init__(self,master):
        self.master = master
        self.master.config()
        self.Connect = tk.Frame(self.master,)
        self.Connect.grid()
        self.label_ip = tk.Label(self.Connect, width=10, height=5, text = "Sever IP")
        self.ip = tk.Entry(self.Connect, width=15, show=None, font=('Arial', 14))
        self.label_ip.grid(row=0, column=1, padx=(160,5))
        self.ip.grid(row=0, column=2, padx=(5,160))
        self.btn = tk.Button(self.Connect, height=3, width=10, text="Connect", command=self.sock_connect)
        self.btn.grid(row=1, column=2, padx=(5,160))
    
    def delete(self,):       
        self.Connect.destroy()
        Auth(self.master)

    def reset_Text(self):
        self.ip.delete(0,"end")
    
    def sock_connect(self):
        TCP_IP = self.ip.get()
        if TCP_IP=="":
            MessageWindow("Inform", "Please type!")
            self.reset_Text()
        else:
            TCP_PORT = 8002
            global sock
            sock = socket.socket()
            sock.settimeout(1)
            try:
                sock.connect((TCP_IP, TCP_PORT))
                self.delete()
            except socket.timeout:
                MessageWindow("Inform", "Connect Fail")
                self.reset_Text()           

class Auth():
    def __init__(self,master):
        self.master = master
        self.master.config()
        self.Auth = tk.Frame(self.master,)
        self.Auth.grid()
        self.label_account = tk.Label(self.Auth, width=10, height=5, text = "Account")
        self.label_password = tk.Label(self.Auth, width=10, height=5, text = "Password")
        self.account = tk.Entry(self.Auth, width=15, show=None, font=('Arial', 14))  
        self.password = tk.Entry(self.Auth, width=15, show='*', font=('Arial', 14))
        self.label_account.grid(row=0,  column=1, padx=(160,5))
        self.account.grid(row=0,  column=2, padx=(5,160))
        self.label_password.grid(row=1, column=1, padx=(160,5))
        self.password.grid(row=1, column=2, padx=(5,160))
        self.btn = tk.Button(self.Auth, height=3, width=10, text="Login", command=self.auth)
        self.btn.grid(row=2, column=2, padx=(5,160))
        self.login_time=0
    
    def delete(self):
        self.Auth.destroy()
        Video_Player(self.master)
    
    def disconnect(self):
        global sock
        sock.close()
        sock = None
        self.Auth.destroy()
        Connect(self.master)
        MessageWindow("Inform", "Please reconnect!")
    
    def reset_Text(self):
        self.account.delete(0,"end")
        self.password.delete(0,"end")
    
    def auth(self):
        global sock
        user_name = self.account.get()
        pwd = self.password.get()
        pwd_h = hashlib.sha1()
        pwd_h.update(pwd.encode())
        sock.send( user_name.encode() )
        sock.send( pwd_h.hexdigest().encode() )
        p = sock.recv(6)
        if(p == b'AuthOK'):
            self.delete()
        else:
            self.login_time+=1
            if(self.login_time>=5):
                self.disconnect()
            else:
                MessageWindow("Inform", "Wrong!")
                self.reset_Text()

class Video_Player():
    def __init__(self,master):
        self.master = master
        self.master.config()
        self.Video_Player = tk.Frame(self.master,)
        self.Video_Player.grid()
        self.btn = tk.Button(self.Video_Player, height=3, width=10, text="disconnect", command=self.destroy)
        self.btn.grid(row=0, column=0,padx=(275), pady=(200))
        self.video_capture = thread_with_trace(target = video_catch)
        #self.video_capture.setDaemon(True) //I put this in thread_with_trace class inits
        self.video_capture.start()

    def disconnect(self):
        global sock
        sock.close()
        sock = None
        self.Video_Player.destroy()
        Connect(self.master)
        MessageWindow("Inform", "Please reconnect!")

    def destroy(self):
        self.video_capture.kill()
        self.video_capture.join()
        self.disconnect()

        
def exit_function():
    global sock
    if sock:
        sock.close() 
    exit()

sock = None
mutex = threading.Lock()
q = queue.Queue(maxsize=20)
root = tk.Tk()
basedesk(root)
root.protocol('WM_DELETE_WINDOW', exit_function)
root.mainloop()