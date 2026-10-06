# 用内置浏览器抓 B站详情和 X（复制即用）

内置浏览器工具是 `mcp__Claude_Browser__*`。批量操作用 `browser_batch`，一次放多个 navigate + javascript_tool。

## B站：读单个视频的粉丝数、简介、收藏

B站的详情接口经常返回 412（风控），直接打开视频页读页面里的数据最稳：

```js
// navigate 到 https://www.bilibili.com/video/BVxxxx 之后执行
const s=window.__INITIAL_STATE__;s?JSON.stringify({t:s.videoData?.title,up:s.upData?.name,fans:s.upData?.fans,desc:s.videoData?.desc?.slice(0,300),tags:(s.tags||[]).map(t=>t.tag_name).slice(0,8),v:s.videoData?.stat.view,l:s.videoData?.stat.like,f:s.videoData?.stat.favorite}):document.title
```
返回 document.title 是“出错啦”说明视频已删，跳过。

## B站：查某个 UP 主最近的视频（好博主名单用）

先 navigate 到 https://www.bilibili.com/ ，再执行：
```js
const r=await (await fetch('https://api.bilibili.com/x/web-interface/search/type?search_type=video&order=pubdate&keyword='+encodeURIComponent('UP主名字'),{credentials:'include'})).json();
(r.data?.result||[]).filter(v=>v.mid==UP主mid).slice(0,8).map(v=>[v.bvid,v.play,v.favorites,new Date(v.pubdate*1000).toISOString().slice(0,10),v.title.replace(/<[^>]+>/g,'')].join(' | '))
```
查 UP 主 mid：`search_type=bili_user&keyword=名字`，返回里的 `mid`、`fans`。

## X：搜索高赞帖子

URL 模板（`f=top` 是热门；`since:` 写日期；`min_faves:` 控制门槛，中文帖 300~800、英文帖 1000~2000 比较合适）：
```
https://x.com/search?q=<关键词> lang:zh min_faves:500 since:YYYY-MM-DD&f=top
```
流程：navigate → wait 3 → **先 screenshot**（不截图不能滚动）→ scroll 两次 → 执行：
```js
[...document.querySelectorAll('article')].map(a=>[[...a.querySelectorAll('a[href*="/status/"]')].map(x=>x.href).find(h=>/status\/\d+$/.test(h)),(a.querySelector('[data-testid="User-Name"]')?.innerText||'').replace(/\n/g,' ').slice(0,40),(a.querySelector('[data-testid="tweetText"]')?.innerText||a.innerText).slice(0,200).replace(/\n/g,' '),a.querySelector('[role="group"]')?.getAttribute('aria-label')].join(' | '))
```
看某个博主：`from:账号 min_faves:300 since:YYYY-MM-DD`。

## X：读正文和粉丝数

- 普通帖：`document.querySelector('article [data-testid="tweetText"]')?.innerText`
- 长文（Article，正文抓出来是空的）：`document.querySelector('main').innerText.slice(0,3000)`
- 粉丝数：打开 `https://x.com/账号` 后 `document.querySelector('a[href$="/verified_followers"], a[href$="/followers"]')?.innerText`

## 小红书

只能在你 Chrome 已登录的前提下用 `opencli xiaohongshu search "关键词" -f yaml`。返回 AUTH_REQUIRED 就跳过，在页面说明里写“小红书没登录，没抓”。**慢、少量、被拦就停，绝不做绕过防爬的事**（模拟鼠标、伪装等都不做，封的是你的号）。
