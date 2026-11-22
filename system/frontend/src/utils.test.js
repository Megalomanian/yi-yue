import { describe, it, expect } from "vitest";
import { estimate, money, stamp, labels } from "./utils";
describe("展示与费用预估", () => {
  it("半小时按校内或校外单价分别估算", () => {
    expect(estimate("2026-11-12T08:00", "2026-11-12T08:30", 280)).toBe(140);
    expect(estimate("2026-11-12T08:00", "2026-11-12T09:30", 560)).toBe(840);
  });
  it("避免负时长展示负费用", () =>
    expect(estimate("2026-11-12T09:00", "2026-11-12T08:00", 280)).toBe(0));
  it("金额和日期显示清晰", () => {
    expect(money(1250.5)).toBe("1,250.50");
    expect(stamp("2026-11-12T08:30:00")).toBe("2026-11-12 08:30");
    expect(stamp(null)).toBe("—");
  });
  it("九种状态均有中文标签", () => expect(Object.keys(labels)).toHaveLength(9));
});
