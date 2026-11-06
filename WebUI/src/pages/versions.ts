/**
 * 版本: versions of the selected knowledge base, their difference, publishing a
 * ready version and rolling back to an earlier one. Both actions name the
 * active version they expect, so a concurrent change is a 409, not a silent
 * overwrite.
 */

import type { KnowledgeBase, Snapshot, SnapshotState } from "@qa/client";
import { confirmStrip, dataTable, facts, formatTime, idText, listOf, row } from "../components/data.js";
import { kbContext, pageLink, type KBContext } from "../components/kb-context.js";
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

const STATE_LABEL: Record<SnapshotState, string> = {
  draft: "草稿",
  staging: "构建中",
  ready: "就绪，未发布",
  published: "曾发布",
  failed: "构建失败",
};

export function renderVersionPage(ctx: PageContext): HTMLElement {
  const kbc = kbContext(ctx);
  const body = h("div", {});
  void kbc.ready.then((kb) => {
    if (kb && !ctx.signal.aborted) body.replaceChildren(...versionSections(ctx, kbc));
  });
  return h(
    "div",
    { class: "page" },
    pageIntro("版本", "查看所选知识库的版本、比较两个版本的文档差异，发布就绪版本或回滚到以前发布过的版本。"),
    kbc.element,
    body,
  );
}
function versionSections(ctx: PageContext, kbc: KBContext): HTMLElement[] {
  const status = createStatusArea();
  const actionStatus = createStatusArea();
  const confirmSlot = h("div", {});
  const table = dataTable("版本列表", ["版本", "状态", "创建时间", "父版本", "文档数", "关键词索引", "操作"]);
  const diff = diffPanel(ctx);

  const versionRow = (kb: KnowledgeBase, version: Snapshot): HTMLTableRowElement => {
    const active = version.version_id === kb.active_version_id;
    const state = version.state ?? "draft";
    const actions: HTMLElement[] = [];
    if (active) actions.push(h("span", { class: "badge" }, "活动版本"));
    else if (state === "ready") actions.push(actionButton("发布", version, publishVersion));
    else if (state === "published") actions.push(actionButton("回滚到此版本", version, rollbackVersion));
    return row(
      [
        idText(version.version_id),
        STATE_LABEL[state] ?? state,
        formatTime(version.created_at),
        idText(version.parent_version_id ?? null),
        String(Object.keys(version.document_revisions ?? {}).length),
        version.keyword_profile ?? "—",
        h("span", { class: "row-actions" }, ...actions),
      ],
      active ? { "data-version-id": version.version_id, "aria-current": "true" } : { "data-version-id": version.version_id },
    );
  };

  type Action = (ctx: PageContext, kbc: KBContext, version: Snapshot, slot: HTMLElement, status: StatusArea) => Promise<boolean>;
  const actionButton = (label: string, version: Snapshot, action: Action): HTMLButtonElement => {
    const element = button(label, () => {
      void action(ctx, kbc, version, confirmSlot, actionStatus).then(() => load());
    });
    element.setAttribute("aria-label", `${label} ${version.version_id}`);
    return element;
  };

  const load = async (): Promise<void> => {
    table.setMessage("正在加载…");
    const kb = await kbc.refresh();
    if (!kb) return;
    const outcome = await attempt(status, "加载版本", () => ctx.client.listVersions(kb.kb_id, { signal: ctx.signal }));
    if (!outcome.ok) {
      table.setMessage(`加载失败：${describeError(outcome.error).title}`, "error");
      return;
    }
    const versions = [...outcome.value].reverse();
    table.setRows(versions.map((version) => versionRow(kb, version)), "还没有版本。在“导入”页完成一次导入后会产生第一个版本。");
    diff.setVersions(kb, versions);
  };

  void load();
  return [
    section("版本列表", toolbar(button("刷新版本", () => void load()), pageLink(ctx, "imports", "去导入")), status.element, table.element, confirmSlot, actionStatus.element),
    diff.element,
  ];
}
/** Make a ready version active; resolves true when the server confirmed it. */
export async function publishVersion(
  ctx: PageContext,
  kbc: KBContext,
  version: Snapshot,
  slot: HTMLElement,
  status: StatusArea,
): Promise<boolean> {
  if (!(await confirmStrip(slot, `确认发布版本 ${version.version_id}？之后的检索和问答将使用它。`, "确认发布"))) return false;
  const expected = kbc.current()?.active_version_id ?? null;
  const outcome = await attempt(status, "发布版本", () =>
    ctx.client.publishVersion(version.version_id, { expected_active_version_id: expected }, { signal: ctx.signal }),
  );
  return report(outcome, status, `已发布：版本 ${version.version_id} 现在是活动版本。`);
}

