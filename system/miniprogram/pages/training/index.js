const { request, error } = require("../../utils/api");
Page({
  data: { items: [], course: null, current: 0, answers: [-1, -1, -1, -1, -1] },
  onLoad() {
    this.load();
  },
  async load() {
    try {
      const items = await request("/instruments"),
        enrollments = await request("/training/enrollments");
      this.setData({
        items: items.map((i) => ({
          ...i,
          enrollment: enrollments.find((e) => e.instrument_id === i.id) || null,
        })),
      });
    } catch (e) {
      error(e);
    }
  },
  async enroll(e) {
    try {
      await request("/training/enrollments", "POST", {
        instrument_id: e.currentTarget.dataset.id,
      });
      this.load();
    } catch (err) {
      error(err);
    }
  },
  async exam(e) {
    try {
      this.setData({
        course: await request("/training/course"),
        current: e.currentTarget.dataset.id,
        answers: [-1, -1, -1, -1, -1],
      });
    } catch (err) {
      error(err);
    }
  },
  answer(e) {
    this.setData({
      ["answers[" + e.currentTarget.dataset.index + "]"]: Number(
        e.detail.value,
      ),
    });
  },
  async submit() {
    try {
      if (this.data.answers.includes(-1)) throw new Error("请完成全部题目");
      const r = await request(
        `/training/${this.data.current}/exam`,
        "POST",
        this.data.answers,
      );
      wx.showModal({
        title: r.score + "分",
        content: r.passed ? "考核通过，资质已颁发" : "未达到80分，请复习后补考",
        showCancel: false,
      });
      this.setData({ course: null });
      this.load();
    } catch (e) {
      error(e);
    }
  },
});
