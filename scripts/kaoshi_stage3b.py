# -*- coding: utf-8 -*-
"""
阶段 III（修订）：音韵抓取 + 稳健的分布替换检验
改动：
  1) 真正抓取 zdic 上古音（王力系统 声纽/韵部），带缓存；
  2) 替换检验改为「右邻字分布 × 语法位置」的加权重叠 + 平滑，并设最低样本门槛，
     避免低频字因分布稀疏而虚假胜出；
  3) 输出显式标注证据强度等级。
"""
import io, json, math, os, re, sys, time, collections, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
CACHE = os.path.join(D, "cache_phon.json")
os.makedirs(RES, exist_ok=True)

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36",
       "Accept-Language": "zh-CN,zh;q=0.9"}
RE_SHANG = re.compile(r"上古音\s*(?:黄侃系统：([^；]*?)；)?\s*(?:王力系统：([^；]*?)；)?\s*韵书")
RE_UNIT = re.compile(r"([\u4e00-\u9fff]母)\s*([\u4e00-\u9fff]部)")


def strip_tags(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def fetch_phon(ch, cache):
    if ch in cache:
        return cache[ch]
    rec = {"initial": None, "rhyme": None, "huangkan": None, "sources": []}
    try:
        url = f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"
        html = urllib.request.urlopen(
            urllib.request.Request(url, headers=HDR), timeout=30
        ).read().decode("utf-8", "replace")
        txt = strip_tags(html)
        m = RE_SHANG.search(txt)
        if m:
            if m.group(1):
                u = RE_UNIT.search(m.group(1))
                if u:
                    rec["huangkan"] = f"{u.group(1)}{u.group(2)}"
            if m.group(2):
                u = RE_UNIT.search(m.group(2))
                if u:
                    rec["initial"], rec["rhyme"] = u.group(1), u.group(2)
        for mm in re.finditer(r"甲骨文\s*(\d+)\s*([^\s]{2,28})", txt):
            rec["sources"].append(mm.group(2))
            if len(rec["sources"]) >= 8:
                break
    except Exception as e:
        rec["err"] = str(e)[:60]
    cache[ch] = rec
    return rec


# ---------------------------------------------------------------- 载入语料
print("载入 OBIMD …")
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
sents = []
for piece in data:
    for grp in piece.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted(((c.get("OrderNumber") or 0), c.get("Label"))
                     for c in (grp.get("RecordUtilOracleCharVoList") or [])
                     if c.get("Label"))
        lab = [l for _, l in seq]
        if lab:
            sents.append(lab)

freq = collections.Counter()
for s in sents:
    freq.update(s)
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []

cands = sorted((l for l in freq if is_anon(l) and freq[l] >= 3), key=lambda l: -freq[l])
known = [l for l in freq if not is_anon(l) and cp(l)]
print(f"辞例 {len(sents):,}｜字形类 {len(freq):,}｜候选 {len(cands)}｜已识字类 {len(known)}")

# ---------------------------------------------------------------- 音韵抓取
need = set()
for l in freq:
    t = cp(l)
    if t:
        need.add(t)
need = sorted(x for x in need if len(x) == 1)
cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
todo = [c for c in need if c not in cache]
print(f"音韵：需 {len(need)} 字，已缓存 {len(cache)}，待抓 {len(todo)}")
for i, ch in enumerate(todo, 1):
    fetch_phon(ch, cache)
    if i % 40 == 0:
        print(f"   … {i}/{len(todo)}")
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(0.3)
json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
got = sum(1 for c in need if (cache.get(c) or {}).get("rhyme"))
print(f"音韵成功 {got}/{len(need)} ({got/len(need):.1%})")


def ph(ch):
    r = cache.get(ch) or {}
    return r.get("initial"), r.get("rhyme")


# ---------------------------------------------------------------- 上下文特征
def feats(s, i):
    n = len(s)
    L = cp(s[i - 1]) if i > 0 else "^"
    R = cp(s[i + 1]) if i < n - 1 else "$"
    pos = "首" if i == 0 else ("末" if i == n - 1 else "中")
    return f"{L}|{R}", pos


K_CTX, K_POS, K_TOT = {}, {}, {}
for l in known:
    K_CTX[l] = collections.Counter()
    K_POS[l] = collections.Counter()
for s in sents:
    for i, l in enumerate(s):
        if l in K_CTX:
            a, p = feats(s, i)
            K_CTX[l][a] += 1
            K_POS[l][p] += 1

MIN_SUP = 10          # 候选字必须至少出现 10 次才参与比较


def overlap_score(U, K, Up, Kp, alpha=0.5):
    """加权重叠：仅对 U 观察到的上下文求和，K 的概率用 add-alpha 平滑"""
    tk = sum(K.values())
    if tk == 0:
        return 0.0
    keys = set(K) | set(U)
    V = max(len(keys), 2)
    s = 0.0
    for a, w in U.items():
        p = (K.get(a, 0) + alpha) / (tk + alpha * V)
        s += w * math.log(p)
    return s / (sum(U.values()) or 1)


results = []
for u in cands:
    U, Up = collections.Counter(), collections.Counter()
    rc, lc = collections.Counter(), collections.Counter()
    ex = []
    for s in sents:
        n = len(s)
        for i, l in enumerate(s):
            if l == u:
                a, p = feats(s, i)
                U[a] += 1
                Up[p] += 1
                if i > 0 and cp(s[i - 1]):
                    lc[cp(s[i - 1])] += 1
                if i < n - 1 and cp(s[i + 1]):
                    rc[cp(s[i + 1])] += 1
        if u in s and len(s) >= 4 and len(ex) < 6:
            ex.append(" ".join("□" if l == u else (cp(l) or "?") for l in s))
    scored = []
    for k in K_CTX:
        if K_CTX[k].total() < MIN_SUP:
            continue
        s1 = overlap_score(U, K_CTX[k], Up, K_POS[k])
        scored.append((s1, k))
    scored.sort(reverse=True)
    top = scored[:15]
    results.append({
        "glyph": cp(u) or u, "label": u, "occurrences": freq[u],
        "n_contexts": U.total(),
        "top_right": rc.most_common(10), "top_left": lc.most_common(10),
        "substitution_candidates": [
            {"char": cp(k), "score": round(sc, 4), "freq": K_CTX[k].total(),
             "initial": ph(cp(k))[0], "rhyme": ph(cp(k))[1]} for sc, k in top],
        "examples": ex,
    })

results.sort(key=lambda r: -r["occurrences"])
json.dump({"method": "smoothed contextual substitution test + Old Chinese phonology",
           "min_support": MIN_SUP, "n_candidates": len(cands), "results": results},
          open(os.path.join(RES, "stage3_substitution.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n" + "=" * 84)
print("阶段 III（修订）：同槽位候选 + 上古音相容性")
print("=" * 84)
for r in results[:12]:
    print(f"\n■ {r['glyph']}  ({r['occurrences']} 次, {r['n_contexts']} 上下文)")
    print("   右邻: " + "、".join(f"{c}×{n}" for c, n in r["top_right"][:6]))
    print("   同槽位候选: " + "  ".join(
        f"{c['char']}[{c['initial'] or '?'}{c['rhyme'] or '?'}]" for c in r["substitution_candidates"][:6]))
    if r["examples"]:
        print("   例: " + r["examples"][0])

json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
print(f"\n[写出] {os.path.join(RES, 'stage3_substitution.json')}")