/** Switch the active pointer back to an earlier verified version (no files are rewritten). */
export async function rollbackVersion(
  ctx: PageContext,
  kbc: KBContext,
  version: Snapshot,
  slot: HTMLElement,
  status: StatusArea,
): Promise<boolean> {
  const message = `确认回滚到版本 ${version.version_id}？活动版本会切换回它，之后的同步以它为基线比较。`;
  if (!(await confirmStrip(slot, message, "确认回滚"))) return false;
  const kb = kbc.current();
  if (!kb) return false;
  const outcome = await attempt(status, "回滚版本", () =>
    ctx.client.rollbackVersion(
      kb.kb_id,
      { target_version_id: version.version_id, expected_active_version_id: kb.active_version_id ?? null },
      { signal: ctx.signal },
    ),
  );
  return report(outcome, status, `已回滚：版本 ${version.version_id} 现在是活动版本。`);
}

function report(outcome: { ok: boolean; error?: unknown }, status: StatusArea, done: string): boolean {
  if (outcome.ok) {
    status.ok(done);
    return true;
  }
  if (isConflict(outcome.error)) {
    status.element.append(h("p", {}, "活动版本已被其他操作改变；列表已刷新，请核对后重试。"));
  }
  return false;
}
interface DiffPanel {
  element: HTMLElement;
  setVersions(kb: KnowledgeBase, versions: Snapshot[]): void;
}

function diffPanel(ctx: PageContext): DiffPanel {
  const status = createStatusArea();
  const left = h("select", { name: "left" });
  const right = h("select", { name: "right" });
  const result = h("div", {});
  const compare = button("比较", () => void run());
  const controls = h("div", { class: "toolbar" }, field("旧版本", left), field("新版本", right), compare);
  const hint = note("需要至少两个版本才能比较。");
  let kb: KnowledgeBase | null = null;

  const run = async (): Promise<void> => {
    if (!kb || !left.value || !right.value) return;
    const current = kb;
    result.replaceChildren();
    const outcome = await attempt(status, "比较版本", () => loadDiff(ctx, current, left.value, right.value));
    if (outcome.ok) result.replaceChildren(outcome.value);
  };

  return {
    element: section("版本差异", hint, controls, status.element, result),
    setVersions(nextKb, versions) {
      kb = nextKb;
      const options = (): HTMLOptionElement[] =>
        versions.map((version) => h("option", { value: version.version_id }, `${version.version_id}（${formatTime(version.created_at)}）`));
      left.replaceChildren(...options());
      right.replaceChildren(...options());
      const enough = versions.length >= 2;
      hint.hidden = enough;
      controls.hidden = !enough;
      result.replaceChildren();
      if (!enough) return;
      const newest = versions[0]?.version_id ?? "";
      const active = nextKb.active_version_id;
      right.value = newest;
      left.value = active && active !== newest ? active : (versions[1]?.version_id ?? "");
    },
  };
}

/** Document-level difference of two versions, with titles where they are known. */
export async function loadDiff(ctx: PageContext, kb: KnowledgeBase, leftId: string, rightId: string): Promise<HTMLElement> {
  const [raw, titles] = await Promise.all([
    ctx.client.diffVersions(kb.kb_id, leftId, rightId, { signal: ctx.signal }),
    documentTitles(ctx, kb),
  ]);
  const ids = (key: "added" | "modified" | "removed"): string[] => {
    const value = raw[key];
    if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
      throw new Error(`服务端返回的版本差异缺少 ${key} 列表`);
    }
    return value;
  };
  const named = (list: string[]): string[] => list.map((id) => (titles.has(id) ? `${titles.get(id)}（${id}）` : id));
  const added = ids("added");
  const modified = ids("modified");
  const removed = ids("removed");
  return h(
    "div",
    { class: "diff", "aria-label": "版本差异结果" },
    facts([
      ["旧版本", idText(leftId)],
      ["新版本", idText(rightId)],
      ["新增文档", String(added.length)],
      ["修改文档", String(modified.length)],
      ["移除文档", String(removed.length)],
    ]),
    h("h3", {}, "新增"),
    listOf(named(added), "无"),
    h("h3", {}, "修改"),
    listOf(named(modified), "无"),
    h("h3", {}, "移除"),
    listOf(named(removed), "无"),
  );
}

async function documentTitles(ctx: PageContext, kb: KnowledgeBase): Promise<Map<string, string>> {
  try {
    const page = await ctx.client.listDocuments(kb.kb_id, { limit: 200 }, { signal: ctx.signal });
    return new Map((page.items ?? []).map((doc) => [doc.document_id, doc.title]));
  } catch {
    // Titles are a convenience: the diff itself is still shown by id.
    return new Map();
  }
}
