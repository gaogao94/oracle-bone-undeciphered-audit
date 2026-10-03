# -*- coding: utf-8 -*-
"""
取 󺡅 的原拓字形：
  1) 测国学大师按字检索能否带出字形/图版
  2) 找出该字所在片，从 OBIMD rubbing.zip 取原拓
  3) 亦从 OBIMD facsimile.zip 取摹本
"""
import io, os, re, sys, json, gzip, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}


def get(u, t=40):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        return b.decode("utf-8", "replace")


print("=" * 96)
print("1) 国学大师按字检索：是否带字形图")
print("=" * 96)
for q in ["王", "禱", "木"]:
    u = "https://www.guoxuedashi.com/jgwhj/?page=1&bhfl=1&bh=" + urllib.parse.quote(q) + "&jgwfl="
    try:
        t = get(u)
    except Exception as e:
        print(f"  「{q}」ERR {e}")
        continue
    imgs = re.findall(r'<img[^>]*src="([^"]+)"', t)
    # 过滤掉界面图标
    real = [i for i in imgs if not any(k in i.lower() for k in
            ("ico", "logo", "banner", "btn", "arrow", "gif"))]
    print(f"  「{q}」len={len(t)}  img 总数={len(imgs)}  疑似字形图={len(real)}")
    for i in real[:6]:
        print(f"       {i[:110]}")

print("\n" + "=" * 96)
print("2) 页面上是否有图版/拓片链接")
print("=" * 96)
u = "https://www.guoxuedashi.com/jgwhj/?page=1&bhfl=1&bh=5250&jgwfl="
t = get(u)
for pat in [r'<img[^>]*>', r'href="([^"]*(?:jpg|png|gif|bmp)[^"]*)"',
            r'图版', r'拓片', r'点击', r'onclick="[^"]{0,120}"']:
    hits = re.findall(pat, t, re.I)
    print(f"  {pat[:30]:32s}: {hits[:5]}")

print("\n" + "=" * 96)
print("3) OBIMD 字形图的实际文件名与来源")
print("=" * 96)
import zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
names = [n for n in ZS.namelist() if "gx21ndp7yy" in n]
print(f"  󺡅 的字形图 {len(names)} 个:")
for n in names:
    print(f"     {n}  ({ZS.getinfo(n).file_size} bytes)")
print("\n  样例路径结构:")
for n in ZS.namelist()[:5]:
    print(f"     {n}")
