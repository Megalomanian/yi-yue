const { request, error, labels } = require("../../utils/api");
Page({
  data: { items: [] },
  onShow() {
    this.load();
  },
  async load() {
    try {
      this.setData({
        items: (await request("/reservations")).map((r) => ({
          ...r,
          label: labels[r.status],
        })),
      });
    } catch (e) {
      error(e);
    }
  },
  async action(e) {
    const { id, action } = e.currentTarget.dataset;
    try {
      await request(`/reservations/${id}/${action}`, "POST", {});
      await this.load();
    } catch (err) {
      error(err);
    }
  },
  cancel(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: "取消预约",
      content: "取消后将释放机时并通知候补用户。",
      success: async (r) => {
        if (r.confirm)
          try {
            await request(`/reservations/${id}/cancel`, "POST", {});
            await this.load();
          } catch (err) {
            error(err);
          }
      },
    });
  },
  scan(e) {
    const id = e.currentTarget.dataset.id;
    wx.scanCode({
      onlyFromCamera: true,
      success: async (result) => {
        try {
          let instrument = Number(result.result);
          if (!instrument) {
            const match = result.result.match(/instrument(?:_id)?[=:](\d+)/);
            instrument = match ? Number(match[1]) : 0;
          }
          if (!instrument) throw new Error("无效仪器二维码");
          await request(`/reservations/${id}/checkin`, "POST", {
            instrument_id: instrument,
          });
          wx.showToast({ title: "签到成功" });
          await this.load();
        } catch (err) {
          error(err);
        }
      },
      fail: () => error(new Error("扫码未完成，可联系机组老师手工签到")),
    });
  },
  download(e) {
    wx.downloadFile({
      url:
        getApp().globalData.baseUrl +
        `/reports/${e.currentTarget.dataset.id}/download`,
      header: { Authorization: "Bearer " + wx.getStorageSync("iy-token") },
      success: (r) => {
        if (r.statusCode !== 200) return error(new Error("下载失败"));
        wx.openDocument({
          filePath: r.tempFilePath,
          showMenu: true,
          fail: () => error(new Error("该原始数据格式请通过网页端下载")),
        });
      },
      fail: () => error(new Error("下载失败")),
    });
  },
});
