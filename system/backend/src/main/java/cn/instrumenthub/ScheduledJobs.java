package cn.instrumenthub;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class ScheduledJobs {
  private final HubService hub;

  public ScheduledJobs(HubService hub) {
    this.hub = hub;
  }

  @Scheduled(
      fixedDelayString = "${app.sweep-ms:60000}",
      initialDelayString = "${app.sweep-ms:60000}")
  public void run() {
    hub.sweep();
  }
}
