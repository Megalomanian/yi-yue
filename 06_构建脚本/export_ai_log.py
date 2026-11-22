# -*- coding: utf-8 -*-
"""导出 OpenCode 真实会话记录为可提交的 AI 沟通记录（Markdown）"""
import sqlite3, os, json, datetime

DB = os.path.expanduser(r"~\.local\share\opencode\opencode.db")
ROOT = r"C:\dev\projects\software engineering\yi-yue\05_AI记录"
ROOT_ID = "ses_e8010d5bfffeXiPj9KKrtjwQwS"

os.makedirs(ROOT, exist_ok=True)
c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
c.row_factory = sqlite3.Row


def ts(ms):
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def sess(sid):
    return c.execute("select * from session_v2 where id=?", (sid,)).fetchone()


def kids(sid):
    return list(c.execute("select * from session_v2 where parent_id=? order by time_created", (sid,)))


def clip(s, n=400):
    s = (s or "").replace("\r", "")
    s = "\n".join(ln for ln in s.split("\n") if ln.strip())
    return s if len(s) <= n else s[:n] + f"……（截断，原文 {len(s)} 字符）"


def dump(sid, fh, title, brief=False):
    s = sess(sid)
    msgs = list(c.execute("select * from session_message where session_id=? order by seq", (sid,)))
    t0 = msgs[0]["time_created"] if msgs else s["time_created"]
    t1 = msgs[-1]["time_created"] if msgs else s["time_created"]
    dur = max(1, (t1 - t0) // 60000)
    model = ""
    try:
        m = json.loads(s["model"]) if s["model"] else {}
        model = f"{m.get('providerID','')}/{m.get('id','')}"
    except Exception:
        model = str(s["model"])

    fh.write(f"# {title}\n\n")
    fh.write(f"| 项 | 内容 |\n|---|---|\n")
    fh.write(f"| 会话 ID | `{sid}` |\n")
    fh.write(f"| 会话标题 | {s['title']} |\n")
    fh.write(f"| 使用模型 | {model} |\n")
    fh.write(f"| 开始时间 | {ts(t0)} |\n")
    fh.write(f"| 结束时间 | {ts(t1)} |\n")
    fh.write(f"| 时长 | 约 {dur} 分钟 |\n")
    fh.write(f"| 消息条数 | {len(msgs)} |\n\n")
    fh.write("---\n\n")

    n_user = 0
    for r in msgs:
        d = json.loads(r["data"])
        role = d.get("role") or ("user" if r["type"] == "user" else "assistant")
        content = d.get("content") or []
        if not content and d.get("text"):
            content = [{"type": "text", "text": d["text"]}]
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        t = ts(r["time_created"])
        for part in content:
            ty = part.get("type")
            if ty == "text" and part.get("text", "").strip():
                body = part["text"].strip()
                body = body.replace("You are a subagent spawned by another session.\n", "", 1)
                if role == "user":
                    n_user += 1
                    fh.write(f"### 【人工指令 {n_user}】{t}\n\n")
                    fh.write(body + "\n\n")
                else:
                    fh.write(f"### 【AI 回复】{t}\n\n")
                    fh.write(body + "\n\n")
            elif ty == "tool" and not brief:
                name = part.get("name", "")
                st = part.get("state") or {}
                inp = st.get("input") or {}
                desc = ""
                for k in ("command", "path", "filePath", "description", "query", "prompt"):
                    if k in inp and isinstance(inp[k], str):
                        desc = f"{k}={clip(inp[k], 160)}"
                        break
                fh.write(f"> ⚙ 调用工具 `{name}`　{desc}\n\n")
                out = st.get("output") or ""
                if out:
                    fh.write("```\n" + clip(str(out), 300) + "\n```\n\n")


# ---------- 主会话 ----------
main_path = os.path.join(ROOT, "01_主会话完整记录.md")
with open(main_path, "w", encoding="utf-8") as fh:
    fh.write("# AI 沟通记录 · 主会话\n\n")
    fh.write("> 本文件由 OpenCode 本地会话数据库直接导出，未经改写，保留时间戳与工具调用轨迹。\n\n")
    dump(ROOT_ID, fh, "主会话：需求澄清与项目推进")

# ---------- 子代理 ----------
names = {
    "A1 开题报告正文": "02_子代理A1_开题报告正文.md",
    "A2 需求建模图": "03_子代理A2_需求建模图.md",
    "A3 SRS 正文": "04_子代理A3_SRS正文.md",
    "A4 事实核验": "05_子代理A4_事实核验.md",
    "R1 开题报告对齐v2": "06_子代理R1_开题报告修订.md",
    "R2 SRS对齐v2": "07_子代理R2_SRS修订.md",
}
index_rows = []
for k in kids(ROOT_ID):
    fn = names.get(k["title"])
    if not fn:
        continue
    p = os.path.join(ROOT, fn)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(f"> 本文件为子代理会话原文导出（父会话 `{ROOT_ID}`），未经改写。\n\n")
        dump(k["id"], fh, f"子代理会话：{k['title']}", brief=False)
    msgs = list(c.execute("select time_created from session_message where session_id=? order by seq", (k["id"],)))
    index_rows.append((k["title"], k["id"], ts(msgs[0]["time_created"]) if msgs else "",
                       ts(msgs[-1]["time_created"]) if msgs else "", len(msgs), fn))

with open(os.path.join(ROOT, "00_索引.md"), "w", encoding="utf-8") as fh:
    fh.write("# AI 沟通记录 · 索引\n\n")
    fh.write("本目录由 OpenCode 本地会话库导出，记录本项目全部 AI 协作过程。\n\n")
    fh.write("## 一、会话清单\n\n| 序号 | 会话 | 会话 ID | 开始 | 结束 | 消息数 | 记录文件 |\n|---|---|---|---|---|---|---|\n")
    msgs = list(c.execute("select time_created from session_message where session_id=? order by seq", (ROOT_ID,)))
    fh.write(f"| 0 | 主会话（需求澄清与推进） | `{ROOT_ID}` | {ts(msgs[0]['time_created'])} | {ts(msgs[-1]['time_created'])} | {len(msgs)} | 01_主会话完整记录.md |\n")
    for i, (t, sid, a, b, n, fn) in enumerate(index_rows, 1):
        fh.write(f"| {i} | {t} | `{sid}` | {a} | {b} | {n} | {fn} |\n")

print("done")
for r in index_rows:
    print(r[1], r[0], r[4])
