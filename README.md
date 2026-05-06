# ICDS_Final-Project

Python socket chatroom with a Tkinter GUI, integrated games, a shared Snake
leaderboard, Tic-Tac-Toe Online, and AI image generation.

## Requirements

- Python 3
- Tkinter, usually included with Python
- Internet access for AI image generation
- Optional: `REPLICATE_API_TOKEN` for Replicate FLUX image generation
- Optional: `replicate` package if using Replicate

The AI image feature can also use the no-key Pollinations endpoint.

## Run

Start the server from the `gui` directory:

```bash
cd gui
python3 chat_server.py
```

Start one or more clients in separate terminals:

```bash
cd gui
python3 chat_cmdl_client.py
```

Log in with a name and password. The first login creates the account. Later
logins with the same name must use the same password.

## Chat Commands

The chat input supports these commands:

```text
time: calendar time in the system
who: to find out who else are there
c _peer_: to connect to the _peer_ and chat
? _term_: to search your chat logs where _term_ appears
p _#_: to get number <#> sonnet
/aipic: _prompt_: to generate an AI image
leaderboard: to show the Snake leaderboard
ttt: to open Tic-Tac-Toe Online
q: to leave the chat system
```

The GUI also provides buttons for common actions: `Time`, `Who`, `Poem`,
`Search`, `Snake`, `Scores`, `Tic-Tac-Toe`, and `Leave Chat`.

## Emoji Shortcuts

The chat input supports emoji keywords that are automatically converted to emoji characters. Example shortcuts include:

- `e_happy` → 😀
- `e_sad` → 😢
- `e_love` → 😍
- `e_cool` → 😎
- `e_cry` → 😢
- `e_angry` → 😡
- `e_thumbup` → 👍
- `e_thumbdown` → 👎
- `e_heart` → ❤️
- `e_fire` → 🔥

## Group Chat

Users can form a group through the connect command. For example:

```text
alice: c bob
charlie: c bob
```

If `bob` is already chatting with `alice`, then `charlie` joins the same group.
Messages sent by any member are forwarded by the server to the other group
members.

## AI Picture Generation

Type an image command in the chat input:

```text
/aipic: a white cat sitting in a classroom drawing on the blackboard
```

The client detects the `/aipic:` prefix, extracts the prompt, and sends it to
the chat server. The server calls an image generation provider and saves the
generated image under:

```text
gui/data/aipic/
```

If the user is currently chatting with peers, the generated image path is also
sent to the peers.

Provider order:

```text
1. Replicate FLUX Schnell, if REPLICATE_API_TOKEN is set
2. Pollinations public image endpoint as a no-key fallback
```

To use Replicate:

```bash
export REPLICATE_API_TOKEN="your token"
```

Both providers are remote image APIs. The generated file is saved locally after
the API returns it. The original Pollinations starter is kept as:

```text
gui/examples/ai_pic2_pollinations_demo.py
```

## Snake Leaderboard

The `Snake` button opens a Tkinter Snake game adapted from:

```text
https://github.com/gaberomualdo/python-snake-game
```

Each player runs Snake locally. When the game ends, the client reports the score
to the chat server. The server keeps each user's best score, sorts the global
leaderboard, and broadcasts updated rankings to connected clients.

Leaderboard data is stored at:

```text
gui/data/leaderboard.json
```

Use the `Scores` button or the `leaderboard` command to view the rankings.

## Tic-Tac-Toe Online

The `Tic-Tac-Toe` button opens a graphical two-player game window inspired by:

```text
https://github.com/yumin-chen/tic-tac-toe-in-python
```

Two logged-in clients join the same server-managed game. The clients render the
board and send moves. The chat server assigns X/O, enforces turns, rejects
illegal moves, checks win/draw conditions, and sends synchronized board state
back to both players.

This satisfies the interactive multiplayer gaming model:

```text
clients render UI and send actions
server owns the game state and synchronizes players
```

## Demo Checklist

1. Start `chat_server.py`.
2. Start two or three clients.
3. Log in as different users.
4. Use `who` to show online users.
5. Use `c _peer_` to connect and chat.
6. Add a third user through the same peer to show group chat.
7. Send `/aipic: a cat wearing sunglasses` and check `gui/data/aipic/`.
8. Play Snake, end the game, and show updated `Scores`.
9. Open `Tic-Tac-Toe` from two clients and make moves in both windows.

## Project Structure

```text
gui/chat_server.py          server, login, chat routing, games, AI images
gui/chat_cmdl_client.py     client entry point
gui/chat_client_class.py    client socket wrapper
gui/client_state_machine.py client command/state handling
gui/GUI.py                  Tkinter chat UI
gui/chat_group.py           group membership logic
gui/chat_utils.py           socket message helpers and command menu
gui/snake_game.py           Snake game window
gui/tictactoe_game.py       Tic-Tac-Toe Online window
gui/ai_pic.py               AI image generation helper
gui/data/                   users, chat indices, generated runtime data
```

## Generated Files

The app may generate these files while running:

```text
gui/data/users.json
gui/data/indices/
gui/data/leaderboard.json
gui/data/aipic/
```

## Third-Party Credits

Third-party license details are in:

```text
gui/THIRD_PARTY_LICENSES.md
```
