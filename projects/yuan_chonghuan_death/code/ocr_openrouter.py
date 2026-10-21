#!/usr/bin/env python3
"""OCR one image with an OpenRouter vision model.

Usage:
  python ocr_openrouter.py IMAGE [--model MODEL] [--prompt FILE] [--out FILE]

The API key is read from the OPENROUTER_API_KEY environment variable, or from
a .env file in any parent directory of this script. The key is never written
to the repository.
"""
import argparse
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = "google/gemini-3.8-flash"

DEFAULT_PROMPT = (
    "You are reading one page of a traditional Chinese woodblock-printed book. "
    "Transcribe every character exactly as printed, in traditional Chinese. "
    "Read the columns from right to left and within each column top to bottom. "
    "Do not translate. Do not add punctuation. Do not modernise characters. "
    "Do not guess: mark a character you cannot read as [？]. "
    "Return only the transcription, one column per line, in right-to-left order."
)


def load_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()
    for parent in pathlib.Path(__file__).resolve().parents:
        env = parent / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("OPENROUTER_API_KEY"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("No OPENROUTER_API_KEY in the environment or in a .env file")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", help="path to a local image file")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", help="path to a prompt file (else use the default)")
    ap.add_argument("--out", help="write the transcription here (else stdout)")
    args = ap.parse_args()

    if args.prompt:
        prompt = pathlib.Path(args.prompt).read_text(encoding="utf-8")
    else:
        prompt = DEFAULT_PROMPT

    image = pathlib.Path(args.image)
    mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(image.read_bytes()).decode("ascii")

    payload = {
        "model": args.model,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{data}"},
                    },
                ],
            }
        ],
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + load_key(),
            "Content-Type": "application/json",
            "X-Title": "dhg508 week-02 OCR",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        sys.exit(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}")

    text = body["choices"][0]["message"]["content"]
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(text)} chars, model={body.get('model')})")
    else:
        print(text)


if __name__ == "__main__":
    main()
