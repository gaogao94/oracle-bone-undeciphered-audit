# -*- coding: utf-8 -*-
"""检查字形图像包的结构：能不能按 Label 取到字形图"""
import io, os, sys, zipfile, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
Z = os.path.join(OB, "subchar_images.zip")

z = zipfile.ZipFile(Z)
names = z.namelist()
print(f"条目数 {len(names):,}")
print("前 25 条:")
for n in names[:25]:
    print("  ", n, z.getinfo(n).file_size)

# 目录结构
pref = collections.Counter("/".join(n.split("/")[:2]) for n in names)
print("\n目录分布（前 15）:")
for k, v in pref.most_common(15):
    print(f"  {k}: {v}")

# 扩展名
ext = collections.Counter(os.path.splitext(n)[1].lower() for n in names)
print("\n扩展名:", dict(ext))

# 看是否以 Label 命名
import json
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
labels = set(mc.keys())
hit = [n for n in names if os.path.splitext(os.path.basename(n))[0] in labels]
print(f"\n文件名直接命中 Label 的条目: {len(hit)}")
if hit:
    print("  例:", hit[:8])
    print("  对应字:", [(n, mc[os.path.splitext(os.path.basename(n))[0]].get('codepoint')) for n in hit[:8]])
