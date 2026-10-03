# -*- coding: utf-8 -*-
"""确认 OBIMD 图像可达性与体积，为"按 Position 切字形"做准备"""
import io, json, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0"}


def head(u):
    try:
        req = urllib.request.Request(u, headers=H, method="HEAD")
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.headers.get("Content-Length"), r.headers.get("Content-Type")
    except Exception as e:
        return "ERR", str(e)[:70], None


BASE = "https://hf-mirror.com/datasets/KLOBIP/OBIMD/resolve/main/"
cands = [
    "rubbing.zip", "facsimile.zip",
    "Hierarchical Character Metadata Supplement/Sub-character Images.zip",
    "OBIMD.py", "README.md",
]
for c in cands:
    st, cl, ct = head(BASE + urllib.parse.quote(c) if False else BASE + c.replace(" ", "%20"))
    mb = f"{int(cl)/1048576:.1f} MB" if (cl or "").isdigit() else cl
    print(f"  {c:60s} {st}  {mb}  {ct}")
