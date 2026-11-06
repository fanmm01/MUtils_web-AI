/**
 * 内容: documents and QA pairs of the selected knowledge base. Every edit names
 * the revision it was based on (`expected_revision_id`); a 409 means someone
 * else changed it first and the page offers to reload. A saved edit is a new
 * revision; whether and when it reaches a published version is what the
 * server's ChangeReceipt says, and the page repeats exactly that.
 */

import type { ChangeReceipt, Document, DocumentDetail, KnowledgeBase, QAPair } from "@qa/client";
import { confirmStrip, dataTable, facts, formatTime, idText, row } from "../components/data.js";
import { watchJob } from "../components/jobs.js";
import { kbContext, pageLink, type KBContext } from "../components/kb-context.js";
import { publishPanel } from "../components/publish.js";
import {
  attempt,
  button,
  createStatusArea,
  describeError,
  field,
  h,
  isConflict,
  note,
  pageIntro,
  section,
  toolbar,
  type StatusArea,
} from "../components/ui.js";
import type { PageContext } from "../state.js";

const PAGE_SIZE = 50;

export function renderContentPage(ctx: PageContext): HTMLElement {
  const kbc = kbContext(ctx);
  const body = h("div", {});
  void kbc.ready.then((kb) => {
    if (kb && !ctx.signal.aborted) body.replaceChildren(documentsSection(ctx, kb, kbc), qaSection(ctx, kb, kbc));
  });
  return h(
    "div",
    { class: "page" },
    pageIntro("内容", "查看和维护所选知识库的文档与问答对。保存修改会生成新修订，不会改写导入的原始文件。"),
    kbc.element,
    body,
  );
}
function documentsSection(ctx: PageContext, kb: KnowledgeBase, kbc: KBContext): HTMLElement {
  const status = createStatusArea();
  const table = dataTable("文档列表", ["标题", "状态", "更新时间", "操作"]);
  const detail = h("div", { class: "detail" });
  let cursor: string | null = null;
  const more = button("加载更多", () => void load(false));
  more.hidden = true;

  const docRow = (doc: Document): HTMLTableRowElement => {
    const open = button("查看/编辑", () => void openDocument(ctx, kb, kbc, doc.document_id, detail, () => void load(true)));
    open.setAttribute("aria-label", `查看文档 ${doc.title}`);
    return row([doc.title, doc.deleted ? "已删除" : "有效", formatTime(doc.updated_at), open], {
      "data-document-id": doc.document_id,
    });
  };

  async function load(reset: boolean): Promise<void> {
    if (reset) {
      cursor = null;
      table.setMessage("正在加载…");
    }
    const query = reset || !cursor ? { limit: PAGE_SIZE } : { limit: PAGE_SIZE, cursor };
    const outcome = await attempt(status, "加载文档", () => ctx.client.listDocuments(kb.kb_id, query, { signal: ctx.signal }));
    if (!outcome.ok) {
      if (reset) table.setMessage(`加载失败：${describeError(outcome.error).title}`, "error");
      return;
    }
    // QA pairs are stored as documents too; they are listed in their own section.
    const docs = (outcome.value.items ?? []).filter((doc) => doc.content_kind !== "qa_pair");
    if (reset) table.setRows(docs.map(docRow), "这个知识库还没有文档。可以在“导入”页导入，或在下方新建。");
    else table.appendRows(docs.map(docRow));
    cursor = outcome.value.next_cursor ?? null;
    more.hidden = !cursor;
  }

  const createStatus = createStatusArea();
  const title = h("input", { name: "title", required: true, maxlength: "400" });
  const text = h("textarea", { name: "text", rows: "6" });
  const form = h(
    "form",
    { class: "form", "aria-label": "新建文档" },
    field("标题", title),
    field("正文", text),
    h("button", { type: "submit" }, "新建文档"),
    createStatus.element,
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void saveDocument(ctx, kb, kbc, null, { title: title.value.trim(), text: text.value }, createStatus, () => undefined).then((receipt) => {
      if (!receipt) return;
      form.reset();
      void load(true);
    });
  });

  void load(true);
  return section(
    "文档",
    toolbar(button("刷新文档", () => void load(true))),
    status.element,
    table.element,
    more,
    detail,
    h("h3", {}, "新建文档"),
    form,
  );
}
/** Load one document with its current revision into `slot`. */
export async function loadDocument(ctx: PageContext, documentId: string): Promise<DocumentDetail> {
  return ctx.client.getDocument(documentId, undefined, { signal: ctx.signal });
}

