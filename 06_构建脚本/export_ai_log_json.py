# -*- coding: utf-8 -*-
"""把 OpenCode 会话导出为 JSONL 日志（每行一条 JSON 记录）

输出：
  00_manifest.json      会话清单（id / 标题 / 模型 / 起止 / 条数 / 文件 / 哈希）
  01_主会话.jsonl       每行一个事件
  02..07_子代理*.jsonl

记录结构（单行）：
  {
    "seq": 12,                       // 会话内递增序号
    "ts":  "2026-10-28T08:26:11.123+08:00",
    "session": "ses_...",
    "parent":  "ses_..." | null,
    "role":    "user" | "assistant",
    "agent":   "build" | "general" | null,
    "model":   {"provider":"workbuddy","id":"deepseek-v4.1-flash","variant":"high"} | null,
    "parts":   [ {"type":"text","text":"..."} |
                 {"type":"tool","name":"shell","input":{...},
                  "output":"...","output_len":1234,"output_truncated":true} ],
    "tokens":  {"input":123,"output":456,"reasoning":78,"cache_read":0,"cache_write":0} | null,
    "cost":    0.00123 | null
  }
"""
import sqlite3, os, json, datetime, hashlib

DB = os.path.expanduser(r"~\.local\share\opencode\opencode.db")
ROOT = r"C:\dev\projects\software engineering\yi-yue\05_AI记录"
ROOT_ID = "ses_e8010d5bfffeXiPj9KKrtjwQwS"

FILES = {
    "A1 开题报告正文": "02_A1_开题报告正文.jsonl",
    "A2 需求建模图": "03_A2_需求建模图.jsonl",
    "A3 SRS 正文": "04_A3_SRS正文.jsonl",
    "A4 事实核验": "05_A4_事实核验.jsonl",
    "R1 开题报告对齐v2": "06_R1_开题报告修订.jsonl",
    "R2 SRS对齐v2": "07_R2_SRS修订.jsonl",
}

os.makedirs(ROOT, exist_ok=True)
c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
c.row_factory = sqlite3.Row


def iso(ms):
    dt = datetime.datetime.fromtimestamp(ms / 1000)
    return dt.isoformat(timespec="milliseconds")


def clip(s, n):
    s = s or ""
    s = s.replace("\r", "")
    return (s[:n], True, len(s)) if len(s) > n else (s, False, len(s))


def export(sid, path, max_out=400, max_text=None):
    s = c.execute("select * from session_v2 where id=?", (sid,)).fetchone()
    model_meta = None
    try:
        m = json.loads(s["model"]) if s["model"] else None
        if m:
            model_meta = {"provider": m.get("providerID"), "id": m.get("id"), "variant": m.get("variant")}
    except Exception:
        model_meta = None

    msgs = list(c.execute(
        "select * from session_message where session_id=? order by seq", (sid,)))
    n = 0
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in msgs:
            d = json.loads(r["data"])
            role = d.get("role") or ("user" if r["type"] == "user" else "assistant")

            parts = []
            content = d.get("content") or []
            if not content and d.get("text"):
                content = [{"type": "text", "text": d["text"]}]
            for p in content:
                ty = p.get("type")
                if ty == "text":
                    t = p.get("text", "")
                    t = t.replace("You are a subagent spawned by another session.\n", "", 1).strip()
                    if not t:
                        continue
                    if max_text:
                        t, tr, ln = clip(t, max_text)
                        parts.append({"type": "text", "text": t, "truncated": tr, "text_len": ln})
                    else:
                        parts.append({"type": "text", "text": t})
                elif ty == "tool":
                    st = p.get("state") or {}
                    inp = st.get("input") or {}
                    out, tr, ln = clip(str(st.get("output") or ""), max_out)
                    parts.append({
                        "type": "tool",
                        "name": p.get("name"),
                        "input": inp,
                        "output": out,
                        "output_len": ln,
                        "output_truncated": tr,
                    })
                # reasoning 不导出（模型内部推理，非沟通内容）

            if not parts:
                continue

            rec = {
                "seq": n + 1,
                "ts": iso(r["time_created"]),
                "session": sid,
                "parent": s["parent_id"],
                "role": role,
            }
            if role == "assistant":
                rec["agent"] = d.get("agent")
                rec["model"] = model_meta
            rec["parts"] = parts
            if role == "assistant":
                tk = d.get("tokens") or {}
                if tk:
                    rec["tokens"] = {k: tk.get(k, 0) for k in
                                     ("input", "output", "reasoning", "cache_read", "cache_write")}
                if d.get("cost") is not None:
                    rec["cost"] = round(d["cost"], 6)
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
            n += 1

    h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    t0, t1 = msgs[0]["time_created"], msgs[-1]["time_created"]
    return {
        "session_id": sid,
        "title": s["title"],
        "parent_id": s["parent_id"],
        "model": model_meta,
        "start": iso(t0),
        "end": iso(t1),
        "duration_min": round((t1 - t0) / 60000, 1),
        "records": n,
        "file": os.path.basename(path),
        "bytes": os.path.getsize(path),
        "sha256_16": h,
    }


manifest = {"project": "仪约 - 高校大型仪器设备开放共享预约平台",
            "exported_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "source": "OpenCode 本地会话库 opencode.db",
            "format": "JSONL（每行一条 JSON 对象，UTF-8 无 BOM）",
            "note": "reasoning（模型内部推理）不导出；工具输出超长部分已截断并标注 output_len / output_truncated。",
            "sessions": []}

manifest["sessions"].append(export(ROOT_ID, os.path.join(ROOT, "01_主会话.jsonl")))

kids = list(c.execute(
    "select * from session_v2 where parent_id=? order by time_created", (ROOT_ID,)))
for k in kids:
    fn = FILES.get(k["title"])
    if not fn:
        continue
    manifest["sessions"].append(export(k["id"], os.path.join(ROOT, fn)))

manifest["total_records"] = sum(s["records"] for s in manifest["sessions"])
with open(os.path.join(ROOT, "00_manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2)

print("导出完成")
for s in manifest["sessions"]:
    print(f'  {s["file"]:<34} {s["records"]:>3} 条  {s["bytes"]:>7} B  {s["start"][11:19]}–{s["end"][11:19]}')
print("总计", manifest["total_records"], "条记录")
