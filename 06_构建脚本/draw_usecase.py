# -*- coding: utf-8 -*-
"""绘制系统用例图（精确坐标排版，避免自动布局导致的连线交叉与越界）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D
import math, os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = r"C:\dev\projects\software engineering\yi-yue\04_图表\png\usecase.png"

# ---------- 画布 ----------
fig = plt.figure(figsize=(10.4, 7.4), dpi=260)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 104)
ax.set_ylim(0, 74)
ax.axis("off")

C_BORDER = "#1F6FEB"
C_FILL = "#F4F8FF"
C_ACTOR = "#333333"
C_INCL = "#C0392B"
C_ASSOC = "#666666"

# ---------- 系统边界 ----------
ax.add_patch(Rectangle((27, 6.5), 50, 64, fill=False, edgecolor=C_BORDER, lw=1.6, zorder=1))
ax.text(52, 69.6, "仪约平台（高校大型仪器设备开放共享预约平台）",
        ha="center", va="center", fontsize=10.5, fontweight="bold", color=C_BORDER)

# ---------- 用例 ----------
EW, EH = 12.6, 3.9
UC = {
    "UC-01": (39, 64.5, "UC-01 仪器检索与\n可用时段查询"),
    "UC-02": (39, 56.5, "UC-02 预约申请"),
    "UC-05": (39, 48.5, "UC-05 扫码上机签到"),
    "UC-03": (39, 40.5, "UC-03 预约审批"),
    "UC-06": (39, 32.5, "UC-06 使用计时与\n费用结算"),
    "UC-10": (39, 24.5, "UC-10 设备维保与停用"),
    "UC-08": (52, 64.5, "UC-08 培训与\n上机资质认证"),
    "UC-04": (52, 50.0, "UC-04 时段冲突校验\n与候补排队"),
    "UC-07": (52, 33.0, "UC-07 检测结果交付"),
    "UC-12": (52, 16.0, "UC-12 消息通知"),
    "UC-13": (65, 64.5, "UC-13 仪器台账管理"),
    "UC-11": (65, 44.0, "UC-11 开放共享\n绩效报表"),
    "UC-09": (65, 24.5, "UC-09 违约认定与\n信用分管理"),
}

def ellipse_point(cx, cy, tx, ty):
    a, b = EW / 2, EH / 2
    dx, dy = tx - cx, ty - cy
    d = math.hypot(dx, dy)
    if d == 0:
        return cx, cy
    t = 1.0 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2)
    return cx + dx * t, cy + dy * t

def draw_uc(key):
    cx, cy, label = UC[key]
    ax.add_patch(Ellipse((cx, cy), EW, EH, facecolor=C_FILL, edgecolor=C_BORDER, lw=1.2, zorder=3))
    ax.text(cx, cy, label, ha="center", va="center", fontsize=8.4, zorder=4, linespacing=1.35)

def draw_actor(cx, cy, label):
    r = 1.15
    ax.add_patch(Ellipse((cx, cy + 2.9), r * 2, r * 2, fill=False, edgecolor=C_ACTOR, lw=1.4, zorder=5))
    ax.add_line(Line2D([cx, cx], [cy + 1.75, cy - 1.1], color=C_ACTOR, lw=1.4, zorder=5))
    ax.add_line(Line2D([cx - 1.75, cx + 1.75], [cy + 0.9, cy + 0.9], color=C_ACTOR, lw=1.4, zorder=5))
    ax.add_line(Line2D([cx, cx - 1.55], [cy - 1.1, cy - 3.4], color=C_ACTOR, lw=1.4, zorder=5))
    ax.add_line(Line2D([cx, cx + 1.55], [cy - 1.1, cy - 3.4], color=C_ACTOR, lw=1.4, zorder=5))
    ax.text(cx, cy - 5.0, label, ha="center", va="center", fontsize=8.6, color=C_ACTOR, linespacing=1.35)

# ---------- 参与者 ----------
ACTORS = {
    "AC-01": (9, 60, "送样人\nAC-01"),
    "AC-05": (9, 44, "校外用户\nAC-05"),
    "AC-02": (9, 24, "仪器负责人\nAC-02"),
    "AC-03": (95, 60, "平台管理员\nAC-03"),
    "AC-04": (95, 40, "主管部门\nAC-04"),
    "AC-06": (95, 20, "定时任务\nAC-06"),
}
for k, (x, y, lab) in ACTORS.items():
    draw_actor(x, y, lab)
for k in UC:
    draw_uc(k)

def assoc(actor, uc):
    ax_, ay_, _ = ACTORS[actor]
    cx, cy, _ = UC[uc]
    sx, sy = ax_ + (2.1 if ax_ < 50 else -2.1), ay_ + 0.9
    ex, ey = ellipse_point(cx, cy, sx, sy)
    ax.add_line(Line2D([sx, ex], [sy, ey], color=C_ASSOC, lw=0.75, zorder=2, alpha=0.9))

ASSOC = [
    # 主参与者（每个用例只画主参与者连线，次要参与者在 3.2 节用例描述表中说明）
    ("AC-01", "UC-01"), ("AC-01", "UC-02"), ("AC-01", "UC-05"),
    ("AC-05", "UC-01"), ("AC-05", "UC-02"),
    ("AC-02", "UC-03"), ("AC-02", "UC-06"), ("AC-02", "UC-07"), ("AC-02", "UC-10"),
    ("AC-03", "UC-08"), ("AC-03", "UC-13"),
    ("AC-04", "UC-11"),
    ("AC-06", "UC-04"), ("AC-06", "UC-09"), ("AC-06", "UC-12"),
]
for a, u in ASSOC:
    assoc(a, u)

def include(src, dst, label=None):
    s = UC[src]
    d = UC[dst]
    sx, sy = ellipse_point(s[0], s[1], d[0], d[1])
    ex, ey = ellipse_point(d[0], d[1], s[0], s[1])
    ax.add_patch(FancyArrowPatch((sx, sy), (ex, ey), arrowstyle="-|>", mutation_scale=9,
                                 linestyle=(0, (4, 2.5)), color=C_INCL, lw=0.95,
                                 shrinkA=0, shrinkB=0, zorder=2))
    if label:
        ax.text((sx + ex) / 2, (sy + ey) / 2 + 0.6, label, ha="center", va="bottom",
                fontsize=7.4, color=C_INCL, style="italic")

include("UC-02", "UC-04")
include("UC-05", "UC-06")
include("UC-02", "UC-12")
include("UC-03", "UC-12")
include("UC-07", "UC-12")
include("UC-08", "UC-12")
include("UC-10", "UC-12")

# ---------- 图例 ----------
ax.text(20, 2.4,
        "图例：实线——参与者与用例的关联（仅绘制主参与者）　红色虚线箭头 <<include>>——用例包含关系\n"
        "说明：①各用例的次要参与者见 3.2 节用例描述表；②UC-08 培训与上机资质认证是 UC-02 的前置条件（未取得资质者不得预约需独立操作的仪器），属前置约束，不画作 include 关系。",
        ha="left", va="center", fontsize=6.9, color="#444444", linespacing=1.7)

fig.savefig(OUT, dpi=260, facecolor="white", bbox_inches="tight", pad_inches=0.15)
print("saved", OUT)

