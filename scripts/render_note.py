"""把 items + 选题 + 发现 渲染成 Obsidian 页面（固定格式，别改）。
items 每条是 11 元组：(组名, 标题, 链接, 平台行, 成绩行, 播放短, 爆款, 推荐3或2, 他做了什么, 你能借鉴的, 额外备注或"")
topics 是 [(选题, 从哪来, 为什么推荐), ...]，findings 是字符串列表。
用法：from render_note import render; render(path, 方向说明, 标题, 引言, items, topics, findings, 说明, date="YYYY-MM-DD")
"""
def render(path, direction_meta, title, intro, items, topics, findings, note, date=None):
    import time
    date = date or time.strftime("%Y-%m-%d")
    rec={3:"✅⭐⭐⭐",2:"⭐⭐"}
    groups=[]
    for it in items:
        if it[0] not in groups: groups.append(it[0])
    L=["---",f"方向: {direction_meta}",f"抓取日期: {date}","来源: B站 · YouTube · X · GitHub · Reddit（小红书待登录后补）","---","",
       f"# {title}","",intro,"> **💰** = 推广付费工具或拉社群。只放 ⭐⭐ 以上，凑数的不放。","",
       "## 作品总表","",
       "> **怎么看这张表**：**点标题** = 直接打开原视频/原帖；**点最右边 👇** = 跳到下面我写的详细介绍。",
       "> **推荐**：✅⭐⭐⭐ = 最推荐先看（干货最多、观众最用得上）；⭐⭐ = 值得看。",
       "> **播放**：B站/YouTube 是播放量，X 是阅读量，GitHub 是星数，Reddit 是赞数。**爆款** = 播放 ÷ 粉丝数，🔥 = 低粉爆款。",
       "","| 编号 | 标题（点了直接打开原视频） | 播放 | 爆款 | 推荐 | 介绍 |","|---|---|---|---|---|---|"]
    for i,it in enumerate(items,1):
        L.append(f"| {i} | [{it[1]}]({it[2]}) | {it[5]} | {it[6]} | {rec[it[7]]} | [[#{i}. {it[1]}\\|👇]] |")
    L+=["","---","",f"## 🎬 今天可以拍的 {len(topics)} 个选题","",f"> 从上面 {len(items)} 个里提炼的，按我推荐的顺序排。**这是初稿，拍之前要核实原文。**","",
        "| 顺序 | 选题（口语化标题） | 从哪来 | 为什么推荐 |","|---|---|---|---|"]
    for n,(t,src,why) in enumerate(topics,1):
        L.append(f"| {n} | **{t}** | {src} | {why} |")
    L+=["","---",""]
    for g in groups:
        its=[(i,it) for i,it in enumerate(items,1) if it[0]==g]
        L+=[f"## {g}（{len(its)} 个）",""]
        for i,it in its:
            L+=[f"### {i}. {it[1]}",f"- **平台**：{it[3]} · [打开]({it[2]}) · [[#作品总表|↑回总表]]",f"- **成绩**：{it[4]}",
                f"- **他做了什么**：{it[8]}",f"- **你能借鉴的**：{it[9]}"]
            if it[10]: L.append(f"- {it[10]}")
            L.append("")
        L+=["---",""]
    L+=["## 我看完的发现",""]+[f"{n}. {f}" for n,f in enumerate(findings,1)]+["","---","",f"> {note}",""]
    open(path,"w").write("\n".join(L))
