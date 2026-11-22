# -*- coding: utf-8 -*-
"""Markdown -> Word（A4 / 黑体标题 / 宋体小四正文 / 表格加框 / 自动目录 / 页眉页脚码）"""
import re, os, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = r"C:\dev\projects\software engineering\yi-yue"
PNG = os.path.join(ROOT, "04_图表", "png")

# ---------------- 图题注册表 ----------------
FIGS = {
    "图3-1": ("usecase.png", "系统用例图（13 个用例、6 类参与者）"),
    "图3-2": ("seq-01-reserve.png", "预约申请与时段冲突校验顺序图"),
    "图3-3": ("seq-02-approve.png", "预约审批与消息通知顺序图"),
    "图3-4": ("seq-03-checkin.png", "扫码上机签到与费用结算顺序图"),
    "图3-5": ("seq-04-noshow.png", "超时未签到违约处理顺序图"),
    "图3-6": ("class.png", "需求分析类图（边界类—控制类—实体类）"),
    "图3-7": ("state.png", "预约单状态图（9 个状态）"),
    "图5-1": ("ui-01-search.png", "移动端仪器检索与时段选择页"),
    "图5-2": ("ui-02-approve.png", "PC 端机组审批工作台"),
    "图5-3": ("ui-03-report.png", "PC 端开放共享绩效考核报表页"),
    "图5-4": ("ui-04-checkin.png", "移动端扫码上机签到页"),
}


def set_run_font(run, cn="宋体", en="Times New Roman", size=12, bold=None, color=None):
    run.font.name = en
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor(*color)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), cn)


def add_field(paragraph, code, placeholder=""):
    r = paragraph.add_run()
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = code
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = placeholder
    f3 = OxmlElement("w:fldChar"); f3.set(qn("w:fldCharType"), "end")
    r._r.append(f1); r._r.append(it); r._r.append(f2); r._r.append(t); r._r.append(f3)
    return r


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)


def set_cell_text(cell, text, bold=False, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    add_rich(p, text, size=size, bold=bold)


def add_rich(p, text, size=12, bold=False, cn="宋体"):
    """支持 **粗体** 与普通文本混排"""
    parts = re.split(r"(\*\*.+?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = p.add_run(part[2:-2]); set_run_font(r, cn=cn, size=size, bold=True)
        else:
            r = p.add_run(part); set_run_font(r, cn=cn, size=size, bold=bold)


def setup_styles(doc):
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.space_before = Pt(0)
    st.paragraph_format.space_after = Pt(0)

    spec = {"Heading 1": (16, "黑体"), "Heading 2": (14, "黑体"), "Heading 3": (12, "黑体")}
    for name, (sz, cn) in spec.items():
        s = doc.styles[name]
        s.font.name = "Times New Roman"
        s.font.size = Pt(sz)
        s.font.bold = True
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.element.rPr.rFonts.set(qn("w:eastAsia"), cn)
        s.paragraph_format.space_before = Pt(12 if name == "Heading 1" else 8)
        s.paragraph_format.space_after = Pt(6)
        s.paragraph_format.line_spacing = 1.5
        s.paragraph_format.keep_with_next = True


def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("— "); set_run_font(r, size=10.5)
    add_field(p, "PAGE", "1")
    r2 = p.add_run(" —"); set_run_font(r2, size=10.5)


def build_cover(doc, meta):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta["org"]); set_run_font(r, cn="黑体", size=18, bold=True)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(30)
    r = p.add_run(meta["subtitle"]); set_run_font(r, cn="黑体", size=12)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(36)
    r = p.add_run(meta["title"]); set_run_font(r, cn="黑体", size=34, bold=True)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run(meta["subtitle2"]); set_run_font(r, cn="黑体", size=16)

    for _ in range(5):
        doc.add_paragraph()

    tbl = doc.add_table(rows=0, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    for k, v in meta["cover_rows"]:
        row = tbl.add_row()
        row.cells[0].width = Cm(3.6); row.cells[1].width = Cm(11.0)
        set_cell_text(row.cells[0], k, size=12, align=WD_ALIGN_PARAGRAPH.RIGHT)
        set_cell_text(row.cells[1], v, size=12, align=WD_ALIGN_PARAGRAPH.LEFT)
        for c in row.cells:
            c.paragraphs[0].paragraph_format.space_before = Pt(5)
            c.paragraphs[0].paragraph_format.space_after = Pt(5)
            c._tc.get_or_add_tcPr()
    # 封面表格去框
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}"); el.set(qn("w:val"), "none"); borders.append(el)
    tblPr.append(borders)

    doc.add_page_break()


def build_history(doc, title):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title); set_run_font(r, cn="黑体", size=16, bold=True)
    p.paragraph_format.space_after = Pt(12)

    heads = ["序号", "变更日期", "变更人", "变更内容", "版本号"]
    widths = [1.4, 2.8, 2.2, 8.4, 2.0]
    tbl = doc.add_table(rows=1, cols=5)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(heads):
        c = tbl.rows[0].cells[i]
        c.width = Cm(widths[i])
        set_cell_text(c, h, bold=True, size=10.5)
        shade(c, "EAF1FB")
    rows = [
        ("1", "2026-10-26", "朱林立", "搭建章节框架，完成各章初稿", "V0.1"),
        ("2", "2026-10-28", "朱林立", "校订政策文件文号与术语表，统稿定稿", "V1.0"),
    ]
    for r_ in rows:
        row = tbl.add_row()
        for i, v in enumerate(r_):
            row.cells[i].width = Cm(widths[i])
            set_cell_text(row.cells[i], v, size=10.5)
    doc.add_page_break()


