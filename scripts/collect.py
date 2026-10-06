#!/usr/bin/env python3
"""抓某个方向的候选作品：B站(按播放)、YouTube(按播放)、Reddit(top)、GitHub(按星)。
用法: python3 collect.py 方向名 [--days N] [--out 目录]
  --days 120 = 做底子（默认）；--days 2 = 每日更新只抓最近两天
  会自动跳过 Obsidian 里已经收录过的链接。输出 <out>/cand_<方向>.json"""
import json, os, re, subprocess, sys, time, html, http.cookiejar, urllib.request, urllib.parse

ENV = dict(os.environ, PATH=os.path.expanduser("~/.local/bin") + ":/opt/homebrew/bin:" +
           os.path.expanduser("~/.nvm/versions/node/v24.21.0/bin") + ":" + os.environ["PATH"])
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"

import argparse
VAULT = os.path.expanduser(os.environ.get('XUANTI_VAULT', '~/Obsidian/AI'))  # 改成你自己的 Obsidian 文件夹
DIRS = json.load(open(os.path.join(os.path.dirname(__file__), "dirs.json")))

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", UA), ("Referer", "https://search.bilibili.com/")]

def bili(kw, n=20):
    if not cj: op.open("https://www.bilibili.com/").read()
    now = int(time.time())
    q = urllib.parse.urlencode(dict(keyword=kw, search_type="video", order="click",
                                    pubtime_begin_s=now - DAYS * 86400, pubtime_end_s=now))
    d = json.loads(op.open("https://api.bilibili.com/x/web-interface/search/type?" + q).read())
    out = []
    for v in (d.get("data") or {}).get("result", [])[:n]:
        out.append(dict(src="B站", kw=kw, title=html.unescape(re.sub("<[^>]+>", "", v["title"])),
                        author=v["author"], views=v["play"], likes=v["like"], favs=v.get("favorites"),
                        date=time.strftime("%Y-%m-%d", time.localtime(v["pubdate"])),
                        desc=v.get("description", "")[:150], url="https://www.bilibili.com/video/" + v["bvid"]))
    return out

def yt(kw, n=15):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(kw) + ("&sp=CAMSAggE" if DAYS > 7 else "&sp=CAMSBAgCEAE")
    r = subprocess.run(["yt-dlp", "--flat-playlist", "--dump-json", "--playlist-end", str(n), url],
                       capture_output=True, text=True, env=ENV, timeout=120)
    out = []
    for l in r.stdout.splitlines():
        v = json.loads(l)
        if not v.get("url", "").startswith("https://www.youtube.com/watch"): continue
        out.append(dict(src="YouTube", kw=kw, title=v.get("title"), author=v.get("channel"),
                        views=v.get("view_count"), desc=(v.get("description") or "")[:150], url=v["url"]))
    return out

def reddit(sub, n=25):
    r = subprocess.run(["opencli", "reddit", "subreddit", sub, "--sort", "top", "--time", ("month" if DAYS > 7 else "week"),
                        "--limit", str(n), "-f", "json"], capture_output=True, text=True, env=ENV, timeout=150)
    try: data = json.loads(r.stdout)
    except Exception: return [dict(src="Reddit", kw=sub, error=(r.stdout + r.stderr)[:200])]
    return [dict(src="Reddit", kw=sub, title=p["title"], author=p["author"], views=p["upvotes"],
                 comments=p["comments"], date=time.strftime("%Y-%m-%d", time.localtime(p["created_utc"])),
                 desc=(p.get("selftext") or "")[:200], url=p["url"]) for p in data]

def github(q, n=15):
    r = subprocess.run(["gh", "search", "repos", q, "--sort", "stars", "--limit", str(n), "--updated", ">" + time.strftime("%Y-%m-%d", time.localtime(time.time() - max(DAYS, 7) * 86400)),
                        "--json", "fullName,stargazersCount,description,url,createdAt"],
                       capture_output=True, text=True, env=ENV, timeout=60)
    try: data = json.loads(r.stdout)
    except Exception: return []
    return [dict(src="GitHub", kw=q, title=p["fullName"], views=p["stargazersCount"],
                 date=p["createdAt"][:10], desc=(p.get("description") or "")[:200], url=p["url"]) for p in data]

def seen_links():
    import glob
    urls = set()
    for p in glob.glob(VAULT + "/*选题研究/**/*.md", recursive=True):
        urls |= set(re.findall(r"https?://[^)\s|]+", open(p, encoding="utf-8").read()))
    return urls

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("--days", type=int, default=120); ap.add_argument("--out", default=".")
    a = ap.parse_args(); DAYS = a.days
    name = a.name; cfg = DIRS[name]; allc, errs = [], []
    jobs = [(bili, k) for k in cfg.get("bili", [])] + [(yt, k) for k in cfg.get("yt", [])] + \
           [(reddit, k) for k in cfg.get("reddit", [])] + [(github, k) for k in cfg.get("github", [])]
    for f, k in jobs:
        try:
            res = f(k); allc += res; print(f.__name__, k, len(res), file=sys.stderr)
        except Exception as e:
            errs.append(f"{f.__name__} {k}: {e}"); print("ERR", f.__name__, k, e, file=sys.stderr)
        time.sleep(1)
    seen, uniq = seen_links(), []
    for c in allc:
        if c.get("url") in seen: continue
        seen.add(c.get("url")); uniq.append(c)
    json.dump(dict(items=uniq, errors=errs), open(os.path.join(a.out, f"cand_{name}.json"), "w"), ensure_ascii=False, indent=1)
    print("total", len(uniq), "errors", errs, file=sys.stderr)
