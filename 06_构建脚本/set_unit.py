# -*- coding: utf-8 -*-
"""用户单位改为宁夏大学测试分析中心"""
import os
R = r"C:\dev\projects\software engineering\yi-yue"
SRS = os.path.join(R, "03_SRS", "SRS-正文.md")
CARD = os.path.join(R, "00_事实源", "project-card.md")
CHK = os.path.join(R, "00_事实源", "待人工核实清单.md")
MD = os.path.join(R, "06_构建脚本", "md2docx.py")
QA = os.path.join(R, "06_构建脚本", "qa.py")

s = open(SRS, encoding="utf-8").read()
a = "把某高校资产与实验室管理处、测试分析中心以及六个学院机组在实际工作中提出的预约、审批、上机、结算、考核等业务诉求"
b = "把宁夏大学测试分析中心及校内各学院共用机组在预约、审批、上机、结算、考核等环节的业务诉求"
assert s.count(a) == 1
s = s.replace(a, b)

a2 = "用户单位为某高校资产与实验室管理处、测试分析中心，业务归口部门是资产与实验室管理处，日常运行由测试分析中心及各学院机组承担。"
b2 = "用户单位为宁夏大学测试分析中心，业务归口部门为学校资产与实验室管理处，日常运行由中心各机组与校内各学院共用机组分别承担。"
assert s.count(a2) == 1
s = s.replace(a2, b2)
open(SRS, "w", encoding="utf-8").write(s)
print("SRS 已改")

c = open(CARD, encoding="utf-8").read()
c = c.replace("| 用户单位 | 某高校资产与实验室管理处、测试分析中心 |",
              "| 用户单位 | 宁夏大学测试分析中心（归口：学校资产与实验室管理处） |")
c = c.replace('> 允许的表述："某高校""校内""我校""学校"。',
              '> 允许的表述："校内""学校"。真实校名只允许出现在两处：署名（宁夏大学信息工程学院）与用户单位（宁夏大学测试分析中心）。')
c = c.replace('2. **绝不出现真实校名/地名/机构专名**，统一"某高校""校内""测试分析中心"。',
              '2. **真实校名只允许出现在署名与用户单位两处**，其余一律写"校内""测试分析中心"；不得写"某高校"。')
c = c.replace('> v2.0 变更：**全文不出现任何真实校名**，统一称"某高校"；',
              '> v2.0 变更：真实校名仅用于署名与用户单位；')
open(CARD, "w", encoding="utf-8").write(c)
print("事实卡已改")

m = open(MD, encoding="utf-8").read()
m = m.replace('("用户单位", "某高校资产与实验室管理处、测试分析中心"),',
              '("用户单位", "宁夏大学测试分析中心"),')
open(MD, "w", encoding="utf-8").write(m)
print("封面配置已改")

q = open(QA, encoding="utf-8").read()
q = q.replace('nx_bad = [l for l in nx if "信息工程学院" not in l]',
              'nx_bad = [l for l in nx if ("信息工程学院" not in l and "测试分析中心" not in l)]')
q = q.replace('校名越界使用（仅允许出现在「宁夏大学信息工程学院」署名处）',
              '校名越界使用（仅允许出现在署名与用户单位两处）')
open(QA, "w", encoding="utf-8").write(q)
print("自检规则已改")
