"""
Original Pollinations starter demo kept for reference.

The production chat integration lives in ../ai_pic.py, which uses this same
no-key endpoint as a fallback provider and saves generated images under
gui/data/aipic/.
"""

import requests


prompt = "a cat is making a cake in the kitchen"
url = f"https://image.pollinations.ai/prompt/{prompt}"

img = requests.get(url).content

with open("cat.png", "wb") as f:
    f.write(img)
