# -*- coding: utf-8 -*-
"""探测哪个 conditionKey 能按现代字检索（返回 屯/王 等高频字）"""
import json, time, urllib.request

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://jgw.aynu.edu.cn/home/zl/search/index.html",
    "Content-Type": "application/json;charset=UTF-8",
}
API = "https://jgw.aynu.edu.cn/AynuBone/FontSearch"


def q(key, val, ctype=0):
    body = json.dumps({
        "select": [{"conditionKey": key, "conditionValue": val,
                    "conditionType": ctype, "beforeConditionType": 0}],
        "condition": {"fieldName": "", "fieldValue": "", "pageIndex": 1,
                      "sortField": "", "sortDescAsc": "desc",
                      "checkedCatID": "", "selectedCatTypeID": "2",
                      "selectedGrade": "3"},
    }).encode("utf-8")
    try:
        req = urllib.request.Request(API, data=body, headers=HDRS, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read().decode("utf-8-sig"))
        d = j.get("Data") or {}
        return (len(d.get("Table1") or []),
                ((d.get("pageData") or [{}])[0] or {}).get("sumCount"))
    except Exception as e:
        return ("ERR", str(e)[:40])


keys = ["YW", "PM", "CC", "JLXS", "ZK", "ZX", "FTZ", "JTZ", "DZ", "JGWZ",
        "JGW", "ZI", "FONT", "XZ", "LS", "SW", "JS", "LX", "JTB", "JTGX",
        "GX", "BH", "SYS", "ID", "MC", "NAME", "TITLE", "GCBH", "CPMC"]
print("key   | 屯     | 王     | 屯(模糊)")
print("-" * 46)
for k in keys:
    a = q(k, "屯", 0)
    b = q(k, "王", 0)
    c = q(k, "屯", 2)
    print(f"{k:6s}| {str(a):18s}| {str(b):18s}| {c}")
    time.sleep(0.15)
