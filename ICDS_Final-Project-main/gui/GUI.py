#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 13:36:58 2021

@author: bing
"""

# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import simpledialog
from chat_utils import *
from snake_game import launch_snake
from tictactoe_game import TicTacToeGame
import json

# GUI class for the chat
class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        self.process = None
        self.tictactoe_game = None
        self.sm.set_tictactoe_handler(self.handleTicTacToeEvent)
        self.emoji_dict = {
            "e_happy": "😀",
            "e_sad": "😢",
            "e_love": "😍",
            "e_cool": "😎",
            "e_cry": "😢",
            "e_angry": "😡",
            "e_thumbup": "👍",
            "e_thumbdown": "👎",
            "e_heart": "❤️",
            "e_fire": "🔥"
        }

    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Login")
        self.login.resizable(width = False, 
                             height = False)
        self.login.configure(width = 400,
                             height = 300)
        # create a Label
        self.pls = Label(self.login, 
                       text = "Please login to continue",
                       justify = CENTER, 
                       font = "Helvetica 14 bold")
          
        self.pls.place(relheight = 0.15,
                       relx = 0.2, 
                       rely = 0.07)
        # create a Label
        self.labelName = Label(self.login,
                               text = "Name: ",
                               font = "Helvetica 12")
          
        self.labelName.place(relheight = 0.2,
                             relx = 0.1, 
                             rely = 0.2)
          
        # create a entry box for 
        # tyoing the message
        self.entryName = Entry(self.login, 
                             font = "Helvetica 14")
          
        self.entryName.place(relwidth = 0.4, 
                             relheight = 0.12,
                             relx = 0.35,
                             rely = 0.2)

        self.labelPass = Label(self.login,
                               text = "Password: ",
                               font = "Helvetica 12")
        self.labelPass.place(relheight = 0.2,
                             relx = 0.1,
                             rely = 0.35)

        self.entryPass = Entry(self.login,
                               font = "Helvetica 14",
                               show = "*")
        self.entryPass.place(relwidth = 0.4,
                             relheight = 0.12,
                             relx = 0.35,
                             rely = 0.35)

        self.loginMsg = Label(self.login,
                              text = "",
                              fg = "#B03A2E",
                              justify = CENTER,
                              font = "Helvetica 10")
        self.loginMsg.place(relheight = 0.12,
                            relx = 0.1,
                            rely = 0.48,
                            relwidth = 0.8)
          
        # set the focus of the curser
        self.entryName.focus()
          
        # create a Continue Button 
        # along with action
        self.go = Button(self.login,
                         text = "CONTINUE", 
                         font = "Helvetica 14 bold", 
                         command = lambda: self.goAhead(self.entryName.get(), self.entryPass.get()))
          
        self.go.place(relx = 0.4,
                      rely = 0.62)
        self.Window.mainloop()
  
    def goAhead(self, name, password):
        if len(name) > 0:
            msg = json.dumps({"action":"login", "name": name, "password": password})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.textCons.config(state = NORMAL)
                # self.textCons.insert(END, "hello" +"\n\n")   
                self.textCons.insert(END, menu +"\n\n")      
                self.textCons.config(state = DISABLED)
                self.textCons.see(END)
                # while True:
                #     self.proc()
                # the thread to receive messages
                self.process = threading.Thread(target=self.proc)
                # Avoid daemon thread crash at interpreter shutdown; we stop it on window close.
                self.process.daemon = False
                self.process.start()
            else:
                status = response.get("status", "")
                if status == "duplicate":
                    self.loginMsg.config(text="This user is already logged in.")
                elif status == "wrong-password":
                    self.loginMsg.config(text="Wrong password for this user.")
                else:
                    self.loginMsg.config(text="Login failed. Please try again.")
  
    # The main layout of the chat
    def layout(self,name):
        
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.Window.resizable(width = False,
                              height = False)
        self.Window.geometry("560x740")
        self.Window.configure(width = 560,
                              height = 740,
                              bg = "#17202A")
        self.labelHead = Label(self.Window,
                             bg = "#17202A", 
                              fg = "#EAECEE",
                              text = self.name ,
                               font = "Helvetica 13 bold",
                               pady = 5)
          
        self.labelHead.place(relwidth = 1)
        self.line = Label(self.Window,
                          width = 450,
                          bg = "#ABB2B9")
          
        self.line.place(relwidth = 1,
                        rely = 0.07,
                        relheight = 0.012)
          
        self.textCons = Text(self.Window,
                             width = 20,
                             height = 2,
                             bg = "#17202A",
                             fg = "#EAECEE",
                             font = "Helvetica 14",
                             padx = 5,
                             pady = 5)

        self.textCons.place(relheight = 0.64,
                            relwidth = 1,
                            rely = 0.125)

        self.buttonFrame = Frame(self.Window, bg="#17202A")
        self.buttonFrame.place(relwidth=1, rely=0.775, relheight=0.095)
        
        self.btnTime = Button(self.buttonFrame, text="Time", command=self.sendTime, bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnTime.grid(row=0, column=0, padx=5, pady=4, sticky="ew")
        
        self.btnWho = Button(self.buttonFrame, text="Who", command=self.sendWho, bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnWho.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        
        self.btnPoem = Button(self.buttonFrame, text="Poem", command=self.sendPoem, bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnPoem.grid(row=0, column=2, padx=5, pady=4, sticky="ew")
        
        self.btnSearch = Button(self.buttonFrame, text="Search", command=self.sendSearch, bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnSearch.grid(row=0, column=3, padx=5, pady=4, sticky="ew")

        self.btnSnake = Button(self.buttonFrame, text="Snake", command=self.openSnake, bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnSnake.grid(row=1, column=0, padx=5, pady=4, sticky="ew")

        self.btnLeaderboard = Button(self.buttonFrame, text="Scores", command=self.sendLeaderboard, bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnLeaderboard.grid(row=1, column=1, padx=5, pady=4, sticky="ew")

        self.btnTicTacToe = Button(self.buttonFrame, text="Tic-Tac-Toe", command=self.openTicTacToe, bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnTicTacToe.grid(row=1, column=2, padx=5, pady=4, sticky="ew")
        
        self.btnLeave = Button(self.buttonFrame, text="Leave Chat", command=lambda : self.sendButton("bye"), bg="#ABB2B9", fg="#17202A", font="Helvetica 10 bold")
        self.btnLeave.grid(row=1, column=3, padx=5, pady=4, sticky="ew")

        for col in range(4):
            self.buttonFrame.grid_columnconfigure(col, weight=1, uniform="toolbar")
          
        self.labelBottom = Label(self.Window,
                                 bg = "#ABB2B9",
                                 height = 120)
          
        self.labelBottom.place(relwidth = 1,
                               rely = 0.882)
          
        self.entryMsg = Entry(self.labelBottom,
                              bg = "#2C3E50",
                              fg = "#EAECEE",
                              font = "Helvetica 13")
          
        # place the given widget
        # into the gui window
        self.entryMsg.place(relwidth = 0.76,
                            relheight = 0.03,
                            rely = 0.008,
                            relx = 0.011)
          
        self.entryMsg.focus()
          
        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text = "Send",
                                font = "Helvetica 10 bold", 
                                width = 20,
                                bg = "#ABB2B9",
                                command = lambda : self.sendButton(self.entryMsg.get()))
          
        self.buttonMsg.place(relx = 0.78,
                             rely = 0.008,
                             relheight = 0.03, 
                             relwidth = 0.21)

        self.textCons.config(cursor = "arrow")
          
        # create a scroll bar
        scrollbar = Scrollbar(self.textCons)
          
        # place the scroll bar 
        # into the gui window
        scrollbar.place(relheight = 1,
                        relx = 0.974)
          
        scrollbar.config(command = self.textCons.yview)
          
        self.textCons.config(state = DISABLED)

    def on_close(self):
        try:
            self.sm.set_state(S_OFFLINE)
        except Exception:
            pass
        try:
            self.Window.quit()
            self.Window.destroy()
        except Exception:
            pass
  
    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        msg = self.process_emojis(msg)
        self.textCons.config(state = DISABLED)
        self.my_msg = msg
        # print(msg)
        self.entryMsg.delete(0, END)

    def sendTime(self):
        self.sendButton("time")

    def sendWho(self):
        self.sendButton("who")

    def sendPoem(self):
        num = simpledialog.askstring("Poem", "Enter sonnet number:")
        if num:
            self.sendButton("p " + num)

    def sendSearch(self):
        term = simpledialog.askstring("Search", "Enter search term:")
        if term:
            self.sendButton("? " + term)

    def openSnake(self):
        launch_snake(self.Window, on_game_over=self.reportSnakeScore)

    def sendLeaderboard(self):
        self.sendButton("leaderboard")

    def reportSnakeScore(self, score):
        self.sendButton("__snake_score__ " + str(score))

    def openTicTacToe(self):
        if self.tictactoe_game is not None and not self.tictactoe_game.closed:
            self.tictactoe_game.window.lift()
            return
        self.tictactoe_game = TicTacToeGame(self.Window, self.sendButton, self.name)

    def handleTicTacToeEvent(self, event):
        self.Window.after(0, lambda: self.applyTicTacToeEvent(event))

    def applyTicTacToeEvent(self, event):
        if self.tictactoe_game is None or self.tictactoe_game.closed:
            return
        self.tictactoe_game.apply_event(event)

    def process_emojis(self, msg):
        for key, emoji in self.emoji_dict.items():
            msg = msg.replace(key, emoji)
        return msg

    def proc(self):
        # print(self.msg)
        while True:
            # If the state machine has gone offline (e.g., user quit), stop the thread.
            try:
                if self.sm.get_state() == S_OFFLINE:
                    break

                read, write, error = select.select([self.socket], [], [], 0)
                peer_msg = []
                # print(self.msg)
                if self.socket in read:
                    peer_msg = self.recv()

                if len(self.my_msg) > 0 or len(peer_msg) > 0:
                    # print(self.system_msg)
                    self.system_msg += self.sm.proc(self.my_msg, peer_msg)
                    self.my_msg = ""
                    if self.system_msg:
                        self.textCons.config(state = NORMAL)
                        self.textCons.insert(END, self.system_msg + "\n\n")
                        self.textCons.config(state = DISABLED)
                        self.textCons.see(END)
                        self.system_msg = ""
            except Exception:
                # Socket/GUI teardown can race with this thread; exit quietly.
                break

    def run(self):
        self.login()
        # After the UI closes, wait briefly for receiver thread to exit cleanly.
        try:
            if self.process is not None and self.process.is_alive():
                self.process.join(timeout=1.0)
        except Exception:
            pass
# create a GUI class object
if __name__ == "__main__": 
    g = GUI()
