# -*- coding: utf-8 -*-
"""检索「侯虎」「侯中」「侯屯」等，建立「侯X」人名的完整用例集"""
import io, re, sys, urllib.parse, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&ldquo;", "「").replace("&rdquo;", "」")
    return re.sub(r"\s+", " ", t)


def search(q):
    u = "https://www.xianqin.org/blog/?s=" + urllib.parse.quote(q)
    try:
        return strip(urllib.request.urlopen(
            urllib.request.Request(u, headers=H), timeout=40).read().decode("utf-8", "replace"))
    except Exception as e:
        return f"ERR {e}"


print("=" * 96)
print("xianqin 站内检索：「侯」字相关")
print("=" * 96)
for q in ["侯虎", "侯屯", "侯中", "比侯", "侯告", "侯奠", "侯璞"]:
    t = search(q)
    n = len(re.findall(r"entry-title", t))
    # 抓上下文
    ctx = []
    for m in re.finditer(re.escape(q), t):
        a = max(0, m.start() - 70)
        ctx.append(t[a:m.start() + 80])
        if len(ctx) >= 3:
            break
    print(f"\n【{q}】命中标题 {n}")
    for c in ctx:
        print(f"    …{c}…")
    time.sleep(0.5)
