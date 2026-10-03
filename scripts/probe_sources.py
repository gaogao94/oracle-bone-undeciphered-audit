# -*- coding: utf-8 -*-
"""探测：字形演变谱系 + 音韵（上古音）数据源可达性
考释三类证据里，字形链和音韵这两类需要外部知识库，先确认拿不拿得到。
"""
import io, json, os, sys, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
     "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def probe(url, note=""):
    try:
        req = urllib.request.Request(url, headers=H)
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read(400)
            return f"OK {r.status} len~{r.headers.get('Content-Length') or '?'} :: {b[:80]!r}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"ERR {type(e).__name__}: {str(e)[:60]}"


print("=== 字形/字源类 ===")
for u in [
    "https://www.zdic.net/",
    "https://www.zdic.net/hans/%E5%B1%AF",
    "https://hanziyuan.net/",
    "https://ccamc.org/",
    "https://www.iguwen.net/",
    "https://www.guoxuedashi.com/",
    "https://www.guoxuedashi.com/jgwhj/?bh=1",
    "https://xiaoxue.iis.sinica.edu.tw/",
    "https://xiaoxue.iis.sinica.edu.tw/yanbian",
]:
    print(f"  {u:58s} {probe(u)}")

print("\n=== 音韵 / 上古音 ===")
for u in [
    "https://baoding.bnu.edu.cn/",
    "https://www.eastling.org/",
    "https://ytenx.org/",
    "https://ytenx.org/kyonh/",
    "https://www.unicode.org/charts/PDF/U4E00.pdf",
]:
    print(f"  {u:58s} {probe(u)}")

print("\n=== OBIMD 字形类 → 是否为「未释」（用 Main-character.json 判定） ===")
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "obimd")
mc = json.load(open(os.path.join(D, "main_character.json"), encoding="utf-8"))
print("  Main-character.json 条目数:", len(mc))
ks = list(mc.keys())[:8]
for k in ks:
    print(f"    {k} -> {json.dumps(mc[k], ensure_ascii=False)}")
# 看 codepoint 字段的取值形态分布
import collections
lens = collections.Counter(len(v.get("codepoint") or "") for v in mc.values())
print("  codepoint 长度分布:", dict(sorted(lens.items())))
tr = collections.Counter(len(v.get("transcription") or []) for v in mc.values())
print("  transcription 条数分布:", dict(sorted(tr.items())))
