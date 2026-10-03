# -*- coding: utf-8 -*-
"""取仓库里的小 JSON，看标注结构；同时探测 figshare 数据集大小"""
import io, json, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0"}


def head_or_get(u, n=1200):
    try:
        req = urllib.request.Request(u, headers=H)
        with urllib.request.urlopen(req, timeout=90) as r:
            info = dict(r.headers)
            b = r.read(n)
        return info, b
    except Exception as e:
        return {"err": str(e)}, b""


RAW = "https://raw.githubusercontent.com/Pengjie-W/HUST-OBC/main/"
for f in ["OCR/Chinese_to_ID.json", "Validation/Validation_train.json",
          "Validation/Validation_label.json", "MoCo/MOCO_train.json"]:
    info, b = head_or_get(RAW + f, 900)
    print(f"===== {f}")
    print("  len:", info.get("Content-Length"), "type:", info.get("Content-Type"))
    print("  head:", b.decode("utf-8", "replace")[:600].replace("\n", " "))
    print()

print("===== figshare 数据集体积探测 =====")
for u in ["https://figshare.com/ndownloader/files/48465988?private_link=8a9c0420312d94fc01e3",
          "https://api.figshare.com/v2/articles/25040543"]:
    info, b = head_or_get(u, 600)
    print(f"--- {u[:80]}")
    print("  ", {k: v for k, v in info.items() if k.lower() in
                  ("content-length", "content-type", "content-disposition", "err")})
    if b:
        print("  head:", b.decode("utf-8", "replace")[:400].replace("\n", " "))
