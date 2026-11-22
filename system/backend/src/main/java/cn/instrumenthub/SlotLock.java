package cn.instrumenthub;

import java.time.Duration;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.*;

@Component
public class SlotLock {
  private final StringRedisTemplate redis;
  private final boolean enabled;

  public SlotLock(StringRedisTemplate redis, @Value("${app.redis-lock}") boolean enabled) {
    this.redis = redis;
    this.enabled = enabled;
  }

  public void acquire(long instrument) {
    if (!enabled) return;
    String key = "iy:lock:instrument:" + instrument, token = UUID.randomUUID().toString();
    try {
      Boolean acquired = redis.opsForValue().setIfAbsent(key, token, Duration.ofSeconds(30));
      if (!Boolean.TRUE.equals(acquired)) throw new Problem(409, "预约繁忙，请重试");
    } catch (Problem e) {
      throw e;
    } catch (Exception e) {
      throw new Problem(503, "预约锁服务暂不可用");
    }
    TransactionSynchronizationManager.registerSynchronization(
        new TransactionSynchronization() {
          @Override
          public void afterCompletion(int status) {
            try {
              redis.execute(
                  new DefaultRedisScript<>(
                      "if redis.call('get',KEYS[1]) == ARGV[1] then return"
                          + " redis.call('del',KEYS[1]) else return 0 end",
                      Long.class),
                  List.of(key),
                  token);
            } catch (Exception ignored) {
            }
          }
        });
  }
}
