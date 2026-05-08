"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.tictactoe_handler = None

    def set_tictactoe_handler(self, handler):
        self.tictactoe_handler = handler

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def submit_snake_score(self, score):
        try:
            score = int(score)
        except Exception:
            score = 0
        mysend(self.s, json.dumps({"action":"snake_score", "score":score}))
        response = json.loads(myrecv(self.s))
        if response.get("new_best"):
            self.out_msg += "Snake game over. New best score: " + str(score) + "\n"
        else:
            self.out_msg += "Snake game over. Score: " + str(score) + "\n"
        self.out_msg += response.get("results", "") + "\n"

    def show_leaderboard(self):
        mysend(self.s, json.dumps({"action":"leaderboard"}))
        response = json.loads(myrecv(self.s))
        self.out_msg += response.get("results", "") + "\n"

    def parse_connect_target(self, my_msg):
        peer = ""
        if my_msg.startswith("c "):
            peer = my_msg[2:].strip()
        elif my_msg.startswith("connect "):
            peer = my_msg[len("connect "):].strip()
        elif my_msg.startswith("c_") and my_msg.endswith("_"):
            peer = my_msg[2:-1].strip()
        return peer

    def generate_ai_picture(self, prompt):
        prompt = prompt.strip()
        if not prompt:
            self.out_msg += "Please enter a prompt after /aipic:\n"
            return
        mysend(self.s, json.dumps({"action":"aipic", "prompt":prompt}))
        response = json.loads(myrecv(self.s))
        if response.get("status") == "ok":
            self.out_msg += response.get("results", "") + "\n"
        else:
            self.out_msg += "AI image generation failed: " + response.get("results", "unknown error") + "\n"

    def emit_tictactoe_event(self, event):
        if self.tictactoe_handler is not None:
            self.tictactoe_handler(event)

    def join_tictactoe(self):
        mysend(self.s, json.dumps({"action":"ttt_join"}))
        self.emit_tictactoe_event(json.loads(myrecv(self.s)))

    def tictactoe_move(self, cell):
        try:
            cell = int(cell)
        except Exception:
            cell = -1
        mysend(self.s, json.dumps({"action":"ttt_move", "cell":cell}))
        self.emit_tictactoe_event(json.loads(myrecv(self.s)))

    def reset_tictactoe(self):
        mysend(self.s, json.dumps({"action":"ttt_reset"}))
        self.emit_tictactoe_event(json.loads(myrecv(self.s)))

    def leave_tictactoe(self):
        mysend(self.s, json.dumps({"action":"ttt_leave"}))
        self.emit_tictactoe_event(json.loads(myrecv(self.s)))

    def handle_tictactoe_command(self, my_msg):
        if my_msg == "__ttt_join__":
            self.join_tictactoe()
            return True
        if my_msg.startswith("__ttt_move__ "):
            self.tictactoe_move(my_msg[len("__ttt_move__ "):].strip())
            return True
        if my_msg == "__ttt_reset__":
            self.reset_tictactoe()
            return True
        if my_msg == "__ttt_leave__":
            self.leave_tictactoe()
            return True
        return False

    def handle_tictactoe_event(self, peer_msg):
        if peer_msg.get("action", "").startswith("ttt_"):
            self.emit_tictactoe_event(peer_msg)
            return True
        return False

    def handle_server_notice(self, peer_msg):
        if peer_msg.get("action") == "leaderboard_update":
            self.out_msg += "Snake leaderboard updated:\n"
            self.out_msg += peer_msg.get("results", "") + "\n"
            return True
        return False

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:
                if my_msg.startswith('@bot'):
                    # 发送给服务器（和聊天状态一样）
                    print("[DEBUG] Client sending @bot") 
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                    self.out_msg += '[' + self.me + '] ' + my_msg + '\n'
                    # 发送后不再执行后续命令判断，直接返回
                    return self.out_msg
                else:
                    if my_msg == 'q':
                        self.out_msg += 'See you next time!\n'
                        self.state = S_OFFLINE

                    elif my_msg == 'time':
                        mysend(self.s, json.dumps({"action":"time"}))
                        time_in = json.loads(myrecv(self.s))["results"]
                        self.out_msg += "Time is: " + time_in

                    elif my_msg == 'who':
                        mysend(self.s, json.dumps({"action":"list"}))
                        logged_in = json.loads(myrecv(self.s))["results"]
                        self.out_msg += 'Here are all the users in the system:\n'
                        self.out_msg += logged_in

                    elif my_msg == 'leaderboard':
                        self.show_leaderboard()

                    elif my_msg == '/summary':
                        mysend(self.s, json.dumps({"action":"summary"}))
                        response = json.loads(myrecv(self.s))
                        self.out_msg += response.get("results", "Summary failed.") + "\n"

                    elif my_msg == '/keywords':
                        mysend(self.s, json.dumps({"action":"keywords"}))
                        response = json.loads(myrecv(self.s))
                        self.out_msg += response.get("results", "Keywords extraction failed.") + "\n"

                    elif my_msg.startswith('/bot_personality '):
                        personality = my_msg[len('/bot_personality '):].strip()
                        mysend(self.s, json.dumps({"action":"bot_personality", "personality":personality}))
                        response = json.loads(myrecv(self.s))
                        self.out_msg += response.get("message", "") + "\n"

                    elif my_msg.startswith('__snake_score__ '):
                        self.submit_snake_score(my_msg[len('__snake_score__ '):].strip())

                    elif my_msg.startswith('/aipic:'):
                        self.generate_ai_picture(my_msg[len('/aipic:'):])

                    elif self.handle_tictactoe_command(my_msg):
                        pass

                    elif my_msg == 'ttt':
                        self.out_msg += "Use the TicTacToe button to open Tic-Tac-Toe Online.\n"

                    elif my_msg.startswith("c ") or my_msg.startswith("connect ") or my_msg.startswith("c_"):
                        peer = self.parse_connect_target(my_msg)
                        if peer:
                            if self.connect_to(peer) == True:
                                self.state = S_CHATTING
                                self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                                self.out_msg += '-----------------------------------\n'
                            else:
                                self.out_msg += 'Connection unsuccessful\n'
                        else:
                            self.out_msg += 'Please specify a peer name after c or connect.\n'

                    elif my_msg.startswith('?'):
                        term = my_msg[1:].strip()
                        mysend(self.s, json.dumps({"action":"search", "target":term}))
                        search_rslt = json.loads(myrecv(self.s))["results"].strip()
                        if (len(search_rslt)) > 0:
                            self.out_msg += search_rslt + '\n\n'
                        else:
                            self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                    elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                        poem_idx = my_msg[1:].strip()
                        mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                        poem = json.loads(myrecv(self.s))["results"]
                        # print(poem)
                        if (len(poem) > 0):
                            self.out_msg += poem + '\n\n'
                        else:
                            self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                    else:
                        self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                    
                if self.handle_tictactoe_event(peer_msg):
                    pass
                elif self.handle_server_notice(peer_msg):
                    pass
                
                elif peer_msg.get("action") == "exchange":
                    msg_text = peer_msg.get("message", "")
                    print(f"[DEBUG] Client received exchange: {msg_text[:50]}")
                    self.out_msg += msg_text + "\n"
                elif peer_msg["action"] == "connect":
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING

    #==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                if my_msg.startswith('@bot'):
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                    self.out_msg += "[" + self.me + "] " + my_msg + "\n"
                    return self.out_msg

                if my_msg == 'leaderboard':
                    self.show_leaderboard()
                    return self.out_msg

                if my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in + "\n"
                    return self.out_msg

                if my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in + "\n"
                    return self.out_msg
                
                if my_msg == '/summary':
                    mysend(self.s, json.dumps({"action":"summary"}))
                    response = json.loads(myrecv(self.s))
                    self.out_msg += response.get("results", "Summary failed.") + "\n"
                    return self.out_msg

                if my_msg == '/keywords':
                    mysend(self.s, json.dumps({"action":"keywords"}))
                    response = json.loads(myrecv(self.s))
                    self.out_msg += response.get("results", "Keywords extraction failed.") + "\n"
                    return self.out_msg

                elif my_msg.startswith('/bot_personality '):
                    personality = my_msg[len('/bot_personality '):].strip()
                    mysend(self.s, json.dumps({"action":"bot_personality", "personality":personality}))
                    response = json.loads(myrecv(self.s))
                    self.out_msg += response.get("message", "") + "\n"
                    return self.out_msg

                if my_msg.startswith('__snake_score__ '):
                    self.submit_snake_score(my_msg[len('__snake_score__ '):].strip())
                    return self.out_msg

                if my_msg.startswith('/aipic:'):
                    self.generate_ai_picture(my_msg[len('/aipic:'):])
                    return self.out_msg

                if self.handle_tictactoe_command(my_msg):
                    return self.out_msg

                # allow 'q' to leave chat as well (consistent with logged-in mode)
                if my_msg == 'q':
                    my_msg = 'bye'

                mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                # Echo my own message to UI immediately (server does not send it back to sender)
                self.out_msg += "[" + self.me + "] " + my_msg + "\n"
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)
                if self.handle_tictactoe_event(peer_msg):
                    pass
                elif self.handle_server_notice(peer_msg):
                    pass
                elif peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " joined)\n"
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                else:
                    self.out_msg += peer_msg["message"] + "\n"


            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
