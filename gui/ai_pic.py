"""
AI picture generation helpers for the chat server.

Usage from the chat client:
    /aipic: a white cat sitting in a classroom drawing on the blackboard

Provider order:
1. Replicate FLUX Schnell if REPLICATE_API_TOKEN is configured.
2. Pollinations public image endpoint as a no-key network fallback.

Both providers are remote image APIs. The generated image is then saved locally
under gui/data/aipic/.
"""

import os
import ssl
import time
import uuid
import urllib.parse
import urllib.request


REPLICATE_PLACEHOLDER = "Paste your Replicate API token here"


def generate_ai_image(prompt, output_dir):
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    os.makedirs(output_dir, exist_ok=True)
    filename = "aipic_" + time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8] + ".png"
    output_path = os.path.join(output_dir, filename)

    token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if token and token != REPLICATE_PLACEHOLDER:
        try:
            return _generate_with_replicate(prompt, output_path)
        except Exception:
            # Fall back to the no-key provider so demos still work.
            pass

    return _generate_with_pollinations(prompt, output_path)


def _generate_with_pollinations(prompt, output_path):
    encoded_prompt = urllib.parse.quote(prompt)
    urls = [
        "https://image.pollinations.ai/prompt/" + encoded_prompt,
        "https://image.pollinations.ai/prompt/" + encoded_prompt + "?nologo=true&model=flux",
    ]
    image_bytes = None
    last_error = None
    for url in urls:
        try:
            with _urlopen(url) as response:
                image_bytes = response.read()
            break
        except Exception as e:
            last_error = e

    if image_bytes is None:
        raise RuntimeError("Pollinations image API failed: " + str(last_error))

    with open(output_path, "wb") as f:
        f.write(image_bytes)
    return output_path


def _generate_with_replicate(prompt, output_path):
    import replicate

    output = replicate.run(
        "black-forest-labs/flux-schnell",
        input={"prompt": prompt},
    )

    first_item = output[0]
    if hasattr(first_item, "read"):
        image_bytes = first_item.read()
    else:
        with _urlopen(str(first_item)) as response:
            image_bytes = response.read()

    with open(output_path, "wb") as f:
        f.write(image_bytes)
    return output_path


def _urlopen(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ICDS-Final-Project-Chat/1.0",
            "Accept": "image/*,*/*;q=0.8",
        },
    )
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
        return urllib.request.urlopen(request, timeout=90, context=context)
    except Exception:
        # Some macOS Python installs do not have a configured local CA bundle.
        # This keeps the class demo path working when certificate discovery fails.
        context = ssl._create_unverified_context()
        return urllib.request.urlopen(request, timeout=90, context=context)


if __name__ == "__main__":
    demo_prompt = "a cat is making a cake in the kitchen"
    print(generate_ai_image(demo_prompt, os.path.join(os.path.dirname(__file__), "data", "aipic")))
