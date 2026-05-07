"""
Tkinter Tic-Tac-Toe window for the chat server multiplayer game.

Inspired by yumin-chen/tic-tac-toe-in-python, an MIT-licensed
socket-based Tkinter Tic-Tac-Toe project. This module uses this chat app's
existing socket protocol instead of the original project's standalone server.
See THIRD_PARTY_LICENSES.md.
"""

import tkinter as tk


class TicTacToeGame:
    def __init__(self, master, send_command, username):
        self.send_command = send_command
        self.username = username
        self.symbol = ""
        self.closed = False

        self.window = tk.Toplevel(master)
        self.window.title("Tic-Tac-Toe Online")
        self.window.geometry("500x590")
        self.window.resizable(False, False)
        self.window.configure(bg="#17202A")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.title = tk.Label(
            self.window,
            text="Tic-Tac-Toe Online",
            bg="#17202A",
            fg="#EAECEE",
            font=("Helvetica", 18, "bold"),
        )
        self.title.pack(pady=(14, 4))

        self.status = tk.Label(
            self.window,
            text="Joining online game...",
            bg="#17202A",
            fg="#D5DBDB",
            font=("Helvetica", 11, "bold"),
            wraplength=330,
        )
        self.status.pack(pady=(0, 12))

        self.board_frame = tk.Frame(self.window, bg="#17202A")
        self.board_frame.pack()

        self.cells = []
        for index in range(9):
            button = tk.Button(
                self.board_frame,
                text="",
                width=5,
                height=2,
                bg="#2C3E50",
                fg="#EAECEE",
                disabledforeground="#EAECEE",
                relief=tk.RAISED,
                activebackground="#34495E",
                activeforeground="#FFFFFF",
                font=("Helvetica", 40, "bold"),
                command=lambda i=index: self.make_move(i),
            )
            button.grid(row=index // 3, column=index % 3, padx=6, pady=6)
            self.cells.append(button)

        self.info = tk.Label(
            self.window,
            text="Two clients join the same server-managed game.",
            bg="#17202A",
            fg="#ABB2B9",
            font=("Helvetica", 10),
            wraplength=330,
        )
        self.info.pack(pady=(14, 8))

        self.reset_button = tk.Button(
            self.window,
            text="New Round",
            command=lambda: self.send_command("__ttt_reset__"),
            bg="#ABB2B9",
            fg="#17202A",
            font=("Helvetica", 10, "bold"),
        )
        self.reset_button.pack()

        self.window.after(100, lambda: self.send_command("__ttt_join__"))

    def make_move(self, index):
        self.status.config(text="Sending move to server...")
        self.send_command("__ttt_move__ " + str(index))

    def apply_event(self, event):
        if self.closed:
            return

        if "symbol" in event:
            self.symbol = event.get("symbol", "")

        board = event.get("board")
        if board is not None:
            for index, value in enumerate(board):
                self.paint_cell(index, value)

        if event.get("status") == "full":
            self.status.config(text="Game is full. Try again when a player leaves.")
            self.set_cells_enabled(False)
            return

        if event.get("status") == "error":
            self.status.config(text=event.get("message", "Move rejected."))
            self.set_cells_enabled(self.can_move(event))
            return

        message = event.get("message", "")
        if message:
            self.status.config(text=message)
        else:
            self.status.config(text=self.describe_state(event))

        self.set_cells_enabled(self.can_move(event))

    def describe_state(self, event):
        winner = event.get("winner", "")
        if winner == "draw":
            return "Draw. Start a new round."
        if winner:
            return winner + " won. Start a new round."

        players = event.get("players", [])
        if len(players) < 2:
            return "Waiting for a second player. You are " + self.symbol + "."

        turn = event.get("turn", "")
        if turn == self.symbol:
            return "Your turn. You are " + self.symbol + "."
        return "Opponent's turn. You are " + self.symbol + "."

    def can_move(self, event):
        if event.get("winner"):
            return False
        if event.get("turn") != self.symbol:
            return False
        if len(event.get("players", [])) < 2:
            return False
        return True

    def set_cells_enabled(self, enabled):
        for cell in self.cells:
            if cell["text"] != "":
                cell.config(state=tk.NORMAL, relief=tk.SUNKEN, cursor="")
            else:
                cell.config(
                    state=tk.NORMAL if enabled else tk.DISABLED,
                    bg="#2C3E50",
                    fg="#EAECEE",
                    disabledforeground="#EAECEE",
                    relief=tk.RAISED,
                    cursor="hand2" if enabled else "",
                )

    def paint_cell(self, index, value):
        colors = {
            "X": ("#1ABC9C", "#102B2A"),
            "O": ("#F4D03F", "#3A3212"),
            "": ("#EAECEE", "#2C3E50"),
        }
        fg, bg = colors.get(value, colors[""])
        self.cells[index].config(
            text=value,
            fg=fg,
            bg=bg,
            activeforeground=fg,
            activebackground=bg,
            disabledforeground=fg,
        )

    def close(self):
        self.closed = True
        self.send_command("__ttt_leave__")
        self.window.destroy()
