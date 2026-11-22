package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.*;
import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.*;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(
    properties = {
      "spring.datasource.url=jdbc:h2:mem:test;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1;LOCK_TIMEOUT=30000",
      "app.sweep-ms=3600000",
      "app.local-storage-path=target/test-reports"
    })
@AutoConfigureMockMvc
class HubIntegrationTest {
  static class MutableClock extends Clock {
    volatile Instant instant =
        LocalDateTime.of(2026, 11, 11, 8, 0).atZone(ZoneId.of("Asia/Shanghai")).toInstant();

    public ZoneId getZone() {
      return ZoneId.of("Asia/Shanghai");
    }

    public Clock withZone(ZoneId z) {
      return this;
    }

    public Instant instant() {
      return instant;
    }

    void at(String local) {
      instant = LocalDateTime.parse(local).atZone(getZone()).toInstant();
    }
  }

  @TestConfiguration
  static class Config {
    @Bean
    @Primary
    MutableClock testClock() {
      return new MutableClock();
    }
  }

  @Autowired HubService hub;
  @Autowired StoreMapper db;
  @Autowired MutableClock clock;
  @Autowired MockMvc mvc;
  @Autowired ObjectMapper json;
  @Autowired BCryptPasswordEncoder passwords;
  @Autowired ReportService reports;
  @Autowired CryptoStorage crypto;
  @Autowired IntegrationService integrations;
  @Autowired AuthService auth;
  @Autowired org.springframework.jdbc.core.JdbcTemplate jdbc;
  static String hash;
  Map<String, Object> admin, manager, student, student2, external, department, otherManager;
  long iid;

  @BeforeEach
  void setup() {
    clock.at("2026-11-11T08:00");
    for (String table :
        List.of(
            "submission_sequence",
            "bill_adjustment",
            "integration_event",
            "report_file",
            "bill",
            "slot_claim",
            "violation",
            "notification",
            "audit_log",
            "training",
            "training_enrollment",
            "identity_review",
            "qualification",
            "maintenance",
            "reservation",
            "instrument",
            "app_user")) db.update("DELETE FROM " + table);
    if (hash == null) hash = passwords.encode("TestPassword123!");
    admin = createUser("admin", "ADMIN", 1);
    manager = createUser("manager", "MANAGER", 1);
    student = createUser("student", "USER", 1);
    student2 = createUser("student2", "USER", 1);
    external = createUser("external", "EXTERNAL", 1);
    department = createUser("department", "DEPARTMENT", 1);
    otherManager = createUser("other", "MANAGER", 2);
    iid = hub.saveInstrument(admin, instrument("IY-TEST", 500000), null);
    for (var u : List.of(student, student2, external)) {
      db.insert(
          "qualification",
          fields("user_id", id(u, "id"), "instrument_id", iid, "expires_at", "2027-11-11T08:00"));
      db.insert(
          "training_enrollment",
          fields("user_id", id(u, "id"), "instrument_id", iid, "approved", true));
    }
  }

  Map<String, Object> createUser(String username, String role, long group) {
    long uid =
        db.insert(
            "app_user",
            fields(
                "username",
                username,
                "name",
                username,
                "password",
                hash,
                "role",
                role,
                "group_id",
                group,
                "department",
                "测试单位",
                "approved",
                true));
    return hub.user(uid);
  }

  Map<String, Object> instrument(String code, int value) {
    return fields(
        "code",
        code,
        "name",
        "测试色谱仪",
        "model",
        "Model 1260",
        "category",
        "色谱",
        "location",
        "A101",
        "group_id",
        1,
        "department",
        "测试机组",
        "price",
        100,
        "external_price",
        200,
        "asset_value",
        value,
        "open_hour",
        8,
        "close_hour",
        18);
  }

  Map<String, Object> form(String start, String end) {
    return fields(
        "instrument_id",
        iid,
        "start_at",
        start,
        "end_at",
        end,
        "samples",
        2,
        "project",
        "成分分析",
        "contact",
        "13800000000",
        "settlement",
        "CARD-001");
  }

  long reserve(Map<String, Object> u, String start, String end) {
    long rid = hub.draft(u, form(start, end));
    hub.submit(u, rid);
    return rid;
  }

  long approved(Map<String, Object> u) {
    long rid = reserve(u, "2026-11-11T09:00", "2026-11-11T10:00");
    hub.approve(manager, rid, true, "");
    return rid;
  }

