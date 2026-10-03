# -*- coding: utf-8 -*-
"""尝试把 OBIMD 字形与殷契文渊字形库连起来（PUA 码位比对）"""
import io, json, os, sys, collections
import openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")

wb = openpyxl.load_workbook(os.path.join(OB, "Sub-character to Glyph Code Point Mapping.xlsx"),
                            read_only=True, data_only=True)
subs = collections.defaultdict(list)
for i, (sub, gcp) in enumerate(wb.active.iter_rows(values_only=True)):
    if i == 0 or not sub:
        continue
    subs[sub].append(gcp)
wb.close()

allcp = [c for v in subs.values() for c in v]
print(f"OBIMD 字形码 {len(allcp):,}")
codes = [ord(c) for c in allcp]
print(f"码位范围: U+{min(codes):04X} … U+{max(codes):04X}")
hist = collections.Counter((c >> 12) for c in codes)
print("码位高 4 位分布（16 进制）:", {hex(k): v for k, v in sorted(hist.items())})

DZ = json.load(open(os.path.join(D, "DZ.json"), encoding="utf-8"))
zkbm = collections.Counter(r["ZKBM"] for r in DZ)
print(f"\n殷契文渊 ZKBM 样例: {list(zkbm)[:6]}")
zk_codes = [int(k[1:], 16) for k in zkbm if k.startswith("U")]
print(f"殷契文渊码位范围: U+{min(zk_codes):04X} … U+{max(zk_codes):04X}")

print("\n=== 交集检查 ===")
a = set(codes)
b = set(zk_codes)
print(f"OBIMD {len(a):,} 个码位｜殷契文渊 {len(b):,} 个码位｜交集 {len(a & b):,}")

# 也许有偏移关系
for off in [0x0, 0x10000, -0x10000, 0x90000, -0x90000]:
    shifted = set(c + off for c in a)
    print(f"  偏移 {off:+#x}: 交集 {len(shifted & b):,}")

# 用 sub->主要素 反查：OBIMD 内部是否用同一套
print("\n=== OBIMD 内部编号是否也是 PUA ===")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
pua = [v["codepoint"] for v in mc.values()
       if v.get("codepoint") and ord(v["codepoint"]) >= 0xE000]
print(f"  Main-character 里 PUA/私用码位 {len(pua):,} / {len(mc):,}")
print(f"  样例: {[(hex(ord(x)), x) for x in pua[:8]]}")
if pua:
    pc = [ord(x) for x in pua]
    print(f"  范围 U+{min(pc):04X} … U+{max(pc):04X}")
    inter = set(pc) & b
    print(f"  与殷契文渊 ZKBM 交集: {len(inter):,}")
    inter2 = set(pc) & a
    print(f"  与 OBIMD 字形码交集: {len(inter2):,}")
