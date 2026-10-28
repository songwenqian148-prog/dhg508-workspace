"""Copy the live TALK_SYSTEM prompt into research/prompts.md so the doc matches
the code. Run after editing the prompt in code/server.py."""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
srv = (root / "code" / "server.py").read_text(encoding="utf-8")
m = re.search(r'TALK_SYSTEM = """(.*?)"""', srv, re.S)
if not m:
    raise SystemExit("TALK_SYSTEM not found in server.py")
block = m.group(1).strip()

doc = root / "research" / "prompts.md"
text = doc.read_text(encoding="utf-8")
start = text.index("你在扮演《史记·刺客列传》里的一个人物")
end = text.index("```", start)
text = text[:start] + block + "\n" + text[end:]
doc.write_text(text, encoding="utf-8", newline="")
print("prompts.md updated; prompt is", len(block), "chars")
