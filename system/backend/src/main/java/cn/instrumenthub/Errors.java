package cn.instrumenthub;

import java.util.Map;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@RestControllerAdvice
public class Errors {
  @ExceptionHandler(Problem.class)
  public ResponseEntity<?> problem(Problem p) {
    return ResponseEntity.status(p.status)
        .body(Map.of("message", p.getMessage(), "status", p.status));
  }

  @ExceptionHandler(DataIntegrityViolationException.class)
  public ResponseEntity<?> conflict(DataIntegrityViolationException p) {
    if (p.getMostSpecificCause() instanceof java.sql.SQLException sql)
      LoggerFactory.getLogger(Errors.class)
          .warn("Database constraint: SQLState={}, code={}", sql.getSQLState(), sql.getErrorCode());
    return ResponseEntity.status(409).body(Map.of("message", "记录已存在或数据约束冲突，请刷新后重试"));
  }

  @ExceptionHandler({
    HttpMessageNotReadableException.class,
    MethodArgumentTypeMismatchException.class,
    MaxUploadSizeExceededException.class
  })
  public ResponseEntity<?> bad(Exception p) {
    return ResponseEntity.badRequest().body(Map.of("message", "请求格式不正确或文件超过20MB"));
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<?> unexpected(Exception p) {
    LoggerFactory.getLogger(Errors.class).error("Request failed: {}", p.getClass().getSimpleName());
    return ResponseEntity.internalServerError().body(Map.of("message", "服务暂时不可用，请稍后重试"));
  }
}
