# -*- coding: utf-8 -*-
"""按最终版 PPT 的配色与版式，生成 5 张可直接贴进幻灯片的图（20 x 11.25 英寸）"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Circle, FancyArrowPatch
from matplotlib.lines import Line2D
import math

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = r"C:\dev\projects\software engineering\yi-yue\04_图表\deck"
os.makedirs(OUT, exist_ok=True)

# ===== 取自最终版 PPT 的配色 =====
BG = "#FFF8EF"
NAVY = "#2B3A67"
NAVY2 = "#2B3B66"
BODY = "#3D4E70"
MUTED = "#5A6B8C"
VIOLET = "#A78BFA"
TEAL = "#4ECDC4"
YELLOW = "#FFD166"
ORANGE = "#FF8A4C"
WHITE = "#FFFFFF"
CARD_LINE = "#E6DED0"
VIOLET_BG = "#F1EBFF"
TEAL_BG = "#E4F8F6"
YELLOW_BG = "#FFF6DF"
ORANGE_BG = "#FFEDE3"

W, H = 20.0, 11.25   # 与 PPT 画布一致（英寸）


def new_slide(kicker, title, sub):
    fig = plt.figure(figsize=(W, H), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), W, H, facecolor=BG, edgecolor="none", zorder=0))
    # 栏目小标
    ax.add_patch(FancyBboxPatch((1.04, 0.83), 2.10, 0.74,
                                boxstyle="round,pad=0,rounding_size=0.12",
                                facecolor=VIOLET_BG, edgecolor="none", zorder=2))
    ax.text(2.09, 1.20, kicker, ha="center", va="center", fontsize=13, color=NAVY, zorder=3)
    # 标题与副标题
    ax.text(1.04, 1.72, title, ha="left", va="center", fontsize=30, color=NAVY, fontweight="bold", zorder=3)
    ax.text(1.04, 2.42, sub, ha="left", va="center", fontsize=13.5, color=MUTED, zorder=3)
    ax.add_patch(Rectangle((1.04, 2.72), 0.9, 0.035, facecolor=VIOLET, edgecolor="none", zorder=3))
    return fig, ax


def card(ax, x, y, w, h, fc=WHITE, ec=CARD_LINE, r=0.14, lw=1.1, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z))


def actor(ax, cx, cy, name, code, color=NAVY):
    """stick figure，cy 为图形中心"""
    ax.add_patch(Circle((cx, cy - 0.62), 0.15, facecolor="none", edgecolor=color, lw=1.6, zorder=5))
    ax.add_line(Line2D([cx, cx], [cy - 0.47, cy + 0.18], color=color, lw=1.6, zorder=5))
    ax.add_line(Line2D([cx - 0.26, cx + 0.26], [cy - 0.10, cy - 0.10], color=color, lw=1.6, zorder=5))
    ax.add_line(Line2D([cx, cx - 0.24], [cy + 0.18, cy + 0.52], color=color, lw=1.6, zorder=5))
    ax.add_line(Line2D([cx, cx + 0.24], [cy + 0.18, cy + 0.52], color=color, lw=1.6, zorder=5))
    ax.text(cx, cy + 0.70, name, ha="center", va="top", fontsize=11.5, color=NAVY, fontweight="bold", zorder=6)
    ax.text(cx, cy + 0.94, code, ha="center", va="top", fontsize=9.5, color=MUTED, zorder=6)


def ellipse_edge(cx, cy, a, b, tx, ty):
    dx, dy = tx - cx, ty - cy
    d = math.hypot(dx, dy) or 1
    t = 1.0 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2)
    return cx + dx * t, cy + dy * t


# =========================================================
# 图 1：用例图
# =========================================================
def fig_usecase():
    fig, ax = new_slide("03  需求分析", "系统用例图：6 类参与者，13 个用例",
                        "实线为主参与者与用例的关联，橙色虚线为 <<include>>；UC-12 被五个用例共同包含，为避免连线过密未逐条绘制")
    bx0, bx1, by0, by1 = 4.30, 15.70, 3.32, 9.12
    card(ax, bx0, by0, bx1 - bx0, by1 - by0, fc="#FFFFFF", ec=VIOLET, lw=1.6)
    ax.text(bx1 - 0.22, by0 + 0.26, "仪约平台", ha="right", va="center",
            fontsize=11.5, color=VIOLET, fontweight="bold", zorder=4)

    EW, EH = 3.30, 0.78
    A, L = 2.05, 17.95
    actors = {
        "AC-01": (A, 4.30, "送样人", "AC-01"),
        "AC-05": (A, 6.35, "校外用户", "AC-05"),
        "AC-02": (A, 8.20, "仪器负责人", "AC-02"),
        "AC-03": (L, 4.30, "平台管理员", "AC-03"),
        "AC-04": (L, 6.35, "主管部门", "AC-04"),
        "AC-06": (L, 8.20, "定时任务", "AC-06"),
    }
    for k, (x, y, n, c) in actors.items():
        actor(ax, x, y, n, c)

    R = [3.80, 4.83, 5.86, 6.89, 7.92, 8.95]
    UC = {
        "UC-01": (6.40, R[0], "UC-01 仪器检索与\n可用时段查询"),
        "UC-02": (6.40, R[1], "UC-02 预约申请"),
        "UC-05": (6.40, R[2], "UC-05 扫码上机签到"),
        "UC-07": (6.40, R[3], "UC-07 检测结果交付"),
        "UC-06": (6.40, R[4], "UC-06 使用计时与费用结算"),
        "UC-03": (6.40, R[5], "UC-03 预约审批"),
        "UC-04": (10.15, R[1], "UC-04 时段冲突校验\n与候补排队"),
        "UC-12": (10.15, R[3], "UC-12 消息通知"),
        "UC-13": (13.90, R[0], "UC-13 仪器台账管理"),
        "UC-08": (13.90, R[1], "UC-08 培训与上机资质认证"),
        "UC-11": (13.90, R[2], "UC-11 开放共享绩效报表"),
        "UC-10": (13.90, R[3], "UC-10 设备维保与停用"),
        "UC-09": (13.90, R[4], "UC-09 违约认定与\n信用分管理"),
    }
    for k, (x, y, t) in UC.items():
        ax.add_patch(Ellipse((x, y), EW, EH, facecolor=VIOLET_BG, edgecolor=VIOLET, lw=1.3, zorder=3))
        ax.text(x, y, t, ha="center", va="center", fontsize=9.4, color=NAVY, zorder=4, linespacing=1.32)

    def assoc(a, u, color=NAVY2):
        ax_, ay_, _, _ = actors[a]
        cx, cy, _ = UC[u]
        sx = ax_ + (0.32 if ax_ < 10 else -0.32)
        sy = ay_ - 0.08
        ex, ey = ellipse_edge(cx, cy, EW / 2, EH / 2, sx, sy)
        ax.add_line(Line2D([sx, ex], [sy, ey], color=color, lw=1.1, alpha=0.8, zorder=2))

    for a, us in [("AC-01", ["UC-01", "UC-02", "UC-05", "UC-07"]),
                  ("AC-05", ["UC-01", "UC-02"]),
                  ("AC-02", ["UC-03", "UC-06", "UC-07"]),
                  ("AC-03", ["UC-13", "UC-08"]),
                  ("AC-04", ["UC-11"]),
                  ("AC-06", ["UC-09", "UC-04", "UC-12"])]:
        for u in us:
            assoc(a, u)

    def inc(s, d):
        sx, sy = ellipse_edge(*UC[s][:2], EW / 2, EH / 2, *UC[d][:2])
        ex, ey = ellipse_edge(*UC[d][:2], EW / 2, EH / 2, *UC[s][:2])
        ax.add_patch(FancyArrowPatch((sx, sy), (ex, ey), arrowstyle="-|>", mutation_scale=12,
                                     linestyle=(0, (4, 2.4)), color=ORANGE, lw=1.3,
                                     shrinkA=0, shrinkB=0, zorder=2))

    inc("UC-02", "UC-04")
    inc("UC-05", "UC-06")

    ax.text(10.15, R[3] + 0.58,
            "UC-12 同时被 UC-02 / 03 / 07 / 08 / 10 包含\n（业务完成后统一写通知记录，属必有行为）",
            ha="center", va="top", fontsize=8.6, color=ORANGE, zorder=5, linespacing=1.4)

    ax.text(4.30, 9.52,
            "实线：主参与者与用例的关联（次要参与者见用例描述表）　　"
            "橙色虚线：<<include>>；UC-08 是 UC-02 的前置约束而非包含，未画箭头",
            fontsize=10.5, color=MUTED, ha="left", va="center")
    fig.savefig(os.path.join(OUT, "01_用例图.png"), dpi=150, facecolor=BG, bbox_inches=None)
    plt.close(fig)
    print("saved 01_用例图.png")


# =========================================================
# 图 2：功能性需求
# =========================================================
def fig_fr():
    fig, ax = new_slide("03  需求分析", "功能性需求：28 条，按四个模块分组",
                        "每条需求都能回溯到一个用例；高优先级 13 条，覆盖预约主链与台账权限基础")
    FR = [
        ("资源与预约入口", VIOLET, VIOLET_BG, 6, [
            ("FR-01", "仪器建档与参数维护", "高"),
            ("FR-02", "按用户类型配置多套单价", "高"),
            ("FR-03", "按分类/关键词检索仪器", "高"),
            ("FR-04", "时段显示剩余样品数与单价", "中"),
            ("FR-05", "预约单填写与草稿暂存", "高"),
            ("FR-06", "提交前校验资质与信用分", "高"),
        ]),
        ("并发与审批", ORANGE, ORANGE_BG, 7, [
            ("FR-07", "提交瞬间唯一性校验", "高"),
            ("FR-08", "时段满则进候补队列", "高"),
            ("FR-09", "审批通过与驳回理由", "高"),
            ("FR-10", "待审批列表与批量审批", "中"),
            ("FR-11", "扫码签到并启动计时", "高"),
            ("FR-12", "代签到与审计标识", "中"),
            ("FR-13", "15 分钟未签到判违约", "高"),
        ]),
        ("计时结算与交付", TEAL, TEAL_BG, 7, [
            ("FR-14", "计时结算与时长修正", "高"),
            ("FR-15", "经费卡内转与对公转账", "高"),
            ("FR-16", "费用单复核、退改与作废", "中"),
            ("FR-17", "报告上传与版本替换", "中"),
            ("FR-18", "在线下载与年度归档", "中"),
            ("FR-19", "线上培训与考试", "中"),
            ("FR-20", "资质颁发与到期提醒", "中"),
        ]),
        ("治理与统计", YELLOW, YELLOW_BG, 8, [
            ("FR-21", "三类违约认定与扣分", "中"),
            ("FR-22", "信用分阈值与权限恢复", "中"),
            ("FR-23", "故障报修与停用下架", "中"),
            ("FR-24", "停用代取消并免违约", "中"),
            ("FR-25", "机时利用率多维统计", "中"),
            ("FR-26", "考核格式导出与口径说明", "中"),
            ("FR-27", "事件触达与消息通知", "中"),
            ("FR-28", "权限配置与审计日志", "高"),
        ]),
    ]
    x0, y0, cw, gap = 1.04, 3.05, 4.38, 0.18
    ch = 6.55
    for i, (name, col, bg, cnt, items) in enumerate(FR):
        x = x0 + i * (cw + gap)
        card(ax, x, y0, cw, ch, fc=WHITE, ec=CARD_LINE)
        card(ax, x, y0, cw, 0.78, fc=bg, ec="none", r=0.14)
        ax.text(x + 0.24, y0 + 0.39, name, va="center", fontsize=15, color=NAVY, fontweight="bold")
        ax.text(x + cw - 0.24, y0 + 0.39, f"{cnt} 条", va="center", ha="right",
                fontsize=12.5, color=col, fontweight="bold")
        for j, (fid, txt, pri) in enumerate(items):
            yy = y0 + 1.02 + j * 0.70
            dot = ORANGE if pri == "高" else MUTED
            ax.add_patch(Circle((x + 0.26, yy + 0.04), 0.05, facecolor=dot, edgecolor="none"))
            ax.text(x + 0.42, yy - 0.16, fid, fontsize=10.5, color=col, fontweight="bold", va="top")
            ax.text(x + 1.20, yy - 0.16, txt, fontsize=11.5, color=BODY, va="top")
    ax.text(1.04, 9.92, "● 高优先级（13 条）　　● 中优先级（15 条）　　优先级按『是否阻断主链路』排，不按重要性排",
            fontsize=11, color=MUTED, ha="left", va="center")
    fig.savefig(os.path.join(OUT, "02_功能性需求.png"), dpi=150, facecolor=BG)
    plt.close(fig)
    print("saved 02_功能性需求.png")


# =========================================================
# 图 3：非功能性需求
# =========================================================
def fig_nfr():
    fig, ax = new_slide("03  需求分析", "非功能性需求：10 条，每条都写了验收方式",
                        "不写『响应快』『稳定性好』这类无法验收的话，全部落成可测指标")
    rows = [
        ("NFR-01", "并发性能", "瞬时并发 500；预约接口 P95 ≤ 800ms；同一时段绝不超卖", "JMeter 500 并发抢同一时段，成功数须恒为 1", True),
        ("NFR-02", "响应性能", "常规查询首屏 ≤ 2s；报表生成 ≤ 5s（20 万单/年）", "抽样 100 次计时，取 P95", False),
        ("NFR-03", "可用性", "7×24；年可用率 ≥ 99.5%；故障恢复 ≤ 30min", "监控统计 + 故障演练", False),
        ("NFR-04", "数据一致性", "结算金额与机时记录偏差为 0；对账差错率为 0", "对账脚本比对费用单与机时流水", True),
        ("NFR-05", "安全性", "达等保二级；审计日志留存 ≥ 180 天", "渗透测试 + 日志抽样核查", False),
        ("NFR-06", "兼容性", "Chrome/Edge 90+；最小 1366×768；微信小程序", "多浏览器矩阵测试", False),
        ("NFR-07", "数据规模", "500 台仪器、20 万单/年、5 年历史在线可查", "造数压测（固定随机种子）", False),
        ("NFR-08", "可维护性", "前后端分离；单元测试覆盖率 ≥ 60%", "覆盖率报告作为交付附件", False),
        ("NFR-09", "易用性", "约一次机时 ≤ 3 步；新用户无需培训", "任务走查，记录完成时间与步数", False),
        ("NFR-10", "合规性", "校外实名审核；个人信息与检测数据加密存储", "隐私合规检查 + 权限矩阵核对", False),
    ]
    x0, y0 = 1.04, 3.00
    widths = [1.65, 1.90, 8.55, 6.10]
    heads = ["编号", "类别", "指标要求", "验收方式"]
    rh = 0.62
    tx = x0
    card(ax, x0, y0, sum(widths), rh, fc=VIOLET_BG, ec=VIOLET, r=0.10)
    for w, h in zip(widths, heads):
        ax.text(tx + 0.22, y0 + rh / 2, h, va="center", fontsize=12.5, color=NAVY, fontweight="bold")
        tx += w
    for i, (fid, cat, idx, ver, key) in enumerate(rows):
        y = y0 + rh + i * rh
        card(ax, x0, y, sum(widths), rh, fc="#FFFFFF" if i % 2 == 0 else "#FDFAF4", ec=CARD_LINE, r=0.02, lw=0.7)
        tx = x0
        ax.text(tx + 0.22, y + rh / 2, fid, va="center", fontsize=11.5,
                color=ORANGE if key else NAVY2, fontweight="bold")
        tx += widths[0]
        ax.text(tx + 0.22, y + rh / 2, cat, va="center", fontsize=11.5, color=BODY)
        tx += widths[1]
        ax.text(tx + 0.22, y + rh / 2, idx, va="center", fontsize=11.5, color=BODY)
        tx += widths[2]
        ax.text(tx + 0.22, y + rh / 2, ver, va="center", fontsize=11, color=MUTED)
    ax.text(1.04, 10.05, "橙色编号的 NFR-01 与 NFR-04 是硬指标：做不到就不能上线，其余为质量目标",
            fontsize=11, color=MUTED, ha="left", va="center")
    fig.savefig(os.path.join(OUT, "03_非功能性需求.png"), dpi=150, facecolor=BG)
    plt.close(fig)
    print("saved 03_非功能性需求.png")


# =========================================================
# 图 4：分析类图
# =========================================================
def fig_class():
    fig, ax = new_slide("03  需求分析", "分析类图：边界类—控制类—实体类",
                        "12 个实体来自领域概念，5 个控制类承接用例行为，3 个边界类对接两端界面与外部系统")
    D = {}
    # ---- 边界类 ----
    B = [("MiniAppUI\n小程序界面", 1.35), ("AdminUI\n管理端界面", 5.55), ("NotifyGateway\n消息网关", 9.75)]
    for name, x in B:
        card(ax, x, 3.05, 3.6, 0.62, fc=TEAL_BG, ec=TEAL, r=0.10)
        ax.text(x + 1.8, 3.36, name.replace("\n", " "), ha="center", va="center",
                fontsize=11.5, color="#0E7D74", fontweight="bold")
    ax.text(14.2, 3.36, "«boundary»", fontsize=10.5, color=TEAL, va="center", style="italic")

    # ---- 控制类 ----
    C = [("ReservationCtrl\n预约控制", 1.35), ("ConflictCtrl\n冲突校验", 4.55),
         ("BillingCtrl\n计费控制", 7.75), ("QualificationCtrl\n资质控制", 10.95),
         ("ReportCtrl\n报表控制", 14.15)]
    for name, x in C:
        card(ax, x, 4.05, 3.05, 0.66, fc=YELLOW_BG, ec=YELLOW, r=0.10)
        ax.text(x + 1.52, 4.38, name.replace("\n", " "), ha="center", va="center",
                fontsize=11, color="#8A6A12", fontweight="bold")
    ax.text(17.5, 4.38, "«control»", fontsize=10.5, color="#B58A16", va="center", style="italic")

    # ---- 实体类 ----
    E = [
        ("Instrument", "仪器", ["instId 仪器编号", "name 名称 / model 型号", "price 原值", "calibers 口径标签", "openStatus 开放状态"], 1.35, 5.30),
        ("Slot", "时段", ["slotId 时段编号", "instId 仪器编号", "start / end 起止", "status 状态"], 5.75, 5.30),
        ("Reservation", "预约单", ["resId 预约单号", "userId / slotId", "status 状态（9 种）", "sampleCount 样品数"], 10.15, 5.30),
        ("FeeBill", "费用单", ["billId 费用单号", "resId 预约单号", "machineHour 机时", "amount 金额"], 14.55, 5.30),
        ("InstrumentGroup", "机组", ["groupId 机组编号", "groupName 名称", "ownerId 负责人"], 1.35, 7.30),
        ("User", "用户", ["userId 用户编号", "userType 用户类型", "creditScore 信用分"], 4.85, 7.30),
        ("Qualification", "资质", ["qualId 资质编号", "userId 持证人", "expireTime 有效期"], 8.35, 7.30),
        ("CreditRecord", "信用记录", ["recordId 流水号", "changeValue 分值变动", "reason 原因"], 11.85, 7.30),
        ("TestReport", "检测报告", ["reportId 报告编号", "resId 预约单号", "fileUrl 存储路径"], 15.35, 7.30),
        ("MaintenanceRecord", "维保记录", ["maintId 记录号", "instId 仪器", "type 故障 / 保养"], 1.35, 8.95),
        ("NotifyMessage", "通知", ["msgId 消息编号", "userId 接收人", "type 消息类型"], 5.85, 8.95),
        ("Role", "角色", ["roleId 角色编号", "roleName 角色名", "scope 权限范围"], 10.35, 8.95),
    ]
    for name, cn, attrs, x, y in E:
        w, h = 3.3, 1.42
        card(ax, x, y, w, h, fc=WHITE, ec=VIOLET, r=0.08)
        ax.add_patch(Rectangle((x, y), w, 0.36, facecolor=VIOLET_BG, edgecolor="none", zorder=3))
        ax.text(x + 0.16, y + 0.18, f"{name}  {cn}", va="center", fontsize=10.2,
                color=NAVY, fontweight="bold", zorder=4)
        for i, a in enumerate(attrs):
            ax.text(x + 0.18, y + 0.52 + i * 0.24, a, va="center", fontsize=8.4, color=BODY, zorder=4)
        D[name] = (x, y, w, h)

    def link(a, b, label=None, style="-", color=NAVY2, lw=0.9):
        x1, y1, w1, h1 = D[a]; x2, y2, w2, h2 = D[b]
        p1 = (x1 + w1 / 2, y1 + h1 if y1 < y2 else y1)
        p2 = (x2 + w2 / 2, y2 if y1 < y2 else y2 + h2)
        if abs(y1 - y2) < 0.05:  # 同一行
            p1 = (x1 + w1 if x1 < x2 else x1, y1 + h1 / 2)
            p2 = (x2 if x1 < x2 else x2 + w2, y2 + h2 / 2)
        ax.add_line(Line2D([p1[0], p2[0]], [p1[1], p2[1]], color=color, lw=lw,
                           linestyle=style, alpha=0.8, zorder=2))
        if label:
            ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 - 0.10, label,
                    ha="center", fontsize=8, color=MUTED, zorder=4,
                    bbox=dict(boxstyle="round,pad=0.12", fc=BG, ec="none"))

    link("Instrument", "Slot", "1 : 0..*")
    link("Slot", "Reservation", "1 : 0..*")
    link("Reservation", "FeeBill", "1 : 0..1")
    link("User", "Reservation", "1 : 0..*")
    link("Instrument", "InstrumentGroup", "0..* : 1")
    link("User", "Qualification", "1 : 0..*")
    link("User", "CreditRecord", "1 : 0..*")
    link("Reservation", "TestReport", "1 : 0..1")
    link("Instrument", "MaintenanceRecord", "1 : 0..*")
    link("User", "NotifyMessage", "1 : 0..*")
    link("Role", "User", "1 : 0..*")
    # 控制类到实体的依赖（淡色虚线）
    ax.add_line(Line2D([2.9, 2.9], [4.71, 5.30], color=MUTED, lw=0.8, ls=(0, (3, 3)), alpha=0.6, zorder=2))
    ax.add_line(Line2D([3.0, 3.0], [4.71, 8.02], color=MUTED, lw=0.8, ls=(0, (3, 3)), alpha=0.4, zorder=2))
    ax.add_line(Line2D([11.9, 11.9], [4.71, 5.30], color=MUTED, lw=0.8, ls=(0, (3, 3)), alpha=0.6, zorder=2))
    ax.add_line(Line2D([16.0, 16.0], [4.71, 5.30], color=MUTED, lw=0.8, ls=(0, (3, 3)), alpha=0.6, zorder=2))
    ax.add_line(Line2D([12.5, 12.5], [4.71, 7.30], color=MUTED, lw=0.8, ls=(0, (3, 3)), alpha=0.4, zorder=2))

    ax.text(1.04, 10.45, "多重性标注在关联线旁；控制类到实体类的虚线为依赖关系。仪器与单价规则之间是多对多，"
                         "通过『用户类型—价格』表达，因此单价不放在关联上而放在规则表里。",
            fontsize=10.5, color=MUTED, ha="left", va="center")
    fig.savefig(os.path.join(OUT, "04_分析类图.png"), dpi=150, facecolor=BG)
    plt.close(fig)
    print("saved 04_分析类图.png")


# =========================================================
# 图 5：数据模型与数据词典
# =========================================================
def fig_data():
    fig, ax = new_slide("03  需求分析", "数据模型：12 张核心表与关键约束",
                        "每张表的字段数与主键、唯一约束都定到字段级；口径做成仪器上的多值标签，不另建表")
    tables = [
        ("instrument", "仪器台账", "inst_id PK; asset_no UK; calibers 多值", "口径标签可同时挂多个，报表按标签过滤"),
        ("instrument_group", "机组", "group_id PK; owner_id FK→user", "一台机组含多台仪器，一个负责人"),
        ("slot", "时段", "slot_id PK; (inst_id,start_time) UK", "唯一约束是防超卖的第一道闸"),
        ("reservation", "预约单", "res_id PK; 同一时段最多一个有效预约", "只允许一个有效占用，取消后释放"),
        ("fee_bill", "费用单", "bill_id PK; res_id FK; version", "一张预约单最多一张有效费用单"),
        ("test_report", "检测报告", "report_id PK; res_id FK; object_key", "文件存 MinIO，库里只存路径"),
        ("maintenance_record", "维保记录", "maint_id PK; inst_id FK", "停用期间自动下架相关时段"),
        ("qualification", "上机资质", "qual_id PK; (user_id,category) UK", "含发证时间与有效期，到期前提醒"),
        ("credit_record", "信用记录", "record_id PK; user_id FK; delta", "流水表，不改历史，只追加"),
        ("notify_message", "通知", "msg_id PK; user_id FK; read_flag", "站内信 + 微信模板消息双通道"),
        ("sys_user", "用户", "user_id PK; login_name UK; pwd_hash", "密码加盐哈希，不存明文"),
        ("sys_role", "角色", "role_id PK; role_code UK", "六类角色，权限到功能点"),
    ]
    x0, y0 = 1.04, 3.00
    widths = [3.05, 2.10, 6.20, 6.85]
    heads = ["表名", "中文名", "主键与关键约束", "设计说明"]
    rh = 0.55
    card(ax, x0, y0, sum(widths), rh, fc=VIOLET_BG, ec=VIOLET, r=0.10)
    tx = x0
    for w, h in zip(widths, heads):
        ax.text(tx + 0.20, y0 + rh / 2, h, va="center", fontsize=12.5, color=NAVY, fontweight="bold")
        tx += w
    for i, (t, cn, key, note) in enumerate(tables):
        y = y0 + rh + i * rh
        card(ax, x0, y, sum(widths), rh, fc="#FFFFFF" if i % 2 == 0 else "#FDFAF4", ec=CARD_LINE, r=0.02, lw=0.7)
        tx = x0
        vals = [(t, NAVY2, True, 10.4), (cn, BODY, False, 11), (key, BODY, False, 9.8), (note, MUTED, False, 9.8)]
        for (v, c, bold, fs), w in zip(vals, widths):
            ax.text(tx + 0.20, y + rh / 2, v, va="center", fontsize=fs, color=c,
                    fontweight="bold" if bold else "normal")
            tx += w
    ax.text(1.04, 10.42, "PK 主键　UK 唯一约束　FK 逻辑外键（不建物理外键，便于分表与归档）　　"
                         "索引：预约单按 (user_id,status)、(inst_id,start_time) 建联合索引",
            fontsize=10.5, color=MUTED, ha="left", va="center")
    fig.savefig(os.path.join(OUT, "05_数据模型.png"), dpi=150, facecolor=BG)
    plt.close(fig)
    print("saved 05_数据模型.png")


# =========================================================
# 图 6：预约申请与时段冲突校验顺序图
# =========================================================
def fig_sequence():
    fig, ax = new_slide(
        "03  需求分析",
        "顺序图：预约申请与时段冲突校验",
        "对应 UC-02 / UC-04；资质、信用分先校验，时段占用在提交瞬间进行原子校验"
    )

    # 泳道参与者
    lanes = [
        ("送样人", 2.45, VIOLET_BG, VIOLET),
        ("小程序 / Web", 5.70, TEAL_BG, TEAL),
        ("预约服务", 9.15, YELLOW_BG, YELLOW),
        ("Redis 锁", 12.60, ORANGE_BG, ORANGE),
        ("MySQL", 16.05, VIOLET_BG, VIOLET),
        ("消息服务", 18.65, TEAL_BG, TEAL),
    ]
    top, bottom = 3.25, 9.40
    for name, x, fc, ec in lanes:
        card(ax, x - 1.08, top, 2.16, 0.58, fc=fc, ec=ec, r=0.10)
        ax.text(x, top + 0.29, name, ha="center", va="center", fontsize=11.2,
                color=NAVY, fontweight="bold", zorder=4)
        ax.add_line(Line2D([x, x], [top + 0.58, bottom], color=CARD_LINE,
                           lw=1.1, linestyle=(0, (3, 3)), zorder=1))

    def msg(src, dst, y, label, color=NAVY2, dashed=False, align_offset=0.0):
        x1 = lanes[src][1]
        x2 = lanes[dst][1]
        ax.add_patch(FancyArrowPatch(
            (x1, y), (x2, y), arrowstyle="-|>", mutation_scale=13,
            linewidth=1.35, color=color,
            linestyle=(0, (4, 2.5)) if dashed else "-",
            shrinkA=0, shrinkB=0, zorder=3
        ))
        ax.text((x1 + x2) / 2, y - 0.13 + align_offset, label,
                ha="center", va="bottom", fontsize=9.4, color=color,
                bbox=dict(boxstyle="round,pad=0.12", fc=BG, ec="none"), zorder=5)

    ys = [4.10, 4.75, 5.40, 6.05, 6.70, 7.35, 8.00, 8.65]
    msg(0, 1, ys[0], "① 选择仪器、时段，填写样品与检测项目", color=NAVY2)
    msg(1, 2, ys[1], "② 提交预约申请", color=NAVY2)
    msg(2, 4, ys[2], "③ 校验资质有效、信用分 ≥ 60", color=NAVY2)
    msg(4, 2, ys[3], "④ 返回校验通过", color=MUTED, dashed=True)
    msg(2, 3, ys[4], "⑤ 按 仪器ID + 时段ID 获取分布式锁", color=ORANGE)
    msg(3, 4, ys[5], "⑥ 执行唯一性检查并写入预约单", color=ORANGE)
    msg(4, 5, ys[6], "⑦ 写入成功后发送待审批通知", color=TEAL)
    msg(5, 1, ys[7], "⑧ 返回预约单号与待审批状态", color=TEAL, dashed=True)

    # 并发冲突 alt 分支说明
    card(ax, 1.04, 9.62, 17.90, 1.02, fc=ORANGE_BG, ec=ORANGE, r=0.12)
    ax.text(1.35, 9.96, "alt：同一时段已被占用", fontsize=11.5, color=ORANGE,
            fontweight="bold", va="center")
    ax.text(5.05, 9.96,
            "拒绝当前预约写入 → 提示可选时段；若已满则创建候补记录 → 按提交时间排队 → 有人取消时原子补位",
            fontsize=11.0, color=BODY, va="center")
    ax.text(1.35, 10.38,
            "锁释放后再写库；数据库唯一约束为最终防线。写入失败回滚并释放锁，避免出现双占用。",
            fontsize=10.1, color=MUTED, va="center")

    fig.savefig(os.path.join(OUT, "06_预约顺序图.png"), dpi=150, facecolor=BG, bbox_inches=None)
    plt.close(fig)
    print("saved 06_预约顺序图.png")


if __name__ == "__main__":
    fig_usecase()
    fig_fr()
    fig_nfr()
    fig_class()
    fig_data()
    fig_sequence()