  long completed(Map<String, Object> u) {
    long rid = approved(u);
    clock.at("2026-11-11T09:00");
    hub.checkin(u, rid, iid);
    clock.at("2026-11-11T09:30");
    hub.checkout(manager, rid);
    return rid;
  }

  void problem(int status, Runnable action) {
    assertThatThrownBy(action::run)
        .isInstanceOfSatisfying(Problem.class, p -> assertThat(p.status).isEqualTo(status));
  }

  @Test
  void coreLifecycleChargesActualTimeAndRetainsSnapshot() {
    long rid = approved(student);
    db.update("UPDATE instrument SET price=999 WHERE id=?", iid);
    clock.at("2026-11-11T09:05");
    hub.checkin(student, rid, iid);
    clock.at("2026-11-11T09:35");
    var bill = hub.checkout(manager, rid);
    assertThat(new BigDecimal(str(bill, "amount"))).isEqualByComparingTo("50.00");
    assertThat(new BigDecimal(str(bill, "hours"))).isEqualByComparingTo("0.500000");
    assertThat(str(db.get("reservation", rid), "status")).isEqualTo("Completed");
    problem(409, () -> hub.checkout(manager, rid));
    assertThat(db.list("SELECT * FROM bill")).hasSize(1);
  }

  @Test
  void externalPriceAndFinanceExport() {
    long rid = completed(external);
    var bill = db.one("SELECT * FROM bill WHERE reservation_id=?", rid);
    assertThat(new BigDecimal(str(bill, "amount"))).isEqualByComparingTo("100");
    assertThat(str(bill, "method")).isEqualTo("对公转账");
    assertThat(reports.financeCsv(department)).contains("CARD-001", "成分分析");
    problem(403, () -> reports.financeCsv(student));
  }

  @Test
  void conflictAndFifoPromotionRequireConfirmation() {
    long first = approved(student);
    long second = reserve(student2, "2026-11-11T09:00", "2026-11-11T10:00");
    long third = reserve(external, "2026-11-11T09:00", "2026-11-11T10:00");
    assertThat(str(db.get("reservation", second), "status")).isEqualTo("Waitlisted");
    hub.cancel(student, first);
    var r = db.get("reservation", second);
    assertThat(str(r, "status")).isEqualTo("Approved");
    assertThat(r.get("confirmed")).isEqualTo(false);
    assertThat(str(db.get("reservation", third), "status")).isEqualTo("Waitlisted");
    hub.confirm(student2, second);
    assertThat(db.get("reservation", second).get("confirmed")).isEqualTo(true);
  }

  @Test
  void overlappingSlotsConflictButAdjacentSlotsDoNot() {
    reserve(student, "2026-11-11T09:00", "2026-11-11T10:30");
    long conflict = reserve(student2, "2026-11-11T10:00", "2026-11-11T11:00");
    long adjacent = reserve(external, "2026-11-11T10:30", "2026-11-11T11:00");
    assertThat(str(db.get("reservation", conflict), "status")).isEqualTo("Waitlisted");
    assertThat(str(db.get("reservation", adjacent), "status")).isEqualTo("Pending");
  }

  @Test
  void confirmationTimeoutMovesToNextCandidate() {
    long first = approved(student);
    long second = reserve(student2, "2026-11-11T09:00", "2026-11-11T10:00");
    long third = reserve(external, "2026-11-11T09:00", "2026-11-11T10:00");
    hub.cancel(student, first);
    clock.at("2026-11-11T08:06");
    hub.sweep();
    assertThat(str(db.get("reservation", second), "status")).isEqualTo("Cancelled");
    assertThat(str(db.get("reservation", third), "status")).isEqualTo("Approved");
    assertThat(id(hub.user(id(student2, "id")), "credit")).isEqualTo(100);
  }

  @Test
  void rejectsMissingExpiredRevokedQualificationAndLowCredit() {
    long rid = hub.draft(student, form("2026-11-11T09:00", "2026-11-11T10:00"));
    db.update(
        "UPDATE qualification SET expires_at='2026-11-10T08:00' WHERE user_id=?",
        id(student, "id"));
    problem(403, () -> hub.submit(student, rid));
    db.update(
        "UPDATE qualification SET expires_at='2027-11-10T08:00',revoked=TRUE WHERE user_id=?",
        id(student, "id"));
    problem(403, () -> hub.submit(student, rid));
    db.update("UPDATE qualification SET revoked=FALSE WHERE user_id=?", id(student, "id"));
    db.update("UPDATE app_user SET credit=59 WHERE id=?", id(student, "id"));
    problem(403, () -> hub.submit(student, rid));
    assertThat(str(db.get("reservation", rid), "status")).isEqualTo("Draft");
    assertThat(db.list("SELECT * FROM slot_claim")).isEmpty();
  }