def build_toc(doc):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("目　　录"); set_run_font(r, cn="黑体", size=16, bold=True)
    p.paragraph_format.space_after = Pt(12)
    p2 = doc.add_paragraph()
    add_field(p2, 'TOC \\o "1-3" \\h \\z \\u', "（请在 Word 中按 Ctrl+A 后 F9 更新目录）")
    doc.add_page_break()


def add_table(doc, rows_data, kind="grid"):
    ncol = max(len(r) for r in rows_data)
    # 两列表（如用例描述表的“项/内容”）左列窄、右列宽；其余等分
    if ncol == 2:
        widths = [Cm(3.3), Cm(12.5)]
    else:
        total = 15.8
        widths = [Cm(total / ncol)] * ncol
    tbl = doc.add_table(rows=0, cols=ncol)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed")
    tbl._tbl.tblPr.append(lay)
    for ri, r in enumerate(rows_data):
        row = tbl.add_row()
        trPr = row._tr.get_or_add_trPr()
        el = OxmlElement("w:cantSplit"); el.set(qn("w:val"), "true"); trPr.append(el)
        for ci in range(ncol):
            val = r[ci] if ci < len(r) else ""
            cell = row.cells[ci]
            cell.width = widths[ci]
            if ri == 0:
                set_cell_text(cell, val, bold=True, size=10.5)
                shade(cell, "EAF1FB")
            else:
                al = WD_ALIGN_PARAGRAPH.LEFT if ci > 0 else WD_ALIGN_PARAGRAPH.CENTER
                set_cell_text(cell, val, size=10.5, align=al)
    # 表头重复
    if len(tbl.rows) > 0:
        trPr = tbl.rows[0]._tr.get_or_add_trPr()
        el = OxmlElement("w:tblHeader"); el.set(qn("w:val"), "true"); trPr.append(el)
    return tbl


def add_figure(doc, key, cap=None):
    from PIL import Image
    fname, caption = FIGS[key]
    path = os.path.join(PNG, fname)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    if os.path.exists(path):
        w, h = Image.open(path).size
        width_cm = 15.2
        max_h = 19.2                      # 单页可用高度上限（cm）
        if width_cm * h / w > max_h:      # 竖图按高度反向收敛
            width_cm = max_h * w / h
        p.add_run().add_picture(path, width=Cm(width_cm))
    else:
        r = p.add_run(f"［缺少图片文件 {fname}］"); set_run_font(r, size=10.5, color=(0xC0, 0x00, 0x00))
    cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(10)
    txt = cap if cap else f"{key}　{caption}"
    r = cp.add_run(txt); set_run_font(r, cn="宋体", size=10.5)


