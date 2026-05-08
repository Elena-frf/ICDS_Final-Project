"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""
MAX_HISTORY = 100   

import time
import socket
import select
import sys
import string
import os
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp
from ai_pic import generate_ai_image
from chat_bot_client import ChatBotClient

class Server:
    def __init__(self):
        self.new_clients = [] #list of new sockets of which the user id is not known
        self.logged_name2sock = {} #dictionary mapping username to socket
        self.logged_sock2name = {} # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        self.ttt_game = self._new_ttt_game()
        self.chatbot = ChatBotClient()
        self.recent_history = {}   # { username: [(timestamp, message), ...] }

        # storage locations (keep generated files out of the project root)
        self.base_dir = os.path.dirname(__file__)
        self.data_dir = os.path.join(self.base_dir, "data")
        self.indices_dir = os.path.join(self.data_dir, "indices")
        self.aipic_dir = os.path.join(self.data_dir, "aipic")
        self.creds_path = os.path.join(self.data_dir, "users.json")
        self.leaderboard_path = os.path.join(self.data_dir, "leaderboard.json")
        os.makedirs(self.indices_dir, exist_ok=True)
        self.credentials = self._load_credentials()
        self.leaderboard = self._load_leaderboard()
        self.user_bots = {}

        #start server
        self.server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        #initialize past chat indices
        self.indices={}
        # sonnet
        # self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        # self.sonnet = pkl.load(self.sonnet_f)
        # self.sonnet_f.close()
        self.sonnet = indexer.PIndex("AllSonnets.txt")

    def _record_history(self, username, message):
        if not username or message is None:
            return
        hist = self.recent_history.setdefault(username, [])
        hist.append((time.time(), message))
        if len(hist) > MAX_HISTORY:
            self.recent_history[username] = hist[-MAX_HISTORY:]

    def _new_ttt_game(self, players=None):
        if players is None:
            players = []
        players = players[:2]
        symbols = {}
        for index, name in enumerate(players):
            symbols[name] = "X" if index == 0 else "O"
        return {
            "players": players,
            "symbols": symbols,
            "board": [""] * 9,
            "turn": "X",
            "winner": ""
        }

    def _load_credentials(self):
        try:
            with open(self.creds_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except Exception:
            return {}

    def _save_credentials(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.creds_path, "w", encoding="utf-8") as f:
            json.dump(self.credentials, f, ensure_ascii=False, indent=2)

    def _load_leaderboard(self):
        try:
            with open(self.leaderboard_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except Exception:
            return {}

    def _save_leaderboard(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.leaderboard_path, "w", encoding="utf-8") as f:
            json.dump(self.leaderboard, f, ensure_ascii=False, indent=2)

    def _leaderboard_rows(self):
        rows = []
        for name, entry in self.leaderboard.items():
            if isinstance(entry, dict):
                score = entry.get("score", 0)
                updated = entry.get("updated", "")
            else:
                score = entry
                updated = ""
            try:
                score = int(score)
            except Exception:
                score = 0
            rows.append((name, score, updated))
        rows.sort(key=lambda row: (-row[1], row[0].lower()))
        return rows

    def _format_leaderboard(self, limit=10):
        rows = self._leaderboard_rows()[:limit]
        if len(rows) == 0:
            return "Snake leaderboard is empty."

        lines = ["Snake Leaderboard:"]
        for rank, row in enumerate(rows, 1):
            name, score, updated = row
            line = str(rank) + ". " + name + " - " + str(score)
            if updated:
                line += " (" + updated + ")"
            lines.append(line)
        return "\n".join(lines)

    def _record_snake_score(self, name, score):
        try:
            score = int(score)
        except Exception:
            score = 0
        score = max(0, score)

        old_entry = self.leaderboard.get(name, {})
        old_score = old_entry.get("score", -1) if isinstance(old_entry, dict) else old_entry
        try:
            old_score = int(old_score)
        except Exception:
            old_score = -1

        is_new_best = score > old_score
        if is_new_best:
            self.leaderboard[name] = {
                "score": score,
                "updated": time.strftime('%d.%m.%y,%H:%M', time.localtime())
            }
            self._save_leaderboard()
        return is_new_best

    def _broadcast_leaderboard(self, exclude_sock=None):
        msg = json.dumps({
            "action":"leaderboard_update",
            "results":self._format_leaderboard()
        })
        for sock in list(self.logged_sock2name.keys()):
            if sock != exclude_sock:
                mysend(sock, msg)

    def _idx_path(self, name):
        # keep original naming for simplicity; folder separation avoids clutter
        return os.path.join(self.indices_dir, name + ".idx")

    def _handle_aipic(self, from_sock, prompt):
        from_name = self.logged_sock2name[from_sock]
        try:
            image_path = generate_ai_image(prompt, self.aipic_dir)
            result = "AI image saved: " + image_path
            chat_notice = from_name + " generated an AI image: " + image_path

            # Share the generated file path with current chat peers as a chat event.
            for g in self.group.list_me(from_name)[1:]:
                to_sock = self.logged_name2sock[g]
                mysend(to_sock, json.dumps({
                    "action":"exchange",
                    "from":"[AI Pic]",
                    "message":chat_notice
                }))

            mysend(from_sock, json.dumps({
                "action":"aipic",
                "status":"ok",
                "results":result,
                "path":image_path
            }))
        except Exception as e:
            mysend(from_sock, json.dumps({
                "action":"aipic",
                "status":"error",
                "results":str(e)
            }))

    def _ttt_public_state(self, message=""):
        return {
            "action": "ttt_state",
            "players": self.ttt_game["players"],
            "symbols": self.ttt_game["symbols"],
            "board": self.ttt_game["board"],
            "turn": self.ttt_game["turn"],
            "winner": self.ttt_game["winner"],
            "message": message
        }

    def _ttt_state_for(self, name, message=""):
        state = self._ttt_public_state(message)
        state["symbol"] = self.ttt_game["symbols"].get(name, "")
        return state

    def _ttt_prune_players(self):
        live_players = [
            name for name in self.ttt_game["players"]
            if name in self.logged_name2sock
        ]
        if live_players != self.ttt_game["players"]:
            self.ttt_game = self._new_ttt_game(live_players)

    def _ttt_notify_players(self, exclude_name=None, message=""):
        self._ttt_prune_players()
        for name in self.ttt_game["players"]:
            if name == exclude_name:
                continue
            sock = self.logged_name2sock.get(name)
            if sock is not None:
                mysend(sock, json.dumps(self._ttt_state_for(name, message)))

    def _ttt_winner(self):
        board = self.ttt_game["board"]
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in wins:
            if board[a] and board[a] == board[b] and board[a] == board[c]:
                return board[a]
        if "" not in board:
            return "draw"
        return ""

    def _ttt_reset_round(self):
        self.ttt_game["board"] = [""] * 9
        self.ttt_game["turn"] = "X"
        self.ttt_game["winner"] = ""

    def _ttt_join(self, name):
        self._ttt_prune_players()
        if name not in self.ttt_game["players"]:
            if len(self.ttt_game["players"]) >= 2:
                state = self._ttt_state_for(name, "Game is full.")
                state["status"] = "full"
                return state
            self.ttt_game["players"].append(name)
            self.ttt_game["symbols"][name] = "X" if len(self.ttt_game["players"]) == 1 else "O"
            self._ttt_reset_round()
            self._ttt_notify_players(exclude_name=name, message=name + " joined Tic-Tac-Toe Online.")
        return self._ttt_state_for(name)

    def _ttt_leave(self, name):
        if name in self.ttt_game["players"]:
            remaining = [player for player in self.ttt_game["players"] if player != name]
            self.ttt_game = self._new_ttt_game(remaining)
            self._ttt_notify_players(exclude_name=name, message=name + " left Tic-Tac-Toe Online.")
        return self._ttt_state_for(name, "You left Tic-Tac-Toe Online.")

    def _ttt_move(self, name, cell):
        self._ttt_prune_players()
        if name not in self.ttt_game["players"]:
            state = self._ttt_state_for(name, "Join the game first.")
            state["status"] = "error"
            return state
        if len(self.ttt_game["players"]) < 2:
            state = self._ttt_state_for(name, "Waiting for a second player.")
            state["status"] = "error"
            return state
        if self.ttt_game["winner"]:
            state = self._ttt_state_for(name, "Round is over. Start a new round.")
            state["status"] = "error"
            return state

        symbol = self.ttt_game["symbols"].get(name)
        if symbol != self.ttt_game["turn"]:
            state = self._ttt_state_for(name, "It is not your turn.")
            state["status"] = "error"
            return state
        if cell < 0 or cell >= 9 or self.ttt_game["board"][cell] != "":
            state = self._ttt_state_for(name, "That move is not legal.")
            state["status"] = "error"
            return state

        self.ttt_game["board"][cell] = symbol
        self.ttt_game["winner"] = self._ttt_winner()
        if not self.ttt_game["winner"]:
            self.ttt_game["turn"] = "O" if self.ttt_game["turn"] == "X" else "X"

        message = name + " played " + symbol + "."
        if self.ttt_game["winner"] == "draw":
            message = "Tic-Tac-Toe ended in a draw."
        elif self.ttt_game["winner"]:
            message = name + " won Tic-Tac-Toe Online."
        self._ttt_notify_players(exclude_name=name, message=message)
        return self._ttt_state_for(name, message)

    def new_client(self, sock):
        #add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        #read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            print("login:", msg)
            if len(msg) > 0:

                if msg["action"] == "login":
                    name = msg["name"]
                    password = msg.get("password", "")
                    
                    # register on first login; otherwise require matching password
                    if name in self.credentials:
                        if self.credentials.get(name) != password:
                            mysend(sock, json.dumps({"action":"login", "status":"wrong-password"}))
                            return
                    else:
                        self.credentials[name] = password
                        self._save_credentials()

                    if self.group.is_member(name) != True:
                        #move socket from new clients list to logged clients
                        self.new_clients.remove(sock)
                        #add into the name to sock mapping
                        self.logged_name2sock[name] = sock
                        self.user_bots[name] = ChatBotClient(name=name)
                        print(f"[DEBUG] Created bot for {name}")
                        self.logged_sock2name[sock] = name
                        #load chat history of that user
                        if name not in self.indices.keys():
                            try:
                                self.indices[name]=pkl.load(open(self._idx_path(name),'rb'))
                            except IOError: #chat index does not exist, then create one
                                # backward compatibility: try old location once
                                try:
                                    self.indices[name]=pkl.load(open(name+'.idx','rb'))
                                except IOError:
                                    self.indices[name] = indexer.Index(name)
                        print(name + ' logged in')
                        self.group.join(name)
                        mysend(sock, json.dumps({"action":"login", "status":"ok"}))
                    else: #a client under this name has already logged in
                        mysend(sock, json.dumps({"action":"login", "status":"duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print ('wrong code received')
            else: #client died unexpectedly
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)

    def logout(self, sock):
        #remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(self._idx_path(name),'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        self._ttt_leave(name)
        if name in self.user_bots:
            del self.user_bots[name]
        sock.close()

#==============================================================================
# main command switchboard
#==============================================================================
    def handle_msg(self, from_sock):
        #read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
#==============================================================================
# handle connect request
#==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action":"connect", "status":"self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps({"action":"connect", "status":"success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps({"action":"connect", "status":"request", "from":from_name}))
                else:
                    msg = json.dumps({"action":"connect", "status":"no-user"})
                mysend(from_sock, msg)
#==============================================================================
# handle messeage exchange: one peer for now. will need multicast later
#==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                said2 = text_proc(msg["message"], from_name)
                self.indices[from_name].add_msg_and_index(said2)
                self._record_history(from_name, said2)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(said2)
                    self._record_history(g, said2)
                    mysend(to_sock, json.dumps({"action":"exchange", "message": said2}))

                # 处理 @bot 命令（广播给群组所有成员）
                if "@bot" in msg["message"].lower():
                    print(f"[DEBUG] @bot detected from {from_name}")
                    user_message = msg["message"].lower().replace("@bot", "").strip()
                    print(f"[DEBUG] user_message: '{user_message}'")
                    if user_message:
                        bot = self.user_bots.get(from_name)
                        print(f"[DEBUG] bot instance: {bot}")
                        if bot:
                            try:
                                prior = self.recent_history.get(from_name, [])
                                if prior:
                                    prior_text = "\n".join([text for (_, text) in prior[-20:]])
                                    user_message = f"Previous conversation:\n{prior_text}\n\nCurrent request:\n{user_message}"
                                print("[DEBUG] Calling bot.chat()...")
                                reply = bot.chat(user_message)
                                print(f"[DEBUG] Got reply: {reply[:50]}...")
                                # 获取当前用户所在的群组成员（包括自己）
                                group_members = self.group.list_me(from_name)  # 返回 [from_name, peer1, peer2, ...]
                                # 遍历群组成员，每个人都发送机器人的回复
                                for member in group_members:
                                    member_sock = self.logged_name2sock.get(member)
                                    if member_sock:
                                        bot_text = f"(Bot) {reply}"
                                        self._record_history(member, bot_text)
                                        mysend(member_sock, json.dumps({"action":"exchange", "message": bot_text}))
                            except Exception as e:
                                print(f"[ERROR] bot.chat() failed: {e}")
                                import traceback
                                traceback.print_exc()
                                # 出错时只发给发送者本人错误信息
                                mysend(from_sock, json.dumps({"action":"exchange", "message": f"(Bot) Error: {e}"}))
                        else:
                            print("[WARN] No bot instance for user")
                            mysend(from_sock, json.dumps({"action":"exchange", "message": "(Bot) Sorry, I'm not ready yet."}))
                    else:
                        print("[DEBUG] Empty user_message after @bot")
#==============================================================================
#             retrieve a sonnet
#==============================================================================
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', poem_indx)
                poem = self.sonnet.get_poem(poem_indx)
                poem = '\n'.join(poem).strip()
                print('here:\n', poem)
                mysend(from_sock, json.dumps({"action":"poem", "results":poem}))
#==============================================================================
#                 time
#==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps({"action":"time", "results":ctime}))

            elif msg["action"] in ("list", "who"):
                users = [name for name in self.group.members.keys()]
                if users:
                    result = "\n".join(users)
                else:
                    result = "No users online."
                mysend(from_sock, json.dumps({"action":"list", "results":result}))
#==============================================================================
#                 search
#==============================================================================
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print('search for ' + from_name + ' for ' + term)
                # search_rslt = (self.indices[from_name].search(term))
                search_rslt = '\n'.join([x[-1] for x in self.indices[from_name].search(term)])
                print('server side search: ' + search_rslt)
                mysend(from_sock, json.dumps({"action":"search", "results":search_rslt}))
#==============================================================================
#                 snake score and leaderboard
#==============================================================================
            elif msg["action"] == "snake_score":
                from_name = self.logged_sock2name[from_sock]
                score = msg.get("score", 0)
                is_new_best = self._record_snake_score(from_name, score)
                self._broadcast_leaderboard(exclude_sock=from_sock)
                mysend(from_sock, json.dumps({
                    "action":"snake_score",
                    "status":"ok",
                    "new_best":is_new_best,
                    "results":self._format_leaderboard()
                }))

            elif msg["action"] == "leaderboard":
                mysend(from_sock, json.dumps({
                    "action":"leaderboard",
                    "results":self._format_leaderboard()
                }))

            elif msg["action"] == "summary":
                from_name = self.logged_sock2name[from_sock]
                hist = self.recent_history.get(from_name, [])
                if not hist:
                    result = "No recent messages to summarize."
                else:
                    # 取最近20条消息的内容
                    recent_texts = [text for (ts, text) in hist[-20:]]
                    conversation = "\n".join(recent_texts)
                    prompt = f"Please summarize the following conversation in one short sentence:\n{conversation}"
                    try:
                        import llm_helper
                        summary = llm_helper.ask_llm(prompt)
                        result = f"Summary: {summary}"
                    except Exception as e:
                        result = f"Failed to summarize: {e}"
                mysend(from_sock, json.dumps({"action":"summary", "results":result}))

            elif msg["action"] == "keywords":
                from_name = self.logged_sock2name[from_sock]
                hist = self.recent_history.get(from_name, [])
                if not hist:
                    result = "No recent messages to extract keywords from."
                else:
                    recent_texts = [text for (ts, text) in hist[-20:]]
                    conversation = " ".join(recent_texts)
                    prompt = f"Extract up to 5 important keywords from the following conversation, separated by commas:\n{conversation}"
                    try:
                        import llm_helper
                        keywords = llm_helper.ask_llm(prompt)
                        result = f"Keywords: {keywords}"
                    except Exception as e:
                        result = f"Failed to extract keywords: {e}"
                mysend(from_sock, json.dumps({"action":"keywords", "results":result}))
#==============================================================================
#                 ai picture generation
#==============================================================================
            elif msg["action"] == "aipic":
                self._handle_aipic(from_sock, msg.get("prompt", ""))

            elif msg["action"] == "bot_personality":
                from_name = self.logged_sock2name[from_sock]
                personality = msg.get("personality", "").strip()
                bot = self.user_bots.get(from_name)
                if bot and personality:
                    bot.set_personality(personality)
                    mysend(from_sock, json.dumps({"action":"bot_personality", "status":"ok", "message":f"Personality set to: {personality}"}))
                else:
                    mysend(from_sock, json.dumps({"action":"bot_personality", "status":"error", "message":"Failed to set personality"}))
#==============================================================================
#                 tic-tac-toe online
#==============================================================================
            elif msg["action"] == "ttt_join":
                from_name = self.logged_sock2name[from_sock]
                mysend(from_sock, json.dumps(self._ttt_join(from_name)))

            elif msg["action"] == "ttt_move":
                from_name = self.logged_sock2name[from_sock]
                cell = msg.get("cell", -1)
                try:
                    cell = int(cell)
                except Exception:
                    cell = -1
                mysend(from_sock, json.dumps(self._ttt_move(from_name, cell)))

            elif msg["action"] == "ttt_reset":
                from_name = self.logged_sock2name[from_sock]
                if from_name in self.ttt_game["players"]:
                    self._ttt_reset_round()
                    self._ttt_notify_players(exclude_name=from_name, message=from_name + " started a new round.")
                    mysend(from_sock, json.dumps(self._ttt_state_for(from_name, "New round started.")))
                else:
                    state = self._ttt_state_for(from_name, "Join the game first.")
                    state["status"] = "error"
                    mysend(from_sock, json.dumps(state))

            elif msg["action"] == "ttt_leave":
                from_name = self.logged_sock2name[from_sock]
                mysend(from_sock, json.dumps(self._ttt_leave(from_name)))
#==============================================================================
# the "from" guy has had enough (talking to "to")!
#==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action":"disconnect"}))
#==============================================================================
#                 the "from" guy really, really has had enough
#==============================================================================

        else:
            #client died unexpectedly
            self.logout(from_sock)

#==============================================================================
# main loop, loops *forever*
#==============================================================================
    def run(self):
        print ('starting server...')
        while(1):
           read,write,error=select.select(self.all_sockets,[],[])
           print('checking logged clients..')
           for logc in list(self.logged_name2sock.values()):
               if logc in read:
                   self.handle_msg(logc)
           print('checking new clients..')
           for newc in self.new_clients[:]:
               if newc in read:
                   self.login(newc)
           print('checking for new connections..')
           if self.server in read :
               #new client request
               sock, address=self.server.accept()
               self.new_client(sock)

def main():
    server=Server()
    server.run()

main()