async function openDocument(
  ctx: PageContext,
  kb: KnowledgeBase,
  kbc: KBContext,
  documentId: string,
  slot: HTMLElement,
  onChanged: () => void,
): Promise<void> {
  const status = createStatusArea();
  slot.replaceChildren(status.element);
  const outcome = await attempt(status, "读取文档", () => loadDocument(ctx, documentId));
  if (!outcome.ok) return;
  slot.replaceChildren(documentEditor(ctx, kb, kbc, outcome.value, slot, onChanged));
  slot.querySelector<HTMLElement>("h3")?.focus();
}

function documentEditor(
  ctx: PageContext,
  kb: KnowledgeBase,
  kbc: KBContext,
  detail: DocumentDetail,
  slot: HTMLElement,
  onChanged: () => void,
): HTMLElement {
  const { document: doc, revision } = detail;
  let based = detail;
  const factsSlot = h("div", {}, documentFacts(detail));
  const status = createStatusArea();
  const confirmSlot = h("div", {});
  const title = h("input", { name: "title", required: true, maxlength: "400" });
  title.value = doc.title;
  const text = h("textarea", { name: "text", rows: "12" });
  text.value = revision.normalized_text ?? "";
  const reload = (): void => void openDocument(ctx, kb, kbc, doc.document_id, slot, onChanged);
  const save = h("button", { type: "submit" }, "保存为新修订");
  const remove = button("删除文档", () =>
    void deleteDocument(ctx, kbc, based.document, confirmSlot, status, reload, () => {
      for (const control of [title, text, save, remove]) control.disabled = true;
      onChanged();
    }),
  );
  remove.classList.add("danger");
  const form = h(
    "form",
    { class: "form", "aria-label": "编辑文档" },
    field("标题", title),
    field("规范化正文", text),
    toolbar(save, remove),
    confirmSlot,
    status.element,
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void saveDocument(ctx, kb, kbc, based, { title: title.value.trim(), text: text.value }, status, reload).then(async (receipt) => {
      if (!receipt) return;
      onChanged();
      // The next edit must name the revision this save created; hold edits until it is known.
      const controls = [title, text, save, remove];
      for (const control of controls) control.disabled = true;
      try {
        based = await loadDocument(ctx, doc.document_id);
        factsSlot.replaceChildren(documentFacts(based));
      } catch (error) {
        conflictHint(status, `无法读取保存后的最新修订（${describeError(error).title}）。`, reload);
      } finally {
        for (const control of controls) control.disabled = false;
      }
    });
  });
  return h(
    "article",
    { class: "editor", "aria-label": `文档 ${doc.title}` },
    h("h3", { tabindex: "-1" }, `文档：${doc.title}`),
    factsSlot,
    form,
    note("这里修改的是规范化正文。替换原始文件请在“导入”页重新上传或同步来源。"),
  );
}

function documentFacts(detail: DocumentDetail): HTMLElement {
  const { document: doc, revision } = detail;
  const diagnostics = revision.diagnostics ?? [];
  return facts([
    ["文档 ID", idText(doc.document_id)],
    ["当前修订", idText(revision.revision_id)],
    ["状态", doc.deleted ? "已删除" : "有效"],
    ["来源文件", revision.relative_path ? h("code", {}, revision.relative_path) : "—（直接录入）"],
    ["修订时间", formatTime(revision.created_at)],
    ["解析诊断", diagnostics.length > 0 ? diagnostics.join("；") : "无"],
  ]);
}
/** Create (`detail` null) or edit a document; resolves with the server's receipt. */
export async function saveDocument(
  ctx: PageContext,
  kb: KnowledgeBase,
  kbc: KBContext,
  detail: DocumentDetail | null,
  form: { title: string; text: string },
  status: StatusArea,
  reload: () => void,
): Promise<ChangeReceipt | null> {
  const outcome = await attempt(status, detail ? "保存文档" : "新建文档", () =>
    detail
      ? ctx.client.updateDocument(
          detail.document.document_id,
          {
            kb_id: kb.kb_id,
            title: form.title,
            text: form.text,
            relative_path: detail.revision.relative_path ?? null,
            expected_revision_id: detail.document.latest_revision_id,
          },
          { signal: ctx.signal },
        )
      : ctx.client.createDocument(kb.kb_id, { kb_id: kb.kb_id, title: form.title, text: form.text }, { signal: ctx.signal }),
  );
  if (!outcome.ok) {
    if (isConflict(outcome.error)) conflictHint(status, "文档已被其他操作修改。", reload);
    return null;
  }
  showReceipt(ctx, kbc, status, detail ? "已保存为新修订。" : "已新建文档。", outcome.value);
  return outcome.value;
}

