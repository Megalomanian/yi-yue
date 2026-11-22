from pathlib import Path
import json, re, shutil
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
evidence=root/'docs/test-results'
evidence.mkdir(parents=True,exist_ok=True)
suite=ET.parse(root/'backend/target/surefire-reports/TEST-cn.instrumenthub.HubIntegrationTest.xml').getroot()
coverage=ET.parse(root/'backend/target/site/jacoco/jacoco.xml').getroot()
metrics={c.attrib['type']:{'covered':int(c.attrib['covered']),'missed':int(c.attrib['missed'])} for c in coverage.findall('counter')}
for v in metrics.values(): v['percent']=round(v['covered']/(v['covered']+v['missed'])*100,2)
browser=json.loads((root/'frontend/test-results/results.json').read_text(encoding='utf-8'))
loadfile=evidence/'http-load.json'
load=json.loads(loadfile.read_text(encoding='utf-8')) if loadfile.exists() else {}
stdout='\n'.join(c.text or '' for c in suite.findall('.//system-out'))
capacity=re.search(r'CAPACITY: instruments=(\d+), reservations=(\d+), report_ms=(\d+)',stdout)
concurrent=re.findall(r'CONCURRENCY: requests=(\d+), occupied_reservations=(\d+), waitlisted=(\d+), p95_ms=(\d+)',stdout)
summary={'backend':dict(suite.attrib),'coverage':metrics,'browser':browser['stats'],'http_load':load,'capacity':capacity.groups() if capacity else None,'service_concurrency':concurrent}
(evidence/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(root/'backend/target/surefire-reports/TEST-cn.instrumenthub.HubIntegrationTest.xml',evidence/'backend-junit.xml')
shutil.copy2(root/'backend/target/site/jacoco/jacoco.xml',evidence/'jacoco.xml')
shutil.copy2(root/'frontend/test-results/results.json',evidence/'browser.json')
cases='\n'.join(f'| {c.attrib["name"]} | {"失败" if c.find("failure") is not None or c.find("error") is not None else "通过"} | {c.attrib.get("time","—")} s |' for c in suite.findall('testcase'))
race='\n'.join(f'| {n} | {occupied} | {waiting} | {p95} ms |' for n,occupied,waiting,p95 in concurrent)
report=f'''# 系统自动测试报告

测试日期：2026-11-11（Asia/Shanghai）。结果来自实际运行的JUnit、JaCoCo、Vitest和Playwright输出。

## 结果

- 后端集成测试：{suite.attrib['tests']} 项，失败 {suite.attrib['failures']}，错误 {suite.attrib['errors']}，跳过 {suite.attrib['skipped']}。
- 后端行覆盖率：{metrics['LINE']['percent']}%；指令覆盖率：{metrics['INSTRUCTION']['percent']}%；分支覆盖率：{metrics['BRANCH']['percent']}%。
- 前端单元测试：4项（Vitest，费用估算、日期金额和状态标签）。
- 浏览器端到端：通过 {browser['stats']['expected']} 项，失败 {browser['stats']['unexpected']} 项，跳过 {browser['stats']['skipped']} 项。
- 前后端生产构建已执行；OpenAPI和界面截图随交付提供。

## 环境与隔离

Windows、Java 21、Spring Boot 3.2.12、H2 2.3.232、Node 24、Vue 3、Chrome。后端测试使用独立H2内存数据库；浏览器操作本地演示服务；HTTP压测使用8081独立内存实例，不向真实机构平台发送数据。测试数据全部合成。

MySQL8、Redis7、MinIO容器配置通过 `docker compose --env-file .env.example config --quiet` 校验。Docker Desktop引擎在本环境未就绪，未执行容器端到端验收。

## 并发与容量

Service层并发测试（带JaCoCo，单位为一次完整提交事务）：

| 并发请求 | 有效占用预约 | 候补预约 | P95 |
|---|---|---|---|
{race}

实际HTTP压测：{load.get('requests','未执行')}请求，状态统计 `{json.dumps(load.get('counts',{}),ensure_ascii=False)}`，P95为{load.get('p95_ms','—')}ms，是否超卖：{load.get('oversold','未验证')}。800ms目标是否达到：{load.get('target_met','未验证')}。HTTP数据是端到端请求耗时，不能与Service单元内耗时混为一谈。

容量测试：{capacity.group(1) if capacity else '—'}台仪器、{capacity.group(2) if capacity else '—'}条完成预约，报表生成{capacity.group(3) if capacity else '—'}ms，核对总机时、对外机时和服务人次数值一致。该测试不是五年百万数据或预约与报表混合负载验收。

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
{cases}

## 结论与未通过项

功能、权限、状态一致性和本地浏览器自动测试的结果见上述计数。500并发同一资源未超卖；当前HTTP P95仍超过800ms，NFR-01性能目标尚未验收通过。测试报告保留这一结果，不用Service耗时或拒绝请求替代实际成功提交性能。

正式SSO/微信/既有平台联调、Redis锁/MinIO服务验证、原生微信真机发布、HTTPS入口、等保测评、年度可用率与恢复演练尚未在此环境验证。完整差异见TRACEABILITY.md。

证据：`docs/test-results/`中的JUnit XML、JaCoCo XML、浏览器JSON、HTTP负载JSON和汇总JSON；截图位于`docs/screenshots/`。完整JaCoCo HTML在`backend/target/site/jacoco/index.html`，Playwright HTML在`frontend/playwright-report/index.html`。
'''
(root/'docs/TEST-REPORT.md').write_text(report,encoding='utf-8')
print(json.dumps({'backend_tests':suite.attrib['tests'],'backend_errors':suite.attrib['errors'],'line_coverage':metrics['LINE']['percent'],'browser':browser['stats'],'http_p95_ms':load.get('p95_ms')},ensure_ascii=False,indent=2))