  @Test
  void dateWindowAndHalfHourValidation() {
    for (var pair :
        List.of(
            new String[] {"2026-11-11T07:00", "2026-11-11T08:00"},
            new String[] {"2026-11-25T09:00", "2026-11-25T10:00"},
            new String[] {"2026-11-11T09:15", "2026-11-11T10:00"},
            new String[] {"2026-11-11T17:30", "2026-11-11T18:30"},
            new String[] {"2026-11-11T10:00", "2026-11-11T09:00"}))
      problem(400, () -> hub.draft(student, form(pair[0], pair[1])));
    problem(400, () -> hub.slots(student, iid, LocalDate.of(2026, 11, 25)));
    assertThat(hub.slots(student, iid, LocalDate.of(2026, 11, 12))).hasSize(20);
  }

  @Test
  void crossGroupAndOwnershipAuthorization() {
    long rid = reserve(student, "2026-11-11T09:00", "2026-11-11T10:00");
    problem(403, () -> hub.approve(otherManager, rid, true, ""));
    problem(403, () -> hub.approve(student, rid, true, ""));
    hub.approve(manager, rid, true, "");
    problem(403, () -> hub.cancel(student2, rid));
    problem(403, () -> hub.maintenance(otherManager, iid, fields("reason", "故障")));
    assertThat(hub.reservations(student2)).isEmpty();
    assertThat(hub.reservations(otherManager)).isEmpty();
  }

  @Test
  void noShowPenaltyIsIdempotentAndAppealRestoresOnce() {
    long rid = approved(student);
    clock.at("2026-11-11T09:16");
    hub.sweep();
    hub.sweep();
    assertThat(str(db.get("reservation", rid), "status")).isEqualTo("NoShow");
    assertThat(id(hub.user(id(student, "id")), "credit")).isEqualTo(80);
    assertThat(hub.violations(student)).hasSize(1);
    var v = hub.violations(student).getFirst();
    hub.appeal(student, id(v, "id"), fields("appeal", "设备故障未能签到"));
    hub.appeal(admin, id(v, "id"), fields("action", "resolve", "restore", true));
    assertThat(id(hub.user(id(student, "id")), "credit")).isEqualTo(100);
    problem(
        409, () -> hub.appeal(admin, id(v, "id"), fields("action", "resolve", "restore", true)));
  }

  @Test
  void overtimePenaltyAndDamageAreAudited() {
    long rid = approved(student);
    clock.at("2026-11-11T09:00");
    hub.checkin(student, rid, iid);
    clock.at("2026-11-11T10:16");
    hub.sweep();
    hub.sweep();
    assertThat(id(hub.user(id(student, "id")), "credit")).isEqualTo(90);
    hub.damage(admin, fields("reservation_id", rid, "points", 25, "reason", "已核实样品台损坏"));
    assertThat(id(hub.user(id(student, "id")), "credit")).isEqualTo(65);
    assertThat(hub.violations(student)).hasSize(2);
  }

  @Test
  void checkinRejectsWrongInstrumentEarlyLateAndDuplicate() {
    long rid = approved(student);
    problem(409, () -> hub.checkin(student, rid, iid));
    clock.at("2026-11-11T09:00");
    problem(409, () -> hub.checkin(student, rid, iid + 1));
    hub.checkin(student, rid, iid);
    problem(409, () -> hub.checkin(student, rid, iid));
    problem(409, () -> hub.cancel(student, rid));
  }

  @Test
  void rejectRequiresReasonAndReleasesWaitlist() {
    long rid = reserve(student, "2026-11-11T09:00", "2026-11-11T10:00");
    long next = reserve(student2, "2026-11-11T09:00", "2026-11-11T10:00");
    problem(400, () -> hub.approve(manager, rid, false, ""));
    hub.approve(manager, rid, false, "样品不符合要求");
    assertThat(str(db.get("reservation", rid), "status")).isEqualTo("Rejected");
    assertThat(str(db.get("reservation", next), "status")).isEqualTo("Approved");
  }

