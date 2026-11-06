/**
 * 知识库: list, create, edit (incl. the auto-selection description) and delete.
 * The selected base is kept in the URL and used by the other KB pages.
 */

import type { KnowledgeBase, UpdateKB } from "@qa/client";
import { confirmStrip, dataTable, formatTime, idText, row } from "../components/data.js";
import {
  attempt,
  button,
  createStatusArea,
  describeError,
  field,
  h,
  isConflict,
  isNotFound,
  note,
  pageIntro,
  section,
  splitList,
  toolbar,
  type StatusArea,
} from "../components/ui.js";
import type { PageContext } from "../state.js";

const PAGE_SIZE = 50;

export function renderKnowledgePage(ctx: PageContext): HTMLElement {
  const notice = createStatusArea();
  if (ctx.notice) notice.ok(ctx.notice);

  const listStatus = createStatusArea();
  const table = dataTable("知识库列表", ["名称", "说明", "领域标签", "活动版本", "更新时间", "操作"]);
  let cursor: string | null = null;
  const more = button("加载更多", () => void loadKnowledgeBases(false));
  more.hidden = true;

  const kbRow = (kb: KnowledgeBase): HTMLTableRowElement => {
    const selected = kb.kb_id === ctx.kbId;
    let action: HTMLElement;
    if (selected) {
      action = h("span", { class: "badge" }, "当前");
    } else {
      action = button("选择", () => ctx.navigate("knowledge", kb.kb_id));
      action.setAttribute("aria-label", `选择知识库 ${kb.name}`);
    }
    const attrs: Record<string, string> = { "data-kb-id": kb.kb_id };
    if (selected) attrs["aria-current"] = "true";
    return row(
      [
        kb.name,
        kb.description || "—",
        (kb.domain_tags ?? []).join("、") || "—",
        kb.active_version_id ? idText(kb.active_version_id) : "尚未发布",
        formatTime(kb.updated_at),
        action,
      ],
      attrs,
    );
  };

  async function loadKnowledgeBases(reset: boolean): Promise<void> {
    if (reset) {
      cursor = null;
      table.setMessage("正在加载…");
    }
    const query = reset || !cursor ? { limit: PAGE_SIZE } : { limit: PAGE_SIZE, cursor };
    const outcome = await attempt(listStatus, "加载知识库列表", () =>
      ctx.client.listKBs(query, { signal: ctx.signal }),
    );
    if (!outcome.ok) {
      if (reset) table.setMessage(`加载失败：${describeError(outcome.error).title}`, "error");
      return;
    }
    const rows = (outcome.value.items ?? []).map(kbRow);
    if (reset) table.setRows(rows, "还没有知识库。可以在下方“新建知识库”创建第一个。");
    else table.appendRows(rows);
    cursor = outcome.value.next_cursor ?? null;
    more.hidden = !cursor;
  }

  const createStatus = createStatusArea();
  const form = h(
    "form",
    { class: "form", "aria-label": "新建知识库" },
    ...kbFields(),
    h("button", { type: "submit" }, "创建"),
    createStatus.element,
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void createKB(ctx, form, createStatus);
  });

  const editor = h("div", {});
  if (ctx.kbId) void loadEditor(ctx, ctx.kbId, editor, () => void loadKnowledgeBases(true));
  else editor.append(note("在列表中选择一个知识库后，可在这里修改名称、说明和自动选库描述，或删除它。"));

  void loadKnowledgeBases(true);
  return h(
    "div",
    { class: "page" },
    pageIntro("知识库", "创建、修改和删除知识库，维护自动选库使用的说明、领域标签和示例问题。选中的知识库用于“导入”“内容”“版本”页。"),
    notice.element,
    section("知识库列表", toolbar(button("刷新列表", () => void loadKnowledgeBases(true))), listStatus.element, table.element, more),
    section("新建知识库", form),
    section("编辑所选知识库", editor),
  );
}

function kbFields(kb?: KnowledgeBase): HTMLElement[] {
  const name = h("input", { name: "name", required: true, maxlength: "200" });
  const description = h("textarea", { name: "description", rows: "2" });
  const tags = h("input", { name: "domain_tags", placeholder: "用逗号分隔，如 产品, 运维" });
  const examples = h("textarea", { name: "routing_examples", rows: "3", placeholder: "每行一个示例问题" });
  if (kb) {
    name.value = kb.name;
    description.value = kb.description ?? "";
    tags.value = (kb.domain_tags ?? []).join(", ");
    examples.value = (kb.routing_examples ?? []).join("\n");
  }
  return [
    field("名称", name),
    field("说明", description),
    field("领域标签", tags),
    field("示例问题（每行一个）", examples),
  ];
}

interface KBForm {
  name: string;
  description: string;
  domain_tags: string[];
  routing_examples: string[];
}

