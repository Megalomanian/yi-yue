const { request, error } = require("../../utils/api");
Page({
  data: { me: {}, notifications: [], qualifications: [], violations: [] },
  onShow() {
    this.load();
  },
  async load() {
    try {
      const [me, notifications, qualifications, violations] = await Promise.all(
        [
          request("/me"),
          request("/notifications"),
          request("/qualifications"),
          request("/violations"),
        ],
      );
      this.setData({ me, notifications, qualifications, violations });
    } catch (e) {
      error(e);
    }
  },
  async read(e) {
    try {
      await request(
        `/notifications/${e.currentTarget.dataset.id}/read`,
        "POST",
        {},
      );
      this.load();
    } catch (err) {
      error(err);
    }
  },
  training() {
    wx.navigateTo({ url: "/pages/training/index" });
  },
  appeal(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: "提交申诉",
      editable: true,
      placeholderText: "填写事实与依据",
      success: async (r) => {
        if (r.confirm)
          try {
            await request(`/violations/${id}`, "POST", { appeal: r.content });
            this.load();
          } catch (err) {
            error(err);
          }
      },
    });
  },
  logout() {
    wx.removeStorageSync("iy-token");
    wx.reLaunch({ url: "/pages/login/index" });
  },
});
