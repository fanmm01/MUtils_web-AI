import type { Client } from "@qa/client";
import {
  button,
  createStatusArea,
  field,
  h,
  note,
  pageHeader,
  runAction,
  section,
  splitList,
  toolbar,
  type StatusArea,
} from "../components/ui.js";
import type { PageContext } from "../state.js";

export function renderKnowledgePage(ctx: PageContext): HTMLElement {
  const listStatus = createStatusArea();
  const list = section(
    "知识库列表",
    toolbar(button("刷新列表", () => void loadKnowledgeBases(ctx.client, listStatus))),
    listStatus.element,
    h(
      "table",
      { class: "table" },
      h("thead", {}, h("tr", {}, h("th", {}, "名称"), h("th", {}, "说明"), h("th", {}, "活动版本"))),
      h("tbody", {}, h("tr", {}, h("td", { colspan: "3", class: "empty" }, "尚未实现：没有可显示的知识库。"))),
    ),
  );

  const createStatus = createStatusArea();
  const name = h("input", { name: "name", required: true, maxlength: "200" });
  const description = h("textarea", { name: "description", rows: "2" });
  const tags = h("input", { name: "domain_tags", placeholder: "用逗号分隔，如 产品, 运维" });
  const form = h(
    "form",
    { class: "form", "aria-label": "新建知识库" },
    field("名称", name),
    field("说明", description),
    field("领域标签", tags),
    h("button", { type: "submit" }, "创建"),
    createStatus.element,
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void createKB(ctx.client, form, createStatus);
  });

  const routing = h(
    "fieldset",
    { class: "form", disabled: true },
    h("legend", {}, "编辑知识库与自动选库描述"),
    field("说明", h("textarea", { rows: "2" })),
    field("领域标签", h("input", {})),
    field("示例问题（每行一个）", h("textarea", { rows: "3" })),
    toolbar(h("button", { type: "button" }, "保存"), h("button", { type: "button" }, "删除知识库")),
    note("需要先从列表中选择知识库；列表尚未实现。"),
  );

  return h(
    "div",
    { class: "page" },
    pageHeader("知识库", "知识库的创建、修改、删除与查询将在 P2 实现；当前操作会如实显示服务端的 501 响应。"),
    list,
    section("新建知识库", form),
    section("编辑", routing),
  );
}

export function loadKnowledgeBases(client: Client, status: StatusArea): Promise<void> {
  return runAction(status, "加载知识库列表", () => client.listKBs());
}

export function createKB(client: Client, form: HTMLFormElement, status: StatusArea): Promise<void> {
  const data = new FormData(form);
  return runAction(status, "创建知识库", () =>
    client.createKB({
      name: String(data.get("name") ?? "").trim(),
      description: String(data.get("description") ?? ""),
      domain_tags: splitList(String(data.get("domain_tags") ?? ""), /[,，]/),
    }),
  );
}
