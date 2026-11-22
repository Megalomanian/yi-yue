const { request, error } = require("../../utils/api");
Page({
  data: { items: [], query: "", approved: true },
  onShow() {
    this.load();
  },
  async load() {
    try {
      const me = await request("/me");
      this.setData({ approved: me.approved });
      if (me.approved)
        this.setData({
          items: await request(
            "/instruments?q=" + encodeURIComponent(this.data.query),
          ),
        });
    } catch (e) {
      error(e);
    }
  },
  search(e) {
    this.setData({ query: e.detail.value });
    this.load();
  },
  book(e) {
    wx.navigateTo({
      url: "/pages/book/index?id=" + e.currentTarget.dataset.id,
    });
  },
});
