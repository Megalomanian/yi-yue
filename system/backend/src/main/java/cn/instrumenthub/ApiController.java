package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.*;

import jakarta.servlet.http.HttpServletRequest;
import java.nio.charset.StandardCharsets;
import java.security.Principal;
import java.time.*;
import java.util.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
public class ApiController {
  private final HubService hub;
  private final AuthService auth;
  private final ReportService reports;

  public ApiController(HubService hub, AuthService auth, ReportService reports) {
    this.hub = hub;
    this.auth = auth;
    this.reports = reports;
  }

  Map<String, Object> actor(Principal p) {
    if (p == null) throw new Problem(401, "请先登录");
    return hub.user(Long.parseLong(p.getName()));
  }

  @PostMapping("/auth/login")
  public Object login(@RequestBody Map<String, Object> b, HttpServletRequest r) {
    return auth.login(b, r.getRemoteAddr());
  }

  @PostMapping("/auth/register")
  public Object register(@RequestBody Map<String, Object> b) {
    return auth.register(b);
  }

  @GetMapping("/me")
  public Object me(Principal p) {
    return AuthService.safe(actor(p));
  }

  @GetMapping("/instruments")
  public Object instruments(
      Principal p,
      @RequestParam(defaultValue = "") String q,
      @RequestParam(defaultValue = "") String category) {
    return hub.instruments(actor(p), q, category);
  }

  @GetMapping("/instruments/{id}/slots")
  public Object slots(Principal p, @PathVariable long id, @RequestParam LocalDate date) {
    return hub.slots(actor(p), id, date);
  }

  @PostMapping("/instruments")
  public Object createInstrument(Principal p, @RequestBody Map<String, Object> b) {
    return fields("id", hub.saveInstrument(actor(p), b, null));
  }

  @PutMapping("/instruments/{id}")
  public Object updateInstrument(
      Principal p, @PathVariable long id, @RequestBody Map<String, Object> b) {
    return fields("id", hub.saveInstrument(actor(p), b, id));
  }

  @PostMapping("/instruments/import")
  public Object importInstruments(Principal p, @RequestBody List<Map<String, Object>> rows) {
    return hub.importInstruments(actor(p), rows);
  }

  @PostMapping("/instruments/{id}/maintenance")
  public void maintenance(Principal p, @PathVariable long id, @RequestBody Map<String, Object> b) {
    hub.maintenance(actor(p), id, b);
  }

  @GetMapping("/maintenance")
  public Object maintenanceList(Principal p) {
    return hub.maintenanceList(actor(p));
  }

