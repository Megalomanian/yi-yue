package cn.instrumenthub;

import static cn.instrumenthub.StoreMapper.fields;

import java.util.*;

public class TrainingCourse {
  public static Object course() {
    return fields(
        "title",
        "大型仪器安全与操作基础",
        "material",
        List.of(
            "取得培训合格资质后，才能独立操作仪器。",
            "发现故障应立即停止操作并报告负责人，禁止自行拆修。",
            "上机前核对样品风险、预约信息，佩戴相应防护用品。",
            "在预约开始后15分钟内扫码签到，下机须由负责人确认结算。",
            "检测数据只向委托用户和授权机组开放，禁止擅自转发。"),
        "questions",
        List.of(
            fields(
                "question",
                "何时可以独立操作仪器？",
                "options",
                List.of("预约成功后即可", "完成培训考核并取得有效资质后", "同学口头同意后")),
            fields("question", "发现异常故障应如何处理？", "options", List.of("停机并联系负责人", "继续运行", "自行拆修")),
            fields("question", "上机前应当？", "options", List.of("跳过样品检查", "核对样品风险并佩戴防护用品", "借用他人账号")),
            fields("question", "签到时限是预约开始后多久？", "options", List.of("60分钟", "30分钟", "15分钟")),
            fields("question", "检测报告可以提供给谁？", "options", List.of("委托用户和授权机组", "任意同学", "公开群聊"))));
  }
}
