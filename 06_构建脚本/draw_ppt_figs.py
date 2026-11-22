# -*- coding: utf-8 -*-
"""答辩 PPT 用的两张配图：技术架构图、进度甘特图"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
OUT = r"C:\dev\projects\software engineering\yi-yue\04_图表\png"
BLUE = "#1F6FEB"; DARK = "#1B2A41"; LIGHT = "#EAF1FB"; GREEN = "#1E8E3E"; ORANGE = "#B06000"


def rbox(ax, x, y, w, h, text, fc=LIGHT, ec=BLUE, fs=9, tc="#202124", bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.25",
                                facecolor=fc, edgecolor=ec, lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold" if bold else "normal", linespacing=1.6)


# ---------------- 技术架构 ----------------
fig = plt.figure(figsize=(9.6, 5.6)); ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 96); ax.set_ylim(0, 56); ax.axis("off")

ax.text(2, 53.4, "四层架构 · 前后端分离 · B/S", fontsize=10, color=DARK, fontweight="bold")

# 用户层
rbox(ax, 2, 45.5, 92, 5.6, "", fc="#F7F9FC", ec="#D5DBE5")
ax.text(3.6, 48.3, "用户层", fontsize=9, color=DARK, fontweight="bold", va="center")
for i, t in enumerate(["微信小程序（师生 / 校外用户）", "PC 管理端（机组 / 管理员 / 主管部门）", "扫码签到（仪器二维码）"]):
    rbox(ax, 15 + i * 26.5, 46.4, 24.5, 3.8, t, fc="#FFFFFF", ec="#B9C6DC", fs=7.6)

# 接入层
rbox(ax, 2, 37.4, 92, 5.6, "", fc="#F7F9FC", ec="#D5DBE5")
ax.text(3.6, 40.2, "接入层", fontsize=9, color=DARK, fontweight="bold", va="center")
for i, t in enumerate(["Nginx 反向代理 / HTTPS", "Spring Security + JWT 鉴权", "统一身份认证对接"]):
    rbox(ax, 15 + i * 26.5, 38.3, 24.5, 3.8, t, fc="#FFFFFF", ec="#B9C6DC", fs=7.6)

# 应用层
rbox(ax, 2, 21.8, 92, 13.6, "", fc=LIGHT, ec=BLUE)
ax.text(3.6, 33.6, "应用层", fontsize=9, color=BLUE, fontweight="bold", va="center")
svc = [("预约服务\nUC-02/03/04", BLUE), ("签到计时\nUC-05/06", BLUE), ("资质信用\nUC-08/09", BLUE),
       ("台账维保\nUC-10/13", BLUE), ("绩效报表\nUC-11", BLUE), ("消息通知\nUC-12", BLUE)]
for i, (t, c) in enumerate(svc):
    rbox(ax, 14.5 + i * 13.2, 28.4, 12.2, 4.6, t, fc="#FFFFFF", ec=c, fs=7.2)
rbox(ax, 14.5, 22.9, 25.4, 4.0, "冲突校验引擎（三重锁）", fc="#FFF4E5", ec=ORANGE, fs=7.6, tc=ORANGE, bold=True)
rbox(ax, 41.6, 22.9, 19.0, 4.0, "计费引擎（多口径）", fc="#FFF4E5", ec=ORANGE, fs=7.6, tc=ORANGE, bold=True)
rbox(ax, 62.2, 22.9, 19.0, 4.0, "定时任务（超时 / 违约）", fc="#FFF4E5", ec=ORANGE, fs=7.6, tc=ORANGE, bold=True)

# 数据层
rbox(ax, 2, 12.6, 92, 6.4, "", fc="#F7F9FC", ec="#D5DBE5")
ax.text(3.6, 15.8, "数据层", fontsize=9, color=DARK, fontweight="bold", va="center")
for i, t in enumerate(["MySQL 8.0\n台账 / 预约 / 结算", "Redis 7\n缓存 / 分布式锁 / 候补队列",
                       "MinIO\n报告与原始数据", "对象存储归档\n5 年数据在线"]):
    rbox(ax, 15 + i * 19.8, 13.4, 18.2, 4.8, t, fc="#FFFFFF", ec="#B9C6DC", fs=7.4)

# 外部系统
rbox(ax, 2, 4.6, 92, 5.4, "", fc="#FFFFFF", ec="#C9D2E0")
ax.text(3.6, 7.3, "外部系统", fontsize=9, color=DARK, fontweight="bold", va="center")
for i, t in enumerate(["统一身份认证", "财务经费卡", "微信公众平台", "既有仪器台账系统"]):
    rbox(ax, 18 + i * 19.2, 5.4, 17.6, 3.8, t, fc="#FFFFFF", ec="#C9D2E0", fs=7.4)

fig.savefig(os.path.join(OUT, "arch.png"), dpi=220, facecolor="white", bbox_inches="tight", pad_inches=0.1)
plt.close(fig)
print("saved arch.png")

# ---------------- 甘特图 ----------------
fig = plt.figure(figsize=(9.6, 4.4)); ax = fig.add_axes([0.24, 0.16, 0.72, 0.72])
tasks = [
    ("M1 开题（报告 + 答辩）", 0, 2, "#8AB4F8"),
    ("M2 需求（SRS + 评审）", 2, 3, BLUE),
    ("M3 设计（架构 / 数据库 / 原型）", 5, 2, "#1A73E8"),
    ("M4 开发（核心 6 个用例）", 7, 3, GREEN),
    ("M5 测试与交付（压测 / 部署）", 10, 2, ORANGE),
]
for i, (name, start, dur, color) in enumerate(tasks):
    y = len(tasks) - i - 1
    ax.barh(y, dur, left=start, height=0.52, color=color, edgecolor="white")
    ax.text(start + dur / 2, y, f"{dur} 周", ha="center", va="center", fontsize=8.5,
            color="white", fontweight="bold")
ax.set_yticks(range(len(tasks)))
ax.set_yticklabels([t[0] for t in reversed(tasks)], fontsize=9.5)
ax.set_xlim(0, 12)
ax.set_xticks(range(0, 13, 2))
ax.set_xticklabels([f"W{x}" for x in range(0, 13, 2)], fontsize=9)
ax.set_xlabel("项目周次（2026-10-26 至 2027-01-15，共 12 周）", fontsize=9.5)
ax.grid(axis="x", linestyle=":", color="#CCCCCC", alpha=0.8)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
# 里程碑标记
for x, t in [(2, "开题答辩"), (5, "SRS 定稿"), (7, "设计评审"), (10, "功能冻结"), (12, "课程验收")]:
    ax.axvline(x, color="#999999", linestyle="--", lw=0.8, alpha=0.7)
    ax.text(x, len(tasks) - 0.35, t, fontsize=7.6, color="#5F6368", ha="center")
ax.set_ylim(-0.6, len(tasks) + 0.2)
fig.savefig(os.path.join(OUT, "gantt.png"), dpi=220, facecolor="white", bbox_inches="tight", pad_inches=0.12)
plt.close(fig)
print("saved gantt.png")