  @Test
  void maintenanceCancelsWithoutPenaltyAndRestores() {
    long first = approved(student);
    long second = reserve(student2, "2026-11-11T09:00", "2026-11-11T10:00");
    hub.maintenance(manager, iid, fields("reason", "灯丝检修"));
    for (long rid : List.of(first, second))
      assertThat(str(db.get("reservation", rid), "status")).isEqualTo("Cancelled");
    assertThat(db.list("SELECT * FROM slot_claim")).isEmpty();
    assertThat(id(hub.user(id(student, "id")), "credit")).isEqualTo(100);
    problem(409, () -> hub.draft(student, form("2026-11-11T11:00", "2026-11-11T12:00")));
    hub.maintenance(manager, iid, fields("action", "restore"));
    assertThat(str(db.get("instrument", iid), "status")).isEqualTo("Open");
  }

  @Test
  void maintenanceCannotEraseActiveUsage() {
    long rid = approved(student);
    clock.at("2026-11-11T09:00");
    hub.checkin(student, rid, iid);
    problem(409, () -> hub.maintenance(manager, iid, fields("reason", "维修")));
    assertThat(str(db.get("instrument", iid), "status")).isEqualTo("Open");
  }

  @Test
  void trainingRequiresPreapprovalAndFailedExamDoesNotIssue() {
    db.update("DELETE FROM qualification WHERE user_id=?", id(student, "id"));
    db.update("DELETE FROM training_enrollment WHERE user_id=?", id(student, "id"));
    var e = (Map<String, Object>) hub.enroll(student, iid);
    problem(403, () -> hub.training(student, iid, List.of(1, 0, 1, 2, 0)));
    hub.approveEnrollment(manager, id(e, "id"));
    assertThat(hub.training(student, iid, List.of(0, 1, 0, 1, 1)).get("passed")).isEqualTo(false);
    assertThat(hub.qualifications(student)).isEmpty();
    assertThat(hub.training(student, iid, List.of(1, 0, 1, 2, 0)).get("passed")).isEqualTo(true);
    assertThat(hub.qualifications(student)).hasSize(1);
    hub.revoke(admin, id(hub.qualifications(student).getFirst(), "id"));
    problem(403, () -> hub.training(student, iid, List.of(1, 0, 1, 2, 0)));
  }

  @Test
  void qualificationExpiryAndUpcomingUseNotifyOnce() {
    db.update(
        "UPDATE qualification SET expires_at='2026-11-20T08:00' WHERE user_id=?",
        id(student, "id"));
    approved(student);
    clock.at("2026-11-11T08:40");
    hub.sweep();
    int count = hub.notifications(student).size();
    hub.sweep();
    assertThat(hub.notifications(student)).hasSize(count);
    assertThat(hub.notifications(student).toString()).contains("到期", "即将开始");
  }

  @Test
  void fileEncryptionOwnershipAndIntegrity() throws Exception {
    long rid = completed(student);
    byte[] content = "%PDF-1.7\nprivate test result".getBytes();
    var file =
        (Map<String, Object>)
            reports.upload(
                manager,
                rid,
                new MockMultipartFile("file", "report.pdf", "application/pdf", content));
    long fid = id(file, "id");
    assertThat(reports.download(student, fid).bytes()).isEqualTo(content);
    assertThatThrownBy(() -> reports.download(student2, fid)).isInstanceOf(Problem.class);
    var stored = db.get("report_file", fid);
    byte[] encrypted =
        Files.readAllBytes(Path.of("target/test-reports", str(stored, "object_key")));
    assertThat(encrypted).isNotEqualTo(content);
    db.update("UPDATE report_file SET checksum='tampered' WHERE id=?", fid);
    assertThatThrownBy(() -> reports.download(student, fid)).isInstanceOf(Problem.class);
  }

  @Test
  void unsafeAndMismatchedFilesAreRejected() throws Exception {
    long rid = completed(student);
    assertThatThrownBy(
            () ->
                reports.upload(
                    manager,
                    rid,
                    new MockMultipartFile(
                        "file", "payload.exe", "application/octet-stream", new byte[] {1})))
        .isInstanceOf(Problem.class);
    assertThatThrownBy(
            () ->
                reports.upload(
                    manager,
                    rid,
                    new MockMultipartFile("file", "fake.pdf", "application/pdf", new byte[] {1})))
        .isInstanceOf(Problem.class);
  }

