# -*- coding: utf-8 -*-
"""盘点 OBIMD 与殷契文渊里还没利用的字形/图像资源，判断"形"这一类证据能补到什么程度"""
import io, json, os, sys, collections, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")

print("=== 1) OBIMD 目录里到底有哪些文件/字段 ===")
for root, dirs, files in os.walk(OB):
    for f in files:
        p = os.path.join(root, f)
        print(f"  {os.path.relpath(p, HERE):48s} {os.path.getsize(p):>12,} B")

data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
print("\n=== 2) 片级字段与图像路径形态 ===")
print("  样本:", json.dumps(data[0], ensure_ascii=False)[:300])
paths = [p.get("Facsimile") for p in data[:5]]
print("  Facsimile 例:", paths)

print("\n=== 3) 图像能否下载（判断能否做部件分解）===")
base_try = [
    "https://hf-mirror.com/datasets/KLOBIP/OBIMD/resolve/main/",
    "https://hf-mirror.com/datasets/KLOBIP/OBIMD/resolve/main/facsimile/",
]
for b in base_try:
    u = b + (data[0]["Facsimile"] or "").split("/")[-1] if "facsimile/" not in b else b + "h00002.jpg"
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            ct = r.headers.get("Content-Type")
            cl = r.headers.get("Content-Length")
            print(f"  OK {u[-70:]}  type={ct} len={cl}")
            break
    except Exception as e:
        print(f"  ERR {u[-70:]}  {type(e).__name__} {str(e)[:40]}")

print("\n=== 4) 殷契文渊：能否按字形码取到图片与部首 ===")
# ZKBM -> 图片端点探测
for zkbm in ["U60000", "U60001"]:
    for pat in [
        f"https://jgw.aynu.edu.cn/File/GetFirstSmallPic?dbId=35&recordId={zkbm}&key=",
        f"https://jgw.aynu.edu.cn/home/zx/method/jgwzx.ashx?type=fontnum",
    ]:
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                pat, headers={"User-Agent": "Mozilla/5.0"}), timeout=20)
            print(f"  {pat[-60:]:62s} -> {r.status} {r.headers.get('Content-Type')}")
        except Exception as e:
            print(f"  {pat[-60:]:62s} -> ERR {str(e)[:40]}")

print("\n=== 5) 字形库中每个 ZKBM 的图片信息是否在 sortallbybs 响应里 ===")
DZ = json.load(open(os.path.join(D, "DZ.json"), encoding="utf-8"))
print("  DZ.json 字段:", list(DZ[0].keys()))
print("  样本:", json.dumps(DZ[0], ensure_ascii=False))
# 是否有重复 ZKBM 映射到不同部首
m = collections.defaultdict(set)
for r in DZ:
    m[r["ZKBM"]].add(r["BSBM"])
print(f"  不同 ZKBM {len(m)}；其中映射到多个部首的 {sum(1 for v in m.values() if len(v)>1)}")