  @GetMapping("/reservations")
  public Object reservations(
      Principal p,
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "500") int size,
      @RequestParam(required = false) LocalDate from,
      @RequestParam(required = false) LocalDate to) {
    return hub.reservations(actor(p), page, size, from, to);
  }

  @PostMapping("/reservations")
  public Object draft(Principal p, @RequestBody Map<String, Object> b) {
    return fields("id", hub.draft(actor(p), b));
  }

  @PutMapping("/reservations/{id}")
  public void editDraft(Principal p, @PathVariable long id, @RequestBody Map<String, Object> b) {
    hub.editDraft(actor(p), id, b);
  }

  @DeleteMapping("/reservations/{id}")
  public void deleteDraft(Principal p, @PathVariable long id) {
    hub.deleteDraft(actor(p), id);
  }

  @PostMapping("/reservations/{id}/submit")
  public Object submit(Principal p, @PathVariable long id) {
    var row = hub.submit(actor(p), id);
    return fields("id", row.get("id"), "status", row.get("status"));
  }

  @PostMapping("/reservations/{id}/approval")
  public void approve(Principal p, @PathVariable long id, @RequestBody Map<String, Object> b) {
    if (!(b.get("approve") instanceof Boolean)) throw new Problem(400, "请选择审批结果");
    hub.approve(actor(p), id, (Boolean) b.get("approve"), str(b, "reason"));
  }

  @PostMapping("/reservations/{id}/cancel")
  public void cancel(Principal p, @PathVariable long id) {
    hub.cancel(actor(p), id);
  }

  @PostMapping("/reservations/{id}/confirm")
  public void confirm(Principal p, @PathVariable long id) {
    hub.confirm(actor(p), id);
  }

  @PostMapping("/reservations/{id}/checkin")
  public void checkin(Principal p, @PathVariable long id, @RequestBody Map<String, Object> b) {
    hub.checkin(actor(p), id, HubService.number(b, "instrument_id"));
  }

  @PostMapping("/reservations/{id}/checkout")
  public Object checkout(Principal p, @PathVariable long id) {
    return hub.checkout(actor(p), id);
  }

  @PostMapping("/bills/{id}")
  public void bill(Principal p, @PathVariable long id, @RequestBody Map<String, Object> b) {
    hub.billAction(actor(p), id, b);
  }

  @GetMapping("/bills/export")
  public ResponseEntity<byte[]> finance(Principal p) {
    return csv(reports.financeCsv(actor(p)), "finance.csv");
  }

  @PostMapping("/reservations/{id}/reports")
  public Object upload(Principal p, @PathVariable long id, @RequestParam MultipartFile file)
      throws Exception {
    return reports.upload(actor(p), id, file);
  }

  @GetMapping("/reports/{id}/download")
  public ResponseEntity<byte[]> download(Principal p, @PathVariable long id) throws Exception {
    var file = reports.download(actor(p), id);
    return ResponseEntity.ok()
        .header(
            HttpHeaders.CONTENT_DISPOSITION,
            ContentDisposition.attachment()
                .filename(file.name(), StandardCharsets.UTF_8)
                .build()
                .toString())
        .contentType(MediaType.APPLICATION_OCTET_STREAM)
        .body(file.bytes());
  }

  @GetMapping("/training/course")
  public Object course() {
    return TrainingCourse.course();
  }

  @PostMapping("/training/enrollments")
  public Object enroll(Principal p, @RequestBody Map<String, Object> b) {
    return hub.enroll(actor(p), HubService.number(b, "instrument_id"));
  }

  @GetMapping("/training/enrollments")
  public Object enrollments(Principal p) {
    return hub.enrollments(actor(p));
  }

  @PostMapping("/training/enrollments/{id}/approve")
  public void approveEnrollment(Principal p, @PathVariable long id) {
    hub.approveEnrollment(actor(p), id);
  }

  @PostMapping("/training/{id}/exam")
  public Object exam(Principal p, @PathVariable long id, @RequestBody List<Integer> answers) {
    return hub.training(actor(p), id, answers);
  }

  @GetMapping("/qualifications")
  public Object qualifications(Principal p) {
    return hub.qualifications(actor(p));
  }

  @GetMapping("/qualifications/all")
  public Object allQualifications(Principal p) {
    return hub.allQualifications(actor(p));
  }

  @PostMapping("/qualifications/{id}/revoke")
  public void revoke(Principal p, @PathVariable long id) {
    hub.revoke(actor(p), id);
  }

  @GetMapping("/violations")
  public Object violations(Principal p) {
    return hub.violations(actor(p));
  }

  @PostMapping("/violations")
  public void damage(Principal p, @RequestBody Map<String, Object> b) {
    hub.damage(actor(p), b);
  }

  @PostMapping("/violations/{id}")
  public void appeal(Principal p, @PathVariable long id, @RequestBody Map<String, Object> b) {
    hub.appeal(actor(p), id, b);
  }

  @GetMapping("/users")
  public Object users(Principal p) {
    return hub.users(actor(p));
  }

  @GetMapping("/users/{id}/identity")
  public Object identity(Principal p, @PathVariable long id) {
    return hub.identity(actor(p), id);
  }

  @PostMapping("/users/{id}/approve")
  public void approveUser(Principal p, @PathVariable long id) {
    hub.approveUser(actor(p), id);
  }

  @GetMapping("/notifications")
  public Object notifications(Principal p) {
    return hub.notifications(actor(p));
  }

  @PostMapping("/notifications/{id}/read")
  public void read(Principal p, @PathVariable long id) {
    hub.readNotification(actor(p), id);
  }

  @GetMapping("/audits")
  public Object audit(Principal p) {
    return hub.audits(actor(p));
  }

  @GetMapping("/statistics")
  public Object statistics(
      Principal p,
      @RequestParam String caliber,
      @RequestParam LocalDate from,
      @RequestParam LocalDate to) {
    return hub.statistics(actor(p), caliber, from, to);
  }

  @GetMapping("/statistics/export")
  public ResponseEntity<byte[]> export(
      Principal p,
      @RequestParam String caliber,
      @RequestParam LocalDate from,
      @RequestParam LocalDate to) {
    return csv(
        reports.statisticsCsv(hub.statistics(actor(p), caliber, from, to)), "statistics.csv");
  }

  private ResponseEntity<byte[]> csv(String csv, String name) {
    return ResponseEntity.ok()
        .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + name)
        .contentType(MediaType.parseMediaType("text/csv;charset=UTF-8"))
        .body(("\uFEFF" + csv).getBytes(StandardCharsets.UTF_8));
  }
}
