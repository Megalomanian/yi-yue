package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.*;

import java.time.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class SeedData implements ApplicationRunner {
  private final StoreMapper db;
  private final BCryptPasswordEncoder passwords;
  private final Clock clock;
  private final boolean demo;
  private final String password, bootstrap;

  public SeedData(
      StoreMapper db,
      BCryptPasswordEncoder passwords,
      Clock clock,
      @Value("${app.demo}") boolean demo,
      @Value("${app.seed-password}") String password,
      @Value("${app.bootstrap-password}") String bootstrap) {
    this.db = db;
    this.passwords = passwords;
    this.clock = clock;
    this.demo = demo;
    this.password = password;
    this.bootstrap = bootstrap;
  }

  @Override
  @Transactional
  public void run(ApplicationArguments args) {
    if (db.one("SELECT id FROM app_user LIMIT 1") != null) return;
    if (!demo) {
      if (bootstrap.length() < 16)
        throw new IllegalStateException("首次生产启动必须设置至少16位 BOOTSTRAP_PASSWORD");
      create("admin", "平台管理员", "ADMIN", 1, bootstrap);
      return;
    }
    create("admin", "平台管理员", "ADMIN", 1, password);
    create("manager", "陈老师", "MANAGER", 1, password);
    create("student", "林同学", "USER", 1, password);
    create("student2", "周同学", "USER", 1, password);
    create("external", "企业送样人", "EXTERNAL", 1, password);
    create("department", "主管部门", "DEPARTMENT", 1, password);
    create("manager2", "另一机组负责人", "MANAGER", 2, password);
    String[][] instruments = {
      {"IY-001", "场发射扫描电子显微镜", "ZEISS Sigma 300", "电子显微", "材料表征机组", "A楼 201"},
      {"IY-002", "高效液相色谱仪", "Agilent 1260 Infinity II", "色谱分析", "化学分析机组", "B楼 108"},
      {"IY-003", "X射线衍射仪", "Bruker D8 Advance", "结构分析", "材料表征机组", "A楼 205"},
      {"IY-004", "紫外可见分光光度计", "Shimadzu UV-2600", "光谱分析", "化学分析机组", "B楼 102"}
    };
    int[] prices = {280, 160, 220, 80};
    int[] values = {1800000, 650000, 850000, 280000};
    for (int j = 0; j < instruments.length; j++) {
      var a = instruments[j];
      long iid =
          db.insert(
              "instrument",
              fields(
                  "code",
                  a[0],
                  "name",
                  a[1],
                  "model",
                  a[2],
                  "category",
                  a[3],
                  "group_id",
                  1,
                  "department",
                  a[4],
                  "location",
                  a[5],
                  "price",
                  prices[j],
                  "external_price",
                  prices[j] * 2,
                  "asset_value",
                  values[j],
                  "status",
                  "Open",
                  "source",
                  "local",
                  "open_hour",
                  8,
                  "close_hour",
                  20));
      for (String username : new String[] {"student", "student2", "external"}) {
        long uid = id(db.one("SELECT id FROM app_user WHERE username=?", username), "id");
        db.insert(
            "qualification",
            fields(
                "user_id",
                uid,
                "instrument_id",
                iid,
                "expires_at",
                LocalDateTime.now(clock).plusYears(1).withNano(0).toString()));
        db.insert(
            "training_enrollment", fields("user_id", uid, "instrument_id", iid, "approved", true));
      }
    }
  }

  private void create(String username, String name, String role, long group, String secret) {
    db.insert(
        "app_user",
        fields(
            "username",
            username,
            "name",
            name,
            "role",
            role,
            "group_id",
            group,
            "department",
            "演示单位",
            "password",
            passwords.encode(secret),
            "approved",
            true,
            "consent",
            true));
  }
}
