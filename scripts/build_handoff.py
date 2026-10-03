# -*- coding: utf-8 -*-
"""
建立完整交接包：
  对 OBIMD 全部未释字，逐片（1）取《合集》释文与类组
                    （2）下载原拓图
                    （3）判定编码缺失 / 真未释
输出：inventory.json + handoff/ 目录
"""
import io, os, re, sys, json, time, collections, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Referer": "https://www.guoxuedashi.com/jgwhj/",
     "Accept": "image/avif,image/webp,image/png,image/*,*/*;q=0.8"}
OB = os.path.join(_HERE, "data", "obimd")
RES = os.path.join(_HERE, "result")
HAND = os.path.join(_HERE, "handoff")
os.makedirs(HAND, exist_ok=True)
RUB = os.path.join(_HERE, "data", "rubbings")
os.makedirs(RUB, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []

freq = collections.Counter()
occ = collections.defaultdict(list)
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if not seq:
            continue
        labs = [c["Label"] for c in seq]
        freq.update(labs)
        for c in seq:
            if is_anon(c["Label"]):
                occ[c["Label"]].append(nm)

print(f"未释字 {len(occ)} 个，涉及片 {len({p for v in occ.values() for p in v})} 个")


def plate_rows(num):
    try:
        rows, _ = gxds2.query(num, maxpages=1)
        return rows
    except Exception:
        return []


def get_rub(num):
    p6 = str(num).zfill(6)
    fp = os.path.join(RUB, p6 + ".png")
    if os.path.exists(fp) and os.path.getsize(fp) > 1200:
        return fp
    u = f"https://pic2.39017.com/jgwhj/1/{p6}.png"
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=20) as r:
            b = r.read()
        if len(b) > 1200:
            open(fp, "wb").write(b)
            return fp
    except Exception:
        pass
    return None


PLACE = set("※□■…")
inventory = []
t0 = time.time()
for i, (lab, plist) in enumerate(sorted(occ.items(), key=lambda x: -freq[x[0]])):
    g = cp(lab) or lab
    uniq_pieces = sorted(set(plist))
    entry = {"glyph": g, "label": lab, "freq": freq[lab],
             "n_pieces": len(uniq_pieces), "pieces": uniq_pieces[:8],
             "corpus": [], "groups": [], "rubbings": [], "verdict": "?"}
    for nm in uniq_pieces[:3]:
        num = nm.lstrip("H")
        if not num.isdigit():
            continue
        rows = plate_rows(num)
        if rows:
            entry["corpus"].append({"plate": num, "group": rows[0]["group"],
                                    "text": " ".join(r["text"] for r in rows)[:200]})
            entry["groups"].append(rows[0]["group"])
        rp = get_rub(num)
        if rp:
            entry["rubbings"].append(os.path.basename(rp))
    inventory.append(entry)
    if (i + 1) % 20 == 0:
        print(f"  … {i+1}/{len(occ)}  用时 {time.time()-t0:.0f}s")

json.dump(inventory, open(os.path.join(HAND, "inventory.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] handoff/inventory.json（{len(inventory)} 条）")
n_rub = len([f for f in os.listdir(RUB) if f.endswith('.png')])
print(f"拓片已下载 {n_rub} 片 → data/rubbings/")
