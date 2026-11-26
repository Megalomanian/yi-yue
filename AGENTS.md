# AGENTS.md — 仪约（InstrumentHub）AI 协作上下文指南

本文件为在此仓库工作的 AI 助手（Antigravity、Claude Code、Codex、OpenCode、Cursor 等）提供权威事实源、合规红线、架构约束与标准命令。开始任何文档修改或代码开发前，请先遵循以下准则。

---

## 1. 权威事实源与阅读入口

1. **需求与元信息唯一事实源（SST）**：[`00_事实源/project-card.md`](./00_事实源/project-card.md)
   - 锁定的编号体系：6 类参与者（`AC-01`~`AC-06`）、13 个用例（`UC-01`~`UC-13`）、9 状态预约状态机、10 项非功能需求（`NFR-01`~`NFR-10`）。未经用户明确指示，**不得更改任何已锁定的编号、角色名或用例名**。
2. **全仓结构化知识库**：[`10_知识库/README.md`](./10_知识库/README.md)
   - 查业务规则看 `02_业务规则与状态机详解.md`；
   - 查代码结构看 `03_系统架构与源码导读.md`；
   - 查全部 **17 张表与 47 个 REST 接口**看 `04_数据库字典与API接口手册.md`；
   - 查 SRS 与代码实现的既有差异及验收边界看 `05_需求追踪与验收边界矩阵.md`。

---

## 2. 文档改稿绝对红线（修改 `01_开题报告/` 或 `03_SRS/` 必守）

`06_构建脚本/qa.py` 会对开题报告与 SRS 正文执行机械扫描，任何改动**严禁触发以下违规**：

1. **12 个 AI 痕迹禁用词（0 容忍）**：
   `赋能`、`抓手`、`闭环生态`、`全方位`、`极大地`、`显著提升`、`深度融合`、`助力`、`打造`、`重塑`、`一站式解决方案`、`生态闭环`。
2. **校名与地域限制**：
   - `宁夏` 仅允许出现在署名（`宁夏大学信息工程学院`）和用户单位（`宁夏大学测试分析中心`）两处；
   - 严禁出现：`银川`、`自治区`、`宁大`、`NXU`、`分析测试中心`（正确写法为**测试分析中心**）；其余正文统一用「学校」「校内」。
3. **政策与事实诚实性红线**：
   - 严禁出现已证伪表述：`应开放尽开放`、`中华人民共和国科学数据管理办法`（正确名称无「中华人民共和国」）；
   - 2026 年 2 月施行的《国家重大科研基础设施和大型科研仪器开放共享评价考核实施细则》**官网无发文字号，严禁自拟文号**，且须注明考核对象为中央级单位、地方高校参照自查；
   - 严禁编造一手访谈人数、问卷份数或校内未公开设备台数；严禁写「完全没有线上系统」等绝对化断言；
   - 正文中的 `[[FIG:图x-x]]` 为排版脚本插图锚点，**不得删除**。

---

## 3. 系统代码开发硬约束（修改 `system/` 必守）

1. **数据库迁移不可变原则**：
   - Schema 唯一事实源位于 `system/backend/src/main/resources/db/migration/V1__initial.sql` ~ `V5__submission_sequence.sql`。
   - **禁止直接修改已发布的 V1~V5 迁移文件**（会导致已有 H2/MySQL 库 Flyway checksum 校验失败）；新增表或字段必须创建 `V6__*.sql`，并同步兼容 MySQL 8 与 H2（`MODE=MySQL;DATABASE_TO_LOWER=TRUE`）。
2. **SQL 参数化与防注入**：
   - 数据访问统一通过 `StoreMapper`（`list`/`one`/`get`/`update`/`insert`）使用 `?` 占位符绑定参数，表名仅允许硬编码常量，严禁拼接用户输入到 SQL 字符串。
3. **并发、计费与安全不变量**：
   - 任何改变预约状态或占用槽位的操作，必须经过 `SlotLock.acquire()`（生产 Redis 锁）+ `lockInstrument()`/`lockReservation()`（`FOR UPDATE` 行锁）+ `transition()`（`version` 乐观锁校验）；
   - 金额与机时计算必须使用 `BigDecimal`（严禁 `double`/`float`），账单修正必须写 `bill_adjustment` 保留原始 `bill.amount`；
   - 个人联系方式、结算卡号/账户、实名核验材料及上传报告必须经 `CryptoStorage`（`AES-256-GCM`）加密落盘，严禁明文入库或写入 `audit_log`；
   - `MANAGER` 操作仪器/预约/账单/报告/培训初审/维保时必须调用 `hub.manager(actor, instrument)` 校验 `group_id` 归属，防止跨机组越权；
   - 异常统一抛出 `new Problem(httpStatus, "面向用户的中文说明")`，由 `Errors` 拦截，严禁向客户端暴露堆栈或 SQL 细节；
   - CSV 导出单元格必须走 `ReportService.cell()` 以防御 `[=+@-]` 公式注入。
4. **运行态与临时文件隔离**：
   - 不要直接运行 `system/backend/target/*.jar`（Windows 下会锁死构建产物），统一使用 `system/scripts/start.ps1` 复制到 `system/data/runtime/` 启动；
   - 打包产物位于 `system/release/`（已被根 `.gitignore` 忽略，通过 GitHub Releases 分发，不要强行 `git add -f` 大体积压缩包或 `*.log`）。

---

## 4. 标准构建、测试与自检命令速查

### 4.1 软件系统（在 `system/` 目录执行）
```powershell
./scripts/build.ps1          # Maven verify (37 项集成测试 + JaCoCo) + npm ci + Vitest + Vite build
./scripts/start.ps1          # 启动本地前后端（前端 :5173，后端 :8080）并等待健康检查 UP
./scripts/stop.ps1           # 安全停止当前工作区前后端进程
./scripts/test.ps1           # 完整构建 + 重启 + Chrome Playwright 6 项 E2E 测试
```

### 4.2 课程文档与机械质检（在仓库根目录执行）
```powershell
python 06_构建脚本/md2docx.py # 由 Markdown 重新生成开题报告与 SRS 的 docx
python 06_构建脚本/qa.py      # 运行合规、页数、字号与章节机械自检，更新 08_自检报告.md
```
