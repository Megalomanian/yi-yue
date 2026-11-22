import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const screenshots = path.resolve("../docs/screenshots");
fs.mkdirSync(screenshots, { recursive: true });
async function login(page, username = "student") {
  await page.goto("/");
  await page.getByRole("textbox", { name: "账号", exact: true }).fill(username);
  await page
    .getByRole("textbox", { name: "密码", exact: true })
    .fill("Demo12345!");
  await page.getByRole("button", { name: "登录平台", exact: true }).click();
  await expect(page.getByTestId("nav-instruments")).toBeVisible();
  await expect(page.locator(".instrument-card").first()).toBeVisible();
}
async function logout(page) {
  await page.getByRole("button", { name: "退出登录", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "登录平台", exact: true }),
  ).toBeVisible();
}
async function token(request, username) {
  const r = await request.post("/api/auth/login", {
    data: { username, password: "Demo12345!" },
  });
  expect(r.ok()).toBeTruthy();
  return (await r.json()).token;
}
test("用户从检索到预约，负责人审批，用户取消释放机时", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page);
  await page.screenshot({
    path: path.join(screenshots, "01-instruments-desktop.png"),
    fullPage: true,
  });
  await page
    .getByRole("textbox", { name: "搜索仪器", exact: true })
    .fill("Sigma");
  await expect(page.locator(".instrument-card")).toHaveCount(1);
  await page.getByRole("button", { name: "查看机时" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.locator(".slot-grid button").first()).toBeVisible();
  await dialog
    .locator(".slot-grid button")
    .filter({ hasText: "可约" })
    .first()
    .click();
  await dialog.getByRole("button", { name: "下一步", exact: true }).click();
  await dialog.locator("textarea").fill("E2E表面形貌检测");
  const inputs = dialog.locator('input:not([role="spinbutton"])');
  await inputs.nth(0).fill("13800000000");
  await inputs.nth(1).fill("E2E-CARD-001");
  await dialog.getByRole("button", { name: "下一步", exact: true }).click();
  await expect(dialog).toContainText("E2E表面形貌检测");
  await dialog.getByTestId("confirm-booking").click();
  await expect(dialog).not.toBeVisible();
  let row = page
    .locator("tbody tr")
    .filter({ hasText: "E2E表面形貌检测" })
    .first();
  await expect(row).toContainText("待审批");
  await logout(page);
  await login(page, "manager");
  await page.getByTestId("nav-reservations").click();
  row = page.locator("tbody tr").filter({ hasText: "E2E表面形貌检测" }).first();
  await row.getByRole("button", { name: "批准", exact: true }).click();
  await expect(row).toContainText("已批准");
  await page.screenshot({
    path: path.join(screenshots, "02-approval-workspace.png"),
    fullPage: true,
  });
  await logout(page);
  await login(page);
  await page.getByTestId("nav-reservations").click();
  row = page.locator("tbody tr").filter({ hasText: "E2E表面形貌检测" }).first();
  await row.getByRole("button", { name: "取消", exact: true }).click();
  await page
    .locator(".el-message-box")
    .getByRole("button", { name: "确定", exact: true })
    .click();
  await expect(row).toContainText("已取消");
  expect(errors).toEqual([]);
});
test("培训课程考试颁发资质，消息可标记已读", async ({ page }) => {
  await login(page);
  await page.getByTestId("nav-training").click();
  await page.getByRole("button", { name: "学习与考核" }).first().click();
  const dialog = page.getByRole("dialog");
  const answers = [1, 0, 1, 2, 0];
  for (let i = 0; i < answers.length; i++)
    await dialog
      .locator(".exam-question")
      .nth(i)
      .locator(".el-radio")
      .nth(answers[i])
      .click();
  await dialog.getByRole("button", { name: "提交考核", exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await page.getByTestId("nav-notifications").click();
  await expect(page.locator(".notification-list")).toContainText(
    "安全考核合格",
  );
  await page.getByRole("button", { name: "标记已读" }).first().click();
  await expect(page.locator(".notification-list")).toContainText("已读");
});
test("管理员查看三种统计口径并导出可读CSV", async ({ page }) => {
  await login(page, "admin");
  await page.getByTestId("nav-statistics").click();
  await expect(page.locator(".chart canvas")).toBeVisible();
  await expect(page.locator("main")).toContainText("共 3 台仪器纳入当前口径");
  await page.locator(".statistics-filters .el-select__wrapper").click();
  await page.getByRole("option", { name: "地方口径 ≥20万元" }).click();
  await page.getByRole("button", { name: "生成报表", exact: true }).click();
  await expect(page.locator("main")).toContainText("共 4 台仪器纳入当前口径");
  const event = page.waitForEvent("download");
  await page.getByRole("button", { name: "导出 CSV", exact: true }).click();
  const file = await event;
  expect(file.suggestedFilename()).toBe("开放共享绩效.csv");
  const stream = await file.createReadStream();
  let contents = "";
  for await (const part of stream) contents += part.toString("utf8");
  expect(contents).toContain("可开放机时");
  await page.screenshot({
    path: path.join(screenshots, "03-statistics-desktop.png"),
    fullPage: true,
  });
});
test("接口鉴权阻止匿名、普通用户及跨机组管理", async ({ request }) => {
  expect((await request.get("/api/instruments")).status()).toBe(401);
  const student = await token(request, "student"),
    other = await token(request, "manager2");
  expect(
    (
      await request.get("/api/users", {
        headers: { Authorization: `Bearer ${student}` },
      })
    ).status(),
  ).toBe(403);
  expect(
    (
      await request.post("/api/instruments/1/maintenance", {
        headers: { Authorization: `Bearer ${other}` },
        data: { reason: "越权测试" },
      })
    ).status(),
  ).toBe(403);
});
test("校外用户注册，管理员审核后才可查看仪器", async ({ request }) => {
  const username = `ext${Date.now()}`;
  const response = await request.post("/api/auth/register", {
    data: {
      username,
      password: "Demo12345!",
      name: "自动化测试用户",
      department: "测试单位",
      contact: "13900000000",
      identity_info: "仅用于自动化测试的虚构实名材料",
      consent: true,
    },
  });
  expect(response.ok()).toBeTruthy();
  const { id } = await response.json();
  const external = await token(request, username);
  expect(
    (
      await request.get("/api/instruments", {
        headers: { Authorization: `Bearer ${external}` },
      })
    ).status(),
  ).toBe(403);
  const admin = await token(request, "admin");
  expect(
    (
      await request.post(`/api/users/${id}/approve`, {
        headers: { Authorization: `Bearer ${admin}` },
        data: {},
      })
    ).ok(),
  ).toBeTruthy();
  expect(
    (
      await request.get("/api/instruments", {
        headers: { Authorization: `Bearer ${external}` },
      })
    ).ok(),
  ).toBeTruthy();
});
test("移动端可浏览和预约，布局无横向溢出", async ({ page }) => {
  await login(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".mobile-tabs")).toBeVisible();
  await expect(page.locator(".instrument-card").first()).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    )
    .toBeTruthy();
  await page.screenshot({
    path: path.join(screenshots, "04-instruments-mobile.png"),
    fullPage: true,
  });
  await page
    .locator(".mobile-tabs")
    .getByText("我的预约", { exact: true })
    .click();
  await expect(page.locator("main h1")).toHaveText("我的预约");
});
