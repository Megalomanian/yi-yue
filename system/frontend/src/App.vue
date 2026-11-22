<script setup>
import {
  ref,
  reactive,
  computed,
  onMounted,
  onBeforeUnmount,
  nextTick,
  watch,
} from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search,
  Calendar,
  Monitor,
  DataAnalysis,
  Document,
  User,
  Message,
  Setting,
  ArrowRight,
  SwitchButton,
  Check,
  Plus,
  Refresh,
  Download,
  Bell,
  Reading,
  Tools,
} from "@element-plus/icons-vue";
import * as echarts from "echarts/core";
import { BarChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { api, post, download } from "./api";
import { labels, roles, money, today, stamp, estimate } from "./utils";
echarts.use([
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
]);

const ssoLoginUrl = import.meta.env.VITE_SSO_LOGIN_URL || "";
const me = ref(null),
  busy = ref(false),
  loading = ref(false),
  tab = ref("instruments"),
  authMode = ref("login");
const auth = reactive({
  username: "student",
  password: "Demo12345!",
  name: "",
  department: "",
  contact: "",
  identity_info: "",
  consent: false,
});
const instruments = ref([]),
  reservations = ref([]),
  notifications = ref([]),
  qualifications = ref([]),
  violations = ref([]),
  users = ref([]),
  audits = ref([]),
  enrollments = ref([]),
  allQualifications = ref([]),
  maintenance = ref([]);
const query = ref(""),
  category = ref(""),
  statusFilter = ref(""),
  selected = ref(null),
  slotDate = ref(today(1)),
  slots = ref([]),
  bookVisible = ref(false),
  step = ref(0),
  bookId = ref(null);
const booking = reactive({
  instrument_id: null,
  start_at: "",
  end_at: "",
  samples: 1,
  project: "",
  contact: "",
  settlement: "",
});
const editor = ref(false),
  editId = ref(null),
  instrumentForm = reactive({});
const course = ref(null),
  examVisible = ref(false),
  examInstrument = ref(null),
  answers = ref([-1, -1, -1, -1, -1]);
const stats = ref(null),
  chartEl = ref(null),
  period = reactive({
    caliber: "national",
    from: today().slice(0, 4) + "-01-01",
    to: today(),
  });
const detail = ref(null),
  detailsVisible = ref(false);
const integration = ref(null),
  historyPage = ref(1),
  historyFrom = ref(""),
  historyTo = ref("");
let chart, refreshTimer;
const staff = computed(() => ["ADMIN", "MANAGER"].includes(me.value?.role)),
  admin = computed(() => me.value?.role === "ADMIN"),
  researcher = computed(() => ["USER", "EXTERNAL"].includes(me.value?.role)),
  reporter = computed(() => ["ADMIN", "DEPARTMENT"].includes(me.value?.role));
const menus = computed(() =>
  [
    { id: "instruments", name: "仪器资源", icon: Monitor, show: true },
    {
      id: "reservations",
      name: staff.value ? "预约工作台" : "我的预约",
      icon: Calendar,
      show: me.value?.role !== "DEPARTMENT",
    },
    {
      id: "billing",
      name: "结算与报告",
      icon: Document,
      show: me.value?.role !== "DEPARTMENT",
    },
    {
      id: "training",
      name: "培训与资质",
      icon: Reading,
      show: me.value?.role !== "DEPARTMENT",
    },
    {
      id: "credit",
      name: "信用与申诉",
      icon: User,
      show: researcher.value || admin.value,
    },
    {
      id: "statistics",
      name: "绩效报表",
      icon: DataAnalysis,
      show: reporter.value,
    },
    { id: "maintenance", name: "设备维保", icon: Tools, show: staff.value },
    { id: "users", name: "用户审核", icon: User, show: admin.value },
    { id: "audits", name: "操作审计", icon: Setting, show: admin.value },
    { id: "integrations", name: "系统对接", icon: Setting, show: admin.value },
    { id: "notifications", name: "消息中心", icon: Message, show: true },
  ].filter((m) => m.show),
);
const title = computed(
  () => menus.value.find((x) => x.id === tab.value)?.name || "仪器资源",
);
const categories = computed(() => [
  ...new Set(instruments.value.map((i) => i.category)),
]);
const visibleInstruments = computed(() =>
  instruments.value.filter(
    (i) =>
      (!category.value || i.category === category.value) &&
      `${i.name} ${i.model} ${i.code}`
        .toLowerCase()
        .includes(query.value.toLowerCase()),
  ),
);
const visibleReservations = computed(() =>
  reservations.value.filter(
    (r) => !statusFilter.value || r.status === statusFilter.value,
  ),
);
const completed = computed(() =>
  reservations.value.filter((r) => r.status === "Completed"),
);
const unread = computed(
  () => notifications.value.filter((n) => !n.is_read).length,
);
const pending = computed(
  () => reservations.value.filter((r) => r.status === "Pending").length,
);
const rate = computed(() =>
  Number(
    selected.value?.[
      me.value?.role === "EXTERNAL" ? "external_price" : "price"
    ] || 0,
  ),
);
const quote = computed(() =>
  estimate(booking.start_at, booking.end_at, rate.value),
);
const statisticsExportPath = computed(
  () => `/statistics/export?${new URLSearchParams(period)}`,
);
const postAction = async (path, body = {}, message = "操作成功") =>
  run(async () => {
    await post(path, body);
    ElMessage.success(message);
    await load();
  });
async function run(action) {
  if (busy.value) return;
  busy.value = true;
  try {
    return await action();
  } catch (e) {
    if (e !== "cancel" && e !== "close")
      ElMessage.error(e.message || "操作未完成");
  } finally {
    busy.value = false;
  }
}
async function login() {
  await run(async () => {
    if (authMode.value === "register") {
      await post("/auth/register", auth);
      ElMessage.success("注册成功，等待实名审核");
      authMode.value = "login";
      return;
    }
    const data = await post("/auth/login", auth);
    sessionStorage.setItem("iy-token", data.token);
    me.value = data.user;
    await load();
  });
}
function logout() {
  sessionStorage.removeItem("iy-token");
  me.value = null;
  tab.value = "instruments";
  instruments.value = [];
  reservations.value = [];
  notifications.value = [];
  chart?.dispose();
  chart = null;
}
async function load() {
  if (!me.value) return;
  loading.value = true;
  try {
    me.value = await api("/me");
    if (!me.value.approved) return;
    const jobs = [
      api("/instruments").then((x) => (instruments.value = x)),
      api("/notifications").then((x) => (notifications.value = x)),
    ];
    const historyParams = new URLSearchParams({
      page: historyPage.value,
      size: 100,
    });
    if (historyFrom.value) historyParams.set("from", historyFrom.value);
    if (historyTo.value) historyParams.set("to", historyTo.value);
    if (me.value.role !== "DEPARTMENT")
      jobs.push(
        api(`/reservations?${historyParams}`).then(
          (x) => (reservations.value = x),
        ),
        api("/qualifications").then((x) => (qualifications.value = x)),
        api("/training/enrollments").then((x) => (enrollments.value = x)),
      );
    if (researcher.value || admin.value)
      jobs.push(api("/violations").then((x) => (violations.value = x)));
    if (admin.value)
      jobs.push(
        api("/users").then((x) => (users.value = x)),
        api("/audits").then((x) => (audits.value = x)),
        api("/qualifications/all").then((x) => (allQualifications.value = x)),
        api("/integrations").then((x) => (integration.value = x)),
      );
    if (staff.value)
      jobs.push(api("/maintenance").then((x) => (maintenance.value = x)));
    await Promise.all(jobs);
    if (tab.value === "statistics") await loadStats();
  } finally {
    loading.value = false;
  }
}
async function startBooking(i) {
  selected.value = i;
  bookId.value = null;
  Object.assign(booking, {
    instrument_id: i.id,
    start_at: "",
    end_at: "",
    samples: 1,
    project: "",
    contact: "",
    settlement: "",
  });
  step.value = 0;
  bookVisible.value = true;
  await fetchSlots();
}
async function fetchSlots() {
  if (!selected.value) return;
  await run(async () => {
    slots.value = await api(
      `/instruments/${selected.value.id}/slots?date=${slotDate.value}`,
    );
  });
}
function pickSlot(s) {
  booking.start_at = s.start_at;
  booking.end_at = s.end_at;
}
function nextStep() {
  if (step.value === 0 && !booking.start_at)
    return ElMessage.warning("请选择一个可预约或候补时段");
  if (
    step.value === 1 &&
    (!booking.project.trim() ||
      !booking.contact.trim() ||
      !booking.settlement.trim())
  )
    return ElMessage.warning("请补全检测项目、联系方式和结算信息");
  step.value++;
}
async function submitBooking(draftOnly = false) {
  await run(async () => {
    if (!bookId.value) bookId.value = (await post("/reservations", booking)).id;
    else
      await api(`/reservations/${bookId.value}`, {
        method: "PUT",
        body: booking,
      });
    if (!draftOnly) {
      const r = await post(`/reservations/${bookId.value}/submit`);
      ElMessage.success(
        r.status === "Waitlisted"
          ? "已加入候补队列"
          : "预约已提交，等待机组审批",
      );
    } else ElMessage.success("草稿已保存");
    bookVisible.value = false;
    tab.value = "reservations";
    await load();
  });
}
async function editReservation(r) {
  selected.value = instruments.value.find((i) => i.id === r.instrument_id);
  bookId.value = r.id;
  Object.assign(booking, r);
  slotDate.value = r.start_at.slice(0, 10);
  step.value = 1;
  bookVisible.value = true;
  await fetchSlots();
}
async function scheduleMaintenance(i) {
  await run(async () => {
    const a = await ElMessageBox.prompt(
      "输入计划开始时间，例如 2026-11-12T09:00",
      "计划维保",
      { inputValue: today(1) + "T09:00" },
    );
    const b = await ElMessageBox.prompt("输入计划结束时间", "计划维保", {
      inputValue: today(1) + "T12:00",
    });
    const reason = await ElMessageBox.prompt(
      "填写检修原因，冲突预约将被免违约取消。",
      "计划维保",
    );
    await post(`/instruments/${i.id}/maintenance`, {
      action: "schedule",
      start_at: a.value,
      end_at: b.value,
      reason: reason.value,
    });
    await load();
  });
}
async function recordDamage() {
  await run(async () => {
    const rid = await ElMessageBox.prompt(
      "填写已上机或完成的预约编号",
      "登记设备损坏",
    );
    const points = await ElMessageBox.prompt(
      "填写扣分（1—100）",
      "登记设备损坏",
    );
    const reason = await ElMessageBox.prompt(
      "填写已核实的事实与证据说明",
      "登记设备损坏",
    );
    await post("/violations", {
      reservation_id: Number(rid.value),
      points: Number(points.value),
      reason: reason.value,
    });
    await load();
  });
}
async function reject(r) {
  await run(async () => {
    const { value } = await ElMessageBox.prompt(
      "请填写驳回原因，系统将通知申请人",
      "驳回预约",
      { inputValidator: (v) => !!v?.trim() || "驳回理由不能为空" },
    );
    await post(`/reservations/${r.id}/approval`, {
      approve: false,
      reason: value,
    });
    await load();
  });
}
async function cancel(r) {
  await run(async () => {
    await ElMessageBox.confirm(
      "取消后将释放时段，并通知候补用户。",
      "取消预约",
    );
    await post(`/reservations/${r.id}/cancel`);
    await load();
  });
}
async function checkin(r) {
  await run(async () => {
    const { value } = await ElMessageBox.prompt(
      "请扫描机位二维码，或输入机位上标注的仪器编号。",
      "上机签到",
      {
        inputPlaceholder: `仪器编号 ${r.instrument_id}`,
        inputValidator: (v) => /^\d+$/.test(v || "") || "请输入数字仪器编号",
      },
    );
    await post(`/reservations/${r.id}/checkin`, {
      instrument_id: Number(value),
    });
    ElMessage.success("签到成功，开始计时");
    await load();
  });
}
async function checkout(r) {
  await run(async () => {
    await ElMessageBox.confirm(
      "确认用户已下机？系统将根据实际时长和预约单价生成费用单。",
      "下机结算",
    );
    await post(`/reservations/${r.id}/checkout`);
    ElMessage.success("结算完成");
    await load();
  });
}
async function upload(r, event) {
  const file = event.target.files?.[0];
  if (!file) return;
  await run(async () => {
    const body = new FormData();
    body.append("file", file);
    await api(`/reservations/${r.id}/reports`, { method: "POST", body });
    ElMessage.success("报告已加密归档并通知用户");
    await load();
  });
  event.target.value = "";
}
async function adjust(bill) {
  await run(async () => {
    const { value } = await ElMessageBox.prompt(
      "输入冲正金额，可为负数。原始费用将保留。",
      "费用冲正",
      {
        inputValidator: (v) =>
          /^-?\d+(\.\d{1,2})?$/.test(v || "") || "请输入有效金额",
      },
    );
    const reason = await ElMessageBox.prompt("请填写冲正原因", "费用冲正", {
      inputValidator: (v) => !!v?.trim() || "原因不能为空",
    });
    await post(`/bills/${bill.id}`, {
      action: "adjust",
      adjustment: value,
      reason: reason.value,
    });
    await load();
  });
}
function openEditor(i) {
  editId.value = i?.id || null;
  Object.assign(
    instrumentForm,
    i || {
      code: "",
      name: "",
      model: "",
      category: "",
      location: "",
      department: "",
      price: 100,
      external_price: 200,
      asset_value: 500000,
      group_id: 1,
      open_hour: 8,
      close_hour: 18,
    },
  );
  editor.value = true;
}
async function saveInstrument() {
  await run(async () => {
    await api("/instruments" + (editId.value ? `/${editId.value}` : ""), {
      method: editId.value ? "PUT" : "POST",
      body: instrumentForm,
    });
    editor.value = false;
    ElMessage.success("仪器台账已保存");
    await load();
  });
}
async function importInstruments(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  await run(async () => {
    await post("/instruments/import", JSON.parse(await file.text()));
    ElMessage.success("批量导入完成");
    await load();
  });
  event.target.value = "";
}
async function stopInstrument(i) {
  await run(async () => {
    const { value } = await ElMessageBox.prompt(
      "停用将免违约取消尚未开始的预约。请填写故障或检修原因。",
      "登记维保停用",
      { inputValidator: (v) => !!v?.trim() || "原因不能为空" },
    );
    await post(`/instruments/${i.id}/maintenance`, {
      action: "stop",
      reason: value,
    });
    await load();
  });
}
async function beginExam(i) {
  await run(async () => {
    course.value = await api("/training/course");
    examInstrument.value = i;
    answers.value = [-1, -1, -1, -1, -1];
    examVisible.value = true;
  });
}
async function submitExam() {
  await run(async () => {
    if (answers.value.includes(-1)) throw new Error("请完成全部题目");
    const result = await post(
      `/training/${examInstrument.value.id}/exam`,
      answers.value,
    );
    ElMessage[result.passed ? "success" : "warning"](
      `${result.score}分，${result.passed ? "考核合格，资质已颁发" : "未达到80分，请复习后补考"}`,
    );
    examVisible.value = false;
    await load();
  });
}
async function appeal(v) {
  await run(async () => {
    const { value } = await ElMessageBox.prompt(
      "请说明申诉事实和依据",
      "信用申诉",
      { inputValidator: (v) => !!v?.trim() || "请填写申诉说明" },
    );
    await post(`/violations/${v.id}`, { appeal: value });
    await load();
  });
}
async function identity(u) {
  await run(async () => {
    const data = await api(`/users/${u.id}/identity`);
    await ElMessageBox.alert(
      `实名材料：${data.identity_info}\n联系方式：${data.contact}`,
      "实名审核材料",
      { confirmButtonText: "已查看" },
    );
  });
}
async function loadStats() {
  stats.value = await api(`/statistics?${new URLSearchParams(period)}`);
  await nextTick();
  if (!chartEl.value) return;
  chart?.dispose();
  chart = echarts.init(chartEl.value);
  chart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: 48, right: 24, top: 25, bottom: 70 },
    xAxis: {
      type: "category",
      data: stats.value.rows.map((r) => r.name),
      axisLabel: { interval: 0, width: 130, overflow: "truncate", rotate: 10 },
    },
    yAxis: { type: "value", name: "机时 / h" },
    series: [
      {
        name: "实际机时",
        type: "bar",
        data: stats.value.rows.map((r) => r.hours),
        itemStyle: { color: "#1f6feb", borderRadius: [5, 5, 0, 0] },
        barMaxWidth: 44,
      },
      {
        name: "对外机时",
        type: "bar",
        data: stats.value.rows.map((r) => r.external_hours),
        itemStyle: { color: "#36b5a3", borderRadius: [5, 5, 0, 0] },
        barMaxWidth: 44,
      },
    ],
    legend: { bottom: 0 },
  });
}
function detailRow(r) {
  detail.value = r;
  detailsVisible.value = true;
}
function resize() {
  chart?.resize();
}
watch(tab, async (value) => {
  if (value === "statistics") await run(loadStats);
});
onMounted(async () => {
  const ticket = new URLSearchParams(location.search).get("ticket");
  if (ticket) {
    history.replaceState({}, "", location.pathname);
    await run(async () => {
      const result = await post("/auth/sso-ticket", { ticket });
      sessionStorage.setItem("iy-token", result.token);
    });
  }
  window.addEventListener("iy-session-expired", logout);
  window.addEventListener("resize", resize);
  if (sessionStorage.getItem("iy-token"))
    await run(async () => {
      me.value = await api("/me");
      await load();
    });
  refreshTimer = setInterval(() => {
    if (me.value && !busy.value && !loading.value)
      api("/notifications")
        .then((x) => (notifications.value = x))
        .catch(() => {});
  }, 60000);
});
onBeforeUnmount(() => {
  clearInterval(refreshTimer);
  window.removeEventListener("iy-session-expired", logout);
  window.removeEventListener("resize", resize);
  chart?.dispose();
});
</script>

