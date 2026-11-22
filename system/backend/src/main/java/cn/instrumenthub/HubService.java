package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.*;

import java.math.*;
import java.time.*;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class HubService {
  final StoreMapper db;
  final Clock clock;
  final SlotLock locks;
  final CryptoStorage crypto;
  final int confirmationMinutes;

  public HubService(
      StoreMapper db,
      Clock clock,
      SlotLock locks,
      CryptoStorage crypto,
      @Value("${app.confirmation-minutes}") int minutes) {
    this.db = db;
    this.clock = clock;
    this.locks = locks;
    this.crypto = crypto;
    this.confirmationMinutes = minutes;
  }

  LocalDateTime now() {
    return LocalDateTime.now(clock).withNano(0);
  }

  public Map<String, Object> user(long id) {
    return db.get("app_user", id);
  }

  public void role(Map<String, Object> u, String... roles) {
    if (!List.of(roles).contains(str(u, "role"))) throw new Problem(403, "无权限执行此操作");
  }

  public void active(Map<String, Object> u) {
    if (!Boolean.TRUE.equals(u.get("approved"))) throw new Problem(403, "账号正在等待实名审核");
  }

  void manager(Map<String, Object> u, Map<String, Object> i) {
    role(u, "MANAGER", "ADMIN");
    if (!"ADMIN".equals(str(u, "role")) && id(u, "group_id") != id(i, "group_id"))
      throw new Problem(403, "仅可管理本机组仪器");
  }

  void owner(Map<String, Object> u, Map<String, Object> r) {
    if (id(u, "id") != id(r, "user_id")) manager(u, db.get("instrument", id(r, "instrument_id")));
  }

  void audit(long actor, String action, long object) {
    var context =
        org.springframework.web.context.request.RequestContextHolder.getRequestAttributes();
    String ip =
        context instanceof org.springframework.web.context.request.ServletRequestAttributes request
            ? request.getRequest().getRemoteAddr()
            : "system";
    db.insert(
        "audit_log",
        fields(
            "actor_id",
            actor,
            "action",
            action,
            "object_id",
            object,
            "created_at",
            now().toString(),
            "source_ip",
            ip));
  }

  static String json(Object body) {
    try {
      return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(body);
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  void notify(long user, String message) {
    long nid =
        db.insert(
            "notification",
            fields("user_id", user, "message", message, "created_at", now().toString()));
    db.insert(
        "integration_event",
        fields(
            "channel",
            "notification",
            "object_id",
            nid,
            "payload",
            json(fields("notification_id", nid, "user_id", user, "message", message)),
            "status",
            "Pending",
            "next_at",
            now().toString()));
  }

  static String text(Map<String, Object> b, String key, int max) {
    String value = str(b, key).strip();
    if (value.isBlank() || value.length() > max) throw new Problem(400, key + " 必填且长度不得超过 " + max);
    return value;
  }

  static long number(Map<String, Object> b, String key) {
    try {
      return Long.parseLong(b.get(key).toString());
    } catch (Exception e) {
      throw new Problem(400, key + " 必须为整数");
    }
  }

  static BigDecimal money(Map<String, Object> b, String key) {
    try {
      var v = new BigDecimal(b.get(key).toString());
      if (v.signum() < 0 || v.compareTo(new BigDecimal("1000000000")) > 0) throw new Exception();
      return v.setScale(2, RoundingMode.HALF_UP);
    } catch (Exception e) {
      throw new Problem(400, key + " 金额不合法");
    }
  }

  static LocalDateTime date(Map<String, Object> b, String key) {
    try {
      return LocalDateTime.parse(b.get(key).toString()).withNano(0);
    } catch (Exception e) {
      throw new Problem(400, key + " 日期格式不合法");
    }
  }

  Map<String, Object> lockInstrument(long id) {
    var i = db.one("SELECT * FROM instrument WHERE id=? FOR UPDATE", id);
    if (i == null) throw new Problem(404, "仪器不存在");
    return i;
  }

  Map<String, Object> lockReservation(long id) {
    var r = db.get("reservation", id);
    lockInstrument(id(r, "instrument_id"));
    return db.get("reservation", id);
  }

  void transition(Map<String, Object> r, String target, String... allowed) {
    if (!List.of(allowed).contains(str(r, "status"))) throw new Problem(409, "当前状态不允许此操作");
    if (db.update(
            "UPDATE reservation SET status=?,version=version+1 WHERE id=? AND version=?",
            target,
            id(r, "id"),
            id(r, "version"))
        != 1) throw new Problem(409, "预约状态已更新，请刷新");
  }

  public List<Map<String, Object>> instruments(
      Map<String, Object> u, String query, String category) {
    active(u);
    return db.list(
        "SELECT * FROM instrument WHERE (name LIKE ? OR model LIKE ? OR code LIKE ?) AND (?='' OR"
            + " category=?) ORDER BY id",
        "%" + query + "%",
        "%" + query + "%",
        "%" + query + "%",
        category,
        category);
  }

  public List<Map<String, Object>> slots(Map<String, Object> u, long instrument, LocalDate day) {
    active(u);
    var i = db.get("instrument", instrument);
    LocalDate today = now().toLocalDate();
    if (day.isBefore(today) || day.isAfter(today.plusDays(13)))
      throw new Problem(400, "仅可查看未来14天时段");
    List<Map<String, Object>> result = new ArrayList<>();
    for (int h = (int) id(i, "open_hour"); h < (int) id(i, "close_hour"); h++)
      for (int m : new int[] {0, 30}) {
        String at = day.atTime(h, m).toString();
        var claim =
            db.one(
                "SELECT reservation_id FROM slot_claim WHERE instrument_id=? AND slot_at=?",
                instrument,
                at);
        boolean stopped =
            db.one(
                    "SELECT id FROM maintenance WHERE instrument_id=? AND closed_at IS NULL AND"
                        + " start_at<? AND (end_at IS NULL OR end_at>?)",
                    instrument,
                    day.atTime(h, m).plusMinutes(30).toString(),
                    at)
                != null;
        String state =
            !"Open".equals(str(i, "status")) || stopped
                ? "停用"
                : day.atTime(h, m).isBefore(now()) ? "已过期" : claim == null ? "可约" : "候补";
        result.add(
            fields(
                "start_at",
                at,
                "end_at",
                day.atTime(h, m).plusMinutes(30).toString(),
                "state",
                state));
      }
    return result;
  }

  public long saveInstrument(Map<String, Object> u, Map<String, Object> b, Long existing) {
    role(u, "ADMIN");
    String name = text(b, "name", 120),
        code = text(b, "code", 50),
        model = text(b, "model", 120),
        category = text(b, "category", 80),
        location = text(b, "location", 150);
    long group = number(b, "group_id"),
        open = number(b, "open_hour"),
        close = number(b, "close_hour");
    if (group < 1 || open < 0 || close > 24 || close <= open) throw new Problem(400, "开放时段或机组不合法");
    BigDecimal price = money(b, "price"),
        external = money(b, "external_price"),
        value = money(b, "asset_value");
    long instrument;
    if (existing == null)
      instrument =
          db.insert(
              "instrument",
              fields(
                  "code",
                  code,
                  "name",
                  name,
                  "model",
                  model,
                  "category",
                  category,
                  "location",
                  location,
                  "group_id",
                  group,
                  "department",
                  str(b, "department"),
                  "price",
                  price,
                  "external_price",
                  external,
                  "asset_value",
                  value,
                  "status",
                  "Open",
                  "source",
                  "local",
                  "open_hour",
                  open,
                  "close_hour",
                  close));
    else {
      var old = lockInstrument(existing);
      if (!"local".equals(str(old, "source"))) throw new Problem(409, "外部台账仅可同步，不能本地修改");
      db.update(
          "UPDATE instrument SET"
              + " code=?,name=?,model=?,category=?,location=?,group_id=?,department=?,price=?,external_price=?,asset_value=?,open_hour=?,close_hour=?,version=version+1"
              + " WHERE id=?",
          code,
          name,
          model,
          category,
          location,
          group,
          str(b, "department"),
          price,
          external,
          value,
          open,
          close,
          existing);
      instrument = existing;
    }
    audit(id(u, "id"), "instrument.save", instrument);
    return instrument;
  }

  public long draft(Map<String, Object> u, Map<String, Object> b) {
    active(u);
    role(u, "USER", "EXTERNAL");
    long instrument = number(b, "instrument_id");
    var i = db.get("instrument", instrument);
    LocalDateTime start = date(b, "start_at"), end = date(b, "end_at");
    validateWindow(i, start, end);
    long samples = number(b, "samples");
    if (samples < 1 || samples > 10000) throw new Problem(400, "样品数须在1到10000之间");
    String project = text(b, "project", 500),
        contact = crypto.seal(text(b, "contact", 100)),
        settlement = crypto.seal(text(b, "settlement", 100));
    return db.insert(
        "reservation",
        fields(
            "user_id",
            id(u, "id"),
            "instrument_id",
            instrument,
            "start_at",
            start.toString(),
            "end_at",
            end.toString(),
            "status",
            "Draft",
            "samples",
            samples,
            "project",
            project,
            "contact",
            contact,
            "settlement",
            settlement,
            "rate",
            i.get("EXTERNAL".equals(str(u, "role")) ? "external_price" : "price"),
            "created_at",
            now().toString()));
  }

  void validateWindow(Map<String, Object> i, LocalDateTime start, LocalDateTime end) {
    if (!start.isAfter(now())
        || start.toLocalDate().isAfter(now().toLocalDate().plusDays(13))
        || !end.isAfter(start)
        || !start.toLocalDate().equals(end.minusSeconds(1).toLocalDate())
        || start.getMinute() % 30 != 0
        || end.getMinute() % 30 != 0
        || start.getSecond() != 0
        || end.getSecond() != 0
        || start.getHour() < id(i, "open_hour")
        || end.isAfter(start.toLocalDate().atStartOfDay().plusHours(id(i, "close_hour"))))
      throw new Problem(400, "请选择未来14天内开放时间中的半小时时段");
    if (!"Open".equals(str(i, "status"))) throw new Problem(409, "仪器已停用");
    if (db.one(
            "SELECT id FROM maintenance WHERE instrument_id=? AND closed_at IS NULL AND start_at<?"
                + " AND (end_at IS NULL OR end_at>?)",
            id(i, "id"),
            end.toString(),
            start.toString())
        != null) throw new Problem(409, "所选时段已安排维保");
  }

  boolean eligible(long uid, long iid) {
    var u = user(uid);
    var q = db.one("SELECT * FROM qualification WHERE user_id=? AND instrument_id=?", uid, iid);
    return Boolean.TRUE.equals(u.get("approved"))
        && id(u, "credit") >= 60
        && q != null
        && !Boolean.TRUE.equals(q.get("revoked"))
        && LocalDateTime.parse(str(q, "expires_at")).isAfter(now());
  }

  boolean available(Map<String, Object> r) {
    return db.one(
            "SELECT * FROM slot_claim WHERE instrument_id=? AND slot_at>=? AND slot_at<?",
            id(r, "instrument_id"),
            str(r, "start_at"),
            str(r, "end_at"))
        == null;
  }

  void claim(Map<String, Object> r) {
    for (var t = LocalDateTime.parse(str(r, "start_at"));
        t.isBefore(LocalDateTime.parse(str(r, "end_at")));
        t = t.plusMinutes(30))
      db.update(
          "INSERT INTO slot_claim(instrument_id,slot_at,reservation_id) VALUES(?,?,?)",
          id(r, "instrument_id"),
          t.toString(),
          id(r, "id"));
  }

  public Map<String, Object> submit(Map<String, Object> u, long reservation) {
    var raw = db.get("reservation", reservation);
    if (id(raw, "user_id") != id(u, "id")) throw new Problem(403, "仅可提交自己的预约");
    locks.acquire(id(raw, "instrument_id"));
    var r = lockReservation(reservation);
    var i = db.get("instrument", id(r, "instrument_id"));
    validateWindow(
        i, LocalDateTime.parse(str(r, "start_at")), LocalDateTime.parse(str(r, "end_at")));
    if (!eligible(id(u, "id"), id(i, "id"))) throw new Problem(403, "上机资质未取得、已过期或信用分低于60");
    String state = available(r) ? "Pending" : "Waitlisted";
    transition(r, state, "Draft");
    long sequence = db.insert("submission_sequence", fields("reservation_id", reservation));
    db.update("UPDATE reservation SET submitted_order=? WHERE id=?", sequence, reservation);
    if ("Pending".equals(state)) claim(r);
    notify(id(u, "id"), "预约 #" + reservation + ("Pending".equals(state) ? " 已提交审批" : " 已进入候补队列"));
    audit(id(u, "id"), "reservation.submit", reservation);
    return db.get("reservation", reservation);
  }

  public List<Map<String, Object>> reservations(Map<String, Object> u) {
    return reservations(u, 1, 500, null, null);
  }

  public List<Map<String, Object>> reservations(
      Map<String, Object> u, int page, int size, LocalDate from, LocalDate to) {
    if (page < 1 || size < 1 || size > 500) throw new Problem(400, "分页参数不合法");
    active(u);
    String role = str(u, "role");
    String filter =
        "ADMIN".equals(role) ? "1=1" : "MANAGER".equals(role) ? "i.group_id=?" : "r.user_id=?";
    Object[] args =
        "ADMIN".equals(role)
            ? new Object[] {}
            : new Object[] {id(u, "MANAGER".equals(role) ? "group_id" : "id")};
    List<Object> parameters = new ArrayList<>(Arrays.asList(args));
    if (from != null) {
      filter += " AND r.start_at>=?";
      parameters.add(from.atStartOfDay().toString());
    }
    if (to != null) {
      filter += " AND r.start_at<?";
      parameters.add(to.plusDays(1).atStartOfDay().toString());
    }
    parameters.add(size);
    parameters.add((long) (page - 1) * size);
    var rows =
        db.list(
            "SELECT r.*,i.name AS instrument_name,u.name AS user_name,u.credit FROM reservation r"
                + " JOIN instrument i ON i.id=r.instrument_id JOIN app_user u ON u.id=r.user_id"
                + " WHERE "
                + filter
                + " ORDER BY r.id DESC LIMIT ? OFFSET ?",
            parameters.toArray());
    for (var r : rows) {
      r.put("contact", crypto.open(str(r, "contact")));
      r.put("settlement", crypto.open(str(r, "settlement")));
      r.put("bills", db.list("SELECT * FROM bill WHERE reservation_id=?", id(r, "id")));
      r.put(
          "reports",
          db.list(
              "SELECT id,filename,checksum,size_bytes,created_at FROM report_file WHERE"
                  + " reservation_id=?",
              id(r, "id")));
    }
    return rows;
  }

  public void approve(Map<String, Object> u, long rid, boolean approve, String reason) {
    var r = lockReservation(rid);
    var i = db.get("instrument", id(r, "instrument_id"));
    manager(u, i);
    if (approve && (!"Open".equals(str(i, "status")) || !eligible(id(r, "user_id"), id(i, "id"))))
      throw new Problem(409, "仪器已停用或用户资质已失效");
    if (!approve && (reason.isBlank() || reason.length() > 500)) throw new Problem(400, "请填写驳回理由");
    transition(r, approve ? "Approved" : "Rejected", "Pending");
    db.update("UPDATE reservation SET reason=? WHERE id=?", reason, rid);
    if (!approve) release(r);
    notify(id(r, "user_id"), "预约 #" + rid + (approve ? " 审批通过" : " 已驳回：" + reason));
    audit(id(u, "id"), approve ? "reservation.approve" : "reservation.reject", rid);
  }

  void release(Map<String, Object> r) {
    db.update("DELETE FROM slot_claim WHERE reservation_id=?", id(r, "id"));
    promote(id(r, "instrument_id"));
  }

  void promote(long iid) {
    if (!"Open".equals(str(db.get("instrument", iid), "status"))) return;
    for (var r :
        db.list(
            "SELECT * FROM reservation WHERE instrument_id=? AND status='Waitlisted' ORDER BY"
                + " submitted_order,id",
            iid)) {
      if (!eligible(id(r, "user_id"), iid)
          || !LocalDateTime.parse(str(r, "start_at")).isAfter(now())) continue;
      if (available(r)) {
        transition(r, "Approved", "Waitlisted");
        claim(r);
        db.update(
            "UPDATE reservation SET confirmed=FALSE,confirm_by=? WHERE id=?",
            now().plusMinutes(confirmationMinutes).toString(),
            id(r, "id"));
        notify(
            id(r, "user_id"), "候补预约 #" + id(r, "id") + " 已补位，请在" + confirmationMinutes + "分钟内确认");
      }
    }
  }

  public void cancel(Map<String, Object> u, long rid) {
    var r = lockReservation(rid);
    owner(u, r);
    transition(r, "Cancelled", "Approved", "Waitlisted");
    release(r);
    audit(id(u, "id"), "reservation.cancel", rid);
  }

  public void confirm(Map<String, Object> u, long rid) {
    var r = lockReservation(rid);
    owner(u, r);
    if (!"Approved".equals(str(r, "status"))
        || Boolean.TRUE.equals(r.get("confirmed"))
        || LocalDateTime.parse(str(r, "confirm_by")).isBefore(now()))
      throw new Problem(409, "补位确认已失效");
    db.update("UPDATE reservation SET confirmed=TRUE WHERE id=?", rid);
  }

  public void checkin(Map<String, Object> u, long rid, long scannedInstrument) {
    var r = lockReservation(rid);
    owner(u, r);
    var i = db.get("instrument", id(r, "instrument_id"));
    LocalDateTime start = LocalDateTime.parse(str(r, "start_at")),
        end = LocalDateTime.parse(str(r, "end_at"));
    if (scannedInstrument != id(i, "id")
        || !"Open".equals(str(i, "status"))
        || now().isBefore(start)
        || !now().isBefore(end)
        || now().isAfter(start.plusMinutes(15))
        || !Boolean.TRUE.equals(r.get("confirmed"))) throw new Problem(409, "仪器码或签到时间窗不符合要求");
    if (!eligible(id(r, "user_id"), id(i, "id"))) throw new Problem(403, "上机资质或信用状态不符合要求");
    transition(r, "InUse", "Approved");
    db.update("UPDATE reservation SET checked_at=? WHERE id=?", now().toString(), rid);
    audit(id(u, "id"), "reservation.checkin", rid);
  }

  public Map<String, Object> checkout(Map<String, Object> u, long rid) {
    var r = lockReservation(rid);
    manager(u, db.get("instrument", id(r, "instrument_id")));
    if (!"InUse".equals(str(r, "status"))) throw new Problem(409, "当前状态不允许下机结算");
    long seconds = Duration.between(LocalDateTime.parse(str(r, "checked_at")), now()).getSeconds();
    if (seconds <= 0) throw new Problem(409, "实际使用时长必须大于零");
    transition(r, "Completed", "InUse");
    BigDecimal
        hours =
            BigDecimal.valueOf(seconds).divide(BigDecimal.valueOf(3600), 6, RoundingMode.HALF_UP),
        rate = new BigDecimal(str(r, "rate"));
    BigDecimal amount =
        rate.multiply(BigDecimal.valueOf(seconds))
            .divide(BigDecimal.valueOf(3600), 2, RoundingMode.HALF_UP);
    long bill =
        db.insert(
            "bill",
            fields(
                "reservation_id",
                rid,
                "hours",
                hours,
                "rate",
                rate,
                "amount",
                amount,
                "method",
                "EXTERNAL".equals(str(user(id(r, "user_id")), "role")) ? "对公转账" : "校内经费卡"));
    db.update("UPDATE reservation SET ended_at=? WHERE id=?", now().toString(), rid);
    notify(id(r, "user_id"), "预约 #" + rid + " 已结算，费用 ¥" + amount);
    audit(id(u, "id"), "bill.create", bill);
    db.insert(
        "integration_event",
        fields(
            "channel",
            "upstream",
            "object_id",
            rid,
            "payload",
            "{\"reservation_id\":"
                + rid
                + ",\"instrument_id\":"
                + id(r, "instrument_id")
                + ",\"hours\":"
                + hours
                + ",\"amount\":"
                + amount
                + "}",
            "status",
            "Pending",
            "next_at",
            now().toString()));
    return db.get("bill", bill);
  }

  public void billAction(Map<String, Object> u, long billId, Map<String, Object> b) {
    var bill = db.get("bill", billId);
    var r = lockReservation(id(bill, "reservation_id"));
    manager(u, db.get("instrument", id(r, "instrument_id")));
    if ("verify".equals(str(b, "action"))) {
      db.update("UPDATE bill SET verified=TRUE WHERE id=?", billId);
      audit(id(u, "id"), "bill.verify", billId);
    } else {
      if (!"adjust".equals(str(b, "action"))) throw new Problem(400, "未知费用操作");
      String reason = text(b, "reason", 500);
      BigDecimal adjustment;
      try {
        adjustment =
            new BigDecimal(b.get("adjustment").toString()).setScale(2, RoundingMode.HALF_UP);
      } catch (Exception e) {
        throw new Problem(400, "冲正金额不合法");
      }
      if (adjustment.add(new BigDecimal(str(bill, "amount"))).signum() < 0)
        throw new Problem(400, "冲正后金额不能为负");
      db.insert(
          "bill_adjustment",
          fields(
              "bill_id",
              billId,
              "actor_id",
              id(u, "id"),
              "previous_adjustment",
              bill.get("adjustment"),
              "new_adjustment",
              adjustment,
              "reason",
              reason,
              "created_at",
              now().toString()));
      db.update(
          "UPDATE bill SET adjustment=?,adjustment_reason=?,verified=FALSE WHERE id=?",
          adjustment,
          reason,
          billId);
      audit(id(u, "id"), "bill.adjust", billId);
    }
  }

  public void maintenance(Map<String, Object> u, long iid, Map<String, Object> b) {
    var i = lockInstrument(iid);
    manager(u, i);
    if ("restore".equals(str(b, "action"))) {
      db.update("UPDATE instrument SET status='Open',version=version+1 WHERE id=?", iid);
      db.update(
          "UPDATE maintenance SET closed_at=? WHERE instrument_id=? AND closed_at IS NULL AND"
              + " start_at<=?",
          now().toString(),
          iid,
          now().toString());
      audit(id(u, "id"), "maintenance.restore", iid);
      return;
    }
    if ("schedule".equals(str(b, "action"))) {
      var start = date(b, "start_at");
      var end = date(b, "end_at");
      String reason = text(b, "reason", 500);
      if (!start.isAfter(now()) || !end.isAfter(start)) throw new Problem(400, "计划维保须选择未来有效时段");
      if (db.one(
              "SELECT id FROM maintenance WHERE instrument_id=? AND closed_at IS NULL AND"
                  + " start_at<? AND (end_at IS NULL OR end_at>?)",
              iid,
              end.toString(),
              start.toString())
          != null) throw new Problem(409, "维保计划时段冲突");
      if (db.one(
              "SELECT id FROM reservation WHERE instrument_id=? AND status='InUse' AND start_at<?"
                  + " AND end_at>?",
              iid,
              end.toString(),
              start.toString())
          != null) throw new Problem(409, "请先完成与维保计划冲突的使用记录");
      db.insert(
          "maintenance",
          fields(
              "instrument_id",
              iid,
              "reason",
              reason,
              "start_at",
              start.toString(),
              "end_at",
              end.toString(),
              "applied",
              false));
      for (var r :
          db.list(
              "SELECT * FROM reservation WHERE instrument_id=? AND status IN"
                  + " ('Pending','Approved','Waitlisted') AND start_at<? AND end_at>?",
              iid,
              end.toString(),
              start.toString())) {
        transition(r, "Cancelled", str(r, "status"));
        db.update("DELETE FROM slot_claim WHERE reservation_id=?", id(r, "id"));
        db.update(
            "UPDATE reservation SET reason=? WHERE id=?", "计划维保，免违约取消：" + reason, id(r, "id"));
        notify(id(r, "user_id"), "预约 #" + id(r, "id") + " 因计划维保免违约取消，请改约");
      }
      audit(id(u, "id"), "maintenance.schedule", iid);
      return;
    }
    if (!"Open".equals(str(i, "status"))) throw new Problem(409, "仪器已经停用");
    String reason = text(b, "reason", 500);
    if (db.one("SELECT id FROM reservation WHERE instrument_id=? AND status='InUse'", iid) != null)
      throw new Problem(409, "请先结束使用中的预约再停用");
    db.update("UPDATE instrument SET status='Maintenance',version=version+1 WHERE id=?", iid);
    db.insert(
        "maintenance",
        fields("instrument_id", iid, "reason", reason, "start_at", now().toString()));
    for (var r :
        db.list(
            "SELECT * FROM reservation WHERE instrument_id=? AND status IN"
                + " ('Pending','Approved','Waitlisted')",
            iid)) {
      transition(r, "Cancelled", str(r, "status"));
      db.update("UPDATE reservation SET reason=? WHERE id=?", "设备停用，免违约：" + reason, id(r, "id"));
      db.update("DELETE FROM slot_claim WHERE reservation_id=?", id(r, "id"));
      notify(id(r, "user_id"), "仪器停用，预约 #" + id(r, "id") + " 已免违约取消，请改约");
    }
    audit(id(u, "id"), "maintenance.stop", iid);
  }

  public Map<String, Object> training(Map<String, Object> u, long iid, List<Integer> answers) {
    active(u);
    db.get("instrument", iid);
    if (db.one(
            "SELECT id FROM training_enrollment WHERE user_id=? AND instrument_id=? AND"
                + " approved=TRUE",
            id(u, "id"),
            iid)
        == null) throw new Problem(403, "请先报名培训并等待机组资格初审");
    if (answers.size() != 5) throw new Problem(400, "请完成全部5道题");
    int score = 0;
    var correct = List.of(1, 0, 1, 2, 0);
    for (int j = 0; j < 5; j++) if (correct.get(j).equals(answers.get(j))) score += 20;
    db.insert(
        "training",
        fields(
            "user_id",
            id(u, "id"),
            "instrument_id",
            iid,
            "score",
            score,
            "created_at",
            now().toString()));
    if (score >= 80) {
      var q =
          db.one(
              "SELECT id FROM qualification WHERE user_id=? AND instrument_id=?", id(u, "id"), iid);
      if (q == null)
        db.insert(
            "qualification",
            fields(
                "user_id",
                id(u, "id"),
                "instrument_id",
                iid,
                "expires_at",
                now().plusYears(1).toString()));
      else
        db.update(
            "UPDATE qualification SET expires_at=?,revoked=FALSE,reminder_sent=FALSE WHERE id=?",
            now().plusYears(1).toString(),
            id(q, "id"));
      notify(id(u, "id"), "安全考核合格，已获得仪器 #" + iid + " 一年上机资质");
      audit(id(u, "id"), "qualification.issue", iid);
    }
    return fields("score", score, "passed", score >= 80);
  }

  public List<Map<String, Object>> qualifications(Map<String, Object> u) {
    return db.list(
        "SELECT q.*,i.name AS instrument_name FROM qualification q JOIN instrument i ON"
            + " i.id=q.instrument_id WHERE q.user_id=?",
        id(u, "id"));
  }

  public void revoke(Map<String, Object> u, long qid) {
    role(u, "ADMIN");
    var q = db.get("qualification", qid);
    db.update("UPDATE qualification SET revoked=TRUE WHERE id=?", qid);
    db.update(
        "UPDATE training_enrollment SET approved=FALSE WHERE user_id=? AND instrument_id=?",
        id(q, "user_id"),
        id(q, "instrument_id"));
    notify(id(q, "user_id"), "仪器上机资质已被撤销，请联系机组复训");
    audit(id(u, "id"), "qualification.revoke", qid);
  }

  public List<Map<String, Object>> violations(Map<String, Object> u) {
    return "ADMIN".equals(str(u, "role"))
        ? db.list("SELECT * FROM violation ORDER BY id DESC")
        : db.list("SELECT * FROM violation WHERE user_id=? ORDER BY id DESC", id(u, "id"));
  }

  public void appeal(Map<String, Object> u, long vid, Map<String, Object> b) {
    var v = db.one("SELECT * FROM violation WHERE id=? FOR UPDATE", vid);
    if (v == null) throw new Problem(404, "违约记录不存在");
    if ("resolve".equals(str(b, "action"))) {
      role(u, "ADMIN");
      if (Boolean.TRUE.equals(v.get("resolved"))) throw new Problem(409, "已处理");
      boolean restore = Boolean.TRUE.equals(b.get("restore"));
      db.update("UPDATE violation SET resolved=TRUE,restored=? WHERE id=?", restore, vid);
      if (restore)
        db.update(
            "UPDATE app_user SET credit=LEAST(100,credit+?) WHERE id=?",
            id(v, "points"),
            id(v, "user_id"));
      notify(id(v, "user_id"), restore ? "申诉成立，信用分已恢复" : "申诉已复核，维持原认定");
      audit(id(u, "id"), "violation.resolve", vid);
    } else {
      if (id(v, "user_id") != id(u, "id")) throw new Problem(403, "仅可申诉自己的记录");
      if (Boolean.TRUE.equals(v.get("resolved"))) throw new Problem(409, "申诉已结案");
      db.update("UPDATE violation SET appeal=? WHERE id=?", text(b, "appeal", 500), vid);
    }
  }

  public List<Map<String, Object>> users(Map<String, Object> u) {
    role(u, "ADMIN");
    return db.list(
        "SELECT id,username,name,role,group_id,department,approved,credit FROM app_user ORDER BY"
            + " id");
  }

  public void approveUser(Map<String, Object> u, long uid) {
    role(u, "ADMIN");
    db.update("UPDATE app_user SET approved=TRUE WHERE id=?", uid);
    audit(id(u, "id"), "user.approve", uid);
  }

  public List<Map<String, Object>> notifications(Map<String, Object> u) {
    return db.list(
        "SELECT * FROM notification WHERE user_id=? ORDER BY id DESC LIMIT 200", id(u, "id"));
  }

  public void readNotification(Map<String, Object> u, long nid) {
    db.update("UPDATE notification SET is_read=TRUE WHERE id=? AND user_id=?", nid, id(u, "id"));
  }

  public List<Map<String, Object>> audits(Map<String, Object> u) {
    role(u, "ADMIN");
    return db.list("SELECT * FROM audit_log ORDER BY id DESC LIMIT 500");
  }

  public Map<String, Object> statistics(
      Map<String, Object> u, String caliber, LocalDate from, LocalDate to) {
    role(u, "ADMIN", "DEPARTMENT");
    if (to.isBefore(from) || to.isAfter(from.plusYears(5))) throw new Problem(400, "统计周期不合法");
    BigDecimal threshold =
        switch (caliber) {
          case "national" -> new BigDecimal("500000");
          case "local" -> new BigDecimal("200000");
          case "campus" -> new BigDecimal("400000");
          default -> throw new Problem(400, "未知统计口径");
        };
    String begin = from.atStartOfDay().toString(),
        finish = to.plusDays(1).atStartOfDay().toString();
    List<Map<String, Object>> rows = new ArrayList<>();
    BigDecimal total = BigDecimal.ZERO,
        external = BigDecimal.ZERO,
        available = BigDecimal.ZERO,
        revenue = BigDecimal.ZERO;
    long visits = 0;
    for (var i : db.list("SELECT * FROM instrument WHERE asset_value>=? ORDER BY id", threshold)) {
      long iid = id(i, "id");
      BigDecimal denominator =
          BigDecimal.valueOf(
              (id(i, "close_hour") - id(i, "open_hour"))
                  * (java.time.temporal.ChronoUnit.DAYS.between(from, to) + 1));
      for (var m :
          db.list(
              "SELECT * FROM maintenance WHERE instrument_id=? AND start_at<? AND (closed_at IS"
                  + " NULL OR closed_at>?)",
              iid,
              finish,
              begin)) {
        LocalDateTime a = LocalDateTime.parse(str(m, "start_at")),
            z =
                !str(m, "closed_at").isEmpty()
                    ? LocalDateTime.parse(str(m, "closed_at"))
                    : !str(m, "end_at").isEmpty() ? LocalDateTime.parse(str(m, "end_at")) : now();
        for (LocalDate day = from; !day.isAfter(to); day = day.plusDays(1)) {
          LocalDateTime x = day.atStartOfDay().plusHours(id(i, "open_hour")),
              y = day.atStartOfDay().plusHours(id(i, "close_hour"));
          if (a.isAfter(x)) x = a;
          if (z.isBefore(y)) y = z;
          if (y.isAfter(x))
            denominator =
                denominator.subtract(
                    BigDecimal.valueOf(Duration.between(x, y).toSeconds())
                        .divide(BigDecimal.valueOf(3600), 6, RoundingMode.HALF_UP));
        }
      }
      denominator = denominator.max(BigDecimal.ZERO);
      BigDecimal used = BigDecimal.ZERO, ext = BigDecimal.ZERO, amount = BigDecimal.ZERO;
      long count = 0;
      for (var r :
          db.list(
              "SELECT r.*,u.role,b.amount,b.adjustment FROM reservation r JOIN app_user u ON"
                  + " u.id=r.user_id JOIN bill b ON b.reservation_id=r.id WHERE r.instrument_id=?"
                  + " AND r.status='Completed' AND r.checked_at<? AND r.ended_at>?",
              iid,
              finish,
              begin)) {
        LocalDateTime x = LocalDateTime.parse(str(r, "checked_at")),
            y = LocalDateTime.parse(str(r, "ended_at"));
        if (x.isBefore(from.atStartOfDay())) x = from.atStartOfDay();
        if (y.isAfter(to.plusDays(1).atStartOfDay())) y = to.plusDays(1).atStartOfDay();
        BigDecimal h =
            BigDecimal.valueOf(Duration.between(x, y).toSeconds())
                .divide(BigDecimal.valueOf(3600), 6, RoundingMode.HALF_UP);
        used = used.add(h);
        if ("EXTERNAL".equals(str(r, "role"))) ext = ext.add(h);
        amount =
            amount.add(new BigDecimal(str(r, "amount"))).add(new BigDecimal(str(r, "adjustment")));
        count++;
      }
      rows.add(
          fields(
              "id",
              iid,
              "name",
              str(i, "name"),
              "group_id",
              id(i, "group_id"),
              "department",
              str(i, "department"),
              "hours",
              used,
              "available_hours",
              denominator,
              "external_hours",
              ext,
              "visits",
              count,
              "revenue",
              amount,
              "utilization",
              denominator.signum() == 0
                  ? BigDecimal.ZERO
                  : used.multiply(BigDecimal.valueOf(100))
                      .divide(denominator, 2, RoundingMode.HALF_UP)));
      total = total.add(used);
      external = external.add(ext);
      available = available.add(denominator);
      revenue = revenue.add(amount);
      visits += count;
    }
    audit(id(u, "id"), "statistics.query", 0);
    return fields(
        "caliber",
        caliber,
        "from",
        from.toString(),
        "to",
        to.toString(),
        "instruments",
        rows.size(),
        "hours",
        total,
        "external_hours",
        external,
        "available_hours",
        available,
        "revenue",
        revenue,
        "visits",
        visits,
        "utilization",
        available.signum() == 0
            ? BigDecimal.ZERO
            : total.multiply(BigDecimal.valueOf(100)).divide(available, 2, RoundingMode.HALF_UP),
        "rows",
        rows);
  }

  public void sweep() {
    for (var m :
        db.list(
            "SELECT * FROM maintenance WHERE closed_at IS NULL AND end_at IS NOT NULL AND"
                + " start_at<=? ORDER BY instrument_id",
            now().toString())) {
      lockInstrument(id(m, "instrument_id"));
      if (!LocalDateTime.parse(str(m, "end_at")).isAfter(now())) {
        db.update("UPDATE maintenance SET closed_at=end_at,applied=TRUE WHERE id=?", id(m, "id"));
        db.update("UPDATE instrument SET status='Open' WHERE id=?", id(m, "instrument_id"));
      } else if (!Boolean.TRUE.equals(m.get("applied"))) {
        db.update("UPDATE maintenance SET applied=TRUE WHERE id=?", id(m, "id"));
        db.update("UPDATE instrument SET status='Maintenance' WHERE id=?", id(m, "instrument_id"));
      }
    }
    for (var q :
        db.list(
            "SELECT * FROM qualification WHERE revoked=FALSE AND reminder_sent=FALSE AND"
                + " expires_at<?",
            now().plusDays(30).toString())) {
      notify(
          id(q, "user_id"),
          "仪器 #" + id(q, "instrument_id") + " 的上机资质将于 " + str(q, "expires_at") + " 到期，请及时复训");
      db.update("UPDATE qualification SET reminder_sent=TRUE WHERE id=?", id(q, "id"));
    }
    for (var raw :
        db.list(
            "SELECT * FROM reservation WHERE status IN ('Approved','InUse') ORDER BY"
                + " instrument_id,id")) {
      var r = lockReservation(id(raw, "id"));
      if ("Approved".equals(str(r, "status"))) {
        if (!Boolean.TRUE.equals(r.get("confirmed"))
            && LocalDateTime.parse(str(r, "confirm_by")).isBefore(now())) {
          transition(r, "Cancelled", "Approved");
          release(r);
          notify(id(r, "user_id"), "候补确认超时，预约已取消");
          continue;
        }
        if (now().isAfter(LocalDateTime.parse(str(r, "start_at")).plusMinutes(15))) {
          transition(r, "NoShow", "Approved");
          penalty(r, "NoShow", 20, "开机15分钟未签到");
          release(r);
        } else if (!Boolean.TRUE.equals(r.get("reminder_sent"))
            && now().plusMinutes(30).isAfter(LocalDateTime.parse(str(r, "start_at")))) {
          notify(id(r, "user_id"), "预约 #" + id(r, "id") + " 即将开始，请按时签到");
          db.update("UPDATE reservation SET reminder_sent=TRUE WHERE id=?", id(r, "id"));
        }
      } else if ("InUse".equals(str(r, "status"))
          && now().isAfter(LocalDateTime.parse(str(r, "end_at")).plusMinutes(15)))
        penalty(r, "Overtime", 10, "超过预约结束时间15分钟仍在占用");
    }
  }

  void penalty(Map<String, Object> r, String kind, int points, String reason) {
    if (db.one("SELECT id FROM violation WHERE reservation_id=? AND kind=?", id(r, "id"), kind)
        != null) return;
    db.insert(
        "violation",
        fields(
            "reservation_id",
            id(r, "id"),
            "user_id",
            id(r, "user_id"),
            "kind",
            kind,
            "points",
            points,
            "reason",
            reason));
    db.update(
        "UPDATE app_user SET credit=GREATEST(0,credit-?) WHERE id=?", points, id(r, "user_id"));
    notify(
        id(r, "user_id"), "预约 #" + id(r, "id") + " 违约扣分：" + reason + "，扣" + points + "分，可在信用中心申诉");
    audit(0, "credit.penalty", id(r, "id"));
  }

  public List<Long> importInstruments(Map<String, Object> u, List<Map<String, Object>> rows) {
    role(u, "ADMIN");
    if (rows.isEmpty() || rows.size() > 500) throw new Problem(400, "每次导入1到500台仪器");
    List<Long> result = new ArrayList<>();
    for (var row : rows) result.add(saveInstrument(u, row, null));
    return result;
  }

  public List<Map<String, Object>> maintenanceList(Map<String, Object> u) {
    role(u, "ADMIN", "MANAGER");
    return "ADMIN".equals(str(u, "role"))
        ? db.list(
            "SELECT m.*,i.name FROM maintenance m JOIN instrument i ON i.id=m.instrument_id ORDER"
                + " BY m.id DESC")
        : db.list(
            "SELECT m.*,i.name FROM maintenance m JOIN instrument i ON i.id=m.instrument_id WHERE"
                + " i.group_id=? ORDER BY m.id DESC",
            id(u, "group_id"));
  }

  public void deleteDraft(Map<String, Object> u, long rid) {
    var r = lockReservation(rid);
    if (id(u, "id") != id(r, "user_id")) throw new Problem(403, "仅可删除自己的草稿");
    if (!"Draft".equals(str(r, "status"))) throw new Problem(409, "仅可删除草稿");
    db.update("DELETE FROM reservation WHERE id=?", rid);
  }

  public void editDraft(Map<String, Object> u, long rid, Map<String, Object> b) {
    var r = lockReservation(rid);
    if (id(u, "id") != id(r, "user_id")) throw new Problem(403, "仅可编辑自己的草稿");
    if (!"Draft".equals(str(r, "status"))) throw new Problem(409, "仅可编辑草稿");
    var i = db.get("instrument", id(r, "instrument_id"));
    var start = date(b, "start_at");
    var end = date(b, "end_at");
    validateWindow(i, start, end);
    long samples = number(b, "samples");
    if (samples < 1 || samples > 10000) throw new Problem(400, "样品数须在1到10000之间");
    db.update(
        "UPDATE reservation SET"
            + " start_at=?,end_at=?,samples=?,project=?,contact=?,settlement=?,version=version+1"
            + " WHERE id=?",
        start.toString(),
        end.toString(),
        samples,
        text(b, "project", 500),
        crypto.seal(text(b, "contact", 100)),
        crypto.seal(text(b, "settlement", 100)),
        rid);
  }

  public Object enroll(Map<String, Object> u, long iid) {
    active(u);
    role(u, "USER", "EXTERNAL");
    db.get("instrument", iid);
    var old =
        db.one(
            "SELECT * FROM training_enrollment WHERE user_id=? AND instrument_id=?",
            id(u, "id"),
            iid);
    if (old != null) return old;
    long eid =
        db.insert("training_enrollment", fields("user_id", id(u, "id"), "instrument_id", iid));
    return db.get("training_enrollment", eid);
  }

  public List<Map<String, Object>> enrollments(Map<String, Object> u) {
    String role = str(u, "role"),
        filter =
            "ADMIN".equals(role) ? "1=1" : "MANAGER".equals(role) ? "i.group_id=?" : "e.user_id=?";
    return db.list(
        "SELECT e.*,i.name AS instrument_name,u.name AS user_name FROM training_enrollment e JOIN"
            + " instrument i ON i.id=e.instrument_id JOIN app_user u ON u.id=e.user_id WHERE "
            + filter,
        "ADMIN".equals(role)
            ? new Object[] {}
            : new Object[] {id(u, "MANAGER".equals(role) ? "group_id" : "id")});
  }

  public void approveEnrollment(Map<String, Object> u, long eid) {
    var e = db.get("training_enrollment", eid);
    manager(u, db.get("instrument", id(e, "instrument_id")));
    db.update("UPDATE training_enrollment SET approved=TRUE WHERE id=?", eid);
    notify(id(e, "user_id"), "培训初审通过，可以学习课程并参加考核");
    audit(id(u, "id"), "training.approve", eid);
  }

  public List<Map<String, Object>> allQualifications(Map<String, Object> u) {
    role(u, "ADMIN");
    return db.list(
        "SELECT q.*,u.name AS user_name,i.name AS instrument_name FROM qualification q JOIN"
            + " app_user u ON u.id=q.user_id JOIN instrument i ON i.id=q.instrument_id");
  }

  public void damage(Map<String, Object> u, Map<String, Object> b) {
    role(u, "ADMIN");
    var r = lockReservation(number(b, "reservation_id"));
    if (!List.of("InUse", "Completed").contains(str(r, "status")))
      throw new Problem(409, "只能对已使用的预约登记设备损坏");
    long points = number(b, "points");
    if (points < 1 || points > 100) throw new Problem(400, "扣分应为1到100分");
    penalty(r, "Damage", (int) points, text(b, "reason", 500));
    audit(id(u, "id"), "damage.record", id(r, "id"));
  }

  public Object identity(Map<String, Object> u, long uid) {
    role(u, "ADMIN");
    var record = db.one("SELECT * FROM identity_review WHERE user_id=?", uid);
    if (record == null) throw new Problem(404, "无实名审核材料");
    audit(id(u, "id"), "identity.read", uid);
    return fields(
        "identity_info",
        crypto.open(str(record, "identity_info")),
        "contact",
        crypto.open(str(record, "contact")));
  }
}
