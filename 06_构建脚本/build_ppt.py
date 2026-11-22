# -*- coding: utf-8 -*-
"""开题答辩 PPT（16:9，15 页）
硬约束：每页正文文字 ≤6 行；正文 ≥20pt；图表优先；细节全部放入演讲备注。
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn as _qn
from lxml import etree
from PIL import Image

ROOT = r"C:\dev\projects\software engineering\yi-yue"
PNG = os.path.join(ROOT, "04_图表", "png")
OUT = os.path.join(ROOT, "02_答辩PPT", "开题答辩.pptx")

DARK = RGBColor(0x1B, 0x2A, 0x41)
BLUE = RGBColor(0x1F, 0x6F, 0xEB)
LIGHT = RGBColor(0xEA, 0xF1, 0xFB)
GRAY = RGBColor(0x5F, 0x63, 0x68)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x1E, 0x8E, 0x3E)
ORANGE = RGBColor(0xB0, 0x60, 0x00)
SOFT = RGBColor(0xF7, 0xF9, 0xFC)
LINE = RGBColor(0xE1, 0xE6, 0xEE)
FONT = "微软雅黑"
W, H = 13.333, 7.5

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]

STATS = []          # 每页正文段落数
BODY_MIN = []       # 每页正文最小字号


def set_bg(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def tb(slide, x, y, w, h, text, size=20, bold=False, color=DARK,
       align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.25, body=True):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color; r.font.name = FONT
    if body:
        _acc(size, text.count("\n") + 1)
    return box


_cur = {"lines": 0, "min": 99}


def _acc(size, n):
    _cur["lines"] += n
    _cur["min"] = min(_cur["min"], size)


def rect(slide, x, y, w, h, color, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color
    if line:
        s.line.color.rgb = line; s.line.width = Pt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            s.adjustments[0] = radius
        except Exception:
            pass
    return s


def page_head(slide, kicker, title):
    rect(slide, 0, 0, 0.18, H, BLUE, shape=MSO_SHAPE.RECTANGLE)
    tb(slide, 0.75, 0.42, 11.8, 0.4, kicker, 15, False, BLUE, body=False)
    tb(slide, 0.75, 0.78, 11.9, 0.8, title, 32, True, DARK, body=False)
    rect(slide, 0.75, 1.62, 1.4, 0.05, BLUE, shape=MSO_SHAPE.RECTANGLE)


def new(kicker, title, n, total=15):
    s = prs.slides.add_slide(BLANK)
    set_bg(s, WHITE)
    page_head(s, kicker, title)
    tb(s, 11.9, 7.0, 1.1, 0.3, f"{n} / {total}", 12, False, GRAY, PP_ALIGN.RIGHT, body=False)
    return s


def close(s, n):
    STATS.append((n, _cur["lines"]))
    BODY_MIN.append((n, _cur["min"] if _cur["min"] != 99 else 20))
    _cur["lines"] = 0
    _cur["min"] = 99


def pic_fit(slide, name, x, y, maxw, maxh):
    p = os.path.join(PNG, name)
    w, h = Image.open(p).size
    sc = min(maxw * 96 / w, maxh * 96 / h)
    return slide.shapes.add_picture(p, Inches(x), Inches(y),
                                    width=Emu(int(w * sc * 9525)), height=Emu(int(h * sc * 9525)))


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def arrow(slide, x1, y1, x2, y2, dashed=False, color=BLUE):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(1.6)
    ln = c.line._get_or_add_ln()
    if dashed:
        etree.SubElement(ln, _qn("a:prstDash")).set("val", "dash")
    te = etree.SubElement(ln, _qn("a:tailEnd"))
    te.set("type", "triangle"); te.set("w", "med"); te.set("len", "med")
    return c


# ===================== 1 封面 =====================
s = prs.slides.add_slide(BLANK)
set_bg(s, DARK)
rect(s, 0, 0, 0.22, H, BLUE, shape=MSO_SHAPE.RECTANGLE)
tb(s, 1.1, 1.45, 11, 0.4, "宁夏大学信息工程学院 · 软件工程课程设计 · 开题答辩", 20, False, RGBColor(0x8A, 0xB4, 0xF8), body=False)
tb(s, 1.1, 2.05, 11, 1.4, "仪约", 72, True, WHITE, body=False)
tb(s, 1.1, 3.35, 11, 0.6, "高校大型仪器设备开放共享预约平台", 32, False, WHITE, body=False)
rect(s, 1.1, 4.35, 2.2, 0.06, BLUE, shape=MSO_SHAPE.RECTANGLE)
tb(s, 1.1, 4.62, 11.2, 1.2,
   "第 3 组　组长：朱林立　组员：张雨欣　张义　秦嘉玉　孙福泽　许军\n指导教师：曾升　　2026 年 11 月 2 日", 18, False,
   RGBColor(0xC6, 0xCF, 0xDC), spacing=1.75, body=False)
STATS.append((1, 4)); BODY_MIN.append((1, 20))
notes(s, "开场 30 秒：各位老师上午好，我们是第 3 组，题目是「仪约」——高校大型仪器设备开放共享预约平台。"
         "选题来自我们自己在测样排队时的一次次等待。")

# ===================== 2 目录 =====================
s = new("CONTENTS", "汇报提纲", 2)
items = ["01　项目背景与意义", "02　软件需求获取", "03　软件需求分析", "04　进度计划与预期成果"]
for i, t in enumerate(items):
    y = 2.15 + i * 1.15
    rect(s, 0.9, y, 11.5, 0.95, SOFT, LINE)
    rect(s, 0.9, y, 0.09, 0.95, BLUE, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 1.35, y + 0.2, 10.6, 0.55, t, 26, i == 0, DARK)
close(s, 2)
notes(s, "四个部分：为什么做、需求怎么来的、需求怎么表达的、多久做完。请重点看第三部分。")

# ===================== 3 背景 =====================
s = new("01 项目背景", "一台仪器，三种互不相通的记录", 3)
cards = [("排机", "谁先谁后，只能翻聊天记录", BLUE),
         ("台账", "同一时段被两人约到，只能现场协调", BLUE),
         ("结算与考核", "月底手算，年终翻本子统计", BLUE)]
for i, (t, d, c) in enumerate(cards):
    x = 0.9 + i * 3.95
    rect(s, x, 2.0, 3.65, 2.9, SOFT, LINE)
    rect(s, x, 2.0, 3.65, 0.13, c, shape=MSO_SHAPE.RECTANGLE)
    tb(s, x + 0.32, 2.35, 3.0, 0.5, t, 26, True, BLUE)
    tb(s, x + 0.32, 3.05, 3.0, 1.6, d, 21, False, DARK, spacing=1.5)
tb(s, 0.9, 5.35, 11.6, 1.2,
   "2026 年 9 月 25 日走访电镜机组时，负责老师说：\n「两分钟里七个人回复，谁先谁后我得往上翻聊天记录。」", 20, False, GRAY, spacing=1.5)
tb(s, 0.9, 6.6, 11.6, 0.5, "缺的不是设备，是一个把预约、上机、计费、统计串起来的载体。", 22, True, ORANGE)
close(s, 3)
notes(s, "痛点三条：排机顺序不可考、台账各自为政、结算与考核全靠人工。"
         "这句原话是真实访谈记录，评委如果追问可以展开讲当时七个人抢三个小时的场面。")

# ===================== 4 政策 =====================
s = new("01 项目背景", "政策已从倡导变为可考核的制度", 4)
tl = [("2014", "国发〔2014〕70 号：50 万元以上仪器纳入国家网络管理平台"),
      ("2017", "国科发基〔2017〕289 号：开放共享管理办法，明确入网与报送"),
      ("2026", "评价考核实施细则：3 个一级指标、9 个二级指标、四档结果"),
      ("本校", "不参加中央级考核，但参照指标开展校内自查")]
y0 = 2.0
for i, (yr, txt) in enumerate(tl):
    y = y0 + i * 1.15
    rect(s, 0.9, y, 1.55, 0.9, LIGHT, BLUE)
    tb(s, 0.9, y + 0.19, 1.55, 0.5, yr, 23, True, BLUE, PP_ALIGN.CENTER)
    rect(s, 2.55, y, 9.9, 0.9, SOFT, LINE)
    tb(s, 2.85, y + 0.19, 9.4, 0.55, txt, 20, False, DARK)
tb(s, 0.9, 6.55, 11.6, 0.5, "结论：平时不沉淀数据，年终就补不出账。", 22, True, ORANGE)
close(s, 4)
notes(s, "特别说明：中央级考核不覆盖地方高校，这一点我们核对过原文，所以写的是「参照指标自查」，"
         "避免答辩时被问住。政策文号全部逐条核过官网。")

# ===================== 5 需求获取 =====================
s = new("02 需求获取", "四种方法交叉验证", 5)
meth = [("深度访谈", "3 位机组老师、2 位管理人员，每人 60–90 分钟"),
        ("问卷调查", "发放 68 份，有效 61 份，两轮修订"),
        ("竞品体验", "4 款同类系统，逐条对比功能覆盖"),
        ("现场观察", "跟完一次排机—上机—结算全流程")]
for i, (t, d) in enumerate(meth):
    x = 0.9 + (i % 2) * 5.85
    y = 2.0 + (i // 2) * 1.95
    rect(s, x, y, 5.55, 1.65, SOFT, LINE)
    rect(s, x, y, 0.09, 1.65, BLUE, shape=MSO_SHAPE.RECTANGLE)
    tb(s, x + 0.35, y + 0.22, 4.9, 0.5, t, 24, True, BLUE)
    tb(s, x + 0.35, y + 0.82, 4.9, 0.75, d, 20, False, DARK)
tb(s, 0.9, 6.1, 11.6, 0.8, "首轮问卷漏问收费口径，补访 5 位老师后修订 —— 这一轮返工避免了计费规则返工。",
   20, False, GRAY)
close(s, 5)
notes(s, "强调方法交叉：访谈给场景，问卷给比例，竞品给边界，观察给细节。"
         "首轮问卷返工是我们自己踩的坑，讲出来比讲完美更可信。")

# ===================== 6 收敛 =====================
s = new("02 需求获取", "七个现象，收敛成三类问题", 6)
groups = [("约定不可信", "抢楼顺序不可复现、时段冲突无校验、爽约无成本", BLUE),
          ("成本不可算", "结算靠手算、资质授权链不完整", GREEN),
          ("数据不可用", "考核数据靠人工汇总、多口径统计困难", ORANGE)]
for i, (t, d, c) in enumerate(groups):
    y = 2.0 + i * 1.45
    rect(s, 0.9, y, 11.55, 1.25, SOFT, c)
    rect(s, 0.9, y, 0.09, 1.25, c, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 1.3, y + 0.14, 3.2, 0.5, t, 24, True, c)
    tb(s, 4.5, y + 0.2, 7.8, 0.9, d, 20, False, DARK)
tb(s, 0.9, 6.45, 11.6, 0.5, "13 个用例逐条对应这三类问题，不做功能堆砌。", 22, True, DARK)
close(s, 6)
notes(s, "七个现象是访谈和问卷里反复出现的，合并成三类问题：约定、成本、数据。"
         "后面的 13 个用例就是按这三条线展开的。")

# ===================== 7 用例图 =====================
s = new("03 需求分析", "6 类参与者，13 个用例", 7)
pic_fit(s, "usecase.png", 0.35, 1.72, 9.3, 5.15)
tb(s, 9.85, 1.95, 3.2, 0.4, "参与者", 20, True, BLUE)
tb(s, 9.85, 2.5, 3.2, 3.6,
   "AC-01　送样人\nAC-02　仪器负责人\nAC-03　平台管理员\nAC-04　主管部门\nAC-05　校外用户\nAC-06　定时任务",
   20, False, DARK, spacing=1.5)
tb(s, 0.9, 7.05, 6, 0.3, "图 3-1　系统用例图", 12, False, GRAY, body=False)
close(s, 7)
notes(s, "重点讲三条：UC-02 包含 UC-04（提交必做冲突校验）；UC-08 是 UC-02 的前置条件而非包含关系；"
         "UC-12 被五个用例包含，是贯穿性的。")

# ===================== 8 顺序图 =====================
s = new("03 需求分析", "一次预约要过三道校验", 8)
lanes = [("送样人", 2.0), ("小程序端", 5.0), ("预约服务", 8.0), ("MySQL / Redis", 11.3)]
for name, cx in lanes:
    rect(s, cx - 1.0, 1.78, 2.0, 0.5, LIGHT, BLUE)
    tb(s, cx - 1.0, 1.87, 2.0, 0.35, name, 14, True, BLUE, PP_ALIGN.CENTER, body=False)
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(cx), Inches(2.28), Inches(cx), Inches(5.85))
    c.line.color.rgb = RGBColor(0xC5, 0xCC, 0xD6); c.line.width = Pt(1.2)
steps = [(2.72, 0, 1, "① 选仪器、选时段，填样品数与经费卡", False, BLUE),
         (3.36, 1, 2, "② 提交预约申请", False, BLUE),
         (4.00, 2, 3, "③ 校验上机资质与信用分（≥60）", False, DARK),
         (4.64, 3, 2, "④ 资质有效 / 信用分不足", True, DARK),
         (5.28, 2, 3, "⑤ 加锁 → 唯一性校验 → 写单", False, ORANGE),
         (5.92, 2, 1, "⑥ 返回预约单号，状态「待审批」", True, GREEN)]
for y, a, b, label, dashed, col in steps:
    x1, x2 = lanes[a][1], lanes[b][1]
    arrow(s, x1, y, x2, y, dashed=dashed, color=col)
    tb(s, (x1 + x2) / 2 - 2.3, y - 0.34, 4.6, 0.3, label, 15, False, col, PP_ALIGN.CENTER, body=False)
rect(s, 0.9, 6.35, 11.6, 0.62, RGBColor(0xFF, 0xF6, 0xE6), ORANGE)
tb(s, 1.15, 6.45, 11.1, 0.42, "任一步失败：提示原因并停留在填写页；时段已满转入候补队列", 20, True, ORANGE)
tb(s, 0.9, 7.05, 8, 0.3, "图 3-2　预约申请与冲突校验顺序图（简化）", 12, False, GRAY, body=False)
close(s, 8)
notes(s, "顺序图只画主成功场景。异常分支在 SRS 的 3.3 节有完整说明，包括资质过期、"
         "仪器停用、二维码损坏、重复扫码四种情况。")

# ===================== 9 三重锁 =====================
s = new("03 需求分析", "同一时段绝不超卖：三层保障", 9)
lock = [("①　数据库唯一约束", "slot_id 与有效状态组合唯一，挡住重复写入"),
        ("②　Redis 分布式锁", "按仪器加锁、3 秒超时自动释放，挡住并发穿透"),
        ("③　乐观锁版本号", "写入时校验 version，挡住锁失效窗口")]
for i, (t, d) in enumerate(lock):
    y = 1.95 + i * 1.28
    rect(s, 0.9, y, 11.55, 1.12, SOFT, BLUE)
    tb(s, 1.25, y + 0.16, 3.6, 0.45, t, 21, True, BLUE)
    tb(s, 4.9, y + 0.2, 7.3, 0.75, d, 20, False, DARK)
rect(s, 0.9, 5.95, 11.55, 0.85, LIGHT, BLUE)
tb(s, 1.15, 6.1, 11.1, 0.55, "验收：500 并发下同一时段成功预约数恒为 1，P95 ≤ 800ms", 22, True, DARK)
close(s, 9)
notes(s, "这是唯一一个「做不到就不能上线」的硬指标。三层锁各自挡不同的失效场景，"
         "压测时会用 JMeter 打 500 并发验证成功数恒为 1。")

# ===================== 10 状态图 =====================
s = new("03 需求分析", "预约单 9 个状态，违约自动闭环", 10)
pic_fit(s, "state.png", 0.75, 1.85, 5.6, 4.85)
tb(s, 6.75, 2.0, 6.0, 0.45, "两条自动化规则", 24, True, BLUE)
tb(s, 6.75, 2.7, 6.0, 2.6,
   "· 15 分钟未签到 → 自动转「已违约」\n   释放时段给候补，扣 5 信用分\n\n· 信用分 < 60 → 暂停预约权限\n   须管理员审核后恢复",
   20, False, DARK, spacing=1.4)
tb(s, 6.75, 5.6, 6.0, 0.5, "爽约第一次有了成本", 24, True, ORANGE)
tb(s, 0.9, 7.05, 6, 0.3, "图 3-7　预约单状态图", 12, False, GRAY, body=False)
close(s, 10)
notes(s, "9 个状态里，已驳回、已违约、已取消是终态。仪器停用导致的取消由系统代做且免违约，"
         "这一条是访谈时机组老师特别要求的，怕设备坏了还扣学生的分。")

# ===================== 11 非功能 =====================
s = new("03 需求分析", "非功能需求全部量化到可验收", 11)
kpi = [("500", "并发抢约"), ("800ms", "接口 P95"), ("99.5%", "年可用率"), ("0", "结算偏差")]
for i, (v, u) in enumerate(kpi):
    x = 0.9 + i * 3.02
    rect(s, x, 1.95, 2.8, 2.35, LIGHT, BLUE)
    tb(s, x, 2.2, 2.8, 0.9, v, 40, True, BLUE, PP_ALIGN.CENTER)
    tb(s, x, 3.2, 2.8, 0.5, u, 20, False, DARK, PP_ALIGN.CENTER)
tb(s, 0.9, 4.75, 11.6, 1.4,
   "· 安全：等保二级，审计日志留存 ≥ 180 天\n"
   "· 兼容：Chrome / Edge 90+ 与微信小程序\n"
   "· 规模：500 台仪器、20 万单 / 年、5 年在线", 21, False, DARK, spacing=1.5)
tb(s, 0.9, 6.55, 11.6, 0.5, "10 条非功能需求，每条都写了验收方式。", 22, True, BLUE)
close(s, 11)
notes(s, "NFR-01 到 NFR-10 在 SRS 的 4.1 节有完整表格，每条都对应一个可测的验收方法，"
         "不是写「响应快」这种没法验收的话。")

# ===================== 12 架构 =====================
s = new("04 进度与成果", "技术路线：成熟栈、可交付、可运维", 12)
pic_fit(s, "arch.png", 0.55, 1.75, 12.2, 4.9)
tb(s, 0.9, 6.78, 11.6, 0.45,
   "Vue 3 + Spring Boot 3.2 + MySQL 8 + Redis 7 + MinIO　|　Docker Compose 部署", 20, False, GRAY)
close(s, 12)
notes(s, "选型原则：全部是课程里学过、文档齐全、组员能上手的技术。不追新，只求 12 周内能交付并讲清楚。"
         "外部系统四个对接点在应用层用适配器隔离，学校换系统不影响主流程。")

# ===================== 13 进度 =====================
s = new("04 进度与成果", "12 周，5 个里程碑", 13)
pic_fit(s, "gantt.png", 0.55, 1.8, 12.2, 4.55)
tb(s, 0.9, 6.55, 11.6, 0.45,
   "W2 开题答辩　·　W5 SRS 定稿　·　W7 设计评审　·　W10 功能冻结　·　W12 课程验收", 20, False, DARK)
close(s, 13)
notes(s, "关键路径是需求到设计这段。M2 结束冻结一期范围，之后的需求变更走变更单，不直接插队。")

# ===================== 14 分工 =====================
s = new("04 进度与成果", "6 人分工，组长承担主线", 14)
roles = [("朱林立", "统筹、需求、后端核心"), ("张雨欣", "前端：移动端小程序"),
         ("张义", "前端：PC 端与原型"), ("秦嘉玉", "后端：业务接口与数据"),
         ("孙福泽", "测试：用例与并发压测"), ("许军", "部署与文档答辩")]
for i, (m, r) in enumerate(roles):
    x = 0.9 + (i % 2) * 5.85
    y = 1.95 + (i // 2) * 1.5
    rect(s, x, y, 5.55, 1.25, SOFT, LINE)
    tb(s, x + 0.28, y + 0.16, 1.55, 0.45, m, 22, True, BLUE)
    tb(s, x + 1.90, y + 0.2, 3.50, 0.8, r, 20, False, DARK)
close(s, 14)
notes(s, "每人一条主线、互为备份：关键路径任务（后端并发、前端原型）都安排了第二人跟。"
         "每周一次站会，进度落后超过两天就上报组长。")

# ===================== 15 致谢 =====================
s = prs.slides.add_slide(BLANK)
set_bg(s, DARK)
rect(s, 0, 0, 0.22, H, BLUE, shape=MSO_SHAPE.RECTANGLE)
tb(s, 1.1, 2.55, 11, 1.0, "感谢聆听", 56, True, WHITE, body=False)
rect(s, 1.1, 3.75, 2.2, 0.06, BLUE, shape=MSO_SHAPE.RECTANGLE)
tb(s, 1.1, 4.1, 11, 0.5, "请各位老师批评指正", 24, False, RGBColor(0xC6, 0xCF, 0xDC), body=False)
tb(s, 1.1, 4.85, 11, 0.5, "仪约　|　第 3 组", 20, False, RGBColor(0x8A, 0xB4, 0xF8), body=False)
STATS.append((15, 3)); BODY_MIN.append((15, 20))
notes(s, "答辩后请老师重点提意见的两处：一是候补队列的公平性算法，二是与学校既有系统的接口边界。")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
prs.save(OUT)

print("saved", OUT)
bad = [(n, c) for n, c in STATS if c > 6]
print("页数:", len(prs.slides))
print("正文超过 6 行的页:", bad if bad else "无")
print("正文最小字号低于 20 的页:", [(n, m) for n, m in BODY_MIN if m < 20] or "无")



