/**
 * Knowledge-base selector shared by the KB-scoped pages. The choice lives in
 * the URL (`?kb=`); this bar loads the list and the selected base from the
 * server and tells the page which base it works on.
 */

import type { KnowledgeBase } from "@qa/client";
import { formatHash, type PageContext, type RouteId } from "../state.js";
import { facts, idText } from "./data.js";
import { attempt, createStatusArea, field, h, isNotFound, type StatusArea } from "./ui.js";

const LIST_LIMIT = 200;

export interface KBContext {
  element: HTMLElement;
  /** Resolves with the selected base, or null when none is selected or it is gone. */
  ready: Promise<KnowledgeBase | null>;
  current(): KnowledgeBase | null;
  /** Re-read the selected base (e.g. after publish or rollback changed its active version). */
  refresh(): Promise<KnowledgeBase | null>;
}

export function kbContext(ctx: PageContext): KBContext {
  const status = createStatusArea();
  const select = h("select", { name: "kb" });
  select.append(h("option", { value: "" }, "（请选择知识库）"));
  const summary = h("div", { class: "kb-summary" });
  const element = h(
    "section",
    { class: "kb-bar", "aria-label": "当前知识库" },
    field("当前知识库", select),
    summary,
    status.element,
  );
  select.addEventListener("change", () => ctx.navigate(ctx.route, select.value || null));

  let selected: KnowledgeBase | null = null;
  const renderSummary = (): void => {
    if (!selected) {
      summary.replaceChildren(
        h("p", { class: "note" }, ctx.kbId ? "" : "请先选择一个知识库；也可以在“知识库”页新建。"),
      );
      return;
    }
    summary.replaceChildren(
      facts([
        ["知识库 ID", idText(selected.kb_id)],
        ["活动版本", selected.active_version_id ? idText(selected.active_version_id) : "尚未发布任何版本"],
      ]),
    );
  };

  const load = async (target: StatusArea): Promise<KnowledgeBase | null> => {
    if (!ctx.kbId) {
      selected = null;
      renderSummary();
      return null;
    }
    const outcome = await attempt(target, "读取知识库", () => ctx.client.getKB(ctx.kbId as string, { signal: ctx.signal }));
    if (!outcome.ok) {
      selected = null;
      if (isNotFound(outcome.error)) {
        target.done("所选知识库不存在或已删除，请重新选择。");
      }
      renderSummary();
      return null;
    }
    selected = outcome.value;
    ensureOption(select, selected.kb_id, selected.name);
    select.value = selected.kb_id;
    renderSummary();
    return selected;
  };

  const listStatus = createStatusArea();
  element.append(listStatus.element);
  void attempt(listStatus, "加载知识库列表", () =>
    ctx.client.listKBs({ limit: LIST_LIMIT }, { signal: ctx.signal }),
  ).then((outcome) => {
    if (!outcome.ok || ctx.signal.aborted) return;
    for (const kb of outcome.value.items ?? []) ensureOption(select, kb.kb_id, kb.name);
    if (selected) select.value = selected.kb_id;
    if (outcome.value.next_cursor) {
      listStatus.done(`下拉框只列出前 ${LIST_LIMIT} 个知识库；其余的请在“知识库”页选择。`);
    }
  });

  renderSummary();
  const ready = load(status);
  return {
    element,
    ready,
    current: () => selected,
    refresh: () => load(status),
  };
}

/** Link to another admin page that keeps the selected knowledge base. */
export function pageLink(ctx: PageContext, route: RouteId, label: string): HTMLAnchorElement {
  return h("a", { href: formatHash(route, ctx.kbId), class: "page-link" }, label);
}

function ensureOption(select: HTMLSelectElement, value: string, label: string): void {
  const existing = [...select.options].find((option) => option.value === value);
  if (existing) existing.textContent = label;
  else select.append(h("option", { value }, label));
}
