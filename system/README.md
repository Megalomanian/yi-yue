# 仪约 InstrumentHub

根据上级目录的 `03_SRS/SRS-正文.md` 和 `00_事实源/project-card.md` 实现的高校大型仪器设备开放共享预约平台。保留原始需求与答辩资料，系统代码独立放在本目录。

## 本地启动

需要 JDK 21、Maven 3.9、Node.js 22 或 24、Chrome。当前工作区已准备 JDK 21 和 Maven，脚本会优先使用 `.tools` 中的工具。

在本目录打开 PowerShell：

```powershell
./scripts/build.ps1
./scripts/start.ps1
```

- 网页：<http://localhost:5173>
- 后端健康检查：<http://localhost:8080/actuator/health>
- OpenAPI JSON：<http://localhost:8080/v3/api-docs>
- Swagger UI：<http://localhost:8080/swagger-ui/index.html>
- 停止本地进程：`./scripts/stop.ps1`，不会删除数据。

本地使用 H2 文件数据库和 AES-GCM 加密的报告文件，数据位于 `backend/data/`。生产配置使用 MySQL 8、Redis 7、MinIO。两种运行方式共用业务代码和 Flyway 数据库迁移。

### 演示账号

全部演示密码为 `Demo12345!`，仅在空库且 `DEMO_MODE=true` 时创建。

| 账号 | 角色 |
|---|---|
| student / student2 | 校内送样人 |
| external | 已审核校外用户 |
| manager | 第一机组仪器负责人 |
| manager2 | 第二机组负责人，用于越权验证 |
| admin | 平台管理员 |
| department | 主管部门，只读报表与财务导出 |

演示账号、单位和仪器数据均为软件演示用的合成数据，不代表实际使用记录。演示送样人已预置资质，便于立即预约；新注册校外用户须审核、培训初审和考试后获得资质。

## 自动测试

```powershell
./scripts/build.ps1       # 后端测试、覆盖率、打包；前端单元测试与构建
./scripts/start.ps1       # 浏览器测试需要正在运行的后端
./scripts/test.ps1        # 完整构建检查及 Chrome 浏览器端到端测试
```

后端测试使用独立内存数据库，不修改本地演示数据库。浏览器测试会创建标记为“E2E”的演示预约和合成校外账号。浏览器工具默认使用本机 Chrome；可用 `E2E_BROWSER=msedge` 改用 Edge。

测试入口：

- `backend/src/test/java/cn/instrumenthub/HubIntegrationTest.java`
- `frontend/src/utils.test.js`
- `frontend/e2e/platform.spec.js`
- `scripts/load-test.mjs`：针对独立 8081 内存数据库实例的 HTTP 并发压测。
- [测试报告](docs/TEST-REPORT.md)：实测结果和验收边界。

## 已实现功能

仪器检索及14天半小时时段、三步预约及草稿、审批、重叠时段冲突与候补确认、扫码/手工签到、实际机时计费、线下核销及冲正记录、加密报告上传下载、培训报名初审与考试、资质撤销及到期提醒、违约扣分与申诉、即时/计划维保、多口径报表及CSV导出、站内消息、仪器建档和批量导入、外部台账去重同步、审计及对接投递队列。

校内统一认证、微信模板消息和既有平台回写提供可配置的网关接口与失败重试。生产机构的协议、凭据及实名审核规则需要由部署方配置；本地不伪造远端投递成功。

## 目录

```text
backend/       Spring Boot 3.2、MyBatis-Plus/MyBatis、Spring Security、JWT
frontend/      Vue 3、Vite、Element Plus、Vant、ECharts
miniprogram/   原生微信小程序客户端
scripts/       构建、启动、停止、测试、压测和备份
docs/          设计、操作、对接、需求追踪、测试报告和界面截图
compose.yml    MySQL、Redis、MinIO、后端、Nginx 的部署编排
```

生产部署和备份见 [运维手册](docs/OPERATIONS.md)，操作流程见 [使用说明](docs/USER-GUIDE.md)，需求覆盖及差异见 [需求追踪](docs/TRACEABILITY.md)。

当前交付可用于本地运行、课程演示与后续集成开发。性能目标、正式微信发布、真实机构系统联调、等保测评和长期可用性不能仅凭本地自动测试认定验收通过，具体以测试报告为准。
