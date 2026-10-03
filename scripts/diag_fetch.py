# -*- coding: utf-8 -*-
"""确诊：抓取为空是限流、URL 格式问题，还是解析问题"""
import io, os, re, sys, gzip, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}


def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=45) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        return b.decode("utf-8", "replace")


# 先看缓存里成功的那个文件长什么样
CACHE = r"D:\coding\gold_hunter\data\gxds"
files = sorted(os.listdir(CACHE))
print(f"缓存文件 {len(files)} 个，样例：")
for f in files[:12]:
    print("  ", f, os.path.getsize(os.path.join(CACHE, f)))
p7371 = [f for f in files if "7371" in f]
print("\n含 7371 的缓存:", p7371)
for f in p7371[:1]:
    t = open(os.path.join(CACHE, f), encoding="utf-8").read()
    trs = re.findall(r"<tr[^>]*>.*?</tr>", t, re.S | re.I)
    print(f"  {f}: len={len(t)} tr数={len(trs)}")
    for tr in trs[:3]:
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip()
                 for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
        print("    ", cells[:6])

print("\n" + "=" * 90)
print("重新抓取 7371，检查响应")
print("=" * 90)
for u in ["https://www.guoxuedashi.com/jgwhj/?page=1&bhfl=1&bh=7371&jgwfl=",
          "https://www.guoxuedashi.com/jgwhj/?bhfl=1&bh=7371"]:
    try:
        t = get(u)
        trs = re.findall(r"<tr[^>]*>.*?</tr>", t, re.S | re.I)
        print(f"  {u[-52:]:54s} len={len(t)} tr数={len(trs)}")
        body = re.search(r"编号\s*序号\s*释文\s*分类(.{0,300})", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
        print(f"     正文片段: {body.group(1)[:200] if body else '(未找到表格正文)'}")
    except Exception as e:
        print(f"  {u[-52:]:54s} ERR {type(e).__name__} {str(e)[:50]}")
    time.sleep(1.5)