export async function deleteDocument(
  ctx: PageContext,
  kbc: KBContext,
  doc: Document,
  confirmSlot: HTMLElement,
  status: StatusArea,
  reload: () => void,
  onDeleted: () => void,
): Promise<void> {
  if (!(await confirmStrip(confirmSlot, `确认删除文档“${doc.title}”？已发布的版本不会被改动。`, "确认删除"))) return;
  const outcome = await attempt(status, "删除文档", () =>
    ctx.client.deleteDocument(doc.document_id, doc.latest_revision_id, { signal: ctx.signal }),
  );
  if (!outcome.ok) {
    if (isConflict(outcome.error)) conflictHint(status, "文档已被其他操作修改。", reload);
    return;
  }
  showReceipt(ctx, kbc, status, "已删除文档。", outcome.value);
  onDeleted();
}

/** Repeat what the server's ChangeReceipt says about when a change takes effect. */
function showReceipt(ctx: PageContext, kbc: KBContext, status: StatusArea, lead: string, receipt: ChangeReceipt): void {
  if (receipt.job_id) {
    const card = watchJob(ctx.client, receipt.job_id, { title: "构建任务", signal: ctx.signal, pollMs: ctx.jobPollMs });
    status.ok(`${lead}服务端已创建构建任务；任务完成并发布新版本后，修改才会进入问答。`, card.element);
    return;
  }
  if (receipt.version_id) {
    // The P2 server rebuilds the whole base synchronously into a ready, unpublished version.
    status.ok(`${lead}服务端已据此构建新版本；发布之前问答仍使用当前活动版本。`, publishPanel(ctx, kbc, receipt.version_id));
    return;
  }
  if (receipt.requires_publish ?? true) {
    status.ok(
      `${lead}服务端没有为这次修改创建构建任务，修改尚未进入任何版本；在包含它的新版本构建并发布之前，问答仍使用当前活动版本。`,
      pageLink(ctx, "versions", "查看版本"),
    );
    return;
  }
  status.ok(`${lead}服务端表示这次修改不需要发布。`);
}

