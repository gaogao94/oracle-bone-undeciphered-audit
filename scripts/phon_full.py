# -*- coding: utf-8 -*-
"""
补全音韵层：三系统（黄侃/王力/白一平-沙加尔或郑张）分组提取
修正上一版正则过严导致 37% 成功率的问题：
  - 把「上古音」到「韵书」之间的整段先切出来，再按「X系统：」逐段找「Y母 Z部」
  - 同时抓中古音（《广韵》反切）作为兜底
"""
import io, json, os, re, sys, time, collections, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
CACHE = os.path.join(D, "cache_phon.json")

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36",
       "Accept-Language": "zh-CN,zh;q=0.9"}
UNIT = re.compile(r"([\u4e00-\u9fff]母)\s*([\u4e00-\u9fff]部)")
SYS = re.compile(r"(黄侃系统|王力系统|白一平[－\-－]沙加尔系统|郑张尚芳系统|董同龢系统|周法高系统|李方桂系统)")


def strip_tags(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def parse_shang(txt):
    """切出上古音段，返回 {系统: 'X母Y部'}"""
    i = txt.find("上古音")
    if i < 0:
        return {}
    seg = txt[i:i + 400]
    j = seg.find("韵书")
    if j > 0:
        seg = seg[:j]
    out = {}
    parts = SYS.split(seg)
    # parts = [前文, 系统名1, 内容1, 系统名2, 内容2, ...]
    for k in range(1, len(parts) - 1, 2):
        name, body = parts[k], parts[k + 1]
        m = UNIT.search(body)
        if m:
            out[name] = f"{m.group(1)}{m.group(2)}"
    if not out:
        m = UNIT.search(seg)
        if m:
            out["unknown"] = f"{m.group(1)}{m.group(2)}"
    return out


def fetch(ch, cache, force=False):
    if ch in cache and cache[ch].get("systems") and not force:
        return cache[ch]
    rec = cache.get(ch) or {}
    rec.setdefault("systems", {})
    try:
        url = f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"
        html = urllib.request.urlopen(
            urllib.request.Request(url, headers=HDR), timeout=30
        ).read().decode("utf-8", "replace")
        txt = strip_tags(html)
        rec["systems"] = parse_shang(txt)
        # 中古音兜底：《广韵》反切
        m = re.search(r"广韵\s*([\u4e00-\u9fff]{1,3}切)", txt)
        rec["guangyun"] = m.group(1) if m else None
        if not rec.get("sources"):
            src = []
            for mm in re.finditer(r"甲骨文\s*(\d+)\s*([^\s]{2,28})", txt):
                src.append(mm.group(2))
                if len(src) >= 8:
                    break
            rec["sources"] = src
    except Exception as e:
        rec["err"] = str(e)[:60]
    cache[ch] = rec
    return rec


# ---- 需要查的字：全部语料字符
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
chars = sorted({mc[k]["codepoint"] for k in mc
                if (mc[k].get("codepoint") or "") and len(mc[k]["codepoint"]) == 1})

cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
todo = [c for c in chars if not (cache.get(c) or {}).get("systems")]
print(f"目标字 {len(chars)}；已有 systems 的 {len(chars)-len(todo)}；本轮需抓 {len(todo)}")

for i, ch in enumerate(todo, 1):
    fetch(ch, cache)
    if i % 50 == 0:
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        done = sum(1 for c in chars[:i] if (cache.get(c) or {}).get("systems"))
        print(f"   {i}/{len(todo)}  本轮成功 {done}")
    time.sleep(0.3)
json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

ok = sum(1 for c in chars if (cache.get(c) or {}).get("systems"))
print(f"\n最终：{ok}/{len(chars)} ({ok/len(chars):.1%}) 拿到上古音")
sysc = collections.Counter()
for c in chars:
    for k in (cache.get(c) or {}).get("systems", {}):
        sysc[k] += 1
print("各系统覆盖数:", dict(sysc))

# 抽样验证
print("\n抽样验证（应与已知音韵关系一致：屯/春/蠢 同文部；徹/歲 同月部）：")
for ch in ["屯", "春", "蠢", "徹", "阱", "歲", "伐", "貞", "王", "史", "畢", "丑"]:
    r = cache.get(ch) or {}
    print(f"  {ch}: {r.get('systems')}  广韵={r.get('guangyun')}")
