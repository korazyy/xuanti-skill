#!/usr/bin/env python3
"""给挑中的作品抓细节：B站=完整简介+标签+章节+热评+AI字幕(若有)；YouTube=简介+字幕前段；Reddit/GitHub=正文/README。
用法: python3 detail.py picks.txt out.json   (picks.txt 每行一个链接)"""
import json, os, re, subprocess, sys, glob, http.cookiejar, urllib.request, urllib.parse, time

ENV = dict(os.environ, PATH=os.path.expanduser("~/.local/bin") + ":/opt/homebrew/bin:" +
           os.path.expanduser("~/.nvm/versions/node/v24.21.0/bin") + ":" + os.environ["PATH"])
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", UA), ("Referer", "https://www.bilibili.com/")]
op.open("https://www.bilibili.com/").read()
J = lambda u: json.loads(op.open(u).read())

def bili(url):
    bv = re.search(r"BV\w+", url).group(0)
    v = J(f"https://api.bilibili.com/x/web-interface/view?bvid={bv}")["data"]
    tags = [t["tag_name"] for t in J(f"https://api.bilibili.com/x/tag/archive/tags?bvid={bv}").get("data") or []]
    out = dict(title=v["title"], author=v["owner"]["name"], views=v["stat"]["view"], likes=v["stat"]["like"],
               favs=v["stat"]["favorite"], coins=v["stat"]["coin"], date=time.strftime("%Y-%m-%d", time.localtime(v["pubdate"])),
               dur_min=round(v["duration"] / 60, 1), desc=v["desc"][:800], tags=tags[:12],
               parts=[p["part"] for p in v.get("pages", [])][:15])
    try:
        r = J(f"https://api.bilibili.com/x/v2/reply/main?type=1&oid={v['aid']}&mode=3")
        out["hot_comments"] = [c["content"]["message"][:120] for c in (r.get("data") or {}).get("replies") or []][:8]
    except Exception as e: out["hot_comments"] = [f"ERR {e}"]
    try:
        s = J(f"https://api.bilibili.com/x/player/wbi/v2?bvid={bv}&cid={v['cid']}")
        subs = s["data"]["subtitle"]["subtitles"]
        if subs:
            su = subs[0]["subtitle_url"]; su = "https:" + su if su.startswith("//") else su
            body = J(su)["body"]; out["subtitle"] = "".join(b["content"] for b in body)[:2500]
    except Exception: pass
    return out

def yt(url):
    d = "ytsub"; os.makedirs(d, exist_ok=True)
    r = subprocess.run(["yt-dlp", "--skip-download", "--write-auto-sub", "--write-sub", "--sub-lang", "en.*,zh.*",
                        "--sub-format", "vtt", "--dump-json", "--no-simulate", "-o", f"{d}/%(id)s", url],
                       capture_output=True, text=True, env=ENV, timeout=180)
    v = json.loads(r.stdout.splitlines()[0]) if r.stdout else {}
    out = dict(title=v.get("title"), author=v.get("channel"), views=v.get("view_count"), likes=v.get("like_count"),
               date=v.get("upload_date"), dur_min=round((v.get("duration") or 0) / 60, 1),
               desc=(v.get("description") or "")[:800], chapters=[c["title"] for c in v.get("chapters") or []][:15])
    fs = glob.glob(f"{d}/{v.get('id')}*.vtt")
    if fs:
        lines, prev = [], None
        for l in open(fs[0], encoding="utf-8"):
            l = re.sub(r"<[^>]+>", "", l).strip()
            if not l or "-->" in l or l.startswith(("WEBVTT", "Kind:", "Language:")) or l == prev: continue
            lines.append(l); prev = l
        out["subtitle"] = " ".join(lines)[:2500]
    return out

def reddit(url):
    r = subprocess.run(["opencli", "reddit", "read", url, "-f", "json"], capture_output=True, text=True, env=ENV, timeout=150)
    return dict(raw=(r.stdout or r.stderr)[:2500])

def gh(url):
    repo = url.split("github.com/")[1].strip("/")
    r = subprocess.run(["gh", "api", f"repos/{repo}/readme", "--jq", ".content"], capture_output=True, text=True, env=ENV)
    import base64
    try: txt = base64.b64decode(r.stdout).decode()
    except Exception: txt = r.stderr
    s = subprocess.run(["gh", "api", f"repos/{repo}", "--jq", ".stargazers_count"], capture_output=True, text=True, env=ENV).stdout.strip()
    return dict(stars=s, readme=re.sub(r"\n\s*\n", "\n", txt)[:2500])

res = {}
for u in [l.strip() for l in open(sys.argv[1]) if l.strip()]:
    try:
        f = bili if "bilibili" in u else yt if "youtube" in u else reddit if "reddit" in u else gh
        res[u] = f(u); print("ok", u, file=sys.stderr)
    except Exception as e:
        res[u] = dict(error=str(e)); print("ERR", u, e, file=sys.stderr)
    time.sleep(0.8)
json.dump(res, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