  @Test
  void sensitiveFieldsAreEncryptedAtRest() {
    long rid = reserve(student, "2026-11-11T09:00", "2026-11-11T10:00");
    assertThat(str(db.get("reservation", rid), "contact")).doesNotContain("13800000000");
    assertThat(hub.reservations(student).getFirst().get("contact")).isEqualTo("13800000000");
    assertThat(hub.audits(admin).toString()).doesNotContain("CARD-001", "13800000000");
  }

  @Test
  void threeStatisticalCalibersAndMaintenanceDenominator() {
    completed(external);
    hub.saveInstrument(admin, instrument("LOW", 280000), null);
    hub.saveInstrument(admin, instrument("MID", 450000), null);
    var from = LocalDate.of(2026, 11, 11);
    var stats = hub.statistics(admin, "national", from, from);
    assertThat(stats.get("instruments")).isEqualTo(1);
    assertThat((BigDecimal) stats.get("hours")).isEqualByComparingTo("0.5");
    assertThat((BigDecimal) stats.get("external_hours")).isEqualByComparingTo("0.5");
    assertThat(hub.statistics(admin, "local", from, from).get("instruments")).isEqualTo(3);
    assertThat(hub.statistics(department, "campus", from, from).get("instruments")).isEqualTo(2);
    problem(403, () -> hub.statistics(student, "national", from, from));
    hub.maintenance(manager, iid, fields("reason", "检修"));
    clock.at("2026-11-11T10:30");
    hub.maintenance(manager, iid, fields("action", "restore"));
    assertThat((BigDecimal) hub.statistics(admin, "national", from, from).get("available_hours"))
        .isEqualByComparingTo("9");
  }

  @Test
  void billingAdjustmentsPreserveOriginalAndRequireReason() {
    long rid = completed(student);
    var b = db.one("SELECT * FROM bill WHERE reservation_id=?", rid);
    hub.billAction(
        manager, id(b, "id"), fields("action", "adjust", "adjustment", -10, "reason", "人工复核"));
    var updated = db.get("bill", id(b, "id"));
    assertThat(new BigDecimal(str(updated, "amount"))).isEqualByComparingTo("50");
    assertThat(new BigDecimal(str(updated, "adjustment"))).isEqualByComparingTo("-10");
    problem(
        400,
        () ->
            hub.billAction(
                manager,
                id(b, "id"),
                fields("action", "adjust", "adjustment", -100, "reason", "无效")));
    hub.billAction(manager, id(b, "id"), fields("action", "verify"));
    assertThat(db.get("bill", id(b, "id")).get("verified")).isEqualTo(true);
  }

  @Test
  void draftEditDeleteAndSubmissionPermissions() {
    long rid = hub.draft(student, form("2026-11-11T09:00", "2026-11-11T10:00"));
    problem(403, () -> hub.submit(student2, rid));
    hub.editDraft(student, rid, form("2026-11-11T10:00", "2026-11-11T11:00"));
    assertThat(str(db.get("reservation", rid), "start_at")).isEqualTo("2026-11-11T10:00");
    hub.deleteDraft(student, rid);
    problem(404, () -> db.get("reservation", rid));
  }

  @Test
  void bulkImportIsAtomicAndExternalRecordsAreReadonly() {
    var first = instrument("DUP", 500000);
    assertThatThrownBy(() -> hub.importInstruments(admin, List.of(first, first)))
        .isInstanceOf(org.springframework.dao.DataIntegrityViolationException.class);
    assertThat(db.one("SELECT id FROM instrument WHERE code='DUP'")).isNull();
    db.update("UPDATE instrument SET source='external' WHERE id=?", iid);
    problem(409, () -> hub.saveInstrument(admin, instrument("IY-TEST", 600000), iid));
  }

  @Test
  void concurrentSubmissionsNeverOversell() throws Exception {
    race(100);
  }

  @Test
  void concurrentDraftCreationIsSafe() throws Exception {
    try (var pool = Executors.newVirtualThreadPerTaskExecutor()) {
      List<Future<Long>> futures = new ArrayList<>();
      for (int j = 0; j < 500; j++)
        futures.add(
            pool.submit(() -> hub.draft(student, form("2026-11-11T09:00", "2026-11-11T10:00"))));
      Set<Long> ids = new HashSet<>();
      for (var f : futures) ids.add(f.get(60, TimeUnit.SECONDS));
      assertThat(ids).hasSize(500);
    }
  }

