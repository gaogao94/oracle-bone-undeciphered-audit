# -*- coding: utf-8 -*-
"""抓取殷契文渊"总单字/总字形"全库表，并落盘为 JSON。"""
import json, os, time, urllib.request

BASE = "https://jgw.aynu.edu.cn/home/zx/method/jgwzx.ashx"
HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://jgw.aynu.edu.cn/home/zl/index.html",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/plain, */*",
}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8-sig"))
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"failed {url}: {last}")


for typ, tag in (("sortallbybs", "DZ"), ("sortzxbybs", "ZX")):
    rows, sumpage = [], None
    for page in range(1, 21):
        obj = get(f"{BASE}?type={typ}&pageindex={page}")
        if sumpage is None:
            sumpage = obj["pageList"][0]["sumpage"]
        n0 = len(rows)
        for grp in obj.get("ALLDZ", []):
            for z in grp.get("JGWZX", []):
                rows.append({
                    "BSBM": grp.get("BSBM"),
                    "ZKBM": z.get("ZKBM"),
                    "FTZ": (z.get("FTZ") or "").strip(),
                    "JTZ": (z.get("JTZ") or "").strip(),
                })
        print(f"[{tag}] page {page}/{sumpage}: +{len(rows)-n0} (total {len(rows)})", flush=True)
        time.sleep(0.25)
    path = os.path.join(OUT, f"{tag}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print(f"[{tag}] WROTE {path} rows={len(rows)}", flush=True)
