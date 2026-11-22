const { request, error } = require("../../utils/api");
Page({
  data: { username: "", password: "", busy: false },
  input(e) {
    this.setData({ [e.currentTarget.dataset.key]: e.detail.value });
  },
  async login() {
    if (this.data.busy) return;
    this.setData({ busy: true });
    try {
      const result = await request("/auth/login", "POST", {
        username: this.data.username,
        password: this.data.password,
      });
      wx.setStorageSync("iy-token", result.token);
      getApp().globalData.user = result.user;
      wx.switchTab({ url: "/pages/home/index" });
    } catch (e) {
      error(e);
    } finally {
      this.setData({ busy: false });
    }
  },
});