  @Test
  void waitlistOrderUsesSubmissionNotDraftCreation() {
    long first = approved(student);
    long earlyDraft = hub.draft(student2, form("2026-11-11T09:00", "2026-11-11T10:00"));
    long firstSubmitted = reserve(external, "2026-11-11T09:00", "2026-11-11T10:00");
    hub.submit(student2, earlyDraft);
    hub.cancel(student, first);
    assertThat(str(db.get("reservation", firstSubmitted), "status")).isEqualTo("Approved");
    assertThat(str(db.get("reservation", earlyDraft), "status")).isEqualTo("Waitlisted");
  }

  @Test
  void fiveHundredConcurrentSubmissionsNeverOversell() throws Exception {
    race(500);
  }

  void race(int count) throws Exception {
    List<Long> ids = new ArrayList<>();
    for (int j = 0; j < count; j++)
      ids.add(hub.draft(student, form("2026-11-11T09:00", "2026-11-11T10:00")));
    var gate = new CountDownLatch(1);
    var times = new CopyOnWriteArrayList<Long>();
    try (var pool = Executors.newVirtualThreadPerTaskExecutor()) {
      List<Future<?>> futures = new ArrayList<>();
      for (long rid : ids)
        futures.add(
            pool.submit(
                () -> {
                  gate.await();
                  long start = System.nanoTime();
                  hub.submit(student, rid);
                  times.add((System.nanoTime() - start) / 1_000_000);
                  return null;
                }));
      gate.countDown();
      for (var f : futures) f.get(60, TimeUnit.SECONDS);
    }
    assertThat(db.list("SELECT id FROM reservation WHERE status='Pending'")).hasSize(1);
    assertThat(db.list("SELECT id FROM reservation WHERE status='Waitlisted'")).hasSize(count - 1);
    assertThat(db.list("SELECT * FROM slot_claim")).hasSize(2);
    times.sort(Long::compare);
    System.out.println(
        "CONCURRENCY: requests="
            + count
            + ", occupied_reservations=1, waitlisted="
            + (count - 1)
            + ", p95_ms="
            + times.get((int) (count * .95) - 1));
  }

