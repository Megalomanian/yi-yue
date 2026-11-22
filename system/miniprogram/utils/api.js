function request(path, method = "GET", data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: getApp().globalData.baseUrl + path,
      method,
      data,
      header: { Authorization: "Bearer " + wx.getStorageSync("iy-token") },
      success: (r) => {
        if (r.statusCode >= 200 && r.statusCode < 300) resolve(r.data);
        else {
          if (r.statusCode === 401) {
            wx.removeStorageSync("iy-token");
            wx.reLaunch({ url: "/pages/login/index" });
          }
          reject(new Error(r.data.message || "请求失败"));
        }
      },
      fail: () => reject(new Error("无法连接服务，请检查服务器地址与网络")),
    });
  });
}
function error(e) {
  wx.showToast({
    title: e.message || "操作失败",
    icon: "none",
    duration: 3000,
  });
}
const labels = {
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
module.exports = { request, error, labels };
