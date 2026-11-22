package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.*;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
@Transactional
public class ReportService {
  private final HubService hub;
  private final StoreMapper db;
  private final CryptoStorage storage;

  public ReportService(HubService hub, StoreMapper db, CryptoStorage storage) {
    this.hub = hub;
    this.db = db;
    this.storage = storage;
  }

  public record Download(String name, byte[] bytes) {}

  public Object upload(Map<String, Object> u, long rid, MultipartFile file) throws Exception {
    var r = hub.lockReservation(rid);
    hub.manager(u, db.get("instrument", id(r, "instrument_id")));
    if (!"Completed".equals(str(r, "status"))) throw new Problem(409, "完成结算后才能上传报告");
    String name = Objects.toString(file.getOriginalFilename(), "").replaceAll("[\\\\/\\r\\n]", "_");
    if (name.length() > 200 || file.isEmpty() || file.getSize() > 20 * 1024 * 1024)
      throw new Problem(400, "文件应为1字节到20MB，文件名不超过200字");
    String lower = name.toLowerCase(Locale.ROOT);
    if (!List.of(".pdf", ".csv", ".txt", ".zip").stream().anyMatch(lower::endsWith))
      throw new Problem(400, "支持PDF、CSV、TXT、ZIP报告和原始数据");
    byte[] data = file.getBytes();
    if (lower.endsWith(".pdf")
        && !new String(Arrays.copyOf(data, Math.min(5, data.length)), StandardCharsets.US_ASCII)
            .equals("%PDF-")) throw new Problem(400, "PDF文件内容与扩展名不符");
    if (lower.endsWith(".zip") && (data.length < 4 || data[0] != 'P' || data[1] != 'K'))
      throw new Problem(400, "ZIP文件内容与扩展名不符");
    String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
    String object = storage.put(data);
    long fid =
        db.insert(
            "report_file",
            fields(
                "reservation_id",
                rid,
                "filename",
                name,
                "object_key",
                object,
                "checksum",
                hash,
                "size_bytes",
                data.length,
                "created_at",
                hub.now().toString()));
    hub.notify(id(r, "user_id"), "预约 #" + rid + " 的检测报告已上传，可下载查看");
    hub.audit(id(u, "id"), "report.upload", fid);
    return fields("id", fid, "filename", name, "checksum", hash);
  }

  public Download download(Map<String, Object> u, long fid) throws Exception {
    var f = db.get("report_file", fid);
    var r = db.get("reservation", id(f, "reservation_id"));
    hub.owner(u, r);
    byte[] data = storage.read(str(f, "object_key"));
    String checksum = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
    if (!checksum.equals(str(f, "checksum"))) throw new Problem(409, "报告完整性校验失败，请联系机组");
    hub.audit(id(u, "id"), "report.download", fid);
    return new Download(str(f, "filename"), data);
  }

  static String cell(Object value) {
    String v = Objects.toString(value, "");
    if (v.matches("^[=+@\\-].*")) v = "'" + v;
    return "\"" + v.replace("\"", "\"\"") + "\"";
  }

  String row(Object... values) {
    return String.join(",", Arrays.stream(values).map(ReportService::cell).toList()) + "\r\n";
  }

  @SuppressWarnings("unchecked")
  public String statisticsCsv(Map<String, Object> stats) {
    StringBuilder out =
        new StringBuilder(
            row("统计口径", stats.get("caliber"), "开始日期", stats.get("from"), "结束日期", stats.get("to")));
    out.append(row("仪器编号", "仪器名称", "机组", "院系", "开机机时", "可开放机时", "利用率%", "对外开放机时", "服务人次", "金额"));
    for (var r : (List<Map<String, Object>>) stats.get("rows"))
      out.append(
          row(
              r.get("id"),
              r.get("name"),
              r.get("group_id"),
              r.get("department"),
              r.get("hours"),
              r.get("available_hours"),
              r.get("utilization"),
              r.get("external_hours"),
              r.get("visits"),
              r.get("revenue")));
    return out.toString();
  }

  public String financeCsv(Map<String, Object> u) {
    hub.role(u, "ADMIN", "DEPARTMENT");
    StringBuilder out =
        new StringBuilder(
            row("费用单号", "预约单号", "经费卡/对公信息", "项目", "原始金额", "冲正金额", "实收金额", "实际机时", "结算时间", "线下核销"));
    for (var r :
        db.list(
            "SELECT b.*,r.settlement,r.project,r.ended_at FROM bill b JOIN reservation r ON"
                + " r.id=b.reservation_id ORDER BY b.id")) {
      out.append(
          row(
              r.get("id"),
              r.get("reservation_id"),
              storage.open(str(r, "settlement")),
              r.get("project"),
              r.get("amount"),
              r.get("adjustment"),
              new java.math.BigDecimal(str(r, "amount"))
                  .add(new java.math.BigDecimal(str(r, "adjustment"))),
              r.get("hours"),
              r.get("ended_at"),
              r.get("verified")));
    }
    hub.audit(id(u, "id"), "finance.export", 0);
    return out.toString();
  }
}