function conflictHint(status: StatusArea, text: string, reload: () => void): void {
  status.element.append(
    h("p", {}, `${text}重新加载会用服务端的最新内容替换你未保存的修改。`),
    toolbar(button("重新加载", reload)),
  );
}
function qaSection(ctx: PageContext, kb: KnowledgeBase, kbc: KBContext): HTMLElement {
  const status = createStatusArea();
  const table = dataTable("问答对列表", ["问题", "答案", "更新时间", "操作"]);
  const detail = h("div", { class: "detail" });
  let cursor: string | null = null;
  const more = button("加载更多", () => void load(false));
  more.hidden = true;

  const qaRow = (pair: QAPair): HTMLTableRowElement => {
    const open = button("编辑", () => openQA(pair));
    open.setAttribute("aria-label", `编辑问答对 ${pair.question}`);
    const answer = pair.answer.length > 80 ? `${pair.answer.slice(0, 80)}…` : pair.answer;
    return row([pair.question, answer, formatTime(pair.updated_at), open], { "data-qa-id": pair.qa_id });
  };
  const openQA = (pair: QAPair): void => {
    detail.replaceChildren(qaEditor(ctx, kb, kbc, pair, () => void load(true), (fresh) => openQA(fresh)));
    detail.querySelector<HTMLElement>("h3")?.focus();
  };

  async function load(reset: boolean): Promise<void> {
    if (reset) {
      cursor = null;
      table.setMessage("正在加载…");
    }
    const query = reset || !cursor ? { limit: PAGE_SIZE } : { limit: PAGE_SIZE, cursor };
    const outcome = await attempt(status, "加载问答对", () => ctx.client.listQA(kb.kb_id, query, { signal: ctx.signal }));
    if (!outcome.ok) {
      if (reset) table.setMessage(`加载失败：${describeError(outcome.error).title}`, "error");
      return;
    }
    const rows = (outcome.value.items ?? []).map(qaRow);
    if (reset) table.setRows(rows, "这个知识库还没有问答对。可以在下方直接录入。");
    else table.appendRows(rows);
    cursor = outcome.value.next_cursor ?? null;
    more.hidden = !cursor;
  }

  const createStatus = createStatusArea();
  const question = h("textarea", { name: "question", required: true, rows: "2" });
  const answer = h("textarea", { name: "answer", required: true, rows: "3" });
  const form = h(
    "form",
    { class: "form", "aria-label": "新建问答对" },
    field("问题", question),
    field("答案", answer),
    h("button", { type: "submit" }, "新建问答对"),
    createStatus.element,
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const body = { question: question.value.trim(), answer: answer.value.trim() };
    void saveQAPair(ctx, kb, kbc, null, body, createStatus, () => undefined).then((receipt) => {
      if (!receipt) return;
      form.reset();
      void load(true);
    });
  });

  void load(true);
  return section("问答对", toolbar(button("刷新问答对", () => void load(true))), status.element, table.element, more, detail, h("h3", {}, "新建问答对"), form);
}
function qaEditor(
  ctx: PageContext,
  kb: KnowledgeBase,
  kbc: KBContext,
  pair: QAPair,
  onChanged: () => void,
  reopen: (fresh: QAPair) => void,
): HTMLElement {
  let based = pair;
  const status = createStatusArea();
  const confirmSlot = h("div", {});
  const question = h("textarea", { name: "question", required: true, rows: "2" });
  question.value = pair.question;
  const answer = h("textarea", { name: "answer", required: true, rows: "4" });
  answer.value = pair.answer;
  const reload = (): void => {
    void attempt(status, "重新加载问答对", () => ctx.client.getQA(pair.qa_id, { signal: ctx.signal })).then((outcome) => {
      if (outcome.ok) reopen(outcome.value);
    });
  };
  const save = h("button", { type: "submit" }, "保存");
  const remove = button("删除问答对", () =>
    void deleteQAPair(ctx, kbc, based, confirmSlot, status, reload, () => {
      for (const control of [question, answer, save, remove]) control.disabled = true;
      onChanged();
    }),
  );
  remove.classList.add("danger");
  const form = h(
    "form",
    { class: "form", "aria-label": "编辑问答对" },
    field("问题", question),
    field("答案", answer),
    toolbar(save, remove),
    confirmSlot,
    status.element,
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const body = { question: question.value.trim(), answer: answer.value.trim() };
    void saveQAPair(ctx, kb, kbc, based, body, status, reload).then(async (receipt) => {
      if (!receipt) return;
      onChanged();
      const controls = [question, answer, save, remove];
      for (const control of controls) control.disabled = true;
      try {
        based = await ctx.client.getQA(pair.qa_id, { signal: ctx.signal });
      } catch (error) {
        conflictHint(status, `无法读取保存后的最新修订（${describeError(error).title}）。`, reload);
      } finally {
        for (const control of controls) control.disabled = false;
      }
    });
  });
  return h("article", { class: "editor", "aria-label": "问答对" }, h("h3", { tabindex: "-1" }, "编辑问答对"), facts([["问答对 ID", idText(pair.qa_id)]]), form);
}

/** Create (`pair` null) or edit a QA pair; resolves with the server's receipt. */
export async function saveQAPair(
  ctx: PageContext,
  kb: KnowledgeBase,
  kbc: KBContext,
  pair: QAPair | null,
  form: { question: string; answer: string },
  status: StatusArea,
  reload: () => void,
): Promise<ChangeReceipt | null> {
  const outcome = await attempt(status, pair ? "保存问答对" : "新建问答对", () =>
    pair
      ? ctx.client.updateQA(pair.qa_id, { kb_id: kb.kb_id, ...form, expected_revision_id: pair.revision_id }, { signal: ctx.signal })
      : ctx.client.createQA(kb.kb_id, { kb_id: kb.kb_id, ...form }, { signal: ctx.signal }),
  );
  if (!outcome.ok) {
    if (isConflict(outcome.error)) conflictHint(status, "问答对已被其他操作修改。", reload);
    return null;
  }
  showReceipt(ctx, kbc, status, pair ? "已保存问答对。" : "已新建问答对。", outcome.value);
  return outcome.value;
}

export async function deleteQAPair(
  ctx: PageContext,
  kbc: KBContext,
  pair: QAPair,
  confirmSlot: HTMLElement,
  status: StatusArea,
  reload: () => void,
  onDeleted: () => void,
): Promise<void> {
  if (!(await confirmStrip(confirmSlot, "确认删除这个问答对？已发布的版本不会被改动。", "确认删除"))) return;
  const outcome = await attempt(status, "删除问答对", () => ctx.client.deleteQA(pair.qa_id, pair.revision_id, { signal: ctx.signal }));
  if (!outcome.ok) {
    if (isConflict(outcome.error)) conflictHint(status, "问答对已被其他操作修改。", reload);
    return;
  }
  showReceipt(ctx, kbc, status, "已删除问答对。", outcome.value);
  onDeleted();
}
