# -*- coding: utf-8 -*-
"""
诊断：《合集》释文里"打不出来"的位置是 PUA 码位、还是扩展区汉字、还是真缺字？
"""
import io, os, re, sys, json, collections, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

CACHE = os.path.join(_HERE, "data", "gxds2")
files = [f for f in os.listdir(CACHE) if f.endswith(".html")]
print(f"缓存 HTML {len(files)} 个")

codes = collections.Counter()
for f in files:
    t = open(os.path.join(CACHE, f), encoding="utf-8").read()
    # 只看释文列（第 4 列）
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 4:
            continue
        txt = re.sub(r"<[^>]+>", " ", tds[3])
        txt = re.sub(r"\s+", " ", txt)
        for ch in txt:
            codes[ch] += 1

print(f"\n不同字符 {len(codes)} 个")
print("\n=== 非 BMP（U+10000 以上）或 PUA 字符 ===")
special = []
for ch, n in codes.items():
    o = ord(ch)
    if o > 0xFFFF or 0xE000 <= o <= 0xF8FF or 0xF0000 <= o <= 0xFFFFD or 0x100000 <= o <= 0x10FFFD:
        special.append((o, ch, n))
special.sort()
for o, ch, n in special[:40]:
    try:
        name = unicodedata.name(ch)
    except Exception:
        name = "(no name)"
    blk = ""
    if 0xF0000 <= o <= 0xFFFFD:
        blk = "PUA-A"
    elif 0x100000 <= o <= 0x10FFFD:
        blk = "PUA-B"
    elif 0xE000 <= o <= 0xF8FF:
        blk = "PUA"
    elif o > 0xFFFF:
        blk = "SIP"
    print(f"  U+{o:05X}  {blk:6s}  x{n:<4} {name[:60]}")
print(f"\n特殊字符共 {len(special)} 种，总计出现 {sum(n for _,_,n in special)} 次")

# 统计 BMP 里的生僻字
print("\n=== BMP 中高码位字符（U+9000 以上，多为生僻字）===")
hi = collections.Counter()
for ch, n in codes.items():
    o = ord(ch)
    if 0x9000 <= o <= 0xFFFF:
        hi[ch] += n
print(f"  种类 {len(hi)}")
for ch, n in hi.most_common(30):
    try:
        name = unicodedata.name(ch)
    except Exception:
        name = "?"
    print(f"  {ch} U+{ord(ch):04X} x{n}  {name[:50]}")

# 统计释文里的占位符
print("\n=== 占位符统计 ===")
for ph in ["※", "□", "■", "…", "〔", "〕", "\ue000-\uf8ff"]:
    if ph == "\ue000-\uf8ff":
        continue
    print(f"  '{ph}' 出现 {sum(n for ch,n in codes.items() if ch==ph)} 次")
