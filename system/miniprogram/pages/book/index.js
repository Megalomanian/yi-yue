const { request, error } = require("../../utils/api");
Page({
  data: {
    id: 0,
    date: "",
    slots: [],
    selected: -1,
    step: 0,
    samples: 1,
    project: "",
    contact: "",
    settlement: "",
    busy: false,
    draftId: null,
  },
  onLoad(o) {
    const d = new Date(Date.now() + 86400000);
    const date = [
      d.getFullYear(),
      String(d.getMonth() + 1).padStart(2, "0"),
      String(d.getDate()).padStart(2, "0"),
    ].join("-");
    this.setData({ id: Number(o.id), date });
    this.load();
  },
  async load() {
    try {
      this.setData({
        slots: (
          await request(
            `/instruments/${this.data.id}/slots?date=${this.data.date}`,
          )
        ).map((s) => ({ ...s, time: s.start_at.slice(11) })),
        selected: -1,
      });
    } catch (e) {
      error(e);
    }
  },
  date(e) {
    this.setData({ date: e.detail.value });
    this.load();
  },
  select(e) {
    this.setData({ selected: Number(e.currentTarget.dataset.index) });
  },
  input(e) {
    this.setData({ [e.currentTarget.dataset.key]: e.detail.value });
  },
  next() {
    if (this.data.selected < 0) return error(new Error("请选择机时"));
    if (
      this.data.step === 1 &&
      (!this.data.project || !this.data.contact || !this.data.settlement)
    )
      return error(new Error("请补全样品和结算信息"));
    this.setData({ step: this.data.step + 1 });
  },
  back() {
    this.setData({ step: this.data.step - 1 });
  },
  async submit() {
    if (this.data.busy) return;
    this.setData({ busy: true });
    try {
      const slot = this.data.slots[this.data.selected];
      if (!this.data.draftId) {
        const d = await request("/reservations", "POST", {
          instrument_id: this.data.id,
          start_at: slot.start_at,
          end_at: slot.end_at,
          samples: Number(this.data.samples),
          project: this.data.project,
          contact: this.data.contact,
          settlement: this.data.settlement,
        });
        this.setData({ draftId: d.id });
      }
      const r = await request(
        `/reservations/${this.data.draftId}/submit`,
        "POST",
        {},
      );
      wx.showModal({
        title: r.status === "Waitlisted" ? "已加入候补" : "预约已提交",
        content: "请在我的预约中查看进度。",
        showCancel: false,
        success: () => wx.switchTab({ url: "/pages/reservations/index" }),
      });
    } catch (e) {
      error(e);
    } finally {
      this.setData({ busy: false });
    }
  },
});
