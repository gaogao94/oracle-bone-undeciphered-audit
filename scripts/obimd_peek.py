# -*- coding: utf-8 -*-
"""OBIMD 结构探查"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "obimd")
data = json.load(open(os.path.join(D, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(D, "main_character.json"), encoding="utf-8"))

print("data.json type:", type(data).__name__)
if isinstance(data, dict):
    print("top keys:", list(data.keys())[:20])
    for k in list(data.keys())[:3]:
        v = data[k]
        print(f"  {k}: {type(v).__name__}", (len(v) if hasattr(v, '__len__') else v))

if isinstance(data, list):
    print("list len:", len(data))
    print("item0 type:", type(data[0]).__name__)
    print("item0:", json.dumps(data[0], ensure_ascii=False)[:1500])

print("\nmain_character.json type:", type(mc).__name__)
if isinstance(mc, dict):
    ks = list(mc.keys())[:5]
    print("keys sample:", ks)
    print("sample val:", json.dumps(mc[ks[0]], ensure_ascii=False)[:600])
elif isinstance(mc, list):
    print("len:", len(mc))
    print("item0:", json.dumps(mc[0], ensure_ascii=False)[:600])
