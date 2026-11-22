package cn.instrumenthub;

import java.util.*;
import org.apache.ibatis.annotations.*;

/** MyBatis parameter binding for SQL owned by StoreMapper and the service repository calls. */
@Mapper
public interface SqlMapper {
  @SelectProvider(type = Provider.class, method = "bound")
  List<Map<String, Object>> select(@Param("sql") String sql, @Param("args") Object[] args);

  @UpdateProvider(type = Provider.class, method = "bound")
  int execute(@Param("sql") String sql, @Param("args") Object[] args);

  @InsertProvider(type = Provider.class, method = "bound")
  @Options(useGeneratedKeys = true, keyProperty = "generatedId")
  int insert(Map<String, Object> command);

  class Provider {
    public static String bound(Map<String, Object> command) {
      String sql = (String) command.get("sql");
      StringBuilder out = new StringBuilder();
      int index = 0;
      for (char c : sql.toCharArray()) {
        if (c == '?') out.append("#{args[").append(index++).append("]}");
        else out.append(c);
      }
      return out.toString();
    }
  }
}
