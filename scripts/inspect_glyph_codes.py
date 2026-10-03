# -*- coding: utf-8 -*-
"""细化：OBIMD 字形码单元格的实际结构"""
import io, collections, os, sys
import openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
wb = openpyxl.load_workbook(os.path.join(OB, "Sub-character to Glyph Code Point Mapping.xlsx"),
                            read_only=True, data_only=True)
rows = list(wb.active.iter_rows(values_only=True))[1:]
wb.close()

lens = collections.Counter(len(g) for _, g in rows if g)
print("字形码字符串长度分布:", dict(sorted(lens.items())[:10]))
print("\n长度 2 的样本（前 20）:")
n = 0
for sub, g in rows:
    if g and len(g) == 2:
        print(f"  sub={sub}  cell={g!r}  chars={[hex(ord(c)) for c in g]}")
        n += 1
        if n >= 20:
            break

print("\n长度 1 的样本（前 10）:")
n = 0
for sub, g in rows:
    if g and len(g) == 1:
        print(f"  sub={sub}  cell={g!r}  U+{ord(g):04X}")
        n += 1
        if n >= 10:
            break

print("\n长度 >2 的样本（前 10）:")
n = 0
for sub, g in rows:
    if g and len(g) > 2:
        print(f"  sub={sub}  cell={g!r}  chars={[hex(ord(c)) for c in g]}")
        n += 1
        if n >= 10:
            break

# 成分统计
first = collections.Counter(ord(g[0]) for _, g in rows if g)
print("\n首字符码位 Top10:", [(hex(k), v) for k, v in first.most_common(10)])
last = collections.Counter(ord(g[-1]) for _, g in rows if g)
print("末字符码位 Top10:", [(hex(k), v) for k, v in last.most_common(10)])
