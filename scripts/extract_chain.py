# -*- coding: utf-8 -*-
"""提取「中」「史」「仲」的完整字形链文本（按阶段分组，含甲骨类组）"""
import io, json, os, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


# 阶段标记（含数量）：甲骨文 33 / 金文 71 / 楚系简帛 86 / 说文小篆 3 / 秦系简牍 3 / 隶书 22
MARK = re.compile(r"(甲骨文|金文|楚系简帛|说文小篆|说文古文|说文籀文|说文|秦系简牍|隶书|楷书|传抄古文字)\s*(\d+)?")
ORDER = ["甲骨文", "金文", "楚系简帛", "说文小篆", "说文古文", "说文籀文", "说文",
         "秦系简牍", "隶书", "传抄古文字", "楷书"]


def chain(ch):
    u = f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"
    t = strip(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=35
                                    ).read().decode("utf-8", "replace"))
    i = t.find("字源演变")
    if i < 0:
        return None
    seg = t[i:]
    j = seg.find("中国大陆")
    if j < 0:
        j = len(seg)
    seg = seg[:j]
    hits = [(m.start(), m.group(1), m.group(2)) for m in MARK.finditer(seg)]
    out = {}
    for k, (pos, name, num) in enumerate(hits):
        if name in out:
            continue
        end = hits[k + 1][0] if k + 1 < len(hits) else len(seg)
        body = seg[pos + len(name) + (len(num) if num else 0):end].strip()
        body = re.sub(r"[\u4e00-\u9fff]{0,2}更多\s*→?", "", body).strip()
        out[name] = {"n": int(num) if num else None, "body": body[:700]}
    return out


allc = {}
for ch in ["中", "史", "仲"]:
    c = chain(ch)
    allc[ch] = c
    print("=" * 100)
    print(f"【{ch}】")
    print("=" * 100)
    for st in ORDER:
        if st in c:
            print(f"  ▸ {st}（{c[st]['n']}）: {c[st]['body'][:520]}")
    print()

# 上古音
print("=" * 100)
print("上古音")
print("=" * 100)
for ch in ["中", "史", "仲", "屯", "春"]:
    u = f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"
    t = strip(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=35
                                    ).read().decode("utf-8", "replace"))
    m = re.search(r"上古音\s*(黄侃系统：[^；]*；)?\s*(王力系统：[^；]*；)?", t)
    print(f"  {ch}: {m.group(0).strip() if m else '—'}")

json.dump(allc, open(os.path.join(HERE, "result", "glyph_chain.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/glyph_chain.json")
