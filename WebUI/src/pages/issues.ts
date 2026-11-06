/**
 * 问题反馈: the issue list is wired to the real API (`GET /v1/issues`) and shows
 * whatever the server returns, including its 501 while feedback is a P4
 * feature. Linking a revision, retesting and resolving stay disabled until P4.
 */

import type { Issue, IssueStatus } from "@qa/client";
import { dataTable, facts, formatTime, idText, row } from "../components/data.js";
import {
  attempt,
  button,
  createStatusArea,
  field,
  h,
  note,
  pageHeader,
  section,
  toolbar,
  type StatusArea,
} from "../components/ui.js";
import type { PageContext } from "../state.js";

const STATUS_OPTIONS: ReadonlyArray<readonly [IssueStatus | "", string]> = [
  ["", "全部"],
  ["open", "待处理"],
  ["linked", "已关联补库"],
  ["resolved", "已解决"],
];
const STATUS_LABEL: Record<IssueStatus, string> = { open: "待处理", linked: "已关联补库", resolved: "已解决" };

export function renderIssuesPage(ctx: PageContext): HTMLElement {
  const status = createStatusArea();
  const filter = h("select", { name: "status" });
  for (const [value, label] of STATUS_OPTIONS) filter.append(h("option", { value }, label));
  const table = dataTable("问题列表", ["问题", "状态", "回答 ID", "关联修订", "创建时间", "操作"]);
  const detail = h("div", { class: "detail" });

  const load = async (): Promise<void> => {
    table.setMessage("正在加载…");
    const outcome = await filterIssues(ctx, filter.value as IssueStatus | "", status);
    if (!outcome) {
      table.setMessage("加载失败，详见上方说明。", "error");
      return;
    }
    table.setRows(
      outcome.map((issue) =>
        row(
          [
            issue.question,
            STATUS_LABEL[issue.status ?? "open"],
            idText(issue.answer_id),
            idText(issue.linked_revision_id ?? null),
            formatTime(issue.created_at),
            button("查看", () => openIssue(issue, detail)),
          ],
          { "data-issue-id": issue.issue_id },
        ),
      ),
      "没有符合条件的问题。",
    );
  };

  void load();
  return h(
    "div",
    { class: "page" },
    pageHeader(
      "问题反馈",
      "反馈记录、补库关联与复测在 P4 实现；问题列表已接到真实接口，服务端目前对它返回 501。",
    ),
    section("问题列表", toolbar(field("状态", filter), button("查询", () => void load())), status.element, table.element),
    section("问题处理", detail, issueActions()),
  );
}

export async function filterIssues(ctx: PageContext, issueStatus: IssueStatus | "", status: StatusArea): Promise<Issue[] | null> {
  const outcome = await attempt(status, "查询问题", () =>
    ctx.client.listIssues(issueStatus ? { status: issueStatus } : undefined, { signal: ctx.signal }),
  );
  return outcome.ok ? outcome.value : null;
}

export function openIssue(issue: Issue, slot: HTMLElement): void {
  slot.replaceChildren(
    h("h3", {}, issue.question),
    facts([
      ["问题 ID", idText(issue.issue_id)],
      ["状态", STATUS_LABEL[issue.status ?? "open"]],
      ["回答 ID", idText(issue.answer_id)],
      ["关联修订", idText(issue.linked_revision_id ?? null)],
      ["关联版本", idText(issue.linked_version_id ?? null)],
      ["创建时间", formatTime(issue.created_at)],
    ]),
  );
}

function issueActions(): HTMLElement {
  return h(
    "fieldset",
    { class: "form", disabled: true },
    h("legend", {}, "补库与复测"),
    field("关联修订", h("input", { name: "revision_id" })),
    toolbar(
      h("button", { type: "button" }, "关联修订"),
      h("button", { type: "button" }, "复测"),
      h("button", { type: "button" }, "标记已解决"),
    ),
    note("关联修订、复测和标记已解决在 P4 实现。"),
  );
}
