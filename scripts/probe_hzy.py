# -*- coding: utf-8 -*-
"""探测 hanziyuan.net API：能否拿到字形分解（部件/偏旁）与甲骨文字形"""
import io, json, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept": "application/json, text/plain, */*"}


def get(u, raw=False):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30)
    b = r.read()
    return b if raw else b.decode("utf-8", "replace")


print("=== hanziyuan /api/ 目录 ===")
try:
    t = get("https://hanziyuan.net/api/")
    print(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))[:800])
except Exception as e:
    print("ERR", e)

print("\n=== 试常见端点 ===")
for p in ["/api/characters", "/api/character/%E5%B1%AF", "/api/search?q=%E5%B1%AF",
          "/api/word/%E5%B1%AF", "/api/dictionary/%E5%B1%AF"]:
    try:
        t = get("https://hanziyuan.net" + p)
        print(f"  {p:34s} OK len={len(t)}  {t[:110]!r}")
    except Exception as e:
        print(f"  {p:34s} ERR {type(e).__name__} {str(e)[:40]}")

print("\n=== 主站 JS 里的 API 路径 ===")
try:
    home = get("https://hanziyuan.net/")
    hits = set(re.findall(r"[\"'](/api/[A-Za-z0-9_/\-{}.$]{2,60})[\"']", home))
    print("  ", sorted(hits)[:30])
    hits2 = set(re.findall(r"axios\.(?:get|post)\(\s*[\"'`]([^\"'`]+)", home))
    print("  axios:", sorted(hits2)[:20])
except Exception as e:
    print("ERR", e)
