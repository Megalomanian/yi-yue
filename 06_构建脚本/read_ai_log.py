# -*- coding: utf-8 -*-
"""把 JSONL 日志还原成可读文本，方便老师或自己核对。

用法：
  python 06_构建脚本/read_ai_log.py            列出全部会话
  python 06_构建脚本/read_ai_log.py 01         打印主会话
  python 06_构建脚本/read_ai_log.py 01 --tools 连工具调用一起打印
  python 06_构建脚本/read_ai_log.py 01 --out 记录.txt   另存为文本
"""
import sys, os, json, glob

ROOT = r"C:\dev\projects\software engineering\yi-yue\05_AI记录"


def load(fn):
    with open(fn, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show_tools = "--tools" in sys.argv
    out_path = None
    if "--out" in sys.argv:
        i = sys.argv.index("--out")
        if i + 1 < len(sys.argv):
            out_path = sys.argv[i + 1]

    files = sorted(glob.glob(os.path.join(ROOT, "0[1-7]_*.jsonl")))
    man = {}
    mp = os.path.join(ROOT, "00_manifest.json")
    if os.path.exists(mp):
        man = {s["file"]: s for s in json.load(open(mp, encoding="utf-8"))["sessions"]}

    if not args:
        print(f"{'序号':<4}{'文件':<34}{'记录数':>6}   起止时间")
        for f in files:
            b = os.path.basename(f)
            m = man.get(b, {})
            recs = sum(1 for _ in open(f, encoding="utf-8"))
            print(f"{b[:2]:<4}{b:<34}{recs:>6}   {m.get('start','')[11:19]}–{m.get('end','')[11:19]}  {m.get('title','')}")
        return

    key = args[0].zfill(2)
    target = next((f for f in files if os.path.basename(f).startswith(key)), None)
    if not target:
        print("找不到序号为", key, "的记录文件")
        return

    lines = []
    b = os.path.basename(target)
    m = man.get(b, {})
    lines.append(f"# {m.get('title', b)}")
    lines.append(f"# 会话 {m.get('session_id','')}  模型 {m.get('model',{})}  "
                 f"{m.get('start','')} → {m.get('end','')}  共 {m.get('records','?')} 条")
    lines.append("")

    n_user = 0
    for rec in load(target):
        head = f"[{rec['ts'][11:23]}] "
        if rec["role"] == "user":
            n_user += 1
            lines.append(f"{head}=== 人工指令 {n_user} ===")
        else:
            lines.append(f"{head}--- AI 回复（{rec.get('agent')}）---")
        for p in rec["parts"]:
            if p["type"] == "text":
                lines.append(p["text"])
            elif p["type"] == "tool" and show_tools:
                inp = json.dumps(p.get("input", {}), ensure_ascii=False)
                if len(inp) > 200:
                    inp = inp[:200] + "…"
                lines.append(f"  ⚙ {p['name']}  {inp}")
                if p.get("output"):
                    first = p["output"].split("\n")[0][:160]
                    lines.append(f"    → {first}")
        lines.append("")

    text = "\n".join(lines)
    if out_path:
        open(out_path, "w", encoding="utf-8").write(text)
        print("已写入", out_path, len(text), "字符")
    else:
        print(text)


if __name__ == "__main__":
    main()
