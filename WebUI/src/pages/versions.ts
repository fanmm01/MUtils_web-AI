import { field, h, note, pageHeader, section, toolbar } from "../components/ui.js";

export function renderVersionPage(): HTMLElement {
  return h(
    "div",
    { class: "page" },
    pageHeader("版本", "版本列表、差异、发布与回滚将在 P2 实现。"),
    section("版本列表", note("需要先选择知识库；版本管理尚未实现，没有可显示的版本。")),
    section(
      "版本差异",
      h(
        "fieldset",
        { class: "form", disabled: true },
        field("左侧版本", h("select", {}, h("option", {}, "（无）"))),
        field("右侧版本", h("select", {}, h("option", {}, "（无）"))),
        h("button", { type: "button" }, "比较"),
      ),
    ),
    section(
      "发布与回滚",
      toolbar(
        h("button", { type: "button", disabled: true }, "发布所选版本"),
        h("button", { type: "button", disabled: true }, "回滚到所选版本"),
      ),
      note("发布与回滚尚未实现。"),
    ),
  );
}
