# -*- coding: utf-8 -*-
"""找出能按现代汉字取「甲骨文/金文/篆书」字形图的可用接口"""
import io, json, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Referer": "https://www.zdic.net/"}


def get(u, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H),
                                 timeout=timeout).read()


print("=== 1) 殷契文渊：按现代字查字形 ===")
h2 = {"User-Agent": H["User-Agent"], "Referer": "https://jgw.aynu.edu.cn/home/zl/index.html",
      "Content-Type": "application/json;charset=UTF-8"}
for body_key in [("YW", "寅"), ("DZ", "寅"), ("JTZ", "寅"), ("FTZ", "寅")]:
    b = json.dumps({"select": [{"conditionKey": body_key[0], "conditionValue": body_key[1],
                                "conditionType": 0, "beforeConditionType": 0}],
                    "condition": {"fieldName": "", "fieldValue": "", "pageIndex": 1,
                                  "sortField": "", "sortDescAsc": "desc", "checkedCatID": "",
                                  "selectedCatTypeID": "2", "selectedGrade": "3"}}).encode()
    try:
        req = urllib.request.Request("https://jgw.aynu.edu.cn/AynuBone/FontSearch",
                                     data=b, headers=h2, method="POST")
        j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig"))
        d = j.get("Data") or {}
        pd = (d.get("pageData") or [{}])[0] or {}
        print(f"  {body_key}: sum={pd.get('sumCount')} rows={len(d.get('Table1') or [])}")
    except Exception as e:
        print(f"  {body_key}: ERR {type(e).__name__} {str(e)[:50]}")

print("\n=== 2) 国学大师 殷周金文集成 ===")
for u in ["https://www.guoxuedashi.com/jinwen/",
          "https://www.guoxuedashi.com/jinwen/?bh=1"]:
    try:
        r = get(u)
        t = r.decode("utf-8", "replace")
        print(f"  {u[-40:]:44s} len={len(t)}  {re.sub(r'<[^>]+>',' ',t)[:100]!r}")
    except Exception as e:
        print(f"  {u[-40:]:44s} ERR {type(e).__name__} {str(e)[:50]}")

print("\n=== 3) 小学堂 字形演变 ===")
for u in ["https://xiaoxue.iis.sinica.edu.tw/yanbian?char=%E5%AF%85",
          "https://xiaoxue.iis.sinica.edu.tw/yanbian/List?char=%E5%AF%85",
          "https://xiaoxue.iis.sinica.edu.tw/"]:
    try:
        r = get(u)
        t = r.decode("utf-8", "replace")
        imgs = re.findall(r'(?:src|href)="([^"]+\.(?:gif|png|jpg))"', t)
        print(f"  {u[-50:]:52s} len={len(t)} imgs={imgs[:4]}")
    except Exception as e:
        print(f"  {u[-50:]:52s} ERR {type(e).__name__} {str(e)[:50]}")

print("\n=== 4) 汉字全息资源应用系统 / 其他 ===")
for u in ["https://qxk.bnu.edu.cn/", "https://www.ihp.sinica.edu.tw/~oracle/",
          "https://ndweb.iis.sinica.edu.tw/"]:
    try:
        r = get(u)
        print(f"  {u:44s} OK len={len(r)}")
    except Exception as e:
        print(f"  {u:44s} ERR {type(e).__name__} {str(e)[:45]}")

print("\n=== 5) zdic 是否有字形演变专用页 / 接口 ===")
for u in ["https://www.zdic.net/zd/zx/%E5%AF%85",
          "https://www.zdic.net/hans/%E5%AF%85/ziyuan",
          "https://img.zdic.net/jgw/5BC5.gif",
          "https://img.zdic.net/zy/5BC5.gif"]:
    try:
        r = get(u)
        print(f"  {u[-44:]:46s} OK len={len(r)} type={r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"  {u[-44:]:46s} ERR {type(e).__name__} {str(e)[:40]}")
