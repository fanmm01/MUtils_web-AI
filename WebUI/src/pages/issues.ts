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
  toolbar,
  type StatusArea,
} from "../components/ui.js";
import type { PageContext } from "../state.js";

const STATUS_OPTIONS: ReadonlyArray<readonly [string, string]> = [
  ["", "全部"],
  ["open", "待处理"],
  ["linked", "已关联补库"],
  ["resolved", "已解决"],
];

export function renderIssuesPage(ctx: PageContext): HTMLElement {
  const status = createStatusArea();
  const filter = h("select", { name: "status" });
  for (const [value, label] of STATUS_OPTIONS) filter.append(h("option", { value }, label));

  return h(
    "div",
    { class: "page" },
    pageHeader("问题反馈", "反馈记录、未回答问题、补库关联与复测将在 P4 实现。"),
    section(
      "问题列表",
      toolbar(
        field("状态", filter),
        button("查询", () => void filterIssues(ctx.client, filter.value, status)),
      ),
      status.element,
      note("尚未实现：没有可显示的问题。"),
    ),
    section(
      "问题处理",
      h(
        "fieldset",
        { class: "form", disabled: true },
        field("关联修订", h("input", {})),
        toolbar(
          h("button", { type: "button" }, "关联修订"),
          h("button", { type: "button" }, "复测"),
          h("button", { type: "button" }, "标记已解决"),
        ),
      ),
      note("需要先从列表中打开问题；问题处理尚未实现。"),
    ),
  );
}

export function filterIssues(client: Client, issueStatus: string, status: StatusArea): Promise<void> {
  return runAction(status, "查询问题", () =>
    client.listIssues(issueStatus ? { status: issueStatus } : undefined),
  );
}
