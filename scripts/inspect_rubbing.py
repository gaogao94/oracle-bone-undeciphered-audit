# -*- coding: utf-8 -*-
"""
从原拓图片按 Position 边界框切字形（用户要求的核心方法）
================================================
不再依赖字形包里的标准化图，而是：
  OBIMD data.json 的 Position(x,y,w,h) + rubbing/<name>.jpg → 切出真实拓片字形
先把 archive 解开，确认文件名映射，然后为候选切图并生成对照。
"""
import io, json, os, sys, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
Z = os.path.join(OB, "rubbing.zip")

z = zipfile.ZipFile(Z)
names = z.namelist()
print(f"条目数 {len(names):,}")
print("前 10 条:")
for n in names[:10]:
    print("  ", n, z.getinfo(n).file_size)
import collections
pref = collections.Counter("/".join(n.split("/")[:1]) for n in names)
print("顶层:", dict(pref))
ext = collections.Counter(os.path.splitext(n)[1].lower() for n in names)
print("扩展名:", dict(ext))

# 文件名是否与 RubbingName 对应
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
rn = {p["RubbingName"]: p for p in data if p.get("RubbingName")}
print(f"\ndata.json 片数 {len(data)}，有 RubbingName 的 {len(rn)}")
sample = list(rn.items())[:5]
print("RubbingName → Rubbing 路径:")
for k, v in sample:
    print(f"  {k} -> {v.get('Rubbing')}")
# 检查文件名匹配
files = {os.path.basename(n): n for n in names if n.lower().endswith(('.jpg', '.jpeg', '.png'))}
print(f"\n图像文件 {len(files)}")
matched = sum(1 for k, v in rn.items()
              if os.path.basename(v.get("Rubbing") or "") in files)
print(f"Rubbing 路径能对上文件的片数: {matched}/{len(rn)}")
