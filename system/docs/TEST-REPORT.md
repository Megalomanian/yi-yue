# 系统自动测试报告

测试日期：2026-11-11（Asia/Shanghai）。结果来自实际运行的JUnit、JaCoCo、Vitest和Playwright输出。

## 结果

- 后端集成测试：37 项，失败 0，错误 0，跳过 0。
- 后端行覆盖率：83.54%；指令覆盖率：81.96%；分支覆盖率：66.04%。
- 前端单元测试：4项（Vitest，费用估算、日期金额和状态标签）。
- 浏览器端到端：通过 6 项，失败 0 项，跳过 0 项。
- 前后端生产构建已执行；OpenAPI和界面截图随交付提供。

## 环境与隔离

Windows、Java 21、Spring Boot 3.2.12、H2 2.3.232、Node 24、Vue 3、Chrome。后端测试使用独立H2内存数据库；浏览器操作本地演示服务；HTTP压测使用8081独立内存实例，不向真实机构平台发送数据。测试数据全部合成。

MySQL8、Redis7、MinIO容器配置通过 `docker compose --env-file .env.example config --quiet` 校验。Docker Desktop引擎在本环境未就绪，未执行容器端到端验收。

## 并发与容量

Service层并发测试（带JaCoCo，单位为一次完整提交事务）：

| 并发请求 | 有效占用预约 | 候补预约 | P95 |
|---|---|---|---|
| 100 | 1 | 99 | 317 ms |
| 500 | 1 | 499 | 1021 ms |

实际HTTP压测：500请求，状态统计 `{"Waitlisted": 499, "Pending": 1}`，P95为2225.68ms，是否超卖：False。800ms目标是否达到：False。HTTP数据是端到端请求耗时，不能与Service单元内耗时混为一谈。

容量测试：500台仪器、200000条完成预约，报表生成3964ms，核对总机时、对外机时和服务人次数值一致。该测试不是五年百万数据或预约与报表混合负载验收。

## 浏览器覆盖

1. 搜索仪器、选择时段、填写样品、提交预约、切换机组批准、用户取消。
2. 学习课程、提交考试、发证消息、标记已读。
3. 切换统计口径、渲染ECharts、下载并读取CSV。
4. 匿名访问、普通用户越权和跨机组管理被拒绝。
5. 校外注册在审核前被限制，管理员批准后放行。
6. 390px移动视口布局、底部导航和无横向溢出。

## 测试中修复的问题

- 修复本地H2旧版的并发自增主键冲突，升级至2.3.232，并加入500并发草稿创建回归。问题与[H2官方Issue #3950](https://github.com/h2database/h2database/issues/3950)的场景一致。
- 候补采用提交序号，避免提前创建草稿抢占候补顺序。
- 修复报表导出表达式在Vue模板中无法调用URLSearchParams的问题。
- 为报表生成与导出增加等待状态；移动布局测试等待实际重排后断言。
- 更新Playwright以兼容当前Node运行环境；生产构建移除未使用的ECharts模块。
- 本地启动复制运行JAR，解决Windows运行中构建无法替换文件的问题。

## 后端用例明细

| 测试方法 | 结果 | 耗时 |
|---|---|---|
| qualificationExpiryAndUpcomingUseNotifyOnce | 通过 | 2.289 s |
| conflictAndFifoPromotionRequireConfirmation | 通过 | 0.138 s |
| threeStatisticalCalibersAndMaintenanceDenominator | 通过 | 0.14 s |
| trainingRequiresPreapprovalAndFailedExamDoesNotIssue | 通过 | 0.06 s |
| integrationQueuePersistsIndependentlyOfRemoteAvailability | 通过 | 0.068 s |
| checkinRejectsWrongInstrumentEarlyLateAndDuplicate | 通过 | 0.069 s |
| coreLifecycleChargesActualTimeAndRetainsSnapshot | 通过 | 0.059 s |
| concurrentDraftCreationIsSafe | 通过 | 0.219 s |
| maintenanceCancelsWithoutPenaltyAndRestores | 通过 | 0.099 s |
| unconfiguredSsoFailsClearlyAndSyncDeduplicates | 通过 | 0.041 s |
| ssoGatewayAndDeliveryRetryContract | 通过 | 0.719 s |
| paginatedHistoryRetainsOwnershipAndDateFilters | 通过 | 0.058 s |
| rejectsMissingExpiredRevokedQualificationAndLowCredit | 通过 | 0.039 s |
| csvPreventsSpreadsheetFormulaInjection | 通过 | 0.019 s |
| overtimePenaltyAndDamageAreAudited | 通过 | 0.064 s |
| waitlistOrderUsesSubmissionNotDraftCreation | 通过 | 0.065 s |
| confirmationTimeoutMovesToNextCandidate | 通过 | 0.062 s |
| reportOnTwoHundredThousandReservations | 通过 | 14.119 s |
| notificationReadCannotChangeAnotherUsersMessage | 通过 | 7.359 s |
| overlappingSlotsConflictButAdjacentSlotsDoNot | 通过 | 0.029 s |
| crossGroupAndOwnershipAuthorization | 通过 | 0.026 s |
| billingAdjustmentsPreserveOriginalAndRequireReason | 通过 | 0.029 s |
| maintenanceCannotEraseActiveUsage | 通过 | 0.022 s |
| rejectRequiresReasonAndReleasesWaitlist | 通过 | 0.026 s |
| sensitiveFieldsAreEncryptedAtRest | 通过 | 0.016 s |
| concurrentSubmissionsNeverOversell | 通过 | 0.401 s |
| jwtAuthenticationAndHttpAuthorization | 通过 | 0.628 s |
| bulkImportIsAtomicAndExternalRecordsAreReadonly | 通过 | 0.266 s |
| fiveHundredConcurrentSubmissionsNeverOversell | 通过 | 1.326 s |
| unsafeAndMismatchedFilesAreRejected | 通过 | 0.041 s |
| noShowPenaltyIsIdempotentAndAppealRestoresOnce | 通过 | 0.019 s |
| scheduledMaintenanceBlocksOnlyPlannedWindowAndRestores | 通过 | 0.02 s |
| fileEncryptionOwnershipAndIntegrity | 通过 | 0.034 s |
| externalRegistrationRequiresConsentAndReview | 通过 | 0.162 s |
| dateWindowAndHalfHourValidation | 通过 | 0.015 s |
| externalPriceAndFinanceExport | 通过 | 0.018 s |
| draftEditDeleteAndSubmissionPermissions | 通过 | 0.011 s |

## 结论与未通过项

功能、权限、状态一致性和本地浏览器自动测试的结果见上述计数。500并发同一资源未超卖；当前HTTP P95仍超过800ms，NFR-01性能目标尚未验收通过。测试报告保留这一结果，不用Service耗时或拒绝请求替代实际成功提交性能。

正式SSO/微信/既有平台联调、Redis锁/MinIO服务验证、原生微信真机发布、HTTPS入口、等保测评、年度可用率与恢复演练尚未在此环境验证。完整差异见TRACEABILITY.md。

证据：`docs/test-results/`中的JUnit XML、JaCoCo XML、浏览器JSON、HTTP负载JSON和汇总JSON；截图位于`docs/screenshots/`。完整JaCoCo HTML在`backend/target/site/jacoco/index.html`，Playwright HTML在`frontend/playwright-report/index.html`。
