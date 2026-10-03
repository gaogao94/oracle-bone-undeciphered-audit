# -*- coding: utf-8 -*-
"""体检 + 字频查询试跑"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://jgw.aynu.edu.cn/home/zl/search/index.html",
    "Content-Type": "application/json;charset=UTF-8",
}
API = "https://jgw.aynu.edu.cn/AynuBone/FontSearch"

dz = json.load(open(os.path.join(DATA, "DZ.json"), encoding="utf-8"))
zx = json.load(open(os.path.join(DATA, "ZX.json"), encoding="utf-8"))


def report(name, rows):
    zk = {r["ZKBM"] for r in rows}
    empty = [r for r in rows if not r["FTZ"] and not r["JTZ"]]
    ftz_only = [r for r in rows if r["FTZ"] and not r["JTZ"]]
    both = [r for r in rows if r["FTZ"] and r["JTZ"]]
    jtz_only = [r for r in rows if not r["FTZ"] and r["JTZ"]]
    print(f"--- {name} ---")
    print(f"  rows={len(rows)}  distinct ZKBM={len(zk)}  distinct BSBM={len({r['BSBM'] for r in rows})}")
    print(f"  双空(未释)={len(empty)}  有FTZ无JTZ={len(ftz_only)}  双有={len(both)}  仅JTZ={len(jtz_only)}")
    return empty


e_dz = report("DZ 总单字", dz)
e_zx = report("ZX 总字形", zx)


def freq(ch, tries=3):
    body = json.dumps({
        "select": [{"conditionKey": "YW", "conditionValue": ch,
                    "conditionType": 0, "beforeConditionType": 0}],
        "condition": {"fieldName": "", "fieldValue": "", "pageIndex": 1,
                      "sortField": "", "sortDescAsc": "desc",
                      "checkedCatID": "", "selectedCatTypeID": "2",
                      "selectedGrade": "3"},
    }).encode("utf-8")
    for i in range(tries):
        try:
            req = urllib.request.Request(API, data=body, headers=HDRS, method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                j = json.loads(r.read().decode("utf-8-sig"))
            return int(j["Data"]["pageData"][0]["sumCount"])
        except Exception as e:
            if i == tries - 1:
                return None
            time.sleep(1 + i)
    return None


# 试跑：已识字（校准）+ 未释字样本
tests = ["屯", "春", "蠢", "阱", "徹", "王", "人", "牛", "雨", "禾"]
print("\n--- 字频试跑（已识字）---")
for ch in tests:
    t0 = time.time()
    n = freq(ch)
    print(f"  {ch}: {n}  ({time.time()-t0:.2f}s)")
    time.sleep(0.2)

sample_un = [r for r in e_dz if len(r["ZKBM"]) > 1][:8]
print("\n--- 字频试跑（未释字 ZKBM）---")
for r in sample_un:
    print(f"  {r['ZKBM']}  FTZ='{r['FTZ']}' JTZ='{r['JTZ']}'")
