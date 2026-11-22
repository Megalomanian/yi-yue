# 对接契约

本项目不包含学校、微信或既有平台的真实密钥。以下网关负责把机构协议转换为平台契约；未配置时统一认证返回503，外部投递保持Pending，站内业务正常保存。

## 统一认证

前端可配置 `VITE_SSO_LOGIN_URL`，机构登录成功后回跳 `https://仪约域名/?ticket=一次性票据`。网页会立即从地址栏移除票据，再发送 `POST /api/auth/sso-ticket`。

后端使用 `Authorization: Bearer SSO_SERVICE_TOKEN` 向 `SSO_EXCHANGE_URL` 发送：

```json
{"ticket":"single-use-ticket"}
```

成功响应必须包含：

```json
{"subject":"唯一学工号","name":"姓名","department":"院系","role":"USER","group_id":1}
```

允许角色仅USER、MANAGER、DEPARTMENT。网关负责验证票据签名、受众、一次性使用和期限，不能把客户端自己声明的角色直接回传。平台保留姓名、院系、机组及身份类型，不保存校内用户密码。subject映射为`sso:subject`本地唯一账号。

生产必须使用HTTPS和受控网关访问。角色或机组变更以可信网关返回为准，平台不会允许SSO签发ADMIN。

## 微信消息及既有平台回写

后端每分钟读取待投递事件。POST至对应网关，附带 `Authorization: Bearer GATEWAY_TOKEN` 和 `Idempotency-Key: iy-event-事件号`。2xx视为成功，失败按指数退避重试，最多8次后Failed，管理员可重试。

微信网关负载：

```json
{"notification_id":123,"user_id":3,"message":"预约 #100 审批通过"}
```

网关负责平台用户与OpenID绑定、用户订阅同意、微信access_token、模板ID和微信错误码处理。平台当前未提供完整微信身份绑定与订阅设置界面，正式微信投递尚需对接该网关。

既有平台结算事件：

```json
{"reservation_id":100,"instrument_id":1,"hours":0.5,"amount":140.00}
```

一期财务采用 `/api/bills/export` CSV离线核销，不接收支付回调。网关回写失败不会撤销已完成的本地结算。

## 外部仪器同步

管理员调用 `POST /api/integrations/instruments`，请求为与仪器导入相同的JSON数组。数据源标为external；重复code更新已有外部仪器；如同code存在本地仪器，整批事务失败并要求核对。当前提供接收接口，不自动拉取学校既有平台；部署方按实际鉴权协议调用。

## OpenAPI

运行时由Springdoc生成 `/v3/api-docs`。部署交付中的 `docs/openapi.json` 是本次最终运行版本快照。业务JSON响应直接返回资源或集合，错误统一返回message和HTTP状态；此处采用资源型REST响应，与SRS中统一code/message/data外壳约定不同。
