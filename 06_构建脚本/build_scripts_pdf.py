# -*- coding: utf-8 -*-
"""把 09_答辩稿 下的 Markdown 批量转换成 Word（A4 / 黑体标题 / 宋体正文 / 页眉页码）"""
import os, sys, glob, re

ROOT = r"C:\dev\projects\software engineering\yi-yue"
sys.path.insert(0, os.path.join(ROOT, "06_构建脚本"))
import md2docx as M  # 复用解析器与样式

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = os.path.join(ROOT, "09_答辩稿")
OUT = os.path.join(SRC, "docx")
os.makedirs(OUT, exist_ok=True)


def build_one(md_path):
    text = open(md_path, encoding="utf-8").read()
    lines = text.split("\n")
    # 取第一行 # 标题
    title = ""
    body_start = 0
    for i, ln in enumerate(lines):
        if ln.strip().startswith("# "):
            title = ln.strip()[2:].strip()
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:])

    who = title.split("·")[0].strip() if "·" in title else ""
    if "总答辩稿" in title:
        who = "全组（主讲：朱林立）"

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.top_margin = Cm(2.4)
    sec.bottom_margin = Cm(2.2)
    M.setup_styles(doc)

    # 页眉
    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = hp.add_run("宁夏大学信息工程学院　软件工程课程设计第 3 组　　仪约")
    M.set_run_font(r, cn="宋体", size=9, color=(0x70, 0x70, 0x70))

    # 页码
    M.add_page_number_footer(sec)

    # 标题块
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(title)
    M.set_run_font(r, cn="黑体", size=22, bold=True)

    if who:
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after = Pt(2)
        r = p2.add_run(f"答辩人：{who}　　项目：仪约——高校大型仪器设备开放共享预约平台")
        M.set_run_font(r, cn="宋体", size=10.5, color=(0x50, 0x50, 0x50))

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_after = Pt(14)
    r = p3.add_run("2026 年 11 月")
    M.set_run_font(r, cn="宋体", size=10.5, color=(0x50, 0x50, 0x50))

    # 分隔线
    pr = p3._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "6"); bottom.set(qn("w:color"), "1F6FEB")
    bd.append(bottom); pr.append(bd)

    M.parse_markdown(doc, body)

    name = os.path.splitext(os.path.basename(md_path))[0] + ".docx"
    out = os.path.join(OUT, name)
    doc.save(out)
    return out


if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(SRC, "*.md")))
    for f in files:
        o = build_one(f)
        print("saved", os.path.basename(o))
    print("共", len(files), "份")
