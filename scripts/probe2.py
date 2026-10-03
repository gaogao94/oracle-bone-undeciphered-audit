# -*- coding: utf-8 -*-
"""确认：字头(隶定字)在甲骨记录中的出现次数是否可查"""
import io, json, sys, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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
        rows = d.get("Table1") or []
        pd = (d.get("pageData") or [{}])[0] or {}
        return len(rows), pd.get("sumCount"), (rows[0] if rows else None)
    except Exception as e:
        return "ERR", str(e)[:60], None


print("=== 字头在现代字字段上搜不到，试试已知字头 ===")
for ch in ["屯", "春", "蠢", "王", "雨", "牛", "年", "月", "贞", "卜"]:
    n, s, row = q("YW", ch)
    print(f"YW='{ch}': rows={n} sum={s}")
    time.sleep(0.15)

print("\n=== 看一条完整记录有哪些字段 ===")
n, s, row = q("YW", "贞")
print(f"rows={n} sum={s}")
print(json.dumps(row, ensure_ascii=False, indent=1)[:900] if row else "no row")

print("\n=== 空条件时返回的记录字段（用于发现可用字段名）===")
body = json.dumps({
    "select": [],
    "condition": {"fieldName": "", "fieldValue": "", "pageIndex": 1,
                  "sortField": "", "sortDescAsc": "desc",
                  "checkedCatID": "", "selectedCatTypeID": "2",
                  "selectedGrade": "3"},
}).encode("utf-8")
req = urllib.request.Request(API, data=body, headers=HDRS, method="POST")
with urllib.request.urlopen(req, timeout=60) as r:
    j = json.loads(r.read().decode("utf-8-sig"))
d = j["Data"]
print("pageData:", json.dumps(d.get("pageData"), ensure_ascii=False))
print("row keys:", list((d.get("Table1") or [{}])[0].keys()))
print("row0:", json.dumps((d.get("Table1") or [{}])[0], ensure_ascii=False))
