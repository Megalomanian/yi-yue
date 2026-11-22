# -*- coding: utf-8 -*-
"""撤销问卷与一手调研承诺：删除附录、清理相关表述"""
import os, re
R = r"C:\dev\projects\software engineering\yi-yue"
KT = os.path.join(R, "01_开题报告", "开题报告-正文.md")
SRS = os.path.join(R, "03_SRS", "SRS-正文.md")
MD = os.path.join(R, "06_构建脚本", "md2docx.py")

t = open(KT, encoding="utf-8").read()
P = [
("与其如此，不如把可以核查的二手资料做扎实，再把一手访谈放到 M2 阶段与需求评审合并进行，用访谈去校准而不是重新发现需求。",
 "与其如此，不如把可以核查的二手资料做扎实，用资料之间的交叉印证来代替一次覆盖不足的调研。"),

("针对以上三点，M2 阶段计划安排 3 至 5 次机组访谈与一次小样本问卷（问卷全文见附录 A，共 23 题，题目与需求条目的对应关系附在问卷末尾），目的不是重新做一遍需求发现，而是校准三件事：痛点排序是否与机组老师的实际感受一致、结算环节的字段是否与实际台账对得上、移动端的使用场景是否真实存在。若访谈结论与本文冲突，以访谈为准，并按 SRS 的变更历史表登记修订。这一安排写入 4.2 的 M2 阶段说明，作为需求阶段的收尾任务。",
 "针对以上三点，M2 阶段不安排大规模的一手调研，而以两种方式校准：一是持续更新竞品资料与政策文件，特别是考核细则指标口径的变化；二是在需求评审中引入外部视角，请指导教师与有仪器使用经验的同学校对痛点排序、结算字段与移动端使用场景是否成立，提出的问题按 SRS 的变更历史表逐条登记并给出处理结论。若后续取得一手数据，以一手数据为准并修订相关段落。这一安排写入开题报告 4.2 的 M2 阶段说明。"),
]
for a, b in P:
    if t.count(a) != 1:
        print("!! 未命中：", a[:28], t.count(a))
    t = t.replace(a, b)
open(KT, "w", encoding="utf-8").write(t)

s = open(SRS, encoding="utf-8").read()
Q = [
("需要说明的是，本阶段未开展一手访谈与问卷，结论来自二手资料与竞品对照；一手访谈安排在 M2 阶段与需求评审合并进行，用于校准痛点排序与字段设置，具体安排见开题报告 2.1.6。",
 "需要说明的是，本阶段未开展一手调研，结论来自二手资料与竞品对照，并在需求评审中由指导教师与有仪器使用经验的同学校准，具体安排见开题报告 2.1.6。"),
("前两周做机组访谈与用例细化（访谈安排见开题报告 2.1.6）",
 "前两周做用例细化与需求补充（资料来源与校准方式见开题报告 2.1.6）"),
]
for a, b in Q:
    if s.count(a) != 1:
        print("!! SRS 未命中：", a[:28], s.count(a))
    s = s.replace(a, b)
open(SRS, "w", encoding="utf-8").write(s)

m = open(MD, encoding="utf-8").read()
m = m.replace('''          os.path.join(ROOT, "01_开题报告", "项目开题报告.docx"), KT,
          appendix=os.path.join(ROOT, "01_开题报告", "附录A-调查问卷.md"))''',
              '''          os.path.join(ROOT, "01_开题报告", "项目开题报告.docx"), KT)''')
open(MD, "w", encoding="utf-8").write(m)

for f in [os.path.join(R, "01_开题报告", "附录A-调查问卷.md"),
          os.path.join(R, "00_事实源", "问卷数据模板.csv"),
          os.path.join(R, "06_构建脚本", "analyze_survey.py")]:
    if os.path.exists(f):
        os.remove(f)
        print("已删除", os.path.basename(f))
print("完成")