/** One form shape for create (CreateKB) and edit (UpdateKB); edit sends every field. */
function readKBForm(form: HTMLFormElement): KBForm & UpdateKB {
  const data = new FormData(form);
  return {
    name: String(data.get("name") ?? "").trim(),
    description: String(data.get("description") ?? ""),
    domain_tags: splitList(String(data.get("domain_tags") ?? ""), /[,，、]/),
    routing_examples: splitList(String(data.get("routing_examples") ?? ""), /\r?\n/),
  };
}

export async function createKB(ctx: PageContext, form: HTMLFormElement, status: StatusArea): Promise<void> {
  const outcome = await attempt(status, "创建知识库", () => ctx.client.createKB(readKBForm(form), { signal: ctx.signal }));
  if (!outcome.ok) return;
  ctx.navigate("knowledge", outcome.value.kb_id, `已创建知识库“${outcome.value.name}”，并设为当前知识库。`);
}

async function loadEditor(ctx: PageContext, kbId: string, slot: HTMLElement, onSaved: () => void): Promise<void> {
  const status = createStatusArea();
  slot.replaceChildren(status.element);
  const outcome = await attempt(status, "读取知识库", () => ctx.client.getKB(kbId, { signal: ctx.signal }));
  if (!outcome.ok) {
    if (isNotFound(outcome.error)) {
      slot.append(toolbar(button("清除选择", () => ctx.navigate("knowledge", null))));
    }
    return;
  }
  slot.replaceChildren(editForm(ctx, outcome.value, onSaved));
}

function editForm(ctx: PageContext, kb: KnowledgeBase, onSaved: () => void): HTMLElement {
  let current = kb;
  const status = createStatusArea();
  const confirmSlot = h("div", {});
  const deleteButton = button("删除知识库", () => void deleteKB(ctx, current, confirmSlot, status, reloadButton));
  deleteButton.classList.add("danger");
  const fields = kbFields(kb);
  const form = h(
    "form",
    { class: "form", "aria-label": "编辑知识库" },
    h("fieldset", { class: "form" }, h("legend", {}, "基本信息"), ...fields.slice(0, 1)),
    h(
      "fieldset",
      { class: "form" },
      h("legend", {}, "自动选库描述"),
      ...fields.slice(1),
      note("说明、领域标签和示例问题是自动选库的匹配依据。"),
    ),
    toolbar(h("button", { type: "submit" }, "保存修改"), deleteButton),
    confirmSlot,
    status.element,
  );

  const reload = async (): Promise<void> => {
    const outcome = await attempt(status, "重新加载知识库", () => ctx.client.getKB(current.kb_id, { signal: ctx.signal }));
    if (!outcome.ok) return;
    current = outcome.value;
    form.replaceWith(editForm(ctx, current, onSaved));
  };
  function reloadButton(): HTMLElement {
    return toolbar(button("重新加载", () => void reload()));
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void updateKB(ctx, current, form, status, reloadButton).then((saved) => {
      if (!saved) return;
      current = saved;
      onSaved();
    });
  });
  return form;
}

/** Save name and auto-selection description in one PATCH guarded by the ETag. */
export async function updateKB(
  ctx: PageContext,
  kb: KnowledgeBase,
  form: HTMLFormElement,
  status: StatusArea,
  reloadButton: () => HTMLElement,
): Promise<KnowledgeBase | null> {
  const outcome = await attempt(status, "保存知识库", () =>
    ctx.client.updateKB(kb.kb_id, readKBForm(form), kb.etag, { signal: ctx.signal }),
  );
  if (outcome.ok) {
    status.ok("已保存。");
    return outcome.value;
  }
  if (isConflict(outcome.error)) {
    status.fail(
      "保存知识库",
      describeError(outcome.error),
      h("p", {}, "知识库已被其他操作修改。重新加载会用服务端的最新内容替换你未保存的修改。"),
      reloadButton(),
    );
  }
  return null;
}

export async function deleteKB(
  ctx: PageContext,
  kb: KnowledgeBase,
  confirmSlot: HTMLElement,
  status: StatusArea,
  reloadButton: () => HTMLElement,
): Promise<void> {
  if (!(await confirmStrip(confirmSlot, `确认删除知识库“${kb.name}”？删除后它不再出现在列表中。`, "确认删除"))) return;
  const outcome = await attempt(status, "删除知识库", () => ctx.client.deleteKB(kb.kb_id, kb.etag, { signal: ctx.signal }));
  if (outcome.ok) {
    ctx.navigate("knowledge", null, `已删除知识库“${kb.name}”。`);
    return;
  }
  if (isConflict(outcome.error)) {
    // 409 covers both a concurrent edit (ETag) and the server's guard: only an empty base
    // with no versions can be deleted. The server's message above says which.
    status.fail(
      "删除知识库",
      describeError(outcome.error),
      h("p", {}, "服务端拒绝删除：知识库已被其他操作修改，或者仍有来源、文档、问答对或版本（只能删除空的、没有版本的知识库）。原因见上方服务端说明。"),
      reloadButton(),
    );
  }
}
