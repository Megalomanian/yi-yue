# -*- coding: utf-8 -*-
"""校验 JSONL、清理旧 md 记录、重排编号"""
import os, json, shutil

ROOT = r"C:\dev\projects\software engineering\yi-yue\05_AI记录"

# ---------- 1 校验 ----------
bad = 0
for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith(".jsonl"):
        continue
    n = 0
    with open(os.path.join(ROOT, fn), encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
                n += 1
            except Exception as e:
                bad += 1
                print("!! 非法行", fn, i, e)
    print(f"  {fn:<34} {n} 行 校验通过")
print("非法行总数：", bad)

# ---------- 2 清理旧文件 ----------
OLD = ["01_主会话完整记录.md", "02_子代理A1_开题报告正文.md", "03_子代理A2_需求建模图.md",
       "04_子代理A3_SRS正文.md", "05_子代理A4_事实核验.md", "06_子代理R1_开题报告修订.md",
       "07_子代理R2_SRS修订.md"]
for f in OLD:
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        os.remove(p)
        print("删除", f)

# ---------- 3 重排编号 ----------
for old, new in [("02_关键决策点.md", "08_关键决策点.md"), ("03_截图清单.md", "09_截图清单.md")]:
    a, b = os.path.join(ROOT, old), os.path.join(ROOT, new)
    if os.path.exists(a):
        os.replace(a, b)
        print(f"{old} -> {new}")
