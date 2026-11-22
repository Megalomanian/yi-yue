# -*- coding: utf-8 -*-
"""生成 4 张界面原型线框图（SRS 第 5 章用）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
import os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
OUT = r"C:\dev\projects\software engineering\yi-yue\04_图表\png"

BLUE = "#1F6FEB"; LIGHT = "#F4F8FF"; GRAY = "#E8EAED"; DGRAY = "#5F6368"; WHITE = "#FFFFFF"


def box(ax, x, y, w, h, text="", fc=WHITE, ec="#C8CCD2", fs=8, tc="#202124", bold=False, r=0.6, ha="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fc, edgecolor=ec, lw=1.0, zorder=2))
    if text:
        ax.text(x + w / 2 if ha == "center" else x + 0.5, y + h / 2, text, ha=ha, va="center",
                fontsize=fs, color=tc, fontweight="bold" if bold else "normal", zorder=3, linespacing=1.5)


def phone(ax, title):
    ax.set_xlim(0, 40); ax.set_ylim(0, 76); ax.axis("off")
    ax.add_patch(FancyBboxPatch((2, 0.6), 36, 74.8, boxstyle="round,pad=0,rounding_size=2.2",
                                facecolor=WHITE, edgecolor="#999999", lw=1.6, zorder=1))
    ax.add_patch(Rectangle((2, 68.4), 36, 7, facecolor=BLUE, edgecolor="none", zorder=2))
    ax.text(4.5, 71.9, title, fontsize=10, color=WHITE, va="center", fontweight="bold", zorder=3)
    ax.text(35.4, 71.9, "···", fontsize=11, color=WHITE, va="center", ha="right", zorder=3)
    # 底部导航
    ax.add_patch(Rectangle((2, 0.6), 36, 6, facecolor=WHITE, edgecolor="#DDDDDD", lw=1, zorder=2))
    for i, t in enumerate(["查机时", "我的预约", "我的"]):
        ax.text(9 + i * 13, 3.4, t, fontsize=7.6, ha="center", va="center",
                color=BLUE if i == 0 else DGRAY, zorder=3)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print("saved", name)


# ---------- 图5-1 小程序：检索与可用时段 ----------
fig = plt.figure(figsize=(3.6, 6.9)); ax = fig.add_axes([0, 0, 1, 1])
phone(ax, "仪约 · 仪器检索")
box(ax, 5, 62.5, 30, 4.2, "搜索仪器名称 / 型号", fc="#F1F3F4", ec="none", fs=8, tc="#9AA0A6")
for i, t in enumerate(["全部分类", "显微分析", "谱学分析", "物性分析"]):
    box(ax, 5 + i * 8.4, 58.4, 7.8, 3.4, t, fc=BLUE if i == 1 else "#EEF1F6", ec="none",
        fs=7, tc=WHITE if i == 1 else DGRAY)
rows = [("场发射扫描电镜", "SU8010 · 显微分析平台", "可约 6 个时段", "¥300/小时"),
        ("高效液相色谱仪", "Agilent 1260 · 谱学分析", "可约 3 个时段", "¥120/小时"),
        ("透射电子显微镜", "JEM-2100 · 显微分析平台", "候补 2 人", "¥400/小时")]
y = 49.6
for n, m, s, p in rows:
    box(ax, 4.5, y, 31, 8.2, "", fc="#FBFCFE", ec="#DDE2EA")
    ax.text(6, y + 6.0, n, fontsize=8.2, fontweight="bold", color="#202124", zorder=4)
    ax.text(6, y + 3.6, m, fontsize=6.8, color=DGRAY, zorder=4)
    ax.text(6, y + 1.5, s, fontsize=6.8, color="#1E8E3E" if "可约" in s else "#B06000", zorder=4)
    ax.text(33.5, y + 5.2, p, fontsize=7, color=BLUE, ha="right", zorder=4)
    ax.text(33.5, y + 1.6, "查看时段 ›", fontsize=6.6, color=BLUE, ha="right", zorder=4)
    y -= 9.6
ax.text(5, 20.5, "可约时段（未来 14 天）", fontsize=8, fontweight="bold", color="#202124", zorder=4)
for i, t in enumerate(["10-29 上午", "10-29 下午", "10-30 上午", "10-30 下午", "10-31 全天"]):
    box(ax, 5 + (i % 3) * 10.4, 14.6 - (i // 3) * 5.2, 9.6, 4.0, t,
        fc="#E8F0FE" if i != 2 else "#F1F3F4", ec="#C8D4E8", fs=6.6, tc=BLUE if i != 2 else "#9AA0A6")
box(ax, 5, 8.2, 30, 4.6, "立即预约", fc=BLUE, ec="none", fs=9, tc=WHITE, bold=True)
save(fig, "ui-01-search.png")

# ---------- 图5-2 PC 审批工作台 ----------
fig = plt.figure(figsize=(8.6, 5.4)); ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")
ax.add_patch(Rectangle((0, 0), 100, 62, facecolor="#F5F6F8", edgecolor="none"))
ax.add_patch(Rectangle((0, 0), 17, 62, facecolor="#1B2A41", edgecolor="none"))
ax.text(2.5, 56, "仪约 · 管理端", fontsize=9, color=WHITE, fontweight="bold")
for i, t in enumerate(["预约审批", "仪器台账", "资质管理", "费用结算", "绩效报表"]):
    sel = i == 0
    if sel:
        ax.add_patch(Rectangle((1, 45.5 - i * 5), 15, 4.2, facecolor=BLUE, edgecolor="none"))
    ax.text(2.5, 47.6 - i * 5, t, fontsize=7.6, color=WHITE if sel else "#AEB6C2")
ax.add_patch(Rectangle((17, 54), 83, 8, facecolor=WHITE, edgecolor="#E3E6EA"))
ax.text(19.5, 58, "预约审批工作台", fontsize=9.5, fontweight="bold", color="#202124")
ax.text(96, 58, "机组：电镜机组      张老师", fontsize=7, color=DGRAY, ha="right")
for i, t in enumerate(["待审批|12", "今日已批|5", "候补排队|3"]):
    lab, val = t.split("|")
    bx = 19 + i * 27
    box(ax, bx, 44, 25, 8, "", fc=WHITE, ec="#E3E6EA")
    ax.text(bx + 2.2, 49.6, lab, fontsize=6.6, color=DGRAY)
    ax.text(bx + 2.2, 45.8, val, fontsize=10, color=BLUE, fontweight="bold")
hdr = ["预约单号", "申请人", "仪器", "时段", "样品数", "操作"]
colx = [19, 33, 45, 61, 75, 85]
ax.add_patch(Rectangle((19, 38.5), 76, 4.2, facecolor="#EAF1FB", edgecolor="#D8E0EC"))
for x, h in zip(colx, hdr):
    ax.text(x + 0.8, 40.5, h, fontsize=7, fontweight="bold", color="#202124")
data = [("R20261028001", "李同学", "SU8010 电镜", "10-29 09:00-12:00", "3", ""),
        ("R20261028002", "王老师", "HPLC 1260", "10-29 14:00-16:00", "8", ""),
        ("R20261028003", "某企业", "TEM JEM-2100", "10-30 09:00-11:00", "2", ""),
        ("R20261028004", "赵同学", "SU8010 电镜", "10-30 09:00-12:00", "1", "")]
for i, row in enumerate(data):
    yy = 34.3 - i * 5.2
    ax.add_patch(Rectangle((19, yy), 76, 5.2, facecolor=WHITE, edgecolor="#EDEFF3"))
    for cx, v in zip(colx, row):
        ax.text(cx + 0.8, yy + 2.6, v, fontsize=6.9, color="#202124" if v else DGRAY)
    if i == 3:
        box(ax, 85, yy + 1.1, 9.4, 3.0, "转候补队列", fc="#FEF7E0", ec="#E8DFB8", fs=6, tc="#B06000")
    else:
        box(ax, 85, yy + 1.1, 4.4, 3.0, "批准", fc="#E6F4EA", ec="#B7DCC0", fs=6, tc="#1E8E3E")
        box(ax, 90, yy + 1.1, 4.4, 3.0, "驳回", fc="#FCE8E6", ec="#F2BDB8", fs=6, tc="#C5221F")
box(ax, 19, 8, 76, 7, "", fc=WHITE, ec="#E3E6EA")
ax.text(21, 12.4, "审批提示：该时段剩余机时 3 小时，申请人已具备 SU8010 上机资质（有效期至 2027-06-30）",
        fontsize=6.9, color="#1E8E3E")
ax.text(21, 9.8, "冲突校验：与 R20261028004 时段重叠，系统已自动将后者转入候补队列", fontsize=6.9, color="#B06000")
box(ax, 78, 1.6, 17, 4.6, "批量通过所选", fc=BLUE, ec="none", fs=7.6, tc=WHITE, bold=True)
save(fig, "ui-02-approve.png")

# ---------- 图5-3 PC 绩效考核报表 ----------
fig = plt.figure(figsize=(8.6, 5.4)); ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")
ax.add_patch(Rectangle((0, 0), 100, 62, facecolor="#F5F6F8", edgecolor="none"))
ax.add_patch(Rectangle((0, 0), 17, 62, facecolor="#1B2A41", edgecolor="none"))
ax.text(2.5, 56, "仪约 · 管理端", fontsize=9, color=WHITE, fontweight="bold")
for i, t in enumerate(["预约审批", "仪器台账", "资质管理", "费用结算", "绩效报表"]):
    sel = i == 4
    if sel:
        ax.add_patch(Rectangle((1, 45.5 - i * 5), 15, 4.2, facecolor=BLUE, edgecolor="none"))
    ax.text(2.5, 47.6 - i * 5, t, fontsize=7.6, color=WHITE if sel else "#AEB6C2")
ax.add_patch(Rectangle((17, 54), 83, 8, facecolor=WHITE, edgecolor="#E3E6EA"))
ax.text(19.5, 58, "开放共享绩效考核报表", fontsize=9.5, fontweight="bold", color="#202124")
ax.text(96, 58, "统计周期：2026 年度", fontsize=7, color=DGRAY, ha="right")
for i, t in enumerate(["统计口径", "国家 50 万", "地方 20 万", "校内 40 万"]):
    box(ax, 19 + i * 13, 48, 11.6, 3.4, t, fc=BLUE if i == 1 else WHITE, ec="#D8E0EC",
        fs=6.6, tc=WHITE if i == 1 else DGRAY)
kpi = [("仪器开放率", "92.4%"), ("年平均有效工作机时", "1 486 h"), ("对外服务机时占比", "27.8%"), ("服务人次", "3 264")]
for i, (k, v) in enumerate(kpi):
    box(ax, 19 + i * 19.2, 38, 17.6, 8, "", fc=WHITE, ec="#E3E6EA")
    ax.text(19 + i * 19.2 + 1.5, 43.6, k, fontsize=6.2, color=DGRAY)
    ax.text(19 + i * 19.2 + 1.5, 40.0, v, fontsize=10.5, color=BLUE, fontweight="bold")
# 柱状图
ax.add_patch(Rectangle((19, 8), 38, 27, facecolor=WHITE, edgecolor="#E3E6EA"))
ax.text(20.4, 32.6, "各机组机时利用率", fontsize=7.2, fontweight="bold", color="#202124")
vals = [0.78, 0.91, 0.64, 0.85, 0.72, 0.88]
for i, v in enumerate(vals):
    x = 21.5 + i * 5.9
    ax.add_patch(Rectangle((x, 12), 3.6, v * 15, facecolor=BLUE, edgecolor="none"))
    ax.text(x + 1.8, 10.2, f"{int(v*100)}", fontsize=5.8, color=DGRAY, ha="center")
    ax.text(x + 1.8, 12 + v * 15 + 0.9, f"{int(v*100)}%", fontsize=5.4, color="#202124", ha="center")
# 明细表
ax.add_patch(Rectangle((60, 8), 35, 27, facecolor=WHITE, edgecolor="#E3E6EA"))
ax.text(61.4, 32.6, "按仪器明细（前 4 台）", fontsize=7.2, fontweight="bold", color="#202124")
th = ["仪器", "机时", "对外机时"]
for i, h in enumerate(th):
    ax.text(61.4 + i * 11, 30.2, h, fontsize=6, fontweight="bold", color=DGRAY)
det = [("SU8010", "920", "310"), ("HPLC 1260", "1 260", "402"), ("JEM-2100", "760", "188"), ("PPMS", "1 100", "265")]
for i, r in enumerate(det):
    yy = 27 - i * 4.6
    for j, v in enumerate(r):
        ax.text(61.4 + j * 11, yy, v, fontsize=6, color="#202124")
box(ax, 78, 1.6, 17, 4.6, "导出考核表（Excel）", fc=BLUE, ec="none", fs=7.2, tc=WHITE, bold=True)
save(fig, "ui-03-report.png")

# ---------- 图5-4 小程序：扫码签到 ----------
fig = plt.figure(figsize=(3.6, 6.9)); ax = fig.add_axes([0, 0, 1, 1])
phone(ax, "仪约 · 扫码上机")
box(ax, 4.5, 38.5, 31, 26, "", fc="#F1F3F4", ec="#DDE2EA")
ax.add_patch(Rectangle((9.5, 44), 21, 15, facecolor="#FFFFFF", edgecolor="#202124", lw=1.2, zorder=3))
for i in range(4):
    for j in range(4):
        if (i + j) % 3 == 0:
            ax.add_patch(Rectangle((10.8 + i * 4.9, 45.2 + j * 3.3), 3.2, 2.0,
                                   facecolor="#202124", edgecolor="none", zorder=4))
ax.text(20, 41.4, "将二维码放入框内，即可自动签到", fontsize=6.6, color=DGRAY, ha="center", zorder=4)
box(ax, 4.5, 30.5, 31, 6.4, "", fc="#EAF1FB", ec="#C8D4E8")
ax.text(6.2, 34.4, "R20261028001　SU8010 场发射扫描电镜", fontsize=7.2, fontweight="bold", color="#202124", zorder=4)
ax.text(6.2, 32.0, "10-29 09:00—12:00　机组：电镜机组", fontsize=6.6, color=DGRAY, zorder=4)
box(ax, 4.5, 22.5, 31, 6.4, "", fc="#FBF8E8", ec="#E8DFB8")
ax.text(6.2, 26.4, "签到倒计时　08:42", fontsize=7.6, fontweight="bold", color="#B06000", zorder=4)
ax.text(6.2, 24.0, "超过 15 分钟未签到，将记为违约并扣 5 信用分", fontsize=6.2, color=DGRAY, zorder=4)
box(ax, 4.5, 15.0, 31, 5.6, "确认签到并开始计时", fc=BLUE, ec="none", fs=8.4, tc=WHITE, bold=True)
box(ax, 4.5, 8.4, 31, 5.2, "取消本次预约", fc=WHITE, ec="#C8CCD2", fs=7.6, tc="#C5221F")
ax.text(20, 6.6, "取消后该时段将自动释放给候补队列", fontsize=6.0, color=DGRAY, ha="center")
save(fig, "ui-04-checkin.png")