def parse_markdown(doc, md_text):
    lines = md_text.split("\n")
    i = 0
    tbl_buf = []

    def flush_table():
        nonlocal tbl_buf
        if not tbl_buf:
            return
        rows = []
        for ln in tbl_buf:
            if re.match(r"^\|[\s:\-\|]+\|$", ln.strip()):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows.append(cells)
        if rows:
            add_table(doc, rows)
            sp = doc.add_paragraph(); sp.paragraph_format.space_after = Pt(6)
        tbl_buf = []

    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()

        if s.startswith("|") and s.endswith("|"):
            tbl_buf.append(s)
            i += 1
            continue
        flush_table()

        if re.match(r"^[-*_]{3,}$", s):
            i += 1
            continue

        if not s:
            i += 1
            continue

        m = re.match(r"^\[\[FIG:(.+?)\]\]$", s)
        if m:
            key = m.group(1).strip()
            # 若下一非空行是图题，则消费它作为图注，避免重复出题
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            cap = None
            if j < len(lines) and re.match(r"^图\s?\d+[-－]\d+", lines[j].strip()):
                cap = lines[j].strip()
                i = j
            add_figure(doc, key, cap)
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            h = doc.add_heading(level=min(lvl, 3))
            h.paragraph_format.first_line_indent = Cm(0)
            txt = m.group(2).strip()
            r = h.add_run(txt)
            sizes = {1: 16, 2: 14, 3: 12}
            cn = "黑体"
            set_run_font(r, cn=cn, size=sizes[min(lvl, 3)], bold=True)
            i += 1
            continue

        # 表题
        if re.match(r"^表\s?\d+[-－]\d+", s) or re.match(r"^\*\*表\s?\d+", s):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            add_rich(p, s.strip("*"), size=10.5, bold=True)
            i += 1
            continue

        if re.match(r"^[-*]\s+", s):
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Cm(0.9); pf.first_line_indent = Cm(-0.35)
            pf.space_after = Pt(2)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_rich(p, "· " + re.sub(r"^[-*]\s+", "", s))
            i += 1
            continue

        if re.match(r"^\d+[\.、]\s*", s):
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Cm(1.0); pf.first_line_indent = Cm(-0.5)
            pf.space_after = Pt(2)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_rich(p, s)
            i += 1
            continue

        if s.startswith(">"):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_after = Pt(4)
            add_rich(p, s.lstrip("> "), size=10.5)
            i += 1
            continue

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(0.74)
        p.paragraph_format.space_after = Pt(3)
        add_rich(p, s)
        i += 1

    flush_table()


def build(md_path, out_path, meta, appendix=None):
    md = open(md_path, encoding="utf-8").read()
    if appendix and os.path.exists(appendix):
        md += "\n\n" + open(appendix, encoding="utf-8").read()
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0); sec.page_height = Cm(29.7)
    sec.left_margin = Cm(2.6); sec.right_margin = Cm(2.6)
    sec.top_margin = Cm(2.6); sec.bottom_margin = Cm(2.4)
    setup_styles(doc)

    # 页眉
    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = hp.add_run(meta["header"]); set_run_font(r, cn="宋体", size=9, color=(0x60, 0x60, 0x60))

    # 页码
    add_page_number_footer(sec)

    build_cover(doc, meta)
    build_history(doc, "文档变更历史记录")
    build_toc(doc)
    parse_markdown(doc, md)
    doc.save(out_path)
    print("saved", out_path)


KT = {
    "org": "宁夏大学信息工程学院",
    "subtitle": "软件工程课程设计",
    "title": "项目开题报告",
    "subtitle2": "仪约——高校大型仪器设备开放共享预约平台",
    "header": "宁夏大学信息工程学院　软件工程课程设计　　　仪约 · 项目开题报告",
    "cover_rows": [
        ("项目名称", "仪约——高校大型仪器设备开放共享预约平台"),
        ("用户单位", "宁夏大学测试分析中心"),
        ("开发单位", "宁夏大学信息工程学院　软件工程课程设计第 3 组"),
        ("指导教师", "曾升"),
        ("组长", "朱林立"),
        ("组员", "张雨欣　张义　秦嘉玉　孙福泽　许军"),
        ("小组人数", "6 人"),
        ("完成日期", "2026 年 10 月 28 日"),
    ],
}

SRS = {
    "org": "宁夏大学信息工程学院",
    "subtitle": "软件工程课程设计",
    "title": "软件需求规格说明书",
    "subtitle2": "仪约——高校大型仪器设备开放共享预约平台",
    "header": "宁夏大学信息工程学院　软件工程课程设计　　　仪约 · 软件需求规格说明书",
    "cover_rows": [
        ("文档编号", "IY-SRS-1.0"),
        ("项目名称", "仪约——高校大型仪器设备开放共享预约平台"),
        ("用户单位", "宁夏大学测试分析中心"),
        ("开发单位", "宁夏大学信息工程学院　软件工程课程设计第 3 组"),
        ("指导教师", "曾升"),
        ("编写小组", "朱林立（组长）　张雨欣　张义　秦嘉玉　孙福泽　许军"),
        ("文档版本", "V1.0"),
        ("密　　级", "内部"),
        ("完成日期", "2026 年 10 月 28 日"),
    ],
}

if __name__ == "__main__":
    build(os.path.join(ROOT, "01_开题报告", "开题报告-正文.md"),
          os.path.join(ROOT, "01_开题报告", "项目开题报告.docx"), KT)
    build(os.path.join(ROOT, "03_SRS", "SRS-正文.md"),
          os.path.join(ROOT, "03_SRS", "软件需求规格说明书.docx"), SRS)


