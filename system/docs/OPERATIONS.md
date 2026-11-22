# 部署与运维

## 开发 / 演示

1. 安装 JDK 21、Maven 3.9、Node.js 22/24、Chrome。当前工作区 `.tools` 已有 JDK/Maven；移动到新电脑时自行安装并设置 `JAVA_HOME`。
2. 在 system 目录执行 `./scripts/build.ps1`。数据库迁移和演示数据会在首次启动自动生成。
3. 执行 `./scripts/start.ps1`。脚本后台启动进程，保存PID和日志到 `data/runtime/`，监听127.0.0.1。
4. 浏览 <http://localhost:5173>。后端完整启动约需10—20秒。
5. 使用 `./scripts/stop.ps1` 停止本项目进程。脚本核对命令行所属目录，避免误停复用PID的其他进程。

运行包复制到 runtime 后再启动，后续构建不会因Windows占用JAR而失败。更新后执行 stop、start 即可加载新包。不要在应用运行时删除 H2 数据文件。

## Docker 生产部署

```powershell
Copy-Item .env.example .env
# 编辑 .env：为数据库、Redis、MinIO、JWT、加密和管理员设置独立随机密钥
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d --build
docker compose ps
```

首次 `DEMO_MODE=false` 启动只创建 admin 账号，密码来自至少16字符的 `BOOTSTRAP_PASSWORD`。此后该变量不会重置已有账号密码。生产模式拒绝内置演示 JWT 和加密密钥。

网页默认仅绑定 `127.0.0.1:8088`，由学校入口反向代理提供域名、HTTPS及证书；MySQL、Redis和MinIO不向宿主机开放端口。HTTPS是部署方必须配置的入口能力，compose本身不包含学校证书。

资源上限约为 MySQL768MB、Redis192MB、MinIO512MB、后端1200MB、Nginx128MB。需要额外预留操作系统及容器运行时空间。镜像已固定版本；正式上线前应对依赖和镜像执行漏洞扫描，并按组织维护策略升级。

本次工作区的 Docker Desktop 引擎未能就绪，compose可执行配置检查，但未据此宣称整套容器已启动通过。

## 重要配置

| 配置 | 用途 |
|---|---|
| DB_URL / DB_USER / DB_PASSWORD | 数据库连接 |
| DEMO_MODE | 是否启用演示种子数据与校内账号本地密码 |
| JWT_SECRET | 至少32字节的JWT签名密钥 |
| ENCRYPTION_KEY | 数据加密主密钥；丢失后无法恢复已有加密内容 |
| REDIS_LOCK / REDIS_HOST / REDIS_PASSWORD | 生产资源锁 |
| STORAGE=local 或 minio | 报告存储后端 |
| MINIO_ENDPOINT / MINIO_USER / MINIO_PASSWORD | 对象存储接入 |
| CONFIRMATION_MINUTES | 候补补位确认期限，默认5分钟 |
| SSO_EXCHANGE_URL / SSO_SERVICE_TOKEN | 统一认证票据交换网关 |
| NOTIFICATION_GATEWAY_URL / UPSTREAM_GATEWAY_URL / GATEWAY_TOKEN | 外部消息及机时回写网关 |

## 备份与恢复

Linux环境可运行 `scripts/backup.sh`，它对数据库单事务快照和对象文件打包后使用 GPG 公钥加密。部署方须准备 `BACKUP_RECIPIENT`，并以 cron 定时执行；脚本不会擅自创建系统计划任务或删除旧备份。密钥保存在独立受控介质，切勿只与数据存于同一磁盘。

推荐每日全量、保留30天，另启用MySQL binlog做增量。更改审计或报告留存期限前，应由机构确认合规规则。当前代码不清除业务和审计历史。

恢复演练步骤：停止应用写入；解密SQL并导入独立测试数据库；还原MinIO对象文件；配置与备份一致的ENCRYPTION_KEY；启动相同版本应用；验证健康检查、登录、预约、报告SHA-256校验和费用总额；记录恢复起止时间。必须先在隔离数据库演练，不能将未验证备份覆盖生产库。

## 故障处理

- 登录401：确认账号密码、JWT是否过期；清除会话后重新登录。
- 预约409：刷新时段。生产Redis锁竞争也会返回409，允许重试。
- 预约503：检查Redis连接；系统不会在锁服务故障时静默接受预约。
- 报告读取失败：检查MinIO或本地文件、加密密钥和对象校验值。
- 外部通知失败：用户仍有站内信；管理员在“系统对接”查看Retry/Failed并重试。服务中断后遗留Sending可人工重试，接收方须按Idempotency-Key去重。
- 首次启动报数据库迁移错误：保留原库，检查Flyway记录与应用版本；不要直接跳过迁移校验。

年可用率99.5%、30分钟恢复、正式等保二级测评需要持续运维数据与恢复演练，本地测试不替代这些证明。
