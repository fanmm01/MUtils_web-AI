# 问答插件（WebWidget）

可嵌入任意网页的悬浮问答插件。当前是 **P1 框架版**：悬浮图标、弹窗、知识库范围控件和推理配置占位已可用；问答本身尚未实现，提交问题会得到服务端的 `501 FEATURE_NOT_IMPLEMENTED`，插件如实显示该错误，不展示假回答。

## 构建

```bash
npm run build -w @qa/widget
```

产物：

- `dist/qa-widget.iife.js`：普通 `<script>` 引入，暴露 `window.QAWidget` 并自动挂载。
- `dist/qa-widget.js`：ES 模块，供打包工具引入。

样式在 Shadow DOM 内，不污染宿主页面，宿主 CSS 也改不到插件内部。

## 一段 script 接入

```html
<script
  src="https://qa.example.com/widget/qa-widget.iife.js"
  data-api-base="https://qa.example.com"
  data-title="产品问答"
  data-position="bottom-right"
  data-kb-ids="kb_product,kb_faq"
  data-max-kbs="2"
  defer
></script>
```

| 属性 | 说明 |
| --- | --- |
| `data-api-base` | 问答服务绝对地址；缺省时不自动挂载 |
| `data-title` | 弹窗标题，默认“问答助手” |
| `data-position` | `bottom-right`（默认）或 `bottom-left` |
| `data-selection-mode` | `auto`（默认）或 `explicit` |
| `data-kb-ids` | 逗号分隔；auto 模式下为候选库，explicit 模式下为检索库 |
| `data-max-kbs` | auto 模式最多选几个库 |
| `data-open` | `true` 时挂载后直接展开 |
| `data-auto-mount` | `false` 时只加载脚本，由宿主调用 `QAWidget.mount()` |

data 属性只放非敏感配置。知识库权限由服务端票据决定，前端配置无法扩大权限。

## 代码挂载与凭据

私有知识库需要宿主后端先校验用户身份，再换取短期票据。插件通过回调读取票据，不写入 localStorage、cookie 或 URL：

```js
const handle = QAWidget.mount({
  apiBase: "https://qa.example.com",
  getCredential: () => fetch("/my-backend/qa-ticket").then((r) => r.text()),
  initialSelection: { mode: "explicit", targets: [{ kb_id: "kb_product" }] },
});

handle.open();
handle.close();
await handle.setSelection({ mode: "auto", max_kbs: 2 });
handle.getSelection();
handle.destroy(); // 移除 DOM 与全部事件监听
```

P1 服务端尚未签发票据（`POST /v1/widget/tickets` 返回 501），因此私有接入只能等 P3。

## 多实例

每次 `mount()` 创建独立实例：各自的 Shadow DOM、状态和会话。同一个 `<script>` 元素不会重复自动挂载。

## 跨域

插件跨域调用时，问答服务需把宿主站点加入 `QA_ALLOWED_ORIGINS`。CORS 只是辅助限制，不替代身份验证。

## P1 尚未实现

- 知识库目录（`GET /v1/knowledge-catalog`）返回 501，单库/多库控件无法列出知识库；未选库时下一轮仍使用当前显示的范围。
- 推理配置选择是禁用占位，插件不发送 `inference` 字段。
- 回答流、引用详情、反馈、取消和新会话在 P3/P4 实现。
