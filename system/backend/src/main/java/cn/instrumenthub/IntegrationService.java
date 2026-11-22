package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.*;

import java.net.http.HttpClient;
import java.time.Duration;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

/** Gateways adapt institution-specific SSO, WeChat templates and legacy platform contracts. */
@Service
public class IntegrationService {
  private final HubService hub;
  private final StoreMapper db;
  private final AuthService auth;
  private final BCryptPasswordEncoder passwords;
  private final String ssoUrl, ssoToken, notificationUrl, upstreamUrl, gatewayToken;
  private final RestClient client;

  public IntegrationService(
      HubService hub,
      StoreMapper db,
      AuthService auth,
      BCryptPasswordEncoder passwords,
      @Value("${app.sso-url}") String ssoUrl,
      @Value("${app.sso-token}") String ssoToken,
      @Value("${app.notification-gateway}") String notificationUrl,
      @Value("${app.upstream-gateway}") String upstreamUrl,
      @Value("${app.gateway-token}") String gatewayToken) {
    this.hub = hub;
    this.db = db;
    this.auth = auth;
    this.passwords = passwords;
    this.ssoUrl = ssoUrl;
    this.ssoToken = ssoToken;
    this.notificationUrl = notificationUrl;
    this.upstreamUrl = upstreamUrl;
    this.gatewayToken = gatewayToken;
    var factory =
        new JdkClientHttpRequestFactory(
            HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build());
    factory.setReadTimeout(Duration.ofSeconds(5));
    client = RestClient.builder().requestFactory(factory).build();
  }

  @Transactional
  @SuppressWarnings("unchecked")
  public Object sso(Map<String, Object> body) {
    if (ssoUrl.isBlank() || ssoToken.isBlank()) throw new Problem(503, "统一认证尚未配置，请联系管理员");
    Map<String, Object> identity;
    try {
      identity =
          client
              .post()
              .uri(ssoUrl)
              .header("Authorization", "Bearer " + ssoToken)
              .body(fields("ticket", HubService.text(body, "ticket", 2000)))
              .retrieve()
              .body(Map.class);
    } catch (Exception e) {
      throw new Problem(401, "统一认证票据无效或认证服务暂不可用");
    }
    if (identity == null) throw new Problem(401, "统一认证未返回身份");
    String subject = HubService.text(identity, "subject", 90),
        name = HubService.text(identity, "name", 100),
        department = HubService.text(identity, "department", 100),
        role = str(identity, "role");
    if (!List.of("USER", "MANAGER", "DEPARTMENT").contains(role))
      throw new Problem(403, "统一认证角色不在允许范围");
    long group = HubService.number(identity, "group_id");
    if (group < 1) throw new Problem(400, "统一认证缺少有效机组");
    var u = db.one("SELECT * FROM app_user WHERE username=?", "sso:" + subject);
    if (u == null) {
      long uid =
          db.insert(
              "app_user",
              fields(
                  "username",
                  "sso:" + subject,
                  "name",
                  name,
                  "department",
                  department,
                  "role",
                  role,
                  "group_id",
                  group,
                  "password",
                  passwords.encode(UUID.randomUUID().toString()),
                  "approved",
                  true,
                  "consent",
                  true));
      u = hub.user(uid);
    } else {
      db.update(
          "UPDATE app_user SET name=?,department=?,role=?,group_id=? WHERE id=?",
          name,
          department,
          role,
          group,
          id(u, "id"));
      u = hub.user(id(u, "id"));
    }
    hub.audit(id(u, "id"), "auth.sso", id(u, "id"));
    return auth.session(u);
  }

  public Object status(Map<String, Object> u) {
    hub.role(u, "ADMIN");
    return fields(
        "sso_configured",
        !ssoUrl.isBlank(),
        "wechat_gateway_configured",
        !notificationUrl.isBlank(),
        "upstream_configured",
        !upstreamUrl.isBlank(),
        "events",
        db.list(
            "SELECT id,channel,object_id,status,attempts,next_at,last_error FROM integration_event"
                + " ORDER BY id DESC LIMIT 200"));
  }

  @Transactional
  public Object sync(Map<String, Object> u, List<Map<String, Object>> records) {
    hub.role(u, "ADMIN");
    if (records.size() > 500) throw new Problem(400, "单批同步最多500台");
    List<Long> ids = new ArrayList<>();
    for (var b : records) {
      String code = HubService.text(b, "code", 50);
      var existing = db.one("SELECT * FROM instrument WHERE code=?", code);
      long iid;
      if (existing == null) {
        iid = hub.saveInstrument(u, b, null);
        db.update("UPDATE instrument SET source='external' WHERE id=?", iid);
      } else {
        if (!"external".equals(str(existing, "source")))
          throw new Problem(409, "外部编号与本地台账冲突，请先人工核对");
        iid = id(existing, "id");
        hub.lockInstrument(iid);
        db.update("UPDATE instrument SET source='local' WHERE id=?", iid);
        hub.saveInstrument(u, b, iid);
        db.update("UPDATE instrument SET source='external' WHERE id=?", iid);
      }
      ids.add(iid);
    }
    hub.audit(id(u, "id"), "integration.sync", 0);
    return ids;
  }

  @Scheduled(
      fixedDelayString = "${app.gateway-ms:60000}",
      initialDelayString = "${app.gateway-ms:60000}")
  public void deliver() {
    // Each delivery carries a stable idempotency key; gateways must deduplicate it.
    for (var e :
        db.list(
            "SELECT * FROM integration_event WHERE status IN ('Pending','Retry') AND next_at<=?"
                + " ORDER BY id LIMIT 50",
            hub.now().toString())) {
      String endpoint = "notification".equals(str(e, "channel")) ? notificationUrl : upstreamUrl;
      if (endpoint.isBlank()) continue;
      long eid = id(e, "id"), attempts = id(e, "attempts") + 1;
      if (db.update(
              "UPDATE integration_event SET status='Sending' WHERE id=? AND status IN"
                  + " ('Pending','Retry')",
              eid)
          != 1) continue;
      try {
        client
            .post()
            .uri(endpoint)
            .header("Authorization", "Bearer " + gatewayToken)
            .header("Idempotency-Key", "iy-event-" + eid)
            .contentType(org.springframework.http.MediaType.APPLICATION_JSON)
            .body(str(e, "payload"))
            .retrieve()
            .toBodilessEntity();
        db.update(
            "UPDATE integration_event SET status='Delivered',attempts=?,last_error=NULL WHERE id=?",
            attempts,
            eid);
      } catch (Exception ex) {
        db.update(
            "UPDATE integration_event SET status=?,attempts=?,next_at=?,last_error=? WHERE id=?",
            attempts >= 8 ? "Failed" : "Retry",
            attempts,
            hub.now().plusMinutes(Math.min(60, 1L << Math.min(attempts, 6))).toString(),
            "远端投递失败，站内消息已保留",
            eid);
      }
    }
  }

  public void retry(Map<String, Object> u, long eid) {
    hub.role(u, "ADMIN");
    db.update(
        "UPDATE integration_event SET status='Pending',attempts=0,next_at=? WHERE id=? AND status"
            + " IN ('Failed','Sending','Retry')",
        hub.now().toString(),
        eid);
    hub.audit(id(u, "id"), "integration.retry", eid);
  }
}
