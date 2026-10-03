# -*- coding: utf-8 -*-
"""列出 HUST-OBC 仓库里所有 json，挑小的拿来做类别分布"""
import io, json, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

H = {"User-Agent": "Mozilla/5.0"}


def get(u, raw=False):
    req = urllib.request.Request(u, headers=H)
    with urllib.request.urlopen(req, timeout=90) as r:
        b = r.read()
    return b if raw else b.decode("utf-8", "replace")


tree = json.loads(get("https://api.github.com/repos/Pengjie-W/HUST-OBC/git/trees/main?recursive=1"))
files = [(t["path"], t.get("size", 0)) for t in tree["tree"] if t["type"] == "blob"]
print("=== json/py files ===")
for p, s in sorted(files, key=lambda x: x[1]):
    if p.lower().endswith((".json", ".csv", ".txt")):
        print(f"  {s:>10,}  {p}")
print("\n=== all files > 200KB ===")
for p, s in sorted(files, key=lambda x: -x[1])[:15]:
    print(f"  {s:>10,}  {p}")