<template>
  <div v-if="!me" class="auth-layout">
    <section class="auth-brand">
      <div class="brand">
        <span class="brand-mark">仪</span
        ><span>仪约 <small>INSTRUMENT HUB</small></span>
      </div>
      <div class="auth-story">
        <span class="eyebrow">OPEN SCIENCE · SHARED RESOURCES</span>
        <h1>让每一次探索，<br />都有仪可依。</h1>
        <p>
          连接科研需求与专业设备，让仪器共享更高效。<br />从预约到成果，每一步清晰可见。
        </p>
        <div class="orbit">
          <div class="orbit-core">IY<span>共享 · 协作 · 发现</span></div>
          <span class="orbit-label one">材料表征</span
          ><span class="orbit-label two">色谱分析</span
          ><span class="orbit-label three">光谱研究</span>
        </div>
      </div>
      <footer>高校大型仪器设备开放共享预约平台</footer>
    </section>
    <section class="auth-form">
      <div class="auth-card">
        <span class="eyebrow">欢迎使用仪约</span>
        <h2>{{ authMode === "login" ? "登录工作空间" : "校外用户注册" }}</h2>
        <p class="muted">
          {{
            authMode === "login"
              ? "访问仪器资源，开启您的科研工作。"
              : "提交实名信息，经管理员审核后即可预约。"
          }}
        </p>
        <el-form label-position="top" @submit.prevent="login">
          <el-form-item label="账号"
            ><el-input
              v-model="auth.username"
              aria-label="账号"
              autocomplete="username"
          /></el-form-item>
          <el-form-item label="密码"
            ><el-input
              v-model="auth.password"
              aria-label="密码"
              type="password"
              show-password
              autocomplete="current-password"
          /></el-form-item>
          <template v-if="authMode === 'register'"
            ><el-form-item label="真实姓名"
              ><el-input v-model="auth.name" /></el-form-item
            ><el-form-item label="单位"
              ><el-input v-model="auth.department" /></el-form-item
            ><el-form-item label="联系方式"
              ><el-input v-model="auth.contact" /></el-form-item
            ><el-form-item label="实名核验材料说明"
              ><el-input
                v-model="auth.identity_info"
                type="textarea"
                placeholder="单位、身份和可核验的材料信息" /></el-form-item
            ><el-checkbox v-model="auth.consent"
              >同意将上述信息用于实名审核与仪器服务，按学校留存期限加密保存。</el-checkbox
            ></template
          >
          <el-button
            type="primary"
            native-type="submit"
            :loading="busy"
            class="login-button"
            >{{ authMode === "login" ? "登录平台" : "提交注册" }}</el-button
          > </el-form
        ><button
          class="text-button"
          @click="authMode = authMode === 'login' ? 'register' : 'login'"
        >
          {{ authMode === "login" ? "校外用户？注册账号" : "返回登录" }}
        </button>
        <a v-if="ssoLoginUrl" :href="ssoLoginUrl" class="sso-link"
          >校内统一身份认证登录</a
        >
        <div class="demo-hint">
          本地演示账号：student / manager / admin / department<br />演示密码：Demo12345!<br /><small
            >生产环境使用部署时配置的账号，演示账号不会自动创建。</small
          >
        </div>
      </div>
    </section>
  </div>
  <div v-else class="app-layout">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">仪</span
        ><span>仪约 <small>INSTRUMENT HUB</small></span>
      </div>
      <div class="workspace-label">科研共享工作空间</div>
      <nav>
        <button
          v-for="m in menus"
          :key="m.id"
          :class="{ active: tab === m.id }"
          @click="
            tab = m.id;
            statusFilter = '';
          "
          :data-testid="`nav-${m.id}`"
        >
          <el-icon><component :is="m.icon" /></el-icon><span>{{ m.name }}</span
          ><span v-if="m.id === 'notifications' && unread" class="count">{{
            unread
          }}</span>
        </button>
      </nav>
      <div class="sidebar-bottom">
        <span class="live-dot"></span>开放共享 · 协同创新
        <div>InstrumentHub / IY</div>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <div class="breadcrumb">
          工作空间 <span>/</span> <strong>{{ title }}</strong>
        </div>
        <div class="topbar-right">
          <button
            class="icon-button"
            aria-label="消息中心"
            @click="tab = 'notifications'"
          >
            <el-badge :value="unread" :hidden="!unread"
              ><el-icon><Bell /></el-icon
            ></el-badge>
          </button>
          <div class="user-avatar">{{ me.name.slice(0, 1) }}</div>
          <div class="user-name">
            {{ me.name }}<small>{{ roles[me.role] }}</small>
          </div>
          <button class="icon-button" aria-label="退出登录" @click="logout">
            <el-icon><SwitchButton /></el-icon>
          </button>
        </div>
      </header>
      <main v-loading="loading">
        <div class="mobile-shortcuts">
          <button
            v-for="m in menus"
            :key="m.id"
            :class="{ active: tab === m.id }"
            @click="tab = m.id"
          >
            {{ m.name }}
          </button>
        </div>
        <div v-if="!me.approved" class="panel empty">
          <h2>实名审核中</h2>
          <p>您的注册已提交，管理员核验后即可使用仪器预约服务。</p>
          <el-button @click="run(load)">刷新审核状态</el-button>
        </div>
        <template v-else>
          <section class="page-heading">
            <div>
              <div class="eyebrow">
                INSTRUMENT HUB / {{ tab.toUpperCase() }}
              </div>
              <h1>{{ title }}</h1>
              <p>
                {{
                  tab === "instruments"
                    ? "发现专业设备，选择合适机时，让科研计划有序推进。"
                    : tab === "reservations"
                      ? "预约、审批与上机进度，在这里一目了然。"
                      : "每一条记录，都是可靠科研服务的一部分。"
                }}
              </p>
            </div>
            <el-button :icon="Refresh" @click="run(load)" :loading="loading"
              >刷新数据</el-button
            >
          </section>
          <template v-if="tab === 'instruments'">
            <div class="resource-banner">
              <div>
                <span class="banner-tag">共享资源 · 随时可见</span>
                <h2>下一次发现，从这里开始</h2>
                <p>未来 14 天机时在线可查，支持半小时预约与有序候补。</p>
              </div>
              <div class="banner-numbers">
                <strong>{{
                  instruments.filter((i) => i.status === "Open").length
                }}</strong
                ><span>台仪器开放中</span>
              </div>
              <div class="banner-grid" aria-hidden="true">
                <i v-for="n in 9" :key="n"></i>
              </div>
            </div>
            <div class="metric-row">
              <div class="mini-metric">
                <span>仪器资源</span
                ><strong>{{ instruments.length }}<small>台</small></strong>
              </div>
              <div class="mini-metric">
                <span>{{ staff ? "待审批预约" : "我的预约" }}</span
                ><strong
                  >{{ staff ? pending : reservations.length
                  }}<small>单</small></strong
                >
              </div>
              <div class="mini-metric">
                <span>{{ researcher ? "当前信用分" : "已完成服务" }}</span
                ><strong
                  >{{ researcher ? me.credit : completed.length
                  }}<small>{{ researcher ? "分" : "次" }}</small></strong
                >
              </div>
              <div class="mini-metric">
                <span>未读通知</span
                ><strong>{{ unread }}<small>条</small></strong>
              </div>
            </div>
            <div class="section-toolbar">
              <div class="search-controls">
                <el-input
                  v-model="query"
                  placeholder="搜索仪器名称、型号或编号"
                  :prefix-icon="Search"
                  clearable
                  aria-label="搜索仪器"
                /><el-select v-model="category" placeholder="全部分类" clearable
                  ><el-option
                    v-for="c in categories"
                    :key="c"
                    :value="c"
                    :label="c"
                /></el-select>
              </div>
              <div v-if="admin" class="actions">
                <label class="file-button"
                  >批量导入<input
                    type="file"
                    accept=".json"
                    @change="importInstruments" /></label
                ><el-button
                  type="primary"
                  :icon="Plus"
                  @click="openEditor(null)"
                  >仪器建档</el-button
                >
              </div>
            </div>
            <div class="resource-count">
              共 {{ visibleInstruments.length }} 台仪器
              <span>实时开放状态 · 校内 / 校外价格</span>
            </div>
            <div class="instrument-grid">
              <article
                v-for="(i, index) in visibleInstruments"
                :key="i.id"
                class="instrument-card"
                :data-testid="`instrument-${i.id}`"
              >
                <div class="instrument-visual" :class="`visual-${index % 4}`">
                  <span class="instrument-category">{{ i.category }}</span
                  ><span
                    :class="[
                      'status',
                      i.status === 'Open' ? 'Approved' : 'NoShow',
                    ]"
                    >{{ i.status === "Open" ? "开放预约" : "维保停用" }}</span
                  >
                  <div class="instrument-drawing">
                    <div class="machine-top"></div>
                    <div class="machine-body">
                      <div class="machine-window"><i></i></div>
                      <div class="machine-controls"><b></b><b></b><b></b></div>
                    </div>
                    <div class="machine-base"></div>
                  </div>
                  <span class="instrument-code">{{ i.code }}</span>
                </div>
                <div class="instrument-info">
                  <h3>{{ i.name }}</h3>
                  <p class="model">{{ i.model }}</p>
                  <div class="instrument-meta">
                    <span>⌖ {{ i.location }}</span
                    ><span>{{ i.department }}</span>
                  </div>
                  <div class="instrument-footer">
                    <div class="price">
                      <strong
                        >¥{{
                          money(
                            i[
                              me.role === "EXTERNAL"
                                ? "external_price"
                                : "price"
                            ],
                          )
                        }}</strong
                      ><span>/ 小时</span
                      ><small>{{
                        me.role === "EXTERNAL" ? "校外服务价" : "校内服务价"
                      }}</small>
                    </div>
                    <el-button
                      v-if="researcher"
                      type="primary"
                      :disabled="i.status !== 'Open'"
                      @click="startBooking(i)"
                      >查看机时<el-icon><ArrowRight /></el-icon></el-button
                    ><el-button v-else @click="startBooking(i)"
                      >查看机时</el-button
                    >
                  </div>
                  <div v-if="admin" class="admin-card-actions">
                    <span
                      >台账来源：{{
                        i.source === "local" ? "本地建档" : "外部同步"
                      }}</span
                    ><button
                      class="text-button"
                      :disabled="i.source !== 'local'"
                      @click="openEditor(i)"
                    >
                      编辑台账
                    </button>
                  </div>
                </div>
              </article>
            </div>
            <div v-if="!visibleInstruments.length" class="panel empty">
              未找到匹配的仪器，请清除搜索条件后重试。
            </div>
          </template>

          <template v-if="tab === 'reservations'"
            ><div class="history-controls">
              <el-date-picker
                v-model="historyFrom"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="预约开始日期"
              /><el-date-picker
                v-model="historyTo"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="预约结束日期"
              /><el-button
                @click="
                  historyPage = 1;
                  run(load);
                "
                >查询历史</el-button
              ><el-button
                :disabled="historyPage === 1"
                @click="
                  historyPage--;
                  run(load);
                "
                >上一页</el-button
              ><span>第 {{ historyPage }} 页</span
              ><el-button
                :disabled="reservations.length&lt;100"
                @click="
                  historyPage++;
                  run(load);
                "
                >下一页</el-button
              >
            </div>
            <div class="status-tabs">
              <button
                :class="{ selected: !statusFilter }"
                @click="statusFilter = ''"
              >
                全部预约 <b>{{ reservations.length }}</b></button
              ><button
                v-for="s in [
                  'Pending',
                  'Approved',
                  'Waitlisted',
                  'InUse',
                  'Completed',
                  'Draft',
                ]"
                :key="s"
                :class="{ selected: statusFilter === s }"
                @click="statusFilter = s"
              >
                {{ labels[s] }}
                <b>{{ reservations.filter((r) => r.status === s).length }}</b>
              </button>
            </div>
            <div class="panel table-panel">
              <table>
                <thead>
                  <tr>
                    <th>预约 / 仪器</th>
                    <th>使用时段</th>
                    <th>申请人</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in visibleReservations" :key="r.id">
                    <td>
                      <button class="record-link" @click="detailRow(r)">
                        {{ r.instrument_name }}</button
                      ><small
                        >#IY-{{ String(r.id).padStart(5, "0") }} ·
                        {{ r.project }}</small
                      >
                    </td>
                    <td>
                      {{ stamp(r.start_at)
                      }}<small>至 {{ stamp(r.end_at) }}</small>
                    </td>
                    <td>
                      {{ r.user_name
                      }}<small
                        >信用 {{ r.credit }} 分 · {{ r.samples }} 份样品</small
                      >
                    </td>
                    <td>
                      <span :class="['status', r.status]">{{
                        labels[r.status]
                      }}</span
                      ><small
                        v-if="r.confirmed === false && r.status === 'Approved'"
                        >待确认 · {{ stamp(r.confirm_by) }}</small
                      >
                    </td>
                    <td>
                      <div class="row-actions">
                        <template v-if="staff && r.status === 'Pending'"
                          ><el-button
                            size="small"
                            type="primary"
                            @click="
                              postAction(`/reservations/${r.id}/approval`, {
                                approve: true,
                              })
                            "
                            >批准</el-button
                          ><el-button size="small" @click="reject(r)"
                            >驳回</el-button
                          ></template
                        ><el-button
                          v-if="r.status === 'Draft' && researcher"
                          size="small"
                          @click="editReservation(r)"
                          >编辑</el-button
                        ><el-button
                          v-if="r.status === 'Draft' && researcher"
                          size="small"
                          type="primary"
                          @click="postAction(`/reservations/${r.id}/submit`)"
                          >提交草稿</el-button
                        ><el-button
                          v-if="r.status === 'Draft' && researcher"
                          size="small"
                          @click="
                            run(async () => {
                              await api(`/reservations/${r.id}`, {
                                method: 'DELETE',
                              });
                              await load();
                            })
                          "
                          >删除</el-button
                        ><el-button
                          v-if="r.status === 'Approved' && !r.confirmed"
                          size="small"
                          type="primary"
                          @click="postAction(`/reservations/${r.id}/confirm`)"
                          >确认补位</el-button
                        ><el-button
                          v-if="r.status === 'Approved' && r.confirmed"
                          size="small"
                          type="primary"
                          @click="checkin(r)"
                          >上机签到</el-button
                        ><el-button
                          v-if="r.status === 'InUse' && staff"
                          size="small"
                          type="primary"
                          @click="checkout(r)"
                          >下机结算</el-button
                        ><el-button
                          v-if="['Approved', 'Waitlisted'].includes(r.status)"
                          size="small"
                          @click="cancel(r)"
                          >取消</el-button
                        ><span
                          v-if="
                            [
                              'Completed',
                              'Cancelled',
                              'Rejected',
                              'NoShow',
                            ].includes(r.status)
                          "
                          class="muted"
                          >{{ r.reason || "流程已结束" }}</span
                        >
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!visibleReservations.length" class="empty">
                暂无此状态的预约。可前往仪器资源选择机时。
              </div>
            </div>
            <p class="footnote">
              待审批预约如需撤回，请联系机组驳回；使用中预约须先下机结算。机位签到支持二维码或人工核验编号。
            </p></template
          >

          <template v-if="tab === 'billing'"
            ><div class="section-toolbar">
              <p class="muted">
                按签到与下机时间结算，保留原始费用和冲正记录。
              </p>
              <el-button
                v-if="admin"
                :icon="Download"
                @click="run(() => download('/bills/export', '财务核销.csv'))"
                >导出财务核销单</el-button
              >
            </div>
            <div class="panel table-panel">
              <table>
                <thead>
                  <tr>
                    <th>预约</th>
                    <th>实际机时 / 单价</th>
                    <th>结算金额</th>
                    <th>费用状态</th>
                    <th>检测报告</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in completed" :key="r.id">
                    <td>
                      {{ r.instrument_name
                      }}<small>#{{ r.id }} · {{ r.user_name }}</small>
                    </td>
                    <td>
                      {{ Number(r.bills[0]?.hours).toFixed(4) }} h<small
                        >¥{{ money(r.rate) }} / h</small
                      >
                    </td>
                    <td>
                      <strong
                        >¥{{
                          money(
                            Number(r.bills[0]?.amount) +
                              Number(r.bills[0]?.adjustment),
                          )
                        }}</strong
                      ><small v-if="Number(r.bills[0]?.adjustment)"
                        >冲正 ¥{{ money(r.bills[0].adjustment) }} ·
                        {{ r.bills[0].adjustment_reason }}</small
                      >
                    </td>
                    <td>
                      <span
                        :class="[
                          'status',
                          r.bills[0]?.verified ? 'Completed' : 'Pending',
                        ]"
                        >{{
                          r.bills[0]?.verified ? "已线下核销" : "待线下核销"
                        }}</span
                      ><small>{{ r.bills[0]?.method }}</small>
                    </td>
                    <td>
                      <div v-for="f in r.reports" :key="f.id">
                        <button
                          class="text-button"
                          @click="
                            run(() =>
                              download(`/reports/${f.id}/download`, f.filename),
                            )
                          "
                        >
                          {{ f.filename }}
                        </button>
                      </div>
                      <span v-if="!r.reports.length" class="muted"
                        >待机组交付</span
                      >
                    </td>
                    <td>
                      <div v-if="staff" class="row-actions">
                        <el-button
                          size="small"
                          @click="
                            postAction(`/bills/${r.bills[0].id}`, {
                              action: 'verify',
                            })
                          "
                          :disabled="r.bills[0]?.verified"
                          >核销</el-button
                        ><el-button size="small" @click="adjust(r.bills[0])"
                          >冲正</el-button
                        ><label class="file-button"
                          >上传报告<input
                            type="file"
                            accept=".pdf,.csv,.txt,.zip"
                            @change="upload(r, $event)"
                        /></label>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!completed.length" class="empty">
                暂无已完成的预约。下机结算后，费用单与报告会显示在这里。
              </div>
            </div></template
          >

          <template v-if="tab === 'training'"
            ><div class="notice">
              独立上机前，须完成培训报名、机组初审与安全考核。80
              分合格，资质有效期一年，到期前 30 天提醒复训。
            </div>
            <div v-if="researcher" class="training-grid">
              <article
                v-for="i in instruments"
                :key="i.id"
                class="panel training-card"
              >
                <el-icon class="training-icon"><Reading /></el-icon>
                <h3>{{ i.name }}</h3>
                <p>
                  {{
                    qualifications.find(
                      (q) => q.instrument_id === i.id && !q.revoked,
                    )
                      ? "资质有效至 " +
                        stamp(
                          qualifications.find((q) => q.instrument_id === i.id)
                            .expires_at,
                        )
                      : "尚未取得有效上机资质"
                  }}
                </p>
                <el-button
                  v-if="!enrollments.some((e) => e.instrument_id === i.id)"
                  @click="
                    postAction(
                      '/training/enrollments',
                      { instrument_id: i.id },
                      '培训报名已提交',
                    )
                  "
                  >报名培训</el-button
                ><el-button
                  v-else-if="
                    !enrollments.find((e) => e.instrument_id === i.id)?.approved
                  "
                  disabled
                  >等待资格初审</el-button
                ><el-button v-else type="primary" plain @click="beginExam(i)"
                  >学习与考核</el-button
                >
              </article>
            </div>
            <div v-if="staff" class="panel table-panel">
              <h3>培训报名审核</h3>
              <table>
                <thead>
                  <tr>
                    <th>申请人</th>
                    <th>仪器</th>
                    <th>初审状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="e in enrollments" :key="e.id">
                    <td>{{ e.user_name }}</td>
                    <td>{{ e.instrument_name }}</td>
                    <td>{{ e.approved ? "已通过" : "待审核" }}</td>
                    <td>
                      <el-button
                        size="small"
                        :disabled="e.approved"
                        @click="
                          postAction(`/training/enrollments/${e.id}/approve`)
                        "
                        >通过初审</el-button
                      >
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="admin" class="panel table-panel spaced">
              <h3>资质授权台账</h3>
              <table>
                <thead>
                  <tr>
                    <th>用户</th>
                    <th>仪器</th>
                    <th>到期时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="q in allQualifications" :key="q.id">
                    <td>{{ q.user_name }}</td>
                    <td>{{ q.instrument_name }}</td>
                    <td>{{ stamp(q.expires_at) }}</td>
                    <td>
                      <el-button
                        size="small"
                        :disabled="q.revoked"
                        @click="
                          run(async () => {
                            await ElMessageBox.confirm(
                              '撤销后用户须重新通过初审和考核。',
                              '撤销上机资质',
                            );
                            await post(`/qualifications/${q.id}/revoke`);
                            await load();
                          })
                        "
                        >{{ q.revoked ? "已撤销" : "撤销资质" }}</el-button
                      >
                    </td>
                  </tr>
                </tbody>
              </table>
            </div></template
          >

          <template v-if="tab === 'credit'"
            ><el-button v-if="admin" class="spaced" @click="recordDamage"
              >登记设备损坏</el-button
            >
            <div class="credit-summary panel">
              <div class="credit-score">
                {{ me.credit }}<span>当前信用分</span>
              </div>
              <div>
                <h2>守时履约，让共享更顺畅</h2>
                <p>
                  初始 100 分，低于 60 分暂停预约。未签到扣 20 分，超时占用扣 10
                  分；有异议可提交申诉。
                </p>
              </div>
            </div>
            <div class="panel table-panel spaced">
              <table>
                <thead>
                  <tr>
                    <th>预约</th>
                    <th>认定原因</th>
                    <th>扣分</th>
                    <th>申诉说明</th>
                    <th>处理状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in violations" :key="v.id">
                    <td>#{{ v.reservation_id }}</td>
                    <td>{{ v.reason }}</td>
                    <td>-{{ v.points }}</td>
                    <td>{{ v.appeal || "—" }}</td>
                    <td>
                      {{
                        v.resolved
                          ? v.restored
                            ? "申诉成立，已恢复"
                            : "维持认定"
                          : "可申诉 / 待复核"
                      }}
                    </td>
                    <td>
                      <el-button
                        v-if="!admin"
                        size="small"
                        :disabled="v.resolved"
                        @click="appeal(v)"
                        >提交申诉</el-button
                      >
                      <div
                        v-else-if="!v.resolved && v.appeal"
                        class="row-actions"
                      >
                        <el-button
                          size="small"
                          @click="
                            postAction(`/violations/${v.id}`, {
                              action: 'resolve',
                              restore: true,
                            })
                          "
                          >恢复分数</el-button
                        ><el-button
                          size="small"
                          @click="
                            postAction(`/violations/${v.id}`, {
                              action: 'resolve',
                              restore: false,
                            })
                          "
                          >维持认定</el-button
                        >
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!violations.length" class="empty">
                暂无违约记录。感谢您按时使用共享仪器。
              </div>
            </div></template
          >

          <template v-if="tab === 'statistics'"
            ><div class="panel statistics-filters">
              <el-select v-model="period.caliber" aria-label="统计口径"
                ><el-option
                  label="国家口径 ≥50万元"
                  value="national" /><el-option
                  label="地方口径 ≥20万元"
                  value="local" /><el-option
                  label="校内口径 ≥40万元"
                  value="campus" /></el-select
              ><el-date-picker
                v-model="period.from"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="开始日期"
              /><span>至</span
              ><el-date-picker
                v-model="period.to"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="结束日期"
              /><el-button
                type="primary"
                :loading="busy"
                @click="run(loadStats)"
                >生成报表</el-button
              ><el-button
                :icon="Download"
                :disabled="busy"
                @click="
                  run(() => download(statisticsExportPath, '开放共享绩效.csv'))
                "
                >导出 CSV</el-button
              >
            </div>
            <template v-if="stats"
              ><div class="metric-row spaced">
                <div class="mini-metric">
                  <span>累计有效机时</span
                  ><strong
                    >{{ Number(stats.hours).toFixed(2)
                    }}<small>h</small></strong
                  >
                </div>
                <div class="mini-metric">
                  <span>对外服务机时</span
                  ><strong
                    >{{ Number(stats.external_hours).toFixed(2)
                    }}<small>h</small></strong
                  >
                </div>
                <div class="mini-metric">
                  <span>机时利用率</span
                  ><strong>{{ stats.utilization }}<small>%</small></strong>
                </div>
                <div class="mini-metric">
                  <span>服务人次</span
                  ><strong>{{ stats.visits }}<small>次</small></strong>
                </div>
              </div>
              <div class="panel spaced">
                <div class="panel-title">
                  <h3>仪器开放共享概览</h3>
                  <span class="muted"
                    >共 {{ stats.instruments }} 台仪器纳入当前口径</span
                  >
                </div>
                <div ref="chartEl" class="chart"></div>
              </div>
              <div class="panel table-panel spaced">
                <table>
                  <thead>
                    <tr>
                      <th>仪器</th>
                      <th>机组 / 院系</th>
                      <th>有效机时</th>
                      <th>可开放机时</th>
                      <th>利用率</th>
                      <th>对外服务机时</th>
                      <th>服务人次</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="r in stats.rows" :key="r.id">
                      <td>{{ r.name }}</td>
                      <td>{{ r.group_id }} / {{ r.department }}</td>
                      <td>{{ Number(r.hours).toFixed(2) }}</td>
                      <td>{{ Number(r.available_hours).toFixed(2) }}</td>
                      <td>{{ r.utilization }}%</td>
                      <td>{{ Number(r.external_hours).toFixed(2) }}</td>
                      <td>{{ r.visits }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="footnote">
                利用率 = 实际开机机时 ÷ 可开放机时 ×
                100%。可开放机时扣除维保时段；跨周期使用按时间交集分摊机时。
              </p>
              <el-button
                :icon="Download"
                @click="run(() => download('/bills/export', '财务核销.csv'))"
                >导出财务核销数据</el-button
              ></template
            ></template
          >

          <template v-if="tab === 'maintenance'"
            ><div class="panel table-panel">
              <table>
                <thead>
                  <tr>
                    <th>仪器</th>
                    <th>位置</th>
                    <th>当前状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="i in instruments.filter(
                      (i) => admin || i.group_id === me.group_id,
                    )"
                    :key="i.id"
                  >
                    <td>{{ i.name }}</td>
                    <td>{{ i.location }}</td>
                    <td>
                      <span
                        :class="[
                          'status',
                          i.status === 'Open' ? 'Approved' : 'NoShow',
                        ]"
                        >{{ i.status === "Open" ? "开放中" : "维保停用" }}</span
                      >
                    </td>
                    <td>
                      <el-button
                        v-if="i.status === 'Open'"
                        size="small"
                        @click="stopInstrument(i)"
                        >登记故障 / 停用</el-button
                      ><el-button
                        v-if="i.status === 'Open'"
                        size="small"
                        @click="scheduleMaintenance(i)"
                        >计划维保</el-button
                      ><el-button
                        v-else
                        size="small"
                        type="primary"
                        @click="
                          postAction(`/instruments/${i.id}/maintenance`, {
                            action: 'restore',
                          })
                        "
                        >维修完成，恢复开放</el-button
                      >
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="panel table-panel spaced">
              <h3>维修记录</h3>
              <table>
                <thead>
                  <tr>
                    <th>仪器</th>
                    <th>原因</th>
                    <th>停用时间</th>
                    <th>恢复时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="m in maintenance" :key="m.id">
                    <td>{{ m.name }}</td>
                    <td>{{ m.reason }}</td>
                    <td>{{ stamp(m.start_at) }}</td>
                    <td>{{ stamp(m.closed_at) }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!maintenance.length" class="empty">暂无维保记录</div>
            </div></template
          >
          <template v-if="tab === 'users'"
            ><div class="notice">
              校外账号须完成实名核验。审核材料加密保存，查看和审批操作均记入审计。
            </div>
            <div class="panel table-panel">
              <table>
                <thead>
                  <tr>
                    <th>姓名 / 账号</th>
                    <th>角色</th>
                    <th>单位</th>
                    <th>信用</th>
                    <th>审核状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="u in users" :key="u.id">
                    <td>
                      {{ u.name }}<small>{{ u.username }}</small>
                    </td>
                    <td>{{ roles[u.role] }}</td>
                    <td>{{ u.department }}</td>
                    <td>{{ u.credit }}</td>
                    <td>{{ u.approved ? "已审核" : "待实名审核" }}</td>
                    <td>
                      <div v-if="u.role === 'EXTERNAL'" class="row-actions">
                        <el-button size="small" @click="identity(u)"
                          >查看材料</el-button
                        ><el-button
                          size="small"
                          :disabled="u.approved"
                          @click="postAction(`/users/${u.id}/approve`)"
                          >审核通过</el-button
                        >
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div></template
          >
          <template v-if="tab === 'audits'"
            ><div class="notice">
              保留登录、审批、结算、导出和授权变更记录。审计数据不提供前端删除入口。
            </div>
            <div class="panel table-panel">
              <table>
                <thead>
                  <tr>
                    <th>记录编号</th>
                    <th>操作人</th>
                    <th>操作类型</th>
                    <th>对象编号</th>
                    <th>时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="a in audits" :key="a.id">
                    <td>{{ a.id }}</td>
                    <td>{{ a.actor_id === 0 ? "系统任务" : a.actor_id }}</td>
                    <td>{{ a.action }}</td>
                    <td>{{ a.object_id }}</td>
                    <td>{{ stamp(a.created_at) }}</td>
                  </tr>
                </tbody>
              </table>
            </div></template
          >
          <template v-if="tab === 'integrations' && integration"
            ><div class="notice">
              统一认证：{{ integration.sso_configured ? "已配置" : "待接入" }} ·
              微信消息网关：{{
                integration.wechat_gateway_configured ? "已配置" : "待接入"
              }}
              · 既有平台回写：{{
                integration.upstream_configured ? "已配置" : "待接入"
              }}。未接入微信时，通知保留在站内消息中心。
            </div>
            <div class="panel table-panel">
              <table>
                <thead>
                  <tr>
                    <th>事件</th>
                    <th>渠道</th>
                    <th>投递状态</th>
                    <th>尝试次数</th>
                    <th>下次尝试</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="e in integration.events" :key="e.id">
                    <td>#{{ e.id }}</td>
                    <td>
                      {{
                        e.channel === "notification" ? "微信消息" : "机时回写"
                      }}
                    </td>
                    <td>
                      {{ e.status }}<small>{{ e.last_error }}</small>
                    </td>
                    <td>{{ e.attempts }}</td>
                    <td>{{ stamp(e.next_at) }}</td>
                    <td>
                      <el-button
                        size="small"
                        :disabled="
                          !['Failed', 'Sending', 'Retry'].includes(e.status)
                        "
                        @click="
                          postAction(`/integrations/events/${e.id}/retry`)
                        "
                        >重试</el-button
                      >
                    </td>
                  </tr>
                </tbody>
              </table>
            </div></template
          ><template v-if="tab === 'notifications'"
            ><div class="panel notification-list">
              <article
                v-for="n in notifications"
                :key="n.id"
                :class="{ unread: !n.is_read }"
              >
                <div class="notification-icon">
                  <el-icon><Bell /></el-icon>
                </div>
                <div>
                  <h3>{{ n.message }}</h3>
                  <p>{{ stamp(n.created_at) }} · 站内通知</p>
                </div>
                <el-button
                  v-if="!n.is_read"
                  size="small"
                  @click="
                    postAction(
                      `/notifications/${n.id}/read`,
                      {},
                      '已标记为已读',
                    )
                  "
                  >标记已读</el-button
                ><span v-else class="muted">已读</span>
              </article>
              <div v-if="!notifications.length" class="empty">
                暂无消息。预约审批、报告交付和资质提醒将在这里通知您。
              </div>
            </div></template
          >
        </template>
        <footer class="page-footer">
          仪约 InstrumentHub <span>让设备开放，让科研连接。</span>
        </footer>
      </main>
    </div>
    <van-tabbar
      v-if="researcher"
      class="mobile-tabs"
      :model-value="tab"
      @update:model-value="tab = $event"
      ><van-tabbar-item name="instruments" icon="home-o"
        >仪器资源</van-tabbar-item
      ><van-tabbar-item name="reservations" icon="calendar-o"
        >我的预约</van-tabbar-item
      ><van-tabbar-item name="notifications" icon="user-o" :badge="unread || ''"
        >我的消息</van-tabbar-item
      ></van-tabbar
    >
  </div>

  <el-dialog
    v-model="bookVisible"
    :title="selected?.name + ' · 预约机时'"
    width="720px"
    destroy-on-close
    ><el-steps :active="step" simple finish-status="success"
      ><el-step title="选择机时" /><el-step title="填写信息" /><el-step
        title="确认提交"
    /></el-steps>
    <div v-if="step === 0" class="booking-step">
      <div class="slot-toolbar">
        <el-date-picker
          v-model="slotDate"
          value-format="YYYY-MM-DD"
          type="date"
          :clearable="false"
          :disabled-date="
            (d) => d < new Date(today()) || d >= new Date(today(14))
          "
          @change="fetchSlots"
        /><span class="muted">每格30分钟，已占用可加入候补</span>
      </div>
      <div class="slot-grid">
        <button
          v-for="s in slots"
          :key="s.start_at"
          :disabled="['停用', '已过期'].includes(s.state)"
          :class="{
            chosen: booking.start_at === s.start_at,
            wait: s.state === '候补',
          }"
          @click="pickSlot(s)"
        >
          <strong>{{ s.start_at.slice(11) }}</strong
          ><span>{{ s.state }}</span>
        </button>
      </div>
      <div v-if="booking.start_at" class="duration-row">
        结束时间
        <el-select v-model="booking.end_at"
          ><el-option
            v-for="s in slots.filter((s) => s.end_at > booking.start_at)"
            :key="s.end_at"
            :label="s.end_at.slice(11)"
            :value="s.end_at" /></el-select
        ><span>预估 ¥{{ money(quote) }}</span>
      </div>
    </div>
    <el-form v-if="step === 1" label-position="top" class="booking-step"
      ><el-form-item label="样品数量"
        ><el-input-number
          v-model="booking.samples"
          :min="1"
          :max="10000" /></el-form-item
      ><el-form-item label="检测项目 / 样品说明" required
        ><el-input
          v-model="booking.project"
          type="textarea"
          maxlength="500"
          placeholder="填写样品类型、检测目的及注意事项" /></el-form-item
      ><el-form-item label="联系方式" required
        ><el-input v-model="booking.contact" maxlength="100" /></el-form-item
      ><el-form-item
        :label="me?.role === 'EXTERNAL' ? '对公结算信息' : '经费卡号 / 项目号'"
        required
        ><el-input v-model="booking.settlement" maxlength="100" /></el-form-item
    ></el-form>
    <div v-if="step === 2" class="booking-step">
      <div class="confirmation">
        <h3>{{ selected?.name }}</h3>
        <p>{{ stamp(booking.start_at) }} 至 {{ stamp(booking.end_at) }}</p>
        <p>{{ booking.samples }} 份样品 · {{ booking.project }}</p>
        <div>
          预估费用 <strong>¥{{ money(quote) }}</strong>
        </div>
        <small
          >最终金额以实际使用机时结算；同一时段存在竞争时进入候补队列。</small
        >
      </div>
      <div class="notice">
        签到时限为开始后15分钟。请确认有效资质与信用分不低于60分。
      </div>
    </div>
    <template #footer
      ><el-button v-if="step > 0" @click="step--">上一步</el-button
      ><el-button
        v-if="step < 2"
        type="primary"
        :disabled="!researcher"
        @click="nextStep"
        >下一步</el-button
      ><template v-else
        ><el-button :loading="busy" @click="submitBooking(true)"
          >保存草稿</el-button
        ><el-button
          type="primary"
          :loading="busy"
          @click="submitBooking(false)"
          data-testid="confirm-booking"
          >确认预约</el-button
        ></template
      ></template
    ></el-dialog
  >
  <el-dialog
    v-model="editor"
    :title="editId ? '编辑仪器台账' : '仪器建档'"
    width="680px"
    ><el-form label-position="top" class="two-column-form"
      ><el-form-item
        v-for="field in [
          { k: 'code', n: '仪器编号' },
          { k: 'name', n: '仪器名称' },
          { k: 'model', n: '型号' },
          { k: 'category', n: '分类' },
          { k: 'location', n: '放置地点' },
          { k: 'department', n: '院系 / 机组名称' },
        ]"
        :key="field.k"
        :label="field.n"
        required
        ><el-input v-model="instrumentForm[field.k]" /></el-form-item
      ><el-form-item
        v-for="field in [
          { k: 'price', n: '校内单价（元/小时）' },
          { k: 'external_price', n: '校外单价（元/小时）' },
          { k: 'asset_value', n: '资产价值（元）' },
          { k: 'group_id', n: '机组编号' },
          { k: 'open_hour', n: '开放开始小时' },
          { k: 'close_hour', n: '开放结束小时' },
        ]"
        :key="field.k"
        :label="field.n"
        ><el-input-number
          v-model="instrumentForm[field.k]"
          :min="0"
          :max="
            ['open_hour', 'close_hour'].includes(field.k) ? 24 : 1000000000
          " /></el-form-item></el-form
    ><template #footer
      ><el-button @click="editor = false">取消</el-button
      ><el-button type="primary" :loading="busy" @click="saveInstrument"
        >保存台账</el-button
      ></template
    ></el-dialog
  >
  <el-dialog v-model="examVisible" title="安全培训与资质考核" width="720px"
    ><template v-if="course"
      ><h3>{{ course.title }}</h3>
      <div class="course-material">
        <p v-for="(m, i) in course.material" :key="m">{{ i + 1 }}. {{ m }}</p>
      </div>
      <div v-for="(q, i) in course.questions" :key="i" class="exam-question">
        <h4>{{ i + 1 }}. {{ q.question }}</h4>
        <el-radio-group v-model="answers[i]"
          ><el-radio v-for="(option, j) in q.options" :key="j" :value="j">{{
            option
          }}</el-radio></el-radio-group
        >
      </div></template
    ><template #footer
      ><el-button type="primary" :loading="busy" @click="submitExam"
        >提交考核</el-button
      ></template
    ></el-dialog
  >
  <el-dialog v-model="detailsVisible" title="预约详情" width="600px"
    ><template v-if="detail"
      ><el-descriptions :column="1" border
        ><el-descriptions-item label="预约编号"
          >#{{ detail.id }}</el-descriptions-item
        ><el-descriptions-item label="仪器">{{
          detail.instrument_name
        }}</el-descriptions-item
        ><el-descriptions-item label="时段"
          >{{ stamp(detail.start_at) }} —
          {{ stamp(detail.end_at) }}</el-descriptions-item
        ><el-descriptions-item label="状态">{{
          labels[detail.status]
        }}</el-descriptions-item
        ><el-descriptions-item label="检测项目">{{
          detail.project
        }}</el-descriptions-item
        ><el-descriptions-item label="联系方式">{{
          detail.contact
        }}</el-descriptions-item
        ><el-descriptions-item label="结算信息">{{
          detail.settlement
        }}</el-descriptions-item
        ><el-descriptions-item label="说明">{{
          detail.reason || "—"
        }}</el-descriptions-item
        ><el-descriptions-item label="签到 / 下机"
          >{{ stamp(detail.checked_at) }} /
          {{ stamp(detail.ended_at) }}</el-descriptions-item
        ></el-descriptions
      ></template
    ></el-dialog
  >
</template>
