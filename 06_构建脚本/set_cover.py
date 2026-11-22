# -*- coding: utf-8 -*-
"""更新封面配置、变更历史、PPT 署名与分工"""
import os
R = r"C:\dev\projects\software engineering\yi-yue"
P1 = os.path.join(R, "06_构建脚本", "md2docx.py")
P2 = os.path.join(R, "06_构建脚本", "build_ppt.py")

# ---------------- md2docx ----------------
t = open(P1, encoding="utf-8").read()

old_hist = '''    rows = [
        ("1", "2026-10-26", "成员A", "创建文档，搭建章节框架", "V0.1"),
        ("2", "2026-10-27", "成员B", "补充需求调研数据与用例清单", "V0.5"),
        ("3", "2026-10-28", "成员F", "按核验结果校订政策文号与术语表", "V0.9"),
        ("4", "2026-10-28", "成员A", "组内评审后定稿，冻结一期范围", "V1.0"),
    ]
    for r_ in rows:
        row = tbl.add_row()
        for i, v in enumerate(r_):
            row.cells[i].width = Cm(widths[i])
            set_cell_text(row.cells[i], v, size=10.5)
    for _ in range(6):
        row = tbl.add_row()
        for i in range(5):
            row.cells[i].width = Cm(widths[i])
            set_cell_text(row.cells[i], "", size=10.5)'''
new_hist = '''    rows = [
        ("1", "2026-10-26", "朱林立", "搭建章节框架，完成各章初稿", "V0.1"),
        ("2", "2026-10-28", "朱林立", "校订政策文件文号与术语表，统稿定稿", "V1.0"),
    ]
    for r_ in rows:
        row = tbl.add_row()
        for i, v in enumerate(r_):
            row.cells[i].width = Cm(widths[i])
            set_cell_text(row.cells[i], v, size=10.5)'''
assert t.count(old_hist) == 1
t = t.replace(old_hist, new_hist)

old_kt = t[t.index('KT = {'):t.index('SRS = {')]
new_kt = '''KT = {
    "org": "宁夏大学信息工程学院",
    "subtitle": "软件工程课程设计",
    "title": "项目开题报告",
    "subtitle2": "仪约——高校大型仪器设备开放共享预约平台",
    "header": "宁夏大学信息工程学院　软件工程课程设计　　　仪约 · 项目开题报告",
    "cover_rows": [
        ("项目名称", "仪约——高校大型仪器设备开放共享预约平台"),
        ("用户单位", "某高校资产与实验室管理处、测试分析中心"),
        ("开发单位", "宁夏大学信息工程学院　软件工程课程设计第 3 组"),
        ("指导教师", "曾升"),
        ("组长", "朱林立"),
        ("组员", "张雨欣　张义　秦嘉玉　孙福泽　许军"),
        ("小组人数", "6 人"),
        ("完成日期", "2026 年 10 月 28 日"),
    ],
}

'''
t = t.replace(old_kt, new_kt)

old_srs = t[t.index('SRS = {'):t.index('if __name__ == "__main__":')]
new_srs = '''SRS = {
    "org": "宁夏大学信息工程学院",
    "subtitle": "软件工程课程设计",
    "title": "软件需求规格说明书",
    "subtitle2": "仪约——高校大型仪器设备开放共享预约平台",
    "header": "宁夏大学信息工程学院　软件工程课程设计　　　仪约 · 软件需求规格说明书",
    "cover_rows": [
        ("文档编号", "IY-SRS-1.0"),
        ("项目名称", "仪约——高校大型仪器设备开放共享预约平台"),
        ("用户单位", "某高校资产与实验室管理处、测试分析中心"),
        ("开发单位", "宁夏大学信息工程学院　软件工程课程设计第 3 组"),
        ("指导教师", "曾升"),
        ("编写小组", "朱林立（组长）　张雨欣　张义　秦嘉玉　孙福泽　许军"),
        ("文档版本", "V1.0"),
        ("密　　级", "内部"),
        ("完成日期", "2026 年 10 月 28 日"),
    ],
}

'''
t = t.replace(old_srs, new_srs)
open(P1, "w", encoding="utf-8").write(t)
print("md2docx 已更新")

# ---------------- build_ppt ----------------
p = open(P2, encoding="utf-8").read()
old_cover = '''tb(s, 1.1, 1.45, 11, 0.4, "软件工程课程设计 · 开题答辩", 20, False, RGBColor(0x8A, 0xB4, 0xF8), body=False)'''
new_cover = '''tb(s, 1.1, 1.45, 11, 0.4, "宁夏大学信息工程学院 · 软件工程课程设计 · 开题答辩", 20, False, RGBColor(0x8A, 0xB4, 0xF8), body=False)'''
assert p.count(old_cover) == 1
p = p.replace(old_cover, new_cover)

old_names = '''tb(s, 1.1, 4.7, 11, 1.1, "第 3 组　|　成员A B C D E F\\n2026 年 11 月 2 日", 20, False,
   RGBColor(0xC6, 0xCF, 0xDC), spacing=1.7, body=False)'''
new_names = '''tb(s, 1.1, 4.62, 11.2, 1.2,
   "第 3 组　组长：朱林立　组员：张雨欣　张义　秦嘉玉　孙福泽　许军\\n指导教师：曾升　　2026 年 11 月 2 日", 18, False,
   RGBColor(0xC6, 0xCF, 0xDC), spacing=1.75, body=False)'''
assert p.count(old_names) == 1
p = p.replace(old_names, new_names)

old_roles = '''roles = [("成员A", "组长：计划与评审主持"), ("成员B", "需求：访谈与用例建模"),
         ("成员C", "架构与前端：原型"), ("成员D", "后端：并发与结算"),
         ("成员E", "测试：压测与部署"), ("成员F", "文档与答辩材料")]'''
new_roles = '''roles = [("朱林立", "统筹、需求建模、后端核心"), ("张雨欣", "前端：移动端小程序"),
         ("张义", "前端：PC 端与原型"), ("秦嘉玉", "后端：业务接口与数据"),
         ("孙福泽", "测试：用例与并发压测"), ("许军", "部署与文档答辩")]'''
assert p.count(old_roles) == 1
p = p.replace(old_roles, new_roles)

p = p.replace('tb(s, x + 0.3, y + 0.16, 1.4, 0.45, m, 22, True, BLUE)\n    tb(s, x + 1.75, y + 0.2, 3.6, 0.8, r, 20, False, DARK)',
              'tb(s, x + 0.28, y + 0.16, 1.55, 0.45, m, 22, True, BLUE)\n    tb(s, x + 1.90, y + 0.2, 3.50, 0.8, r, 20, False, DARK)')
p = p.replace('s = new("04 进度与成果", "6 人分工，每人一条主线", 14)', 's = new("04 进度与成果", "6 人分工，组长承担主线", 14)')
open(P2, "w", encoding="utf-8").write(p)
print("build_ppt 已更新")