  @Test
  void jwtAuthenticationAndHttpAuthorization() throws Exception {
    mvc.perform(get("/api/instruments")).andExpect(status().isUnauthorized());
    var login =
        mvc.perform(
                post("/api/auth/login")
                    .contentType("application/json")
                    .content(
                        json.writeValueAsString(
                            fields("username", "student", "password", "TestPassword123!"))))
            .andExpect(status().isOk())
            .andReturn();
    String token = json.readTree(login.getResponse().getContentAsString()).get("token").asText();
    mvc.perform(get("/api/me").header("Authorization", "Bearer " + token))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.password").doesNotExist());
    mvc.perform(get("/api/users").header("Authorization", "Bearer " + token))
        .andExpect(status().isForbidden());
    mvc.perform(get("/api/instruments").header("Authorization", "Bearer " + token + "x"))
        .andExpect(status().isUnauthorized());
    clock.at("2026-11-11T11:00");
    mvc.perform(get("/api/me").header("Authorization", "Bearer " + token))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void externalRegistrationRequiresConsentAndReview() throws Exception {
    var body =
        fields(
            "username",
            "new-external",
            "password",
            "LongPassword123!",
            "name",
            "新用户",
            "department",
            "企业",
            "contact",
            "13900000000",
            "identity_info",
            "单位身份证明",
            "consent",
            true);
    mvc.perform(
            post("/api/auth/register")
                .contentType("application/json")
                .content(json.writeValueAsString(body)))
        .andExpect(status().isOk());
    var u = db.one("SELECT * FROM app_user WHERE username='new-external'");
    assertThat(u.get("approved")).isEqualTo(false);
    problem(403, () -> hub.instruments(u, "", ""));
    assertThat(hub.identity(admin, id(u, "id")).toString()).contains("单位身份证明");
    hub.approveUser(admin, id(u, "id"));
    assertThat(hub.instruments(hub.user(id(u, "id")), "", "")).hasSize(1);
    body.put("username", "no-consent");
    body.put("consent", false);
    mvc.perform(
            post("/api/auth/register")
                .contentType("application/json")
                .content(json.writeValueAsString(body)))
        .andExpect(status().isBadRequest());
  }

  @Test
  void notificationReadCannotChangeAnotherUsersMessage() {
    hub.notify(id(student, "id"), "私有消息");
    long nid = id(hub.notifications(student).getFirst(), "id");
    hub.readNotification(student2, nid);
    assertThat(hub.notifications(student).getFirst().get("is_read")).isEqualTo(false);
    hub.readNotification(student, nid);
    assertThat(hub.notifications(student).getFirst().get("is_read")).isEqualTo(true);
  }

  @Test
  void csvPreventsSpreadsheetFormulaInjection() {
    assertThat(ReportService.cell("=CMD()")).isEqualTo("\"'=CMD()\"");
    assertThat(ReportService.cell("a,b\"c")).isEqualTo("\"a,b\"\"c\"");
  }

  @Test
  void unconfiguredSsoFailsClearlyAndSyncDeduplicates() {
    problem(503, () -> integrations.sso(fields("ticket", "test")));
    var source = instrument("EXTERNAL-01", 500000);
    integrations.sync(admin, List.of(source));
    integrations.sync(admin, List.of(source));
    assertThat(db.list("SELECT * FROM instrument WHERE code='EXTERNAL-01'")).hasSize(1);
    assertThat(str(db.one("SELECT * FROM instrument WHERE code='EXTERNAL-01'"), "source"))
        .isEqualTo("external");
    problem(409, () -> integrations.sync(admin, List.of(instrument("IY-TEST", 500000))));
    problem(403, () -> integrations.status(student));
    assertThat(integrations.status(admin).toString()).contains("sso_configured=false");
  }

  @Test
  void integrationQueuePersistsIndependentlyOfRemoteAvailability() {
    completed(student);
    assertThat(db.list("SELECT * FROM integration_event WHERE channel='upstream'")).hasSize(1);
    integrations.deliver();
    assertThat(db.list("SELECT * FROM integration_event WHERE status='Pending'")).isNotEmpty();
  }

  @Test
  void scheduledMaintenanceBlocksOnlyPlannedWindowAndRestores() {
    long cancelled = approved(student);
    long retained = reserve(student2, "2026-11-11T11:00", "2026-11-11T12:00");
    hub.maintenance(
        manager,
        iid,
        fields(
            "action",
            "schedule",
            "start_at",
            "2026-11-11T09:00",
            "end_at",
            "2026-11-11T10:00",
            "reason",
            "计划检修"));
    assertThat(str(db.get("reservation", cancelled), "status")).isEqualTo("Cancelled");
    assertThat(str(db.get("reservation", retained), "status")).isEqualTo("Pending");
    problem(409, () -> hub.draft(student, form("2026-11-11T09:30", "2026-11-11T10:00")));
    clock.at("2026-11-11T09:01");
    hub.sweep();
    assertThat(str(db.get("instrument", iid), "status")).isEqualTo("Maintenance");
    clock.at("2026-11-11T10:01");
    hub.sweep();
    assertThat(str(db.get("instrument", iid), "status")).isEqualTo("Open");
    assertThat(id(hub.user(id(student, "id")), "credit")).isEqualTo(100);
  }

  @Test
  void paginatedHistoryRetainsOwnershipAndDateFilters() {
    reserve(student, "2026-11-11T09:00", "2026-11-11T10:00");
    reserve(student, "2026-11-12T09:00", "2026-11-12T10:00");
    assertThat(hub.reservations(student, 1, 1, null, null)).hasSize(1);
    assertThat(hub.reservations(student, 2, 1, null, null)).hasSize(1);
    assertThat(hub.reservations(student, 3, 1, null, null)).isEmpty();
    assertThat(
            hub.reservations(
                student, 1, 100, LocalDate.of(2026, 11, 12), LocalDate.of(2026, 11, 12)))
        .hasSize(1);
    assertThat(hub.reservations(student2, 1, 100, null, null)).isEmpty();
    problem(400, () -> hub.reservations(student, 0, 100, null, null));
  }

  @Test
  void ssoGatewayAndDeliveryRetryContract() throws Exception {
    var server =
        com.sun.net.httpserver.HttpServer.create(new java.net.InetSocketAddress("127.0.0.1", 0), 0);
    var received = new java.util.concurrent.atomic.AtomicInteger();
    var responseCode = new java.util.concurrent.atomic.AtomicInteger(500);
    server.createContext(
        "/sso",
        exchange -> {
          assertThat(exchange.getRequestHeaders().getFirst("Authorization"))
              .isEqualTo("Bearer service-secret");
          exchange.getRequestBody().readAllBytes();
          byte[] body =
              "{\"subject\":\"20260001\",\"name\":\"认证用户\",\"department\":\"化学学院\",\"role\":\"USER\",\"group_id\":1}"
                  .getBytes(java.nio.charset.StandardCharsets.UTF_8);
          exchange.getResponseHeaders().set("Content-Type", "application/json;charset=UTF-8");
          exchange.sendResponseHeaders(200, body.length);
          exchange.getResponseBody().write(body);
          exchange.close();
        });
    server.createContext(
        "/events",
        exchange -> {
          received.incrementAndGet();
          assertThat(exchange.getRequestHeaders().getFirst("Idempotency-Key"))
              .startsWith("iy-event-");
          exchange.getRequestBody().readAllBytes();
          exchange.sendResponseHeaders(responseCode.get(), -1);
          exchange.close();
        });
    server.start();
    try {
      String base = "http://127.0.0.1:" + server.getAddress().getPort();
      var gateway =
          new IntegrationService(
              hub,
              db,
              auth,
              passwords,
              base + "/sso",
              "service-secret",
              base + "/events",
              base + "/events",
              "gateway-secret");
      assertThat(gateway.sso(fields("ticket", "one-time-ticket")).toString()).contains("认证用户");
      gateway.sso(fields("ticket", "another-ticket"));
      assertThat(db.list("SELECT id FROM app_user WHERE username='sso:20260001'")).hasSize(1);
      hub.notify(id(student, "id"), "测试通知");
      gateway.deliver();
      assertThat(db.list("SELECT * FROM integration_event WHERE status='Retry'")).hasSize(1);
      assertThat(hub.notifications(student)).hasSize(1);
      responseCode.set(204);
      clock.at("2026-11-11T08:03");
      gateway.deliver();
      gateway.deliver();
      assertThat(db.list("SELECT * FROM integration_event WHERE status='Delivered'")).hasSize(1);
      assertThat(received.get()).isEqualTo(2);
    } finally {
      server.stop(0);
    }
  }

  @Test
  void reportOnTwoHundredThousandReservations() {
    List<Long> resources = new ArrayList<>();
    resources.add(iid);
    for (int n = 1; n < 500; n++)
      resources.add(hub.saveInstrument(admin, instrument("CAP-" + n, 500000), null));
    String insertReservation =
        "INSERT INTO"
            + " reservation(id,user_id,instrument_id,start_at,end_at,status,samples,project,contact,settlement,rate,created_at,checked_at,ended_at)"
            + " VALUES(?,?,?,?,?,'Completed',1,'capacity','encrypted','encrypted',100,?,?,?)";
    for (int batch = 0; batch < 200; batch++) {
      List<Object[]> rs = new ArrayList<>(), bs = new ArrayList<>();
      for (int j = 0; j < 1000; j++) {
        int n = batch * 1000 + j;
        long rid = 10000000L + n;
        var at =
            LocalDateTime.of(2025, 1, 1, 8, 0).plusDays((n / 500) % 365).plusHours((n / 182500));
        String begin = at.toString(), end = at.plusHours(1).toString();
        rs.add(
            new Object[] {
              rid,
              id(n % 10 == 0 ? external : student, "id"),
              resources.get(n % 500),
              begin,
              end,
              begin,
              begin,
              end
            });
        bs.add(new Object[] {rid, 1, 100, 100, "校内经费卡"});
      }
      jdbc.batchUpdate(insertReservation, rs);
      jdbc.batchUpdate(
          "INSERT INTO bill(reservation_id,hours,rate,amount,method) VALUES(?,?,?,?,?)", bs);
    }
    long begin = System.nanoTime();
    var result =
        hub.statistics(admin, "national", LocalDate.of(2025, 1, 1), LocalDate.of(2025, 12, 31));
    long millis = (System.nanoTime() - begin) / 1_000_000;
    assertThat(result.get("instruments")).isEqualTo(500);
    assertThat((BigDecimal) result.get("hours")).isEqualByComparingTo("200000");
    assertThat(result.get("visits")).isEqualTo(200000L);
    assertThat((BigDecimal) result.get("external_hours")).isEqualByComparingTo("20000");
    System.out.println(
        "CAPACITY: instruments=500, reservations=200000, report_ms=" + millis + ", target_ms=5000");
  }
}
