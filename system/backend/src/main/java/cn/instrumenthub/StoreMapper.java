package cn.instrumenthub;

import java.util.*;
import org.springframework.stereotype.Repository;

/** Parameterized SQL repository; table identifiers are application constants only. */
@Repository
public class StoreMapper {
  private final SqlMapper db;

  public StoreMapper(SqlMapper db) {
    this.db = db;
  }

  public List<Map<String, Object>> list(String sql, Object... args) {
    return db.select(sql, args);
  }

  public Map<String, Object> one(String sql, Object... args) {
    var rows = list(sql, args);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  public Map<String, Object> get(String table, long id) {
    var row = one("SELECT * FROM " + table + " WHERE id=?", id);
    if (row == null) throw new Problem(404, "记录不存在");
    return row;
  }

  public int update(String sql, Object... args) {
    return db.execute(sql, args);
  }

  public long insert(String table, Map<String, Object> values) {
    var keys = new ArrayList<>(values.keySet());
    var command =
        fields(
            "sql",
            "INSERT INTO "
                + table
                + " ("
                + String.join(",", keys)
                + ") VALUES ("
                + String.join(",", Collections.nCopies(keys.size(), "?"))
                + ")",
            "args",
            keys.stream().map(values::get).toArray());
    db.insert(command);
    return ((Number) command.get("generatedId")).longValue();
  }

  public static long id(Map<String, Object> row, String key) {
    return ((Number) row.get(key)).longValue();
  }

  public static String str(Map<String, Object> row, String key) {
    return Objects.toString(row.get(key), "");
  }

  public static Map<String, Object> fields(Object... pairs) {
    Map<String, Object> out = new LinkedHashMap<>();
    for (int i = 0; i < pairs.length; i += 2) out.put((String) pairs[i], pairs[i + 1]);
    return out;
  }
}
