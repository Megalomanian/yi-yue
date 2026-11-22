export const labels = {
  Draft: "草稿",
  Pending: "待审批",
  Approved: "已批准",
  Waitlisted: "候补中",
  InUse: "使用中",
  Completed: "已完成",
  Rejected: "已驳回",
  NoShow: "已违约",
  Cancelled: "已取消",
};
export const roles = {
  USER: "校内送样人",
  EXTERNAL: "校外用户",
  MANAGER: "仪器负责人",
  ADMIN: "平台管理员",
  DEPARTMENT: "主管部门",
};
export function money(value) {
  return Number(value || 0).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
export function today(offset = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
export function stamp(s) {
  return s ? s.replace("T", " ").slice(0, 16) : "—";
}
export function estimate(start, end, rate) {
  return (
    Math.max(0, (new Date(end) - new Date(start)) / 3600000) * Number(rate || 0)
  );
}
