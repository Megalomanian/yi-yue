package cn.instrumenthub;

import java.security.Principal;
import java.util.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class IntegrationController {
  private final IntegrationService service;
  private final HubService hub;

  public IntegrationController(IntegrationService service, HubService hub) {
    this.service = service;
    this.hub = hub;
  }

  @PostMapping("/auth/sso-ticket")
  public Object sso(@RequestBody Map<String, Object> body) {
    return service.sso(body);
  }

  @GetMapping("/integrations")
  public Object status(Principal p) {
    return service.status(hub.user(Long.parseLong(p.getName())));
  }

  @PostMapping("/integrations/instruments")
  public Object sync(Principal p, @RequestBody List<Map<String, Object>> body) {
    return service.sync(hub.user(Long.parseLong(p.getName())), body);
  }

  @PostMapping("/integrations/events/{id}/retry")
  public void retry(Principal p, @PathVariable long id) {
    service.retry(hub.user(Long.parseLong(p.getName())), id);
  }
}
