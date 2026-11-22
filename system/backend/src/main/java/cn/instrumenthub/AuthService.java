package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.*;

import io.jsonwebtoken.Jwts;
import java.time.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import javax.crypto.SecretKey;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {
  private final StoreMapper db;
  private final BCryptPasswordEncoder passwords;
  private final SecretKey key;
  private final Clock clock;
  private final CryptoStorage crypto;
  private final Map<String, Attempt> attempts = new ConcurrentHashMap<>();

  private record Attempt(int count, Instant since) {}

  private final boolean demo;

  public AuthService(
      StoreMapper db,
      BCryptPasswordEncoder passwords,
      SecretKey key,
      Clock clock,
      CryptoStorage crypto,
      @org.springframework.beans.factory.annotation.Value("${app.demo}") boolean demo) {
    this.db = db;
    this.passwords = passwords;
    this.key = key;
    this.clock = clock;
    this.crypto = crypto;
    this.demo = demo;
  }

  @Transactional
  public synchronized Map<String, Object> login(Map<String, Object> b, String ip) {
    String username = HubService.text(b, "username", 100),
        password = HubService.text(b, "password", 72);
    String attemptKey = ip + ":" + username;
    Instant cutoff = clock.instant().minusSeconds(900);
    attempts.entrySet().removeIf(e -> e.getValue().since().isBefore(cutoff));
    Attempt a = attempts.get(attemptKey);
    if (a != null && a.count() >= 5) throw new Problem(429, "登录失败次数过多，请15分钟后再试");
    var u = db.one("SELECT * FROM app_user WHERE username=?", username);
    if (u == null || !passwords.matches(password, str(u, "password"))) {
      attempts.put(
          attemptKey,
          new Attempt(a == null ? 1 : a.count() + 1, a == null ? clock.instant() : a.since()));
      throw new Problem(401, "账号或密码错误");
    }
    if (!demo && List.of("USER", "MANAGER", "DEPARTMENT").contains(str(u, "role")))
      throw new Problem(403, "校内用户请通过统一身份认证登录");
    attempts.remove(attemptKey);
    db.insert(
        "audit_log",
        fields(
            "actor_id",
            id(u, "id"),
            "action",
            "auth.login",
            "object_id",
            id(u, "id"),
            "created_at",
            LocalDateTime.now(clock).withNano(0).toString(),
            "source_ip",
            ip));
    return session(u);
  }

  public Map<String, Object> session(Map<String, Object> u) {
    String token =
        Jwts.builder()
            .subject(String.valueOf(id(u, "id")))
            .issuedAt(Date.from(clock.instant()))
            .expiration(Date.from(clock.instant().plusSeconds(7200)))
            .signWith(key)
            .compact();
    return fields("token", token, "user", safe(u));
  }

  @Transactional
  public Map<String, Object> register(Map<String, Object> b) {
    String username = HubService.text(b, "username", 100),
        password = HubService.text(b, "password", 72);
    if (!username.matches("[a-zA-Z0-9_.@-]{4,100}") || password.length() < 10)
      throw new Problem(400, "账号至少4位，密码至少10位");
    if (!Boolean.TRUE.equals(b.get("consent"))) throw new Problem(400, "请先阅读并同意个人信息用途说明");
    long uid =
        db.insert(
            "app_user",
            fields(
                "username",
                username,
                "password",
                passwords.encode(password),
                "name",
                HubService.text(b, "name", 100),
                "department",
                HubService.text(b, "department", 100),
                "role",
                "EXTERNAL",
                "approved",
                false,
                "consent",
                true));
    db.insert(
        "identity_review",
        fields(
            "user_id",
            uid,
            "identity_info",
            crypto.seal(HubService.text(b, "identity_info", 500)),
            "contact",
            crypto.seal(HubService.text(b, "contact", 100))));
    return fields("id", uid, "message", "注册成功，等待管理员实名审核");
  }

  public static Map<String, Object> safe(Map<String, Object> u) {
    var out = new LinkedHashMap<>(u);
    out.remove("password");
    return out;
  }
}
