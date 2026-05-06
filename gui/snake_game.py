"""
Snake game integrated from gaberomualdo/python-snake-game.

Original project:
https://github.com/gaberomualdo/python-snake-game

Adapted for Python 3 and for launching from this Tkinter chat client.
Original code is licensed under the MIT License; see THIRD_PARTY_LICENSES.md.
"""

import math
import random
import tkinter as tk


class SnakeGame:
    def __init__(self, master=None, on_game_over=None):
        self.window_dimensions = [625, 625]
        self.game_scale = 25
        self.game_dimensions = [
            self.window_dimensions[0] // self.game_scale,
            self.window_dimensions[1] // self.game_scale,
        ]
        self.frames_per_second = 12
        self.after_id = None
        self.on_game_over = on_game_over
        self.game_over = False

        if master is None:
            self.window = tk.Tk()
            self.owns_root = True
        else:
            self.window = tk.Toplevel(master)
            self.owns_root = False

        self.window.geometry(str(self.window_dimensions[0]) + "x" + str(self.window_dimensions[1]))
        self.window.resizable(False, False)
        self.window.title("Snake Game")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.game_canvas = tk.Canvas(
            self.window,
            width=self.window_dimensions[0],
            height=self.window_dimensions[1],
            bd=0,
            highlightthickness=0,
        )
        self.game_canvas.pack()

        self.player_coords = [
            math.floor(self.game_dimensions[0] / 2.0),
            math.floor(self.game_dimensions[1] / 2.0),
        ]
        self.player_tail = []
        self.player_velocity = [1, 0]
        self.velocity_changed_this_frame = False
        self.score = 0
        self.apple_coords = self.generate_apple_coords()

        self.window.bind("<KeyPress>", self.on_key_down)
        self.window.bind("<space>", self.restart)
        self.window.focus_set()
        self.gameloop()

    def generate_apple_coords(self):
        generated_apple_coords = [
            random.randint(0, self.game_dimensions[0] - 1),
            random.randint(0, self.game_dimensions[1] - 1),
        ]

        for item in self.player_tail:
            if item[0] == generated_apple_coords[0] and item[1] == generated_apple_coords[1]:
                return self.generate_apple_coords()

        return generated_apple_coords

    def create_grid_item(self, coords, hexcolor):
        self.game_canvas.create_rectangle(
            coords[0] * self.game_scale,
            coords[1] * self.game_scale,
            (coords[0] + 1) * self.game_scale,
            (coords[1] + 1) * self.game_scale,
            fill=hexcolor,
            outline="#222222",
            width=3,
        )

    def reset_game(self):
        self.player_coords = [
            math.floor(self.game_dimensions[0] / 2.0),
            math.floor(self.game_dimensions[1] / 2.0),
        ]
        self.player_tail = []
        self.player_velocity = [1, 0]
        self.score = 0
        self.apple_coords = self.generate_apple_coords()
        self.velocity_changed_this_frame = False
        self.game_over = False

    def gameloop(self):
        if self.game_over:
            return

        delay = int(1000 / self.frames_per_second)
        self.after_id = self.window.after(delay, self.gameloop)
        self.velocity_changed_this_frame = False

        self.game_canvas.delete("all")
        self.game_canvas.create_rectangle(
            0,
            0,
            self.window_dimensions[0],
            self.window_dimensions[1],
            fill="#222222",
            outline="#222222",
        )

        self.player_tail.append([self.player_coords[0], self.player_coords[1]])
        self.player_coords[0] += self.player_velocity[0]
        self.player_coords[1] += self.player_velocity[1]

        if (
            self.player_coords[0] < 0
            or self.player_coords[0] >= self.game_dimensions[0]
            or self.player_coords[1] < 0
            or self.player_coords[1] >= self.game_dimensions[1]
        ):
            self.finish_game()
            return

        for item in self.player_tail:
            if item[0] == self.player_coords[0] and item[1] == self.player_coords[1]:
                self.finish_game()
                return
            self.create_grid_item(item, "#00ff00")

        self.create_grid_item(self.apple_coords, "#ff0000")

        if self.apple_coords[0] == self.player_coords[0] and self.apple_coords[1] == self.player_coords[1]:
            self.score += 1
            self.apple_coords = self.generate_apple_coords()
        elif self.player_tail:
            self.player_tail.pop(0)

        self.game_canvas.create_text(
            12,
            12,
            anchor="nw",
            fill="#ffffff",
            font=("Helvetica", 14, "bold"),
            text="Score: " + str(self.score),
        )

    def finish_game(self):
        self.game_over = True
        if self.after_id is not None:
            try:
                self.window.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

        if self.on_game_over is not None:
            self.on_game_over(self.score)

        self.game_canvas.create_rectangle(
            0,
            0,
            self.window_dimensions[0],
            self.window_dimensions[1],
            fill="#111111",
            stipple="gray50",
            outline="#111111",
        )
        self.game_canvas.create_text(
            self.window_dimensions[0] // 2,
            self.window_dimensions[1] // 2 - 34,
            fill="#ffffff",
            font=("Helvetica", 32, "bold"),
            text="Game Over",
        )
        self.game_canvas.create_text(
            self.window_dimensions[0] // 2,
            self.window_dimensions[1] // 2 + 10,
            fill="#ffffff",
            font=("Helvetica", 18, "bold"),
            text="Score: " + str(self.score),
        )
        self.game_canvas.create_text(
            self.window_dimensions[0] // 2,
            self.window_dimensions[1] // 2 + 48,
            fill="#dddddd",
            font=("Helvetica", 14),
            text="Press Space to play again",
        )

    def restart(self, event=None):
        if not self.game_over:
            return
        self.reset_game()
        self.gameloop()

    def on_key_down(self, event):
        if self.velocity_changed_this_frame:
            return

        self.velocity_changed_this_frame = True
        if event.keysym == "Left" and self.player_velocity[0] != 1:
            self.player_velocity = [-1, 0]
        elif event.keysym == "Right" and self.player_velocity[0] != -1:
            self.player_velocity = [1, 0]
        elif event.keysym == "Up" and self.player_velocity[1] != 1:
            self.player_velocity = [0, -1]
        elif event.keysym == "Down" and self.player_velocity[1] != -1:
            self.player_velocity = [0, 1]
        else:
            self.velocity_changed_this_frame = False

    def close(self):
        if self.after_id is not None:
            try:
                self.window.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None
        self.window.destroy()

    def run(self):
        if self.owns_root:
            self.window.mainloop()


def launch_snake(master=None, on_game_over=None):
    game = SnakeGame(master, on_game_over)
    return game


if __name__ == "__main__":
    launch_snake().run()
